"""One persistent clarification workbook, available before any case design."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import PatternFill

from artifact_language import ArtifactText, output_language
from artifact_layout import clarification_workbook_path
from artifact_tools import ValidationFailure, sha256_file, validate_manifest_file, write_bytes_atomic
from design_context import validate_design_context_file
from draft_design import question_rows, question_refs
from requirement_readiness import dialogue_links, readiness_errors
from xlsx_support import load_case_excel, text_cell, workbook_bytes
from validation_session import operation


HEADERS = ['疑问编号', '需求追溯', '待确认内容', '影响', '规则编号', '测试点编号', '用例编号',
           '可选处理方式', '澄清状态', '答复内容', '处理结论', '答复依据', '阻塞整体确认']
ANSWER = HEADERS.index('答复内容')
SHEET = '需求澄清'
FORMAT = '1.0'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def response_view(context, qid):
    """Keep actual replies distinct from their interpreted decision resolutions."""
    _, _, answered, _ = dialogue_links(context)
    replies = [e for e in context['dialogue_events'] if qid in answered.get(e['id'], {})]
    if not replies:
        return '', ''
    event = replies[-1]
    scoped = next((r['text'] for r in event.get('responses', []) if r['question_id'] == qid), event['text'])
    return scoped, '\n'.join(e['message_ref'] for e in replies)


def clarification_rows(context, manifest=None):
    tr = ArtifactText(output_language(context))
    questions = [*context['open_questions'], *context.get('closed_questions', [])]
    inventory = dict(context, open_questions=questions)
    rows = question_rows(inventory, manifest)
    cases = {c['id']: c for c in (manifest or {}).get('cases', [])}
    closed = {q['id']: q for q in context.get('closed_questions', [])}
    for row, question in zip(rows, questions):
        qid = question['id']
        decisions = [d for d in context['decisions'] if d.get('question_id') == qid and d['status'] == 'confirmed']
        dids = {d['id'] for d in decisions}
        rules = [r for r in context['rules'] if qid in question_refs(r) or dids & set(r['decision_refs'])]
        point_ids = set(row[5].splitlines())
        point_ids.update(p for r in rules if dids & set(r['decision_refs']) for model in r['design_models'] for item in model['items'] for p in item['test_point_refs'])
        case_ids = set(row[6].splitlines())
        case_ids.update(c['id'] for c in cases.values() if point_ids & set(c['test_point_refs']))
        row[4] = '\n'.join(r['id'] for r in rules)
        row[5] = '\n'.join(sorted(point_ids)) if manifest else ''
        row[6] = ('\n'.join(cid + ' — ' + cases[cid]['title'] for cid in sorted(case_ids)) or tr('尚未关联用例；请结合上述业务影响确认。')) if manifest else tr('尚未生成用例；先确认上述业务影响。')
        if not row[7]:
            row[7] = tr('请负责人提供上述具体规则；当前材料没有足够依据列出选项。')
        response, evidence = response_view(context, qid)
        # A confirmed decision may only acknowledge deferral. Active questions
        # stay pending; actual answered parts remain visible in the resolution.
        state = '已解决' if qid in closed else '待确认'
        if qid in closed and closed[qid]['disposition'] == 'excluded':
            state = '已排除'
        row.extend([tr(state), response, '\n'.join(d['resolution'] for d in decisions),
                    '\n'.join(filter(None, [evidence, *(ref for d in decisions for ref in d.get('approval_refs', []))])),
                    tr('是' if question.get('blocking') and qid not in closed else '否')])
    return rows


def inputs(context_path, *, draft=False, manifest_path=None):
    context = validate_design_context_file(context_path, final=False)
    manifest_path = manifest_path or context_path.with_name('test-manifest.json')
    if manifest_path.exists():
        if manifest_path.parent.resolve() != context_path.parent.resolve():
            raise ValidationFailure(['clarification and manifest must use the same context directory'])
        manifest = validate_manifest_file(manifest_path, final=not draft)
    else:
        manifest = None
        errors = readiness_errors(context, final=False, clarification=True)
        if errors:
            raise ValidationFailure(errors)
    return context, manifest


def render_bytes(context, manifest=None):
    tr = ArtifactText(output_language(context))
    rows = clarification_rows(context, manifest)
    workbook = Workbook()
    workbook.remove(workbook.active)
    sheet = tr.add_table(workbook, SHEET, HEADERS, rows, {
        '疑问编号':16, '待确认内容':65, '影响':45, '可选处理方式':48, '答复内容':55,
        '处理结论':48, '用例编号':48, '澄清状态':18, '阻塞整体确认':16})
    for row in sheet.iter_rows(min_row=2):
        row[ANSWER].fill = PatternFill('solid', fgColor='FFF2CC')
    tr.add_table(workbook, '使用说明', ['项目', '说明'], [
        [tr('项目'), context['project']['name']],
        [tr('阶段'), tr('用例同步' if manifest else '整体业务澄清')],
        [tr('说明'), tr('先阅读整体业务理解和全部问题，在黄色答复列集中填写，或按编号在聊天中答复。整体确认不等于确认未知规则。')],
        [tr('可编辑'), tr('仅编辑答复内容，可排序；其余列由 Designer 更新。新问题或问题纠正在答复中说明，不删除历史行。')],
        [tr('处理结论'), tr('答复回读后结合实际业务依据更新规则与用例；填写单元格不会自动确认业务、关闭问题或放行执行。')],
        [tr('稳定编号'), tr('同一问题沿用编号。未决项、部分答复和已解决结论持续保留；生成用例后补充关联用例。')],
        [tr('说明'), tr('当前没有待确认问题。') if not context['open_questions'] else tr('局部未决项允许生成带待确认预期的初稿；整体范围或主流程冲突需先澄清。')],
    ], {'项目':24, '说明':110})
    metadata = workbook.create_sheet('_baseline')
    metadata.sheet_state = 'veryHidden'
    payload = canonical({'language':output_language(context), 'rows':rows,
                         'questions':{q['id']:q for q in [*context['open_questions'], *context.get('closed_questions', [])]}})
    meta = [('format', FORMAT), ('sha256', hashlib.sha256(payload.encode()).hexdigest())]
    meta += [('payload', payload[i:i + 30000]) for i in range(0, len(payload), 30000)]
    for i, values in enumerate(meta, 1):
        for j, value in enumerate(values, 1):
            text_cell(metadata.cell(i, j), value)
    return workbook_bytes(workbook)


def read_workbook(path):
    book = load_case_excel(path)
    try:
        metadata = list(book['_baseline'].values)
        values = {r[0]:r[1] for r in metadata if r[0] != 'payload'}
        payload = ''.join(r[1] for r in metadata if r[0] == 'payload')
        if values.get('format') != FORMAT or values.get('sha256') != hashlib.sha256(payload.encode()).hexdigest():
            raise ValidationFailure(['clarification workbook baseline changed or unsupported format'])
        baseline = json.loads(payload)
        tr = ArtifactText(baseline['language'])
        if set(book.sheetnames) != {tr(SHEET), tr('使用说明'), '_baseline'}:
            raise ValidationFailure(['preserve the clarification workbook sheets'])
        rows = [[r[h] for h in HEADERS] for r in tr.read_table(book, SHEET, HEADERS)]
        original = {r[0]:r for r in baseline['rows']}
        if len(rows) != len(original) or {r[0] for r in rows} != set(original):
            raise ValidationFailure(['clarification question IDs/rows changed; retain every question'])
        for row in rows:
            if any(a != b for i, (a,b) in enumerate(zip(row, original[row[0]])) if i != ANSWER):
                raise ValidationFailure([row[0] + ': only the clarification answer column is editable'])
        return baseline, rows
    except (KeyError, ValueError, TypeError, IndexError) as exc:
        raise ValidationFailure(['invalid clarification workbook: ' + str(exc)]) from exc
    finally:
        book.close()


@operation
def render_workbook(context_path, *, draft=False):
    context, manifest = inputs(context_path, draft=draft)
    path = clarification_workbook_path(context_path)
    if path.exists():
        baseline, edited = read_workbook(path)
        before = {r[0]:r for r in baseline['rows']}
        current = {r[0]:r for r in clarification_rows(context, manifest)}
        if set(before) - set(current):
            raise ValidationFailure(['retain resolved questions in closed_questions before updating the clarification workbook'])
        for row in edited:
            if row[ANSWER] != before[row[0]][ANSWER] and row[ANSWER] != current[row[0]][ANSWER]:
                raise ValidationFailure([row[0] + ': unreviewed clarification answer; import and reconcile before exporting'])
    write_bytes_atomic(path, render_bytes(context, manifest))
    validate_workbook(context_path, draft=draft)
    return path


@operation
def validate_workbook(context_path, *, draft=False):
    context, manifest = inputs(context_path, draft=draft)
    baseline, rows = read_workbook(clarification_workbook_path(context_path))
    if baseline['language'] != output_language(context) or sorted(rows) != sorted(clarification_rows(context, manifest)):
        raise ValidationFailure(['clarification workbook has unreviewed answers or stale question/status/case links; reconcile and rerender'])


def import_answers(context_path):
    """Return literal cell edits as one evidence packet; do not approve or mutate state."""
    context = validate_design_context_file(context_path, final=False)
    path = clarification_workbook_path(context_path)
    baseline, rows = read_workbook(path)
    before = {r[0]:r for r in baseline['rows']}
    questions = {q['id']:q for q in [*context['open_questions'], *context.get('closed_questions', [])]}
    responses = []
    for row in rows:
        qid = row[0]
        if row[ANSWER] == before[qid][ANSWER]:
            continue
        current = questions.get(qid, {})
        prior = baseline['questions'][qid]
        if any(current.get(k) != prior.get(k) for k in ('description', 'options', 'source_refs', 'unit_id', 'impact')):
            raise ValidationFailure([qid + ': answer addresses a changed or missing question; reconcile its prior wording first'])
        responses.append({'question_id':qid, 'text':row[ANSWER]})
    return {'workbook':str(path), 'sha256':sha256_file(path), 'responses':responses}


def main(operation):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('context', type=Path)
    parser.add_argument('--draft', action='store_true', help='Use the current draft case manifest when present.')
    args = parser.parse_args()
    path = args.context.resolve()
    if operation == 'render':
        print('WROTE: ' + str(render_workbook(path, draft=args.draft)))
    elif operation == 'validate':
        validate_workbook(path, draft=args.draft)
        print('OK: independent clarification workbook matches questions, replies and current cases')
    else:
        sys.stdout.reconfigure(encoding='utf-8')
        print(json.dumps(import_answers(path), ensure_ascii=False, indent=2))
    return 0


def render_main():
    return main('render')


def validate_main():
    return main('validate')


def import_main():
    return main('import')
