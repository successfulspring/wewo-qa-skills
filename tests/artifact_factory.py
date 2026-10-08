from __future__ import annotations

import json
import os
from pathlib import Path

from artifact_tools import load_json, sha256_file
from case_workbook import module_paths, render_case_workbook
from prepare_execution_profile import build_profile


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def artifact_set(directory: Path):
    context = load_json(FIXTURES / "design-context.json")
    points = load_json(FIXTURES / "test-points.json")
    manifest = load_json(FIXTURES / "valid-test-manifest.json")
    write_json(directory / "design-context.json", context)
    points["design_context_baseline"]["sha256"] = sha256_file(directory / "design-context.json")
    write_json(directory / "test-points.json", points)
    manifest["test_points_baseline"]["sha256"] = sha256_file(directory / "test-points.json")
    path = directory / "test-manifest.json"
    write_json(path, manifest)
    (directory / "test-cases.xlsx").write_bytes(render_case_workbook(manifest, sha256_file(path), module_paths(points), context))
    return context, points, manifest, path


def execution_set(directory: Path, suite="smoke", targets=None):
    _, _, manifest, manifest_path = artifact_set(directory)
    targets = targets or ["web-chrome"]
    run_dir = directory / "runs" / "synthetic-run"
    profile_path = run_dir / "execution-profile.json"
    profile = build_profile(manifest, manifest_path, profile_path, suite, targets)
    needs = {r["id"]: r for r in manifest["runtime_requirements"]}
    for binding in profile["bindings"]:
        req = needs[binding["requirement_id"]]
        binding.update(status="resolved", source=req["collection"])
        if req["sensitive"]:
            binding["session_ref"] = "synthetic-session-reference"
        else:
            binding["value"] = "synthetic:" + binding["requirement_id"]
    write_json(profile_path, profile)
    results = {"schema_version": "1.3", "run": {
        "run_id": "synthetic-run", "manifest_path": Path(os.path.relpath(manifest_path, run_dir)).as_posix(),
        "manifest_sha256": sha256_file(manifest_path), "case_workbook_sha256": sha256_file(directory / "test-cases.xlsx"),
        "execution_profile_path": "execution-profile.json", "execution_profile_sha256": sha256_file(profile_path),
        "suite": suite, "targets": targets, "environment": {"name": "Synthetic QA", "kind": "test", "build": "fixture"},
        "started_at": "2026-09-04T10:00:00+08:00", "finished_at": "2026-09-04T10:01:00+08:00",
    }, "results": []}
    for case in manifest["cases"]:
        if suite not in case["suite_membership"]:
            continue
        for target in case["applicable_targets"]:
            if target not in targets:
                continue
            auto = next(a for a in case["automation"] if a["target_id"] == target)
            result = {"case_id": case["id"], "target_id": target, "status": "passed", "attempts": 1, "tool": "synthetic-test-fixture", "assertions": [], "evidence": [], "observed": "Synthetic observations, not a product execution."}
            if auto["feasibility"] == "manual":
                result.update(status="not-run", attempts=0, blocker="manual-only")
            else:
                types = set(auto["required_evidence"])
                planned = [a for a in case["assertions"] if target in a["target_ids"]]
                types.update(t for a in planned for t in a["required_evidence"])
                for i, kind in enumerate(sorted(types), 1):
                    evidence = {"id": f"EV-{i}", "type": kind, "path": f"evidence/{case['id']}-{target}-{kind}.txt", "description": "Synthetic validator evidence"}
                    evidence_path = run_dir / evidence["path"]
                    evidence_path.parent.mkdir(parents=True, exist_ok=True)
                    evidence_path.write_text("Synthetic fixture only", encoding="utf-8")
                    evidence["sha256"] = sha256_file(evidence_path)
                    result["evidence"].append(evidence)
                for a in planned:
                    eid = "UI-" + a["id"]
                    evidence = {"id":eid, "type":"tool-output", "path":f"evidence/{case['id']}-{target}-{a['id']}.json", "description":"Synthetic UI output; not a real product run"}
                    record = {"format":"wewo-qa-ui-observation/1", "run_id":results["run"]["run_id"], "case_id":case["id"], "target_id":target, "attempt":1, "subject":"synthetic-account", "location":a["observation"], "captured_at":"2026-09-04T10:00:30+08:00", "tool":result["tool"], "raw":{"value":a["check"]["expected_value"]}}
                    write_json(run_dir / evidence["path"], record)
                    evidence["sha256"] = sha256_file(run_dir / evidence["path"])
                    linked = [e["id"] for e in result["evidence"] if e["type"] in a["required_evidence"]] + [eid]
                    result["evidence"].append(evidence)
                    result["assertions"].append({"assertion_id": a["id"], "description": a["description"], "expected": a["expected"], "actual": a["expected"], "status": "passed", "evidence_refs":linked, "observations":[{"attempt":1,"phase":"after","evidence_id":eid,"pointer":"/raw/value"}]})
            results["results"].append(result)
    result_path = run_dir / "execution-results.json"
    write_json(result_path, results)
    return manifest, manifest_path, profile, profile_path, results, result_path


def mutate_observation(result, assertion, run_dir, value):
    observation = assertion["observations"][-1]
    evidence = next(e for e in result["evidence"] if e["id"] == observation["evidence_id"])
    path = run_dir / evidence["path"]
    record = load_json(path)
    record["raw"]["value"] = value
    write_json(path, record)
    evidence["sha256"] = sha256_file(path)
