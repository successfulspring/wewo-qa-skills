"""Replace one reviewed batch, retaining recoverable originals on interruption."""
from __future__ import annotations

import json
from pathlib import Path
import uuid

from artifact_tools import ValidationFailure, sha256_file, write_bytes_atomic
from validation_session import current


def publish_batch(files, journal_root, expected=None):
    files = {Path(p).resolve(): b for p, b in files.items()}
    journal_root = Path(journal_root).resolve()
    journal = journal_root / ('batch-' + uuid.uuid4().hex)
    journal.mkdir(parents=True)
    originals = {}
    for index, path in enumerate(files):
        if expected is not None:
            want = expected.get(str(path))
            actual = __import__('hashlib').sha256(path.read_bytes()).hexdigest() if path.exists() else None
            if actual != want:
                raise ValidationFailure(['changed before replacement: ' + str(path)])
        originals[path] = path.read_bytes() if path.exists() else None
        if originals[path] is not None:
            (journal / f'{index}.before').write_bytes(originals[path])
    record = {'status': 'prepared', 'files': [
        {'path': str(p), 'backup': f'{i}.before' if originals[p] is not None else None}
        for i, p in enumerate(files)]}
    metadata = journal / 'transaction.json'
    metadata.write_text(json.dumps(record, indent=2), encoding='utf-8')
    changed = []
    try:
        for path, content in files.items():
            # Recheck the particular destination immediately before replacing it.
            if (path.read_bytes() if path.exists() else None) != originals[path]:
                raise ValidationFailure(['edited during replacement: ' + str(path)])
            write_bytes_atomic(path, content)
            changed.append(path)
    except Exception:
        for path in reversed(changed):
            if path.read_bytes() != files[path]:
                continue  # Preserve a concurrent human edit, keep its backup journal.
            if originals[path] is None:
                path.unlink()
                if current(): current().invalidate(path)
            else:
                write_bytes_atomic(path, originals[path])
        record['status'] = 'failed; inspect originals before retry'
        metadata.write_text(json.dumps(record, indent=2), encoding='utf-8')
        raise
    record['status'] = 'complete'
    metadata.write_text(json.dumps(record, indent=2), encoding='utf-8')
    return journal
