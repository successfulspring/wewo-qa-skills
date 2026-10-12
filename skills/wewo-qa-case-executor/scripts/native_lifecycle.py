"""Bind preparation, actual environment and cleanup to runner-produced events."""
from __future__ import annotations


def lifecycle_for(receipt, events, binding):
    from artifact_tools import _parse_datetime
    keys = ("case_id", "target_id", "test_id")
    selected = [e for e in events if isinstance(e, dict) and e.get("event") == "lifecycle" and
                all(e.get(k) == binding[k] for k in keys)]
    allowed = ("phase", "status", "detail", "captured_at", "entry", "build")
    records = []
    errors = []
    if [e.get("phase") for e in selected] != ["environment", "preparation", "cleanup"]:
        errors.append("missing, duplicate or unordered environment/preparation/cleanup observations")
    previous = receipt["started_at"]
    for event in selected:
        try:
            if event.get("run_id") != receipt["run_id"] or event.get("attempt") != 1:
                raise ValueError("wrong run or attempt")
            if not _parse_datetime(previous) <= _parse_datetime(event["captured_at"]) <= _parse_datetime(receipt["finished_at"]):
                raise ValueError("outside execution order/time")
            previous = event["captured_at"]
            if not isinstance(event.get("detail"), str) or not event["detail"].strip():
                raise ValueError("missing lifecycle detail")
            if event.get("phase") not in {"environment", "preparation", "cleanup"} or event.get("status") not in {"passed", "failed", "not-required"}:
                raise ValueError("invalid lifecycle phase or status")
            if any(k in event and not isinstance(event[k], str) for k in ("entry", "build")):
                raise ValueError("invalid environment metadata")
            records.append({k:event[k] for k in allowed if k in event})
        except (ValueError, KeyError, TypeError):
            errors.append("invalid lifecycle identity, detail or timing")
    by_phase = {e.get("phase"):e for e in records}
    actual = by_phase.get("environment", {})
    target = next((e for e in receipt.get("environments", []) if e["target_id"] == binding["target_id"]), {})
    if not target or actual.get("status") != "passed" or any(actual.get(k) != target.get(k) for k in ("entry", "build")):
        errors.append("actual target entry/build was not verified against the frozen profile")
    if by_phase.get("preparation", {}).get("status") != "passed":
        errors.append("case starting data/state was not prepared and verified")
    prepared = not errors
    if by_phase.get("cleanup", {}).get("status") not in {"passed", "not-required"}:
        errors.append("cleanup failed or was not verified")
    if receipt.get("asset_changes"):
        errors.append("test workspace assets changed during execution")
    return records, errors, prepared


def validate_lifecycle_result(receipt, events, binding, result):
    records, errors, prepared = lifecycle_for(receipt, events, binding)
    if result.get("lifecycle", []) != records:
        raise ValueError("result lifecycle differs from original runner events")
    if result["status"] == "passed" and errors:
        raise ValueError("incomplete execution lifecycle: " + "; ".join(errors))
    if any(a["status"] != "not-evaluated" for a in result["assertions"]) and not prepared:
        raise ValueError("business checks lack verified environment and preparation")
