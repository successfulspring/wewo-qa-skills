"""Evidence-aware late-source updates; semantic interpretation remains agent work."""
from __future__ import annotations


def document_decision_errors(context, decision):
    """Check recorded approval provenance, not the identity or truth of its author."""
    errors, did = [], decision['id']
    items = {i['id']: i for i in context['requirement_items']}
    segments = {s['id']: s for s in context['segments']}
    sources = {s['id']: s for s in context['sources']}
    historical = decision['status'] == 'superseded'

    def usable(ref):
        segment = segments.get(ref, {})
        source = sources.get(segment.get('source_id'), {})
        return (segment.get('read_status') == 'read' and segment.get('disposition') != 'excluded'
                and source.get('scope') == 'included'
                and (historical or source.get('authority') == 'authoritative'))

    if not decision.get('requirement_refs') or not decision.get('approval_refs'):
        errors.append(did + ': document decision needs requirement clauses and approval evidence')
    for ref in decision.get('requirement_refs', []):
        item = items.get(ref, {})
        if (item.get('claim_type') != 'business_requirement' or item.get('disposition') not in {'requirement', 'context', 'excluded'}
                or not usable(item.get('origin_ref'))):
            errors.append(did + ': document decision needs a current authoritative business requirement: ' + ref)
    for ref in decision.get('approval_refs', []):
        if not usable(ref):
            errors.append(did + ': approval must cite current read authoritative evidence: ' + ref)
    if not decision.get('approved_by', '').strip() or not decision.get('applicability', '').strip():
        errors.append(did + ': document decision needs the actual owner and applicability explanation')
    if decision.get('response_event_ref') or decision.get('selected_options'):
        errors.append(did + ': document evidence must not invent a dialogue answer or option')
    return errors


def update_errors(context):
    errors, seen = [], set()
    sources = {s['id'] for s in context['sources']}
    rules = {r['id'] for r in context['rules']}
    items = {i['id'] for i in context['requirement_items']}
    questions = {q['id'] for q in context['open_questions']}
    decisions = {d['id']: d for d in context['decisions']}
    # A resolved question remains attributable through its decision after leaving the queue.
    resolved = {d.get('question_id') for d in decisions.values() if d['status'] != 'assumed'}
    for update in context.get('source_updates', []):
        uid = update['id']
        if uid in seen:
            errors.append(uid + ': duplicate source update')
        seen.add(uid)
        if not set(update['source_refs']) <= sources:
            errors.append(uid + ': unknown update source')
        for change in update['changes']:
            if not set(change['rule_refs']) <= rules or not set(change['requirement_refs']) <= items:
                errors.append(uid + ': unknown affected rule or requirement clause')
            if not set(change['decision_refs']) <= set(decisions):
                errors.append(uid + ': unknown update decision')
            if not set(change['question_refs']) <= questions | resolved:
                errors.append(uid + ': unknown update question')
            if change['disposition'] == 'pending' and not change['question_refs']:
                errors.append(uid + ': pending update needs a question')
            if change['kind'] in {'revision', 'retirement'} and change['disposition'] == 'applied':
                if not change['decision_refs']:
                    errors.append(uid + ': changed business scope needs an authoritative decision')
            if change['kind'] in {'implementation-gap', 'out-of-scope', 'corroboration'} and change['disposition'] != 'no-change':
                errors.append(uid + ': reported gaps, unrelated material and restatements do not change business expectations')
    return errors


def change_for(context, amendment):
    for update in context.get('source_updates', []):
        if update['id'] == amendment.get('source_update_ref'):
            return next((c for c in update['changes'] if amendment['ref'] in c['entity_refs']), None)
    return None


def entity(context, ref):
    if ref == 'PROJECT':
        return context['project']
    for collection in ('sources', 'segments', 'objects', 'relationships', 'flows', 'requirement_units', 'rules'):
        for item in context[collection]:
            if item['id'] == ref:
                return item
    return None


def semantic_value(ref, value):
    """Only provenance/derived fields may differ under an evidence amendment."""
    if value is None:
        return None
    excluded = set()
    if ref.startswith('RULE-'):
        excluded = {'segment_refs', 'decision_refs', 'requirement_refs', 'question_refs',
                    'coverage', 'design_models', 'factors'}
    elif ref.startswith('RU-'):
        excluded = {'source_refs', 'status'}
    elif ref.startswith('OBJ-'):
        excluded = {'segment_refs'}
    return {k: v for k, v in value.items() if k not in excluded}


def nonbusiness_amendment_errors(context, amendment, baseline, *, final):
    from requirement_confirmation import entity_projection
    from requirement_coverage import digest
    ref, kind = amendment['ref'], amendment['kind']
    current, before = entity(context, ref), amendment.get('before')
    change = change_for(context, amendment)
    if change is None:
        return [ref + ': amendment needs a matching source update change']
    errors = []
    original = baseline.get(ref)
    if original is not None:
        if before is None or digest(entity_projection(ref, before)) != original:
            return [ref + ': evidence amendment must preserve the original confirmed entity']
    elif before is not None:
        return [ref + ': newly introduced entity cannot invent an original baseline']
    if current is None:
        return [ref + ': removing confirmed content requires a business decision']
    if kind == 'evidence':
        if ref.startswith(('SRC-', 'SEG-')):
            # A new version uses new IDs; an approved source must not be rewritten in place.
            if original is not None:
                permitted = {'role', 'applies_to', 'notes'} if ref.startswith('SRC-') else set()
                if {k: v for k, v in before.items() if k not in permitted} != {k: v for k, v in current.items() if k not in permitted}:
                    errors.append(ref + ': retain source history; ingest revised content with new IDs')
            if ref.startswith('SRC-'):
                update = next(u for u in context['source_updates'] if u['id'] == amendment['source_update_ref'])
                if ref not in update['source_refs']:
                    errors.append(ref + ': evidence source is not part of this update')
            else:
                update = next(u for u in context['source_updates'] if u['id'] == amendment['source_update_ref'])
                if current['source_id'] not in update['source_refs']:
                    errors.append(ref + ': evidence segment is not part of this update')
        elif before is None or semantic_value(ref, before) != semantic_value(ref, current):
            errors.append(ref + ': evidence-only amendment changes business meaning')
        if change['disposition'] == 'pending' and not ref.startswith(('SRC-', 'SEG-')):
            errors.append(ref + ': unresolved business content needs a pending amendment')
    elif kind == 'pending':
        if final:
            errors.append(ref + ': pending amendment cannot finalize')
        if change['disposition'] != 'pending' or not change['question_refs']:
            errors.append(ref + ': pending amendment needs its unresolved question')
        if ref.startswith('RULE-'):
            if current.get('status') != 'pending' or current.get('expected') is not None or not set(change['question_refs']) <= set(current.get('question_refs', [])):
                errors.append(ref + ': pending rule must omit its unknown oracle and link the question')
            if before is not None:
                ignored = {'status', 'expected', 'rationale'}
                a, b = semantic_value(ref, before), semantic_value(ref, current)
                if {k:v for k,v in a.items() if k not in ignored} != {k:v for k,v in b.items() if k not in ignored}:
                    errors.append(ref + ': pending status cannot silently change a known condition or action')
        elif ref.startswith('RU-'):
            if current.get('status') not in {'waiting', 'discussing'}:
                errors.append(ref + ': pending unit must remain waiting or discussing')
            old_facts = before.get('confirmed_facts', []) if before else []
            if not set(current.get('confirmed_facts', [])) <= set(old_facts):
                errors.append(ref + ': pending unit cannot assert new confirmed facts')
            if before is not None:
                ignored = {'status', 'source_refs', 'rule_refs', 'confirmed_facts'}
                if {k:v for k,v in before.items() if k not in ignored} != {k:v for k,v in current.items() if k not in ignored}:
                    errors.append(ref + ': pending unit cannot silently change the agreed scope')
        else:
            errors.append(ref + ': pending amendment is limited to local rules or requirement units')
    return errors


def affected_artifacts(context, rule_refs, points=None, manifest=None):
    """Conservative impact closure from declared dependencies; not semantic inference."""
    rules, units = set(rule_refs), set()
    changed = True
    while changed:
        previous = (set(rules), set(units))
        for unit in context['requirement_units']:
            if rules.intersection(unit['rule_refs']) or units.intersection(unit['depends_on']):
                units.add(unit['id'])
                rules.update(unit['rule_refs'])
        for link in context['relationships'] + context['flows']:
            if rules.intersection(link['rule_refs']):
                rules.update(link['rule_refs'])
        changed = previous != (rules, units)
    point_refs = set()
    if points:
        from artifact_tools import walk_test_points
        point_refs = {p['id'] for p in walk_test_points(points['tree'])
                      if not p['children'] and (rules.intersection(p.get('rule_refs', []))
                                               or units.intersection(p.get('requirement_unit_refs', [])))}
    cases = {c['id'] for c in manifest['cases'] if point_refs.intersection(c['test_point_refs'])} if manifest else set()
    return {'rule_refs': sorted(rules), 'unit_refs': sorted(units), 'point_refs': sorted(point_refs), 'case_refs': sorted(cases)}


def artifact_changes(before, after):
    old, new = ({c['id']: c for c in m['cases']} for m in (before, after))
    common = old.keys() & new.keys()
    return {'added': sorted(new.keys() - old.keys()), 'modified': sorted(k for k in common if old[k] != new[k]),
            'retired': sorted(old.keys() - new.keys()), 'unchanged': sorted(k for k in common if old[k] == new[k])}


def validate_update_files(context, path):
    """Retain the pre-update artifact state for inspection and retired-case history."""
    from artifact_tools import load_json, ValidationFailure
    root = path.parent.resolve()
    for update in context.get('source_updates', []):
        previous = (root / update['base_context_ref']).resolve()
        if not previous.is_relative_to(root) or previous == path.resolve():
            raise ValidationFailure([update['id'] + ': update baseline must be a retained private context file'])
        before = load_json(previous)
        if before.get('project', {}).get('artifact_id') != context['project']['artifact_id']:
            raise ValidationFailure([update['id'] + ': update baseline belongs to another artifact'])
        old_confirmation = before.get('requirement_confirmation', {})
        current_confirmation = context['requirement_confirmation']
        if any(old_confirmation.get(k) != current_confirmation.get(k) for k in
               ('summary_event_ref', 'response_event_ref', 'response_ref', 'response_text', 'snapshot_sha256')):
            # A genuinely new overall baseline starts a new update history, preserving the prior files.
            raise ValidationFailure([update['id'] + ': update must preserve its original overall confirmation'])
        old_questions = {q['id'] for q in before.get('open_questions', [])}
        decisions = {d['id']: d for d in context['decisions']}
        for change in update['changes']:
            for ref in change['decision_refs']:
                decision = decisions.get(ref, {})
                qid = decision.get('question_id')
                if (decision.get('evidence_kind') == 'document' and qid and not decision.get('question_event_ref')
                        and qid not in old_questions):
                    raise ValidationFailure([ref + ': document resolution must preserve the actual earlier workbook question'])


def main():
    """Summarize recorded changes after validation; never infer or approve a rule."""
    import argparse
    import json
    from pathlib import Path
    from artifact_tools import load_json, schema_errors, DESIGNER_SCHEMA_ROOT, ValidationFailure
    parser = argparse.ArgumentParser(description='Report source-update impacts and actual case changes; does not approve or validate the full delivery.')
    parser.add_argument('context', type=Path)
    parser.add_argument('--update', required=True)
    args = parser.parse_args()
    path = args.context.resolve()
    context = load_json(path)
    errors = schema_errors(context, DESIGNER_SCHEMA_ROOT / 'design-context.schema.json')
    if errors:
        raise ValidationFailure(errors)
    errors = update_errors(context)
    if errors:
        raise ValidationFailure(errors)
    validate_update_files(context, path)
    update = next((u for u in context.get('source_updates', []) if u['id'] == args.update), None)
    if update is None:
        raise ValidationFailure(['unknown source update: ' + args.update])
    points = load_json(path.with_name('test-points.json'))
    manifest = load_json(path.with_name('test-manifest.json'))
    previous = load_json((path.parent / update['base_context_ref']).with_name('test-manifest.json'))
    if any(m.get('project', {}).get('artifact_id') != context['project']['artifact_id'] for m in (points, manifest, previous)):
        raise ValidationFailure(['source update artifacts belong to different projects'])
    refs = {r for c in update['changes'] for r in c['rule_refs']}
    print(json.dumps({'update_id': update['id'], 'source_refs': update['source_refs'], 'changes': update['changes'],
                     'impact': affected_artifacts(context, refs, points, manifest),
                     'case_changes': artifact_changes(previous, manifest),
                     'open_questions': context['open_questions']}, ensure_ascii=True, indent=2))
    return 0
