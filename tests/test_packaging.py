"""Distribution gates: no maintainer leak, complete references, native integrity."""
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tooling"))
from package_plugin import validate_archive
import validate_package


class MarketplaceDistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in validate_package.MARKETPLACES:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / relative).read_bytes())
        self.patch = patch.object(validate_package, "ROOT", self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def set_source(self, relative, source):
        path = self.root / relative
        value = json.loads(path.read_text(encoding="utf8"))
        value["plugins"][0]["source"] = source
        path.write_text(json.dumps(value), encoding="utf8")

    def validate(self):
        errors = []
        validate_package.validate_marketplaces(errors)
        return errors

    def test_each_distribution_accepts_matching_marketplaces(self):
        for url in validate_package.APPROVED_SOURCE_URLS:
            with self.subTest(url=url):
                for relative in validate_package.MARKETPLACES:
                    self.set_source(relative, {"source": "url", "url": url, "ref": "main"})
                self.assertEqual([], self.validate())

    def test_mixed_distribution_sources_are_rejected(self):
        for relative, url in zip(validate_package.MARKETPLACES,
                (validate_package.GITHUB_SOURCE_URL, validate_package.GITLAB_SOURCE_URL)):
            self.set_source(relative, {"source": "url", "url": url, "ref": "main"})
        self.assertEqual(["Claude and Codex marketplaces must reference the same distribution repository"],
                         self.validate())

    def test_unapproved_or_malformed_sources_are_rejected(self):
        relative = validate_package.MARKETPLACES[0]
        for source in ("./", {"source": "github", "repo": "successfulspring/wewo-qa-skills"},
                {"source": "url", "url": "https://example.com/wewo-qa-skills.git", "ref": "main"},
                {"source": "url", "url": {}, "ref": "main"}):
            with self.subTest(source=source):
                self.set_source(relative, source)
                self.assertTrue(self.validate())

    def test_gitlab_source_still_requires_codex_main_ref(self):
        for relative in validate_package.MARKETPLACES:
            self.set_source(relative, {"source": "url", "url": validate_package.GITLAB_SOURCE_URL})
        self.assertTrue(any("Codex source ref must be main" in error for error in self.validate()))


class RuntimeArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "synthetic-distribution.zip"
        payload = b"synthetic packaging fixture; not an executable test"
        self.entries = {
            "README.md": b"[license](LICENSE)", "LICENSE": b"Synthetic fixture",
            "THIRD_PARTY_NOTICES.md": b"Synthetic fixture", "skills/runtime-tool.md": b"Runtime",
            "bin/windows-x64/wewo-qa.exe": payload,
            "bin/windows-x64/runtime.json": json.dumps({"version":"0.2.0","sha256":hashlib.sha256(payload).hexdigest(),"contract_sha256":"0"*64}).encode(),
        }
        for host in ("codex", "claude"):
            self.entries[f".{host}-plugin/plugin.json"] = b'{"version":"0.2.0"}'
        self.entries[".agents/plugins/marketplace.json"] = b"{}"
        self.entries[".claude-plugin/marketplace.json"] = b"{}"
        for skill in ("wewo-qa-case-designer", "wewo-qa-case-executor"):
            self.entries[f"skills/{skill}/SKILL.md"] = b"[runtime](../runtime-tool.md)"

    def validate(self):
        with zipfile.ZipFile(self.path, "w") as archive:
            for name,data in self.entries.items():
                archive.writestr(name,data)
        validate_archive(self.path,"windows-x64",expected_contract="0"*64)

    def test_complete_runtime_links_and_metadata_are_accepted(self):
        self.validate()

    def test_source_cache_and_second_host_cannot_leak_into_installation(self):
        for name in ("tests/test_internal.py","skills/wewo-qa-case-designer/scripts/author.py",".git/config","skills/__pycache__/a.pyc","bin/linux-x64/wewo-qa"):
            with self.subTest(name=name):
                self.entries[name]=b"unwanted"
                with self.assertRaises(ValueError): self.validate()
                self.entries.pop(name)

    def test_omitted_cross_skill_reference_is_rejected(self):
        self.entries["skills/wewo-qa-case-designer/SKILL.md"] = b"[guide](references/absent.md)"
        with self.assertRaisesRegex(ValueError,"missing packaged reference"):
            self.validate()

    def test_changed_binary_cannot_use_old_record(self):
        self.entries["bin/windows-x64/wewo-qa.exe"]=b"changed"
        with self.assertRaisesRegex(ValueError,"binary/version"):
            self.validate()

    def test_archive_cannot_escape_its_installation(self):
        self.entries["../outside.txt"]=b"outside"
        with self.assertRaisesRegex(ValueError,"unsafe archive path"):
            self.validate()


if __name__ == "__main__": unittest.main()
