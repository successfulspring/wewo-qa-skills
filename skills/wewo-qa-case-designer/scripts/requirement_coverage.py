"""Source extraction, frozen derivation plans and source-first omission checks."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from artifact_tools import ValidationFailure, _duplicates, load_json, write_text_atomic


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def source_texts(context):
    # Decisions are also source material: a clarification can introduce a variant.
    return {**{s["id"]: s["content"] for s in context["segments"] if s["read_status"] == "read" and s["disposition"] != "excluded"},
            **{d["id"]: d["resolution"] for d in context["decisions"] if d["status"] != "superseded"}}


def extraction_errors(context, *, final):
    errors = []
    origins = source_texts(context)
    items = {i["id"]: i for i in context["requirement_items"]}
    rules = {r["id"]: r for r in context["rules"]}
    for duplicate in sorted(_duplicates(i["id"] for i in context["requirement_items"])):
        errors.append("duplicate requirement item " + duplicate)
    spans = {origin: [] for origin in origins}
    for item in context["requirement_items"]:
        tag, origin = item["id"], item["origin_ref"]
        text = origins.get(origin)
        if text is None:
            errors.append(tag + ": unknown, unread or excluded extraction origin " + origin)
            continue
        start, end = item["start"], item["end"]
        if not 0 <= start < end <= len(text) or not text[start:end].strip():
            errors.append(tag + ": invalid source character span")
        else:
            spans[origin].append((start, end, tag))
        if item["disposition"] == "requirement":
            if final and not item["rule_refs"]:
                errors.append(tag + ": requirement clause has no modeled rule")
            for rid in item["rule_refs"]:
                rule = rules.get(rid)
                if not rule or rule["status"] == "excluded" or tag not in rule["requirement_refs"]:
                    errors.append(tag + ": requirement/rule linkage disagrees: " + rid)
                elif origin not in rule["segment_refs"] + rule["decision_refs"]:
                    errors.append(tag + ": rule does not cite its extraction origin")
        elif item["rule_refs"] or not item.get("reason", "").strip():
            errors.append(tag + ": non-requirement clause needs a reason and no rules")
        if final and item["disposition"] == "pending":
            errors.append(tag + ": unresolved source clause; clarify before final design")
    for origin, text in origins.items():
        cursor = 0
        for start, end, tag in sorted(spans[origin]):
            if start < cursor:
                errors.append(tag + ": overlapping source clauses")
            if final and text[cursor:start].strip():
                errors.append(f"{origin}: unaccounted source content at characters {cursor}:{start}")
            cursor = max(cursor, end)
        if final and text[cursor:].strip():
            errors.append(f"{origin}: unaccounted source content at characters {cursor}:{len(text)}")
    for rule in rules.values():
        rid = rule["id"]
        if final and rule["status"] != "excluded" and not rule["requirement_refs"]:
            errors.append(rid + ": included rule requires atomic requirement items")
        for ref in rule["requirement_refs"]:
            item = items.get(ref)
            if not item or item["disposition"] != "requirement" or rid not in item["rule_refs"]:
                errors.append(rid + ": unknown or unlinked requirement item " + ref)
    return errors


def plan_digest(context):
    from design_context import requirement_digest
    rules = []
    for rule in context["rules"]:
        models = copy.deepcopy(rule["design_models"])
        for model in models:
            for item in model["items"]:
                item.pop("test_point_refs", None)
        rules.append({"id": rule["id"], "factors": rule["factors"], "design_models": models,
                      "coverage": [{k: v for k, v in d.items() if k != "test_point_refs"} for d in rule["coverage"]]})
    return digest({"requirements": requirement_digest(context), "rules": rules})


def plan_errors(context, *, final):
    errors, factor_ids, outcome_ids = [], {}, {}
    for rule in context["rules"]:
        rid = rule["id"]
        refs = set(rule["requirement_refs"])
        applicable = {d["dimension"] for d in rule["coverage"] if d["applicability"] == "required"}
        factors = {f["id"]: f for f in rule["factors"]}
        observed = {fid: set() for fid in factors}
        covered_requirements = set()
        if len({f["name"] for f in factors.values()}) != len(factors):
            errors.append(rid + ": factor names must identify distinct business conditions")
        for dimension in rule["coverage"]:
            if dimension["applicability"] == "pending":
                if final or dimension["test_point_refs"]:
                    errors.append(rid + ": unresolved coverage applicability: " + dimension["dimension"])
            if not set(dimension["basis_refs"]) <= refs or (final and not dimension["basis_refs"]):
                if rule["status"] != "excluded":
                    errors.append(rid + ": applicability requires its own requirement evidence: " + dimension["dimension"])
        for factor in rule["factors"]:
            fid = factor["id"]
            if fid in factor_ids and factor_ids[fid] != factor:
                errors.append("conflicting shared coverage factor " + fid)
            factor_ids[fid] = factor
            if factor["dimension"] not in applicable:
                errors.append(fid + ": known factor contradicts not-applicable dimension")
            if not set(factor["basis_refs"]) <= refs:
                errors.append(fid + ": factor lacks rule-specific requirement evidence")
        for model in rule["design_models"]:
            for item in model["items"]:
                cid = item["id"]
                if not set(item["requirement_refs"]) <= refs:
                    errors.append(cid + ": derivation uses an unrelated requirement item")
                needed = {f["id"] for f in factors.values() if f["dimension"] in item["dimensions"]}
                if not needed <= set(item["factor_values"]):
                    errors.append(cid + ": scenario omits applicable planned factors")
                for fid, value in item["factor_values"].items():
                    if fid in factors and value is None:
                        name = factors[fid]["name"]
                        if model["method"] == "decision-table" and name in item.get("assignment", {}) and item["assignment"][name] is None and item.get("reason", "").strip():
                            observed[fid].update(factors[fid]["values"])
                        else:
                            errors.append(cid + ": wildcard needs an outcome-invariant decision row and evidence-based reason")
                    elif fid not in factors or value not in factors[fid]["values"]:
                        errors.append(cid + ": unknown factor or representative value " + fid)
                    else:
                        observed[fid].add(value)
                    if model["method"] == "decision-table" and fid in factors and item.get("assignment", {}).get(factors[fid]["name"]) != value:
                        errors.append(cid + ": decision assignment disagrees with its planned factor value")
                if item["disposition"] == "required" and not item["outcomes"]:
                    errors.append(cid + ": required scenario needs independently observable outcomes")
                if item["disposition"] == "required":
                    covered_requirements.update(item["requirement_refs"])
                if item["disposition"] == "excluded" and item["outcomes"]:
                    errors.append(cid + ": excluded scenario cannot create observable obligations")
                for outcome in item["outcomes"]:
                    oid = outcome["id"]
                    signature = (outcome, item["condition"], item["action"], item["factor_values"])
                    if oid in outcome_ids and outcome_ids[oid] != signature:
                        errors.append("conflicting planned outcome " + oid)
                    outcome_ids[oid] = signature
                if model["method"] == "decision-table":
                    for name, domain in model.get("factors", {}).items():
                        matches = [f for f in factors.values() if f["name"] == name]
                        if len(matches) != 1 or set(matches[0]["values"]) != set(domain):
                            errors.append(model["id"] + ": decision factor differs from the requirement-derived factor inventory: " + name)
        if final:
            if len(rule["coverage"]) != 6:
                errors.append(rid + ": assess all six coverage dimensions before freezing")
            if rule["status"] != "excluded" and refs - covered_requirements:
                errors.append(rid + ": requirement items lack concrete required scenarios: " + ", ".join(sorted(refs - covered_requirements)))
            for fid, factor in factors.items():
                missing = set(factor["values"]) - observed[fid]
                if missing:
                    errors.append(fid + ": uncovered planned factor values: " + ", ".join(sorted(missing)))
    stamp = context["coverage_plan"]
    if final and (stamp["status"] != "frozen" or not stamp.get("frozen_at") or stamp.get("sha256") != plan_digest(context)):
        errors.append("coverage plan is unfrozen or changed; derive and freeze it before authoring test points")
    return errors


def source_audit_errors(context, *, final):
    if not final:
        return []
    errors = []
    origins = source_texts(context)
    checks = context["review"].get("source_checks", [])
    if len(checks) != len(origins) or {c["origin_ref"] for c in checks} != set(origins):
        errors.append("source-first audit must revisit every included source segment and decision")
    requirements = context["requirement_items"]
    for check in checks:
        origin = check["origin_ref"]
        expected = {i["id"] for i in requirements if i["origin_ref"] == origin}
        if set(check["requirement_refs"]) != expected:
            errors.append(origin + ": source audit omits or invents extraction items")
        if origin in origins and check["content_sha256"] != hashlib.sha256(origins[origin].encode("utf-8")).hexdigest():
            errors.append(origin + ": source audit is stale for the current source content")
    if context["review"].get("plan_sha256") != plan_digest(context):
        errors.append("coverage/atomicity review is stale for the current derivation plan")
    return errors


def freeze_plan(context):
    """Freeze already derived obligations, not human approval or coverage completeness."""
    from design_context import validate_design_context_data
    from requirement_readiness import readiness_errors
    from design_methods import derivation_errors
    validate_design_context_data(context, final=False)
    errors = readiness_errors(context, confirmed=True)
    if errors:
        errors.insert(0, "confirm the actual final requirements before freezing the coverage plan")
    # Check planned applicability, representatives and outcomes before any leaves.
    candidate = copy.deepcopy(context)
    candidate["coverage_plan"] = {"status": "frozen", "frozen_at": datetime.now(timezone.utc).isoformat(), "sha256": plan_digest(context)}
    errors.extend(plan_errors(candidate, final=True))
    errors.extend(derivation_errors(context, final=True, require_points=False))
    for rule in context["rules"]:
        if any(d["test_point_refs"] for d in rule["coverage"]) or any(i["test_point_refs"] for m in rule["design_models"] for i in m["items"]):
            errors.append(rule["id"] + ": freeze coverage before attaching leaf test points")
    if errors:
        raise ValidationFailure(errors)
    candidate["review"] = {"status": "draft"}
    for key in ("notes", "findings"):
        if key in context["review"]:
            candidate["review"][key] = copy.deepcopy(context["review"][key])
    return candidate


def main():
    parser = argparse.ArgumentParser(description="Freeze a requirement-derived coverage plan before XMind/case authoring; does not approve requirements.")
    parser.add_argument("context", type=Path)
    args = parser.parse_args()
    path = args.context.resolve()
    context = freeze_plan(load_json(path))
    write_text_atomic(path, json.dumps(context, ensure_ascii=False, indent=2) + "\n")
    print("OK: coverage plan frozen; source/atomicity audit and tester XMind review still required")
    return 0
