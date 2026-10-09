from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from artifact_tools import (
    DESIGNER_SCHEMA_ROOT, ValidationFailure, _duplicates, load_json, schema_errors,
)
from design_methods import derivation_errors, review_errors


DIMENSIONS = {"positive", "negative", "boundary", "state", "role", "cross-object"}


def requirement_digest(context):
    """Confirmation covers business facts, independently of later test derivation."""
    snapshot = {k: context[k] for k in ("project", "sources", "segments", "decisions", "objects", "relationships", "flows")}
    snapshot["rules"] = [{k:v for k,v in r.items() if k not in {"coverage", "design_models"}} for r in context["rules"]]
    return hashlib.sha256(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def validate_design_context_data(context: Any, *, final: bool = True) -> None:
    errors = schema_errors(context, DESIGNER_SCHEMA_ROOT / "design-context.schema.json")
    if errors:
        raise ValidationFailure(errors)
    for key in ("sources", "segments", "decisions", "objects", "relationships", "flows", "rules"):
        for duplicate in sorted(_duplicates(item["id"] for item in context[key])):
            errors.append(f"duplicate {key} id: {duplicate}")
    sources = {x["id"]: x for x in context["sources"]}
    segments = {x["id"]: x for x in context["segments"]}
    decisions = {x["id"]: x for x in context["decisions"]}
    objects = {x["id"]: x for x in context["objects"]}
    rules = {x["id"]: x for x in context["rules"]}
    anchors: set[tuple[str, str]] = set()
    referenced_segments: set[str] = set()

    for source in sources.values():
        if source["scope"] == "excluded" and not source.get("reason"):
            errors.append(f"{source['id']}: excluded source requires reason")
        if final and source["scope"] == "included" and source["inventory_status"] != "complete":
            errors.append(f"{source['id']}: included source inventory is incomplete")
        if source["inventory_status"] != "complete" and not source.get("reason"):
            errors.append(f"{source['id']}: incomplete inventory requires reason")

    for segment in segments.values():
        sid = segment["id"]
        source = sources.get(segment["source_id"])
        if source is None:
            errors.append(f"{sid}: unknown source {segment['source_id']}")
        anchor = (segment["source_id"], segment["anchor"])
        if anchor in anchors:
            errors.append(f"{sid}: duplicate source anchor {anchor[1]}")
        anchors.add(anchor)
        if segment["read_status"] == "read" and not segment["content"].strip():
            errors.append(f"{sid}: read segment requires extracted or visually verified content")
        if segment["disposition"] != "requirement" and not segment.get("review_note"):
            errors.append(f"{sid}: non-requirement segment requires review_note")
        if segment["read_status"] == "excluded" and segment["disposition"] != "excluded":
            errors.append(f"{sid}: excluded read status requires excluded disposition")
        if source and source["scope"] == "excluded" and segment["disposition"] != "excluded":
            errors.append(f"{sid}: excluded source cannot supply included content")
        if final and source and source["scope"] == "included" and segment["read_status"] not in {"read", "excluded"}:
            errors.append(f"{sid}: relevant source content has not been read")

    for source in sources.values():
        if source["scope"] == "included" and not any(s["source_id"] == source["id"] for s in segments.values()):
            errors.append(f"{source['id']}: included source has no content segments")

    def check_segments(owner: str, refs: list[str]) -> None:
        for sid in refs:
            segment = segments.get(sid)
            if segment is None:
                errors.append(f"{owner}: unknown segment {sid}")
            elif segment["read_status"] != "read" or segment["disposition"] == "excluded":
                errors.append(f"{owner}: cannot derive facts from unread or excluded segment {sid}")

    for item in objects.values():
        check_segments(item["id"], item["segment_refs"])

    for rule in rules.values():
        rid = rule["id"]
        if not (rule["segment_refs"] or rule["decision_refs"]):
            errors.append(f"{rid}: rule requires a source segment or confirmed decision")
        if rule["status"] != "confirmed" and not rule.get("rationale"):
            errors.append(f"{rid}: assumed or excluded rule requires rationale")
        check_segments(rid, rule["segment_refs"])
        referenced_segments.update(rule["segment_refs"])
        for did in rule["decision_refs"]:
            if did not in decisions:
                errors.append(f"{rid}: unknown decision {did}")
        for oid in rule["object_refs"]:
            if oid not in objects:
                errors.append(f"{rid}: unknown business object {oid}")
        dims = [c["dimension"] for c in rule["coverage"]]
        if set(dims) != DIMENSIONS or len(dims) != len(set(dims)):
            errors.append(f"{rid}: assess each coverage dimension exactly once")
        for coverage in rule["coverage"]:
            if coverage["applicability"] == "not-applicable":
                if not coverage.get("reason") or coverage["test_point_refs"]:
                    errors.append(f"{rid}/{coverage['dimension']}: non-applicable coverage needs reason and no points")
            elif final and not coverage["test_point_refs"]:
                errors.append(f"{rid}/{coverage['dimension']}: required coverage has no test points")
        if rule["kind"] == "transition":
            transition = rule.get("transition")
            has_matrix = any(m["method"] == "state-transition" for m in rule["design_models"])
            if not transition and not has_matrix:
                errors.append(f"{rid}: transition rule requires its object/states or a concrete state-transition matrix")
            elif transition:
                business_object = objects.get(transition["object_ref"])
                if not business_object or transition["object_ref"] not in rule["object_refs"]:
                    errors.append(f"{rid}: transition references an unknown or unrelated object")
                elif any(transition[k] not in business_object["states"] for k in ("from", "to")):
                    errors.append(f"{rid}: transition references an undeclared business state")
    for segment in segments.values():
        if final and segment["disposition"] == "requirement" and segment["id"] not in referenced_segments:
            errors.append(f"{segment['id']}: requirement content has no modeled rule")
    for item in context["relationships"]:
        if item["from_object"] not in objects or item["to_object"] not in objects:
            errors.append(f"{item['id']}: relationship references unknown object")
    for item in context["relationships"] + context["flows"]:
        for rid in item["rule_refs"]:
            if rid not in rules or rules[rid]["status"] == "excluded":
                errors.append(f"{item['id']}: unknown or excluded rule {rid}")
    if final:
        confirmation = context["requirement_confirmation"]
        if confirmation["status"] != "confirmed" or not all(confirmation.get(k) for k in ("confirmed_at", "response_ref", "response_text", "snapshot_sha256")):
            errors.append("requirements need explicit user confirmation with the actual response before final test points")
        elif confirmation["snapshot_sha256"] != requirement_digest(context):
            errors.append("confirmed requirement facts changed; discuss and reconfirm requirements")
        if context["review"]["status"] != "confirmed" or not context["review"].get("confirmed_at"):
            errors.append("design context requires confirmed review and timestamp")
        if any(q["material"] for q in context["open_questions"]):
            errors.append("design context has unresolved material questions")
    errors.extend(derivation_errors(context, final=final))
    errors.extend(review_errors(context["review"], final=final))
    if errors:
        raise ValidationFailure(errors)


def validate_design_context_file(path: Path, *, final: bool = True) -> dict[str, Any]:
    context = load_json(path)
    validate_design_context_data(context, final=final)
    return context


def digest_main():
    parser = argparse.ArgumentParser(description="Print the business snapshot hash; does not confirm requirements.")
    parser.add_argument("context", type=Path)
    args = parser.parse_args()
    context = validate_design_context_file(args.context.resolve(), final=False)
    print(requirement_digest(context))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate source intake, business model, and rule coverage.")
    parser.add_argument("context", type=Path)
    parser.add_argument("--draft", action="store_true", help="Check structure while discovery is still in progress.")
    args = parser.parse_args()
    try:
        validate_design_context_file(args.context, final=not args.draft)
    except ValidationFailure as exc:
        for error in exc.errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: design context" + (" (draft; not execution-ready)" if args.draft else ""))
    return 0
