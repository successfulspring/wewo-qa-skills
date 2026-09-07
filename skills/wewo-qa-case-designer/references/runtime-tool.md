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
<qa-tool> validate-test-points <artifact-dir>/test-points.json
<qa-tool> render-test-points-xmind <artifact-dir>/test-points.json --output <artifact-dir>/test-points.xmind
<qa-tool> validate-test-manifest <artifact-dir>/test-manifest.json
<qa-tool> render-case-docs <artifact-dir>/test-manifest.json --output-dir <artifact-dir>
```

Treat a non-zero exit as a failed artifact gate. Fix the canonical JSON and rerun the command; never hand-edit rendered files.
