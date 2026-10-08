# Bundled runtime tool

The plugin includes a self-contained executable; testers must not install Python, Node.js or package dependencies. Resolve the plugin root two directories above `SKILL.md` and select the current host:

- Windows x64: `<plugin-root>/bin/windows-x64/wewo-qa.exe`
- macOS arm64: `<plugin-root>/bin/macos-arm64/wewo-qa`
- macOS x64: `<plugin-root>/bin/macos-x64/wewo-qa`
- Linux x64: `<plugin-root>/bin/linux-x64/wewo-qa`

Run `<qa-tool> --version`; these contracts require `wewo-qa 0.2.0`. If the executable is missing, unsupported or a different version, report that the installed plugin runtime needs rebuilding/updating. Do not use maintenance source modules as a fallback or ask testers to install dependencies.

Use the selected executable as `<qa-tool>` in [artifact contract](artifact-contract.md) and [source intake](source-intake.md). `--help` lists extraction, design-context validation, points validation/rendering, manifest validation, Excel rendering/import/validation, profile preparation/validation and result validation/reporting. A non-zero exit is a failed gate: fix the structured artifact and rerun; never bypass a review or discard workbook edits.
