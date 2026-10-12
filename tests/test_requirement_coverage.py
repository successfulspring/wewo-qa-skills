"""Regression tests for source omissions, reverse-filled coverage and over-merges."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tooling/runtime"), str(ROOT / "skills/wewo-qa-case-designer/scripts"), str(ROOT / "skills/wewo-qa-case-executor/scripts"), str(ROOT / "tests")]
from artifact_tools import ValidationFailure, load_json, validate_manifest_data, validate_test_points_data
from artifact_factory import seal_synthetic_context, seal_synthetic_readiness
from design_context import requirement_digest, validate_design_context_data
from requirement_coverage import freeze_plan, plan_digest


def planned_context():
    context = load_json(ROOT / "tests/fixtures/design-context.json")
    context["coverage_plan"] = {"status": "draft"}
    context["review"] = {"status": "draft"}
    for rule in context["rules"]:
        for d in rule["coverage"]:
            d["test_point_refs"] = []
        for model in rule["design_models"]:
            for item in model["items"]:
                item["test_point_refs"] = []
    return context


def suffix_plan():
    context = planned_context()
    rule = context["rules"][0]
    rule["factors"] = [{"id":"FAC-SUFFIX","name":"Allowed suffix prefix","dimension":"positive","values":["U000001","U123456"],"basis_refs":rule["requirement_refs"][:]}]
    item = rule["design_models"][0]["items"][0]
    item["factor_values"] = {"FAC-SUFFIX":"U000001"}
    return context


class RequirementCoverageTests(unittest.TestCase):
    def test_can_freeze_before_leaves_without_stamping_human_or_tree_review(self):
        context = planned_context()
        original = copy.deepcopy(context)
        frozen = freeze_plan(context)
        self.assertEqual(frozen["coverage_plan"]["sha256"], plan_digest(frozen))
        self.assertEqual(frozen["requirement_confirmation"], original["requirement_confirmation"])
        self.assertEqual(frozen["review"], {"status":"draft"})
        self.assertEqual(context, original)

    def test_cannot_freeze_after_attaching_leaf_links(self):
        with self.assertRaisesRegex(ValidationFailure, "before attaching leaf"):
            freeze_plan(load_json(ROOT / "tests/fixtures/design-context.json"))

    def test_refreezing_preserves_findings_and_clears_prior_audit(self):
        context = planned_context()
        finding = {"id":"F-HISTORY","category":"coverage","scope_refs":["RULE-LOGIN-001"],"description":"Missing nickname outcome was discovered.","status":"resolved","resolution":"Separate planned nickname result added."}
        context["review"].update(findings=[finding],checks=["coverage"],source_checks=[],plan_sha256="0"*64)
        frozen = freeze_plan(context)
        self.assertEqual(frozen["review"], {"status":"draft","findings":[finding]})

    def test_source_paragraph_with_one_rule_cannot_hide_another_operation(self):
        context = planned_context()
        # Existing rule still points to this source; the new clause has no disposition.
        context["segments"][0]["content"] += "；可打印拆柜单"
        context["requirement_confirmation"]["snapshot_sha256"] = requirement_digest(context)
        with self.assertRaisesRegex(ValidationFailure, "unaccounted source content"):
            freeze_plan(context)

    def test_an_extracted_operation_without_its_rule_is_not_covered(self):
        context = planned_context()
        text = "打印拆柜单后生成包含当前收货单编号的文档"
        context["segments"].append({"id":"SEG-PRINT","source_id":"SRC-001","anchor":"Print","kind":"text","content":text,"read_status":"read","disposition":"requirement"})
        context["requirement_items"].append({"id":"REQ-PRINT","origin_ref":"SEG-PRINT","start":0,"end":len(text),"statement":text,"disposition":"requirement","rule_refs":[]})
        context["requirement_confirmation"]["snapshot_sha256"] = requirement_digest(context)
        with self.assertRaisesRegex(ValidationFailure, "REQ-PRINT.*no modeled rule"):
            freeze_plan(context)

    def test_partial_extraction_and_pending_applicability_are_usable_drafts(self):
        context = planned_context()
        context["requirement_items"] = []
        context["requirement_confirmation"] = {"status":"draft"}
        for rule in context["rules"]:
            rule["requirement_refs"] = []
            rule["design_models"] = []
            for d in rule["coverage"]:
                d.update(applicability="pending",basis_refs=[],reason="Awaiting source interpretation.")
        validate_design_context_data(context, final=False)
        with self.assertRaisesRegex(ValidationFailure, "confirm the actual final requirements|unresolved coverage"):
            freeze_plan(context)

    def test_whitespace_between_accounted_clauses_is_allowed(self):
        context = planned_context()
        context["segments"][0]["content"] += "\n  "
        seal_synthetic_readiness(context)
        freeze_plan(context)

    def test_overlapping_or_out_of_range_source_spans_are_rejected(self):
        for start, end in [(0,5),(0,10000)]:
            context = planned_context()
            context["requirement_items"][1].update(start=start,end=end)
            with self.assertRaisesRegex(ValidationFailure, "overlapping|invalid source character span"):
                freeze_plan(context)

    def test_unread_or_incomplete_included_sources_block_freeze(self):
        context = planned_context()
        context["sources"][0]["inventory_status"] = "partial"
        context["requirement_confirmation"]["snapshot_sha256"] = requirement_digest(context)
        with self.assertRaises(ValidationFailure):
            freeze_plan(context)

    def test_known_non_00_prefix_requires_its_own_representative(self):
        with self.assertRaisesRegex(ValidationFailure, "uncovered planned factor values.*U123456"):
            freeze_plan(suffix_plan())

    def test_rule_link_alone_cannot_cover_an_unmodeled_clause(self):
        context = planned_context()
        for item in context["rules"][0]["design_models"][0]["items"]:
            item["requirement_refs"] = ["REQ-LOGIN-1-1"]
        with self.assertRaisesRegex(ValidationFailure, "requirement items lack concrete.*REQ-LOGIN-1-2"):
            freeze_plan(context)

    def test_different_prefix_representatives_can_complete_the_plan(self):
        context = suffix_plan()
        model = context["rules"][0]["design_models"][0]
        second = copy.deepcopy(model["items"][0])
        second.update(id="COV-SUFFIX-OTHER",factor_values={"FAC-SUFFIX":"U123456"})
        second["condition"] += "; suffix U123456"
        for outcome in second["outcomes"]:
            outcome["id"] += "-OTHER"
        model["items"].append(second)
        freeze_plan(context)

    def test_known_factor_cannot_be_marked_not_applicable(self):
        context = suffix_plan()
        context["rules"][0]["coverage"][0].update(applicability="not-applicable",reason="No example was generated.")
        with self.assertRaisesRegex(ValidationFailure, "contradicts not-applicable|contradict rule applicability"):
            freeze_plan(context)

    def test_three_mutually_exclusive_types_cannot_be_one_factor_assignment(self):
        context = suffix_plan()
        context["rules"][0]["design_models"][0]["items"][0]["factor_values"]["FAC-SUFFIX"] = ["快递","电商卡派","非电商卡派"]
        with self.assertRaisesRegex(ValidationFailure, "factor_values"):
            freeze_plan(context)

    def test_scenario_wildcard_cannot_hide_multiple_types(self):
        context = suffix_plan()
        item = context["rules"][0]["design_models"][0]["items"][0]
        item["factor_values"]["FAC-SUFFIX"] = None
        with self.assertRaisesRegex(ValidationFailure, "wildcard needs"):
            freeze_plan(context)

    def test_plan_change_is_detected_but_leaf_linking_does_not_change_digest(self):
        context = load_json(ROOT / "tests/fixtures/design-context.json")
        expected = plan_digest(context)
        context["rules"][0]["design_models"][0]["items"][0]["test_point_refs"] = ["TP-ANOTHER"]
        self.assertEqual(plan_digest(context), expected)
        context["rules"][0]["design_models"][0]["items"][0]["outcomes"].pop()
        with self.assertRaisesRegex(ValidationFailure, "coverage plan.*changed"):
            validate_design_context_data(context)

    def test_two_independent_results_cannot_share_one_leaf(self):
        context = load_json(ROOT / "tests/fixtures/design-context.json")
        points = load_json(ROOT / "tests/fixtures/test-points.json")
        item = context["rules"][0]["design_models"][0]["items"][0]
        item["test_point_refs"] = ["TP-LOGIN-SUCCESS"]
        context["rules"][0]["coverage"][0]["test_point_refs"] = ["TP-LOGIN-SUCCESS"]
        points["tree"]["children"][0]["children"] = [n for n in points["tree"]["children"][0]["children"] if n["id"] != "TP-LOGIN-NICKNAME"]
        with self.assertRaisesRegex(ValidationFailure, "split each independent outcome"):
            validate_test_points_data(points, context)

    def test_leaf_verification_cannot_change_frozen_condition_or_outcome(self):
        context = load_json(ROOT / "tests/fixtures/design-context.json")
        points = load_json(ROOT / "tests/fixtures/test-points.json")
        points["tree"]["children"][0]["children"][0]["verification"]["expected"] = "All values and states are correct"
        with self.assertRaisesRegex(ValidationFailure, "verification differs"):
            validate_test_points_data(points, context)

    def test_one_assertion_cannot_bundle_two_independent_points(self):
        manifest = load_json(ROOT / "tests/fixtures/valid-test-manifest.json")
        manifest["cases"][0]["assertions"][0]["test_point_refs"] = ["TP-LOGIN-SUCCESS","TP-LOGIN-NICKNAME"]
        with self.assertRaisesRegex(ValidationFailure, "test_point_refs"):
            validate_manifest_data(manifest)

    def test_case_cannot_silently_replace_the_confirmed_leaf_expectation(self):
        manifest = load_json(ROOT / "tests/fixtures/valid-test-manifest.json")
        points = load_json(ROOT / "tests/fixtures/test-points.json")
        manifest["cases"][0]["assertions"][0]["expected"] = "Whatever the implementation currently shows"
        validate_manifest_data(manifest, points, final=False)
        with self.assertRaisesRegex(ValidationFailure, "expectation differs from confirmed leaf"):
            validate_manifest_data(manifest, points)

    def test_source_audit_must_include_clarification_decisions(self):
        context = load_json(ROOT / "tests/fixtures/design-context.json")
        context["review"]["source_checks"] = [c for c in context["review"]["source_checks"] if c["origin_ref"] != "DEC-001"]
        with self.assertRaisesRegex(ValidationFailure, "source-first audit"):
            validate_design_context_data(context)

    def test_audit_is_bound_to_current_source_and_plan(self):
        context = load_json(ROOT / "tests/fixtures/design-context.json")
        context["review"]["source_checks"][0]["content_sha256"] = "0" * 64
        context["review"]["plan_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValidationFailure, "source audit is stale|atomicity review is stale"):
            validate_design_context_data(context)

    def test_final_gate_accepts_separate_outcomes_in_one_coherent_case(self):
        context = load_json(ROOT / "tests/fixtures/design-context.json")
        points = load_json(ROOT / "tests/fixtures/test-points.json")
        manifest = load_json(ROOT / "tests/fixtures/valid-test-manifest.json")
        validate_test_points_data(points, context)
        validate_manifest_data(manifest, points)
        self.assertEqual(len(manifest["cases"][0]["test_point_refs"]), 2)


if __name__ == "__main__":
    unittest.main()
