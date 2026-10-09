"""Run an existing project test runner and preserve its native evidence.

This command does not invent tests or oracles. The agent supplies reviewed test
assets and a scoped plan; observations must be emitted by the running tests.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from artifact_tools import (ValidationFailure, _safe_evidence_path, load_json,
    sha256_file, write_text_atomic, validate_execution_profile_file,
    runtime_requirement_ids_for_pair, validate_results_file, schema_errors, EXECUTOR_SCHEMA_ROOT)


def now():
    return datetime.now(timezone.utc).isoformat()


def native_tests(path, kind):
    """Preserve native identifiers and outcomes; zero discovered tests is not pass."""
    outcomes = {}
    def add(ident, status):
        outcomes.setdefault(ident, []).append(status)
    if kind == "junit":
        root = ET.parse(path).getroot()
        for case in root.iter():
            if case.tag.split("}")[-1] != "testcase":
                continue
            tags = {c.tag.split("}")[-1] for c in case}
            status = "failed" if tags & {"failure", "error"} else "skipped" if "skipped" in tags else "passed"
            add(case.get("classname", "") + "::" + case.get("name", ""), status)
    elif kind == "playwright-json":
        report = load_json(path)
        def walk(suite, parents):
            titles = parents + ([suite["title"]] if suite.get("title") else [])
            for spec in suite.get("specs", []):
                for test in spec.get("tests", []):
                    ident = " > ".join(titles + [spec["title"]]) + " [" + test.get("projectName", "") + "]"
                    for result in test.get("results", []):
                        status = result.get("status")
                        # Expected-to-fail tests cannot prove the frozen business oracle.
                        if test.get("expectedStatus", "passed") != "passed":
                            status = "skipped"
                        add(ident, status if status in {"passed", "skipped"} else "failed")
            for child in suite.get("suites", []):
                walk(child, titles)
        for suite in report.get("suites", []):
            walk(suite, [])
    else:
        raise ValueError("unsupported native report; use junit or playwright-json")
    return outcomes


def write_json(path, value):
    write_text_atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def receipt_file(base, receipt, field):
    item = receipt[field]
    path = _safe_evidence_path(base, item["path"])
    if path is None or not path.is_file() or sha256_file(path) != item["sha256"]:
        raise ValueError("native runner evidence is missing, outside run, or changed: " + field)
    return path


def validate_native_observation(record, base, run, result, assertion_id):
    link = record["native"]
    path = _safe_evidence_path(base, link["receipt_path"])
    if path is None or not path.is_file() or sha256_file(path) != link["receipt_sha256"]:
        raise ValueError("native run receipt is missing or changed")
    receipt = load_json(path)
    if receipt["run_id"] != run["run_id"] or receipt["manifest_sha256"] != run["manifest_sha256"] or receipt["profile_sha256"] != run["execution_profile_sha256"]:
        raise ValueError("native receipt belongs to another run or baseline")
    bindings = [b for b in receipt["bindings"] if (b["case_id"], b["target_id"]) == (result["case_id"], result["target_id"])]
    if len(bindings) != 1 or assertion_id not in bindings[0]["assertion_ids"]:
        raise ValueError("assertion is not mapped to this native test")
    binding = bindings[0]
    report = receipt_file(base, receipt, "report")
    outcomes = native_tests(report, receipt["report_format"])
    statuses = outcomes.get(binding["test_id"], [])
    if len(statuses) != 1:
        raise ValueError("native test is absent or retry history is ambiguous; use separate invocations")
    if result["status"] == "passed" and (statuses != ["passed"] or receipt.get("timeout")):
        raise ValueError("native runner did not pass this case")
    if receipt["exit_code"] != 0 and not any("failed" in v for v in outcomes.values()):
        raise ValueError("runner exited unsuccessfully without an attributable native test failure")
    for asset in receipt["assets"]:
        evidence = _safe_evidence_path(base, asset["evidence_path"])
        if evidence is None or not evidence.is_file() or sha256_file(evidence) != asset["sha256"]:
            raise ValueError("frozen executable test asset changed")
    logs = receipt_file(base, receipt, "observations").read_text(encoding="utf-8").splitlines()
    index = link["line"] - 1
    if index < 0 or index >= len(logs):
        raise ValueError("native observation line is missing")
    event = json.loads(logs[index])
    expected = {k:record[k] for k in ("run_id", "case_id", "target_id", "attempt", "subject", "location", "captured_at")}
    expected.update(assertion_id=assertion_id, test_id=binding["test_id"], phase=link["phase"])
    if any(event.get(k) != v for k,v in expected.items()) or json.dumps(event.get("value"), sort_keys=True) != json.dumps(record["raw"], sort_keys=True):
        raise ValueError("native observation differs from runner-produced data")
    from artifact_tools import _parse_datetime
    if not _parse_datetime(receipt["started_at"]) <= _parse_datetime(event["captured_at"]) <= _parse_datetime(receipt["finished_at"]):
        raise ValueError("native observation was not captured during this invocation")


def execute(plan, manifest_path, profile_path, environment, *, timeout=600):
    errors = schema_errors(plan, EXECUTOR_SCHEMA_ROOT / "native-plan.schema.json")
    if errors:
        raise ValidationFailure(errors)
    profile, manifest = validate_execution_profile_file(profile_path, manifest_path)
    if plan["manifest_sha256"] != sha256_file(manifest_path) or plan["profile_sha256"] != sha256_file(profile_path):
        raise ValidationFailure(["native plan baseline is stale"])
    if environment["kind"] not in {"test", "staging", "preview"}:
        raise ValidationFailure(["native automation requires an identified test environment"])
    repo = Path(plan["repository"]).resolve(strict=True)
    if not repo.is_dir() or not plan.get("runner") or not isinstance(plan.get("argv"), list) or not all(isinstance(x,str) and x for x in plan["argv"]):
        raise ValidationFailure(["native plan requires a repository, runner and explicit argv"])
    run_dir = profile_path.resolve().parent
    run_id = run_dir.name
    cases = {c["id"]:c for c in manifest["cases"]}
    pairs = {(c["id"], t) for c in cases.values() if profile["suite"] in c["suite_membership"] for t in c["applicable_targets"] if t in profile["targets"]}
    resolved = {b["requirement_id"] for b in profile["bindings"] if b["status"] == "resolved"}
    seen = set()
    assets = {}
    for binding in plan["bindings"]:
        pair = (binding["case_id"], binding["target_id"])
        if pair not in pairs or pair in seen:
            raise ValidationFailure(["native plan contains unexpected or duplicate case-target binding"])
        seen.add(pair)
        case = cases[pair[0]]
        auto = next(a for a in case["automation"] if a["target_id"] == pair[1])
        if auto["feasibility"] == "manual":
            raise ValidationFailure(["manual-only case cannot have generated automation"])
        if case["safety"]["requires_confirmation"] and not binding.get("authorization_ref"):
            raise ValidationFailure(["consequential test needs the existing explicit authorization reference"])
        required = {a["id"] for a in case["assertions"] if pair[1] in a["target_ids"]}
        if set(binding["assertion_ids"]) != required:
            raise ValidationFailure(["native test mapping must cover exactly the planned assertions"])
        if not runtime_requirement_ids_for_pair(manifest, case, pair[1]) <= resolved:
            raise ValidationFailure(["native plan contains an unresolved execution prerequisite"])
        asset = (repo / binding["asset"]).resolve()
        if not asset.is_relative_to(repo) or not asset.is_file() or sha256_file(asset) != binding["asset_sha256"]:
            raise ValidationFailure(["native test asset escapes the repository, is absent, or changed"])
        if not binding.get("test_id") or not binding.get("route"):
            raise ValidationFailure(["native binding requires the actual test identifier and evidence route"])
        assets[str(asset)] = asset
    if not seen:
        raise ValidationFailure(["no executable mapped cases; do not start a runner"])
    if len({b["test_id"] for b in plan["bindings"]}) != len(plan["bindings"]):
        raise ValidationFailure(["each case-target needs an unambiguous native test identifier"])
    if plan["report_format"] not in {"junit", "playwright-json"}:
        raise ValidationFailure(["unsupported native report format"])
    invocation = run_dir / "native" / uuid.uuid4().hex
    invocation.mkdir(parents=True, exist_ok=False)
    report = invocation / ("report.xml" if plan["report_format"] == "junit" else "report.json")
    observations = invocation / "observations.jsonl"
    env = os.environ.copy()
    env.update(WEWO_QA_RUN_ID=run_id, WEWO_QA_OBSERVATIONS_FILE=str(observations), WEWO_QA_REPORT_FILE=str(report))
    substitutions = {"{report}":str(report), "{output_dir}":str(invocation), "{observations}":str(observations)}
    argv = []
    for argument in plan["argv"]:
        for key,value in substitutions.items():
            argument = argument.replace(key,value)
        argv.append(argument)
    receipt = {"format":"wewo-qa-native-run/1", "run_id":run_id, "runner":plan["runner"], "argv":argv,
        "repository":str(repo), "manifest_sha256":sha256_file(manifest_path), "profile_sha256":sha256_file(profile_path),
        "bindings":copy.deepcopy(plan["bindings"]), "report_format":plan["report_format"], "started_at":now(), "assets":[]}
    for i,asset in enumerate(assets.values()):
        frozen = invocation / "assets" / f"{i}{asset.suffix}"
        frozen.parent.mkdir(exist_ok=True)
        frozen.write_bytes(asset.read_bytes())
        receipt["assets"].append({"path":asset.relative_to(repo).as_posix(), "sha256":sha256_file(frozen), "evidence_path":frozen.relative_to(run_dir).as_posix()})
    with (invocation / "stdout.log").open("wb") as stdout, (invocation / "stderr.log").open("wb") as stderr:
        try:
            process = subprocess.run(argv, cwd=repo, env=env, stdout=stdout, stderr=stderr, timeout=timeout, check=False)
            receipt.update(exit_code=process.returncode, timeout=False)
        except subprocess.TimeoutExpired:
            receipt.update(exit_code=-1, timeout=True)
        except OSError as exc:
            receipt.update(exit_code=-1, timeout=False, startup_error=str(exc))
    receipt["finished_at"] = now()
    for field,path in [("report", report), ("observations", observations), ("stdout",invocation/"stdout.log"), ("stderr",invocation/"stderr.log"), ("human_report",invocation/"html-report/index.html")]:
        if path.is_file():
            receipt[field] = {"path":path.relative_to(run_dir).as_posix(), "sha256":sha256_file(path)}
    receipt_path = invocation / "receipt.json"
    write_json(receipt_path, receipt)
    results = collect(receipt_path, manifest, manifest_path, profile, profile_path, environment)
    output = run_dir / f"execution-results.{invocation.name}.json"
    write_json(output, results)
    validate_results_file(output, manifest_path)
    return output


def collect(receipt_path, manifest, manifest_path, profile, profile_path, environment):
    run_dir = profile_path.parent
    receipt = load_json(receipt_path)
    run = {"run_id":receipt["run_id"], "manifest_path":profile["manifest_path"], "manifest_sha256":sha256_file(manifest_path),
        "execution_profile_path":"execution-profile.json", "execution_profile_sha256":sha256_file(profile_path),
        "case_workbook_sha256":profile["case_workbook_sha256"], "suite":profile["suite"], "targets":profile["targets"],
        "environment":environment, "started_at":receipt["started_at"], "finished_at":receipt["finished_at"]}
    candidate = {"schema_version":"1.3", "run":run, "results":[]}
    try:
        outcomes = native_tests(receipt_file(run_dir, receipt, "report"), receipt["report_format"])
    except (KeyError, OSError, ValueError, ET.ParseError):
        outcomes = {}
    try:
        events = [json.loads(line) for line in receipt_file(run_dir, receipt, "observations").read_text(encoding="utf-8").splitlines()]
    except (KeyError, OSError, ValueError):
        events = []
    from observation_checks import evaluate_observations
    for case in manifest["cases"]:
        if profile["suite"] not in case["suite_membership"]:
            continue
        for target in case["applicable_targets"]:
            if target not in profile["targets"]:
                continue
            auto = next(a for a in case["automation"] if a["target_id"] == target)
            binding = next((b for b in receipt["bindings"] if (b["case_id"], b["target_id"]) == (case["id"],target)), None)
            result = {"case_id":case["id"],"target_id":target,"status":"blocked","attempts":1 if binding else 0,
                "tool":receipt["runner"],"assertions":[],"evidence":[],"blocker":"No mapped native test or complete runner evidence."}
            if auto["feasibility"] == "manual":
                result.update(status="not-run",attempts=0,blocker="manual-only case")
            if binding:
                result["native_test"] = {"receipt_path":receipt_path.relative_to(run_dir).as_posix(), "receipt_sha256":sha256_file(receipt_path),
                    "asset":binding["asset"], "test_id":binding["test_id"], "route":binding["route"]}
                for planned in case["assertions"]:
                    if target not in planned["target_ids"]:
                        continue
                    actual = {"assertion_id":planned["id"], "description":planned["description"], "expected":planned["expected"],
                        "actual":"", "status":"not-evaluated", "observations":[], "evidence_refs":[], "reason":"Missing or inconsistent native observations."}
                    for index,event in enumerate(events,1):
                        if (event.get("case_id"),event.get("target_id"),event.get("assertion_id"),event.get("test_id")) != (case["id"],target,planned["id"],binding["test_id"]):
                            continue
                        if event.get("phase") not in {"before","after"}:
                            continue
                        eid = f"EV-NATIVE-{index}"
                        wrapper = {k:event.get(k) for k in ("run_id","case_id","target_id","attempt","subject","location","captured_at")}
                        wrapper.update(format="wewo-qa-native-observation/1",tool=receipt["runner"],raw=event.get("value"),
                            native={"receipt_path":receipt_path.relative_to(run_dir).as_posix(),"receipt_sha256":sha256_file(receipt_path),"line":index,"phase":event["phase"]})
                        path = receipt_path.parent / f"observation-{index}.json"
                        write_json(path,wrapper)
                        evidence = {"id":eid,"type":"tool-output","description":"Runner-produced observed value","path":path.relative_to(run_dir).as_posix(),"sha256":sha256_file(path)}
                        if not any(e["id"] == eid for e in result["evidence"]):
                            result["evidence"].append(evidence)
                        actual["evidence_refs"].append(eid)
                        actual["observations"].append({"attempt":event.get("attempt",1),"phase":event["phase"],"evidence_id":eid,"pointer":"/raw"})
                        for i,attachment in enumerate(event.get("attachments",[])):
                            attached = (receipt_path.parent / attachment["path"]).resolve()
                            if not attached.is_relative_to(receipt_path.parent) or not attached.is_file():
                                continue
                            aid = f"{eid}-ATT-{i}"
                            result["evidence"].append({"id":aid,"type":attachment["type"],"description":attachment["description"],
                                "path":attached.relative_to(run_dir).as_posix(),"sha256":sha256_file(attached)})
                            actual["evidence_refs"].append(aid)
                    try:
                        verdicts = evaluate_observations(actual,planned,{e["id"]:e for e in result["evidence"]},run,result,run_dir,fill_actual=True)
                        types = {e["type"] for e in result["evidence"] if e["id"] in actual["evidence_refs"]}
                        if planned["check"]["kind"] == "evidence-review" or not set(planned["required_evidence"]) <= types:
                            raise ValueError("Requires additional original visual/native evidence and explicit review.")
                        actual.update(status="passed" if all(verdicts) else "failed")
                        actual.pop("reason",None)
                    except (ValueError, KeyError) as exc:
                        actual.update(status="not-evaluated",reason=str(exc),observations=[])
                    result["assertions"].append(actual)
                statuses = outcomes.get(binding["test_id"],[])
                if any(a["status"] == "failed" for a in result["assertions"]):
                    result.update(status="failed",failure_reason="Runner-produced value differs from the requirement-derived expected result.")
                    result.pop("blocker",None)
                elif statuses == ["passed"] and result["assertions"] and all(a["status"] == "passed" for a in result["assertions"]) and not receipt.get("timeout"):
                    result["status"] = "passed"
                    result.pop("blocker",None)
                else:
                    result["blocker"] = "Native status " + str(statuses) + "; incomplete checks, skipped test, startup/test defect, or ambiguous retries."
            result["observed"] = "; ".join(a["assertion_id"] + ": " + a["actual"] for a in result["assertions"] if a["actual"])
            candidate["results"].append(result)
    return candidate


def main():
    parser = argparse.ArgumentParser(description="Execute mapped repository-native acceptance tests and preserve real evidence.")
    parser.add_argument("manifest",type=Path)
    parser.add_argument("profile",type=Path)
    parser.add_argument("plan",type=Path)
    parser.add_argument("--environment",type=Path,required=True,help="Non-secret, verified test environment identity JSON.")
    parser.add_argument("--timeout",type=int,default=600)
    args = parser.parse_args()
    if args.timeout < 1:
        raise ValueError("timeout must be positive")
    path = execute(load_json(args.plan),args.manifest.resolve(),args.profile.resolve(),load_json(args.environment),timeout=args.timeout)
    print(f"WROTE: {path}; native execution complete, inspect verdicts before reporting")
    return 0
