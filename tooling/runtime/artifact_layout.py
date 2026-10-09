"""Public deliverables and private state have distinct, fixed locations."""
from pathlib import Path

SUITES = ("smoke", "regression", "full")

def artifact_root(baseline: Path) -> Path:
    parent = baseline.resolve().parent
    return parent.parent if parent.name == ".qa-state" else parent

def case_workbook_path(manifest: Path, suite: str) -> Path:
    if suite not in SUITES:
        raise ValueError("unknown case suite")
    return artifact_root(manifest) / f"test-cases.{suite}.xlsx"
