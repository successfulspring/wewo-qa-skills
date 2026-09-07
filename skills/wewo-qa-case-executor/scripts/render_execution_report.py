from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from artifact_tools import md_cell, validate_results_file, write_text_atomic


STATUS_LABELS = {
    "passed": "通过",
    "failed": "失败",
    "blocked": "阻塞",
    "flaky": "不稳定",
    "not-run": "未执行",
}


def _automatic_gate(results: dict[str, Any], manifest: dict[str, Any]) -> str:
    case_by_id = {case["id"]: case for case in manifest["cases"]}
    relevant = []
    for result in results["results"]:
        case = case_by_id[result["case_id"]]
        automation = next(item for item in case["automation"] if item["target_id"] == result["target_id"])
        if automation["feasibility"] != "manual":
            relevant.append(result)
    if any(item["status"] == "failed" for item in relevant):
        return "FAILED"
    if any(item["status"] in {"blocked", "flaky", "not-run"} for item in relevant):
        return "INCOMPLETE"
    return "PASSED"


def render_report(results: dict[str, Any], manifest: dict[str, Any]) -> str:
    run = results["run"]
    project = manifest["project"]
    counts = Counter(item["status"] for item in results["results"])
    gate = _automatic_gate(results, manifest)
    case_by_id = {case["id"]: case for case in manifest["cases"]}
    target_by_id = {target["id"]: target for target in project["targets"]}
    lines = [
        f"# {project['name']} — 自动化测试执行报告",
        "",
        "| 字段 | 内容 |",
        "| --- | --- |",
        f"| 自动化执行门禁 | **{gate}** |",
        f"| Run ID | {md_cell(run['run_id'])} |",
        f"| 用例集 | {run['suite']} |",
        f"| 目标 | {md_cell(', '.join(run['targets']))} |",
        f"| 环境 | {md_cell(run['environment']['name'])}（{run['environment']['kind']}） |",
        f"| 构建 | {md_cell(run['environment']['build'])} |",
        f"| 开始时间 | {run['started_at']} |",
        f"| 结束时间 | {run['finished_at']} |",
        f"| 用例清单 SHA-256 | `{run['manifest_sha256']}` |",
        f"| 执行条件清单 | {md_cell(run['execution_profile_path'])} @ `{run['execution_profile_sha256']}` |",
        "",
        "## 结果汇总",
        "",
        "| 通过 | 失败 | 阻塞 | 不稳定 | 未执行 | 总计 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| {counts['passed']} | {counts['failed']} | {counts['blocked']} | {counts['flaky']} | {counts['not-run']} | {len(results['results'])} |",
        "",
        "> `not-run` 包含人工用例；人工用例不计入自动化执行门禁，但必须由测试人员另行处理。",
        "",
        "## 明细",
        "",
        "| 用例 | 目标 | 平台 | 状态 | 尝试 | 工具 | 观察与原因 |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for result in results["results"]:
        case = case_by_id[result["case_id"]]
        target = target_by_id[result["target_id"]]
        reason = result.get("failure_reason") or result.get("blocker") or result.get("observed") or "—"
        platform = f"{target['surface']} / {target['os']}"
        lines.append(
            f"| {result['case_id']} {md_cell(case['title'])} | {result['target_id']} | {platform} | "
            f"{STATUS_LABELS[result['status']]} | {result['attempts']} | {md_cell(result['tool'] or '—')} | {md_cell(reason)} |"
        )

    exceptional = [item for item in results["results"] if item["status"] != "passed"]
    if exceptional:
        lines.extend(["", "## 非通过项", ""])
        for result in exceptional:
            lines.extend([f"### {result['case_id']} / {result['target_id']} — {STATUS_LABELS[result['status']]}", ""])
            if result.get("failure_reason"):
                lines.append(f"- 失败原因：{result['failure_reason']}")
            if result.get("blocker"):
                lines.append(f"- 阻塞/未执行原因：{result['blocker']}")
            if result.get("observed"):
                lines.append(f"- 实际观察：{result['observed']}")
            if result["assertions"]:
                lines.append("- 断言：")
                for assertion in result["assertions"]:
                    symbol = "✓" if assertion["passed"] else "✗"
                    lines.append(
                        f"  - {symbol} {assertion['description']}；期望：{assertion['expected']}；实际：{assertion['actual']}"
                    )
            if result["evidence"]:
                lines.append("- 证据：")
                for evidence in result["evidence"]:
                    lines.append(f"  - [{evidence['description']}]({evidence['path']})（{evidence['type']}）")
            lines.append("")

    if run.get("notes"):
        lines.extend(["## 执行说明", "", run["notes"], ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Wewo QA execution report.")
    parser.add_argument("results", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results_path = args.results.resolve()
    manifest_path = args.manifest.resolve()
    output_path = args.output.resolve() if args.output else results_path.parent / "test-execution-report.md"
    results, manifest = validate_results_file(results_path, manifest_path)
    write_text_atomic(output_path, render_report(results, manifest))
    print(f"WROTE: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
