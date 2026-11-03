"""Bind overall understanding and scoped amendments to actual human replies."""
from requirement_coverage import digest


def entity_projection(ref, item):
    excluded = set()
    if ref == 'PROJECT':
        excluded = {'output_language'}
    elif ref.startswith('RULE-'):
        excluded = {'coverage', 'design_models', 'factors', 'requirement_refs', 'decision_refs', 'question_refs'}
    elif ref.startswith('RU-'):
        excluded = {'status'}
    return {k: v for k, v in item.items() if k not in excluded}


def business_snapshot(context):
    """Business content only: conversation bookkeeping is not a new product rule."""
    result = {'PROJECT': digest({k:v for k,v in context['project'].items() if k != 'output_language'})}
    for collection in ('sources', 'segments', 'objects', 'relationships', 'flows', 'requirement_units', 'rules'):
        for item in context[collection]:
            result[item['id']] = digest(entity_projection(item['id'], item))
    return result


def confirmation_errors(context, *, final=True):
    from requirement_readiness import dialogue_links
    confirmation = context['requirement_confirmation']
    events = {e['id']:e for e in context['dialogue_events']}
    positions = {e['id']:i for i, e in enumerate(context['dialogue_events'])}
    summary = events.get(confirmation.get('summary_event_ref'), {})
    response = events.get(confirmation.get('response_event_ref'), {})
    errors = []
    if confirmation['status'] != 'confirmed' or not all(confirmation.get(k) for k in ('confirmed_at','response_ref','response_text')):
        errors.append('requirements need explicit user confirmation with the actual response before test points')
    if response.get('kind') != 'confirmation' or response.get('in_reply_to') != summary.get('id') or response.get('text') != confirmation.get('response_text') or response.get('message_ref') != confirmation.get('response_ref'):
        errors.append('confirmation must preserve the actual reply to the displayed summary')
    baseline = confirmation.get('baseline')
    snapshot = confirmation.get('snapshot_sha256')
    if summary.get('kind') != 'summary' or summary.get('snapshot_sha256') != snapshot:
        errors.append('confirmation must bind the actual displayed summary')
    current = business_snapshot(context)
    if baseline is None:
        if snapshot != digest(current):
            errors.append('confirmed requirement facts changed; record the confirmed baseline and explicit amendments or reconfirm requirements')
        return errors
    if digest(baseline) != snapshot:
        errors.append('confirmation baseline does not match its displayed summary digest')
    amendments = {a['ref']:a for a in confirmation.get('amendments', [])}
    decisions = {d['id']:d for d in context['decisions']}
    _, asked, answered, latest = dialogue_links(context)
    units = {u['id']:u for u in context['requirement_units']}
    rules = {r['id']:r for r in context['rules']}
    for ref in set(baseline) | set(current):
        if baseline.get(ref) == current.get(ref):
            continue
        amendment = amendments.get(ref, {})
        if not amendment or amendment.get('sha256') != current.get(ref):
            errors.append(ref + ': changed business content needs a scoped confirmed amendment')
            continue
        if amendment.get('kind') in {'evidence', 'pending'}:
            from source_updates import nonbusiness_amendment_errors
            errors.extend(nonbusiness_amendment_errors(context, amendment, baseline, final=final))
            continue
        if not amendment.get('decision_refs'):
            errors.append(ref + ': changed business content needs a scoped confirmed amendment')
            continue
        for did in amendment['decision_refs']:
            decision = decisions.get(did, {})
            response_id, qid = decision.get('response_event_ref'), decision.get('question_id')
            if decision.get('evidence_kind') == 'document':
                from source_updates import document_decision_errors
                errors.extend(document_decision_errors(context, decision))
                if decision.get('status') != 'confirmed':
                    errors.append(ref + ': amendment requires a current confirmed document decision')
            elif decision.get('status') != 'confirmed' or not response_id or answered.get(response_id, {}).get(qid) != asked.get(qid) or response_id != latest.get(qid):
                errors.append(ref + ': amendment requires the current actual business answer: ' + did)
            if decision.get('evidence_kind') != 'document' and positions.get(response_id, -1) <= positions.get(summary.get('id'), -1):
                errors.append(ref + ': amendment answer must follow the confirmed summary')
            if ref in units and decision.get('unit_id') != ref:
                errors.append(ref + ': amendment decision belongs to another requirement unit')
            if ref in rules:
                owners = {u['id'] for u in units.values() if ref in u['rule_refs']}
                # Retired rules cannot remain in an active unit's rule_refs. Keep
                # ownership attributable to the actual confirmed unit instead.
                if rules[ref]['status'] == 'excluded':
                    for uid in units:
                        before = amendments.get(uid, {}).get('before')
                        if (isinstance(before, dict) and before.get('id') == uid
                                and ref in before.get('rule_refs', [])
                                and baseline.get(uid) == digest(entity_projection(uid, before))):
                            owners.add(uid)
                if decision.get('unit_id') not in owners or did not in rules[ref]['decision_refs']:
                    errors.append(ref + ': amendment decision does not support this rule')
    return errors
