"""Compare frozen black-box oracles with values in preserved UI tool output."""
from __future__ import annotations

from collections import Counter
import json

from jsonpointer import resolve_pointer, JsonPointerException
from numeric_values import finite_decimal as _number, decimal_sum

from artifact_tools import (
    EXECUTOR_SCHEMA_ROOT, ValidationFailure, _parse_datetime, _safe_evidence_path,
    load_json, schema_errors, sha256_file,
)


def _typed(value):
    # Type-sensitive JSON equality; unordered lists retain multiplicity.
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def check_errors(check):
    kind, errors = check["kind"], []
    if kind not in {"unchanged", "evidence-review"} and "expected_value" not in check:
        errors.append("comparison requires expected_value")
    if kind in {"unchanged", "evidence-review"} and "expected_value" in check:
        errors.append("comparison does not use expected_value")
    if kind == "evidence-review" and not check.get("criteria", "").strip():
        errors.append("evidence review requires objective criteria")
    if "expected_value" in check:
        expected = check["expected_value"]
        try:
            if kind in {"number-equals", "number-delta"}:
                _number(expected)
            elif kind == "contains" and (not isinstance(expected, str) or not expected):
                errors.append("contains requires nonempty text expected_value")
            elif kind == "unordered-equals" and not isinstance(expected, list):
                errors.append("unordered comparison requires a list expected_value")
            _typed(expected)
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def compare(check, after, before=None):
    kind = check["kind"]
    expected = check.get("expected_value")
    if kind == "equals":
        return _typed(after) == _typed(expected)
    if kind == "contains":
        if not isinstance(after, str):
            raise ValueError("contains observation must be text")
        return expected in after
    if kind == "number-equals":
        return _number(after) == _number(expected)
    if kind == "number-delta":
        return decimal_sum(_number(after), _number(before).copy_negate()) == _number(expected)
    if kind == "unordered-equals":
        if not isinstance(after, list):
            raise ValueError("unordered observation must be a list")
        return Counter(map(_typed, after)) == Counter(map(_typed, expected))
    if kind == "unchanged":
        return _typed(before) == _typed(after)
    if kind == "evidence-review":
        return None
    raise ValueError("unknown comparison")


def evaluate_observations(assertion, planned, evidence, run, result, base_dir, *, fill_actual=False):
    """Return per-attempt verdicts; never trust the agent-written actual/status."""
    if base_dir is None:
        raise ValueError("evaluated assertions require a run directory with original tool output")
    grouped = {}
    for observation in assertion["observations"]:
        attempt, phase = observation["attempt"], observation["phase"]
        if attempt > result["attempts"] or phase in grouped.setdefault(attempt, {}):
            raise ValueError("invalid or duplicate observation attempt/phase")
        item = evidence.get(observation["evidence_id"])
        if not item or item["type"] != "tool-output" or item["id"] not in assertion["evidence_refs"]:
            raise ValueError("observation requires linked tool-output evidence")
        path = _safe_evidence_path(base_dir, item["path"])
        if path is None or not path.is_file():
            raise ValueError("observation file missing or outside run directory")
        if sha256_file(path) != item["sha256"]:
            raise ValueError("observation evidence hash mismatch")
        record = load_json(path)
        if record.get("format") == "wewo-qa-native-observation/1":
            from native_execution import validate_native_observation
            validate_native_observation(record, base_dir, run, result, assertion["assertion_id"])
        errors = schema_errors(record, EXECUTOR_SCHEMA_ROOT / "ui-observation.schema.json")
        if errors:
            raise ValueError("invalid UI observation: " + "; ".join(errors))
        if any(record[k] != value for k, value in {"run_id":run["run_id"], "case_id":result["case_id"], "target_id":result["target_id"], "attempt":attempt, "tool":result["tool"]}.items()):
            raise ValueError("UI observation belongs to a different run/case/target/attempt/tool")
        captured = _parse_datetime(record["captured_at"])
        if not _parse_datetime(run["started_at"]) <= captured <= _parse_datetime(run["finished_at"]):
            raise ValueError("UI observation timestamp is outside this run")
        try:
            value = resolve_pointer(record, observation["pointer"])
        except JsonPointerException as exc:
            raise ValueError("observation pointer does not resolve in original tool output") from exc
        grouped[attempt][phase] = (value, record, observation["pointer"])
    required = {"after", "before"} if planned["check"]["kind"] in {"unchanged", "number-delta"} else {"after"}
    if set(grouped) != set(range(1, result["attempts"] + 1)):
        raise ValueError("evaluated assertion requires observations for every attempt")
    verdicts = []
    for attempt, phases in sorted(grouped.items()):
        if set(phases) != required:
            raise ValueError("observation phases do not match comparison requirements")
        before = phases.get("before")
        after = phases["after"]
        if before:
            if before[2] != after[2]:
                raise ValueError("before/after must extract the same field pointer")
            if any(before[1][k] != after[1][k] for k in ("subject", "location")):
                raise ValueError("before/after observations refer to different subjects or locations")
            if _parse_datetime(before[1]["captured_at"]) > _parse_datetime(after[1]["captured_at"]):
                raise ValueError("before observation occurs after after observation")
        verdicts.append(compare(planned["check"], after[0], before[0] if before else None))
    last = grouped[result["attempts"]]
    value = last["after"][0]
    actual = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    if "before" in last:
        actual = json.dumps({"before":last["before"][0], "after":value}, ensure_ascii=False, sort_keys=True)
    if fill_actual:
        assertion["actual"] = actual
    elif assertion["actual"] != actual:
        raise ValueError("actual text differs from preserved UI observation")
    if planned["check"]["kind"] == "evidence-review":
        judgments = assertion.get("judgments", [])
        if [j["attempt"] for j in judgments] != list(range(1, result["attempts"] + 1)):
            raise ValueError("evidence review requires a reasoned judgment for every attempt")
        verdicts = [j["status"] == "passed" for j in judgments]
    elif assertion.get("judgments"):
        raise ValueError("deterministic comparison cannot be replaced with agent judgments")
    return verdicts
