"""One snapshot, staged five-file delivery and measurable operation-local checks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import uuid

from artifact_tools import ValidationFailure, load_json, validate_test_points_file, validate_manifest_file, write_bytes_atomic
from case_workbook import render_case_workbooks
from deliverables import validate_delivery
from question_workbook import render_workbook, validate_workbook
from render_test_points_xmind import render_xmind_bytes
from state_transaction import publish_batch
from validation_session import current, operation, phase

PUBLIC = ['requirement-clarifications.xlsx', 'test-points.xmind',
          'test-cases.smoke.xlsx', 'test-cases.regression.xlsx', 'test-cases.full.xlsx']


def copy_history(source, destination):
    if not source.exists(): return
    for p in source.rglob('*'):
        if p.is_symlink() or getattr(p, 'is_junction', lambda: False)():
            raise ValidationFailure(['history must not traverse linked directories: ' + str(p)])
        target = destination / p.relative_to(source)
        if p.is_dir(): target.mkdir(parents=True, exist_ok=True)
        elif p.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(p.read_bytes())


def layout_report(root):
    from openpyxl import load_workbook
    from xlsx_support import wrapped_lines
    from openpyxl.utils import get_column_letter
    risks = []
    for path in root.glob('*.xlsx'):
        book = load_workbook(path, data_only=False)
        try:
            for sheet in book:
                if sheet.sheet_state != 'visible': continue
                for row in sheet.iter_rows(min_row=2):
                    for cell in row:
                        if cell.value is None: continue
                        width = sheet.column_dimensions[get_column_letter(cell.column)].width or 24
                        needed = wrapped_lines(cell.value, width) * 16 + 10
                        actual = sheet.row_dimensions[cell.row].height or 15
                        if needed > actual + 1:
                            risks.append({'file': path.name, 'sheet': sheet.title, 'cell': cell.coordinate,
                                          'estimated_height': needed, 'row_height': actual,
                                          'reason': 'row-height-limit' if needed > 409 else 'layout-needs-review'})
        finally:
            book.close()
    return risks


@operation
def build_delivery(root, stage='draft'):
    root = Path(root).resolve()
    state = root / '.qa-state'
    if stage not in {'clarification', 'draft', 'final'}: raise ValueError('unknown delivery stage')
    if not (state / 'design-context.json').is_file(): raise ValidationFailure(['missing .qa-state/design-context.json'])
    if stage == 'clarification' and (state / 'test-manifest.json').exists():
        raise ValidationFailure(['existing cases require draft/final delivery; retain their clarification links'])
    names = PUBLIC[:1] if stage == 'clarification' else PUBLIC
    expected = {str(root / n): hashlib.sha256((root / n).read_bytes()).hexdigest() if (root / n).exists() else None for n in names}
    token = uuid.uuid4().hex
    staging = state / 'work' / 'delivery' / token
    staged_state = staging / '.qa-state'
    staged_state.mkdir(parents=True)
    original_baselines = {}
    with phase('snapshot-and-edit-protection'):
        for name in ('design-context.json', 'test-points.json', 'test-manifest.json'):
            path = state / name
            if path.exists():
                raw = current().read(path)
                original_baselines[path] = hashlib.sha256(raw).hexdigest()
                (staged_state / name).write_bytes(raw)
        copy_history(state / 'history', staged_state / 'history')
        for name in names:
            if (root / name).exists():
                (staging / name).write_bytes((root / name).read_bytes())
    with phase('validate-and-render-cases'):
        if stage != 'clarification':
            points = validate_test_points_file(staged_state / 'test-points.json', final=stage == 'final')
            validate_manifest_file(staged_state / 'test-manifest.json', final=stage == 'final')
            write_bytes_atomic(staging / 'test-points.xmind', render_xmind_bytes(points, draft=stage == 'draft'))
            render_case_workbooks(staged_state / 'test-manifest.json', draft=stage == 'draft')
    with phase('clarification-and-readback'):
        render_workbook(staged_state / 'design-context.json', draft=stage == 'draft')
        if stage == 'clarification': validate_workbook(staged_state / 'design-context.json')
        else: validate_delivery(staging, draft=stage == 'draft')
    with phase('layout-check'):
        risks = layout_report(staging)
    with phase('publish'):
        current().unchanged()
        # Context may have changed outside this process while files were rendering.
        for p, digest in original_baselines.items():
            if hashlib.sha256(p.read_bytes()).hexdigest() != digest:
                raise ValidationFailure(['baseline changed during delivery: ' + str(p)])
        files = {root / name: (staging / name).read_bytes() for name in names}
        publish_batch(files, state / 'work' / 'transactions', expected)
    report = {'stage': stage, 'outputs': [str(root / n) for n in names],
              'layout_review': risks, **current().report()}
    report_path = state / 'work' / 'performance' / (token + '.json')
    write_bytes_atomic(report_path, json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8'))
    return {**report, 'report': str(report_path)}


def main():
    parser = argparse.ArgumentParser(description='Stage, validate and publish clarification or all five design deliverables using one snapshot.')
    parser.add_argument('directory', type=Path)
    parser.add_argument('--stage', choices=('clarification', 'draft', 'final'), required=True)
    args = parser.parse_args()
    result = build_delivery(args.directory, args.stage)
    # Large row-risk inventories stay in the private report; never silently drop them.
    print(json.dumps({k: v for k, v in result.items() if k != 'layout_review'} | {
        'layout_review_count': len(result['layout_review']), 'layout_review_sample': result['layout_review'][:5]}, ensure_ascii=False))
    return 0
