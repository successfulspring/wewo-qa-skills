from __future__ import annotations

"""Maintenance check: use the bundled executable for complete artifact operations."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tooling/runtime"), str(ROOT / "skills/wewo-qa-case-designer/scripts"), str(ROOT / "skills/wewo-qa-case-executor/scripts"), str(ROOT / "tests")]
from artifact_factory import execution_set, write_json, mutate_observation
from artifact_tools import sha256_file
from openpyxl import load_workbook
from runtime_version import VERSION


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True, type=Path)
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    def run(*arguments, fail=False):
        result = subprocess.run([str(runtime), *map(str, arguments)], text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=90)
        if (result.returncode != 0) != fail:
            raise RuntimeError(f"command {' '.join(map(str, arguments))}: {result.returncode}\n{result.stdout}\n{result.stderr}")
        return result.stdout
    if run("--version").strip() != f"wewo-qa {VERSION}":
        raise RuntimeError("runtime version does not match source")
    with tempfile.TemporaryDirectory(prefix="wewo-qa-smoke-") as folder:
        directory = Path(folder)
        manifest, path, profile, profile_path, results, results_path = execution_set(directory)
        run("validate-design-context", directory / "design-context.json")
        run("validate-test-points", directory / "test-points.json")
        run("render-test-points-xmind", directory / "test-points.json")
        run("render-test-points-xmind", directory / "test-points.json", "--format", "zen", "--output", directory / "points-zen.xmind")
        run("validate-test-manifest", path)
        run("render-case-workbook", path)
        run("validate-case-workbook", path)
        # A new export changes the workbook container hash; bind this run to that export.
        workbook_hash = sha256_file(directory / "test-cases.smoke.xlsx")
        profile["case_workbook_sha256"] = workbook_hash
        write_json(profile_path, profile)
        results["run"]["case_workbook_sha256"] = workbook_hash
        results["run"]["execution_profile_sha256"] = sha256_file(profile_path)
        write_json(results_path, results)
        run("prepare-execution-profile", path, "--suite", "smoke", "--target", "web-chrome", "--output", results_path.parent / "missing-profile.json")
        run("validate-execution-profile", profile_path, path)
        run("validate-execution-results", results_path, path)
        run("judge-execution-results", results_path, path)
        run("validate-execution-results", results_path.with_name("execution-results.judged.json"), path)
        run("render-execution-report", results_path, path)
        # Missing planned checks must fail independently of a successful interaction.
        removed = results["results"][0]["assertions"].pop()
        write_json(results_path, results)
        run("validate-execution-results", results_path, path, fail=True)
        results["results"][0]["assertions"].append(removed)
        results["results"][0].update(status="failed", failure_reason="Controlled synthetic mismatch")
        removed.update(status="failed", actual="Synthetic mismatching outcome")
        mutate_observation(results["results"][0], removed, results_path.parent, "Synthetic mismatching outcome")
        # A falsely declared pass must be rejected, then judging must recover the
        # failing verdict from the evidence without changing the expected value.
        removed["status"] = "passed"
        results["results"][0]["status"] = "passed"
        write_json(results_path, results)
        run("validate-execution-results", results_path, path, fail=True)
        run("judge-execution-results", results_path, path, "--output", results_path.with_name("fault-judged.json"))
        run("validate-execution-results", results_path.with_name("fault-judged.json"), path)
        removed["status"] = "failed"
        results["results"][0]["status"] = "failed"
        write_json(results_path, results)
        run("render-execution-report", results_path, path)
        report = load_workbook(results_path.parent / "test-execution-report.xlsx")
        if report["执行汇总"]["B3"].value != "FAILED":
            raise RuntimeError("controlled mismatch did not fail the report gate")
        report.close()
        workbook = load_workbook(directory / "test-cases.smoke.xlsx")
        workbook["测试用例"]["C2"] = "Tester edit"
        workbook.save(directory / "test-cases.smoke.xlsx")
        workbook.close()
        run("validate-case-workbook", path, fail=True)
        run("import-case-workbook", path)
        pending = json.loads((directory / "test-manifest.pending.json").read_text(encoding="utf-8"))
        if pending["review"]["status"] != "pending" or not any(c["title"] == "Tester edit" for c in pending["cases"]):
            raise RuntimeError("Excel edit was not retained for review")
        run("validate-test-manifest", directory / "test-manifest.pending.json", fail=True)
        source = directory / "source.docx"
        from docx import Document
        document = Document()
        document.add_paragraph("Synthetic source rule")
        document.save(source)
        run("extract-source", source, "--source-id", "SRC-001", "--output", directory / "source.json")
        from pptx import Presentation
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[1])
        slide.shapes.title.text = "Synthetic flow"
        presentation.save(directory / "source.pptx")
        run("extract-source", directory / "source.pptx", "--source-id", "SRC-002", "--output", directory / "slides.json")
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.write(directory / "source.pdf")
        run("extract-source", directory / "source.pdf", "--source-id", "SRC-003", "--output", directory / "pdf.json")
        from PIL import Image
        Image.new("RGB", (10, 10), "white").save(directory / "source.png")
        run("extract-source", directory / "source.png", "--source-id", "SRC-004", "--output", directory / "image.json")
        run("extract-source", directory / "test-cases.smoke.xlsx", "--source-id", "SRC-005", "--output", directory / "excel-source.json")
        run("extract-source", directory / "test-points.xmind", "--source-id", "SRC-006", "--output", directory / "xmind-source.json")
        context_path, points_path = directory / "design-context.json", directory / "test-points.json"
        context = json.loads(context_path.read_text(encoding="utf-8"))
        context["review"] = {"status": "draft"}
        context["open_questions"] = [{"id": "Q-001", "description": "Synthetic unanswered scope", "material": True}]
        write_json(context_path, context)
        points = json.loads(points_path.read_text(encoding="utf-8"))
        points["design_context_baseline"]["sha256"] = sha256_file(context_path)
        write_json(points_path, points)
        run("validate-test-points", points_path, "--draft")
        run("render-test-points-xmind", points_path, "--draft")
        run("render-test-points-xmind", points_path, fail=True)
    print("OK: bundled extraction, XMind, Excel roundtrip, profile, assertion rejection and failure report smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
