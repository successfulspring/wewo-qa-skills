"""Verify the independent clarification workbook and four case-design files."""
import argparse
from pathlib import Path
from artifact_tools import ValidationFailure, validate_test_points_file
from case_workbook import validate_case_workbooks
from artifact_layout import CLARIFICATION_FILENAME
from question_workbook import validate_workbook
from validation_session import operation

@operation
def validate_delivery(root, *, draft=False):
    expected = {CLARIFICATION_FILENAME, "test-points.xmind", "test-cases.smoke.xlsx", "test-cases.regression.xlsx", "test-cases.full.xlsx"}
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
    validate_test_points_file(root / ".qa-state" / "test-points.json", final=not draft)
    validate_case_workbooks(root / ".qa-state" / "test-manifest.json", draft=draft)
    validate_workbook(root / '.qa-state' / 'design-context.json', draft=draft)
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
        with zipfile.ZipFile(io.BytesIO(render_xmind_bytes(points, kind, draft=draft))) as rendered:
            if actual.read(content) != rendered.read(content):
                raise ValidationFailure(["delivered XMind differs from confirmed test points"])
    finally:
        actual.close()

def main():
    parser = argparse.ArgumentParser(description="Check clarification XLSX, XMind and three case workbooks together.")
    parser.add_argument("directory", type=Path)
    parser.add_argument('--draft', action='store_true', help='Validate the five current draft deliverables, not an execution baseline.')
    args = parser.parse_args()
    validate_delivery(args.directory.resolve(), draft=args.draft)
    print("OK: clarification workbook, XMind and three Excel suite files; internal state is private")
    return 0
