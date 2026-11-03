"""Synthetic business uncertainty through the actual draft delivery pipeline."""
import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / p) for p in ("tooling/runtime", "skills/wewo-qa-case-designer/scripts", "skills/wewo-qa-case-executor/scripts", "tests")]
from artifact_tools import ValidationFailure, load_json, sha256_file, validate_manifest_data, validate_manifest_file, validate_test_points_file
from artifact_factory import write_json, seal_synthetic_points, seal_synthetic_readiness, seal_synthetic_cases
from case_workbook import render_case_workbooks, read_case_workbook, import_case_workbooks
from design_context import validate_design_context_data, requirement_digest
from question_workbook import render_workbook


def draft_set(directory, *, language=None):
    c = load_json(ROOT / "tests/fixtures/design-context.json")
    p = load_json(ROOT / "tests/fixtures/test-points.json")
    m = load_json(ROOT / "tests/fixtures/valid-test-manifest.json")
    if language:
        for artifact in (c, p, m):
            artifact['project']['output_language'] = language
    qid = "Q2.1"
    c["open_questions"] = [{"id": qid, "unit_id": "RU-001", "material": True,
        "description": "Which member name is displayed?", "impact": "Nickname assertion only",
        "source_refs": [c["requirement_units"][0]["source_refs"][0]],
        "options": ["Member nickname", "Account identifier"]}]
    rule = c["rules"][0]
    rule.update(status="pending", question_refs=[qid], rationale="Display identity needs owner confirmation")
    rule.pop("expected")
    item = rule["design_models"][0]["items"][0]
    item.update(status="pending", question_refs=[qid])
    item.pop("expected")
    outcome = item["outcomes"][1]
    outcome.update(status="pending", question_refs=[qid])
    outcome.pop("expected")
    c["coverage_plan"] = {"status": "draft"}
    c["review"] = {"status": "draft"}
    c["requirement_units"][0]["status"] = "waiting"
    p["requirement_units"][0]["status"] = "waiting"
    leaf = p["tree"]["children"][0]["children"][1]
    leaf.update(status="pending", question_refs=[qid], title="Submitted login: displayed name pending")
    leaf["verification"].pop("expected")
    p["stage"] = m["stage"] = "draft"
    a = m["cases"][0]["assertions"][1]
    a.update(status="pending", question_refs=[qid])
    a.pop("expected")
    a.pop("check")
    m["review"] = {"status": "pending"}
    m["test_points_baseline"].pop("confirmed_at", None)
    m["test_points_baseline"].pop("response_ref", None)
    m["test_points_baseline"].pop("response_text", None)
    # Explicitly synthetic overall confirmation includes the disclosed uncertainty.
    seal_synthetic_readiness(c)
    write_json(directory / "design-context.json", c)
    p["design_context_baseline"]["sha256"] = sha256_file(directory / "design-context.json")
    seal_synthetic_points(p)
    write_json(directory / "test-points.json", p)
    m["test_points_baseline"]["sha256"] = sha256_file(directory / "test-points.json")
    path = directory / "test-manifest.json"
    write_json(path, m)
    return c, p, m, path


class DesignerDraftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / ".qa-state"
        self.state.mkdir()
        self.context, self.points, self.manifest, self.path = draft_set(self.state)

    def test_pending_business_rule_is_a_valid_draft_without_invented_expected(self):
        validate_design_context_data(self.context, final=False)
        validate_manifest_data(self.manifest, final=False)
        self.assertNotIn("check", self.manifest["cases"][0]["assertions"][1])

    def test_draft_points_and_cases_can_be_validated_without_frozen_plan(self):
        validate_test_points_file(self.state / "test-points.json", final=False)
        validate_manifest_file(self.path, final=False)

    def test_suite_drafts_roundtrip_without_embedded_question_sheet(self):
        from openpyxl import load_workbook
        outputs = render_case_workbooks(self.path, draft=True)
        self.assertEqual(len(outputs), 3)
        for output in outputs:
            candidate, original, _ = read_case_workbook(output)
            self.assertEqual(candidate, original)
        book = load_workbook(next(p for p in outputs if p.name.endswith("full.xlsx")))
        self.addCleanup(book.close)
        self.assertNotIn('待确认问题', book.sheetnames)
        questions = load_workbook(render_workbook(self.state / 'design-context.json', draft=True))
        self.addCleanup(questions.close)
        rows = list(questions['需求澄清'].values)
        self.assertIn("Q2.1", str(rows))
        self.assertIn("QA-LOGIN-001", str(rows))
        self.assertIn("TP-LOGIN-NICKNAME", str(rows))

    def test_draft_is_rejected_by_the_default_execution_baseline_validation(self):
        with self.assertRaisesRegex(ValidationFailure, "draft|pending"):
            validate_manifest_file(self.path)

    def test_pending_assertion_cannot_hide_an_executable_check(self):
        self.manifest["cases"][0]["assertions"][1]["check"] = {"kind": "equals", "timing": "After login", "expected_value": "guessed"}
        with self.assertRaises(ValidationFailure):
            validate_manifest_data(self.manifest, final=False)

    def test_draft_cannot_change_a_known_oracle_away_from_its_leaf(self):
        self.manifest['cases'][0]['assertions'][0]['expected'] = 'Different invented known result'
        with self.assertRaisesRegex(ValidationFailure, 'expectation differs'):
            validate_manifest_data(self.manifest, self.points, final=False)

    def test_draft_export_keeps_user_edits_and_import_preserves_pending_assertion(self):
        from openpyxl import load_workbook
        outputs = render_case_workbooks(self.path, draft=True)
        full = next(p for p in outputs if p.name.endswith("full.xlsx"))
        book = load_workbook(full)
        book["测试用例"].cell(2, 3, "User corrected draft title")
        pending_row = next(row[0].row for row in book['必检断言'].iter_rows(min_row=2) if row[-1].value == 'Q2.1')
        book['必检断言'].cell(pending_row, 8, 'Proposed member display name')
        book.save(full)
        book.close()
        with self.assertRaisesRegex(ValidationFailure, "unreviewed edits"):
            render_case_workbooks(self.path, draft=True)
        candidate = import_case_workbooks(self.path)
        edited = next(c for c in candidate['cases'] if c['id'] == 'QA-LOGIN-001')
        self.assertEqual(edited["title"], "User corrected draft title")
        self.assertEqual(edited["assertions"][1]["question_refs"], ["Q2.1"])
        self.assertEqual(edited['assertions'][1]['expected'], 'Proposed member display name')
        self.assertEqual(edited['assertions'][1]['status'], 'pending')
        self.assertNotIn('check', edited['assertions'][1])

    def test_five_draft_files_validate_together_but_cannot_finalize(self):
        from render_test_points_xmind import render_xmind_bytes
        from deliverables import validate_delivery
        render_case_workbooks(self.path, draft=True)
        render_workbook(self.state / 'design-context.json', draft=True)
        (self.state.parent / 'test-points.xmind').write_bytes(render_xmind_bytes(self.points, draft=True))
        validate_delivery(self.state.parent, draft=True)
        with self.assertRaises(ValidationFailure):
            validate_delivery(self.state.parent)

    def test_pending_reference_cannot_disappear_with_question_queue(self):
        self.context['open_questions'] = []
        with self.assertRaisesRegex(ValidationFailure, 'unknown pending question'):
            validate_design_context_data(self.context, final=False)

    def test_english_draft_preserves_question_refs_and_blank_comparison(self):
        from openpyxl import load_workbook
        _, _, _, path = draft_set(self.state, language='en')
        outputs = render_case_workbooks(path, draft=True)
        full = next(p for p in outputs if p.name.endswith('full.xlsx'))
        book = load_workbook(full)
        self.addCleanup(book.close)
        self.assertNotIn('Open Questions', book.sheetnames)
        rows = list(book['Required Assertions'].values)
        pending = next(dict(zip(rows[0], r)) for r in rows[1:] if 'Q2.1' in str(r))
        self.assertEqual(pending['Design Status'], 'Pending confirmation')
        self.assertIsNone(pending['Comparison'])
        self.assertEqual(read_case_workbook(full)[0], read_case_workbook(full)[1])

    def test_question_sheet_cannot_be_silently_added_back_to_full_cases(self):
        from openpyxl import load_workbook
        outputs = render_case_workbooks(self.path, draft=True)
        full = next(p for p in outputs if p.name.endswith('full.xlsx'))
        book = load_workbook(full)
        book.create_sheet('待确认问题').cell(2, 3, 'Unexpected duplicate question inventory')
        book.save(full)
        book.close()
        with self.assertRaises(ValidationFailure):
            render_case_workbooks(self.path, draft=True)

    def test_batch_answer_finalizes_same_artifacts_without_new_overall_or_xmind_reply(self):
        from requirement_confirmation import business_snapshot
        from requirement_readiness import point_units, point_decisions, readiness_errors
        from requirement_coverage import freeze_plan, source_texts, plan_digest
        from render_test_points_xmind import render_xmind_bytes
        from deliverables import validate_delivery
        from prepare_execution_profile import build_profile
        c, p, m = self.context, self.points, self.manifest
        outputs = render_case_workbooks(self.path, draft=True)
        clarification_path = render_workbook(self.state / 'design-context.json', draft=True)
        original_confirmation = copy.deepcopy(c['requirement_confirmation'])
        original_ids = [(case['id'], case['test_point_refs']) for case in m['cases']]
        c['requirement_confirmation']['baseline'] = business_snapshot(c)
        c['dialogue_events'] += [
            {'id':'EVT-Q-DRAFT', 'kind':'question', 'message_ref':'synthetic://draft/questions',
             'text':'[SYNTHETIC] Q2.1 Which name appears?', 'question_ids':['Q2.1']},
            {'id':'EVT-A-DRAFT', 'kind':'answer', 'message_ref':'synthetic://draft/answer',
             'text':'[SYNTHETIC] Display the member nickname.', 'in_reply_to':'EVT-Q-DRAFT', 'question_ids':['Q2.1']}]
        decision = {'id':'DEC-002', 'unit_id':'RU-001', 'question_id':'Q2.1', 'topic':'Displayed name',
                    'resolution':'Display the member nickname.', 'status':'confirmed', 'response_event_ref':'EVT-A-DRAFT'}
        c['decisions'].append(decision)
        c['branch_reviews'].append({'answer_event_ref':'EVT-A-DRAFT', 'unit_refs':['RU-001'],
            'note':'Synthetic owner answer resolves the name only; login success and rejection outcomes remain unchanged.'})
        c['requirement_items'].append({'id':'REQ-DISPLAY', 'origin_ref':'DEC-002', 'start':0,
            'end':len(decision['resolution']), 'statement':decision['resolution'], 'disposition':'requirement', 'rule_refs':[c['rules'][0]['id']]})
        resolved = load_json(ROOT / 'tests/fixtures/design-context.json')
        c['rules'][0] = copy.deepcopy(resolved['rules'][0])
        rule = c['rules'][0]
        rule['decision_refs'].append('DEC-002')
        rule['requirement_refs'].append('REQ-DISPLAY')
        rule['design_models'][0]['items'][0]['requirement_refs'].append('REQ-DISPLAY')
        c['requirement_units'][0]['status'] = 'confirmed'
        c['closed_questions'] = [dict(q, disposition='resolved', resolution_refs=['DEC-002']) for q in c['open_questions']]
        c['open_questions'] = []
        c['requirement_confirmation']['amendments'] = [{'ref':rule['id'], 'sha256':business_snapshot(c)[rule['id']], 'decision_refs':['DEC-002']}]
        c['requirement_review']['snapshot_sha256'] = requirement_digest(c)
        self.assertEqual(readiness_errors(c, confirmed=True), [])
        saved_links = []
        for r in c['rules']:
            for entry in [*r['coverage'], *(i for model in r['design_models'] for i in model['items'])]:
                saved_links.append((entry, entry['test_point_refs']))
                entry['test_point_refs'] = []
        frozen = freeze_plan(c)
        c['coverage_plan'] = frozen['coverage_plan']
        for entry, refs in saved_links:
            entry['test_point_refs'] = refs
        c['review'] = copy.deepcopy(resolved['review'])
        c['review'].update(plan_sha256=plan_digest(c), source_checks=[{
            'origin_ref':origin, 'content_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'requirement_refs':[i['id'] for i in c['requirement_items'] if i['origin_ref'] == origin],
            'note':'Synthetic lifecycle fixture: check source and the batch answer against all corresponding clauses.'
        } for origin, text in source_texts(c).items()])
        write_json(self.state / 'design-context.json', c)
        p['tree'] = load_json(ROOT / 'tests/fixtures/test-points.json')['tree']
        p.update(stage='final', requirement_units=point_units(c), decisions=point_decisions(c))
        p['design_context_baseline']['sha256'] = sha256_file(self.state / 'design-context.json')
        seal_synthetic_points(p)
        write_json(self.state / 'test-points.json', p)
        final_manifest = load_json(ROOT / 'tests/fixtures/valid-test-manifest.json')
        m.update(stage='final', cases=final_manifest['cases'], review=final_manifest['review'])
        m['decisions'] = [{k:v for k,v in d.items() if k in {'id','topic','resolution','status','rationale'}} for d in p['decisions']]
        m['test_points_baseline']['sha256'] = sha256_file(self.state / 'test-points.json')
        seal_synthetic_cases(m)
        write_json(self.path, m)
        self.assertEqual(render_case_workbooks(self.path), outputs)
        self.assertEqual(render_workbook(self.state / 'design-context.json'), clarification_path)
        (self.state.parent / 'test-points.xmind').write_bytes(render_xmind_bytes(p))
        validate_delivery(self.state.parent)
        self.assertEqual([(case['id'], case['test_point_refs']) for case in m['cases']], original_ids)
        self.assertEqual({k:c['requirement_confirmation'][k] for k in original_confirmation}, original_confirmation)
        self.assertNotIn('response_text', m['test_points_baseline'])
        profile = build_profile(validate_manifest_file(self.path), self.path,
            self.state / 'runs/synthetic/execution-profile.json', 'smoke', ['web-chrome'])
        self.assertEqual(profile['suite'], 'smoke')


if __name__ == "__main__":
    unittest.main()
