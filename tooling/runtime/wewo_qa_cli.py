from __future__ import annotations

"""Single entry point for the self-contained Wewo QA runtime binary."""

import sys
from pathlib import Path


if not getattr(sys, "frozen", False):
    plugin_root = Path(__file__).resolve().parents[2]
    sys.path[:0] = [
        str(plugin_root / "skills" / "wewo-qa-case-designer" / "scripts"),
        str(plugin_root / "skills" / "wewo-qa-case-executor" / "scripts"),
    ]

import prepare_execution_profile
import case_workbook
import design_context
import extract_source
import judge_execution_results
import native_execution
import deliverables
import render_execution_report
import render_test_points_xmind
import validate_execution_profile
import validate_execution_results
import validate_test_manifest
import validate_test_points
from runtime_version import VERSION


COMMANDS = {
    "extract-source": extract_source.main,
    "validate-design-context": design_context.main,
    "requirement-digest": design_context.digest_main,
    "validate-test-points": validate_test_points.main,
    "render-test-points-xmind": render_test_points_xmind.main,
    "validate-test-manifest": validate_test_manifest.main,
    "render-case-workbook": case_workbook.render_main,
    "import-case-workbook": case_workbook.import_main,
    "validate-case-workbook": case_workbook.validate_main,
    "prepare-execution-profile": prepare_execution_profile.main,
    "validate-execution-profile": validate_execution_profile.main,
    "validate-execution-results": validate_execution_results.main,
    "judge-execution-results": judge_execution_results.main,
    "render-execution-report": render_execution_report.main,
    "run-native-tests": native_execution.main,
    "validate-deliverables": deliverables.main,
}


def _usage() -> str:
    commands = "\n".join(f"  {name}" for name in COMMANDS)
    return (
        "Wewo QA artifact runtime\n\n"
        "Usage: wewo-qa <command> [arguments]\n\n"
        f"Commands:\n{commands}\n"
    )


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--version":
        print(f"wewo-qa {VERSION}")
        return 0
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help", "help"}:
        print(_usage())
        return 0 if len(sys.argv) >= 2 else 2

    command = sys.argv[1]
    handler = COMMANDS.get(command)
    if handler is None:
        print(f"ERROR: unknown command {command!r}\n", file=sys.stderr)
        print(_usage(), file=sys.stderr)
        return 2

    sys.argv = [f"wewo-qa {command}", *sys.argv[2:]]
    from artifact_tools import ValidationFailure
    try:
        return handler()
    except (ValidationFailure, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
