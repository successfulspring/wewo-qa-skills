# Bundled runtime tool

The installed plugin includes a self-contained `wewo-qa` executable. The tester must not be asked to install Python, Node.js, `jsonschema`, or another language runtime.

Resolve the plugin root two directories above `SKILL.md`, identify the host OS and CPU architecture, and select exactly one executable:

- Windows x64: `<plugin-root>/bin/windows-x64/wewo-qa.exe`
- macOS arm64: `<plugin-root>/bin/macos-arm64/wewo-qa`
- macOS x64: `<plugin-root>/bin/macos-x64/wewo-qa`
- Linux x64: `<plugin-root>/bin/linux-x64/wewo-qa`

If the host has no matching bundled executable, report the unsupported OS/architecture. Do not fall back to the Python maintenance sources and do not ask the tester to install a runtime.

Use the selected executable as `<qa-tool>`:

```text
<qa-tool> validate-test-manifest <artifact-dir>/test-manifest.json
<qa-tool> prepare-execution-profile <artifact-dir>/test-manifest.json --suite <suite> --target <target-id> --output <run-dir>/execution-profile.json
<qa-tool> validate-execution-profile <run-dir>/execution-profile.json <artifact-dir>/test-manifest.json
<qa-tool> validate-execution-results <run-dir>/execution-results.json <artifact-dir>/test-manifest.json
<qa-tool> render-execution-report <run-dir>/execution-results.json <artifact-dir>/test-manifest.json --output <run-dir>/test-execution-report.md
```

Repeat `--target` for multiple selected targets. Treat a non-zero exit as a failed artifact gate.
