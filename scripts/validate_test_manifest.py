from __future__ import annotations

import argparse
import sys
from pathlib import Path

from artifact_tools import ValidationFailure, validate_manifest_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Wewo QA test manifest.")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        manifest = validate_manifest_file(args.manifest.resolve())
    except ValidationFailure as exc:
        for error in exc.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.manifest} ({len(manifest['cases'])} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
