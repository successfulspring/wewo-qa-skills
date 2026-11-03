"""Write explicit business/design changes; derive only redundant mechanical fields."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from artifact_tools import (DESIGNER_SCHEMA_ROOT, ValidationFailure, load_json, schema_errors,
                            sha256_file, walk_test_points, validate_test_points_data, validate_manifest_data)
from design_context import validate_design_context_data, requirement_digest
from requirement_confirmation import business_snapshot
from requirement_readiness import point_decisions, point_units, readiness_errors, dialogue_links
from state_transaction import publish_batch
from validation_session import operation

FORMAT = 'wewo-qa-authoring/1'
COLLECTIONS = {'sources': 'SRC', 'segments': 'SEG', 'requirement_items': 'REQ', 'objects': 'OBJ',
               'relationships': 'REL', 'flows': 'FLOW', 'rules': 'RULE', 'requirement_units': 'RU',
               'open_questions': 'Q', 'closed_questions': 'Q', 'decisions': 'DEC',
               'source_updates': 'UPD'}
NESTED = {'design_models': 'DM', 'items': 'COV', 'outcomes': 'OUT', 'factors': 'FAC',
          'cases': 'QA-AUTO', 'assertions': 'AS', 'runtime_requirements': 'RT'}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def now():
    return datetime.now(timezone.utc).isoformat()


def fail(text):
    raise ValidationFailure([text])


def upsert(existing, additions):
    result = copy.deepcopy(existing)
    ids = {x['id']: i for i, x in enumerate(result)}
    seen = set()
    for value in additions:
        key = value['id']
        if key in seen: fail('duplicate request id: ' + key)
        seen.add(key)
        if key in ids:
            result[ids[key]] = {**result[ids[key]], **value}
        else:
            ids[key] = len(result)
            result.append(value)
    return result


class Ids:
    def __init__(self, index, context, points=None, manifest=None):
        self.index = copy.deepcopy(index)
        self.used = set(self.index.values())
        def scan(value):
            if isinstance(value, dict):
                if isinstance(value.get('id'), str): self.used.add(value['id'])
                for v in value.values(): scan(v)
            elif isinstance(value, list):
                for v in value: scan(v)
        for value in (context, points, manifest): scan(value)

    def get(self, key, prefix):
        token = prefix + ':' + key
        if key.startswith('@') and any(k.split(':', 1)[1] == key and k != token for k in self.index):
            fail('alias reused across record types: ' + key)
        if token not in self.index:
            n = 1
            while True:
                value = f'Q1.{n}' if prefix == 'Q' else f'{prefix}-{n:03}'
                if value not in self.used: break
                n += 1
            self.index[token] = value
            self.used.add(value)
        return self.index[token]

    def aliases(self, request):
        aliases = {}
        def scan(value, collection=''):
            if isinstance(value, dict):
                ident = value.get('id')
                if isinstance(ident, str) and ident.startswith('@'):
                    prefix = {**COLLECTIONS, **NESTED}.get(collection)
                    if not prefix: fail('alias requires a known record collection: ' + ident)
                    actual = self.get(ident, prefix)
                    if ident in aliases and aliases[ident] != actual: fail('alias reused across record types: ' + ident)
                    aliases[ident] = actual
                for key, child in value.items(): scan(child, key)
            elif isinstance(value, list):
                for child in value: scan(child, collection)
        scan(request)
        for key, value in self.index.items():
            label = key.split(':', 1)[1]
            if label.startswith('@'): aliases.setdefault(label, value)
        def replace(value, field=''):
            reference = field == 'id' or field.endswith(('_refs', '_ref')) or field in {'question_ids', 'unit_id', 'question_id', 'point', 'points', 'in_reply_to', 'answer_to', 'archive_questions', 'from_object', 'to_object'}
            if isinstance(value, str) and value.startswith('@') and reference:
                if value not in aliases: fail('unresolved alias: ' + value)
                return aliases[value]
            if isinstance(value, dict):
                return {(replace(k, 'factor_ref') if field == 'factor_values' else k): replace(v, k)
                        for k, v in value.items()}
            if isinstance(value, list): return [replace(v, field) for v in value]
            return value
        return replace(request)


def locate_excerpt(item, origins):
    result = dict(item)
    quote = result.pop('quote', None)
    occurrence = result.pop('occurrence', None)
    if quote is None: return result
    text = origins.get(result['origin_ref'])
    if text is None: fail('excerpt origin missing: ' + result['origin_ref'])
    if not quote: fail('excerpt quote cannot be empty')
    positions, offset = [], 0
    while (offset := text.find(quote, offset)) >= 0:
        positions.append(offset); offset += 1
    if not positions: fail('literal excerpt not found: ' + result['id'])
    if occurrence is None and len(positions) != 1: fail('ambiguous quote; specify zero-based occurrence: ' + result['id'])
    occurrence = 0 if occurrence is None else occurrence
    if not isinstance(occurrence, int) or not 0 <= occurrence < len(positions): fail('invalid excerpt occurrence')
    result.update(start=positions[occurrence], end=positions[occurrence] + len(quote))
    result.setdefault('statement', quote)
    return result


def synchronize_context(context):
    rules = {r['id']: r for r in context['rules']}
    origins = {s['id']: s['content'] for s in context['segments']}
    origins.update({d['id']: d['resolution'] for d in context['decisions']})
    context['requirement_items'] = [locate_excerpt(i, origins) for i in context['requirement_items']]
    for r in rules.values():
        for key in ('coverage', 'design_models', 'factors', 'requirement_refs', 'segment_refs', 'decision_refs'):
            r.setdefault(key, [])
        # Extraction links are explicitly chosen by the author, not guessed from prose.
        r['requirement_refs'] = [i['id'] for i in context['requirement_items'] if r['id'] in i['rule_refs']]
        for item in context['requirement_items']:
            if r['id'] in item['rule_refs']:
                key = 'segment_refs' if item['origin_ref'].startswith('SEG-') else 'decision_refs'
                if item['origin_ref'] not in r[key]: r[key].append(item['origin_ref'])
        for model in r['design_models']:
            for item in model['items']:
                item.setdefault('test_point_refs', [])
    for unit in context['requirement_units']:
        unit.setdefault('depends_on', [])
        unit.setdefault('rule_refs', [])


def source_view(context):
    fields = {'id', 'title', 'type', 'locator', 'authority', 'version', 'retrieved_at', 'notes', 'sha256', 'role', 'applies_to'}
    return [{k: v for k, v in s.items() if k in fields} for s in context['sources']]


def design_points(context, project, ids, previous=None):
    from artifact_language import ArtifactText, output_language
    text = ArtifactText(output_language({'project': project}))
    nodes, outcome_points = [], {}
    previous_leaves = [p for p in walk_test_points(previous['tree']) if not p['children']] if previous else []
    items = {i['id']: (m['id'], i) for r in context['rules'] for m in r['design_models'] for i in m['items']}
    groups, group_models, emitted, signatures = {}, {}, {}, {}
    # Existing leaf groups take precedence, including intentionally separate old
    # leaves. New methods can join an explicit shared outcome without renumbering.
    for leaf in previous_leaves:
        oid, pid = leaf.get('outcome_ref'), leaf['id']
        models = {items[cid][0] for cid in leaf['coverage_item_refs'] if cid in items
                  and any(o['id'] == oid for o in items[cid][1]['outcomes'])}
        if models:
            groups.setdefault(oid, []).append(pid)
            group_models[pid] = models
    owners = {r['id']: [u['id'] for u in context['requirement_units'] if r['id'] in u['rule_refs']] for r in context['rules']}
    segments = {s['id']: s for s in context['segments']}
    def node(pid, title, kind, units, trace, children=None):
        return {'id': pid, 'title': title, 'kind': kind, 'status': 'confirmed', 'requirement_unit_refs': units,
                'trace_refs': trace, 'children': children or [], 'coverage_item_refs': []}
    for rule in context['rules']:
        if rule['status'] == 'excluded': continue
        trace = sorted({segments[s]['source_id'] + '#' + segments[s]['anchor'] for s in rule['segment_refs']} | set(rule['decision_refs']))
        leaves = []
        for model in rule['design_models']:
            for item in model['items']:
                item['test_point_refs'] = []
                if item['disposition'] != 'required': continue
                for outcome in item['outcomes']:
                    oid = outcome['id']
                    signature = (outcome, item['condition'], item['action'], item['factor_values'])
                    if oid in signatures and signatures[oid] != signature:
                        fail('conflicting planned outcome ' + oid)
                    signatures[oid] = signature
                    old = next((p for p in previous_leaves if item['id'] in p.get('coverage_item_refs', []) and p.get('outcome_ref') == outcome['id']), None)
                    pid = old['id'] if old else next((p for p in groups.get(oid, []) if model['id'] not in group_models[p]), None)
                    if pid is None:
                        pid = ids.get(item['id'] + ':' + oid, 'TP')
                        groups.setdefault(oid, []).append(pid)
                        group_models[pid] = set()
                    group_models[pid].add(model['id'])
                    item['test_point_refs'].append(pid)
                    if pid not in outcome_points.setdefault(oid, []): outcome_points[oid].append(pid)
                    if pid in emitted:
                        leaf = emitted[pid]
                        leaf['coverage_item_refs'].append(item['id'])
                        leaf['rule_refs'] = sorted(set(leaf['rule_refs']) | {rule['id']})
                        leaf['requirement_unit_refs'] = sorted(set(leaf['requirement_unit_refs']) | set(owners[rule['id']]))
                        leaf['trace_refs'] = sorted(set(leaf['trace_refs']) | set(trace))
                        continue
                    pending = outcome.get('status') == 'pending'
                    if not pending and 'expected' not in outcome:
                        fail(outcome['id'] + ': expected outcome not supplied')
                    result = (text('待确认') + ': ' + ', '.join(outcome['question_refs'])
                              if pending else outcome['expected'])
                    title = ' / '.join((item['condition'], item['action'], outcome['subject'], outcome['observable'])) + ' → ' + result
                    leaf = node(pid, title, 'oracle', owners[rule['id']], trace)
                    leaf.update(rule_refs=[rule['id']], coverage_item_refs=[item['id']], outcome_ref=outcome['id'],
                                verification={'condition': item['condition'], 'action': item['action']})
                    if pending:
                        leaf.update(status='pending', question_refs=outcome['question_refs'])
                    else:
                        leaf['verification']['expected'] = outcome['expected']
                    emitted[pid] = leaf
                    leaves.append(leaf)
        for dimension in rule['coverage']:
            dimension['test_point_refs'] = sorted({p for m in rule['design_models'] for i in m['items']
                if dimension['dimension'] in i['dimensions'] for p in i['test_point_refs']})
        if leaves:
            nodes.append(node(ids.get('rule:' + rule['id'], 'TP'), rule['title'], 'rule', owners[rule['id']], trace, leaves))
    root = node('TP-ROOT', project['requirement'], 'root', [], [], nodes)
    result = {'schema_version': '1.6', 'generated_at': now(), 'stage': 'draft', 'project': project,
              'sources': source_view(context), 'decisions': point_decisions(context), 'requirement_units': point_units(context),
              'tree': root, 'design_context_baseline': {'path': 'design-context.json', 'sha256': '0' * 64}, 'design_review': {}}
    return result, outcome_points


def compile_cases(cases, points, outcome_points, ids, defaults=None):
    leaves = {p['id']: p for p in walk_test_points(points['tree']) if not p['children']}
    result = []
    for authored in cases:
        case = {**copy.deepcopy(defaults or {}), **copy.deepcopy(authored)}
        missing = [key for key in ('applicable_targets', 'automation') if key not in case]
        if missing: fail(case['id'] + ': supply explicit case or batch fields: ' + ', '.join(missing))
        assert_map = {}
        for a in case['assertions']:
            ref = a.pop('point', None)
            if ref is not None:
                if ref in outcome_points:
                    if len(outcome_points[ref]) != 1: fail(ref + ': outcome used in multiple scenarios; specify point ID')
                    ref = outcome_points[ref][0]
                if ref not in leaves: fail('unknown assertion point: ' + ref)
                a.setdefault('id', ids.get(case['id'] + ':' + ref, 'AS'))
                a['test_point_refs'] = [ref]
                leaf = leaves[ref]
                a.setdefault('description', leaf['title'])
                a.setdefault('target_ids', case['applicable_targets'])
                if leaf['status'] == 'pending':
                    if 'check' in a: fail(a['id'] + ': pending oracle cannot have an executable check')
                    a.update(status='pending', question_refs=leaf['question_refs'])
                else:
                    expected = leaf['verification']['expected']
                    if 'expected' in a and a['expected'] != expected: fail(a['id'] + ': authored expectation differs from outcome')
                    a['expected'] = expected
            for p in a['test_point_refs']: assert_map[p] = a['id']
        case['test_point_refs'] = sorted(assert_map)
        case['source_refs'] = sorted({s for p in assert_map for s in leaves[p]['trace_refs']})
        for step in case['steps']:
            if 'points' in step:
                refs = []
                for ref in step.pop('points'):
                    pids = outcome_points.get(ref, [ref])
                    if len(pids) != 1 or pids[0] not in assert_map: fail('step must bind its own single authored assertion: ' + ref)
                    refs.append(assert_map[pids[0]])
                step['assertion_refs'] = refs
            step.setdefault('assertion_refs', [])
        # Target dependencies remain attached to the explicitly authored target.
        # Lifting them to the case would apply one target's access/setup to all targets.
        case.setdefault('runtime_requirement_refs', [])
        result.append(case)
    return result


@operation
def apply_request(path, request):
    path = Path(path).resolve()
    if request.get('format') != FORMAT: fail('authoring request format must be ' + FORMAT)
    errors = schema_errors(request, DESIGNER_SCHEMA_ROOT / 'authoring-request.schema.json')
    if errors: raise ValidationFailure(errors)
    allowed = {'format', 'base_sha256', 'project', 'upsert', 'requirement_checks', 'design', 'review', 'archive_questions', 'amendments', 'branch_reviews'}
    if set(request) - allowed: fail('unknown authoring request fields: ' + ', '.join(sorted(set(request) - allowed)))
    digest = hashlib.sha256(encoded(request)).hexdigest()
    receipts_path = path.with_name('authoring-index.json')
    index = load_json(receipts_path) if receipts_path.exists() else {'ids': {}, 'receipts': {}}
    actual = sha256_file(path) if path.exists() else None
    receipt = index['receipts'].get(digest)
    if receipt and actual == receipt['context_sha256']:
        if all((path.parent / name).is_file() and sha256_file(path.parent / name) == value for name, value in receipt['files'].items()):
            return {'status': 'unchanged', 'context_sha256': actual, 'ids': index['ids']}
        fail('replayed request has changed derived artifacts; inspect current state instead of overwriting')
    if request.get('base_sha256') != actual: fail('stale authoring base_sha256; inspect current context before applying')
    if path.exists():
        context = load_json(path)
    else:
        if 'project' not in request: fail('initial request requires project')
        context = {k: [] for k in COLLECTIONS if k not in {'source_updates', 'closed_questions'}}
        context.update(schema_version='1.6', generated_at=now(), project=request['project'],
                       review={'status': 'draft'}, requirement_confirmation={'status': 'draft'},
                       coverage_plan={'status': 'draft'}, requirement_review={'status': 'draft'},
                       dialogue_events=[], branch_reviews=[])
    points_path, manifest_path = path.with_name('test-points.json'), path.with_name('test-manifest.json')
    points = load_json(points_path) if points_path.exists() else None
    manifest = load_json(manifest_path) if manifest_path.exists() else None
    ids = Ids(index['ids'], context, points, manifest)
    request = ids.aliases(copy.deepcopy(request))
    for key, records in request.get('upsert', {}).items():
        if key not in COLLECTIONS: fail('not an authorable collection: ' + key)
        if key == 'segments':
            for record in records:
                cache = record.pop('cache_ref', None)
                cache_id = record.pop('cache_segment_id', record['id'])
                if cache:
                    data = load_json((path.parent / cache).resolve())
                    raw = next((s for s in data['segments'] if s['id'] == cache_id), None)
                    if not raw: fail('unknown cached segment: ' + cache_id)
                    for name in ('source_id', 'anchor', 'kind', 'content'):
                        if name in record and record[name] != raw[name]: fail('cached source differs from authored segment: ' + record['id'])
                        record[name] = raw[name]
        context[key] = upsert(context.get(key, []), records)
    for qid in request.get('archive_questions', []):
        if not any(q['id'] == qid for q in context.get('closed_questions', [])): fail('archive requires an explicit closed question with resolution_refs: ' + qid)
        context['open_questions'] = [q for q in context['open_questions'] if q['id'] != qid]
    if 'amendments' in request:
        if context['requirement_confirmation'].get('status') != 'confirmed': fail('amendments require an existing actual confirmation')
        amendments = {a['ref']: a for a in context['requirement_confirmation'].get('amendments', [])}
        snapshot = business_snapshot(context)
        for amendment in request['amendments']:
            value = dict(amendment)
            value.setdefault('sha256', snapshot.get(value['ref']))
            amendments[value['ref']] = value
        context['requirement_confirmation']['amendments'] = list(amendments.values())
    if 'branch_reviews' in request:
        context['branch_reviews'].extend(request['branch_reviews'])
    synchronize_context(context)
    if 'requirement_checks' in request:
        context['requirement_review'] = {'status': 'ready', 'snapshot_sha256': requirement_digest(context),
                                         'checks': request['requirement_checks']}
    validate_design_context_data(context, final=False)
    files = {}
    design = request.get('design')
    if design:
        stage = design.get('stage', 'draft')
        if stage not in {'draft', 'final'}: fail('invalid design stage')
        errors = readiness_errors(context, confirmed=True, final=stage == 'final')
        if errors: raise ValidationFailure(errors)
        project = design.get('project') or (points or {}).get('project')
        if not project: fail('first design requires full project and explicit targets')
        if any(project.get(k) != context['project'].get(k) for k in ('name', 'artifact_id')): fail('design project does not match context')
        project['output_language'] = context['project'].get('output_language', 'zh-CN')
        points, outcome_points = design_points(context, project, ids, points)
        points['stage'] = stage
        cases = compile_cases(design.get('cases', []), points, outcome_points, ids, design.get('case_defaults'))
        manifest = manifest or {'schema_version': '1.8', 'generated_at': now(), 'stage': 'draft',
            'runtime_requirements': [], 'cases': [], 'review': {'status': 'pending'}}
        manifest.update(project=project, sources=points['sources'], decisions=points['decisions'], stage=stage)
        manifest['cases'] = upsert(manifest['cases'], cases)
        manifest['runtime_requirements'] = upsert(manifest['runtime_requirements'], design.get('runtime_requirements', []))
        points['design_context_baseline']['sha256'] = hashlib.sha256(encoded(context)).hexdigest()
        manifest['test_points_baseline'] = {'path': 'test-points.json', 'sha256': hashlib.sha256(encoded(points)).hexdigest()}
        for value, name in ((points, 'test-points'), (manifest, 'test-manifest')):
            errors = schema_errors(value, DESIGNER_SCHEMA_ROOT / (name + '.schema.json'))
            if errors: raise ValidationFailure(errors)
        # Derivations are checked now. Full tree/case reviews remain explicit later.
        validate_design_context_data(context, final=False)
        validate_test_points_data(points, context, final=False, _authoring=True)
        validate_manifest_data(manifest, points, final=False, _authoring=True)
        files.update({points_path: encoded(points), manifest_path: encoded(manifest)})
    if 'review' in request:
        apply_reviews(context, points, manifest, request['review'])
        if points:
            points['design_context_baseline']['sha256'] = hashlib.sha256(encoded(context)).hexdigest()
            from design_review import point_review_digest, case_review_digest
            if 'points' in request['review']: points['design_review']['snapshot_sha256'] = point_review_digest(points)
            if manifest:
                manifest['test_points_baseline']['sha256'] = hashlib.sha256(encoded(points)).hexdigest()
                if 'cases' in request['review']:
                    lookup = {c['id']: c for c in manifest['cases']}
                    for check in manifest['review']['case_checks']:
                        check['snapshot_sha256'] = case_review_digest(manifest, lookup[check['case_id']])
                files[manifest_path] = encoded(manifest)
            files[points_path] = encoded(points)
        validate_design_context_data(context, final=False)
        if points and 'points' in request['review']:
            validate_test_points_data(points, context, final=False)
        if manifest:
            validate_manifest_data(manifest, points, final=False)
    files[path] = encoded(context)
    index['ids'] = ids.index
    context_sha = hashlib.sha256(files[path]).hexdigest()
    index['receipts'][digest] = {'context_sha256': context_sha,
                               'files': {p.name: hashlib.sha256(b).hexdigest() for p, b in files.items()}}
    files[receipts_path] = encoded(index)
    from validation_session import current
    current().unchanged()
    expected = {str(p): current().files[p][1] if p in current().files else hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None for p in files}
    publish_batch(files, path.parent / 'work' / 'transactions', expected)
    return {'status': 'written; semantic review and delivery gates still required',
            'context_sha256': context_sha, 'ids': ids.index,
            'cases': len(manifest['cases']) if manifest else 0}


def apply_reviews(context, points, manifest, review):
    if 'context' in review:
        # Notes and checked origins must be supplied by the reviewer. Do not fabricate them.
        authored = copy.deepcopy(review['context'])
        from requirement_coverage import source_texts, plan_digest
        origins = source_texts(context)
        for check in authored.get('source_checks', []):
            origin = check['origin_ref']
            if origin not in origins: fail('review refers to unknown origin: ' + origin)
            if not check.get('note', '').strip(): fail('source review requires an actual authored note')
            check['content_sha256'] = hashlib.sha256(origins[origin].encode('utf-8')).hexdigest()
            check.setdefault('requirement_refs', [i['id'] for i in context['requirement_items'] if i['origin_ref'] == origin])
        if authored.get('status') == 'confirmed':
            authored.setdefault('confirmed_at', now())
            authored['plan_sha256'] = plan_digest(context)
        context['review'].update(authored)
    if 'points' in review:
        if not points: fail('no points to review')
        supplied = review['points']
        if set(supplied.get('checked_leaf_refs', [])) != {p['id'] for p in walk_test_points(points['tree']) if not p['children']}:
            fail('point review must explicitly account for every current leaf')
        if not supplied.get('atomicity_note', '').strip() or not supplied.get('visible_path_note', '').strip(): fail('point review needs actual review notes')
        points['design_review'] = dict(supplied)
    if 'cases' in review:
        if not manifest: fail('no cases to review')
        if {c['case_id'] for c in review['cases']} != {c['id'] for c in manifest['cases']}: fail('case review must explicitly account for every case')
        manifest['review']['case_checks'] = copy.deepcopy(review['cases'])
    if 'manifest' in review:
        if not manifest: fail('no manifest to review')
        manifest['review'].update(review['manifest'])


@operation
def record_dialogue(path, request):
    path = Path(path).resolve()
    if request.get('base_sha256') != sha256_file(path): fail('stale dialogue base_sha256')
    context = load_json(path)
    event = copy.deepcopy(request['event'])
    if not event.get('message_ref') or not event.get('text', '').strip(): fail('actual displayed/replied text and message_ref are required')
    if any(e['id'] == event['id'] for e in context['dialogue_events']):
        if next(e for e in context['dialogue_events'] if e['id'] == event['id']) == event:
            return {'status': 'unchanged', 'context_sha256': sha256_file(path)}
        fail('dialogue ID already used; preserve the actual earlier event')
    files = {}
    if event['kind'] == 'summary':
        event['snapshot_sha256'] = requirement_digest(context)
        files[path.parent / 'history' / ('summary-' + hashlib.sha256(event['id'].encode()).hexdigest() + '.json')] = encoded(
            {'snapshot_sha256': event['snapshot_sha256'], 'baseline': business_snapshot(context), 'event': event})
    if event['kind'] == 'question':
        _, asked, _, _ = dialogue_links(context)
        revisits = {q: asked[q] for q in event['question_ids'] if q in asked}
        if revisits: event['revisits'] = revisits
    if event['kind'] == 'confirmation':
        parent = next((e for e in context['dialogue_events'] if e['id'] == event.get('in_reply_to') and e['kind'] == 'summary'), None)
        if not parent: fail('confirmation must refer to an actual displayed summary')
        snapshot_path = path.parent / 'history' / ('summary-' + hashlib.sha256(parent['id'].encode()).hexdigest() + '.json')
        snapshot = load_json(snapshot_path) if snapshot_path.exists() else {'snapshot_sha256': requirement_digest(context), 'baseline': business_snapshot(context)}
        if snapshot['snapshot_sha256'] != parent['snapshot_sha256']: fail('cannot recover displayed business baseline')
        if context['requirement_confirmation'].get('status') == 'confirmed': fail('retain existing confirmation; apply scoped amendments for later answers')
        context['requirement_confirmation'] = {'status': 'confirmed', 'confirmed_at': request.get('recorded_at', now()),
            'response_ref': event['message_ref'], 'response_text': event['text'], 'summary_event_ref': parent['id'],
            'response_event_ref': event['id'], 'snapshot_sha256': snapshot['snapshot_sha256'], 'baseline': snapshot['baseline']}
    context['dialogue_events'].append(event)
    if event['kind'] in {'answer', 'confirmation'} and event.get('question_ids'):
        if 'branch_review' not in request: fail('answered questions require an authored branch review')
        context['branch_reviews'].append({'answer_event_ref': event['id'], **request['branch_review']})
    validate_design_context_data(context, final=False)
    files[path] = encoded(context)
    from validation_session import current
    current().unchanged()
    expected = {str(p): current().files[p][1] if p in current().files else hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None for p in files}
    publish_batch(files, path.parent / 'work' / 'transactions', expected)
    return {'status': 'recorded; unresolved questions are unchanged', 'context_sha256': hashlib.sha256(files[path]).hexdigest()}


def main(mode='apply'):
    parser = argparse.ArgumentParser(description='Apply explicit structured design input; never infer business approvals or review results.')
    parser.add_argument('context', type=Path)
    parser.add_argument('--input', required=True, type=Path)
    args = parser.parse_args()
    result = record_dialogue(args.context, load_json(args.input)) if mode == 'dialogue' else apply_request(args.context, load_json(args.input))
    print(json.dumps(result, ensure_ascii=False))
    return 0


def dialogue_main():
    return main('dialogue')


def inspect_schema(name):
    if name == 'authoring-request':
        return load_json(DESIGNER_SCHEMA_ROOT / 'authoring-request.schema.json')
    schemas = {key: load_json(DESIGNER_SCHEMA_ROOT / (key + '.schema.json'))
               for key in ('design-context', 'test-points', 'test-manifest')}
    inventory = {key: {'definitions': sorted(value.get('$defs', {})),
                       'properties': sorted(value.get('properties', {}))}
                 for key, value in schemas.items()}
    if name == 'list': return inventory
    document, separator, field = name.partition(':')
    if not separator: document, field = None, name
    matches = []
    for key, schema in schemas.items():
        if document and document != key: continue
        for area in ('$defs', 'properties'):
            if field in schema.get(area, {}):
                matches.append({'schema': key, 'definition': schema[area][field]})
                break
    if len(matches) == 1: return matches[0]
    if len(matches) > 1:
        fail('ambiguous schema name; specify ' + ', '.join(m['schema'] + ':' + field for m in matches))
    fail('unknown schema field: ' + name + '; use --schema list for exact definition/property names')


def inspect_main():
    parser = argparse.ArgumentParser(description='Inspect only the current business unit or requested authoring schema; does not perform a review.')
    parser.add_argument('context', type=Path, nargs='?')
    parser.add_argument('--unit')
    parser.add_argument('--schema', help='list, authoring-request, an exact definition/property name, or document:name')
    args = parser.parse_args()
    if args.schema:
        result = inspect_schema(args.schema)
    else:
        if not args.context: fail('context path is required without --schema')
        context = load_json(args.context)
        result = {'context_sha256': sha256_file(args.context), 'project': context['project'],
                  'confirmation': context['requirement_confirmation'].get('status'),
                  'units': [{'id': u['id'], 'title': u['title'], 'depends_on': u['depends_on']} for u in context['requirement_units']],
                  'open_questions': context['open_questions']}
        if args.unit:
            units = {u['id']: u for u in context['requirement_units']}
            if args.unit not in units: fail('unknown requirement unit: ' + args.unit)
            selected, pending = set(), [args.unit]
            while pending:
                uid = pending.pop()
                if uid in selected: continue
                selected.add(uid); pending.extend(units[uid]['depends_on'])
            result['units'] = [u for u in context['requirement_units'] if u['id'] in selected]
            rules = {r for u in result['units'] for r in u['rule_refs']}
            result['rules'] = [r for r in context['rules'] if r['id'] in rules]
            requirements = {i for r in result['rules'] for i in r['requirement_refs']}
            result['requirement_items'] = [i for i in context['requirement_items'] if i['id'] in requirements]
            sources = {s for r in result['rules'] for s in r['segment_refs']}
            result['segments'] = [s for s in context['segments'] if s['id'] in sources]
            result['open_questions'] = [q for q in context['open_questions'] if q['unit_id'] in selected]
        index = args.context.with_name('authoring-index.json')
        if index.exists(): result['ids'] = load_json(index)['ids']
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
