from __future__ import annotations

"""Build the self-contained Wewo QA runtime used by installed plugins."""

import argparse
import os
from pathlib import Path

import PyInstaller.__main__


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    output_dir = args.output_dir.resolve()
    work_dir = repo_root / ".tmp-pyinstaller"
    output_dir.mkdir(parents=True, exist_ok=True)

    runtime_sources = repo_root / "tooling" / "runtime"
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
