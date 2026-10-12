"""Validate recorded execution discovery without inventing successful checks."""
from __future__ import annotations

AREAS = ("interaction", "observation", "data", "cleanup", "tooling")


def selected_pairs(manifest, suite, targets):
    return [(case, target, next(a for a in case["automation"] if a["target_id"] == target))
            for case in manifest["cases"] if suite in case["suite_membership"]
            for target in case["applicable_targets"] if target in targets]


def draft_readiness(manifest, suite, targets):
    return [{"case_id": c["id"], "target_id": t,
             "status": "manual" if a["feasibility"] == "manual" else "pending",
             "route": a["candidate_route"], "runtime_requirement_refs": [],
             "checks": [{"area": area, "status": "pending", "detail": ""} for area in AREAS],
             "reason": a.get("reason", "")}
            for c,t,a in selected_pairs(manifest, suite, targets)]


def pair_requirements(manifest, profile, case, target):
    from artifact_tools import runtime_requirement_ids_for_pair
    ids = runtime_requirement_ids_for_pair(manifest, case, target)
    for item in profile.get("case_readiness", []):
        if (item["case_id"], item["target_id"]) == (case["id"], target):
            ids.update(item["runtime_requirement_refs"])
    return ids


def validate_readiness(profile, manifest):
    if profile["schema_version"] == "1.1":
        return []
    errors = []
    environments = {e["target_id"]: e for e in profile["environments"]}
    if len(environments) != len(profile["environments"]) or set(environments) != set(profile["targets"]):
        errors.append("environments must identify every selected target exactly once")
    for target, env in environments.items():
        if env["verified"] and any(not env[k].strip() for k in ("name", "entry", "build", "evidence")):
            errors.append(target + ": verified environment requires entry, build and actual verification evidence")
    needs = manifest["runtime_requirements"] + profile["discovered_requirements"]
    need_by_id = {n["id"]: n for n in needs}
    if len(need_by_id) != len(needs):
        errors.append("discovered requirement IDs must be distinct from manifest and other discovered requirements")
    pairs = {(c["id"],t):(c,a) for c,t,a in selected_pairs(manifest,profile["suite"],profile["targets"])}
    records = {(r["case_id"],r["target_id"]):r for r in profile["case_readiness"]}
    if len(records) != len(profile["case_readiness"]) or set(records) != set(pairs):
        errors.append("case_readiness must account for every selected case-target exactly once")
    resolved = {b["requirement_id"] for b in profile["bindings"] if b["status"] == "resolved"}
    referenced = set()
    for pair, record in records.items():
        if pair not in pairs:
            continue
        case, assessment = pairs[pair]
        label = "/".join(pair)
        if record["route"] != assessment["candidate_route"]:
            errors.append(label + ": readiness route differs from reviewed evidence surface")
        manual = assessment["feasibility"] == "manual"
        if (record["status"] == "manual") != manual:
            errors.append(label + ": readiness cannot silently change the design automation assessment")
        checks = {c["area"]: c for c in record["checks"]}
        if len(checks) != len(record["checks"]) or set(checks) != set(AREAS):
            errors.append(label + ": readiness needs all five distinct capability checks")
        for check in record["checks"]:
            if check["status"] != "pending" and not check["detail"].strip():
                errors.append(label + ": checked capability requires substantive detail")
        if record["status"] in {"blocked", "manual"} and not record["reason"].strip():
            errors.append(label + ": blocked/manual readiness requires a reason")
        for rid in record["runtime_requirement_refs"]:
            referenced.add(rid)
            req = need_by_id.get(rid)
            if req is None or (req["scope"] == "target" and pair[1] not in req.get("target_ids", [])):
                errors.append(label + ": unknown or inapplicable discovered runtime requirement " + rid)
        if record["status"] == "ready":
            if not environments.get(pair[1], {}).get("verified"):
                errors.append(label + ": ready case requires a verified target environment")
            if any(c["status"] not in {"verified", "not-applicable"} for c in record["checks"]):
                errors.append(label + ": ready case contains unfinished capability checks")
            if any(checks.get(area, {}).get("status") != "verified" for area in ("interaction", "observation", "tooling")):
                errors.append(label + ": interaction, observation and tooling must be verified")
            if not pair_requirements(manifest,profile,case,pair[1]) <= resolved:
                errors.append(label + ": ready case has unresolved execution prerequisites")
    if {n["id"] for n in profile["discovered_requirements"]} - referenced:
        errors.append("discovered requirements must identify their affected cases")
    return errors


def require_ready(profile, manifest, case_id, target_id):
    from artifact_tools import ValidationFailure
    if profile["schema_version"] != "1.2":
        raise ValidationFailure(["new execution requires fresh profile 1.2 discovery; legacy profiles are historical only"])
    record = next(r for r in profile["case_readiness"] if (r["case_id"],r["target_id"]) == (case_id,target_id))
    if record["status"] != "ready":
        raise ValidationFailure([case_id + "/" + target_id + ": execution readiness is " + record["status"] + "; " + record["reason"]])
    return record
