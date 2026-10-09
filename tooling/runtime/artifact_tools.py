from __future__ import annotations
from artifact_layout import case_workbook_path

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


if getattr(sys, "frozen", False):
    # PyInstaller expands bundled schemas under its private runtime directory.
    PLUGIN_ROOT = Path(getattr(sys, "_MEIPASS")).resolve()
else:
    PLUGIN_ROOT = Path(__file__).resolve().parents[2]

DESIGNER_SCHEMA_ROOT = (
    PLUGIN_ROOT / "skills" / "wewo-qa-case-designer" / "references" / "schemas"
)
EXECUTOR_SCHEMA_ROOT = (
    PLUGIN_ROOT / "skills" / "wewo-qa-case-executor" / "references" / "schemas"
)
TEST_POINTS_SCHEMA_PATH = DESIGNER_SCHEMA_ROOT / "test-points.schema.json"
MANIFEST_SCHEMA_PATH = DESIGNER_SCHEMA_ROOT / "test-manifest.schema.json"
RESULTS_SCHEMA_PATH = EXECUTOR_SCHEMA_ROOT / "execution-results.schema.json"
EXECUTION_PROFILE_SCHEMA_PATH = EXECUTOR_SCHEMA_ROOT / "execution-profile.schema.json"


class ValidationFailure(ValueError):
    def __init__(self, errors: Iterable[str]):
        self.errors = list(errors)
        super().__init__("\n".join(self.errors))


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    try:
        def reject_constant(value):
            raise ValueError("non-finite JSON constant: " + value)
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys, parse_constant=reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValidationFailure([f"{path}: cannot read valid UTF-8 JSON: {exc}"]) from exc


def load_schema(path: Path) -> dict[str, Any]:
    schema = load_json(path)
    Draft202012Validator.check_schema(schema)
    return schema


def schema_errors(instance: Any, schema_path: Path) -> list[str]:
    validator = Draft202012Validator(load_schema(schema_path), format_checker=FormatChecker())
    errors: list[str] = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"{location}: {error.message}")
    return errors


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicate: set[str] = set()
    for value in values:
        if value in seen:
            duplicate.add(value)
        seen.add(value)
    return duplicate


def _root_reference(reference: str) -> str:
    return reference.split("#", 1)[0]


def walk_test_points(root: dict[str, Any]) -> Iterable[dict[str, Any]]:
    yield root
    for child in root["children"]:
        yield from walk_test_points(child)


def validate_test_points_data(test_points: Any, context: dict[str, Any] | None = None, *, final: bool = True) -> None:
    errors = schema_errors(test_points, TEST_POINTS_SCHEMA_PATH)
    if errors or not isinstance(test_points, dict):
        raise ValidationFailure(errors or ["$: test points must be an object"])

    sources = test_points["sources"]
    decisions = test_points["decisions"]
    targets = test_points["project"]["targets"]
    units = test_points["requirement_units"]
    nodes = list(walk_test_points(test_points["tree"]))

    for label, values in (
        ("source", [item["id"] for item in sources]),
        ("decision", [item["id"] for item in decisions]),
        ("target", [item["id"] for item in targets]),
        ("requirement unit", [item["id"] for item in units]),
        ("test point", [item["id"] for item in nodes]),
    ):
        for duplicate in sorted(_duplicates(values)):
            errors.append(f"duplicate {label} id: {duplicate}")

    source_ids = {item["id"] for item in sources}
    decision_ids = {item["id"] for item in decisions}
    unit_by_id = {item["id"]: item for item in units}

    for unit in units:
        unit_id = unit["id"]
        for source_ref in unit["source_refs"]:
            if _root_reference(source_ref) not in source_ids:
                errors.append(f"{unit_id}: unknown source reference {source_ref}")
        if unit["status"] == "assumed" and not unit.get("assumptions"):
            errors.append(f"{unit_id}: assumed unit requires at least one disclosed assumption")
        if unit["status"] == "excluded" and not unit.get("exclusion_reason", "").strip():
            errors.append(f"{unit_id}: excluded unit requires exclusion_reason")

    for decision in decisions:
        decision_id = decision["id"]
        if decision["unit_id"] not in unit_by_id:
            errors.append(f"{decision_id}: unknown requirement unit {decision['unit_id']}")
        if decision["status"] == "assumed" and not decision.get("rationale", "").strip():
            errors.append(f"{decision_id}: assumed decision requires rationale")

    root = test_points["tree"]
    if root["id"] != "TP-ROOT" or root["kind"] != "root":
        errors.append("test-point tree root must use id TP-ROOT and kind root")

    referenced_units: set[str] = set()
    leaf_count = 0
    for node in nodes:
        node_id = node["id"]
        if not node["children"]:
            leaf_count += 1
        if node is root:
            continue
        if node["kind"] == "root" or node_id == "TP-ROOT":
            errors.append(f"{node_id}: only the tree root may use root identity or kind")
        if not node["requirement_unit_refs"]:
            errors.append(f"{node_id}: non-root test point requires a requirement-unit reference")
        if not node["trace_refs"]:
            errors.append(f"{node_id}: non-root test point requires a source or decision reference")
        if node["status"] == "assumed" and not node.get("rationale", "").strip():
            errors.append(f"{node_id}: assumed test point requires rationale")
        for unit_id in node["requirement_unit_refs"]:
            unit = unit_by_id.get(unit_id)
            if unit is None:
                errors.append(f"{node_id}: unknown requirement unit {unit_id}")
            elif unit["status"] == "excluded":
                errors.append(f"{node_id}: excluded requirement unit {unit_id} cannot produce test points")
            else:
                referenced_units.add(unit_id)
        for trace_ref in node["trace_refs"]:
            root_ref = _root_reference(trace_ref)
            if root_ref not in source_ids and root_ref not in decision_ids:
                errors.append(f"{node_id}: unknown source or decision reference {trace_ref}")

    if leaf_count == 0:
        errors.append("test-point tree requires at least one leaf")
    for unit in units:
        if final and unit["status"] != "excluded" and unit["id"] not in referenced_units:
            errors.append(f"{unit['id']}: included requirement unit is not represented in the test-point tree")

    if context is not None:
        from design_context import validate_design_context_data
        validate_design_context_data(context, final=final)
        if any(context["project"][key] != test_points["project"][key] for key in ("name", "artifact_id")):
            errors.append("design context project does not match test points")
        context_sources = {item["id"]: item for item in context["sources"]}
        if set(context_sources) != source_ids:
            errors.append("design context source IDs do not match test points")
        for source in sources:
            original = context_sources.get(source["id"], {})
            if any(original.get(key) != value for key, value in source.items()):
                errors.append(f"{source['id']}: source metadata differs from design context")
        if context["decisions"] != decisions:
            errors.append("test-point decisions differ from design context")
        rules = {item["id"]: item for item in context["rules"]}
        leaves = {node["id"]: node for node in nodes if not node["children"]}
        from design_methods import derivation_links
        errors.extend(derivation_links(context, leaves, final=final))
        anchors = {f"{s['source_id']}#{s['anchor']}" for s in context["segments"] if s["read_status"] == "read" and s["disposition"] != "excluded"}
        included_sources = {s["id"] for s in context["sources"] if s["scope"] == "included"}
        for node in nodes:
            for trace in node["trace_refs"]:
                if trace.startswith("SRC-") and _root_reference(trace) not in included_sources:
                    errors.append(f"{node['id']}: trace references excluded source {trace}")
                if trace.startswith("SRC-") and "#" in trace and trace not in anchors:
                    errors.append(f"{node['id']}: source anchor is not inventoried: {trace}")
            for rid in node.get("rule_refs", []):
                if rid not in rules or rules[rid]["status"] == "excluded":
                    errors.append(f"{node['id']}: unknown or excluded business rule {rid}")
        covered_rules: set[str] = set()
        for rule in rules.values():
            for dimension in rule["coverage"]:
                for pid in dimension["test_point_refs"]:
                    if pid not in leaves:
                        errors.append(f"{rule['id']}: coverage references unknown or non-leaf point {pid}")
                    elif rule["id"] not in leaves[pid].get("rule_refs", []):
                        errors.append(f"{pid}: coverage rule is not referenced by leaf {rule['id']}")
                    else:
                        covered_rules.add(rule["id"])
            if final and rule["status"] != "excluded" and rule["id"] not in covered_rules:
                errors.append(f"{rule['id']}: included business rule has no leaf coverage")
        coverage_pairs = {(r["id"], p) for r in rules.values() for d in r["coverage"] for p in d["test_point_refs"]}
        for pid, leaf in leaves.items():
            for rid in leaf.get("rule_refs", []):
                if final and (rid, pid) not in coverage_pairs:
                    errors.append(f"{pid}: leaf is absent from rule coverage {rid}")

    if errors:
        raise ValidationFailure(errors)


def validate_test_points_file(path: Path, *, final: bool = True) -> dict[str, Any]:
    test_points = load_json(path)
    validate_test_points_data(test_points, final=final)
    from design_context import validate_design_context_file
    context_path = path.parent / test_points["design_context_baseline"]["path"]
    if not context_path.is_file() or sha256_file(context_path) != test_points["design_context_baseline"]["sha256"]:
        raise ValidationFailure(["design_context_baseline.sha256 does not match adjacent design-context.json"])
    context = validate_design_context_file(context_path, final=final)
    validate_test_points_data(test_points, context, final=final)
    return test_points


def validate_manifest_data(manifest: Any, test_points: dict[str, Any] | None = None, *, final: bool = True) -> None:
    errors = schema_errors(manifest, MANIFEST_SCHEMA_PATH)
    if errors or not isinstance(manifest, dict):
        raise ValidationFailure(errors or ["$: manifest must be an object"])

    sources = manifest["sources"]
    decisions = manifest["decisions"]
    targets = manifest["project"]["targets"]
    runtime_requirements = manifest["runtime_requirements"]
    cases = manifest["cases"]

    for label, values in (
        ("source", [item["id"] for item in sources]),
        ("decision", [item["id"] for item in decisions]),
        ("target", [item["id"] for item in targets]),
        ("runtime requirement", [item["id"] for item in runtime_requirements]),
        ("case", [item["id"] for item in cases]),
    ):
        for duplicate in sorted(_duplicates(values)):
            errors.append(f"duplicate {label} id: {duplicate}")

    source_ids = {item["id"] for item in sources}
    decision_ids = {item["id"] for item in decisions}
    target_by_id = {item["id"]: item for item in targets}
    runtime_requirement_by_id = {item["id"]: item for item in runtime_requirements}
    case_ids = {item["id"] for item in cases}

    from design_methods import review_errors
    errors.extend(review_errors(manifest["review"], final=final))
    if final and (manifest["review"]["status"] != "confirmed" or not manifest["review"].get("reviewed_at")):
        errors.append("case design review is pending; reconcile Excel edits and review before execution")

    for requirement in runtime_requirements:
        requirement_id = requirement["id"]
        target_ids = requirement.get("target_ids", [])
        if requirement["scope"] != "target" and target_ids:
            errors.append(f"{requirement_id}: only target-scoped requirements may declare target_ids")
        for target_id in target_ids:
            target = target_by_id.get(target_id)
            if target is None:
                errors.append(f"{requirement_id}: unknown target {target_id}")
            elif not target["in_scope"]:
                errors.append(f"{requirement_id}: out-of-scope target {target_id} cannot require runtime input")
        if requirement["kind"] == "credential" and not requirement["sensitive"]:
            errors.append(f"{requirement_id}: credential requirements must be sensitive")
        if requirement["sensitive"] and requirement["collection"] not in {"secret-reference", "authenticated-session"}:
            errors.append(
                f"{requirement_id}: sensitive requirements must use secret-reference or authenticated-session collection"
            )
        if not requirement["sensitive"] and requirement["collection"] in {"secret-reference", "authenticated-session"}:
            errors.append(f"{requirement_id}: secret/session collection requires sensitive=true")

    leaf_test_point_ids: set[str] = set()
    if test_points is not None:
        validate_test_points_data(test_points)
        for key in ("name", "artifact_id", "requirement", "baseline"):
            if manifest["project"][key] != test_points["project"][key]:
                errors.append(f"project.{key} does not match test-points.json")
        if {item["id"] for item in sources} != {item["id"] for item in test_points["sources"]}:
            errors.append("manifest source IDs do not match test-points.json")
        if {item["id"] for item in decisions} != {item["id"] for item in test_points["decisions"]}:
            errors.append("manifest decision IDs do not match test-points.json")
        if {item["id"] for item in targets} != {item["id"] for item in test_points["project"]["targets"]}:
            errors.append("manifest target IDs do not match test-points.json")
        point_sources = {item["id"]: item for item in test_points["sources"]}
        for source in sources:
            if point_sources.get(source["id"]) != source:
                errors.append(f"{source['id']}: manifest source differs from test-points.json")
        point_decisions = {item["id"]: item for item in test_points["decisions"]}
        for decision in decisions:
            baseline_decision = point_decisions.get(decision["id"], {})
            for key in ("topic", "resolution", "status", "rationale"):
                if decision.get(key) != baseline_decision.get(key):
                    errors.append(f"{decision['id']}: manifest decision.{key} differs from test-points.json")
        point_targets = {item["id"]: item for item in test_points["project"]["targets"]}
        for target in targets:
            if point_targets.get(target["id"]) != target:
                errors.append(f"{target['id']}: manifest target differs from test-points.json")
        leaf_test_point_ids = {
            node["id"] for node in walk_test_points(test_points["tree"]) if not node["children"]
        }

    for decision in decisions:
        if decision["status"] == "assumed" and not decision.get("rationale", "").strip():
            errors.append(f"{decision['id']}: assumed decision requires rationale")

    for case in cases:
        case_id = case["id"]
        common_runtime_refs = set(case["runtime_requirement_refs"])
        suites = set(case["suite_membership"])
        if "full" not in suites:
            errors.append(f"{case_id}: every case must belong to full")
        if "smoke" in suites and "regression" not in suites:
            errors.append(f"{case_id}: smoke membership requires regression membership")
        if "regression" in suites and "full" not in suites:
            errors.append(f"{case_id}: regression membership requires full membership")

        for source_ref in case["source_refs"]:
            root_ref = _root_reference(source_ref)
            if root_ref not in source_ids and root_ref not in decision_ids:
                errors.append(f"{case_id}: unknown source or decision reference {source_ref}")

        for requirement_id in case["runtime_requirement_refs"]:
            requirement = runtime_requirement_by_id.get(requirement_id)
            if requirement is None:
                errors.append(f"{case_id}: unknown runtime requirement {requirement_id}")
            elif requirement["scope"] == "target":
                errors.append(
                    f"{case_id}: target-scoped runtime requirement {requirement_id} must be referenced by an automation target"
                )

        if test_points is not None:
            for test_point_ref in case["test_point_refs"]:
                if test_point_ref not in leaf_test_point_ids:
                    errors.append(f"{case_id}: unknown or non-leaf test point reference {test_point_ref}")

        applicable = set(case["applicable_targets"])
        for target_id in sorted(applicable):
            target = target_by_id.get(target_id)
            if target is None:
                errors.append(f"{case_id}: unknown applicable target {target_id}")
            elif not target["in_scope"]:
                errors.append(f"{case_id}: out-of-scope target {target_id} cannot be applicable")

        automation_ids = [item["target_id"] for item in case["automation"]]
        for duplicate in sorted(_duplicates(automation_ids)):
            errors.append(f"{case_id}: duplicate automation assessment for {duplicate}")
        automation_set = set(automation_ids)
        if automation_set != applicable:
            missing = sorted(applicable - automation_set)
            extra = sorted(automation_set - applicable)
            if missing:
                errors.append(f"{case_id}: missing automation assessment for {', '.join(missing)}")
            if extra:
                errors.append(f"{case_id}: automation assessment has non-applicable target(s) {', '.join(extra)}")

        assertions = {item["id"]: item for item in case["assertions"]}
        for duplicate in sorted(_duplicates(item["id"] for item in case["assertions"])):
            errors.append(f"{case_id}: duplicate planned assertion {duplicate}")
        used_assertions = {aid for step in case["steps"] for aid in step["assertion_refs"]}
        for aid in used_assertions - set(assertions):
            errors.append(f"{case_id}: step references unknown assertion {aid}")
        for aid in set(assertions) - used_assertions:
            errors.append(f"{case_id}: planned assertion is not assigned to a step: {aid}")
        asserted_points = {pid for a in assertions.values() for pid in a["test_point_refs"]}
        if asserted_points != set(case["test_point_refs"]):
            errors.append(f"{case_id}: planned assertions must exactly cover case test-point references")
        for assertion in assertions.values():
            from observation_checks import check_errors
            errors.extend(f"{case_id}/{assertion['id']}: {e}" for e in check_errors(assertion["check"]))
            if not set(assertion["target_ids"]) <= applicable:
                errors.append(f"{case_id}/{assertion['id']}: assertion has non-applicable target")
        for target_id in applicable:
            target_points = {pid for a in assertions.values() if target_id in a["target_ids"] for pid in a["test_point_refs"]}
            if target_points != set(case["test_point_refs"]):
                errors.append(f"{case_id}/{target_id}: each target requires planned assertions for every case test point")

        for automation in case["automation"]:
            feasibility = automation["feasibility"]
            route = automation["candidate_route"]
            target_id = automation["target_id"]
            for requirement_id in automation["runtime_requirement_refs"]:
                requirement = runtime_requirement_by_id.get(requirement_id)
                if requirement is None:
                    errors.append(f"{case_id}/{target_id}: unknown runtime requirement {requirement_id}")
                elif requirement["scope"] == "target" and target_id not in requirement.get("target_ids", []):
                    errors.append(
                        f"{case_id}/{target_id}: runtime requirement {requirement_id} does not apply to this target"
                    )
            if feasibility == "manual" and route != "none":
                errors.append(f"{case_id}/{target_id}: manual assessment must use route none")
            if feasibility != "manual" and route == "none":
                errors.append(f"{case_id}/{target_id}: {feasibility} assessment requires an execution route")
            if feasibility == "conditional" and not (common_runtime_refs or automation["runtime_requirement_refs"]):
                errors.append(f"{case_id}/{target_id}: conditional automation requires a structured runtime requirement")

        safety = case["safety"]
        if safety["impact"] in {"irreversible", "external"} and not safety["requires_confirmation"]:
            errors.append(f"{case_id}: {safety['impact']} impact requires confirmation")

        variant_of = case.get("variant_of")
        if variant_of:
            if variant_of == case_id:
                errors.append(f"{case_id}: variant_of cannot reference itself")
            elif variant_of not in case_ids:
                errors.append(f"{case_id}: variant_of references unknown case {variant_of}")

    if test_points is not None:
        covered_test_points = {ref for case in cases for ref in case["test_point_refs"]}
        for test_point_id in sorted(leaf_test_point_ids - covered_test_points):
            errors.append(f"{test_point_id}: leaf test point is not covered by any case")

    referenced_runtime_requirements = {
        requirement_id
        for case in cases
        for requirement_id in (
            case["runtime_requirement_refs"]
            + [
                ref
                for automation in case["automation"]
                for ref in automation["runtime_requirement_refs"]
            ]
        )
    }
    for requirement_id in sorted(set(runtime_requirement_by_id) - referenced_runtime_requirements):
        errors.append(f"{requirement_id}: runtime requirement is not referenced by any case or target assessment")

    if errors:
        raise ValidationFailure(errors)


def validate_manifest_file(path: Path, *, final: bool = True) -> dict[str, Any]:
    manifest = load_json(path)
    validate_manifest_data(manifest, final=final)
    baseline = manifest["test_points_baseline"]
    test_points_path = (path.parent / baseline["path"]).resolve()
    try:
        test_points_path.relative_to(path.parent.resolve())
    except ValueError as exc:
        raise ValidationFailure(["test_points_baseline.path escapes the artifact directory"]) from exc
    if not test_points_path.is_file():
        raise ValidationFailure([f"test-point baseline does not exist: {test_points_path}"])
    if sha256_file(test_points_path) != baseline["sha256"]:
        raise ValidationFailure(["test_points_baseline.sha256 does not match test-points.json"])
    test_points = validate_test_points_file(test_points_path)
    validate_manifest_data(manifest, test_points, final=final)
    context = load_json(path.parent / "design-context.json")
    anchors = {f"{s['source_id']}#{s['anchor']}" for s in context["segments"] if s["read_status"] == "read" and s["disposition"] != "excluded"}
    included_sources = {s["id"] for s in context["sources"] if s["scope"] == "included"}
    errors = []
    for case in manifest["cases"]:
        for reference in case["source_refs"]:
            if reference.startswith("SRC-") and (_root_reference(reference) not in included_sources or ("#" in reference and reference not in anchors)):
                errors.append(f"{case['id']}: case source anchor is unread, excluded or not inventoried: {reference}")
    if errors:
        raise ValidationFailure(errors)
    return manifest


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _safe_evidence_path(base_dir: Path, relative_path: str) -> Path | None:
    candidate = (base_dir / relative_path).resolve()
    base = base_dir.resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    return candidate


def runtime_requirement_ids_for_pair(manifest: dict[str, Any], case: dict[str, Any], target_id: str) -> set[str]:
    automation = next(item for item in case["automation"] if item["target_id"] == target_id)
    return set(case["runtime_requirement_refs"]) | set(automation["runtime_requirement_refs"])


def expected_runtime_requirement_ids(manifest: dict[str, Any], suite: str, targets: Iterable[str]) -> set[str]:
    selected_targets = set(targets)
    requirement_ids: set[str] = set()
    for case in manifest["cases"]:
        if suite not in case["suite_membership"]:
            continue
        for target_id in set(case["applicable_targets"]) & selected_targets:
            automation = next(item for item in case["automation"] if item["target_id"] == target_id)
            if automation["feasibility"] != "manual":
                requirement_ids.update(runtime_requirement_ids_for_pair(manifest, case, target_id))
    return requirement_ids


def validate_execution_profile_data(
    profile: Any,
    manifest: dict[str, Any],
    manifest_path: Path,
) -> None:
    errors = schema_errors(profile, EXECUTION_PROFILE_SCHEMA_PATH)
    if errors or not isinstance(profile, dict):
        raise ValidationFailure(errors or ["$: execution profile must be an object"])

    if profile["manifest_sha256"] != sha256_file(manifest_path):
        errors.append("manifest_sha256 does not match the supplied manifest")
    workbook_path = case_workbook_path(manifest_path, profile["suite"])
    if not workbook_path.is_file() or profile["case_workbook_sha256"] != sha256_file(workbook_path):
        errors.append("case_workbook_sha256 does not match selected suite workbook")

    target_by_id = {item["id"]: item for item in manifest["project"]["targets"]}
    for target_id in profile["targets"]:
        target = target_by_id.get(target_id)
        if target is None:
            errors.append(f"execution profile references unknown target {target_id}")
        elif not target["in_scope"]:
            errors.append(f"execution profile references out-of-scope target {target_id}")

    expected_ids = expected_runtime_requirement_ids(manifest, profile["suite"], profile["targets"])
    binding_ids = [item["requirement_id"] for item in profile["bindings"]]
    for duplicate in sorted(_duplicates(binding_ids)):
        errors.append(f"duplicate runtime binding: {duplicate}")
    actual_ids = set(binding_ids)
    for requirement_id in sorted(expected_ids - actual_ids):
        errors.append(f"missing runtime binding for {requirement_id}")
    for requirement_id in sorted(actual_ids - expected_ids):
        errors.append(f"unexpected runtime binding for {requirement_id}")

    requirement_by_id = {item["id"]: item for item in manifest["runtime_requirements"]}
    for binding in profile["bindings"]:
        requirement_id = binding["requirement_id"]
        requirement = requirement_by_id.get(requirement_id)
        if requirement is None:
            continue
        status = binding["status"]
        if status == "resolved":
            if not binding.get("source"):
                errors.append(f"{requirement_id}: resolved binding requires source")
            if requirement["sensitive"]:
                if binding.get("value"):
                    errors.append(f"{requirement_id}: sensitive value must not be stored in execution-profile.json")
                if not (binding.get("secret_ref") or binding.get("session_ref")):
                    errors.append(f"{requirement_id}: resolved sensitive binding requires secret_ref or session_ref")
                if binding.get("source") not in {"secret-reference", "authenticated-session"}:
                    errors.append(f"{requirement_id}: sensitive binding source must be secret-reference or authenticated-session")
            else:
                if not binding.get("value"):
                    errors.append(f"{requirement_id}: resolved non-sensitive binding requires value")
                if binding.get("secret_ref") or binding.get("session_ref"):
                    errors.append(f"{requirement_id}: non-sensitive binding must not use secret_ref or session_ref")
        else:
            if binding.get("value") or binding.get("secret_ref") or binding.get("session_ref"):
                errors.append(f"{requirement_id}: unresolved binding must not contain a value or reference")
            if status == "unavailable" and not binding.get("notes"):
                errors.append(f"{requirement_id}: unavailable binding requires notes")

    if errors:
        raise ValidationFailure(errors)


def validate_execution_profile_file(
    profile_path: Path,
    manifest_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = validate_manifest_file(manifest_path)
    from case_workbook import validate_case_workbooks
    validate_case_workbooks(manifest_path)
    profile = load_json(profile_path)
    validate_execution_profile_data(profile, manifest, manifest_path)
    referenced_manifest = (profile_path.parent / profile["manifest_path"]).resolve()
    if referenced_manifest != manifest_path.resolve():
        raise ValidationFailure(["manifest_path in execution profile does not resolve to the supplied manifest"])
    return profile, manifest


def validate_results_data(
    results: Any,
    manifest: dict[str, Any],
    manifest_path: Path,
    evidence_base_dir: Path | None = None,
    execution_profile: dict[str, Any] | None = None,
) -> None:
    errors = schema_errors(results, RESULTS_SCHEMA_PATH)
    if errors or not isinstance(results, dict):
        raise ValidationFailure(errors or ["$: execution results must be an object"])

    run = results["run"]
    if run["manifest_sha256"] != sha256_file(manifest_path):
        errors.append("run.manifest_sha256 does not match the supplied manifest")
    workbook_path = case_workbook_path(manifest_path, run["suite"])
    if not workbook_path.is_file() or run["case_workbook_sha256"] != sha256_file(workbook_path):
        errors.append("run.case_workbook_sha256 does not match selected suite workbook")

    try:
        if _parse_datetime(run["finished_at"]) < _parse_datetime(run["started_at"]):
            errors.append("run.finished_at precedes run.started_at")
    except ValueError:
        pass

    target_by_id = {item["id"]: item for item in manifest["project"]["targets"]}
    run_targets = set(run["targets"])
    for target_id in sorted(run_targets):
        target = target_by_id.get(target_id)
        if target is None:
            errors.append(f"run references unknown target {target_id}")
        elif not target["in_scope"]:
            errors.append(f"run references out-of-scope target {target_id}")

    if execution_profile is not None:
        if execution_profile["suite"] != run["suite"]:
            errors.append("execution profile suite does not match result run")
        if set(execution_profile["targets"]) != run_targets:
            errors.append("execution profile targets do not match result run")
        if execution_profile["case_workbook_sha256"] != run["case_workbook_sha256"]:
            errors.append("execution profile workbook does not match result run")
        binding_status = {item["requirement_id"]: item["status"] for item in execution_profile["bindings"]}
    else:
        binding_status = {}

    selected_cases = [case for case in manifest["cases"] if run["suite"] in case["suite_membership"]]
    expected_pairs = {
        (case["id"], target_id)
        for case in selected_cases
        for target_id in case["applicable_targets"]
        if target_id in run_targets
    }

    result_pairs = [(item["case_id"], item["target_id"]) for item in results["results"]]
    for duplicate in sorted(_duplicates(f"{case_id}\0{target_id}" for case_id, target_id in result_pairs)):
        case_id, target_id = duplicate.split("\0", 1)
        errors.append(f"duplicate result for {case_id}/{target_id}")
    actual_pairs = set(result_pairs)
    for case_id, target_id in sorted(expected_pairs - actual_pairs):
        errors.append(f"missing result for {case_id}/{target_id}")
    for case_id, target_id in sorted(actual_pairs - expected_pairs):
        errors.append(f"unexpected result for {case_id}/{target_id}")

    case_by_id = {case["id"]: case for case in manifest["cases"]}
    for result in results["results"]:
        case_id = result["case_id"]
        target_id = result["target_id"]
        status = result["status"]
        case = case_by_id.get(case_id)
        if case is None:
            continue
        automation = next((item for item in case["automation"] if item["target_id"] == target_id), None)
        if automation is None:
            continue

        if execution_profile is not None and status in {"passed", "failed", "flaky"}:
            unresolved = sorted(
                requirement_id
                for requirement_id in runtime_requirement_ids_for_pair(manifest, case, target_id)
                if binding_status.get(requirement_id) != "resolved"
            )
            if unresolved:
                errors.append(
                    f"{case_id}/{target_id}: executed result has unresolved runtime requirement(s) {', '.join(unresolved)}"
                )

        if automation["feasibility"] == "manual":
            if status != "not-run" or result["attempts"] != 0:
                errors.append(f"{case_id}/{target_id}: manual case must be not-run with zero attempts")
            if "manual" not in result.get("blocker", "").lower():
                errors.append(f"{case_id}/{target_id}: manual not-run result must identify manual-only blocker")

        planned = {a["id"]: a for a in case["assertions"] if target_id in a["target_ids"]}
        submitted = [a["assertion_id"] for a in result["assertions"]]
        for aid in sorted(_duplicates(submitted)):
            errors.append(f"{case_id}/{target_id}: duplicate result assertion {aid}")
        if status in {"passed", "failed", "flaky"} or result["attempts"] > 0:
            for aid in sorted(set(planned) - set(submitted)):
                errors.append(f"{case_id}/{target_id}: missing required assertion {aid}")
        for aid in sorted(set(submitted) - set(planned)):
            errors.append(f"{case_id}/{target_id}: unknown or inapplicable assertion {aid}")
        evidence_by_id = {e["id"]: e for e in result["evidence"]}
        if result.get("native_test") and evidence_base_dir is not None:
            link = result["native_test"]
            receipt_path = _safe_evidence_path(evidence_base_dir, link["receipt_path"])
            if receipt_path is None or not receipt_path.is_file() or sha256_file(receipt_path) != link["receipt_sha256"]:
                errors.append(f"{case_id}/{target_id}: native receipt missing or changed")
            else:
                receipt = load_json(receipt_path)
                native_binding = [b for b in receipt["bindings"] if (b["case_id"], b["target_id"]) == (case_id,target_id)]
                if len(native_binding) != 1 or any(link[k] != native_binding[0][k] for k in ("asset","test_id","route")) or receipt["run_id"] != run["run_id"]:
                    errors.append(f"{case_id}/{target_id}: native mapping differs from the execution receipt")
                if status == "passed":
                    for a in result["assertions"]:
                        for observation in a["observations"]:
                            e = evidence_by_id.get(observation["evidence_id"])
                            p = _safe_evidence_path(evidence_base_dir,e["path"]) if e else None
                            if p is None or not p.is_file() or load_json(p).get("format") != "wewo-qa-native-observation/1":
                                errors.append(f"{case_id}/{target_id}: native passed case requires runner-produced observations")
        attempt_verdicts = []
        for eid in sorted(_duplicates(e["id"] for e in result["evidence"])):
            errors.append(f"{case_id}/{target_id}: duplicate evidence id {eid}")
        for assertion in result["assertions"]:
            aid = assertion["assertion_id"]
            expected_assertion = planned.get(aid)
            if expected_assertion is None:
                continue
            if assertion["expected"] != expected_assertion["expected"]:
                errors.append(f"{case_id}/{target_id}/{aid}: expected value differs from planned oracle")
            for eid in assertion["evidence_refs"]:
                if eid not in evidence_by_id:
                    errors.append(f"{case_id}/{target_id}/{aid}: unknown evidence {eid}")
            if assertion["status"] == "not-evaluated":
                if not assertion.get("reason"):
                    errors.append(f"{case_id}/{target_id}/{aid}: unevaluated assertion requires reason")
            else:
                if not assertion["actual"].strip():
                    errors.append(f"{case_id}/{target_id}/{aid}: evaluated assertion requires actual observation")
                types = {evidence_by_id[e]["type"] for e in assertion["evidence_refs"] if e in evidence_by_id}
                if not assertion["evidence_refs"] or not set(expected_assertion["required_evidence"]) <= types:
                    errors.append(f"{case_id}/{target_id}/{aid}: assertion is missing linked required evidence")
                try:
                    from observation_checks import evaluate_observations
                    verdicts = evaluate_observations(assertion, expected_assertion, evidence_by_id, run, result, evidence_base_dir)
                    derived = "passed" if verdicts and all(verdicts) else "failed"
                    if assertion["status"] != derived:
                        errors.append(f"{case_id}/{target_id}/{aid}: declared status disagrees with preserved UI observation comparison")
                    attempt_verdicts.append(verdicts)
                except (ValueError, ValidationFailure, TypeError, ArithmeticError) as exc:
                    errors.append(f"{case_id}/{target_id}/{aid}: {exc}")
        if status in {"passed", "failed", "flaky"} and len(attempt_verdicts) == len(planned):
            attempts_passed = [all(v[i] for v in attempt_verdicts) for i in range(result["attempts"])]
            if attempts_passed and any(attempts_passed) and not all(attempts_passed) and status != "flaky":
                errors.append(f"{case_id}/{target_id}: mixed outcomes across attempts require flaky status")
            if status == "flaky" and (not any(attempts_passed) or all(attempts_passed)):
                errors.append(f"{case_id}/{target_id}: flaky requires preserved passing and failing attempt outcomes")
        if status == "blocked" and any(a["status"] == "failed" for a in result["assertions"]):
            errors.append(f"{case_id}/{target_id}: observed product mismatch cannot be hidden as blocked")

        if status == "passed":
            if result["attempts"] < 1:
                errors.append(f"{case_id}/{target_id}: passed result requires at least one attempt")
            if not result["assertions"] or not all(item["status"] == "passed" for item in result["assertions"]):
                errors.append(f"{case_id}/{target_id}: passed result requires only passing assertions")
            if not result["evidence"]:
                errors.append(f"{case_id}/{target_id}: passed result requires evidence")
            present_types = {item["type"] for item in result["evidence"]}
            missing_types = set(automation["required_evidence"]) - present_types
            if missing_types:
                errors.append(f"{case_id}/{target_id}: missing required evidence type(s) {', '.join(sorted(missing_types))}")
        elif status == "failed":
            if result["attempts"] < 1 or not result.get("failure_reason"):
                errors.append(f"{case_id}/{target_id}: failed result requires an attempt and failure_reason")
            if not any(item["status"] == "failed" for item in result["assertions"]):
                errors.append(f"{case_id}/{target_id}: failed result requires a failing assertion")
            if not result["evidence"]:
                errors.append(f"{case_id}/{target_id}: failed result requires evidence")
        elif status == "blocked":
            if not result.get("blocker"):
                errors.append(f"{case_id}/{target_id}: blocked result requires blocker")
        elif status == "flaky":
            if result["attempts"] < 2 or not result.get("failure_reason") or not result["evidence"]:
                errors.append(f"{case_id}/{target_id}: flaky result requires two attempts, failure_reason, and evidence")
        elif status == "not-run":
            if result["attempts"] != 0 or not result.get("blocker"):
                errors.append(f"{case_id}/{target_id}: not-run result requires zero attempts and blocker")

        if evidence_base_dir is not None:
            for evidence in result["evidence"]:
                evidence_path = _safe_evidence_path(evidence_base_dir, evidence["path"])
                if evidence_path is None:
                    errors.append(f"{case_id}/{target_id}: evidence path escapes run directory: {evidence['path']}")
                elif not evidence_path.is_file():
                    errors.append(f"{case_id}/{target_id}: evidence file does not exist: {evidence['path']}")
                elif sha256_file(evidence_path) != evidence["sha256"]:
                    errors.append(f"{case_id}/{target_id}: evidence hash mismatch: {evidence['path']}")

    if errors:
        raise ValidationFailure(errors)


def validate_results_file(results_path: Path, manifest_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = validate_manifest_file(manifest_path)
    results = load_json(results_path)
    errors = schema_errors(results, RESULTS_SCHEMA_PATH)
    if errors or not isinstance(results, dict):
        raise ValidationFailure(errors or ["$: execution results must be an object"])
    referenced_manifest = (results_path.parent / results["run"]["manifest_path"]).resolve()
    if referenced_manifest != manifest_path.resolve():
        raise ValidationFailure(["run.manifest_path does not resolve to the supplied manifest"])
    profile_path = _safe_evidence_path(results_path.parent, results["run"].get("execution_profile_path", ""))
    if profile_path is None:
        raise ValidationFailure(["run.execution_profile_path escapes the run directory"])
    if not profile_path.is_file():
        raise ValidationFailure([f"execution profile does not exist: {profile_path}"])
    if results["run"].get("execution_profile_sha256") != sha256_file(profile_path):
        raise ValidationFailure(["run.execution_profile_sha256 does not match execution-profile.json"])
    execution_profile, _ = validate_execution_profile_file(profile_path, manifest_path)
    validate_results_data(results, manifest, manifest_path, results_path.parent, execution_profile)
    return results, manifest


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def write_bytes_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", "<br>")


def md_list(values: list[str], empty: str = "无") -> str:
    if not values:
        return empty
    return "\n".join(f"- {value}" for value in values)
