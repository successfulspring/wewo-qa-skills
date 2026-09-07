from __future__ import annotations

"""Validate the distributable cross-host Wewo QA plugin package."""

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "wewo-qa-skills"
DISPLAY_NAME = "Wewo QA Skills"
SOURCE_URL = "https://github.com/successfulspring/wewo-qa-skills.git"
EXPECTED_SKILLS = {"wewo-qa-case-designer", "wewo-qa-case-executor"}
MANIFESTS = (
    Path(".codex-plugin/plugin.json"),
    Path(".claude-plugin/plugin.json"),
)
MARKETPLACES = (
    Path(".agents/plugins/marketplace.json"),
    Path(".claude-plugin/marketplace.json"),
)
RUNTIMES = (
    Path("bin/windows-x64/wewo-qa.exe"),
    Path("bin/linux-x64/wewo-qa"),
    Path("bin/macos-arm64/wewo-qa"),
    Path("bin/macos-x64/wewo-qa"),
)
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")
MACHINE_PATH = re.compile(r"(?i)(?:[A-Z]:[\\/](?:Users|AI)[\\/]|/(?:Users|home)/[^\s/]+/)")


def load_json(path: Path, errors: list[str]) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.relative_to(ROOT)}: root must be an object")
        return {}
    return value


def validate_manifests(errors: list[str]) -> None:
    loaded = [load_json(ROOT / path, errors) for path in MANIFESTS]
    versions: set[str] = set()
    for relative, manifest in zip(MANIFESTS, loaded):
        if manifest.get("name") != PLUGIN_NAME:
            errors.append(f"{relative}: name must be {PLUGIN_NAME}")
        version = manifest.get("version")
        if not isinstance(version, str) or not SEMVER.fullmatch(version):
            errors.append(f"{relative}: version must be semantic versioning")
        else:
            versions.add(version)
        if manifest.get("skills") != "./skills/":
            errors.append(f"{relative}: skills must be ./skills/")
    if len(versions) != 1:
        errors.append("Claude and Codex manifest versions must match")
    claude = loaded[1] if len(loaded) > 1 else {}
    if claude.get("displayName") != DISPLAY_NAME:
        errors.append(f"{MANIFESTS[1]}: displayName must be {DISPLAY_NAME}")


def validate_marketplaces(errors: list[str]) -> None:
    for relative in MARKETPLACES:
        marketplace = load_json(ROOT / relative, errors)
        if marketplace.get("name") != PLUGIN_NAME:
            errors.append(f"{relative}: marketplace name must be {PLUGIN_NAME}")
        plugins = marketplace.get("plugins")
        if not isinstance(plugins, list) or len(plugins) != 1:
            errors.append(f"{relative}: must contain exactly one plugin")
            continue
        entry = plugins[0]
        if not isinstance(entry, dict) or entry.get("name") != PLUGIN_NAME:
            errors.append(f"{relative}: plugin entry must be {PLUGIN_NAME}")
            continue
        source = entry.get("source")
        if not isinstance(source, dict) or source.get("source") != "url" or source.get("url") != SOURCE_URL:
            errors.append(f"{relative}: source must reference {SOURCE_URL}")
        if relative == Path(".agents/plugins/marketplace.json"):
            if not isinstance(source, dict) or source.get("ref") != "main":
                errors.append(f"{relative}: Codex source ref must be main")
            policy = entry.get("policy")
            if policy != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}:
                errors.append(f"{relative}: required installation policy is missing")
            if entry.get("category") != "Productivity":
                errors.append(f"{relative}: category must be Productivity")


def parse_frontmatter(path: Path, errors: list[str]) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        errors.append(f"{path.relative_to(ROOT)}: missing frontmatter")
        return {}
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        errors.append(f"{path.relative_to(ROOT)}: unclosed frontmatter")
        return {}
    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip("\"'")
    return metadata


def validate_skills(errors: list[str]) -> None:
    skills_root = ROOT / "skills"
    actual = {path.name for path in skills_root.iterdir() if path.is_dir()}
    if actual != EXPECTED_SKILLS:
        errors.append(f"skills/: expected {sorted(EXPECTED_SKILLS)}, got {sorted(actual)}")
    for skill in sorted(EXPECTED_SKILLS):
        path = skills_root / skill / "SKILL.md"
        if not path.is_file():
            errors.append(f"missing {path.relative_to(ROOT)}")
            continue
        metadata = parse_frontmatter(path, errors)
        if metadata.get("name") != skill:
            errors.append(f"{path.relative_to(ROOT)}: name must match directory")
        if not metadata.get("description"):
            errors.append(f"{path.relative_to(ROOT)}: description is required")

    for path in skills_root.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if MACHINE_PATH.search(text):
            errors.append(f"{path.relative_to(ROOT)}: machine-specific absolute path")
        if re.search(r"(?i)\bpython(?:3)?\b.*(?:scripts|artifact_tools)", text):
            errors.append(f"{path.relative_to(ROOT)}: installed workflow depends on Python")


def validate_links(errors: list[str]) -> None:
    for path in ROOT.rglob("*.md"):
        if any(part.startswith(".") and part not in {"."} for part in path.relative_to(ROOT).parts):
            continue
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            target = unquote(match.group(1).split("#", 1)[0].strip())
            parsed = urlparse(target)
            if not target or parsed.scheme or target.startswith("//") or "<" in target:
                continue
            if not (path.parent / target).exists():
                errors.append(f"{path.relative_to(ROOT)}: missing local link {target}")


def validate_runtimes(errors: list[str]) -> None:
    for relative in RUNTIMES:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing bundled runtime {relative}")
        elif path.stat().st_size < 1_000_000:
            errors.append(f"bundled runtime is unexpectedly small: {relative}")


def main() -> int:
    errors: list[str] = []
    validate_manifests(errors)
    validate_marketplaces(errors)
    validate_skills(errors)
    validate_links(errors)
    validate_runtimes(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: distributable Codex and Claude Code plugin package")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
