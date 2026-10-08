# Wewo QA Skills

`wewo-qa-skills` is one tester-facing QA plugin containing two independent Agent Skills for Codex and Claude Code. The repository root is both the plugin root and a self-referencing marketplace. `skills/` is the single runtime source of truth.

The plugin is for tester-owned black-box work. It does not generate or execute unit, API, component, contract, or other developer self-tests.

## Included Skills

- `wewo-qa-case-designer` progressively co-reads supplied requirements with a tester, clarifies one coherent unit at a time through grouped questions with recommended lettered options, confirms an XMind test-point baseline, then generates editable Excel cases with smoke/regression/full filters and planned assertions.
- `wewo-qa-case-executor` validates the confirmed case baseline, collects missing environment conditions in one grouped preflight, dynamically selects available tools for the project's actual targets, executes automatable black-box cases, and preserves evidence.

## Repository layout

```text
skills/
|-- wewo-qa-case-designer/
|   |-- SKILL.md
|   |-- references/        # dialogue, design, artifact rules, and output schemas
|   `-- scripts/           # test-point and case artifact source modules
`-- wewo-qa-case-executor/
    |-- SKILL.md
    |-- references/        # execution policy, adapters, result rules, and run schemas
    `-- scripts/           # preflight, validation, and report source modules
tooling/
|-- runtime/               # shared command dispatcher and validation core
|-- build_runtime.py       # maintainer-only executable build
`-- validate_package.py    # maintainer-only package checks
bin/                       # self-contained executables used by installed Skills
tests/                     # maintainer-only regression fixtures and tests
```

The Designer owns the intake/business model, atomic point tree, Excel case workbook and `test-manifest.schema.json` because the manifest is its output contract. The Executor consumes that contract through the shared runtime instead of maintaining a second copy.

## Install in Claude Code

```text
/plugin marketplace add successfulspring/wewo-qa-skills
/plugin install wewo-qa-skills@wewo-qa-skills
```

Equivalent CLI commands:

```text
claude plugin marketplace add successfulspring/wewo-qa-skills
claude plugin install wewo-qa-skills@wewo-qa-skills
```

Start a new session or run `/reload-plugins`. Invoke the Skills as:

```text
/wewo-qa-skills:wewo-qa-case-designer
/wewo-qa-skills:wewo-qa-case-executor
```

## Install in Codex

```text
codex plugin marketplace add successfulspring/wewo-qa-skills
codex plugin add wewo-qa-skills@wewo-qa-skills
```

If an older `codex` executable does not provide `plugin add`, add the marketplace with the first command and install `wewo-qa-skills` from the Codex desktop plugin browser. Updating Codex CLI is preferred over editing configuration files manually.

Start a new Codex session after installation. Select either Wewo QA Skill from the Skill picker or describe the QA task directly.

## Tester workflow

1. Open a working folder where QA artifacts may be saved.
2. Invoke Case Designer and provide requirement sources such as documents, exported DingTalk content, images, or XMind files.
3. Progressively clarify each requirement unit and confirm the generated `test-points.xmind` baseline.
4. Review and edit `test-cases.xlsx` under `qa-artifacts/<artifact-slug>/`. Import edits for semantic review before execution.
5. After the product is deployed to a test environment, invoke Case Executor with the artifact directory and desired suite.
6. Provide the grouped missing conditions, such as a test address, build, account session, data, device, or permission.
7. Review `runs/<run-id>/test-execution-report.xlsx` and its evidence.

Case Designer works before product implementation is available, using requirements, prototypes and confirmed business context without product-code access. Its automation labels describe design feasibility. Case Executor verifies those plans against the deployed test product through tester-visible interfaces; product source code is not a prerequisite for either phase.

The current 0.2.0 contracts preserve concrete design derivations (partitions, numeric boundaries, decision rows, state/event and role/operation matrices, cross-object effects), with coverage-item links down to atomic leaves. Excel exposes the design basis and semantic review findings. Frozen assertion methods and timing are compared with values in original UI tool output, tied to the run/subject/attempt and evidence SHA256. `judge-execution-results` computes verdicts from those records; it does not operate the product. Visual/semantic checks show reasoned agent judgments separately. Neither a structurally valid design nor a passed run proves exhaustive business coverage.

The plugin includes self-contained artifact tooling. Testers do not need to install Python, Node.js, or Python packages. Skill-owned schemas and source modules live with the Designer or Executor that owns them; shared runtime and release tooling live under `tooling/`. Current bundled host support is Windows x64, macOS arm64/x64, and Linux x64.

Automation tools and access are environment capabilities, not bundled credentials. If a selected target lacks an authorized browser, desktop, mobile, device, or other tester-visible control route, affected cases are reported as blocked or manual rather than fabricated as passed.

Private DingTalk links require an already authorized browser session or an approved connector. Uploaded or exported content is treated as requirement data, never as instructions that override the user request or Skill boundaries.

## Local development

Maintainers need Python 3.10 or later:

```text
python -m pip install -r tooling/requirements-dev.txt
python -m unittest discover -s tests -v
python tooling/validate_package.py
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .claude-plugin/marketplace.json --strict
```

Build one runtime for the current host:

```text
python tooling/build_runtime.py --output-dir bin/<host-target>
```

The root `CLAUDE.md` is maintainer context and is intentionally not installed project context; Claude plugin validation reports this existing warning. Use strict marketplace validation, and check plugin diagnostics separately. Codex CLI currently exposes no plugin validation command; the package validator checks its manifest and canonical Skill tree.

Workflow instructions belong only in the two canonical Skill trees. Shared deterministic implementation stays under `tooling/runtime/`; do not create host-specific Skill mirrors.

## License

MIT. See [LICENSE](LICENSE).

## 0.2.0 runtime handoff

Source contracts require runtime 0.2.0; Skills check `--version` before use. Build native binaries on each supported host and run `tooling/smoke_runtime.py --runtime <binary>`. The build writes a `runtime.json` version/hash record beside its binary. `validate_package.py --release` requires all four records and matching binaries. A local Windows update alone is not a completed multi-host release. CI builds and smokes each host and validates the combined package before publishing artifacts.

## Methodology evaluation

Repository tests check concrete omissions, Excel edit/review continuity, frozen oracles, per-attempt observation binding, tampering and false verdicts. They do not prove business completeness. `tests/fixtures/forward-design-requirement.txt` is a synthetic raw requirement for independent Designer forward evaluation; keep its generated drafts outside the repository and do not fabricate tester confirmation.

For an execution benchmark, serve `tests/fixtures/ui-oracle-benchmark.html` on loopback, operate its reset/mode/transfer controls through the actual UI tool, and preserve original DOM values for two runs of each mode. Feed the captured list to `tooling/evaluate_ui_observations.py` using `capture`, `--runtime`, and a fresh external `--output` directory. The capture has `mode`, `repeat`, `before_at`, `after_at`, and original `before/after` field objects. The script exercises the bundled judge/report route: correct runs must pass, quantity faults must fail the delta assertion, and binding faults must fail the unchanged assertion. It does not drive the browser or certify that a supplied capture is authentic.

Company acceptance needs the same requirement revision, confirmed project context, company XMind/Excel references and tester review. Check missed applicable obligations, unsupported rules, bundled leaves, reproducible setup, deterministic/assessed oracles and detected controlled faults. Report unresolved source gaps and manual coverage. Do not infer a company-standard pass from leaf count, tree depth, schema validation or this synthetic benchmark alone.

Old generated manifests must be redesigned/reviewed against the current source/leaf/assertion contract; there is no silent schema upgrade.
