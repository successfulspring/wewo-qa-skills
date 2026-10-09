"""Executor validation commands; checks are shared with native execution."""
import argparse
from pathlib import Path

from artifact_tools import validate_execution_profile_file, validate_results_file


def profile_main():
    parser = argparse.ArgumentParser(description="Validate Wewo QA runtime inputs against a manifest.")
    parser.add_argument("profile", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    profile, _ = validate_execution_profile_file(args.profile.resolve(), args.manifest.resolve())
    resolved = sum(b["status"] == "resolved" for b in profile["bindings"])
    print(f"OK: {args.profile} ({resolved}/{len(profile['bindings'])} runtime requirements resolved)")
    return 0


def results_main():
    parser = argparse.ArgumentParser(description="Validate Wewo QA execution results against a manifest.")
    parser.add_argument("results", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    results, _ = validate_results_file(args.results.resolve(), args.manifest.resolve())
    print(f"OK: {args.results} ({len(results['results'])} case-target results)")
    return 0
