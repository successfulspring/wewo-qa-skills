"""Aggregate immutable invocations; never discard earlier failing evidence."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from artifact_tools import (ValidationFailure, load_json, sha256_file, write_text_atomic,
                            validate_execution_profile_file, validate_results_file)
from execution_readiness import selected_pairs


def asset_signature(receipt, binding):
    entries = {b["asset"].replace("\\", "/") for b in receipt["bindings"]}
    own = binding["asset"].replace("\\", "/")
    relevant = [(a["path"],a["sha256"]) for a in receipt["assets"] if a["path"] == own or a["path"] not in entries]
    return hashlib.sha256(json.dumps(sorted(relevant)).encode()).hexdigest()


def aggregate(manifest_path, profile_path):
    profile, manifest = validate_execution_profile_file(profile_path, manifest_path)
    if profile["schema_version"] != "1.2":
        raise ValidationFailure(["run aggregation requires profile 1.2; retain legacy reports as historical evidence"])
    base = profile_path.parent
    sources, history = [], {}
    receipts = sorted((base / "native").glob("*/receipt.json"), key=lambda p:load_json(p)["started_at"])
    started = finished = profile["collected_at"]
    for receipt_path in receipts:
        receipt = load_json(receipt_path)
        ident = receipt_path.parent.name
        raw = base / ("execution-results." + ident + ".json")
        judged = base / ("execution-results." + ident + ".judged.json")
        if not raw.is_file():
            raise ValidationFailure(["invocation has no result file; recover its original evidence before summarizing: " + ident])
        validate_results_file(raw, manifest_path)
        path = judged if judged.is_file() else raw
        results, _ = validate_results_file(path, manifest_path)
        if receipt["profile_sha256"] != sha256_file(profile_path) or receipt["manifest_sha256"] != sha256_file(manifest_path):
            raise ValidationFailure(["invocation belongs to a different frozen profile or case baseline"])
        if results["run"].get("invocation_id") != ident or results["run"]["run_id"] != base.name:
            raise ValidationFailure(["result does not identify its actual invocation"])
        receipt_hash = sha256_file(receipt_path)
        if not sources:
            started = receipt["started_at"]
        finished = max(finished, receipt["finished_at"])
        source = {"invocation_id":ident, "receipt":receipt_path.relative_to(base).as_posix(), "receipt_sha256":receipt_hash,
                  "original":raw.name, "original_sha256":sha256_file(raw), "results":path.name, "results_sha256":sha256_file(path)}
        sources.append(source)
        for binding in receipt["bindings"]:
            pair = (binding["case_id"],binding["target_id"])
            result = next(r for r in results["results"] if (r["case_id"],r["target_id"]) == pair)
            if result.get("native_test", {}).get("receipt_sha256") != receipt_hash:
                raise ValidationFailure(["result replaced its original native execution mapping"])
            previous = history.setdefault(pair, [])
            rerun = binding.get("rerun", {})
            if previous and rerun.get("previous_receipt_sha256") != previous[-1]["receipt_sha256"]:
                raise ValidationFailure(["invocation history omits or mislinks an earlier attempt"])
            if not previous and rerun:
                raise ValidationFailure(["rerun has no preserved initial attempt"])
            previous.append({"source":path.name, "receipt_sha256":receipt_hash,
                             "asset_signature":asset_signature(receipt,binding), "status":result["status"],
                             "rerun":rerun, "result":copy.deepcopy(result)})
    run = {"run_id":base.name,"manifest_path":profile["manifest_path"],"manifest_sha256":sha256_file(manifest_path),
           "execution_profile_path":profile_path.name,"execution_profile_sha256":sha256_file(profile_path),
           "case_workbook_sha256":profile["case_workbook_sha256"],"suite":profile["suite"],"targets":profile["targets"],
           "environments":profile["environments"],"environment":{k:profile["environments"][0][k] for k in ("name","kind","build")},
           "started_at":started,"finished_at":finished}
    if profile.get("notes"):
        run["notes"] = profile["notes"]
    presentation, pair_records, history_rows = [], [], []
    for case,target,auto in selected_pairs(manifest,profile["suite"],profile["targets"]):
        attempts = history.get((case["id"],target), [])
        if attempts:
            latest = attempts[-1]
            result = copy.deepcopy(latest["result"])
            previous_failures = [a for a in attempts[:-1] if a["status"] == "failed"]
            note = ""
            if result["status"] == "passed" and previous_failures:
                if any(a["asset_signature"] == latest["asset_signature"] for a in previous_failures):
                    result["status"] = "flaky"
                    note = "Equivalent code/environment attempts include failure and pass; inspect all preserved evidence."
                elif latest["rerun"].get("kind") != "test-repair":
                    result["status"] = "blocked"
                    note = "Earlier failure followed by changed test assets without a documented test repair."
                else:
                    note = "Current test revision passed after a documented test repair; original failures are retained. " + latest["rerun"]["reason"]
            if note:
                result["history_note"] = note
                if result["status"] == "blocked":
                    result["blocker"] = note
                elif result["status"] == "flaky":
                    result["failure_reason"] = note
            result["attempts"] = len(attempts)
        else:
            readiness = next(r for r in profile["case_readiness"] if (r["case_id"],r["target_id"]) == (case["id"],target))
            result = {"case_id":case["id"],"target_id":target,"status":"not-run" if auto["feasibility"] == "manual" else "blocked",
                      "attempts":0,"tool":"","assertions":[],"evidence":[],
                      "blocker":("manual-only: " if auto["feasibility"] == "manual" else "") + (readiness["reason"] or "No native execution; required readiness or test implementation is incomplete.")}
        presentation.append(result)
        pair_records.append({"case_id":case["id"],"target_id":target,"status":result["status"],"attempts":len(attempts),
                             "latest_source":attempts[-1]["source"] if attempts else "","note":result.get("history_note",result.get("blocker",""))})
        for number, attempt in enumerate(attempts,1):
            history_rows.append({"case_id":case["id"],"target_id":target,"attempt":number,"status":attempt["status"],
                                 "source":attempt["source"],"kind":attempt["rerun"].get("kind","initial"),
                                 "reason":attempt["rerun"].get("reason",""),"reset_note":attempt["rerun"].get("reset_note","")})
    summary = {"format":"wewo-qa-run-summary/1","run":run,"sources":sources,"pairs":pair_records}
    view = {"run":run,"results":presentation,"history":history_rows,"readiness":copy.deepcopy(profile["case_readiness"])}
    return summary, view, manifest


def load_summary(path, manifest_path):
    saved = load_json(path)
    expected, view, manifest = aggregate(manifest_path, path.parent / "execution-profile.json")
    if saved != expected:
        raise ValidationFailure(["run summary is stale or modified; regenerate it from every preserved invocation"])
    return view, manifest


def main():
    parser = argparse.ArgumentParser(description="Summarize every native invocation, including failures and unexecuted scope.")
    parser.add_argument("manifest",type=Path)
    parser.add_argument("profile",type=Path)
    parser.add_argument("--output",type=Path)
    args = parser.parse_args()
    profile = args.profile.resolve()
    output = args.output.resolve() if args.output else profile.with_name("execution-summary.json")
    if output.parent != profile.parent or output.name != "execution-summary.json":
        raise ValidationFailure(["summary belongs at execution-summary.json in the same run directory"])
    summary, _, _ = aggregate(args.manifest.resolve(),profile)
    write_text_atomic(output,json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print("WROTE: " + str(output))
    return 0
