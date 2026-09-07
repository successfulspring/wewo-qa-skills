from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from artifact_tools import md_cell, md_list, validate_manifest_file, write_text_atomic


SUITES = {
    "smoke": ("冒烟测试用例", "smoke-test-cases.md"),
    "regression": ("回归测试用例", "regression-test-cases.md"),
    "full": ("全量测试用例", "full-test-cases.md"),
}

FEASIBILITY_LABELS = {
    "automatable": "可自动化",
    "conditional": "条件自动化",
    "manual": "人工",
}


def _target_summary(target: dict[str, Any]) -> str:
    details = [target["surface"], target["os"]]
    for key in ("os_version", "browser", "browser_version", "device", "device_mode", "host"):
        if target.get(key):
            details.append(str(target[key]))
    return " / ".join(details)


def _requirement_label(requirement_id: str, requirements: dict[str, dict[str, Any]]) -> str:
    requirement = requirements[requirement_id]
    return f"{requirement_id} {requirement['name']}"


def _render_case(
    case: dict[str, Any],
    targets: dict[str, dict[str, Any]],
    requirements: dict[str, dict[str, Any]],
) -> str:
    lines = [
        f"## {case['id']} {case['title']}",
        "",
        "| 字段 | 内容 |",
        "| --- | --- |",
        f"| 优先级 | {case['priority']} |",
        f"| 风险 | {case['risk']} |",
        f"| 所属用例集 | {', '.join(case['suite_membership'])} |",
        f"| 适用目标 | {', '.join(case['applicable_targets'])} |",
        f"| 需求追踪 | {md_cell(', '.join(case['source_refs']))} |",
        f"| 测试点追踪 | {md_cell(', '.join(case['test_point_refs']))} |",
    ]
    if case.get("variant_of"):
        lines.append(f"| 平台变体基线 | {case['variant_of']} |")
    common_requirements = [
        _requirement_label(requirement_id, requirements) for requirement_id in case["runtime_requirement_refs"]
    ]
    lines.extend(["", "### 执行所需外部条件", "", md_list(common_requirements)])
    lines.extend(["", "### 前置条件", "", md_list(case["preconditions"]), "", "### 测试数据", "", md_list(case["test_data"]), ""])
    lines.extend(["### 操作步骤与预期结果", "", "| # | 操作 | 可观察预期结果 |", "| ---: | --- | --- |"])
    for index, step in enumerate(case["steps"], 1):
        lines.append(f"| {index} | {md_cell(step['action'])} | {md_cell(step['expected'])} |")
    lines.extend(["", "### 自动化评估", "", "| 目标 | 平台 | 可行性 | 候选路径 | 目标专属外部条件 | 条件或原因 | 必需证据 |", "| --- | --- | --- | --- | --- | --- | --- |"])
    for automation in case["automation"]:
        target = targets[automation["target_id"]]
        condition_or_reason = automation.get("condition") or automation.get("reason") or "—"
        evidence = ", ".join(automation["required_evidence"]) or "—"
        target_requirements = ", ".join(
            _requirement_label(requirement_id, requirements)
            for requirement_id in automation["runtime_requirement_refs"]
        ) or "—"
        lines.append(
            f"| {automation['target_id']} | {md_cell(_target_summary(target))} | "
            f"{FEASIBILITY_LABELS[automation['feasibility']]} | {automation['candidate_route']} | "
            f"{md_cell(target_requirements)} | {md_cell(condition_or_reason)} | {md_cell(evidence)} |"
        )
    safety = case["safety"]
    lines.extend(
        [
            "",
            "### 安全与清理",
            "",
            f"- 影响级别：`{safety['impact']}`",
            f"- 执行前确认：{'需要' if safety['requires_confirmation'] else '不需要'}",
            f"- 清理步骤：{'；'.join(safety['cleanup_steps']) if safety['cleanup_steps'] else '无'}",
        ]
    )
    if safety.get("notes"):
        lines.append(f"- 安全说明：{safety['notes']}")
    if case.get("notes"):
        lines.extend(["", f"> 备注：{case['notes']}"])
    lines.append("")
    return "\n".join(lines)


def render_suite(manifest: dict[str, Any], suite: str) -> str:
    title, _ = SUITES[suite]
    project = manifest["project"]
    cases = [case for case in manifest["cases"] if suite in case["suite_membership"]]
    target_ids = {target_id for case in cases for target_id in case["applicable_targets"]}
    targets = {target["id"]: target for target in project["targets"]}
    requirements = {item["id"]: item for item in manifest["runtime_requirements"]}
    requirement_ids = {
        requirement_id
        for case in cases
        for requirement_id in (
            case["runtime_requirement_refs"]
            + [
                ref
                for automation in case["automation"]
                for ref in automation["runtime_requirement_refs"]
            ]
        )
    }
    lines = [
        f"# {project['name']} — {title}",
        "",
        "> 本文档由 `test-manifest.json` 自动生成；请修改清单后重新生成，不要直接维护本文档。",
        "",
        "| 字段 | 内容 |",
        "| --- | --- |",
        f"| 需求/版本 | {md_cell(project['requirement'])} |",
        f"| 基线 | {md_cell(project['baseline'])} |",
        f"| 用例集 | {suite} |",
        f"| 用例数量 | {len(cases)} |",
        f"| 生成时间 | {manifest['generated_at']} |",
        f"| 测试点基线 | {manifest['test_points_baseline']['path']} @ {manifest['test_points_baseline']['sha256'][:12]} |",
        "",
        "## 本次目标",
        "",
        "| ID | 名称 | 产品形态 | 操作系统 | 范围 | 其他信息 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for target in project["targets"]:
        if target["id"] not in target_ids:
            continue
        extra = []
        for key in ("browser", "browser_version", "os_version", "device", "device_mode", "host"):
            if target.get(key):
                extra.append(f"{key}={target[key]}")
        lines.append(
            f"| {target['id']} | {md_cell(target['name'])} | {target['surface']} | {target['os']} | "
            f"{'范围内' if target['in_scope'] else '范围外'} | {md_cell(', '.join(extra) or '—')} |"
        )
    lines.extend(["", "## 需求来源", ""])
    for source in manifest["sources"]:
        lines.append(f"- `{source['id']}` {source['title']}（{source['type']}，{source['authority']}）：{source['locator']}")
    if manifest["decisions"]:
        lines.extend(["", "## 已确认决定与假设", "", "| ID | 状态 | 主题 | 结论 |", "| --- | --- | --- | --- |"])
        for decision in manifest["decisions"]:
            resolution = decision["resolution"]
            if decision.get("rationale"):
                resolution += f"（依据：{decision['rationale']}）"
            lines.append(f"| {decision['id']} | {decision['status']} | {md_cell(decision['topic'])} | {md_cell(resolution)} |")
    lines.extend(
        [
            "",
            "## 执行所需外部条件",
            "",
            "> 此处只声明执行时需要提供或检查的条件；密码、Token、Cookie 等敏感值不得写入用例文档。",
            "",
            "| ID | 名称 | 类型 | 范围 | 目标 | 获取方式 | 敏感 | 说明 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for requirement in manifest["runtime_requirements"]:
        if requirement["id"] not in requirement_ids:
            continue
        lines.append(
            f"| {requirement['id']} | {md_cell(requirement['name'])} | {requirement['kind']} | "
            f"{requirement['scope']} | {md_cell(', '.join(requirement.get('target_ids', [])) or '—')} | "
            f"{requirement['collection']} | "
            f"{'是' if requirement['sensitive'] else '否'} | {md_cell(requirement['description'])} |"
        )
    lines.extend(["", "## 测试用例", ""])
    if not cases:
        lines.append("当前用例集为空。")
    else:
        for case in cases:
            lines.append(_render_case(case, targets, requirements))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Wewo QA smoke, regression, and full Markdown documents.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir else manifest_path.parent
    manifest = validate_manifest_file(manifest_path)
    for suite, (_, filename) in SUITES.items():
        output_path = output_dir / filename
        write_text_atomic(output_path, render_suite(manifest, suite))
        print(f"WROTE: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
