"""Late upstream documents must not become invented approvals or product oracles."""
import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / p) for p in ('tooling/runtime', 'skills/wewo-qa-case-designer/scripts',
                                      'skills/wewo-qa-case-executor/scripts', 'tests')]
from artifact_tools import load_json, sha256_file, ValidationFailure
from requirement_confirmation import business_snapshot, confirmation_errors
from source_updates import document_decision_errors, update_errors, affected_artifacts, artifact_changes


def add_handoff(c, *, approved=False):
    source = {'id': 'SRC-002', 'title': 'Synthetic development handoff', 'type': 'document',
              'locator': 'synthetic://handoff', 'role': 'development', 'applies_to': 'Login v1',
              'authority': 'authoritative' if approved else 'supporting', 'scope': 'included',
              'inventory_status': 'complete', 'method': 'Synthetic fixture'}
    c['sources'].append(source)
    text = 'Home shows the account identifier.' if approved else 'Nickname display is not implemented.'
    segment = {'id': 'SEG-HANDOFF', 'source_id': source['id'], 'anchor': 'behavior', 'kind': 'text',
               'content': text, 'read_status': 'read', 'disposition': 'requirement' if approved else 'context'}
    if not approved:
        segment['review_note'] = 'Reported implementation gap; the requirement remains unchanged.'
    c['segments'].append(segment)
    c['requirement_items'].append({'id': 'REQ-HANDOFF', 'origin_ref': segment['id'], 'start': 0,
        'end': len(text), 'statement': text, 'claim_type': 'business_requirement' if approved else 'implementation_report',
        'disposition': 'requirement' if approved else 'context', 'rule_refs': [c['rules'][0]['id']] if approved else [],
        **({} if approved else {'reason': segment['review_note']})})
    if approved:
        approval = {'id': 'SEG-APPROVAL', 'source_id': source['id'], 'anchor': 'approval', 'kind': 'text',
                    'content': 'Synthetic product owner approves account identifier for Login v1.',
                    'read_status': 'read', 'disposition': 'context', 'review_note': 'Approval evidence, not a separate test obligation.'}
        c['segments'].append(approval)
        c['requirement_items'].append({'id': 'REQ-APPROVAL', 'origin_ref': approval['id'], 'start': 0,
            'end': len(approval['content']), 'statement': approval['content'], 'claim_type': 'background',
            'disposition': 'context', 'rule_refs': [], 'reason': approval['review_note']})
    return source


def update_record(c, *, kind='implementation-gap', disposition='no-change'):
    return {'id': 'UPD-001', 'source_refs': ['SRC-002'], 'base_context_ref': 'history/UPD-001/design-context.json',
        'changes': [{'kind': kind, 'entity_refs': ['SRC-002', 'SEG-HANDOFF'],
                     'requirement_refs': ['REQ-HANDOFF'], 'rule_refs': [c['rules'][0]['id']],
                     'disposition': disposition, 'decision_refs': [], 'question_refs': [],
                     'reason': 'Synthetic late handoff, inspected against the existing business baseline.'}]}


def document_decision(c):
    return {'id': 'DEC-002', 'unit_id': 'RU-001', 'evidence_kind': 'document',
            'topic': 'Displayed identity', 'resolution': 'Home shows the account identifier.', 'status': 'confirmed',
            'requirement_refs': ['REQ-HANDOFF'], 'approval_refs': ['SEG-APPROVAL'],
            'approved_by': 'Synthetic product owner', 'applicability': 'Approved for the current Login v1 scope.'}


def late_document_set(directory, *, language=None, initial=None, chat_question=True):
    """Synthetic product draft -> owner-approved later handoff, with no new reply."""
    from test_designer_drafts import draft_set
    from artifact_factory import write_json, seal_synthetic_points, seal_synthetic_cases
    from requirement_readiness import point_decisions, point_units
    from design_context import requirement_digest
    from requirement_coverage import source_texts, plan_digest
    c, p, m, path = initial if initial else draft_set(directory, language=language)
    c['requirement_confirmation']['baseline'] = business_snapshot(c)
    if chat_question:
        c['dialogue_events'].append({'id': 'EVT-Q-HANDOFF', 'kind': 'question', 'message_ref': 'synthetic://draft/question',
            'text': '[SYNTHETIC] Q2.1 Which name should appear?', 'question_ids': ['Q2.1']})
    write_json(directory / 'history/UPD-001/design-context.json', c)
    write_json(directory / 'history/UPD-001/test-points.json', p)
    write_json(directory / 'history/UPD-001/test-manifest.json', m)
    original_confirmation = copy.deepcopy(c['requirement_confirmation'])
    add_handoff(c, approved=True)
    resolved = load_json(ROOT / 'tests/fixtures/design-context.json')
    p_final = load_json(ROOT / 'tests/fixtures/test-points.json')
    m_final = load_json(ROOT / 'tests/fixtures/valid-test-manifest.json')
    rule = copy.deepcopy(resolved['rules'][0])
    text = rule['expected']
    c['segments'][-2]['content'] = text
    c['requirement_items'][-2].update(statement=text, end=len(text))
    decision = document_decision(c)
    decision.update(resolution=text, question_id='Q2.1')
    if chat_question:
        decision['question_event_ref'] = 'EVT-Q-HANDOFF'
    c['decisions'].append(decision)
    c['requirement_items'].append({'id': 'REQ-DOC-DECISION', 'origin_ref': decision['id'], 'start': 0,
        'end': len(text), 'statement': text, 'disposition': 'requirement', 'rule_refs': [rule['id']]})
    rule['segment_refs'].append('SEG-HANDOFF')
    rule['decision_refs'].append(decision['id'])
    for ref in ('REQ-HANDOFF', 'REQ-DOC-DECISION'):
        rule['requirement_refs'].append(ref)
        rule['design_models'][0]['items'][0]['requirement_refs'].append(ref)
    c['rules'][0] = rule
    c['open_questions'] = []
    c['requirement_units'][0]['status'] = 'confirmed'
    update = update_record(c, kind='revision', disposition='applied')
    update['changes'][0]['entity_refs'] += ['SEG-APPROVAL', rule['id']]
    update['changes'][0]['decision_refs'] = [decision['id']]
    update['changes'][0]['question_refs'] = ['Q2.1']
    c['source_updates'] = [update]
    impact = affected_artifacts(c, [rule['id']])
    c['branch_reviews'].append({'source_update_ref': update['id'], 'unit_refs': impact['unit_refs'],
        'note': 'Synthetic source review: identity resolved; required-field and lockout behavior unchanged.'})
    snapshot = business_snapshot(c)
    c['requirement_confirmation']['amendments'] = [
        {'ref': ref, 'sha256': snapshot[ref], 'kind': 'evidence', 'source_update_ref': update['id']}
        for ref in snapshot.keys() - original_confirmation['baseline'].keys()]
    c['requirement_confirmation']['amendments'].append({'ref': rule['id'], 'sha256': snapshot[rule['id']],
        'kind': 'business', 'decision_refs': [decision['id']]})
    c['schema_version'] = p['schema_version'] = '1.6'
    m['schema_version'] = '1.8'
    c['requirement_review']['snapshot_sha256'] = requirement_digest(c)
    c['coverage_plan'] = {'status': 'frozen', 'frozen_at': '2026-10-29T12:00:00+08:00', 'sha256': plan_digest(c)}
    c['review'] = copy.deepcopy(resolved['review'])
    c['review'].update(plan_sha256=plan_digest(c), source_checks=[{
        'origin_ref': origin, 'content_sha256': hashlib.sha256(value.encode()).hexdigest(),
        'requirement_refs': [i['id'] for i in c['requirement_items'] if i['origin_ref'] == origin],
        'note': 'Synthetic fixture review; every supplied clause accounted for, no real approval or product execution.'
    } for origin, value in source_texts(c).items()])
    p['tree']['children'][0]['children'][1] = p_final['tree']['children'][0]['children'][1]
    target = next(case for case in m['cases'] if case['id'] == 'QA-LOGIN-001')
    target['assertions'][1] = m_final['cases'][0]['assertions'][1]
    p['stage'] = m['stage'] = 'final'
    p['requirement_units'] = point_units(c)
    p['decisions'] = point_decisions(c)
    source = {k:v for k,v in c['sources'][-1].items() if k not in {'scope','inventory_status','method','reason'}}
    p['sources'].append(source)
    m['sources'] = copy.deepcopy(p['sources'])
    m['decisions'] = copy.deepcopy(p['decisions'])
    imported = m.get('review', {}).get('excel_import')
    m['review'] = copy.deepcopy(m_final['review'])
    if imported:
        m['review']['excel_import'] = imported
    write_json(directory / 'design-context.json', c)
    p['design_context_baseline']['sha256'] = sha256_file(directory / 'design-context.json')
    seal_synthetic_points(p)
    write_json(directory / 'test-points.json', p)
    m['test_points_baseline']['sha256'] = sha256_file(directory / 'test-points.json')
    seal_synthetic_cases(m)
    write_json(path, m)
    return c, p, m, path, original_confirmation


class SourceUpdateTests(unittest.TestCase):
    def setUp(self):
        self.c = load_json(ROOT / 'tests/fixtures/design-context.json')
        self.c['requirement_confirmation']['baseline'] = business_snapshot(self.c)
        self.original = copy.deepcopy(self.c)

    def evidence_amendments(self):
        current = business_snapshot(self.c)
        self.c['requirement_confirmation']['amendments'] = [
            {'ref': ref, 'sha256': current[ref], 'kind': 'evidence', 'source_update_ref': 'UPD-001'}
            for ref in current.keys() - business_snapshot(self.original).keys()]

    def test_late_implementation_gap_preserves_oracle_and_original_confirmation(self):
        add_handoff(self.c)
        self.c['source_updates'] = [update_record(self.c)]
        self.evidence_amendments()
        self.assertEqual(confirmation_errors(self.c), [])
        self.assertEqual(update_errors(self.c), [])
        self.assertEqual(self.c['rules'], self.original['rules'])
        self.assertEqual(self.c['requirement_confirmation']['response_text'],
                         self.original['requirement_confirmation']['response_text'])

    def test_evidence_label_cannot_approve_changed_expected(self):
        add_handoff(self.c)
        self.c['source_updates'] = [update_record(self.c)]
        self.evidence_amendments()
        rule = self.c['rules'][0]
        rule['expected'] = 'An unsupported different oracle'
        self.c['source_updates'][0]['changes'][0]['entity_refs'].append(rule['id'])
        self.c['requirement_confirmation']['amendments'].append({
            'ref': rule['id'], 'sha256': business_snapshot(self.c)[rule['id']], 'kind': 'evidence',
            'source_update_ref': 'UPD-001', 'before': self.original['rules'][0]})
        self.assertTrue(any('business meaning' in e for e in confirmation_errors(self.c)))

    def test_document_decision_needs_no_fabricated_question_or_answer(self):
        add_handoff(self.c, approved=True)
        decision = document_decision(self.c)
        self.c['decisions'].append(decision)
        self.assertEqual(document_decision_errors(self.c, decision), [])
        self.assertNotIn('question_id', decision)
        self.assertNotIn('response_event_ref', decision)

    def test_implementation_report_cannot_support_document_business_decision(self):
        add_handoff(self.c, approved=True)
        self.c['requirement_items'][-2]['claim_type'] = 'implementation_report'
        self.assertTrue(document_decision_errors(self.c, document_decision(self.c)))

    def test_historical_or_unread_approval_cannot_resolve_current_rule(self):
        add_handoff(self.c, approved=True)
        self.c['sources'][-1]['authority'] = 'historical'
        self.assertTrue(document_decision_errors(self.c, document_decision(self.c)))
        self.c['sources'][-1]['authority'] = 'authoritative'
        self.c['segments'][-1]['read_status'] = 'needs-review'
        self.assertTrue(document_decision_errors(self.c, document_decision(self.c)))

    def test_duplicate_update_and_missing_pending_question_are_rejected(self):
        add_handoff(self.c)
        record = update_record(self.c, kind='conflict', disposition='pending')
        self.c['source_updates'] = [record, copy.deepcopy(record)]
        errors = update_errors(self.c)
        self.assertTrue(any('duplicate' in e for e in errors))
        self.assertTrue(any('question' in e for e in errors))

    def test_impact_includes_related_units_points_and_cases(self):
        points = load_json(ROOT / 'tests/fixtures/test-points.json')
        manifest = load_json(ROOT / 'tests/fixtures/valid-test-manifest.json')
        self.c['requirement_units'][1]['depends_on'] = ['RU-001']
        impact = affected_artifacts(self.c, [self.c['rules'][0]['id']], points, manifest)
        self.assertEqual(set(impact['unit_refs']), {'RU-001', 'RU-002'})
        self.assertTrue(impact['point_refs'])
        self.assertEqual(set(impact['case_refs']), {c['id'] for c in manifest['cases']})

    def test_case_delta_distinguishes_unchanged_modified_added_and_retired(self):
        before = {'cases': [{'id': 'A', 'title': 'keep'}, {'id': 'B', 'title': 'old'}, {'id': 'C'}]}
        after = {'cases': [{'id': 'A', 'title': 'keep'}, {'id': 'B', 'title': 'new'}, {'id': 'D'}]}
        self.assertEqual(artifact_changes(before, after),
                         {'added': ['D'], 'modified': ['B'], 'retired': ['C'], 'unchanged': ['A']})

    def test_full_document_resolution_roundtrip_without_new_human_reply(self):
        from artifact_tools import validate_manifest_file
        from case_workbook import render_case_workbooks, read_case_workbook
        from render_test_points_xmind import render_xmind_bytes
        from deliverables import validate_delivery
        for language in ('zh-CN', 'en'):
            with self.subTest(language=language), tempfile.TemporaryDirectory() as folder:
                state = Path(folder) / '.qa-state'
                state.mkdir()
                c, p, m, path, original = late_document_set(state, language=language)
                validate_manifest_file(path)
                for output in render_case_workbooks(path):
                    candidate, baseline, _ = read_case_workbook(output)
                    self.assertEqual(candidate, baseline)
                (state.parent / 'test-points.xmind').write_bytes(render_xmind_bytes(p))
                from question_workbook import render_workbook
                render_workbook(state / 'design-context.json')
                validate_delivery(state.parent)
                self.assertEqual(c['requirement_confirmation']['snapshot_sha256'], original['snapshot_sha256'])
                self.assertEqual(c['requirement_confirmation']['response_text'], original['response_text'])
                self.assertEqual(len([e for e in c['dialogue_events'] if e['kind'] == 'confirmation']), 1)
                old = load_json(state / 'history/UPD-001/test-manifest.json')
                delta = artifact_changes(old, m)
                self.assertEqual(delta['added'], [])
                self.assertEqual(delta['retired'], [])
                self.assertEqual(len(delta['modified']), 1)
                self.assertGreater(len(delta['unchanged']), 0)

    def test_missing_retained_baseline_is_not_accepted(self):
        from artifact_tools import validate_manifest_file
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder)
            c, p, m, path, _ = late_document_set(state)
            (state / 'history/UPD-001/design-context.json').unlink()
            with self.assertRaisesRegex(ValidationFailure, 'cannot read'):
                validate_manifest_file(path)

    def test_imported_title_survives_later_document_resolution_in_same_case(self):
        from test_designer_drafts import draft_set
        from case_workbook import render_case_workbooks, import_case_workbooks, read_case_workbook
        from openpyxl import load_workbook
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / '.qa-state'
            state.mkdir()
            c, p, m, path = draft_set(state)
            outputs = render_case_workbooks(path, draft=True)
            full = next(f for f in outputs if f.name.endswith('full.xlsx'))
            book = load_workbook(full)
            book['测试用例'].cell(2, 3, 'Tester preserved title')
            book.save(full)
            book.close()
            m = import_case_workbooks(path)
            _, _, _, path, _ = late_document_set(state, initial=(c, p, m, path))
            for output in render_case_workbooks(path):
                candidate, _, _ = read_case_workbook(output)
                self.assertEqual(next(case for case in candidate['cases'] if case['id'] == 'QA-LOGIN-001')['title'], 'Tester preserved title')

    def test_document_approval_does_not_authorize_another_unit(self):
        add_handoff(self.c, approved=True)
        d = document_decision(self.c)
        d['unit_id'] = 'RU-002'
        self.c['decisions'].append(d)
        r = self.c['rules'][0]
        r.update(expected=d['resolution'], decision_refs=[d['id']])
        self.c['requirement_confirmation']['amendments'] = [
            {'ref': r['id'], 'sha256': business_snapshot(self.c)[r['id']], 'decision_refs': [d['id']]}]
        self.assertTrue(any('does not support this rule' in e for e in confirmation_errors(self.c)))

    def test_local_conflict_can_stay_pending_without_changing_known_conditions(self):
        add_handoff(self.c)
        update = update_record(self.c, kind='conflict', disposition='pending')
        r = self.c['rules'][0]
        update['changes'][0]['entity_refs'].append(r['id'])
        update['changes'][0]['question_refs'] = ['Q2.1']
        self.c['source_updates'] = [update]
        self.c['open_questions'] = [{'id':'Q2.1','unit_id':'RU-001','description':'Which identity?',
            'impact':'Name only','material':True}]
        r.update(status='pending', question_refs=['Q2.1'], rationale='Two current specifications conflict')
        r.pop('expected')
        self.evidence_amendments()
        self.c['requirement_confirmation']['amendments'].append({'ref': r['id'], 'kind':'pending',
            'source_update_ref':'UPD-001','sha256':business_snapshot(self.c)[r['id']], 'before':self.original['rules'][0]})
        self.assertEqual(confirmation_errors(self.c, final=False), [])
        self.assertTrue(confirmation_errors(self.c))
        r['action'] = 'An unrelated new action'
        self.c['requirement_confirmation']['amendments'][-1]['sha256'] = business_snapshot(self.c)[r['id']]
        self.assertTrue(any('known condition or action' in e for e in confirmation_errors(self.c, final=False)))

    def test_restatement_can_extend_rule_provenance_without_new_approval(self):
        add_handoff(self.c)
        self.c['source_updates'] = [update_record(self.c, kind='corroboration')]
        r = self.c['rules'][0]
        r['segment_refs'].append('SEG-HANDOFF')
        self.c['source_updates'][0]['changes'][0]['entity_refs'].append(r['id'])
        self.evidence_amendments()
        amendment = {'ref':r['id'], 'kind':'evidence','source_update_ref':'UPD-001',
                     'sha256':business_snapshot(self.c)[r['id']], 'before':copy.deepcopy(self.original['rules'][0])}
        self.c['requirement_confirmation']['amendments'].append(amendment)
        self.assertEqual(confirmation_errors(self.c), [])
        amendment['before']['expected'] = 'Fabricated historical expectation'
        self.assertTrue(any('original confirmed entity' in e for e in confirmation_errors(self.c)))

    def test_document_resolution_cannot_close_a_new_followup(self):
        from requirement_readiness import dialogue_errors
        with tempfile.TemporaryDirectory() as folder:
            c, _, _, _, _ = late_document_set(Path(folder))
            event = c['dialogue_events'][-1]
            c['dialogue_events'].append({**event,'id':'EVT-NEW','message_ref':'synthetic://followup',
                                        'revisits':{'Q2.1':event['id']}})
            self.assertTrue(any('latest' in e for e in dialogue_errors(c, reviewed=True)))

    def test_document_can_resolve_a_recorded_workbook_question_without_invented_dialogue(self):
        from requirement_readiness import dialogue_errors
        with tempfile.TemporaryDirectory() as folder:
            c, _, _, _, _ = late_document_set(Path(folder))
            c['dialogue_events'] = [e for e in c['dialogue_events'] if e['id'] != 'EVT-Q-HANDOFF']
            c['decisions'][-1].pop('question_event_ref')
            self.assertEqual(dialogue_errors(c, reviewed=True), [])

    def test_workbook_resolution_must_exist_in_retained_question_history(self):
        from artifact_factory import write_json
        from source_updates import validate_update_files
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder)
            c, _, _, path, _ = late_document_set(state, chat_question=False)
            previous_path = state / c['source_updates'][0]['base_context_ref']
            before = load_json(previous_path)
            before['open_questions'] = []
            write_json(previous_path, before)
            with self.assertRaisesRegex(ValidationFailure, 'actual earlier workbook question'):
                validate_update_files(c, path.with_name('design-context.json'))

    def test_manifest_cannot_change_document_approval_details(self):
        from artifact_tools import validate_manifest_data
        with tempfile.TemporaryDirectory() as folder:
            _, p, m, _, _ = late_document_set(Path(folder))
            m['decisions'][-1]['approved_by'] = 'Someone else'
            with self.assertRaisesRegex(ValidationFailure, 'approved_by'):
                validate_manifest_data(m, p, final=False)

    def test_retirement_record_requires_a_business_decision(self):
        add_handoff(self.c)
        self.c['source_updates'] = [update_record(self.c, kind='retirement', disposition='applied')]
        self.assertTrue(any('authoritative decision' in e for e in update_errors(self.c)))

    def retired_rule(self):
        add_handoff(self.c, approved=True)
        decision = document_decision(self.c)
        self.c['decisions'].append(decision)
        rule, unit = self.c['rules'][0], self.c['requirement_units'][0]
        before = copy.deepcopy(unit)
        rule.update(status='excluded', rationale='Synthetic approved retirement.',
                    decision_refs=[decision['id']])
        unit['rule_refs'].remove(rule['id'])
        self.c['source_updates'] = [update_record(self.c, kind='retirement', disposition='applied')]
        self.c['source_updates'][0]['changes'][0]['entity_refs'].append('SEG-APPROVAL')
        self.c['source_updates'][0]['changes'][0]['decision_refs'] = [decision['id']]
        self.evidence_amendments()
        current = business_snapshot(self.c)
        self.c['requirement_confirmation']['amendments'] += [
            {'ref':rule['id'], 'sha256':current[rule['id']], 'decision_refs':[decision['id']]},
            {'ref':unit['id'], 'sha256':current[unit['id']], 'decision_refs':[decision['id']], 'before':before}]
        return rule, unit, decision

    def test_retired_rule_uses_confirmed_historical_owner_not_active_membership(self):
        rule, unit, _ = self.retired_rule()
        self.assertNotIn(rule['id'], unit['rule_refs'])
        self.assertEqual(confirmation_errors(self.c), [])

    def test_retired_rule_rejects_fabricated_historical_owner(self):
        self.retired_rule()
        self.c['requirement_confirmation']['amendments'][-1]['before']['title'] = 'Fabricated owner'
        self.assertTrue(any('does not support this rule' in e for e in confirmation_errors(self.c)))

    def test_retired_rule_still_requires_matching_actual_decision(self):
        _, _, decision = self.retired_rule()
        decision['unit_id'] = 'RU-002'
        self.assertTrue(any('does not support this rule' in e for e in confirmation_errors(self.c)))
        decision['unit_id'] = 'RU-001'
        decision['status'] = 'assumed'
        self.assertTrue(any('current confirmed document decision' in e for e in confirmation_errors(self.c)))

    def test_new_source_branch_review_cannot_omit_dependencies(self):
        from requirement_readiness import dialogue_errors
        with tempfile.TemporaryDirectory() as folder:
            c, _, _, _, _ = late_document_set(Path(folder))
            c['requirement_units'][1]['depends_on'] = ['RU-001']
            self.assertTrue(any('dependency units' in e for e in dialogue_errors(c, reviewed=True)))

    def test_source_update_summary_uses_actual_case_delta(self):
        import json
        import subprocess
        with tempfile.TemporaryDirectory() as folder:
            c, _, m, path, _ = late_document_set(Path(folder))
            run = subprocess.run([sys.executable, '-B', str(ROOT/'tooling/runtime/wewo_qa_cli.py'),
                'summarize-source-update', str(path.with_name('design-context.json')), '--update','UPD-001'],
                capture_output=True, encoding='utf-8')
            self.assertEqual(run.returncode, 0, run.stderr)
            summary = json.loads(run.stdout)
            self.assertEqual(summary['case_changes']['modified'], [m['cases'][0]['id']])
            self.assertEqual(summary['open_questions'], [])

    def test_summary_preserves_unicode_under_windows_legacy_output_encoding(self):
        import json
        import os
        import subprocess
        from artifact_factory import write_json
        with tempfile.TemporaryDirectory() as folder:
            c, _, _, path, _ = late_document_set(Path(folder))
            reason = '保留已确认的锁定预期，补全昵称显示 ✅'
            c['source_updates'][0]['changes'][0]['reason'] = reason
            context_path = path.with_name('design-context.json')
            write_json(context_path, c)
            env = {**os.environ, 'PYTHONIOENCODING': 'gbk', 'PYTHONUTF8': '0'}
            run = subprocess.run([sys.executable, '-B', str(ROOT/'tooling/runtime/wewo_qa_cli.py'),
                'summarize-source-update', str(context_path), '--update','UPD-001'], capture_output=True, env=env)
            self.assertEqual(run.returncode, 0, run.stderr)
            summary = json.loads(run.stdout.decode('ascii'))
            self.assertEqual(summary['changes'][0]['reason'], reason)


if __name__ == '__main__':
    unittest.main()
