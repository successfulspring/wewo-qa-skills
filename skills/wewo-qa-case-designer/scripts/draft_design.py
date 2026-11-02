"""Explicit unknown business expectations, shared by draft validation and views."""
from __future__ import annotations


def is_draft(artifact):
    return artifact.get('stage', 'final') == 'draft'


def pending_errors(value, *, final, questions=None):
    """Validate each recorded uncertainty without guessing an expected value."""
    errors = []
    if isinstance(value, dict):
        if value.get('status') == 'pending' and 'question_refs' in value:
            label = value.get('id', 'business expectation')
            if final:
                errors.append(label + ': pending business expectation cannot be finalized')
            if questions is not None:
                for qid in value['question_refs']:
                    if qid not in questions:
                        errors.append(label + ': unknown pending question ' + qid)
        for child in value.values():
            errors.extend(pending_errors(child, final=final, questions=questions))
    elif isinstance(value, list):
        for child in value:
            errors.extend(pending_errors(child, final=final, questions=questions))
    return errors


def question_refs(value):
    result = set()
    if isinstance(value, dict):
        result.update(value.get('question_refs', []))
        for key, child in value.items():
            if key != 'question_refs':
                result.update(question_refs(child))
    elif isinstance(value, list):
        for child in value:
            result.update(question_refs(child))
    return result


def pending_text(value, tr):
    return tr('待确认') + ': ' + ', '.join(sorted(question_refs(value)))


def question_rows(context, manifest, points=None):
    """One question inventory; impacts are derived from references, never edited twice."""
    from artifact_tools import walk_test_points
    leaves = list(walk_test_points(points['tree'])) if points else []
    rows = []
    for q in context['open_questions']:
        qid = q['id']
        cases = [c for c in manifest['cases'] if qid in question_refs(c)]
        point_ids = {p['id'] for p in leaves if qid in question_refs(p)}
        point_ids.update(p for c in cases for a in c['assertions'] if qid in question_refs(a) for p in a['test_point_refs'])
        rules = [r['id'] for r in context['rules'] if qid in question_refs(r)]
        rows.append([qid, '\n'.join(q.get('source_refs', [])), q['description'], q['impact'],
                     '\n'.join(rules), '\n'.join(sorted(point_ids)), '\n'.join(c['id'] for c in cases),
                     '\n'.join(q.get('options', []))])
    return rows
