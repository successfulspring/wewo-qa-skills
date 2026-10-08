"""Derive recorded verdicts from preserved UI output; does not operate the product."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from artifact_tools import (
    RESULTS_SCHEMA_PATH, ValidationFailure, load_json, schema_errors,
    validate_manifest_file, validate_results_file, write_text_atomic,
)
from observation_checks import evaluate_observations


def judge(results, manifest, base_dir):
    candidate = copy.deepcopy(results)
    cases = {c["id"]:c for c in manifest["cases"]}
    for result in candidate["results"]:
        if result["attempts"] == 0:
            continue
        case = cases.get(result["case_id"])
        if case is None:
            raise ValidationFailure(["unknown case in observations"])
        planned = {a["id"]:a for a in case["assertions"] if result["target_id"] in a["target_ids"]}
        evidence = {e["id"]:e for e in result["evidence"]}
        evaluated = []
        for assertion in result["assertions"]:
            if assertion["status"] == "not-evaluated":
                continue
            original = planned.get(assertion["assertion_id"])
            if original is None or assertion["expected"] != original["expected"]:
                raise ValidationFailure(["unknown assertion or changed frozen oracle"])
            verdicts = evaluate_observations(assertion, original, evidence, candidate["run"], result, base_dir, fill_actual=True)
            assertion["status"] = "passed" if all(verdicts) else "failed"
            evaluated.append(verdicts)
        complete = len(evaluated) == len(planned) and set(a["assertion_id"] for a in result["assertions"]) == set(planned)
        attempts_passed = [all(v[i] for v in evaluated) for i in range(result["attempts"])] if complete else []
        if attempts_passed and any(attempts_passed) and not all(attempts_passed):
            result.update(status="flaky", failure_reason="Preserved equivalent attempts include both passing and failing outcomes; investigate cause.")
        elif any(a["status"] == "failed" for a in result["assertions"]):
            result.update(status="failed", failure_reason="Preserved UI observation differs from the frozen check; inspect linked evidence.")
        elif complete and all(attempts_passed):
            result["status"] = "passed"
            result.pop("failure_reason", None)
            result.pop("blocker", None)
        else:
            result.update(status="blocked", blocker=result.get("blocker", "Required checks were interrupted or not evaluated."))
    return candidate


def main():
    parser = argparse.ArgumentParser(description="Compare frozen checks with preserved UI observations; no product actions.")
    parser.add_argument("results", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source, manifest_path = args.results.resolve(), args.manifest.resolve()
    output = args.output.resolve() if args.output else source.with_name("execution-results.judged.json")
    if output.parent != source.parent or output.suffix != ".json" or output == source or output.name == "execution-profile.json":
        raise ValidationFailure(["judged output must be a separate JSON file in the same run directory"])
    if output.exists():
        raise ValidationFailure(["judged output already exists; choose another name to preserve evidence"])
    results = load_json(source)
    errors = schema_errors(results, RESULTS_SCHEMA_PATH)
    if errors:
        raise ValidationFailure(errors)
    manifest = validate_manifest_file(manifest_path)
    candidate = judge(results, manifest, source.parent)
    # Validate before publishing a candidate; use an ephemeral file alongside the run
    # so relative evidence/profile paths resolve under the normal validator.
    import tempfile
    with tempfile.NamedTemporaryFile(prefix=".judge-", suffix=".json", dir=source.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        write_text_atomic(temporary, json.dumps(candidate, ensure_ascii=False, indent=2) + "\n")
        validate_results_file(temporary, manifest_path)
        write_text_atomic(output, json.dumps(candidate, ensure_ascii=False, indent=2) + "\n")
    finally:
        temporary.unlink(missing_ok=True)
    print(f"WROTE: {output}")
    return 0
