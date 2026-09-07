from __future__ import annotations

import argparse
import sys
from pathlib import Path

from artifact_tools import ValidationFailure, validate_test_points_file, walk_test_points


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Wewo QA test-point baseline.")
    parser.add_argument("test_points", type=Path)
    args = parser.parse_args()
    try:
        test_points = validate_test_points_file(args.test_points.resolve())
    except ValidationFailure as exc:
        for error in exc.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    nodes = list(walk_test_points(test_points["tree"]))
    leaves = [node for node in nodes if not node["children"]]
    print(f"OK: {args.test_points} ({len(nodes)} nodes, {len(leaves)} leaf test points)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
