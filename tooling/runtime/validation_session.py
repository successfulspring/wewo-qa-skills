"""Operation-local reuse of checks on identical content, never approval caching."""
from __future__ import annotations

import copy
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import hashlib
import json
from pathlib import Path
from time import perf_counter


_CURRENT = ContextVar('qa_validation_session', default=None)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


class Session:
    def __init__(self):
        self.files, self.parsed, self.validators, self.checks = {}, {}, {}, set()
        self.metrics = {'file_reads': 0, 'schema_compiles': 0, 'checks': 0, 'check_hits': 0}
        self.started = perf_counter()
        self.phases = []

    def read(self, path):
        path = Path(path).resolve()
        if path not in self.files:
            data = path.read_bytes()
            self.files[path] = (data, hashlib.sha256(data).hexdigest())
            self.metrics['file_reads'] += 1
        return self.files[path][0]

    def invalidate(self, path):
        path = Path(path).resolve()
        self.files.pop(path, None)
        self.parsed.pop(path, None)

    def unchanged(self):
        from artifact_tools import ValidationFailure
        changed = []
        for path, (_, expected) in self.files.items():
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                changed.append(str(path))
        if changed:
            raise ValidationFailure(['input changed during operation; retry from current files: ' + p for p in changed])

    def report(self):
        return {'elapsed_seconds': round(perf_counter() - self.started, 6),
                'counters': dict(self.metrics), 'phases': self.phases}


def current():
    return _CURRENT.get()


@contextmanager
def session():
    existing = current()
    if existing is not None:
        yield existing
        return
    active = Session()
    token = _CURRENT.set(active)
    try:
        yield active
        active.unchanged()
    finally:
        _CURRENT.reset(token)


def operation(function):
    @wraps(function)
    def run(*args, **kwargs):
        with session():
            return function(*args, **kwargs)
    return run


def checked(function):
    """Only decorate pure checks that raise on failure and return None."""
    @wraps(function)
    def run(*args, **kwargs):
        active = current()
        if active is None:
            return function(*args, **kwargs)
        key = (function.__module__, function.__name__, fingerprint([args, kwargs]))
        if key in active.checks:
            active.metrics['check_hits'] += 1
            return None
        active.metrics['checks'] += 1
        result = function(*args, **kwargs)
        if result is not None:
            raise TypeError('checked functions must return None')
        active.checks.add(key)
        return result
    return run


def read_json(path, parse):
    active = current()
    if active is None:
        return parse(Path(path).read_text(encoding='utf-8'))
    path = Path(path).resolve()
    if path not in active.parsed:
        active.parsed[path] = parse(active.read(path).decode('utf-8'))
    # Callers may author candidates; mutating them must not mutate the snapshot.
    return copy.deepcopy(active.parsed[path])


@contextmanager
def phase(name):
    active = current()
    started = perf_counter()
    success = False
    try:
        yield
        success = True
    finally:
        if active:
            active.phases.append({'phase': name, 'seconds': round(perf_counter() - started, 6),
                                  'status': 'passed' if success else 'failed'})
