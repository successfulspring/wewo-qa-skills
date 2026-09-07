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

    PyInstaller.__main__.run(
        [
            str(repo_root / "scripts" / "wewo_qa_cli.py"),
            "--name",
            "wewo-qa",
            "--onefile",
            "--clean",
            "--noconfirm",
            "--paths",
            str(repo_root / "scripts"),
            "--add-data",
            f"{repo_root / 'schemas'}{os.pathsep}schemas",
            "--distpath",
            str(output_dir),
            "--workpath",
            str(work_dir / "work"),
            "--specpath",
            str(work_dir / "spec"),
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
