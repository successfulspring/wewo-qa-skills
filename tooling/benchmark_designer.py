"""Paired local replay of identical design inputs. Never measures LLM reasoning."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
from time import perf_counter


def snapshot(source, destination):
    state = destination / '.qa-state'
    state.mkdir(parents=True)
    for path in (source / '.qa-state').glob('*.json'):
        shutil.copy2(path, state / path.name)
    history = source / '.qa-state' / 'history'
    if history.exists():
        for path in history.rglob('*'):
            if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
                raise ValueError('benchmark history cannot follow directory links')
            target = state / 'history' / path.relative_to(history)
            if path.is_dir(): target.mkdir(parents=True, exist_ok=True)
            elif path.is_file():
                target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, target)
    for path in source.iterdir():
        if path.suffix in {'.xlsx', '.xmind'}: shutil.copy2(path, destination / path.name)


def commands(repo, root, candidate, native):
    cli = [str(repo / 'bin/windows-x64/wewo-qa.exe')] if native else [sys.executable, '-B', str(repo / 'tooling/runtime/wewo_qa_cli.py')]
    if candidate: return [cli + ['build-deliverables', str(root), '--stage', 'draft']]
    state = root / '.qa-state'
    return [cli + args for args in [
        ['render-test-points-xmind', str(state / 'test-points.json'), '--draft'],
        ['render-case-workbook', str(state / 'test-manifest.json'), '--draft'],
        ['render-clarification-workbook', str(state / 'design-context.json'), '--draft'],
        ['validate-deliverables', str(root), '--draft']]]


def implementation(repo, output, kind, native):
    if native:
        target = output / 'implementations' / kind / 'bin' / 'windows-x64'
        target.mkdir(parents=True)
        source = repo / 'bin' / 'windows-x64'
        record = json.loads((source / 'runtime.json').read_text(encoding='utf-8'))
        raw = (source / 'wewo-qa.exe').read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if record['sha256'] != digest:
            raise ValueError(kind + ': native runtime does not match its build record')
        (target / 'wewo-qa.exe').write_bytes(raw)
        (target / 'runtime.json').write_text(json.dumps(record), encoding='utf-8')
        return target.parents[1], record
    paths = sorted({p for folder in [repo / 'tooling/runtime', repo / 'skills']
                    for p in folder.rglob('*') if p.is_file() and p.suffix in {'.py', '.json'}
                    and '__pycache__' not in p.parts})
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(repo).as_posix().encode('utf-8'))
        digest.update(path.read_bytes())
    return repo, {'source_sha256': digest.hexdigest(), 'files': len(paths)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--artifacts', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--repeat', type=int, default=3)
    p.add_argument('--native', action='store_true')
    args = p.parse_args()
    if args.repeat < 1: p.error('repeat must be positive')
    output = args.output.resolve()
    if any(output.is_relative_to(p.resolve()) for p in (args.baseline, args.candidate, args.artifacts)):
        p.error('benchmark outputs must be outside source repositories and original artifacts')
    output.mkdir(parents=True, exist_ok=False)
    results = []
    env = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'}
    implementations = {kind: implementation(getattr(args, kind).resolve(), output, kind, args.native)
                       for kind in ('baseline', 'candidate')}
    for index in range(args.repeat):
        for kind in (('baseline', 'candidate') if index % 2 == 0 else ('candidate', 'baseline')):
            repo, identity = implementations[kind]
            root = output / f'{index + 1}-{kind}'
            snapshot(args.artifacts.resolve(), root)
            before = {n: hashlib.sha256((root / '.qa-state' / n).read_bytes()).hexdigest()
                      for n in ('design-context.json', 'test-points.json', 'test-manifest.json')}
            started = perf_counter(); steps = []
            for i, command in enumerate(commands(repo, root, kind == 'candidate', args.native)):
                tick = perf_counter()
                result = subprocess.run(command, env=env, capture_output=True, text=True, encoding='utf-8')
                (root / '.qa-state' / f'benchmark-{i}.log').write_text(result.stdout + result.stderr, encoding='utf-8')
                steps.append({'command': command[1:] if args.native else command[3:], 'seconds': perf_counter() - tick,
                              'exit_code': result.returncode})
                if result.returncode: raise RuntimeError(f'{kind} failed; inspect {root}')
            elapsed = perf_counter() - started
            after = {n: hashlib.sha256((root / '.qa-state' / n).read_bytes()).hexdigest() for n in before}
            if before != after: raise RuntimeError('benchmark changed business/case baselines')
            if not args.native and implementation(repo, output, kind, False)[1] != identity:
                raise RuntimeError('benchmark implementation changed during measurement')
            row = {'run': index + 1, 'kind': kind, 'seconds': elapsed, 'steps': steps, 'baselines_unchanged': True}
            results.append(row)
            (output / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
            print(json.dumps(row), flush=True)
    medians = {k: statistics.median(r['seconds'] for r in results if r['kind'] == k) for k in ('baseline', 'candidate')}
    summary = {'measurement': 'fixed-input native tools' if args.native else 'fixed-input source tools',
               'not_measured': 'LLM reading, reasoning, authoring and semantic review', 'repeat': args.repeat,
               'implementations': {k: v[1] for k, v in implementations.items()},
               'median_seconds': medians, 'reduction_percent': 100 * (1 - medians['candidate'] / medians['baseline'])}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__': main()
