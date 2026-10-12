"""Synthetic dialogue and design mutations at the actual Designer gates."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / p) for p in ("tooling/runtime", "skills/wewo-qa-case-designer/scripts", "skills/wewo-qa-case-executor/scripts", "tests")]
from artifact_tools import ValidationFailure, load_json, validate_test_points_data, validate_manifest_data
from artifact_factory import seal_synthetic_readiness, seal_synthetic_points
from design_context import requirement_digest, validate_design_context_data
from requirement_readiness import dialogue_errors, readiness_errors, point_decisions, point_units
from requirement_coverage import freeze_plan


class DesignerReadinessTests(unittest.TestCase):
    def setUp(self):
        self.context = load_json(ROOT / "tests/fixtures/design-context.json")
        self.points = load_json(ROOT / "tests/fixtures/test-points.json")
        self.manifest = load_json(ROOT / "tests/fixtures/valid-test-manifest.json")

    def test_discovery_can_start_without_fake_rules_models_or_tree(self):
        c = self.context
        c.update(rules=[], decisions=[], requirement_items=[], requirement_units=[], dialogue_events=[],
                 branch_reviews=[], requirement_review={"status":"draft"}, requirement_confirmation={"status":"draft"},
                 review={"status":"draft"}, coverage_plan={"status":"draft"})
        validate_design_context_data(c, final=False)
        self.assertTrue(readiness_errors(c))

    def test_requirements_ready_before_any_test_plan_or_final_confirmation(self):
        c = self.context
        before = requirement_digest(c)
        for r in c["rules"]:
            r.update(coverage=[], design_models=[], factors=[])
        c.update(coverage_plan={"status":"draft"}, review={"status":"draft"}, requirement_confirmation={"status":"draft"})
        c["dialogue_events"] = c["dialogue_events"][:2]
        validate_design_context_data(c, final=False)
        self.assertEqual(requirement_digest(c), before)
        self.assertEqual(readiness_errors(c), [])
        self.assertTrue(readiness_errors(c, confirmed=True))

    def test_empty_queue_does_not_replace_branch_review(self):
        self.context["branch_reviews"] = []
        seal_synthetic_readiness(self.context)
        self.assertTrue(any("every actual answer" in e for e in readiness_errors(self.context)))

    def followup(self):
        qid = self.context["decisions"][0]["question_id"]
        question = {"id":"EVT-QUESTION-002", "kind":"question", "message_ref":"synthetic://q2",
            "text":"[SYNTHETIC] Please restate the failure limit and lock duration in your own words.",
            "question_ids":[qid], "revisits":{qid:"EVT-QUESTION-001"}}
        self.context["dialogue_events"].append(question)
        return question

    def answer_followup(self):
        question = self.followup()
        answer = {"id":"EVT-ANSWER-002", "kind":"answer", "message_ref":"synthetic://a2",
            "text":"[SYNTHETIC] Five failures lock the account for fifteen minutes.",
            "question_ids":question["question_ids"], "in_reply_to":question["id"]}
        self.context["dialogue_events"].append(answer)
        self.context["branch_reviews"].append({"answer_event_ref":answer["id"], "unit_refs":["RU-002"],
            "note":"Synthetic free-form restatement preserves the same threshold and duration; no new business branch."})
        return answer

    def replace_decision(self, answer):
        old = self.context["decisions"][0]
        new = {**old, "id":"DEC-002", "response_event_ref":answer["id"]}
        new.pop("selected_options", None)
        old.update(status="superseded", superseded_by=new["id"])
        self.context["decisions"].append(new)
        for rule in self.context["rules"]:
            rule["decision_refs"] = [new["id"] if ref == old["id"] else ref for ref in rule["decision_refs"]]
        for item in self.context["requirement_items"]:
            if item["origin_ref"] == old["id"]:
                item["origin_ref"] = new["id"]

    def test_same_question_followup_accepts_open_answer_and_preserves_history(self):
        c = self.context
        c["dialogue_events"][0]["question_ids"] = ["Q1.1"]
        c["decisions"][0]["question_id"] = "Q1.1"
        answer = self.answer_followup()
        self.replace_decision(answer)
        c.update(coverage_plan={"status":"draft"}, review={"status":"draft"})
        seal_synthetic_readiness(c)
        validate_design_context_data(c, final=False)
        self.assertEqual(readiness_errors(c), [])
        self.assertEqual(len(c["decisions"]), 2)
        self.assertEqual(point_decisions(c)[0]["question_id"], "Q1.1")
        self.assertNotIn("selected_options", point_decisions(c)[0])
        self.points["decisions"] = point_decisions(c)
        # Check the compact question ID in the downstream schema without changing its business fixture.
        self.points["decisions"][0]["id"] = "DEC-001"
        seal_synthetic_points(self.points)
        validate_test_points_data(self.points)

    def test_reopened_question_does_not_reuse_old_resolution(self):
        self.followup()
        validate_design_context_data(self.context, final=False)
        seal_synthetic_readiness(self.context)
        errors = readiness_errors(self.context)
        self.assertTrue(any("latest answer" in e for e in errors))
        self.assertTrue(any("no decision or explicit pending" in e for e in errors))

    def test_followup_answer_requires_reconciling_the_current_decision(self):
        self.answer_followup()
        seal_synthetic_readiness(self.context)
        self.assertTrue(any("latest answer" in e for e in readiness_errors(self.context)))

    def test_same_question_followup_requires_latest_prior_occurrence(self):
        q = self.followup()
        del q["revisits"]
        self.assertTrue(any("latest earlier occurrence" in e for e in dialogue_errors(self.context)))
        q["revisits"] = {q["question_ids"][0]:"EVT-QUESTION-001"}
        next_q = {**q, "id":"EVT-QUESTION-003", "message_ref":"synthetic://q3"}
        self.context["dialogue_events"].append(next_q)
        self.assertTrue(any("latest earlier occurrence" in e for e in dialogue_errors(self.context)))
        next_q["revisits"] = {q["question_ids"][0]:q["id"]}
        self.assertEqual(dialogue_errors(self.context), [])

    def test_new_question_cannot_claim_a_nonexistent_prior_occurrence(self):
        q = self.context["dialogue_events"][0]
        q["revisits"] = {q["question_ids"][0]:"EVT-MISSING"}
        self.assertTrue(any("first occurrence" in e for e in dialogue_errors(self.context)))

    def test_late_correction_to_original_batch_invalidates_old_decision(self):
        c = self.context
        c["dialogue_events"].append({"id":"EVT-ANSWER-002", "kind":"answer", "message_ref":"synthetic://a2",
            "text":"[SYNTHETIC] Correction: the lock duration needs owner confirmation.", "in_reply_to":"EVT-QUESTION-001"})
        c["branch_reviews"].append({"answer_event_ref":"EVT-ANSWER-002", "unit_refs":["RU-002"],
            "note":"Synthetic correction reopens the duration and dependent acceptance oracle."})
        seal_synthetic_readiness(c)
        self.assertTrue(any("latest answer" in e for e in readiness_errors(c)))

    def test_later_reply_to_old_wording_still_reopens_the_current_decision(self):
        c = self.context
        self.replace_decision(self.answer_followup())
        c["dialogue_events"].append({"id":"EVT-ANSWER-003", "kind":"answer", "message_ref":"synthetic://a3",
            "text":"[SYNTHETIC] About the original question: I cannot confirm that duration.",
            "in_reply_to":"EVT-QUESTION-001"})
        c["branch_reviews"].append({"answer_event_ref":"EVT-ANSWER-003", "unit_refs":["RU-002"],
            "note":"Synthetic later reply to the original wording reopens the current oracle."})
        seal_synthetic_readiness(c)
        self.assertTrue(any("latest answer" in e for e in readiness_errors(c)))

    def test_partial_reply_cannot_support_an_unaddressed_question(self):
        c = self.context
        c["dialogue_events"][0]["question_ids"].append("Q1.2")
        c["dialogue_events"][1]["question_ids"] = ["Q-RU002-01"]
        self.assertEqual(dialogue_errors(c), [])
        seal_synthetic_readiness(c)
        self.assertTrue(any("Q1.2: displayed question has no decision" in e for e in readiness_errors(c)))
        c["decisions"][0]["question_id"] = "Q1.2"
        self.assertTrue(any("actual answer event" in e for e in dialogue_errors(c)))

    def test_multi_question_reply_requires_explicit_addressed_subset(self):
        self.context["dialogue_events"][0]["question_ids"].append("Q1.2")
        self.assertTrue(any("identify addressed" in e for e in dialogue_errors(self.context)))

    def test_one_reply_can_address_two_batches_without_duplicate_events(self):
        c = self.context
        q = {"id":"EVT-QUESTION-002", "kind":"question", "message_ref":"synthetic://q2",
            "text":"[SYNTHETIC] Which member name is displayed?", "question_ids":["Q2.1"]}
        c["dialogue_events"].insert(1, q)
        answer = c["dialogue_events"][2]
        answer.update(in_reply_to=["EVT-QUESTION-001", q["id"]], question_ids=["Q-RU002-01", "Q2.1"],
            text="[SYNTHETIC] Five failures lock for fifteen minutes; use the logged-in account's nickname.")
        c["decisions"].append({"id":"DEC-002", "question_id":"Q2.1", "unit_id":"RU-001", "status":"confirmed",
            "topic":"Displayed member name", "resolution":"Display the logged-in account's nickname.", "response_event_ref":answer["id"]})
        c["branch_reviews"][0]["unit_refs"] = ["RU-001", "RU-002"]
        self.assertEqual(dialogue_errors(c, ready=True), [])
        # Exercise the structured multi-parent field through schema validation too.
        c["decisions"].pop()
        c.update(coverage_plan={"status":"draft"}, review={"status":"draft"})
        validate_design_context_data(c, final=False)
        answer["question_ids"].append("Q9.9")
        self.assertTrue(any("absent from the referenced" in e for e in dialogue_errors(c)))

    def test_reply_cannot_ambiguously_cite_two_versions_of_same_question(self):
        answer = self.answer_followup()
        answer["in_reply_to"] = ["EVT-QUESTION-001", "EVT-QUESTION-002"]
        self.assertTrue(any("multiple occurrences" in e for e in dialogue_errors(self.context)))

    def test_confirmation_cannot_reply_to_multiple_summaries(self):
        self.context["dialogue_events"][3]["in_reply_to"] = ["EVT-SUMMARY-001"]
        self.assertTrue(any("one summary event" in e for e in dialogue_errors(self.context)))

    def test_retry_does_not_create_a_second_record_of_the_same_actual_reply(self):
        answer = {**self.context["dialogue_events"][1], "id":"EVT-ANSWER-RETRY"}
        self.context["dialogue_events"].append(answer)
        self.assertTrue(any("actual message already recorded" in e for e in dialogue_errors(self.context)))
        answer["message_ref"] = "synthetic://distinct-occurrence-with-same-words"
        self.assertEqual(dialogue_errors(self.context), [])

    def test_unanswered_displayed_question_cannot_disappear_from_empty_queue(self):
        self.context["dialogue_events"][0]["question_ids"].append("Q-RU002-02")
        seal_synthetic_readiness(self.context)
        self.assertTrue(any("no decision or explicit pending" in e for e in readiness_errors(self.context)))

    def test_later_dialogue_requires_a_new_summary_even_if_hashes_are_rewritten(self):
        self.context["dialogue_events"].append({"id":"EVT-QUESTION-002", "kind":"question", "message_ref":"synthetic://q2",
            "text":"[SYNTHETIC] What happens to the counter after expiry?", "question_ids":["Q-RU002-02"]})
        seal_synthetic_readiness(self.context)
        self.assertTrue(any("summary predates" in e for e in readiness_errors(self.context, confirmed=True)))

    def test_excluded_unit_does_not_require_invented_confirmed_facts(self):
        self.points["requirement_units"].append({"id":"RU-003", "title":"Deferred recovery behavior", "source_refs":["SRC-001"],
            "status":"excluded", "understanding":"Outside this limited synthetic fixture", "confirmed_facts":[],
            "exclusion_reason":"Synthetic benchmark only; recovery is explicitly outside its scope."})
        seal_synthetic_points(self.points)
        validate_test_points_data(self.points)

    def test_answer_unlocks_question_even_if_all_units_were_marked_confirmed(self):
        self.context["open_questions"].append({"id":"Q-RU002-02", "unit_id":"RU-002", "parent_decision_ref":"DEC-001",
            "description":"When the lock expires, what happens to the failure counter?", "impact":"Changes the next failed-login expectation", "material":True})
        seal_synthetic_readiness(self.context)
        self.assertTrue(any("unresolved material question" in e for e in readiness_errors(self.context)))
        with self.assertRaisesRegex(ValidationFailure, "material question"):
            freeze_plan(self.context)

    def test_unknown_owner_answer_cannot_close_waiting_unit(self):
        self.context["requirement_units"][1]["status"] = "waiting"
        seal_synthetic_readiness(self.context)
        self.assertTrue(any("still waiting" in e for e in readiness_errors(self.context)))

    def test_selected_option_cannot_replace_original_question_and_answer(self):
        self.context["dialogue_events"][0]["question_ids"] = ["Q-RU002-09"]
        self.assertTrue(any("actual answer event" in e for e in readiness_errors(self.context)))

    def test_summary_must_be_the_current_displayed_summary_with_actual_reply(self):
        self.context["dialogue_events"][2]["snapshot_sha256"] = "0" * 64
        self.assertTrue(any("displayed final summary" in e for e in readiness_errors(self.context, confirmed=True)))
        self.context["requirement_confirmation"]["response_text"] = "AI-generated approval"
        self.assertTrue(any("actual reply" in e for e in readiness_errors(self.context, confirmed=True)))

    def test_assumed_oracle_does_not_become_ready_from_overall_approval(self):
        self.context["decisions"][0]["status"] = "assumed"
        seal_synthetic_readiness(self.context)
        self.assertTrue(any("unconfirmed business assumption" in e for e in readiness_errors(self.context, confirmed=True)))

    def test_superseded_decision_remains_history_but_cannot_drive_current_rule(self):
        c = self.context
        old = c["decisions"][0]
        replacement = {**old, "id":"DEC-002", "resolution":"Lock after three failures", "response_event_ref":"EVT-ANSWER-002", "question_id":"Q-RU002-02"}
        c["dialogue_events"] += [
            {"id":"EVT-QUESTION-002","kind":"question","message_ref":"synthetic://q2","text":"[SYNTHETIC] Q-RU002-02 Replace five with three failures?", "question_ids":["Q-RU002-02"]},
            {"id":"EVT-ANSWER-002","kind":"answer","message_ref":"synthetic://a2","text":"[SYNTHETIC] Yes, three.","in_reply_to":"EVT-QUESTION-002"}]
        c["decisions"].append(replacement)
        old.update(status="superseded", superseded_by="DEC-002")
        self.assertTrue(any("still uses superseded" in e for e in readiness_errors(c)))
        self.assertEqual([d["id"] for d in point_decisions(c)], ["DEC-002"])
        self.assertEqual(len(c["decisions"]), 2)

    def test_requirement_change_blocks_xmind_draft_despite_old_frozen_plan(self):
        self.context["requirement_confirmation"] = {"status":"draft"}
        with self.assertRaisesRegex(ValidationFailure, "explicit user confirmation"):
            validate_test_points_data(self.points, self.context, final=False)

    def test_current_understanding_is_not_independently_editable_in_points(self):
        self.points["requirement_units"][0]["confirmed_facts"].append("Unconfirmed invented rule")
        seal_synthetic_points(self.points)
        with self.assertRaisesRegex(ValidationFailure, "current business understanding"):
            validate_test_points_data(self.points, self.context)

    def test_existing_but_unrelated_decision_does_not_support_a_leaf(self):
        self.points["tree"]["children"][0]["children"][0]["trace_refs"].append("DEC-001")
        seal_synthetic_points(self.points)
        with self.assertRaisesRegex(ValidationFailure, "unrelated to its business rules"):
            validate_test_points_data(self.points, self.context)

    def test_changed_visible_title_requires_fresh_tree_review_even_for_draft(self):
        self.points["tree"]["children"][0]["children"][0]["title"] = "Result correct"
        with self.assertRaisesRegex(ValidationFailure, "visible tree"):
            validate_test_points_data(self.points, self.context, final=False)

    def test_review_flags_alone_cannot_approve_edited_case_or_missing_walkthrough(self):
        self.manifest["cases"][0]["steps"][0]["action"] = "Perform process"
        with self.assertRaisesRegex(ValidationFailure, "walkthrough/oracle review is stale"):
            validate_manifest_data(self.manifest, self.points)
        validate_manifest_data(self.manifest, self.points, final=False)
        self.manifest["review"]["case_checks"] = []
        with self.assertRaisesRegex(ValidationFailure, "walk every case"):
            validate_manifest_data(self.manifest, self.points)

    def test_timestamp_alone_is_not_xmind_confirmation(self):
        self.manifest["test_points_baseline"].pop("response_text")
        with self.assertRaisesRegex(ValidationFailure, "actual tester confirmation"):
            validate_manifest_data(self.manifest, self.points)


if __name__ == "__main__":
    unittest.main()
