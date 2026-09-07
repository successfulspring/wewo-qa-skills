from __future__ import annotations

import argparse
import sys
from pathlib import Path

from artifact_tools import ValidationFailure, validate_results_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Wewo QA execution results against a manifest.")
    parser.add_argument("results", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        results, _ = validate_results_file(args.results.resolve(), args.manifest.resolve())
    except ValidationFailure as exc:
        for error in exc.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.results} ({len(results['results'])} case-target results)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
