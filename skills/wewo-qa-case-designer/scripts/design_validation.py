"""Designer validation commands; checks are shared with artifact operations."""
import argparse
from pathlib import Path

from artifact_tools import validate_manifest_file, validate_test_points_file, walk_test_points


def points_main():
    parser = argparse.ArgumentParser(description="Validate a Wewo QA test-point baseline.")
    parser.add_argument("test_points", type=Path)
    parser.add_argument("--draft", action="store_true")
    args = parser.parse_args()
    points = validate_test_points_file(args.test_points.resolve(), final=not args.draft)
    nodes = list(walk_test_points(points["tree"]))
    print(f"OK: {args.test_points} ({len(nodes)} nodes, {sum(not n['children'] for n in nodes)} leaf test points)")
    return 0


def manifest_main():
    parser = argparse.ArgumentParser(description="Validate a Wewo QA test manifest.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--draft", action="store_true", help="Check a candidate before completed case review.")
    args = parser.parse_args()
    manifest = validate_manifest_file(args.manifest.resolve(), final=not args.draft)
    print(f"OK: {args.manifest} ({len(manifest['cases'])} cases)")
    return 0
