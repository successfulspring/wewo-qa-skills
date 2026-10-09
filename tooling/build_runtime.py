from __future__ import annotations

"""Build the self-contained Wewo QA runtime used by installed plugins."""

import argparse
import os
import hashlib
import json
import platform
import sys
import tempfile
from pathlib import Path

import PyInstaller.__main__


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    version = json.loads((repo_root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
    output_dir = args.output_dir.resolve()
    with tempfile.TemporaryDirectory(prefix="wewo-qa-build-") as temporary:
        work_dir = Path(temporary).resolve()
        if not work_dir.is_relative_to(Path(tempfile.gettempdir()).resolve()):
            raise ValueError("build workspace must stay inside the system temporary directory")
        return build(repo_root, output_dir, work_dir, version)


def build(repo_root, output_dir, work_dir, version):
    output_dir.mkdir(parents=True, exist_ok=True)

    runtime_sources = repo_root / "tooling" / "runtime"
    sys.path.insert(0, str(runtime_sources))
    from runtime_contract import contract_digest
    contract_hash = contract_digest(repo_root)
    skill_sources = (
        repo_root / "skills" / "wewo-qa-case-designer" / "scripts",
        repo_root / "skills" / "wewo-qa-case-executor" / "scripts",
    )
    schema_roots = (
        repo_root / "skills" / "wewo-qa-case-designer" / "references" / "schemas",
        repo_root / "skills" / "wewo-qa-case-executor" / "references" / "schemas",
    )

    pyinstaller_args = [
        str(runtime_sources / "wewo_qa_cli.py"),
        "--name",
        "wewo-qa",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--paths",
        os.pathsep.join(str(path) for path in (runtime_sources, *skill_sources)),
        "--distpath",
        str(output_dir),
        "--workpath",
        str(work_dir / "work"),
        "--specpath",
        str(work_dir / "spec"),
    ]
    for schema_root in schema_roots:
        pyinstaller_args.extend(
            ["--add-data", f"{schema_root}{os.pathsep}{schema_root.relative_to(repo_root).as_posix()}"]
        )

    PyInstaller.__main__.run(pyinstaller_args)
    binary = output_dir / ("wewo-qa.exe" if platform.system() == "Windows" else "wewo-qa")
    record = {"version": version, "contract_sha256": contract_hash, "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(), "system": platform.system(), "machine": platform.machine()}
    (output_dir / "runtime.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
