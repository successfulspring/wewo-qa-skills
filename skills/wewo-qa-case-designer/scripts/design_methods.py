"""Concrete black-box derivations and semantic-review gates, owned by Designer."""
from __future__ import annotations

from math import prod
from numeric_values import finite_decimal as decimal, decimal_sum


REVIEW_CHECKS = {"source-fidelity", "coverage", "executability", "oracle-consistency"}


def review_errors(review, *, final):
    errors = []
    checks = review.get("checks", [])
    if final and set(checks) != REVIEW_CHECKS:
        errors.append("review must record source-fidelity, coverage, executability, and oracle-consistency checks")
    ids = set()
    for finding in review.get("findings", []):
        if finding["id"] in ids:
            errors.append("duplicate review finding " + finding["id"])
        ids.add(finding["id"])
        if finding["status"] == "resolved" and not finding.get("resolution", "").strip():
            errors.append(finding["id"] + ": resolved finding requires resolution")
        if final and finding["status"] == "open":
            errors.append(finding["id"] + ": unresolved review finding")
    return errors


def derivation_errors(context, *, final):
    errors, ids = [], set()
    objects = {o["id"]: o for o in context["objects"]}
    for rule in context["rules"]:
        required = {d["dimension"] for d in rule["coverage"] if d["applicability"] == "required"}
        covered = set()
        for model in rule["design_models"]:
            mid = model["id"]
            for item in [model] + model["items"]:
                if item["id"] in ids:
                    errors.append("duplicate derivation id " + item["id"])
                ids.add(item["id"])
            if rule["status"] == "excluded":
                errors.append(mid + ": excluded rule cannot produce derivations")
            for item in model["items"]:
                tag = item["id"]
                if not set(item["dimensions"]) <= required:
                    errors.append(tag + ": dimensions contradict rule applicability")
                if item["disposition"] == "excluded":
                    if not item.get("reason", "").strip() or item["test_point_refs"]:
                        errors.append(tag + ": excluded item needs reason and no points")
                else:
                    covered.update(item["dimensions"])
                    if final and not item["test_point_refs"]:
                        errors.append(tag + ": required derivation has no leaf test point")
            kind = model["method"]
            try:
                if kind == "equivalence-partition":
                    if any(not i.get("partition") or not i.get("data") for i in model["items"]):
                        errors.append(mid + ": partitions require partition descriptions and representative data")
                elif kind == "boundary":
                    bounds = model.get("bounds", [])
                    if not model.get("field") or not bounds:
                        errors.append(mid + ": boundaries require field, bounds, and resolution")
                    if len({b["id"] for b in bounds}) != len(bounds):
                        errors.append(mid + ": duplicate boundary id")
                    for bound in bounds:
                        value, resolution = decimal(bound["value"]), decimal(bound["resolution"])
                        if resolution <= 0:
                            errors.append(mid + ": boundary resolution must be positive")
                        values = [decimal(i["value"]) for i in model["items"] if i.get("boundary_ref") == bound["id"]]
                        if set(values) != {decimal_sum(value, resolution.copy_negate()), value, decimal_sum(value, resolution)}:
                            errors.append(mid + ": boundary must cover below/on/above at declared resolution")
                        if len(values) != len(set(values)):
                            errors.append(mid + ": duplicate boundary representative")
                    if any(i.get("boundary_ref") not in {b["id"] for b in bounds} for i in model["items"]):
                        errors.append(mid + ": unknown boundary reference")
                elif kind == "decision-table":
                    factors = model.get("factors", {})
                    rows = [i.get("assignment", {}) for i in model["items"]]
                    if not factors or any(not domain or len(domain) != len(set(domain)) for domain in factors.values()):
                        errors.append(mid + ": decision factors need unique nonempty domains")
                    elif any(set(row) != set(factors) or any(v is not None and v not in factors[k] for k, v in row.items()) for row in rows):
                        errors.append(mid + ": each decision row must assign every factor (null means all values)")
                    else:
                        for index, row in enumerate(rows):
                            if any(all(row[k] is None or other[k] is None or row[k] == other[k] for k in factors) for other in rows[:index]):
                                errors.append(mid + ": overlapping decision rows")
                        if sum(prod(len(factors[k]) if row[k] is None else 1 for k in factors) for row in rows) != prod(map(len, factors.values())):
                            errors.append(mid + ": decision table omits condition combinations")
                elif kind in {"state-transition", "permission"}:
                    if kind == "state-transition":
                        oid = model.get("object_ref")
                        states, events = model.get("states", []), model.get("events", [])
                        if oid not in rule["object_refs"] or oid not in objects or not set(states) <= set(objects.get(oid, {}).get("states", [])):
                            errors.append(mid + ": transition model has unknown object or states")
                        axes, keys = (states, events), ("from", "event")
                        if any(i.get("to") not in states for i in model["items"]):
                            errors.append(mid + ": transition destination is undeclared")
                    else:
                        axes, keys = (model.get("roles", []), model.get("operations", [])), ("role", "operation")
                    pairs = [(i.get(keys[0]), i.get(keys[1])) for i in model["items"]]
                    if not all(axes) or len(pairs) != len(set(pairs)) or set(pairs) != {(a, b) for a in axes[0] for b in axes[1]}:
                        errors.append(mid + ": matrix must cover every declared pair once, including prohibited or excluded pairs")
                elif kind == "cross-object":
                    for item in model["items"]:
                        effects = item.get("effects", [])
                        if len({e["object_ref"] for e in effects}) < 2:
                            errors.append(item["id"] + ": cross-object item requires effects on at least two objects")
                        if any(e["object_ref"] not in rule["object_refs"] or e["object_ref"] not in objects for e in effects):
                            errors.append(item["id"] + ": cross-object effect references unrelated object")
            except (ValueError, KeyError, ArithmeticError) as exc:
                errors.append(mid + ": incomplete method data: " + str(exc))
        if final and rule["status"] != "excluded" and covered != required:
            errors.append(rule["id"] + ": concrete derivations do not cover applicable dimensions")
        methods = {m["method"] for m in rule["design_models"]}
        for dimension, method in [("boundary", "boundary"), ("state", "state-transition"), ("role", "permission"), ("cross-object", "cross-object")]:
            if dimension in required and method not in methods:
                errors.append(rule["id"] + ": applicable " + dimension + " requires concrete " + method + " model")
    return errors


def derivation_links(context, leaves, *, final):
    errors, pairs = [], set()
    items = {i["id"]: (r, m, i) for r in context["rules"] for m in r["design_models"] for i in m["items"]}
    for cid, (rule, model, item) in items.items():
        dimension_points = {p for d in rule["coverage"] if d["dimension"] in item["dimensions"] for p in d["test_point_refs"]}
        for pid in item["test_point_refs"]:
            leaf = leaves.get(pid)
            if not leaf or cid not in leaf.get("coverage_item_refs", []) or rule["id"] not in leaf["rule_refs"] or pid not in dimension_points:
                errors.append(cid + ": leaf linkage disagrees with rule, dimension, or coverage item: " + pid)
            pairs.add((cid, pid))
    for rule in context["rules"]:
        for dimension in rule["coverage"]:
            derived = {p for model in rule["design_models"] for item in model["items"] if dimension["dimension"] in item["dimensions"] for p in item["test_point_refs"]}
            if final and set(dimension["test_point_refs"]) != derived:
                errors.append(rule["id"] + ": dimension leaf list differs from concrete derivations: " + dimension["dimension"])
    for pid, leaf in leaves.items():
        refs = leaf["coverage_item_refs"]
        if final and not refs:
            errors.append(pid + ": leaf requires a concrete coverage item")
        linked_models = []
        for cid in refs:
            if cid not in items or (cid, pid) not in pairs:
                errors.append(pid + ": unknown or unlinked coverage item " + cid)
            else:
                linked_models.append(items[cid][1]["id"])
        if len(linked_models) != len(set(linked_models)):
            errors.append(pid + ": split mutually exclusive representatives from the same model into separate leaves")
    return errors
