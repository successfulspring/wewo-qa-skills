# Wewo QA Skills

`wewo-qa-skills` is one tester-facing QA plugin containing two independent Agent Skills for Codex and Claude Code. The repository root is both the plugin root and a self-referencing marketplace. `skills/` is the single runtime source of truth.

The plugin is for tester-owned acceptance work: requirement clarification and case design first, then generated test code and native execution against the test environment. It preserves required UI/interface evidence and does not repair production code.

## Included Skills

- `wewo-qa-case-designer` progressively co-reads supplied requirements with a tester, clarifies one coherent unit at a time through grouped questions with recommended lettered options, confirms an XMind test-point baseline, then generates editable Excel cases with smoke/regression/full three suite files and planned assertions.
- `wewo-qa-case-executor` validates the confirmed case baseline, collects missing environment conditions in one grouped preflight, dynamically selects available tools for the project's actual targets, generates and runs automatable acceptance test code, and preserves evidence.

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

1. Supply requirements in documents/images/prototypes/links; disclose inaccessible scope.
2. Explain and clarify the whole business with the tester across dialogue rounds.
3. Present the complete requirement summary and obtain explicit final confirmation.
4. Derive and confirm `test-points.xmind`, split to independently verifiable business checks.
5. Deliver `test-cases.smoke.xlsx`, `test-cases.regression.xlsx`, and `test-cases.full.xlsx` with stable shared IDs and automation feasibility.
6. Inspect the actual project source, established test framework and identified test environment.
7. Reuse/write durable acceptance tests in project test paths, run them with the native runner, and preserve original evidence.
8. Deliver `test-execution-report.xlsx` plus the native human report when available.

Keep machine JSON, caches, helper scripts and raw run evidence under `.qa-state/`; the public design directory has only one XMind and three Excel files. Excel edits in any view need reconciliation/review before execution. Generation uses no product code; execution uses it to implement tests without changing requirement-derived oracles. Native runner success with missing business checks cannot pass. Live UI inspection alone cannot establish code-based automation completion.

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

Source contracts require runtime 0.2.0; Skills check `--version` before use. Build native binaries on each supported host and run `tooling/smoke_runtime.py --runtime <binary>`. The build writes a `runtime.json` version/contract/hash record beside its binary. `validate_package.py --release` requires all four records and matching source-contract/binary hashes. A local Windows update alone is not a completed multi-host release. CI builds and smokes each host and validates the combined package before publishing artifacts.

## Methodology evaluation

Repository tests check concrete omissions, Excel edit/review continuity, frozen oracles, per-attempt observation binding, tampering and false verdicts. They do not prove business completeness. `tests/fixtures/forward-design-requirement.txt` is a synthetic raw requirement for independent Designer forward evaluation; keep its generated drafts outside the repository and do not fabricate tester confirmation.

For an execution benchmark, serve `tests/fixtures/ui-oracle-benchmark.html` on loopback, operate its reset/mode/transfer controls through the actual UI tool, and preserve original DOM values for two runs of each mode. This older tool-only benchmark checks observation comparison, not code-generation completion. Feed the captured list to `tooling/evaluate_ui_observations.py` using `capture`, `--runtime`, and a fresh external `--output` directory. The capture has `mode`, `repeat`, `before_at`, `after_at`, and original `before/after` field objects. The script exercises the bundled judge/report route: correct diagnostic observations must compare successfully (their code-execution gate remains NO_CODE_EXECUTION), quantity faults must fail the delta assertion, and binding faults must fail the unchanged assertion. It does not drive the browser or certify that a supplied capture is authentic.

Company acceptance needs the same requirement revision, confirmed project context, company XMind/Excel references and tester review. Check missed applicable obligations, unsupported rules, bundled leaves, reproducible setup, deterministic/assessed oracles and detected controlled faults. Report unresolved source gaps and manual coverage. Do not infer a company-standard pass from leaf count, tree depth, schema validation or this synthetic benchmark alone.

Old generated manifests must be redesigned/reviewed against the current source/leaf/assertion contract; there is no silent schema upgrade.
