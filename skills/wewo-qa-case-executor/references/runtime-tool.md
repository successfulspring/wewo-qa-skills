# Bundled runtime tool

Use the self-contained executable under the plugin root (two directories above `SKILL.md`) for this host: `bin/windows-x64/wewo-qa.exe`, `bin/macos-arm64/wewo-qa`, `bin/macos-x64/wewo-qa`, or `bin/linux-x64/wewo-qa`. Testers must not install language runtimes or dependencies.

Run `<qa-tool> --version`; these contracts require `wewo-qa 0.2.0`. A missing/unsupported/different runtime blocks dependent work until the installed plugin is rebuilt/updated. Do not fall back to maintenance sources.

```text
<qa-tool> validate-test-manifest <artifact-dir>/test-manifest.json
<qa-tool> validate-case-workbook <artifact-dir>/test-manifest.json
<qa-tool> prepare-execution-profile <artifact-dir>/test-manifest.json --suite <suite> --target <target-id> --output <run-dir>/execution-profile.json
<qa-tool> validate-execution-profile <run-dir>/execution-profile.json <artifact-dir>/test-manifest.json
<qa-tool> judge-execution-results <run-dir>/execution-results.json <artifact-dir>/test-manifest.json
<qa-tool> validate-execution-results <run-dir>/execution-results.json <artifact-dir>/test-manifest.json
<qa-tool> render-execution-report <run-dir>/execution-results.json <artifact-dir>/test-manifest.json
```

Repeat `--target` for multiple selected targets. A non-zero exit is a failed gate. Excel edits belong to Designer's import/review flow; never execute stale JSON. Reports default to `test-execution-report.xlsx`.

Judging writes `execution-results.judged.json` in the same run, preserving the submitted file. Use the judged path for validation/reporting. The command rejects an existing output; `--output` selects another separate JSON filename in that run. It never creates observations or changes a frozen check.
