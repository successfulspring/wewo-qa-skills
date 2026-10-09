"""Verify the tester's four-file delivery, not an engineering scratch folder."""
import argparse
from pathlib import Path
from artifact_tools import ValidationFailure, validate_test_points_file
from case_workbook import validate_case_workbooks

def validate_delivery(root):
    expected = {"test-points.xmind", "test-cases.smoke.xlsx", "test-cases.regression.xlsx", "test-cases.full.xlsx"}
    allowed = expected | {".qa-state", "test-execution-report.xlsx", "test-report"}
    errors = []
    if not (root / ".qa-state").is_dir():
        errors.append("internal baselines must be under .qa-state")
    for name in sorted(expected):
        if not (root / name).is_file():
            errors.append("missing tester deliverable: " + name)
    for child in root.iterdir():
        if child.name not in allowed:
            errors.append("not a tester deliverable; move task-owned scratch/state to private workspace: " + child.name)
    if errors:
        raise ValidationFailure(errors)
    validate_test_points_file(root / ".qa-state" / "test-points.json")
    validate_case_workbooks(root / ".qa-state" / "test-manifest.json")
    # Confirm XMind is the actual rendered tree, not just a file with the right name.
    from artifact_tools import load_json
    import zipfile
    points = load_json(root / ".qa-state" / "test-points.json")
    from render_test_points_xmind import render_xmind_bytes
    # ZIP containers differ in timestamps. Compare semantic content entries.
    import io
    actual = zipfile.ZipFile(root / "test-points.xmind")
    try:
        kind = "legacy" if "content.xml" in actual.namelist() else "zen"
        content = "content.xml" if kind == "legacy" else "content.json"
        with zipfile.ZipFile(io.BytesIO(render_xmind_bytes(points, kind))) as rendered:
            if actual.read(content) != rendered.read(content):
                raise ValidationFailure(["delivered XMind differs from confirmed test points"])
    finally:
        actual.close()

def main():
    parser = argparse.ArgumentParser(description="Check the clean XMind and three-Excel tester delivery.")
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    validate_delivery(args.directory.resolve())
    print("OK: XMind and three Excel suite files; internal state is private")
    return 0
