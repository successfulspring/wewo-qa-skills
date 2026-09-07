from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [
    str(ROOT / "tooling" / "runtime"),
    str(ROOT / "skills" / "wewo-qa-case-designer" / "scripts"),
    str(ROOT / "skills" / "wewo-qa-case-executor" / "scripts"),
]

from artifact_tools import (  # noqa: E402
    ValidationFailure,
    expected_runtime_requirement_ids,
    load_json,
    sha256_file,
    validate_execution_profile_data,
    validate_manifest_data,
    validate_manifest_file,
    validate_results_data,
    validate_results_file,
    validate_test_points_data,
    walk_test_points,
)
from render_case_docs import render_suite  # noqa: E402
from render_execution_report import render_report  # noqa: E402
from render_test_points_xmind import render_xmind_bytes  # noqa: E402


FIXTURE = ROOT / "tests" / "fixtures" / "valid-test-manifest.json"
TEST_POINTS_FIXTURE = ROOT / "tests" / "fixtures" / "valid-test-points.json"


def resolved_profile(manifest: dict, manifest_path: Path, suite: str, targets: list[str]) -> dict:
    requirements = {item["id"]: item for item in manifest["runtime_requirements"]}
    bindings = []
    for requirement_id in sorted(expected_runtime_requirement_ids(manifest, suite, targets)):
        requirement = requirements[requirement_id]
        if requirement["sensitive"]:
            bindings.append(
                {
                    "requirement_id": requirement_id,
                    "status": "resolved",
                    "source": "authenticated-session",
                    "session_ref": "current-authorized-session"
                }
            )
        else:
            bindings.append(
                {
                    "requirement_id": requirement_id,
                    "status": "resolved",
                    "source": requirement["collection"],
                    "value": f"resolved:{requirement_id}"
                }
            )
    return {
        "schema_version": "1.0",
        "manifest_path": "../../test-manifest.json",
        "manifest_sha256": sha256_file(manifest_path),
        "suite": suite,
        "targets": targets,
        "collected_at": "2026-09-04T09:59:00+08:00",
        "bindings": bindings
    }


class ArtifactToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_json(FIXTURE)
        self.test_points = load_json(TEST_POINTS_FIXTURE)

    def test_valid_manifest_and_nested_rendering(self) -> None:
        validate_test_points_data(self.test_points)
        validate_manifest_data(self.manifest, self.test_points)
        smoke = render_suite(self.manifest, "smoke")
        regression = render_suite(self.manifest, "regression")
        full = render_suite(self.manifest, "full")
        self.assertIn("QA-LOGIN-001", smoke)
        self.assertNotIn("QA-LOGIN-002", smoke)
        self.assertIn("QA-LOGIN-002", regression)
        self.assertNotIn("QA-LOGIN-003", regression)
        self.assertIn("QA-LOGIN-003", full)
        self.assertIn("TP-LOGIN-SUCCESS", smoke)

    def test_test_point_rendering_supports_legacy_and_zen(self) -> None:
        expected_titles = {node["title"] for node in walk_test_points(self.test_points["tree"])}
        legacy = render_xmind_bytes(self.test_points, "legacy")
        with zipfile.ZipFile(BytesIO(legacy)) as archive:
            self.assertIn("content.xml", archive.namelist())
            content = archive.read("content.xml").decode("utf-8")
            for title in expected_titles:
                self.assertIn(title, content)
        zen = render_xmind_bytes(self.test_points, "zen")
        with zipfile.ZipFile(BytesIO(zen)) as archive:
            self.assertIn("content.json", archive.namelist())
            content = archive.read("content.json").decode("utf-8")
            for title in expected_titles:
                self.assertIn(title, content)

    def test_uncovered_leaf_test_point_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.manifest)
        invalid["cases"] = invalid["cases"][:-1]
        with self.assertRaisesRegex(ValidationFailure, "leaf test point is not covered"):
            validate_manifest_data(invalid, self.test_points)

    def test_case_cannot_reference_grouping_test_point(self) -> None:
        invalid = copy.deepcopy(self.manifest)
        invalid["cases"][0]["test_point_refs"] = ["TP-LOGIN"]
        with self.assertRaisesRegex(ValidationFailure, "unknown or non-leaf"):
            validate_manifest_data(invalid, self.test_points)

    def test_manifest_file_is_bound_to_adjacent_test_point_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact_dir = Path(directory)
            test_points_path = artifact_dir / "test-points.json"
            manifest_path = artifact_dir / "test-manifest.json"
            test_points_path.write_text(
                json.dumps(self.test_points, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            manifest = copy.deepcopy(self.manifest)
            manifest["test_points_baseline"]["sha256"] = sha256_file(test_points_path)
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            validate_manifest_file(manifest_path)
            test_points_path.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValidationFailure, "sha256 does not match"):
                validate_manifest_file(manifest_path)

    def test_smoke_without_regression_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.manifest)
        invalid["cases"][0]["suite_membership"] = ["smoke", "full"]
        with self.assertRaisesRegex(ValidationFailure, "smoke membership requires regression"):
            validate_manifest_data(invalid, self.test_points)

    def test_unknown_runtime_requirement_reference_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.manifest)
        invalid["cases"][0]["runtime_requirement_refs"].append("RT-UNKNOWN")
        with self.assertRaisesRegex(ValidationFailure, "unknown runtime requirement"):
            validate_manifest_data(invalid, self.test_points)

    def test_execution_profile_aggregates_only_selected_automatic_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "test-manifest.json"
            manifest_path.write_text(json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")
            expected = expected_runtime_requirement_ids(self.manifest, "smoke", ["web-chrome"])
            self.assertEqual(
                expected,
                {"RT-ENV-BASE-URL", "RT-ACCOUNT-MEMBER", "RT-CREDENTIAL-MEMBER"},
            )
            profile = resolved_profile(self.manifest, manifest_path, "smoke", ["web-chrome"])
            validate_execution_profile_data(profile, self.manifest, manifest_path)

    def test_execution_profile_rejects_plaintext_sensitive_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "test-manifest.json"
            manifest_path.write_text(json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")
            profile = resolved_profile(self.manifest, manifest_path, "smoke", ["web-chrome"])
            credential = next(
                item for item in profile["bindings"] if item["requirement_id"] == "RT-CREDENTIAL-MEMBER"
            )
            credential.pop("session_ref")
            credential["source"] = "user-input"
            credential["value"] = "plaintext-password"
            with self.assertRaisesRegex(ValidationFailure, "sensitive value must not be stored"):
                validate_execution_profile_data(profile, self.manifest, manifest_path)

    def test_complete_results_validate_and_render(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact_dir = Path(directory)
            test_points_path = artifact_dir / "test-points.json"
            test_points_path.write_text(
                json.dumps(self.test_points, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            manifest = copy.deepcopy(self.manifest)
            manifest["test_points_baseline"]["sha256"] = sha256_file(test_points_path)
            manifest_path = artifact_dir / "test-manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            run_dir = artifact_dir / "runs" / "run-20260904-001"
            run_dir.mkdir(parents=True)
            profile = resolved_profile(manifest, manifest_path, "smoke", ["web-chrome", "ios-app"])
            profile_path = run_dir / "execution-profile.json"
            profile_path.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
            evidence_dir = run_dir / "evidence"
            evidence_dir.mkdir()
            (evidence_dir / "web.png").write_bytes(b"png")
            (evidence_dir / "web.md").write_text("snapshot", encoding="utf-8")
            results = {
                "schema_version": "1.1",
                "run": {
                    "run_id": "run-20260904-001",
                    "manifest_path": "../../test-manifest.json",
                    "manifest_sha256": sha256_file(manifest_path),
                    "execution_profile_path": "execution-profile.json",
                    "execution_profile_sha256": sha256_file(profile_path),
                    "suite": "smoke",
                    "targets": ["web-chrome", "ios-app"],
                    "environment": {"name": "QA", "kind": "test", "build": "1.0.0"},
                    "started_at": "2026-09-04T10:00:00+08:00",
                    "finished_at": "2026-09-04T10:05:00+08:00"
                },
                "results": [
                    {
                        "case_id": "QA-LOGIN-001",
                        "target_id": "web-chrome",
                        "status": "passed",
                        "attempts": 1,
                        "tool": "Playwright",
                        "assertions": [
                            {
                                "description": "会员首页展示昵称",
                                "expected": "显示测试会员昵称",
                                "actual": "显示测试会员昵称",
                                "passed": True
                            }
                        ],
                        "evidence": [
                            {"type": "screenshot", "path": "evidence/web.png", "description": "登录后页面"},
                            {"type": "accessibility-snapshot", "path": "evidence/web.md", "description": "登录后结构化页面状态"}
                        ],
                        "observed": "登录成功并进入会员首页"
                    },
                    {
                        "case_id": "QA-LOGIN-001",
                        "target_id": "ios-app",
                        "status": "blocked",
                        "attempts": 0,
                        "tool": "",
                        "assertions": [],
                        "evidence": [],
                        "observed": "",
                        "blocker": "未连接授权的 iOS 真机"
                    }
                ]
            }
            validate_results_data(results, manifest, manifest_path, run_dir, profile)
            results_path = run_dir / "execution-results.json"
            results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            validate_results_file(results_path, manifest_path)
            report = render_report(results, manifest)
            self.assertIn("INCOMPLETE", report)
            self.assertIn("未连接授权的 iOS 真机", report)

    def test_pass_without_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            manifest_path = run_dir / "test-manifest.json"
            manifest_path.write_text(json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")
            profile = resolved_profile(self.manifest, manifest_path, "smoke", ["web-chrome"])
            profile_path = run_dir / "execution-profile.json"
            profile_path.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
            results = {
                "schema_version": "1.1",
                "run": {
                    "run_id": "run-invalid",
                    "manifest_path": "test-manifest.json",
                    "manifest_sha256": sha256_file(manifest_path),
                    "execution_profile_path": "execution-profile.json",
                    "execution_profile_sha256": sha256_file(profile_path),
                    "suite": "smoke",
                    "targets": ["web-chrome"],
                    "environment": {"name": "QA", "kind": "test", "build": "1.0.0"},
                    "started_at": "2026-09-04T10:00:00+08:00",
                    "finished_at": "2026-09-04T10:01:00+08:00"
                },
                "results": [
                    {
                        "case_id": "QA-LOGIN-001",
                        "target_id": "web-chrome",
                        "status": "passed",
                        "attempts": 1,
                        "tool": "Playwright",
                        "assertions": [{"description": "首页", "expected": "可见", "actual": "可见", "passed": True}],
                        "evidence": [],
                        "observed": "可见"
                    }
                ]
            }
            with self.assertRaisesRegex(ValidationFailure, "passed result requires evidence"):
                validate_results_data(results, self.manifest, manifest_path, run_dir, profile)


if __name__ == "__main__":
    unittest.main()
