"""Render the shared question inventory for an answerable chat delivery."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from artifact_language import ArtifactText, output_language
from artifact_tools import load_json, validate_manifest_file
from draft_design import question_rows


def render_questions(context, manifest):
    """Retain every authored decision and option; do not infer missing rules."""
    tr = ArtifactText(output_language(manifest))
    rows = question_rows(context, manifest)
    if not rows:
        return tr('当前没有待确认问题。') + '\n'
    cases = {case['id']: case['title'] for case in manifest['cases']}
    questions = {question['id']: question for question in context['open_questions']}
    result = []
    for qid, sources, description, impact, _rules, _points, case_ids, options in rows:
        result.extend([f'### {qid}', '', description, '',
            f"**{tr('需求追溯')}：** " + (sources.replace('\n', '; ') or tr('未记录')),
            '', f"**{tr('影响')}：** {impact}", '', f"**{tr('涉及用例')}：**"])
        result.extend(f'- {cid} — {cases[cid]}' for cid in case_ids.splitlines())
        if not case_ids:
            result.append(tr('尚未关联用例；请结合上述业务影响确认。'))
        result.extend(['', f"**{tr('可选处理方式')}：**"])
        if options:
            # Preserve each option as authored, including its continuation lines.
            question = questions[qid]
            result.extend(f'{i}. ' + option.replace('\n', '\n   ')
                          for i, option in enumerate(question['options'], 1))
        else:
            result.append(tr('请负责人提供上述具体规则；当前材料没有足够依据列出选项。'))
        result.append('')
    result.append(tr('请按问题编号及子项集中答复。暂时无法确定的项可回复“待定”，相关预期继续保留待确认。'))
    return '\n'.join(result) + '\n'


def render_from_manifest(path, *, draft=False):
    manifest = validate_manifest_file(path, final=not draft)
    context = load_json(path.with_name('design-context.json'))
    return render_questions(context, manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--draft', action='store_true', help='Read a confirmed draft with pending expectations.')
    args = parser.parse_args()
    text = render_from_manifest(args.manifest.resolve(), draft=args.draft)
    # Chat output must retain Chinese and literal Unicode on Windows as well.
    sys.stdout.reconfigure(encoding='utf-8')
    print(text, end='')
    return 0
