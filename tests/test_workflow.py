"""Regression gates for the tester's requested end-to-end workflow."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT/"tooling/runtime"),str(ROOT/"skills/wewo-qa-case-designer/scripts"),str(ROOT/"skills/wewo-qa-case-executor/scripts"),str(ROOT/"tests")]
from artifact_factory import artifact_set, execution_set, write_json
from artifact_tools import ValidationFailure, sha256_file, validate_results_file
from case_workbook import render_case_workbooks, read_case_workbook, import_case_workbooks, validate_case_workbooks
from design_context import validate_design_context_data
from deliverables import validate_delivery
from native_execution import execute, native_tests
from render_execution_report import automatic_gate, render_report
from render_test_points_xmind import render_xmind_bytes
from openpyxl import load_workbook


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.context,self.points,self.manifest,self.path = artifact_set(self.root/".qa-state")
        # Fixture helper's private workbooks are not public deliverables.
        render_case_workbooks(self.path)
        (self.root/"test-points.xmind").write_bytes(render_xmind_bytes(self.points,"legacy"))

    def test_four_public_files_have_their_own_exact_suite_rows(self):
        validate_delivery(self.root)
        self.assertEqual({p.name for p in self.root.iterdir()}, {".qa-state","test-points.xmind","test-cases.smoke.xlsx","test-cases.regression.xlsx","test-cases.full.xlsx"})
        for suite in ("smoke","regression","full"):
            book=load_workbook(self.root/f"test-cases.{suite}.xlsx")
            try:
                ids={r[0] for r in book["测试用例"].iter_rows(min_row=2,values_only=True)}
                self.assertEqual(ids,{c["id"] for c in self.manifest["cases"] if suite in c["suite_membership"]})
                self.assertTrue({r[0] for r in book["必检断言"].iter_rows(min_row=2,values_only=True)} <= ids)
            finally: book.close()

    def test_python_at_delivery_root_rejects_completion(self):
        (self.root/"build_artifacts.py").write_text("# unwanted generation helper")
        with self.assertRaisesRegex(ValidationFailure,"not a tester deliverable"):
            validate_delivery(self.root)

    def test_unconfirmed_or_changed_requirement_cannot_finalize(self):
        context=copy.deepcopy(self.context)
        context["requirement_confirmation"]={"status":"draft"}
        with self.assertRaisesRegex(ValidationFailure,"explicit user confirmation"):
            validate_design_context_data(context)
        context=copy.deepcopy(self.context)
        context["rules"][0]["expected"]="A changed business outcome"
        with self.assertRaisesRegex(ValidationFailure,"reconfirm requirements"):
            validate_design_context_data(context)

    def edit_title(self,suite,text):
        path=self.root/f"test-cases.{suite}.xlsx"
        book=load_workbook(path)
        book["测试用例"]["C2"]=text
        book.save(path)
        book.close()

    def test_edit_to_overlapping_view_merges_without_losing_full_scope(self):
        self.edit_title("smoke","Edited smoke business case")
        candidate=import_case_workbooks(self.path)
        self.assertEqual(len(candidate["cases"]),len(self.manifest["cases"]))
        self.assertEqual(candidate["review"]["status"],"pending")
        self.assertEqual(candidate["cases"][-1]["title"],"Edited smoke business case")
        with self.assertRaisesRegex(ValidationFailure,"unreviewed edits"):
            render_case_workbooks(self.path)

    def test_conflicting_overlapping_edits_are_not_silently_chosen(self):
        self.edit_title("smoke","Smoke interpretation")
        self.edit_title("full","Different full interpretation")
        with self.assertRaisesRegex(ValidationFailure,"conflicting edits"):
            import_case_workbooks(self.path)

    def test_reviewed_import_can_regenerate_synchronized_views(self):
        self.edit_title("smoke","Reviewed case title")
        merged=import_case_workbooks(self.path)
        merged["review"].update(status="confirmed",reviewed_at=self.manifest["review"]["reviewed_at"],checks=self.manifest["review"]["checks"])
        write_json(self.path,merged)
        render_case_workbooks(self.path)
        validate_case_workbooks(self.path)


class NativeRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.manifest,self.path,self.profile,self.profile_path,_,_=execution_set(self.root)
        self.repo=self.root/"project"
        self.repo.mkdir()
        # This is deliberately a synthetic plumbing fixture, not product coverage.
        self.runner=self.repo/"tests"/"fixture_runner.py"
        self.runner.parent.mkdir()
        self.runner.write_text('''import json,os,sys,datetime
from pathlib import Path
data=json.loads(Path("fixture-events.json").read_text())
rows=[]
for event in data["events"]:
 event.update(run_id=os.environ["WEWO_QA_RUN_ID"],captured_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
 rows.append(json.dumps(event,ensure_ascii=False))
Path(os.environ["WEWO_QA_OBSERVATIONS_FILE"]).write_text("\\n".join(rows)+"\\n",encoding="utf8")
Path(os.environ["WEWO_QA_REPORT_FILE"]).write_text(data["report"],encoding="utf8")
print("Synthetic runner actually executed")
sys.exit(data["exit_code"])
''',encoding="utf8")
        self.case=self.manifest["cases"][0]
        for a in self.case["assertions"]: a["required_evidence"]=["tool-output"]
        self.case["automation"][0]["required_evidence"]=["tool-output"]
        write_json(self.path,self.manifest)
        render_case_workbooks(self.path)
        from prepare_execution_profile import build_profile
        self.profile=build_profile(self.manifest,self.path,self.profile_path,"smoke",["web-chrome"])
        for b in self.profile["bindings"]:
            b.update(status="resolved",source="user-input",value="synthetic-value")
            req=next(r for r in self.manifest["runtime_requirements"] if r["id"] == b["requirement_id"])
            if req["sensitive"]:
                b.pop("value")
                b.update(source="authenticated-session",session_ref="synthetic-session")
        write_json(self.profile_path,self.profile)
        self.events=[]
        for a in self.case["assertions"]:
            self.events.append({"case_id":self.case["id"],"target_id":"web-chrome","assertion_id":a["id"],"test_id":"Synthetic::acceptance","attempt":1,"phase":"after","subject":"synthetic-order","location":"synthetic-observable-value","value":a["check"]["expected_value"]})
        self.plan={"repository":str(self.repo),"runner":"synthetic-native-runner","argv":[sys.executable,str(self.runner)],"manifest_sha256":sha256_file(self.path),"profile_sha256":sha256_file(self.profile_path),"report_format":"junit","bindings":[{"case_id":self.case["id"],"target_id":"web-chrome","asset":"tests/fixture_runner.py","asset_sha256":sha256_file(self.runner),"test_id":"Synthetic::acceptance","route":"synthetic-plumbing-only","assertion_ids":[a["id"] for a in self.case["assertions"]]}]}
        self.environment={"name":"Synthetic local test fixture","kind":"test","build":"fixture-v1"}

    def run_fixture(self,events=None,report=None,exit_code=0):
        write_json(self.repo/"fixture-events.json",{"events":self.events if events is None else events,"report":report or '<testsuites><testsuite><testcase classname="Synthetic" name="acceptance"/></testsuite></testsuites>',"exit_code":exit_code})
        output=execute(self.plan,self.path,self.profile_path,self.environment)
        return output,json.loads(output.read_text(encoding="utf8"))

    def test_real_process_and_native_report_are_required_for_pass(self):
        output,results=self.run_fixture()
        self.assertEqual(results["results"][0]["status"],"passed")
        self.assertEqual(automatic_gate(results,self.manifest),"PASSED")
        self.assertIn("fixture_runner.py",results["results"][0]["native_test"]["asset"])
        validate_results_file(output,self.path)

    def test_runner_success_cannot_hide_wrong_observed_value(self):
        events=copy.deepcopy(self.events)
        events[0]["value"]="Wrong observed business value"
        _,results=self.run_fixture(events=events)
        self.assertEqual(results["results"][0]["status"],"failed")

    def test_runner_success_cannot_hide_missing_planned_observation(self):
        _,results=self.run_fixture(events=self.events[1:])
        self.assertEqual(results["results"][0]["status"],"blocked")
        self.assertEqual(automatic_gate(results,self.manifest),"INCOMPLETE")

    def test_skipped_or_undiscovered_native_test_is_not_passed(self):
        for report in ['<testsuites/>','<testsuite><testcase classname="Synthetic" name="acceptance"><skipped/></testcase></testsuite>']:
            _,results=self.run_fixture(report=report)
            self.assertEqual(results["results"][0]["status"],"blocked")

    def test_changed_native_report_invalidates_result(self):
        output,results=self.run_fixture()
        receipt_path=self.profile_path.parent/results["results"][0]["native_test"]["receipt_path"]
        receipt=json.loads(receipt_path.read_text())
        (self.profile_path.parent/receipt["report"]["path"]).write_text('<testsuites/>')
        with self.assertRaisesRegex(ValidationFailure,"native runner evidence"):
            validate_results_file(output,self.path)

    def test_public_report_links_resolve_to_original_native_evidence(self):
        output,results=self.run_fixture()
        report_dir=self.root/"tester-delivery"
        report_dir.mkdir()
        report=report_dir/"test-execution-report.xlsx"
        report.write_bytes(render_report(results,self.manifest,results_dir=output.parent,report_dir=report_dir))
        book=load_workbook(report)
        try:
            for sheet,columns in [("证据索引",(6,)),("自动化实现",(5,7,8))]:
                for row in range(2,book[sheet].max_row+1):
                    for column in columns:
                        cell=book[sheet].cell(row,column)
                        self.assertIsNotNone(cell.hyperlink)
                        self.assertTrue((report_dir/cell.hyperlink.target).is_file())
        finally:
            book.close()

    def test_unmapped_assertion_and_changed_asset_block_before_execution(self):
        self.plan["bindings"][0]["assertion_ids"].pop()
        with self.assertRaisesRegex(ValidationFailure,"exactly the planned assertions"):
            execute(self.plan,self.path,self.profile_path,self.environment)

if __name__ == "__main__": unittest.main()
