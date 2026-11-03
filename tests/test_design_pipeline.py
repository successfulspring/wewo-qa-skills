import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('tooling/runtime', 'skills/wewo-qa-case-designer/scripts', 'skills/wewo-qa-case-executor/scripts', 'tests')]
from artifact_tools import ValidationFailure
from artifact_factory import write_json
from test_question_workbook import initial_context
from test_designer_drafts import draft_set
from design_pipeline import build_delivery
from deliverables import validate_delivery
from state_transaction import publish_batch
from openpyxl import load_workbook, Workbook
from xlsx_support import add_table, wrapped_lines


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / '.qa-state'; self.state.mkdir()

    def test_cli_delivery_report_preserves_unicode_paths_with_legacy_encoding(self):
        import os
        import subprocess
        root = self.root / '需求😀'; state = root / '.qa-state'; state.mkdir(parents=True)
        initial_context(state)
        env = {**os.environ, 'PYTHONIOENCODING':'cp1252', 'PYTHONUTF8':'0'}
        result = subprocess.run([sys.executable, '-B', str(ROOT/'tooling/runtime/wewo_qa_cli.py'),
            'build-deliverables', str(root), '--stage', 'clarification'], capture_output=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout.decode('utf-8'))
        self.assertEqual(report['outputs'], [str(root/'requirement-clarifications.xlsx')])
        self.assertTrue(Path(report['outputs'][0]).is_file())

    def test_first_clarification_then_five_files_with_same_question_inventory(self):
        initial_context(self.state)
        initial = build_delivery(self.root, 'clarification')
        self.assertEqual(len(initial['outputs']), 1)
        draft_set(self.state)
        final = build_delivery(self.root, 'draft')
        self.assertEqual(len(final['outputs']), 5)
        self.assertGreater(final['counters']['check_hits'], 0)
        validate_delivery(self.root, draft=True)
        for suite in ('smoke', 'regression', 'full'):
            book = load_workbook(self.root / f'test-cases.{suite}.xlsx')
            self.assertNotIn('待确认问题', book.sheetnames)
            book.close()

    def test_unimported_reply_preserved_when_batch_fails(self):
        initial_context(self.state); build_delivery(self.root, 'clarification')
        path = self.root / 'requirement-clarifications.xlsx'
        book = load_workbook(path); book['需求澄清'].cell(2, 10, '真实填写待定'); book.save(path); book.close()
        before = path.read_bytes()
        draft_set(self.state)
        with self.assertRaisesRegex(ValidationFailure, 'unreviewed clarification answer'):
            build_delivery(self.root, 'draft')
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((self.root / 'test-points.xmind').exists())

    def test_transaction_restores_previous_files_if_replace_fails(self):
        a, b = self.root / 'a', self.root / 'b'
        a.write_bytes(b'old-a'); b.write_bytes(b'old-b')
        from artifact_tools import write_bytes_atomic
        def write(path, content):
            if path == b and content == b'new-b': raise OSError('simulated locked workbook')
            write_bytes_atomic(path, content)
        with patch('state_transaction.write_bytes_atomic', side_effect=write):
            with self.assertRaises(OSError):
                publish_batch({a: b'new-a', b: b'new-b'}, self.state / 'transactions')
        self.assertEqual(a.read_bytes(), b'old-a'); self.assertEqual(b.read_bytes(), b'old-b')

    def test_cjk_layout_retains_text_and_identifies_unavoidable_height_limit(self):
        book = Workbook(); book.remove(book.active)
        text = '测试人员需要逐项观察保存结果以及关联数据是否保持一致。' * 8
        sheet = add_table(book, 'Cases', ['Steps'], [[text]], {'Steps': 55})
        self.assertEqual(sheet['A2'].value, text)
        self.assertGreater(sheet.row_dimensions[2].height, 80)
        overflow = '\n'.join('步骤' + str(i) for i in range(50))
        add_table(book, 'Long', ['Steps'], [[overflow]], {'Steps': 55})
        self.assertTrue(any(x['sheet'] == 'Long' for x in book._qa_layout_warnings))
        self.assertEqual(book['Long']['A2'].value, overflow)
        self.assertGreater(wrapped_lines('中文' * 20, 30), wrapped_lines('AB' * 20, 30))


if __name__ == '__main__': unittest.main()
