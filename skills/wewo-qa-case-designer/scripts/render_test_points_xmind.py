from __future__ import annotations

"""Render Wewo QA test points as XMind 8 or Zen packages.

The package structure was checked against the open-source XMind tooling listed
in OPEN_SOURCE_FOUNDATIONS.md. This implementation is purpose-built for the
validated Wewo QA test-point contract and uses only the Python standard library.
"""

import argparse
import hashlib
import io
import json
import os
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from artifact_tools import validate_test_points_file


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


def _topic_title(node: dict[str, Any]) -> str:
    if node["id"] == "TP-ROOT":
        return node["title"]
    return f"{node['id']}｜{node['title']}"


def _topic_note(node: dict[str, Any]) -> str:
    lines = [
        f"类型：{node['kind']}",
        f"状态：{node['status']}",
    ]
    if node["requirement_unit_refs"]:
        lines.append(f"需求片段：{', '.join(node['requirement_unit_refs'])}")
    if node["trace_refs"]:
        lines.append(f"追溯：{', '.join(node['trace_refs'])}")
    if "automation_candidate" in node:
        lines.append(f"自动化候选：{'是' if node['automation_candidate'] else '否'}")
    if node.get("rationale"):
        lines.append(f"依据：{node['rationale']}")
    if node.get("notes"):
        lines.append(node["notes"])
    return "\n".join(lines)


def _zen_topic(node: dict[str, Any]) -> dict[str, Any]:
    topic: dict[str, Any] = {
        "id": _stable_xmind_id(node["id"]),
        "class": "topic",
        "title": _topic_title(node),
        "notes": {"plain": {"content": _topic_note(node)}},
        "labels": [node["kind"], node["status"]],
    }
    if node["children"]:
        topic["children"] = {"attached": [_zen_topic(child) for child in node["children"]]}
    return topic


def _render_zen(test_points: dict[str, Any]) -> dict[str, bytes]:
    project = test_points["project"]
    sheet = {
        "id": _stable_xmind_id(f"sheet:{project['artifact_id']}"),
        "class": "sheet",
        "title": f"{project['requirement']} 测试点",
        "rootTopic": _zen_topic(test_points["tree"]),
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


def _legacy_topic(parent: ET.Element, node: dict[str, Any], timestamp: str) -> None:
    topic = ET.SubElement(parent, _ctag("topic"))
    topic.set("id", _stable_xmind_id(node["id"]))
    topic.set("timestamp", timestamp)
    if node["id"] == "TP-ROOT":
        topic.set("structure-class", "org.xmind.ui.logic.right")
    ET.SubElement(topic, _ctag("title")).text = _topic_title(node)

    notes = ET.SubElement(topic, _ctag("notes"))
    ET.SubElement(notes, _ctag("plain")).text = _topic_note(node)
    labels = ET.SubElement(topic, _ctag("labels"))
    for value in (node["kind"], node["status"]):
        ET.SubElement(labels, _ctag("label")).text = value

    if node["children"]:
        children = ET.SubElement(topic, _ctag("children"))
        attached = ET.SubElement(children, _ctag("topics"))
        attached.set("type", "attached")
        for child in node["children"]:
            _legacy_topic(attached, child, timestamp)


def _render_legacy(test_points: dict[str, Any]) -> dict[str, bytes]:
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
    _legacy_topic(sheet, test_points["tree"], timestamp)
    ET.SubElement(sheet, _ctag("title")).text = f"{project['requirement']} 测试点"
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


def render_xmind_bytes(test_points: dict[str, Any], output_format: str = "legacy") -> bytes:
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


def _write_bytes_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a validated Wewo QA test-point baseline as XMind.")
    parser.add_argument("test_points", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("legacy", "zen"), default="legacy")
    args = parser.parse_args()
    input_path = args.test_points.resolve()
    output_path = args.output.resolve() if args.output else input_path.with_suffix(".xmind")
    test_points = validate_test_points_file(input_path)
    _write_bytes_atomic(output_path, render_xmind_bytes(test_points, args.format))
    print(f"WROTE: {output_path} ({args.format})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
