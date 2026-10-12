# Shared artifact runtime

Both QA Skills use one self-contained executable. Resolve the plugin root two directories above either `SKILL.md`, then choose the current host:

| Host | Executable relative to plugin root |
| --- | --- |
| Windows x64 | `bin/windows-x64/wewo-qa.exe` |
| Linux x64 | `bin/linux-x64/wewo-qa` |
| macOS arm64 | `bin/macos-arm64/wewo-qa` |
| macOS x64 | `bin/macos-x64/wewo-qa` |

Per-host distributions contain only the selected host's executable. Artifact operations need no tester-installed language runtime or dependencies. Actual acceptance tests reuse suitable existing or agent-managed test runtimes; resolve missing execution infrastructure during preflight.

Run `<qa-tool> --version` and `--help`. Current contracts require `wewo-qa 0.4.0` and the commands `validate-requirement-readiness`, `design-review-digest`, `requirement-digest`, `freeze-coverage-plan`, `validate-deliverables`, `run-native-tests` and `summarize-execution`. A missing, unsupported or stale binary requires updating/rebuilding the plugin. A matching version alone does not prove command compatibility. Never fall back to maintainer source modules or bypass a failed gate.

Use `<qa-tool>` for the commands in the relevant Skill's artifact/execution references. A non-zero exit is a failed operation: preserve drafts/edits/evidence, resolve the cause, and rerun as needed. Generation helpers and internal state belong under `.qa-state`, not among tester deliverables.
