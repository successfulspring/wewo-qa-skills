"""Requirement-only gates; no test plan, leaf or case is needed for readiness."""
from __future__ import annotations

import argparse

from artifact_tools import ValidationFailure, _duplicates
from requirement_coverage import extraction_errors


AUDITS = {"business-coverage", "branch-expansion", "decision-provenance"}
UNIT_VIEW_FIELDS = {"id", "title", "source_refs", "status", "understanding", "confirmed_facts", "assumptions", "exclusion_reason"}
DECISION_VIEW_FIELDS = {"id", "unit_id", "question_id", "selected_options", "topic", "resolution", "status", "rationale",
                        "evidence_kind", "requirement_refs", "approval_refs", "approved_by", "applicability", "question_event_ref"}


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
            if kind == "answer" or (kind == 'confirmation' and event.get('answer_to')):
                if kind == 'confirmation':
                    parents = [preceding.get(ref) for ref in event['answer_to']]
                    if any(not p or p['kind'] != 'question' for p in parents):
                        errors.append(eid + ': combined confirmation must answer earlier question batches')
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


def dialogue_errors(context, *, ready=False, reviewed=False):
    """Check recorded evidence, not whether an answer is true or sufficient."""
    errors, asked, answered, latest_answers = dialogue_links(context)
    for event in context['dialogue_events']:
        responses = event.get('responses', [])
        ids = [r['question_id'] for r in responses]
        if responses and (event['kind'] not in {'answer', 'confirmation'} or
                          len(ids) != len(set(ids)) or not set(ids) <= set(answered.get(event['id'], {}))):
            errors.append(event['id'] + ': cell responses must uniquely match the addressed questions')
    units = {u["id"]: u for u in context["requirement_units"]}
    events = {e["id"]: e for e in context["dialogue_events"]}
    decisions = {d["id"]: d for d in context["decisions"]}
    rules = {r["id"]: r for r in context["rules"]}
    questions = {q["id"]: q for q in context["open_questions"]}
    closed = context.get('closed_questions', [])
    closed_ids = [q['id'] for q in closed]
    if len(closed_ids) != len(set(closed_ids)) or set(closed_ids) & set(questions):
        errors.append('closed questions must have unique IDs and cannot also remain open')
    for q in closed:
        if q['unit_id'] not in units:
            errors.append(q['id'] + ': unknown closed question unit')
        for ref in q['resolution_refs']:
            decision = decisions.get(ref, {})
            if decision.get('question_id') != q['id'] or decision.get('status') != 'confirmed':
                errors.append(q['id'] + ': closing a question requires its confirmed resolution decision')
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
        response_id, qid = decision.get("response_event_ref"), decision.get("question_id")
        if decision.get('evidence_kind') == 'document':
            from source_updates import document_decision_errors
            errors.extend(document_decision_errors(context, decision))
            recorded = qid in questions or qid in closed_ids or any(
                qid in change['question_refs'] and did in change['decision_refs']
                for update in context.get('source_updates', []) for change in update['changes'])
            current = not qid or ((qid in asked or recorded) and
                                 decision.get('question_event_ref') == asked.get(qid))
        else:
            occurrence = answered.get(response_id, {}).get(qid)
            if not occurrence:
                errors.append(did + ": decision must link its displayed question and actual answer event")
            current = occurrence == asked.get(qid) and response_id == latest_answers.get(qid)
        if decision["status"] != "superseded":
            if current and qid and decision["status"] == "confirmed":
                resolved_questions.add(qid)
            if (ready or (reviewed and decision['status'] == 'confirmed')) and not current:
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
        if ready and rule["status"] in {"assumed", "pending"}:
            errors.append(rule["id"] + ": unconfirmed business oracle")
        for ref in rule["decision_refs"]:
            if ref in decisions and decisions[ref]["status"] == "superseded":
                errors.append(rule["id"] + ": rule still uses superseded decision " + ref)
    if ready or reviewed:
        for qid in set(asked) - resolved_questions - set(questions):
            errors.append(qid + ": displayed question has no decision or explicit pending disposition")
    if ready:
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
    answer_reviews = [r for r in reviews if 'answer_event_ref' in r]
    answers = {e["id"] for e in events.values() if e["kind"] == "answer" or (e['kind'] == 'confirmation' and e.get('answer_to'))}
    if (ready or reviewed) and ({r["answer_event_ref"] for r in answer_reviews} != answers or len(answer_reviews) != len(answers)):
        errors.append("review newly unlocked branches after every actual answer")
    for review in answer_reviews:
        if review["answer_event_ref"] not in answers or not set(review["unit_refs"]) <= set(units):
            errors.append("branch review references unknown answer or units")
        affected = {d["unit_id"] for d in decisions.values() if d.get("response_event_ref") == review["answer_event_ref"]}
        if not affected <= set(review["unit_refs"]):
            errors.append("branch review omits units whose decisions changed in this answer")
    updates = {u['id']: u for u in context.get('source_updates', [])}
    source_reviews = [r for r in reviews if 'source_update_ref' in r]
    if (ready or reviewed) and ({r['source_update_ref'] for r in source_reviews} != set(updates) or len(source_reviews) != len(updates)):
        errors.append('review newly unlocked branches after every source update')
    for review in source_reviews:
        update = updates.get(review['source_update_ref'])
        if not update or not set(review['unit_refs']) <= set(units):
            errors.append('source branch review references unknown update or units')
            continue
        from source_updates import affected_artifacts
        changed_rules = {r for change in update['changes'] for r in change['rule_refs']}
        if not set(affected_artifacts(context, changed_rules)['unit_refs']) <= set(review['unit_refs']):
            errors.append('source branch review omits affected dependency units')
    from source_updates import update_errors
    errors.extend(update_errors(context))
    return errors


def readiness_errors(context, *, confirmed=False, final=True, clarification=False):
    from design_context import requirement_digest
    if clarification and (confirmed or final):
        return ['clarification is a pre-confirmation view, not a design or finalization gate']
    errors = dialogue_errors(context, ready=final, reviewed=True)
    if not final and not clarification:
        errors.extend(q['id'] + ': blocking question prevents draft design' for q in context['open_questions'] if q.get('blocking'))
    for source in context["sources"]:
        if source["scope"] == "included" and source["inventory_status"] != "complete":
            errors.append(source["id"] + ": included source inventory is incomplete")
    included = {s["id"] for s in context["sources"] if s["scope"] == "included"}
    for segment in context["segments"]:
        if segment["source_id"] in included and segment["read_status"] not in {"read", "excluded"}:
            errors.append(segment["id"] + ": relevant source content has not been read")
    errors.extend(extraction_errors(context, final=final, complete=True))
    snapshot = requirement_digest(context)
    review = context["requirement_review"]
    if review["status"] != "ready" or review.get("snapshot_sha256") != snapshot:
        errors.append("requirement completeness review is missing or stale")
    audits = review.get("checks", [])
    if len(audits) != len(AUDITS) or {a["kind"] for a in audits} != AUDITS:
        errors.append("perform business-coverage, branch-expansion and decision-provenance audits before the overall summary")
    for audit in audits:
        if set(audit["unit_refs"]) != {u["id"] for u in context["requirement_units"]}:
            errors.append(audit["kind"] + ": audit must account for every current unit, including exclusions")
    if confirmed:
        from requirement_confirmation import confirmation_errors
        errors.extend(confirmation_errors(context, final=final))
    return errors


def main():
    from design_context import validate_design_context_file
    from pathlib import Path
    parser = argparse.ArgumentParser(description="Validate requirement completeness before the summary; never confirms on behalf of the user.")
    parser.add_argument("context", type=Path)
    parser.add_argument("--confirmed", action="store_true", help="Also require actual overall confirmation and any scoped amendments.")
    parser.add_argument("--draft", action="store_true", help="Check overall understanding while localized business questions remain open.")
    parser.add_argument('--clarification', action='store_true', help='Check complete reading for the initial clarification workbook; allows unresolved overall blockers.')
    args = parser.parse_args()
    context = validate_design_context_file(args.context, final=False)
    errors = readiness_errors(context, confirmed=args.confirmed, final=not (args.draft or args.clarification), clarification=args.clarification)
    if errors:
        raise ValidationFailure(errors)
    print("OK: requirement readiness" + (" and recorded confirmation" if args.confirmed else "; present the summary and obtain user confirmation"))
    return 0
