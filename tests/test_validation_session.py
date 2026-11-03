import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('tooling/runtime', 'skills/wewo-qa-case-designer/scripts', 'skills/wewo-qa-case-executor/scripts', 'tests')]
from validation_session import session, checked
from artifact_tools import load_json, write_text_atomic, ValidationFailure
from design_context import validate_design_context_data


class ValidationSessionTests(unittest.TestCase):
    def test_same_content_reuses_success_but_mutation_and_modes_do_not(self):
        calls = []
        @checked
        def check(value, *, final):
            calls.append((copy.deepcopy(value), final))
            if value.get('bad') or final:
                raise ValueError('invalid')
        with session() as s:
            data = {'a': [1]}
            check(data, final=False)
            check(copy.deepcopy(data), final=False)
            data['a'].append(2)
            check(data, final=False)
            for _ in range(2):
                with self.assertRaises(ValueError): check(data, final=True)
            self.assertEqual(len(calls), 4)
            self.assertEqual(s.metrics['check_hits'], 1)
        with session(): check(data, final=False)
        self.assertEqual(len(calls), 5)

    def test_parsed_copy_cannot_poison_snapshot_and_own_write_is_reloaded(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'data.json'
            p.write_text('{"x": [1]}')
            with session() as s:
                a = load_json(p); a['x'].append(2)
                self.assertEqual(load_json(p), {'x': [1]})
                self.assertEqual(s.metrics['file_reads'], 1)
                write_text_atomic(p, '{"x": [3]}')
                self.assertEqual(load_json(p), {'x': [3]})

    def test_external_change_cannot_finish_using_cached_input(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'data.json'; p.write_text('{"x": 1}')
            with self.assertRaisesRegex(ValidationFailure, 'input changed'):
                with session():
                    load_json(p)
                    p.write_text('{"x": 2}')
                    load_json(p)

    def test_optimized_and_standalone_checks_reject_same_invalid_contexts(self):
        good = load_json(ROOT / 'tests/fixtures/design-context.json')
        variants = [copy.deepcopy(good) for _ in range(4)]
        variants[0]['rules'][0]['segment_refs'] = ['SEG-missing']
        variants[1]['requirement_items'][0]['start'] = -1
        variants[2]['requirement_confirmation']['status'] = 'draft'
        variants[3]['rules'][0]['object_refs'] = ['OBJ-missing']
        validate_design_context_data(good)
        for data in variants:
            with self.assertRaises(ValidationFailure) as plain: validate_design_context_data(data)
            with session():
                with self.assertRaises(ValidationFailure) as shared: validate_design_context_data(data)
            self.assertEqual(plain.exception.errors, shared.exception.errors)

    def test_schema_compiles_once_per_content_within_operation(self):
        good = load_json(ROOT / 'tests/fixtures/design-context.json')
        with session() as s:
            validate_design_context_data(good)
            changed = copy.deepcopy(good); changed['generated_at'] = '2026-11-02T00:00:00Z'
            validate_design_context_data(changed)
            self.assertEqual(s.metrics['schema_compiles'], 1)


if __name__ == '__main__': unittest.main()
