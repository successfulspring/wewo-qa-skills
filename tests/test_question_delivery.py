"""Synthetic many-question deliveries preserve decisions across chat and Excel."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / p) for p in ('tooling/runtime', 'skills/wewo-qa-case-designer/scripts',
    'skills/wewo-qa-case-executor/scripts', 'tests')]
from artifact_factory import write_json, seal_synthetic_readiness, seal_synthetic_points, seal_synthetic_cases
from artifact_tools import load_json, sha256_file, ValidationFailure
from case_workbook import render_case_workbooks, read_case_workbook
from test_designer_drafts import draft_set
from question_delivery import render_questions, render_from_manifest


def many_question_set(directory, *, language='en'):
    """A simulated confirmed login draft; all unknowns affect its identity result."""
    context, points, manifest, path = draft_set(directory, language=language)
    original = context['open_questions'][0]
    questions = load_json(ROOT / 'tests/fixtures/delivery-questions.json')
    for question in questions:
        question.update(unit_id=original['unit_id'], material=True, source_refs=original['source_refs'][:])
    context['open_questions'] = questions
    ids = [q['id'] for q in questions]
    def replace_refs(value):
        if isinstance(value, dict):
            if value.get('question_refs') == [original['id']]:
                value['question_refs'] = ids[:]
            for key, child in value.items():
                if key != 'question_refs':
                    replace_refs(child)
        elif isinstance(value, list):
            for child in value:
                replace_refs(child)
    for value in (context, points, manifest):
        replace_refs(value)
    seal_synthetic_readiness(context)
    write_json(directory / 'design-context.json', context)
    points['design_context_baseline']['sha256'] = sha256_file(directory / 'design-context.json')
    seal_synthetic_points(points)
    write_json(directory / 'test-points.json', points)
    manifest['test_points_baseline']['sha256'] = sha256_file(directory / 'test-points.json')
    seal_synthetic_cases(manifest)
    write_json(path, manifest)
    return context, points, manifest, path


class QuestionDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / '.qa-state'
        self.state.mkdir()
        self.context, self.points, self.manifest, self.path = many_question_set(self.state)

    def test_fourteen_decisions_subquestions_and_options_survive_delivery(self):
        before = copy.deepcopy((self.context, self.manifest))
        text = render_from_manifest(self.path, draft=True)
        for question in self.context['open_questions']:
            self.assertIn(question['id'], text)
            self.assertEqual(text.count(question['description']), 1)
            self.assertIn(question['impact'], text)
            for option in question.get('options', []):
                for line in option.splitlines():
                    self.assertIn(line, text)
        self.assertEqual(before, (self.context, self.manifest))

    def test_chat_and_independent_workbook_retain_the_same_decisions_and_case_links(self):
        from openpyxl import load_workbook
        outputs = render_case_workbooks(self.path, draft=True)
        full = next(p for p in outputs if p.name.endswith('full.xlsx'))
        text = render_from_manifest(self.path, draft=True)
        from question_workbook import render_workbook
        book = load_workbook(render_workbook(self.state / 'design-context.json', draft=True))
        try:
            rows = list(book['Requirement Clarification'].values)
            self.assertEqual(len(rows) - 1, 14)
            for row in rows[1:]:
                for index in (0, 1, 2, 3, 6):
                    for value in str(row[index]).splitlines():
                        self.assertIn(value, text)
        finally:
            book.close()
        self.assertIn(self.manifest['cases'][0]['title'], text)
        candidate, original, _ = read_case_workbook(full)
        self.assertEqual(candidate, original)

    def test_partial_answers_leave_only_remaining_questions_in_the_view(self):
        resolved = self.context['open_questions'][:4]
        self.context['open_questions'] = self.context['open_questions'][4:]
        text = render_questions(self.context, self.manifest)
        for question in resolved:
            self.assertNotIn(question['description'], text)
        for question in self.context['open_questions']:
            self.assertIn(question['description'], text)

    def test_no_invented_options_or_case_links_for_unlinked_unknown(self):
        question = self.context['open_questions'][-1]
        self.context['open_questions'] = [question]
        self.manifest['cases'] = []
        text = render_questions(self.context, self.manifest)
        self.assertIn(question['description'], text)
        self.assertIn(question['impact'], text)
        self.assertNotIn('QA-LOGIN-', text)
        self.assertNotIn('Display the account ID.', text)
        self.assertNotIn('options', question)

    def test_partial_subanswer_keeps_remaining_decision_under_its_original_id(self):
        question = next(q for q in self.context['open_questions'] if q['id'] == 'Q2.3')
        answered, _, remaining = question['description'].splitlines()
        question['description'] = remaining
        text = render_questions(self.context, self.manifest)
        self.assertIn(question['id'], text)
        self.assertIn(remaining, text)
        self.assertNotIn(answered, text)

    def test_empty_inventory_does_not_replay_resolved_decisions(self):
        self.context['open_questions'] = []
        text = render_questions(self.context, self.manifest)
        self.assertTrue(text.strip())
        self.assertNotIn('Q1.1', text)
        self.assertNotIn('Reply by question ID', text)

    def test_chinese_labels_keep_literal_question_content(self):
        self.manifest['project']['output_language'] = 'zh-CN'
        self.context['open_questions'][0]['description'] = '显示昵称还是账号？请分别说明。'
        text = render_questions(self.context, self.manifest)
        self.assertIn('显示昵称还是账号？请分别说明。', text)
        self.assertIn('涉及用例', text)
        self.assertIn('请负责人提供上述具体规则', text)

    def test_stale_context_cannot_be_presented_as_current_delivery(self):
        self.context['open_questions'][0]['description'] = 'A newly changed business question'
        write_json(self.state / 'design-context.json', self.context)
        with self.assertRaises(ValidationFailure):
            render_from_manifest(self.path, draft=True)

    def test_pending_draft_requires_the_explicit_draft_route(self):
        with self.assertRaises(ValidationFailure):
            render_from_manifest(self.path)

    def test_rendering_questions_does_not_bypass_overall_confirmation(self):
        response_id = self.context['requirement_confirmation']['response_event_ref']
        self.context['dialogue_events'] = [e for e in self.context['dialogue_events'] if e['id'] != response_id]
        write_json(self.state / 'design-context.json', self.context)
        self.points['design_context_baseline']['sha256'] = sha256_file(self.state / 'design-context.json')
        write_json(self.state / 'test-points.json', self.points)
        self.manifest['test_points_baseline']['sha256'] = sha256_file(self.state / 'test-points.json')
        write_json(self.path, self.manifest)
        with self.assertRaises(ValidationFailure):
            render_from_manifest(self.path, draft=True)

    def test_cli_preserves_unicode_under_legacy_windows_output_encoding(self):
        env = dict(os.environ, PYTHONIOENCODING='gbk', PYTHONUTF8='0')
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'tooling/runtime/wewo_qa_cli.py'),
            'render-open-questions', str(self.path), '--draft'], env=env, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf8', errors='replace'))
        text = result.stdout.decode('utf8').replace('\r\n', '\n')
        for question in self.context['open_questions']:
            self.assertIn(question['description'], text)


if __name__ == '__main__':
    unittest.main()
