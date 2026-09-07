from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from artifact_tools import (
    ValidationFailure,
    expected_runtime_requirement_ids,
    sha256_file,
    validate_execution_profile_data,
    validate_manifest_file,
    write_text_atomic,
)
import json


def build_profile(
    manifest: dict[str, Any],
    manifest_path: Path,
    output_path: Path,
    suite: str,
    targets: list[str],
) -> dict[str, Any]:
    requirement_ids = expected_runtime_requirement_ids(manifest, suite, targets)
    relative_manifest = Path(os.path.relpath(manifest_path, output_path.parent)).as_posix()
    profile = {
        "schema_version": "1.0",
        "manifest_path": relative_manifest,
        "manifest_sha256": sha256_file(manifest_path),
        "suite": suite,
        "targets": targets,
        "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "bindings": [
            {"requirement_id": requirement_id, "status": "missing"}
            for requirement_id in sorted(requirement_ids)
        ],
    }
    validate_execution_profile_data(profile, manifest, manifest_path)
    return profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a deduplicated Wewo QA execution-input profile.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--suite", required=True, choices=("smoke", "regression", "full"))
    parser.add_argument("--target", action="append", required=True, dest="targets")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    output_path = args.output.resolve()
    try:
        manifest = validate_manifest_file(manifest_path)
        profile = build_profile(manifest, manifest_path, output_path, args.suite, args.targets)
    except ValidationFailure as exc:
        for error in exc.errors:
            print(f"ERROR: {error}")
        return 1

    write_text_atomic(output_path, json.dumps(profile, ensure_ascii=False, indent=2) + "\n")
    print(f"WROTE: {output_path}")
    print(f"MISSING: {len(profile['bindings'])} runtime requirement(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
