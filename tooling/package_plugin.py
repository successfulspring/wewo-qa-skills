"""Build a per-host plugin archive from the canonical Skill tree."""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import sys
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

from validate_package import (ROOT, EXPECTED_SKILLS, MANIFESTS, MARKETPLACES,
    MARKDOWN_LINK, validate_manifests, validate_marketplaces, validate_skills, validate_links)

HOSTS = ("windows-x64", "linux-x64", "macos-arm64", "macos-x64")


def validate_archive(path, target, *, expected_contract=None):
    """Reject maintenance leaks, broken references and mismatched native files."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate archive entries")
        for name in names:
            parts = PurePosixPath(name).parts
            if "\\" in name or name.startswith("/") or ".." in parts:
                raise ValueError("unsafe archive path: " + name)
            if parts[0] not in {"skills", "bin", ".agents", ".codex-plugin", ".claude-plugin", "README.md", "LICENSE", "THIRD_PARTY_NOTICES.md"}:
                raise ValueError("unapproved root content in runtime archive: " + name)
            if name.startswith(("tooling/", "tests/", "docs/", ".git/", ".github/", ".codex/")) or any(p in {"scripts", "__pycache__"} or p.startswith(".tmp-") for p in parts) or name.endswith((".py", ".pyc")):
                raise ValueError("maintenance content in runtime archive: " + name)
        binary = f"bin/{target}/wewo-qa" + (".exe" if target == "windows-x64" else "")
        runtime_names = {binary, f"bin/{target}/runtime.json"}
        if {n for n in names if n.startswith("bin/")} != runtime_names:
            raise ValueError("archive must contain exactly one host runtime and its record")
        required = {p.as_posix() for p in (*MANIFESTS, *MARKETPLACES)} | {
            "README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "skills/runtime-tool.md",
            *(f"skills/{skill}/SKILL.md" for skill in EXPECTED_SKILLS),
        }
        if not required <= set(names):
            raise ValueError("runtime archive is missing required plugin resources")
        versions = {json.loads(archive.read(p.as_posix()))["version"] for p in MANIFESTS}
        record = json.loads(archive.read(f"bin/{target}/runtime.json"))
        if versions != {record["version"]} or hashlib.sha256(archive.read(binary)).hexdigest() != record["sha256"]:
            raise ValueError("native binary/version does not match archive record")
        if expected_contract is not None and record.get("contract_sha256") != expected_contract:
            raise ValueError("runtime archive belongs to a stale source contract")
        for name in names:
            if not name.endswith(".md"):
                continue
            for match in MARKDOWN_LINK.finditer(archive.read(name).decode("utf8")):
                link = unquote(match.group(1).split("#", 1)[0].strip())
                if not link or urlparse(link).scheme or link.startswith("//") or "<" in link:
                    continue
                referenced = posixpath.normpath(posixpath.join(posixpath.dirname(name), link))
                if referenced not in names:
                    raise ValueError(f"{name}: missing packaged reference {link}")


def build_package(target, output):
    if target not in HOSTS:
        raise ValueError("unsupported host target")
    output = output.resolve()
    if output.suffix != ".zip" or output.exists():
        raise ValueError("choose a new .zip output; existing files are not overwritten")
    if output.is_relative_to(ROOT):
        raise ValueError("distribution archives belong outside the source repository")
    errors = []
    for validate in (validate_manifests, validate_marketplaces, validate_skills, validate_links):
        validate(errors)
    if errors:
        raise ValueError("\n".join(errors))
    sys.path.insert(0, str(ROOT / "tooling/runtime"))
    from runtime_contract import contract_digest
    contract = contract_digest(ROOT)
    version = json.loads((ROOT / MANIFESTS[0]).read_text(encoding="utf8"))["version"]
    binary = ROOT / "bin" / target / ("wewo-qa.exe" if target == "windows-x64" else "wewo-qa")
    record_path = binary.with_name("runtime.json")
    record = json.loads(record_path.read_text(encoding="utf8"))
    if record.get("version") != version or record.get("contract_sha256") != contract or record.get("sha256") != hashlib.sha256(binary.read_bytes()).hexdigest():
        raise ValueError("rebuild and smoke the selected host runtime before packaging")
    paths = [ROOT / p for p in (*MANIFESTS, *MARKETPLACES)]
    paths += [ROOT / n for n in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md")]
    paths += [p for p in (ROOT / "skills").rglob("*") if p.is_file() and not any(part in {"scripts", "__pycache__"} for part in p.relative_to(ROOT).parts)]
    paths += [binary, record_path]
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(paths):
            name = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            if name == "README.md":
                data = data.decode("utf8").split("## 维护仓库", 1)[0].rstrip().encode("utf8") + b"\n"
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (0o100755 if path == binary else 0o100644) << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data)
    validate_archive(output, target, expected_contract=contract)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=HOSTS)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        path = build_package(args.target, args.output)
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    print(f"WROTE: {path} (runtime-only {args.target})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
