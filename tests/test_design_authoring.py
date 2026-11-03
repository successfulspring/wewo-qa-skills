import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('tooling/runtime', 'skills/wewo-qa-case-designer/scripts', 'skills/wewo-qa-case-executor/scripts', 'tests')]
from artifact_tools import load_json, sha256_file, ValidationFailure, validate_test_points_file, validate_manifest_file, walk_test_points
from artifact_factory import write_json, compact_fixture_cases
from design_authoring import FORMAT, apply_request, record_dialogue, locate_excerpt, Ids, compile_cases, inspect_schema, design_points
from test_question_workbook import initial_context
from test_designer_drafts import draft_set
from design_context import requirement_digest


class AuthoringTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / '.qa-state'; self.state.mkdir()
        self.context, self.path = initial_context(self.state)

    def packet(self, **kwargs):
        return dict(format=FORMAT, base_sha256=sha256_file(self.path), **kwargs)

    def test_literal_excerpt_unicode_and_repeated_text(self):
        item = {'id': 'REQ-001', 'origin_ref': 'SEG-001', 'quote': '名字🙂', 'disposition': 'context', 'rule_refs': []}
        result = locate_excerpt(item, {'SEG-001': '甲名字🙂乙'})
        self.assertEqual((result['start'], result['end']), (1, 4))
        with self.assertRaisesRegex(ValidationFailure, 'ambiguous'):
            locate_excerpt(item, {'SEG-001': '名字🙂名字🙂'})
        self.assertEqual(locate_excerpt(dict(item, occurrence=1), {'SEG-001': '名字🙂名字🙂'})['start'], 3)

    def test_ids_repeat_safely_and_stale_packet_cannot_overwrite(self):
        unit = self.context['requirement_units'][0]['id']
        p = self.packet(upsert={'open_questions': [{'id': '@new', 'unit_id': unit,
            'description': '@new is literal business text', 'impact': 'Clarify this result', 'material': True}]})
        result = apply_request(self.path, p)
        saved = self.path.read_bytes()
        again = apply_request(self.path, p)
        self.assertEqual(again['status'], 'unchanged'); self.assertEqual(saved, self.path.read_bytes())
        added = load_json(self.path)['open_questions'][-1]
        self.assertEqual(added['description'], '@new is literal business text')
        self.assertTrue(added['id'].startswith('Q1.'))
        with self.assertRaisesRegex(ValidationFailure, 'stale'):
            apply_request(self.path, dict(p, upsert={}))

    def test_invalid_patch_does_not_replace_context(self):
        old = self.path.read_bytes()
        with self.assertRaises(ValidationFailure):
            apply_request(self.path, self.packet(upsert={'rules': [{'id': self.context['rules'][0]['id'], 'object_refs': ['OBJ-missing']}]}))
        self.assertEqual(old, self.path.read_bytes())

    def test_summary_then_real_confirmation_does_not_close_questions(self):
        self.context['dialogue_events'] = []
        self.context['branch_reviews'] = []
        self.context['decisions'] = []
        for r in self.context['rules']: r['decision_refs'] = []
        self.context['requirement_items'] = [i for i in self.context['requirement_items'] if not i['origin_ref'].startswith('DEC-')]
        for r in self.context['rules']:
            r['requirement_refs'] = [i['id'] for i in self.context['requirement_items'] if r['id'] in i['rule_refs']]
        write_json(self.path, self.context)
        record_dialogue(self.path, {'base_sha256': sha256_file(self.path), 'event': {
            'id': 'EV-SUM', 'kind': 'summary', 'text': 'Synthetic actual displayed summary', 'message_ref': 'synthetic://summary'}})
        record_dialogue(self.path, {'base_sha256': sha256_file(self.path), 'event': {
            'id': 'EV-CONF', 'kind': 'confirmation', 'text': 'Synthetic actual user agreement; local items pending',
            'message_ref': 'synthetic://reply', 'in_reply_to': 'EV-SUM'}})
        current = load_json(self.path)
        self.assertEqual(current['requirement_confirmation']['status'], 'confirmed')
        self.assertEqual(current['open_questions'], self.context['open_questions'])
        self.assertEqual(current['decisions'], [])

    def test_confirmation_without_displayed_summary_fails(self):
        with self.assertRaisesRegex(ValidationFailure, 'displayed summary'):
            record_dialogue(self.path, {'base_sha256': sha256_file(self.path), 'event': {
                'id': 'EV-C', 'kind': 'confirmation', 'text': 'yes', 'message_ref': 'synthetic://reply', 'in_reply_to': 'missing'}})

    def test_compact_case_preserves_known_and_pending_assertions_and_binds_steps(self):
        _, points, manifest, _ = draft_set(self.state)
        old = manifest['cases'][0]
        authored = copy.deepcopy(old)
        for a in authored['assertions']:
            a['point'] = a['test_point_refs'][0]
            a.pop('expected', None); a.pop('test_point_refs')
        lookup = {a['id']: a['point'] for a in authored['assertions']}
        for step in authored['steps']:
            step['points'] = [lookup[a] for a in step.pop('assertion_refs')]
        result = compile_cases([authored], points, {}, Ids({}, self.context, points, manifest))[0]
        self.assertEqual(result['steps'], old['steps'])
        for a, original in zip(result['assertions'], old['assertions']):
            self.assertEqual(a.get('expected'), original.get('expected'))
            self.assertEqual(a.get('check'), original.get('check'))
        pending = next(a for a in authored['assertions'] if a.get('status') == 'pending')
        pending['check'] = {'kind': 'equals', 'expected_value': 'guess', 'timing': 'after'}
        with self.assertRaisesRegex(ValidationFailure, 'pending oracle'):
            compile_cases([authored], points, {}, Ids({}, self.context, points, manifest))

    def test_aliases_handle_relationships_and_literal_text_separately(self):
        registry = Ids({}, self.context)
        value = registry.aliases({'upsert': {'objects': [{'id': '@a'}, {'id': '@b'}],
            'relationships': [{'id': '@link', 'from_object': '@a', 'to_object': '@b', 'description': '@a and @b are literal'}]}})
        a, b = [x['id'] for x in value['upsert']['objects']]
        relationship = value['upsert']['relationships'][0]
        self.assertEqual((relationship['from_object'], relationship['to_object']), (a, b))
        self.assertEqual(relationship['description'], '@a and @b are literal')

    def test_alias_identity_cannot_change_type_in_later_request(self):
        registry = Ids({}, self.context)
        registry.aliases({'upsert': {'objects': [{'id': '@asset'}]}})
        later = Ids(registry.index, self.context)
        with self.assertRaisesRegex(ValidationFailure, 'alias reused across record types'):
            later.aliases({'upsert': {'rules': [{'id': '@asset'}]}})

    def test_factor_assignment_keys_resolve_alias_but_values_remain_literal(self):
        registry = Ids({}, self.context)
        value = registry.aliases({'upsert': {'rules': [{'id': '@rule',
            'factors': [{'id': '@factor'}], 'design_models': [{'id': '@model',
                'items': [{'id': '@item', 'factor_values': {'@factor': '@literal-value'}}]}]}]}})
        rule = value['upsert']['rules'][0]
        self.assertEqual(rule['design_models'][0]['items'][0]['factor_values'],
                         {rule['factors'][0]['id']: '@literal-value'})

    def test_compilation_preserves_target_dependency_scope(self):
        _, points, manifest, _ = draft_set(self.state)
        authored = copy.deepcopy(manifest['cases'][0])
        authored.pop('runtime_requirement_refs')
        authored['automation'][0]['runtime_requirement_refs'] = ['RT-TARGET-ACCESS']
        result = compile_cases([authored], points, {}, Ids({}, self.context, points, manifest))[0]
        self.assertEqual(result['runtime_requirement_refs'], [])
        self.assertEqual(result['automation'][0]['runtime_requirement_refs'], ['RT-TARGET-ACCESS'])

    def test_explicit_batch_defaults_expand_complete_cases_without_shared_mutable_state(self):
        _, points, manifest, _ = draft_set(self.state)
        original = manifest['cases'][0]
        defaults = {k: copy.deepcopy(original[k]) for k in ('preconditions', 'applicable_targets',
                    'automation', 'runtime_requirement_refs', 'safety')}
        authored = copy.deepcopy(original)
        for key in defaults: authored.pop(key)
        cases = [authored, {**copy.deepcopy(authored), 'id': 'QA-SECOND', 'preconditions': ['Explicit second-case setup']}]
        result = compile_cases(cases, points, {}, Ids({}, self.context, points, manifest), defaults)
        for key in defaults: self.assertEqual(result[0][key], original[key])
        self.assertEqual(result[1]['preconditions'], ['Explicit second-case setup'])
        result[0]['safety']['cleanup'] = 'Mutated local test copy'
        self.assertEqual(result[1]['safety'], defaults['safety'])
        self.assertEqual(defaults['safety'], original['safety'])
        with self.assertRaisesRegex(ValidationFailure, 'Additional properties'):
            apply_request(self.path, self.packet(design={'case_defaults': {'priority': 'P0'}, 'cases': []}))

    def test_initial_request_creates_only_draft_context_and_keeps_missing_reading_visible(self):
        path = self.state / 'new' / 'design-context.json'
        source = copy.deepcopy(self.context['sources'][0])
        segment = copy.deepcopy(next(s for s in self.context['segments'] if s['source_id'] == source['id']))
        segment['read_status'] = 'needs-review'
        result = apply_request(path, {'format': FORMAT, 'base_sha256': None, 'project': self.context['project'],
                                     'upsert': {'sources': [source], 'segments': [segment]}})
        data = load_json(path)
        self.assertEqual(data['requirement_confirmation'], {'status': 'draft'})
        self.assertEqual(data['rules'], [])
        self.assertEqual(data['segments'][0]['read_status'], 'needs-review')
        from design_pipeline import build_delivery
        # No implied reading or automatically manufactured audit allows delivery.
        with self.assertRaises(ValidationFailure):
            from question_workbook import render_workbook
            render_workbook(path)

    def test_schema_inspection_exposes_inline_contracts_without_ambiguous_project_guess(self):
        questions = inspect_schema('design-context:open_questions')['definition']
        self.assertEqual(questions['type'], 'array')
        self.assertIn('description', questions['items']['properties'])
        project = inspect_schema('test-manifest:project')['definition']
        self.assertIn('targets', project['properties'])
        with self.assertRaisesRegex(ValidationFailure, 'ambiguous schema name'):
            inspect_schema('project')
        self.assertIn('open_questions', inspect_schema('list')['design-context']['properties'])

    def test_preflight_does_not_become_an_export_or_final_gate(self):
        from artifact_tools import validate_test_points_data
        _, points, _, _ = draft_set(self.state)
        points['design_review'] = {}
        validate_test_points_data(points, final=False, _authoring=True)
        with self.assertRaisesRegex(ValidationFailure, 'review'):
            validate_test_points_data(points, final=False)
        with self.assertRaisesRegex(ValidationFailure, 'cannot validate a final'):
            validate_test_points_data(points, final=True, _authoring=True)

    def test_derive_points_and_cases_from_authored_outcomes_and_keep_pending(self):
        context, old_points, old_manifest, _ = draft_set(self.state)
        self.path = self.state / 'design-context.json'
        request = self.packet(design={'project': old_points['project'], 'cases': [], 'runtime_requirements': old_manifest['runtime_requirements']})
        apply_request(self.path, request)
        points = load_json(self.state / 'test-points.json')
        self.assertEqual({n['id'] for n in walk_test_points(points['tree']) if not n['children']},
                         {n['id'] for n in walk_test_points(old_points['tree']) if not n['children']})
        self.assertEqual(points['design_review'], {})
        self.assertTrue(any(n['status'] == 'pending' for n in walk_test_points(points['tree'])))
        with self.assertRaisesRegex(ValidationFailure, 'review'):
            validate_test_points_file(self.state / 'test-points.json', final=False)
        notes = {'checked_leaf_refs': [n['id'] for n in walk_test_points(points['tree']) if not n['children']],
                 'atomicity_note': 'Synthetic reviewer checked each independent fixture result.',
                 'visible_path_note': 'Synthetic reviewer checked source conditions and visible paths.'}
        apply_request(self.path, self.packet(review={'points': notes}))
        validate_test_points_file(self.state / 'test-points.json', final=False)
        validate_manifest_file(self.state / 'test-manifest.json', final=False)

    def test_first_design_from_confirmed_context_uses_pending_review_and_compiles_cases(self):
        context, old_points, old_manifest, _ = draft_set(self.state)
        self.path = self.state / 'design-context.json'
        cases = compact_fixture_cases(old_points, old_manifest)
        self.path.with_name('test-points.json').unlink()
        self.path.with_name('test-manifest.json').unlink()
        apply_request(self.path, self.packet(design={'project': old_points['project'],
                      'cases': cases, 'runtime_requirements': old_manifest['runtime_requirements']}))
        actual = load_json(self.path.with_name('test-manifest.json'))
        self.assertEqual(actual['review'], {'status': 'pending'})
        self.assertEqual(len(actual['cases']), len(cases))
        self.assertEqual([a.get('check') for c in actual['cases'] for a in c['assertions']],
                         [a.get('check') for c in old_manifest['cases'] for a in c['assertions']])
        # A successful authoring batch is still not a completed review/export.
        with self.assertRaisesRegex(ValidationFailure, 'review'):
            validate_manifest_file(self.path.with_name('test-manifest.json'), final=False)

    def test_visible_leaf_preserves_subject_and_actual_known_or_pending_result(self):
        context, previous, manifest, _ = draft_set(self.state)
        outcomes = {o['id']: o for r in context['rules'] for m in r['design_models']
                    for item in m['items'] for o in item['outcomes']}
        original = copy.deepcopy(outcomes)
        for language, pending_label in [('zh-CN', '待确认'), ('en', 'Pending confirmation')]:
            project = dict(previous['project'], output_language=language)
            points, _ = design_points(context, project, Ids({}, context, previous, manifest), previous)
            for leaf in walk_test_points(points['tree']):
                if leaf['children']: continue
                outcome = outcomes[leaf['outcome_ref']]
                self.assertIn(outcome['subject'], leaf['title'])
                self.assertIn(outcome['observable'], leaf['title'])
                if outcome.get('status') == 'pending':
                    self.assertIn(pending_label, leaf['title'])
                    self.assertNotIn('expected', leaf['verification'])
                    for qid in outcome['question_refs']: self.assertIn(qid, leaf['title'])
                else:
                    self.assertIn(outcome['expected'], leaf['title'])
                    self.assertEqual(leaf['verification']['expected'], outcome['expected'])
            self.assertEqual(outcomes, original)
    def test_same_outcome_across_distinct_models_shares_leaf_and_preserves_existing_identity(self):
        context, points, manifest, _ = draft_set(self.state)
        self.path = self.state / 'design-context.json'
        rule = next(r for r in context['rules'] if r['design_models'])
        original = rule['design_models'][0]
        shared = copy.deepcopy(original)
        shared['id'] += '-SECOND'
        for item in shared['items']: item['id'] += '-SECOND'
        models = [original, shared, *rule['design_models'][1:]]
        apply_request(self.path, self.packet(upsert={'rules': [{'id': rule['id'], 'design_models': models}]},
                                           design={'project': points['project'], 'cases': []}))
        updated = load_json(self.path.with_name('test-points.json'))
        before = {p['id'] for p in walk_test_points(points['tree']) if not p['children']}
        after = {p['id']: p for p in walk_test_points(updated['tree']) if not p['children']}
        self.assertEqual(set(after), before)
        for first, second in zip(original['items'], shared['items']):
            for outcome in first['outcomes']:
                leaf = next(p for p in after.values() if first['id'] in p['coverage_item_refs'] and p['outcome_ref'] == outcome['id'])
                self.assertIn(second['id'], leaf['coverage_item_refs'])
        saved = self.path.read_bytes()
        bad = copy.deepcopy(shared)
        bad['items'][0]['condition'] += ' with a different business prerequisite'
        with self.assertRaisesRegex(ValidationFailure, 'conflicting planned outcome'):
            apply_request(self.path, self.packet(upsert={'rules': [{'id': rule['id'],
                'design_models': [original, bad, *rule['design_models'][1:]]}]}, design={'cases': []}))
        self.assertEqual(self.path.read_bytes(), saved)

    def test_existing_separate_leaf_ids_are_not_silently_merged(self):
        context, previous, manifest, _ = draft_set(self.state)
        rule = next(r for r in context['rules'] if r['design_models'])
        original = rule['design_models'][0]
        shared = copy.deepcopy(original)
        shared['id'] += '-SECOND'
        for item in shared['items']: item['id'] += '-SECOND'
        rule['design_models'].append(shared)
        first = next(i for i in original['items'] if i['outcomes'])
        second = next(i for i in shared['items'] if i['id'] == first['id'] + '-SECOND')
        oid = first['outcomes'][0]['id']
        leaf = next(p for p in walk_test_points(previous['tree'])
                    if first['id'] in p['coverage_item_refs'] and p.get('outcome_ref') == oid)
        another = copy.deepcopy(leaf)
        another.update(id='TP-LEGACY-SECOND', coverage_item_refs=[second['id']])
        previous['tree']['children'].append(another)
        generated, outcomes = design_points(context, previous['project'], Ids({}, context, previous, manifest), previous)
        leaves = {p['id']: p for p in walk_test_points(generated['tree']) if not p['children']}
        self.assertIn(leaf['id'], leaves)
        self.assertIn(another['id'], leaves)
        self.assertEqual(set(outcomes[oid]), {leaf['id'], another['id']})


if __name__ == '__main__': unittest.main()
