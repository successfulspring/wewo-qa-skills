"""Bind semantic review records to the actual tester-facing design being reviewed."""
from requirement_coverage import digest


def point_review_digest(points):
    return digest({k: v for k, v in points.items() if k not in {"generated_at", "design_review"}})


def point_review_errors(points, leaves):
    review = points["design_review"]
    errors = []
    if review.get("snapshot_sha256") != point_review_digest(points):
        errors.append("test-point semantic review is missing or stale for the visible tree")
    if set(review.get("checked_leaf_refs", [])) != set(leaves):
        errors.append("test-point review must inspect every leaf for atomicity and visible condition/action/outcome")
    if not all(review.get(k, "").strip() for k in ("atomicity_note", "visible_path_note")):
        errors.append("test-point review needs substantive atomicity and visible-path notes")
    return errors


def main():
    import argparse
    import json
    from pathlib import Path
    from artifact_tools import DESIGNER_SCHEMA_ROOT, ValidationFailure, load_json, schema_errors
    parser = argparse.ArgumentParser(description="Print current design review fingerprints; never performs or stamps a semantic review.")
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    data = load_json(args.artifact)
    is_manifest = isinstance(data, dict) and "cases" in data
    name = "test-manifest" if is_manifest else "test-points"
    errors = schema_errors(data, DESIGNER_SCHEMA_ROOT / (name + ".schema.json"))
    if errors:
        raise ValidationFailure(errors)
    result = {c["id"]: case_review_digest(data, c) for c in data["cases"]} if is_manifest else point_review_digest(data)
    print(json.dumps(result, ensure_ascii=False) if is_manifest else result)
    return 0


def case_review_digest(manifest, case):
    return digest({"case": case, "project": manifest["project"], "sources": manifest["sources"],
                   "decisions": manifest["decisions"], "test_points_baseline": manifest["test_points_baseline"],
                   "runtime_requirements": manifest["runtime_requirements"]})


def case_review_errors(manifest, *, final):
    if not final:
        return []
    errors = []
    reviews = manifest["review"].get("case_checks", [])
    cases = {c["id"]: c for c in manifest["cases"]}
    if len(reviews) != len(cases) or {r["case_id"] for r in reviews} != set(cases):
        errors.append("case review must walk every case's preparation, data, steps, oracles and suite rationale")
    for review in reviews:
        case = cases.get(review["case_id"])
        if case and review["snapshot_sha256"] != case_review_digest(manifest, case):
            errors.append(case["id"] + ": case walkthrough/oracle review is stale")
    baseline = manifest["test_points_baseline"]
    if not baseline.get("response_ref") or not baseline.get("response_text", "").strip():
        errors.append("test-point baseline needs the actual tester confirmation response and reference")
    return errors
