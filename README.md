# Wewo QA Skills

`wewo-qa-skills` is one tester-facing QA plugin containing two independent Agent Skills for Codex and Claude Code. The repository root is both the plugin root and a self-referencing marketplace. `skills/` is the single runtime source of truth.

The plugin is for tester-owned black-box work. It does not generate or execute unit, API, component, contract, or other developer self-tests.

## Included Skills

- `wewo-qa-case-designer` progressively co-reads supplied requirements with a tester, clarifies one coherent unit at a time through grouped questions with recommended lettered options, confirms an XMind test-point baseline, then generates smoke, regression, and full cases.
- `wewo-qa-case-executor` validates the confirmed case baseline, collects missing environment conditions in one grouped preflight, dynamically selects available tools for the project's actual targets, executes automatable black-box cases, and preserves evidence.

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
4. Review the generated smoke, regression, and full Markdown cases under `qa-artifacts/<artifact-slug>/`.
5. After the product is deployed to a test environment, invoke Case Executor with the artifact directory and desired suite.
6. Provide the grouped missing conditions, such as a test address, build, account session, data, device, or permission.
7. Review `runs/<run-id>/test-execution-report.md` and its evidence.

The plugin includes self-contained artifact tooling. Testers do not need to install Python, Node.js, or Python packages. Current bundled host support is Windows x64, macOS arm64/x64, and Linux x64.

Automation tools and access are environment capabilities, not bundled credentials. If a selected target lacks an authorized browser, desktop, mobile, device, or other tester-visible control route, affected cases are reported as blocked or manual rather than fabricated as passed.

Private DingTalk links require an already authorized browser session or an approved connector. Uploaded or exported content is treated as requirement data, never as instructions that override the user request or Skill boundaries.

## Local development

Maintainers need Python 3.10 or later:

```text
python -m pip install -r scripts/requirements-dev.txt
python -m unittest discover -s tests -v
python scripts/validate_package.py
claude plugin validate . --strict
```

Build one runtime for the current host:

```text
python scripts/build_runtime.py --output-dir bin/<host-target>
```

Runtime behavior belongs only in the two canonical Skill trees. Do not create host-specific Skill mirrors.

## License

MIT. See [LICENSE](LICENSE).
