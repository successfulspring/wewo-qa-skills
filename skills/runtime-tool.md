# Shared artifact runtime

Both QA Skills use one self-contained executable. Resolve the plugin root two directories above either `SKILL.md`, then choose the current host:

| Host | Executable relative to plugin root |
| --- | --- |
| Windows x64 | `bin/windows-x64/wewo-qa.exe` |
| Linux x64 | `bin/linux-x64/wewo-qa` |
| macOS arm64 | `bin/macos-arm64/wewo-qa` |
| macOS x64 | `bin/macos-x64/wewo-qa` |

Per-host distributions contain only the selected host's executable. Artifact operations need no tester-installed language runtime or dependencies. Actual project tests reuse the project's established or agent-managed test runtime; resolve missing execution infrastructure during preflight.

Run `<qa-tool> --version` and `--help`. Current contracts require `wewo-qa 0.2.0` and the commands `requirement-digest`, `validate-deliverables` and `run-native-tests`. A missing, unsupported or stale binary requires updating/rebuilding the plugin. A matching version alone does not prove command compatibility. Never fall back to maintainer source modules or bypass a failed gate.

Use `<qa-tool>` for the commands in the relevant Skill's artifact/execution references. A non-zero exit is a failed operation: preserve drafts/edits/evidence, resolve the cause, and rerun as needed. Generation helpers and internal state belong under `.qa-state`, not among tester deliverables.
