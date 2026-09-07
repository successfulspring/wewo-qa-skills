# Repository maintenance

- Keep `skills/` as the single canonical Skill tree for every host.
- Keep Case Designer limited to tester-facing case design and Case Executor limited to tester-facing black-box execution.
- Do not add unit, API, component, contract, developer self-test, production implementation, or product repair workflows.
- Do not hardcode Web, mobile, desktop, iOS, Android, or a page-based interface as a universal project target.
- Installed runtime behavior must not require testers to install Python, Node.js, or package dependencies.
- Keep Designer-owned schemas and source modules under `skills/wewo-qa-case-designer/` and Executor-owned schemas and source modules under `skills/wewo-qa-case-executor/`.
- Keep shared runtime, build, and package-validation sources under `tooling/`; maintain all Python sources only as build and test inputs for the bundled runtime executables.
- Keep Claude and Codex plugin names and semantic versions synchronized.
- Run repository tests, package validation, both host validators when available, and runtime smoke tests before release.
- Never commit generated QA artifacts, credentials, authenticated session data, or real production data.
