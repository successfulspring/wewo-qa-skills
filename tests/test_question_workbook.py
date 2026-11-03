"""Clarification precedes design and stays one editable, evidence-backed workbook."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / p) for p in ('tooling/runtime', 'skills/wewo-qa-case-designer/scripts', 'skills/wewo-qa-case-executor/scripts', 'tests')]
from openpyxl import load_workbook
from artifact_tools import ValidationFailure, sha256_file
from artifact_factory import write_json, seal_synthetic_readiness
from test_designer_drafts import draft_set
from design_context import validate_design_context_data
from question_workbook import HEADERS, ANSWER, render_workbook, validate_workbook, read_workbook, import_answers, clarification_rows


def initial_context(directory, *, language='zh-CN'):
    context, _, _, _ = draft_set(directory, language=language)
    for name in ('test-points.json', 'test-manifest.json'):
        (directory / name).unlink()
    for rule in context['rules']:
        rule.update(coverage=[], design_models=[], factors=[])
    context['requirement_confirmation'] = {'status':'draft'}
    context['dialogue_events'] = context['dialogue_events'][:2]
    seal_synthetic_readiness(context)
    path = directory / 'design-context.json'
    write_json(path, context)
    return context, path


class QuestionWorkbookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / '.qa-state'
        self.state.mkdir()
        self.context, self.path = initial_context(self.state)

    def edit(self, output, value, *, column=ANSWER + 1):
        book = load_workbook(output)
        book['需求澄清'].cell(2, column, value)
        book.save(output)
        book.close()

    def record_reply(self, packet):
        c = self.context
        c['dialogue_events'] += [
            {'id':'EV-Q-SHEET', 'kind':'question', 'message_ref':'synthetic://displayed-initial-sheet',
             'question_ids':['Q2.1'], 'text':'[SYNTHETIC] Q2.1 Which member name is displayed?'},
            {'id':'EV-A-SHEET', 'kind':'answer', 'message_ref':'synthetic://returned-sheet/' + packet['sha256'],
             'question_ids':[r['question_id'] for r in packet['responses']], 'in_reply_to':'EV-Q-SHEET',
             'text':'[SYNTHETIC] Returned workbook reply cells.', 'responses':packet['responses']}]
        c['branch_reviews'].append({'answer_event_ref':'EV-A-SHEET', 'unit_refs':['RU-001'],
            'note':'Synthetic partial reply is retained without assuming its missing business rule.'})
        write_json(self.path, c)

    def test_initial_sheet_needs_no_confirmation_points_cases_or_design_plan(self):
        self.context['open_questions'][0]['blocking'] = True
        write_json(self.path, self.context)
        output = render_workbook(self.path)
        validate_workbook(self.path)
        _, rows = read_workbook(output)
        self.assertEqual(output.name, 'requirement-clarifications.xlsx')
        self.assertEqual({p.name for p in self.state.parent.iterdir()}, {'.qa-state', output.name})
        self.assertIn('尚未生成用例', rows[0][6])
        self.assertEqual(rows[0][-1], '是')
        self.assertNotIn('TP-', rows[0][5])
        self.assertEqual(self.context['requirement_confirmation']['status'], 'draft')

    def test_unread_material_or_stale_audit_cannot_masquerade_as_complete_reading(self):
        self.context['segments'][0]['read_status'] = 'unread'
        write_json(self.path, self.context)
        with self.assertRaises(ValidationFailure):
            render_workbook(self.path)

    def test_empty_queue_still_delivers_stable_sheet_without_inventing_questions(self):
        self.context['open_questions'] = []
        rule = self.context['rules'][0]
        rule.update(status='confirmed', expected='Synthetic known display')
        rule.pop('question_refs')
        seal_synthetic_readiness(self.context)
        write_json(self.path, self.context)
        output = render_workbook(self.path)
        self.assertEqual(read_workbook(output)[1], [])

    def test_unreviewed_cell_reply_cannot_be_overwritten_or_auto_close_question(self):
        output = render_workbook(self.path)
        self.edit(output, '待定：显示内容由产品补充。')
        before = self.path.read_bytes()
        packet = import_answers(self.path)
        self.assertEqual(packet['responses'], [{'question_id':'Q2.1', 'text':'待定：显示内容由产品补充。'}])
        self.assertEqual(before, self.path.read_bytes())
        with self.assertRaisesRegex(ValidationFailure, 'unreviewed clarification answer'):
            render_workbook(self.path)
        with self.assertRaises(ValidationFailure):
            validate_workbook(self.path)
        self.record_reply(packet)
        render_workbook(self.path)
        _, rows = read_workbook(output)
        self.assertEqual(rows[0][ANSWER], packet['responses'][0]['text'])
        self.assertEqual(rows[0][8], '待确认')
        self.assertEqual(import_answers(self.path)['responses'], [])
        self.assertEqual(self.context['requirement_confirmation']['status'], 'draft')

    def test_question_or_generated_state_edits_are_detected(self):
        output = render_workbook(self.path)
        self.edit(output, 'Silently change the question', column=3)
        with self.assertRaises(ValidationFailure):
            import_answers(self.path)
        with self.assertRaises(ValidationFailure):
            render_workbook(self.path)

    def test_old_reply_to_reworded_question_needs_explicit_reconciliation(self):
        output = render_workbook(self.path)
        self.edit(output, 'A')
        self.context['open_questions'][0]['description'] = 'Different business choice'
        write_json(self.path, self.context)
        with self.assertRaisesRegex(ValidationFailure, 'changed or missing question'):
            import_answers(self.path)

    def test_formula_in_reply_is_rejected_and_authored_formula_text_is_literal(self):
        self.context['open_questions'][0]['description'] = '=SUM(1,2) is literal business text'
        write_json(self.path, self.context)
        output = render_workbook(self.path)
        self.assertEqual(read_workbook(output)[1][0][2], self.context['open_questions'][0]['description'])
        self.edit(output, '=1+2')
        with self.assertRaisesRegex(ValidationFailure, 'formulas'):
            import_answers(self.path)

    def test_sorting_is_allowed_but_deleted_or_duplicate_rows_are_rejected(self):
        extra = dict(self.context['open_questions'][0], id='Q2.2', description='Second concrete decision')
        self.context['open_questions'].append(extra)
        write_json(self.path, self.context)
        output = render_workbook(self.path)
        book = load_workbook(output)
        sheet = book['需求澄清']
        first, second = list(sheet.values)[1:]
        for col, value in enumerate(second, 1): sheet.cell(2, col).value = value
        for col, value in enumerate(first, 1): sheet.cell(3, col).value = value
        book.save(output)
        validate_workbook(self.path)
        sheet.delete_rows(3)
        book.save(output)
        book.close()
        with self.assertRaises(ValidationFailure):
            read_workbook(output)

    def test_english_sheet_keeps_literal_unicode_questions_and_has_translated_help(self):
        self.context['project']['output_language'] = 'en'
        self.context['open_questions'][0]['description'] = '中文原文 / 😀: Which name?'
        write_json(self.path, self.context)
        output = render_workbook(self.path)
        book = load_workbook(output)
        try:
            self.assertIn('Requirement Clarification', book.sheetnames)
            self.assertEqual(book['Requirement Clarification']['C2'].value, '中文原文 / 😀: Which name?')
            self.assertEqual(book['Requirement Clarification']['J1'].value, 'Reply')
            self.assertEqual(book['Instructions']['B3'].value, 'Initial Business Clarification')
        finally:
            book.close()

    def test_same_file_gains_real_case_links_after_design(self):
        output = render_workbook(self.path)
        _, _, _, manifest = draft_set(self.state)
        result = render_workbook(self.path, draft=True)
        self.assertEqual(result, output)
        row = read_workbook(output)[1][0]
        self.assertIn('QA-LOGIN-001', row[6])
        self.assertIn('TP-LOGIN-NICKNAME', row[5])
        self.assertEqual(row[0], 'Q2.1')
        self.context['open_questions'][0]['impact'] = 'new impact'
        write_json(self.path, self.context)
        with self.assertRaises(ValidationFailure):
            render_workbook(self.path, draft=True)

    def test_resolved_row_is_retained_with_evidence_and_not_reasked(self):
        output = render_workbook(self.path)
        self.edit(output, 'Use member nickname.')
        self.record_reply(import_answers(self.path))
        c = self.context
        question = c['open_questions'].pop()
        c['closed_questions'] = [dict(question, disposition='resolved', resolution_refs=['DEC-002'])]
        c['decisions'].append({'id':'DEC-002', 'unit_id':'RU-001', 'question_id':'Q2.1',
            'topic':'Display name', 'resolution':'Use member nickname.', 'status':'confirmed',
            'response_event_ref':'EV-A-SHEET'})
        rule = c['rules'][0]
        rule.update(status='confirmed', expected='Use member nickname.')
        rule.pop('question_refs')
        rule['decision_refs'].append('DEC-002')
        rule['requirement_refs'].append('REQ-REPLY')
        c['requirement_items'].append({'id':'REQ-REPLY', 'origin_ref':'DEC-002', 'start':0,
            'end':len('Use member nickname.'), 'statement':'Use member nickname.', 'disposition':'requirement', 'rule_refs':[rule['id']]})
        seal_synthetic_readiness(c)
        write_json(self.path, c)
        render_workbook(self.path)
        row = read_workbook(output)[1][0]
        self.assertEqual(row[8], '已解决')
        self.assertEqual(row[10], 'Use member nickname.')
        self.assertTrue(row[11])
        c['closed_questions'] = []
        write_json(self.path, c)
        with self.assertRaisesRegex(ValidationFailure, 'retain resolved questions'):
            render_workbook(self.path)

    def test_closing_question_without_matching_confirmed_decision_is_rejected(self):
        question = self.context['open_questions'].pop()
        self.context['closed_questions'] = [dict(question, disposition='resolved', resolution_refs=['DEC-001'])]
        with self.assertRaisesRegex(ValidationFailure, 'closing a question'):
            validate_design_context_data(self.context, final=False)

    def test_partial_reply_and_new_question_keep_original_id_and_response(self):
        output = render_workbook(self.path)
        self.edit(output, 'Use nickname; length remains undecided.')
        self.record_reply(import_answers(self.path))
        self.context['open_questions'].append(dict(self.context['open_questions'][0], id='Q2.2', description='What is the display length limit?'))
        write_json(self.path, self.context)
        render_workbook(self.path)
        rows = read_workbook(output)[1]
        self.assertEqual([r[0] for r in rows], ['Q2.1', 'Q2.2'])
        self.assertEqual(rows[0][ANSWER], 'Use nickname; length remains undecided.')
        self.assertEqual(rows[1][ANSWER], '')

    def test_clarification_route_cannot_bypass_design_confirmation(self):
        from requirement_readiness import readiness_errors
        self.assertTrue(readiness_errors(self.context, confirmed=True, final=False))
        self.assertTrue(readiness_errors(self.context, confirmed=True, final=False, clarification=True))

    def test_confirming_deferral_does_not_make_an_unknown_rule_partially_resolved(self):
        self.context['decisions'].append({'id':'DEC-002', 'unit_id':'RU-001', 'question_id':'Q2.1',
            'topic':'Keep unanswered', 'resolution':'Undecided; retain the pending question.',
            'status':'confirmed', 'response_event_ref':'synthetic-deferred-reply'})
        row = clarification_rows(self.context)[0]
        self.assertEqual(row[8], '待确认')
        self.assertEqual(row[10], 'Undecided; retain the pending question.')

    def test_legacy_embedded_sheet_import_preserves_case_edits_before_migration(self):
        import hashlib
        import json
        from artifact_language import ArtifactText
        from draft_design import question_rows
        from case_workbook import render_case_workbooks, read_case_workbook, QUESTION_HEADERS
        from xlsx_support import text_cell
        context, _, _, path = draft_set(self.state)
        outputs = render_case_workbooks(path, draft=True)
        full = next(p for p in outputs if p.name.endswith('full.xlsx'))
        book = load_workbook(full)
        metadata = list(book['_baseline'].values)
        generated = json.loads(''.join(r[1] for r in metadata if r[0] == 'design'))
        generated['待确认问题'] = question_rows(context, read_case_workbook(full)[0])
        ArtifactText().add_table(book, '待确认问题', QUESTION_HEADERS, generated['待确认问题'])
        payload = json.dumps(generated, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        rows = [list(r) for r in metadata if r[0] != 'design']
        for row in rows:
            if row[0] == 'format': row[1] = '1.5'
            if row[0] == 'design_sha256': row[1] = hashlib.sha256(payload.encode()).hexdigest()
        rows += [['design', payload]]
        del book['_baseline']
        meta = book.create_sheet('_baseline')
        meta.sheet_state = 'veryHidden'
        for i, values in enumerate(rows, 1):
            for j, value in enumerate(values, 1): text_cell(meta.cell(i,j), value)
        book['测试用例']['C2'] = 'Human corrected legacy case'
        book.save(full)
        book.close()
        candidate, original, _ = read_case_workbook(full)
        self.assertNotEqual(candidate, original)
        self.assertEqual(candidate['cases'][0]['title'], 'Human corrected legacy case')
        with self.assertRaisesRegex(ValidationFailure, 'unreviewed edits'):
            render_case_workbooks(path, draft=True)

    def test_current_draft_delivery_requires_independent_workbook(self):
        from case_workbook import render_case_workbooks
        from render_test_points_xmind import render_xmind_bytes
        from deliverables import validate_delivery
        _, points, _, path = draft_set(self.state)
        render_case_workbooks(path, draft=True)
        (self.state.parent / 'test-points.xmind').write_bytes(render_xmind_bytes(points, draft=True))
        with self.assertRaisesRegex(ValidationFailure, 'requirement-clarifications.xlsx'):
            validate_delivery(self.state.parent, draft=True)
        render_workbook(self.path, draft=True)
        validate_delivery(self.state.parent, draft=True)


if __name__ == '__main__':
    unittest.main()
