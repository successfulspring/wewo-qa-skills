from __future__ import annotations

"""Render Wewo QA test points as XMind 8 or Zen packages.

The package structure was checked against the open-source XMind tooling listed
in OPEN_SOURCE_FOUNDATIONS.md. This implementation is purpose-built for the
validated Wewo QA test-point contract and uses only the Python standard library.
"""

import argparse
import copy
import hashlib
import io
import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from artifact_tools import validate_test_points_file, write_bytes_atomic
from artifact_language import ArtifactText, DEFAULT_LANGUAGE, output_language


CONTENT_NS = "urn:xmind:xmap:xmlns:content:2.0"
XLINK_NS = "http://www.w3.org/1999/xlink"


def _stable_xmind_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8"), usedforsecurity=False).hexdigest()[:26]


def _generated_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _timestamp_ms(value: str) -> str:
    return str(int(_generated_datetime(value).timestamp() * 1000))


def _topic_title(node: dict[str, Any], language=DEFAULT_LANGUAGE) -> str:
    if node["id"] == "TP-ROOT":
        return node["title"]
    separator = "｜" if language == DEFAULT_LANGUAGE else " | "
    return node["id"] + separator + node["title"]


def _topic_note(node: dict[str, Any], language=DEFAULT_LANGUAGE) -> str:
    tr = ArtifactText(language)
    separator = "：" if language == DEFAULT_LANGUAGE else ": "
    def field(label, value):
        return tr(label) + separator + value
    lines = [field("编号", node["id"]), field("类型", node["kind"]), field("状态", node["status"])]
    for key, label in (("requirement_unit_refs", "需求片段"), ("trace_refs", "追溯")):
        if node[key]:
            lines.append(field(label, ", ".join(node[key])))
    if "automation_candidate" in node:
        lines.append(field("自动化候选", tr("是" if node["automation_candidate"] else "否")))
    if node.get("rationale"):
        lines.append(field("依据", node["rationale"]))
    if node.get("notes"):
        lines.append(node["notes"])
    for key, label in (("rule_refs", "业务规则"), ("coverage_item_refs", "设计覆盖项")):
        if node.get(key):
            lines.append(field(label, ", ".join(node[key])))
    if node.get("outcome_ref"):
        lines.append(field("独立检查结果", node["outcome_ref"]))
    if node.get("verification"):
        lines.extend(field(label, node["verification"][key])
            for key, label in (("condition", "条件"), ("action", "动作"), ("expected", "预期")))
    return "\n".join(lines)


def _zen_topic(node: dict[str, Any], language=DEFAULT_LANGUAGE) -> dict[str, Any]:
    topic: dict[str, Any] = {
        "id": _stable_xmind_id(node["id"]),
        "class": "topic",
        "title": _topic_title(node, language),
        "notes": {"plain": {"content": _topic_note(node, language)}},
        "labels": [node["kind"], node["status"]],
    }
    if node["children"]:
        topic["children"] = {"attached": [_zen_topic(child, language) for child in node["children"]]}
    return topic


def _render_zen(test_points: dict[str, Any]) -> dict[str, bytes]:
    language = output_language(test_points)
    tr = ArtifactText(language)
    project = test_points["project"]
    sheet = {
        "id": _stable_xmind_id(f"sheet:{project['artifact_id']}"),
        "class": "sheet",
        "title": project["requirement"] + " " + tr("测试点"),
        "rootTopic": _zen_topic(test_points["tree"], language),
    }
    content = json.dumps([sheet], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    metadata = json.dumps(
        {"creator": {"name": "Wewo QA Case Designer"}, "dataStructureVersion": "2"},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    manifest = json.dumps(
        {"file-entries": {"content.json": {}, "metadata.json": {}}},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return {"content.json": content, "metadata.json": metadata, "manifest.json": manifest}


def _ctag(name: str) -> str:
    return f"{{{CONTENT_NS}}}{name}"


def _legacy_topic(parent: ET.Element, node: dict[str, Any], timestamp: str, language=DEFAULT_LANGUAGE) -> None:
    topic = ET.SubElement(parent, _ctag("topic"))
    topic.set("id", _stable_xmind_id(node["id"]))
    topic.set("timestamp", timestamp)
    if node["id"] == "TP-ROOT":
        topic.set("structure-class", "org.xmind.ui.logic.right")
    ET.SubElement(topic, _ctag("title")).text = _topic_title(node, language)

    notes = ET.SubElement(topic, _ctag("notes"))
    ET.SubElement(notes, _ctag("plain")).text = _topic_note(node, language)
    labels = ET.SubElement(topic, _ctag("labels"))
    for value in (node["kind"], node["status"]):
        ET.SubElement(labels, _ctag("label")).text = value

    if node["children"]:
        children = ET.SubElement(topic, _ctag("children"))
        attached = ET.SubElement(children, _ctag("topics"))
        attached.set("type", "attached")
        for child in node["children"]:
            _legacy_topic(attached, child, timestamp, language)


def _render_legacy(test_points: dict[str, Any]) -> dict[str, bytes]:
    language = output_language(test_points)
    tr = ArtifactText(language)
    ET.register_namespace("", CONTENT_NS)
    ET.register_namespace("xlink", XLINK_NS)
    timestamp = _timestamp_ms(test_points["generated_at"])
    project = test_points["project"]
    root = ET.Element(_ctag("xmap-content"), {"version": "2.0"})
    sheet = ET.SubElement(
        root,
        _ctag("sheet"),
        {"id": _stable_xmind_id(f"sheet:{project['artifact_id']}"), "timestamp": timestamp},
    )
    _legacy_topic(sheet, test_points["tree"], timestamp, language)
    ET.SubElement(sheet, _ctag("title")).text = project["requirement"] + " " + tr("测试点")
    content = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    generated = _generated_datetime(test_points["generated_at"])
    created = generated.strftime("%Y-%m-%d %H:%M:%S UTC")
    meta = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<meta xmlns="urn:xmind:xmap:xmlns:meta:2.0" version="2.0">'
        '<Author><Name>Wewo QA</Name><Email/><Org>Wewo</Org></Author>'
        f'<Create><Time>{created}</Time></Create>'
        '<Creator><Name>Wewo QA Case Designer</Name><Version>0.2</Version></Creator>'
        '</meta>'
    ).encode("utf-8")
    styles = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<xmap-styles xmlns="urn:xmind:xmap:xmlns:style:2.0" version="2.0">'
        '<automatic-styles/><master-styles/></xmap-styles>'
    ).encode("utf-8")
    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest xmlns="urn:xmind:xmap:xmlns:manifest:1.0">'
        '<file-entry full-path="content.xml" media-type="text/xml"/>'
        '<file-entry full-path="meta.xml" media-type="text/xml"/>'
        '<file-entry full-path="styles.xml" media-type="text/xml"/>'
        '<file-entry full-path="META-INF/" media-type=""/>'
        '<file-entry full-path="META-INF/manifest.xml" media-type="text/xml"/>'
        '</manifest>'
    ).encode("utf-8")
    return {
        "content.xml": content,
        "meta.xml": meta,
        "styles.xml": styles,
        "META-INF/manifest.xml": manifest,
    }


def render_xmind_bytes(test_points: dict[str, Any], output_format: str = "legacy", *, draft: bool = False) -> bytes:
    language = output_language(test_points)
    tr = ArtifactText(language)
    if draft:
        test_points = copy.deepcopy(test_points)
        separator = "｜" if language == DEFAULT_LANGUAGE else " | "
        test_points["tree"]["title"] = tr("草案（待确认）") + separator + test_points["tree"]["title"]
        warning = tr("供评审的草案，尚未成为已确认的用例或执行基线。")
        test_points["tree"]["notes"] = warning + ("\n" + test_points["tree"]["notes"] if test_points["tree"].get("notes") else "")
    files = _render_legacy(test_points) if output_format == "legacy" else _render_zen(test_points)
    generated = _generated_datetime(test_points["generated_at"])
    zip_time = (max(generated.year, 1980), generated.month, generated.day, generated.hour, generated.minute, generated.second)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            info = zipfile.ZipInfo(name, date_time=zip_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, content)
    data = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        expected = "content.xml" if output_format == "legacy" else "content.json"
        if expected not in archive.namelist():
            raise ValueError(f"generated XMind archive is missing {expected}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a validated Wewo QA test-point baseline as XMind.")
    parser.add_argument("test_points", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("legacy", "zen"), default="legacy")
    parser.add_argument("--draft", action="store_true", help="Render an explicitly labeled review draft, without final coverage approval.")
    args = parser.parse_args()
    input_path = args.test_points.resolve()
    from artifact_layout import artifact_root
    output_path = args.output.resolve() if args.output else artifact_root(input_path) / "test-points.xmind"
    test_points = validate_test_points_file(input_path, final=not args.draft)
    if output_path == input_path or output_path == input_path.with_name("design-context.json"):
        raise ValueError("XMind output must not overwrite a design baseline")
    write_bytes_atomic(output_path, render_xmind_bytes(test_points, args.format, draft=args.draft))
    print(f"WROTE: {output_path} ({args.format})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
