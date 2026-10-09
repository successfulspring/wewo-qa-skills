# Repository maintenance

- Keep `skills/` as the single canonical Skill tree for every host.
- Keep shared runtime instructions in `skills/runtime-tool.md`; keep essential maintainer instructions in `README.md` and generated build/package work outside the repository.
- Keep Case Designer limited to requirement clarification and tester-facing case design; it does not inspect product source. Case Executor reads the actual repository and generates/runs durable acceptance automation from reviewed cases.
- Preserve the reviewed cases' business evidence: UI or interface-defined acceptance tests and relevant setup/checks. Do not substitute mocked/unit-only checks for end-to-end acceptance, add unrelated developer test scope, or change production implementation.
- Do not hardcode Web, mobile, desktop, iOS, Android, or a page-based interface as a universal project target.
- Bundled artifact tooling must not require tester-installed language runtimes. Generated automation reuses the project/agent-provided test runtime and declared dependencies; disclose unavailable execution infrastructure.
- Keep Designer-owned schemas and source modules under `skills/wewo-qa-case-designer/` and Executor-owned schemas and source modules under `skills/wewo-qa-case-executor/`.
- Keep shared runtime, build, and package-validation sources under `tooling/`; maintain all Python sources only as build and test inputs for the bundled runtime executables.
- Keep Claude and Codex plugin names and semantic versions synchronized.
- Run repository tests, package validation, both host validators when available, and runtime smoke tests before release.
- Per-host runtime archives include instructions, plugin metadata, notices and one native executable; exclude maintenance source, tests, Git state and temporary files.
- Never commit generated QA artifacts, credentials, authenticated session data, or real production data.
- Push to GitHub only when the user explicitly requests uploading the current changes; earlier upload requests do not authorize later changes.
