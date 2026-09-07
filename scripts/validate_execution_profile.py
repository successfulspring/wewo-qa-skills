from __future__ import annotations

import argparse
import sys
from pathlib import Path

from artifact_tools import ValidationFailure, validate_execution_profile_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Wewo QA runtime inputs against a manifest.")
    parser.add_argument("profile", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        profile, _ = validate_execution_profile_file(args.profile.resolve(), args.manifest.resolve())
    except ValidationFailure as exc:
        for error in exc.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    resolved = sum(binding["status"] == "resolved" for binding in profile["bindings"])
    print(f"OK: {args.profile} ({resolved}/{len(profile['bindings'])} runtime requirements resolved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
