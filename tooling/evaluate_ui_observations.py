"""Maintainer benchmark: judge original browser observations from the synthetic UI.

This does not drive a browser. Capture the fixture through an actual UI tool first.
Artifacts are synthetic and must be generated outside the repository.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tooling/runtime"), str(ROOT / "skills/wewo-qa-case-designer/scripts"), str(ROOT / "skills/wewo-qa-case-executor/scripts"), str(ROOT / "tests")]
from artifact_factory import artifact_set, write_json
from artifact_tools import load_json, sha256_file, validate_manifest_file
from case_workbook import module_paths, render_case_workbook
from prepare_execution_profile import build_profile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError("benchmark artifacts must be outside the repository")
    if output.exists():
        raise ValueError("benchmark output already exists")
    output.mkdir(parents=True)
    context, points, manifest, path = artifact_set(output)
    target = "web-chrome"
    project = copy.deepcopy(manifest["project"])
    project.update(name="合成 UI 判定基准", artifact_id="ui-observation-benchmark", requirement="转运两件后状态与关联数量", baseline="Maintainer synthetic fixture; not tester approval")
    project["targets"] = [t for t in project["targets"] if t["id"] == target]
    context["project"] = {k:project[k] for k in ["name","artifact_id"]}
    points["project"] = manifest["project"] = project
    source = copy.deepcopy(points["sources"][0])
    source.update(title="Synthetic transfer observation obligations", type="other", locator="Maintainer synthetic obligation subset", version="benchmark-1")
    points["sources"] = manifest["sources"] = [source]
    context["sources"] = [{**source, "scope":"included", "inventory_status":"complete", "method":"Explicit synthetic four-obligation benchmark"}]
    for item in [context,points,manifest]: item["decisions"] = []
    context["segments"] = [{"id":"SEG-001-001", "source_id":"SRC-001", "anchor":"benchmark", "kind":"text", "content":"On creation for a Ready order, become InTransit; incoming increases by the selected two parcels; origin reserved quantity and parcel order binding remain unchanged. This benchmark only covers these four observable obligations.", "read_status":"read", "disposition":"requirement"}]
    points["requirement_units"] = [{"id":"RU-001", "title":"Four benchmark observations", "source_refs":["SRC-001#benchmark"], "status":"confirmed", "understanding":context["segments"][0]["content"], "confirmed_facts":[context["segments"][0]["content"]]}]
    obligations = [("state","状态成为 InTransit",{"kind":"equals","expected_value":"InTransit"}), ("incoming","目的在途数量增加 2",{"kind":"number-delta","expected_value":2}), ("reserved","来源保留数量不变",{"kind":"unchanged"}), ("binding","包裹订单绑定不变",{"kind":"unchanged"})]
    template_rule = copy.deepcopy(context["rules"][0])
    template_leaf = copy.deepcopy(points["tree"]["children"][0]["children"][0])
    context["rules"], leaves, assertions = [], [], []
    for index, (field,title,check) in enumerate(obligations,1):
        rid,pid,cid,aid = f"RULE-UI-{index}",f"TP-UI-{index}",f"COV-UI-{index}",f"AS-UI-{index}"
        rule = copy.deepcopy(template_rule)
        rule.update(id=rid,title=title,kind="other",object_refs=[],segment_refs=["SEG-001-001"],decision_refs=[],condition="Ready order; select two parcels",action="Create transfer through UI",expected=title)
        for dimension in rule["coverage"]:
            dimension.update(applicability="required" if dimension["dimension"] == "positive" else "not-applicable",test_point_refs=[pid] if dimension["dimension"] == "positive" else [],reason="This narrowly scoped observation benchmark does not claim overall feature coverage.")
        rule["design_models"] = [{"id":f"DM-UI-{index}","method":"scenario","rationale":"One fixed operation checks this independently observable outcome; full feature design is outside this benchmark.","items":[{"id":cid,"dimensions":["positive"],"condition":rule["condition"],"action":rule["action"],"expected":title,"setup":"Restore synthetic order via the fixture reset button.","disposition":"required","test_point_refs":[pid]}]}]
        context["rules"].append(rule)
        leaf = copy.deepcopy(template_leaf)
        leaf.update(id=pid,title=title,kind="oracle",trace_refs=["SRC-001#benchmark"],rule_refs=[rid],coverage_item_refs=[cid],verification={k:rule[k] for k in ["condition","action","expected"]})
        leaves.append(leaf)
        assertions.append({"id":aid,"description":title,"observation":"Synthetic order " + field + " field","expected":title,"target_ids":[target],"test_point_refs":[pid],"required_evidence":["tool-output"],"check":{**check,"timing":"After create-transfer changes order state to InTransit"}})
    points["tree"].update(title=project["name"],children=leaves)
    case = copy.deepcopy(manifest["cases"][0])
    case.update(id="QA-UI-001",title="转运 2 件的四项结果",source_refs=["SRC-001#benchmark"],test_point_refs=[l["id"] for l in leaves],applicable_targets=[target],runtime_requirement_refs=["RT-ENV-BASE-URL"],preconditions=["Restore isolated synthetic order"],test_data=["SYNTHETIC-O1; two parcels"],steps=[{"action":"Read baseline quantities/binding; create transfer for two parcels; inspect state and quantities","expected":"; ".join(t for _,t,_ in obligations),"assertion_refs":[a["id"] for a in assertions]}],assertions=assertions,automation=[{"target_id":target,"feasibility":"automatable","candidate_route":"browser-ui","runtime_requirement_refs":[],"required_evidence":["tool-output"]}],safety={"impact":"reversible","requires_confirmation":False,"cleanup_steps":["Restore fixture data via reset button"]},tags=["synthetic-benchmark"])
    manifest["cases"] = [case]
    manifest["runtime_requirements"] = [manifest["runtime_requirements"][0]]
    manifest["runtime_requirements"][0].update(description="Loopback synthetic fixture",name="Fixture address")
    write_json(output / "design-context.json", context)
    points["design_context_baseline"]["sha256"] = sha256_file(output / "design-context.json")
    write_json(output / "test-points.json", points)
    manifest["test_points_baseline"]["sha256"] = sha256_file(output / "test-points.json")
    write_json(path, manifest)
    validate_manifest_file(path)
    (output / "test-cases.xlsx").write_bytes(render_case_workbook(manifest,sha256_file(path),module_paths(points),context))
    summary = []
    for capture in load_json(args.capture):
        run_id = f"ui-{capture['mode']}-{capture['repeat']}"
        run_dir = output / "runs" / run_id
        run_dir.mkdir(parents=True)
        profile_path = run_dir / "execution-profile.json"
        profile = build_profile(manifest,path,profile_path,"smoke",[target])
        for binding in profile["bindings"]: binding.update(status="resolved",source="user-input",value="http://127.0.0.1:8769/ui-oracle-benchmark.html")
        write_json(profile_path,profile)
        run = {"run_id":run_id,"manifest_path":"../../test-manifest.json","manifest_sha256":sha256_file(path),"case_workbook_sha256":sha256_file(output / "test-cases.xlsx"),"execution_profile_path":"execution-profile.json","execution_profile_sha256":sha256_file(profile_path),"suite":"smoke","targets":[target],"environment":{"name":"Loopback synthetic UI","kind":"test","build":"benchmark-1"},"started_at":capture["before_at"],"finished_at":capture["after_at"]}
        result = {"case_id":case["id"],"target_id":target,"attempts":1,"tool":"cua-repl/browser-playwright","status":"passed","observed":"Original DOM values captured by the browser tool; verdicts are derived next.","assertions":[],"evidence":[]}
        for phase in ["before","after"]:
            record = {"format":"wewo-qa-ui-observation/1","run_id":run_id,"case_id":case["id"],"target_id":target,"attempt":1,"subject":capture[phase]["subject"],"location":"Synthetic order fields","captured_at":capture[phase + "_at"],"tool":result["tool"],"raw":capture[phase]}
            ep = run_dir / "evidence" / (phase + ".json")
            write_json(ep,record)
            result["evidence"].append({"id":phase,"type":"tool-output","path":"evidence/"+phase+".json","description":"Original DOM-only browser evaluation result", "sha256":sha256_file(ep)})
        for planned,(field,_,_) in zip(assertions,obligations):
            phases = ["after"] if planned["check"]["kind"] == "equals" else ["before","after"]
            result["assertions"].append({"assertion_id":planned["id"],"description":planned["description"],"expected":planned["expected"],"actual":"To be derived from original output","status":"passed","evidence_refs":phases,"observations":[{"attempt":1,"phase":p,"evidence_id":p,"pointer":"/raw/"+field} for p in phases]})
        results_path = run_dir / "execution-results.json"
        write_json(results_path,{"schema_version":"1.3","run":run,"results":[result]})
        judged_path = run_dir / "execution-results.judged.json"
        for command, result_file in [("judge-execution-results",results_path),("render-execution-report",judged_path)]:
            completed = subprocess.run([str(args.runtime.resolve()),command,str(result_file),str(path)],capture_output=True,text=True,encoding="utf-8",timeout=90)
            if completed.returncode: raise RuntimeError(completed.stdout + completed.stderr)
        judged = load_json(judged_path)["results"][0]
        expected = "passed" if capture["mode"] == "correct" else "failed"
        if judged["status"] != expected: raise RuntimeError("Wrong UI benchmark verdict: " + run_id)
        summary.append({"run":run_id,"status":judged["status"],"failed_assertions":[a["assertion_id"] for a in judged["assertions"] if a["status"] == "failed"]})
    write_json(output / "benchmark-summary.json",summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("WROTE: " + str(output))


if __name__ == "__main__":
    main()
