"""Identify executable contracts even when a maintainer retains a version number."""
import hashlib
from pathlib import Path

def contract_digest(root: Path):
    paths = set((root/"tooling/runtime").glob("*.py"))
    for skill in (root/"skills").iterdir():
        paths.update((skill/"scripts").glob("*.py"))
        paths.update((skill/"references/schemas").glob("*.json"))
    paths.add(root/"tooling/requirements-dev.txt")
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode()+b"\0")
        digest.update(path.read_bytes().replace(b"\r\n",b"\n")+b"\0")
    return digest.hexdigest()
