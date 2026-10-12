"""Requirement-only gates; no test plan, leaf or case is needed for readiness."""
from __future__ import annotations

import argparse

from artifact_tools import ValidationFailure, _duplicates
from requirement_coverage import extraction_errors


AUDITS = {"business-coverage", "branch-expansion", "decision-provenance"}
UNIT_VIEW_FIELDS = {"id", "title", "source_refs", "status", "understanding", "confirmed_facts", "assumptions", "exclusion_reason"}
DECISION_VIEW_FIELDS = {"id", "unit_id", "question_id", "selected_options", "topic", "resolution", "status", "rationale"}


def active_decisions(context):
    return [d for d in context["decisions"] if d["status"] != "superseded"]


def point_decisions(context):
    return [{k: v for k, v in d.items() if k in DECISION_VIEW_FIELDS} for d in active_decisions(context)]


def point_units(context):
    return [{k: v for k, v in u.items() if k in UNIT_VIEW_FIELDS} for u in context["requirement_units"]]


def reply_refs(event):
    value = event.get("in_reply_to", [])
    return [value] if isinstance(value, str) else value


def dialogue_links(context):
    """Index actual question occurrences and the subset addressed by each reply."""
    errors, preceding, messages = [], {}, set()
    asked, answered, latest_answers = {}, {}, {}
    for event in context["dialogue_events"]:
        eid, kind = event["id"], event["kind"]
        message_key = (kind, event["message_ref"])
        if message_key in messages:
            errors.append(eid + ": actual message already recorded for this event kind")
        messages.add(message_key)
        if kind == "question":
            qids, revisits = event.get("question_ids", []), event.get("revisits", {})
            if not qids:
                errors.append(eid + ": question event requires the displayed question IDs")
            if set(revisits) - set(qids):
                errors.append(eid + ": revisits must name displayed questions")
            for qid in qids:
                if qid in asked:
                    if revisits.get(qid) != asked[qid]:
                        errors.append(eid + ": follow-up must revisit the latest earlier occurrence of " + qid)
                elif qid in revisits:
                    errors.append(eid + ": first occurrence cannot revisit " + qid)
                asked[qid] = eid
        elif "revisits" in event:
            errors.append(eid + ": only questions may carry revisits")
        if kind in {"answer", "confirmation"}:
            refs = reply_refs(event)
            expected = "question" if kind == "answer" else "summary"
            parents = [preceding.get(ref) for ref in refs]
            if not parents or any(not p or p["kind"] != expected for p in parents):
                errors.append(eid + ": reply must refer to an earlier " + expected + " event")
            if kind == "confirmation" and not isinstance(event.get("in_reply_to"), str):
                errors.append(eid + ": confirmation must reply to one summary event")
            if kind == "answer":
                available = {}
                for parent in parents:
                    if not parent or parent["kind"] != "question":
                        continue
                    for qid in parent.get("question_ids", []):
                        if qid in available:
                            errors.append(eid + ": reply cites multiple occurrences of " + qid)
                        available[qid] = parent["id"]
                if len(available) > 1 and "question_ids" not in event:
                    errors.append(eid + ": multi-question reply must identify addressed question_ids")
                addressed = event.get("question_ids", list(available) if len(available) == 1 else [])
                if set(addressed) - set(available):
                    errors.append(eid + ": addressed question is absent from the referenced batches")
                answered[eid] = {qid: available[qid] for qid in addressed if qid in available}
                for qid in answered[eid]:
                    latest_answers[qid] = eid
        preceding[eid] = event
    return errors, asked, answered, latest_answers


def dialogue_errors(context, *, ready=False):
    """Check recorded evidence, not whether an answer is true or sufficient."""
    errors, asked, answered, latest_answers = dialogue_links(context)
    units = {u["id"]: u for u in context["requirement_units"]}
    events = {e["id"]: e for e in context["dialogue_events"]}
    decisions = {d["id"]: d for d in context["decisions"]}
    rules = {r["id"]: r for r in context["rules"]}
    questions = {q["id"]: q for q in context["open_questions"]}
    sources = {s["id"] for s in context["sources"]}
    for key in ("requirement_units", "dialogue_events", "open_questions"):
        errors.extend("duplicate " + key + " id: " + i for i in _duplicates(x["id"] for x in context[key]))
    for unit in units.values():
        uid = unit["id"]
        if any(ref.split("#", 1)[0] not in sources for ref in unit["source_refs"]):
            errors.append(uid + ": unknown unit source")
        if any(ref not in units or ref == uid for ref in unit["depends_on"]):
            errors.append(uid + ": invalid unit dependency")
        if any(ref not in rules or rules[ref]["status"] == "excluded" for ref in unit["rule_refs"]):
            errors.append(uid + ": unknown or excluded unit rule")
        if unit["status"] == "excluded" and (not unit.get("exclusion_reason", "").strip() or unit["rule_refs"]):
            errors.append(uid + ": excluded unit requires a reason and no active rules")
        if ready and unit["status"] not in {"confirmed", "excluded"}:
            errors.append(uid + ": requirement unit is still " + unit["status"])
        if ready and unit["status"] == "confirmed" and (not unit["confirmed_facts"] or not unit["rule_refs"]):
            errors.append(uid + ": confirmed behavioral unit needs facts and active rules")

    resolved_questions = set()
    for decision in decisions.values():
        did = decision["id"]
        if decision["unit_id"] not in units:
            errors.append(did + ": unknown requirement unit")
        response_id, qid = decision.get("response_event_ref"), decision["question_id"]
        occurrence = answered.get(response_id, {}).get(qid)
        if not occurrence:
            errors.append(did + ": decision must link its displayed question and actual answer event")
        current = occurrence == asked.get(qid) and response_id == latest_answers.get(qid)
        if decision["status"] != "superseded":
            if current and decision["status"] == "confirmed":
                resolved_questions.add(qid)
            if ready and not current:
                errors.append(did + ": current decision must use the latest answer to the latest question occurrence")
        if decision["status"] == "superseded":
            replacement = decisions.get(decision.get("superseded_by"))
            if not replacement or replacement is decision:
                errors.append(did + ": superseded decision needs a replacement")
            seen, current = {did}, replacement
            while current and current["status"] == "superseded":
                if current["id"] in seen:
                    errors.append(did + ": cyclic decision supersession")
                    break
                seen.add(current["id"])
                current = decisions.get(current.get("superseded_by"))
        elif decision.get("superseded_by"):
            errors.append(did + ": only superseded decisions may name a replacement")
        if ready and decision["status"] == "assumed":
            errors.append(did + ": unconfirmed business assumption must be resolved or explicitly excluded")

    for rule in rules.values():
        if ready and rule["status"] == "assumed":
            errors.append(rule["id"] + ": unconfirmed business oracle")
        for ref in rule["decision_refs"]:
            if ref in decisions and decisions[ref]["status"] == "superseded":
                errors.append(rule["id"] + ": rule still uses superseded decision " + ref)
    if ready:
        for qid in set(asked) - resolved_questions - set(questions):
            errors.append(qid + ": displayed question has no decision or explicit pending disposition")
        assigned = {ref for u in units.values() for ref in u["rule_refs"]}
        errors.extend(r["id"] + ": business rule has no requirement unit" for r in rules.values() if r["status"] != "excluded" and r["id"] not in assigned)
        if not units or not any(r["status"] == "confirmed" for r in rules.values()):
            errors.append("requirement readiness needs included behavioral units and confirmed rules")

    for q in questions.values():
        if q["unit_id"] not in units:
            errors.append(q["id"] + ": unknown question unit")
        if q.get("parent_decision_ref") and q["parent_decision_ref"] not in decisions:
            errors.append(q["id"] + ": unknown parent decision")
        if ready and q["material"]:
            errors.append(q["id"] + ": unresolved material question: " + q["description"])
    reviews = context["branch_reviews"]
    answers = {e["id"] for e in events.values() if e["kind"] == "answer"}
    if ready and ({r["answer_event_ref"] for r in reviews} != answers or len(reviews) != len(answers)):
        errors.append("review newly unlocked branches after every actual answer")
    for review in reviews:
        if review["answer_event_ref"] not in answers or not set(review["unit_refs"]) <= set(units):
            errors.append("branch review references unknown answer or units")
        affected = {d["unit_id"] for d in decisions.values() if d["response_event_ref"] == review["answer_event_ref"]}
        if not affected <= set(review["unit_refs"]):
            errors.append("branch review omits units whose decisions changed in this answer")
    return errors


def readiness_errors(context, *, confirmed=False):
    from design_context import requirement_digest
    errors = dialogue_errors(context, ready=True)
    for source in context["sources"]:
        if source["scope"] == "included" and source["inventory_status"] != "complete":
            errors.append(source["id"] + ": included source inventory is incomplete")
    included = {s["id"] for s in context["sources"] if s["scope"] == "included"}
    for segment in context["segments"]:
        if segment["source_id"] in included and segment["read_status"] not in {"read", "excluded"}:
            errors.append(segment["id"] + ": relevant source content has not been read")
    errors.extend(extraction_errors(context, final=True))
    snapshot = requirement_digest(context)
    review = context["requirement_review"]
    if review["status"] != "ready" or review.get("snapshot_sha256") != snapshot:
        errors.append("requirement completeness review is missing or stale")
    audits = review.get("checks", [])
    if len(audits) != len(AUDITS) or {a["kind"] for a in audits} != AUDITS:
        errors.append("perform business-coverage, branch-expansion and decision-provenance audits before the final summary")
    for audit in audits:
        if set(audit["unit_refs"]) != {u["id"] for u in context["requirement_units"]}:
            errors.append(audit["kind"] + ": audit must account for every current unit, including exclusions")
    if confirmed:
        confirmation = context["requirement_confirmation"]
        events = {e["id"]: e for e in context["dialogue_events"]}
        summary = events.get(confirmation.get("summary_event_ref"), {})
        response = events.get(confirmation.get("response_event_ref"), {})
        if confirmation["status"] != "confirmed" or not all(confirmation.get(k) for k in ("confirmed_at", "response_ref", "response_text")):
            errors.append("requirements need explicit user confirmation with the actual response before test points")
        if confirmation.get("snapshot_sha256") != snapshot:
            errors.append("confirmed requirement facts changed; discuss and reconfirm requirements")
        if summary.get("kind") != "summary" or summary.get("snapshot_sha256") != snapshot:
            errors.append("confirmation must bind the actual displayed final summary to current requirements")
        order = {e["id"]: i for i, e in enumerate(context["dialogue_events"])}
        if any(order[e["id"]] > order.get(summary.get("id"), -1) for e in events.values() if e["kind"] in {"question", "answer"}):
            errors.append("final summary predates later dialogue; present the revised summary and reconfirm")
        if response.get("kind") != "confirmation" or response.get("in_reply_to") != summary.get("id") or response.get("text") != confirmation.get("response_text") or response.get("message_ref") != confirmation.get("response_ref"):
            errors.append("confirmation must preserve the actual reply to that final summary")
    return errors


def main():
    from design_context import validate_design_context_file
    from pathlib import Path
    parser = argparse.ArgumentParser(description="Validate requirement completeness before the summary; never confirms on behalf of the user.")
    parser.add_argument("context", type=Path)
    parser.add_argument("--confirmed", action="store_true", help="Also require the actual final summary and user confirmation.")
    args = parser.parse_args()
    context = validate_design_context_file(args.context, final=False)
    errors = readiness_errors(context, confirmed=args.confirmed)
    if errors:
        raise ValidationFailure(errors)
    print("OK: requirement readiness" + (" and recorded confirmation" if args.confirmed else "; present the summary and obtain user confirmation"))
    return 0
