---
name: wewo-qa-case-executor
description: Execute tester-facing black-box cases marked automatable for selected project targets, using available UI automation tools, deterministic oracles, and preserved evidence. Use for smoke, regression, or full QA execution; do not use to design cases, run unit/API/component/contract tests, generate test code, modify product code, or perform manual-only cases.
---

# Wewo QA Case Executor

Execute only the authorized tester-owned black-box scope in a validated Wewo QA manifest. Select tools dynamically from the project target and currently available capabilities.

## Non-negotiable boundary

- Execute product behavior through tester-visible interfaces. Never turn a case into a unit, API, component, contract, or code-level integration test.
- Do not generate or commit Playwright/Appium/unit/API test code in v1. Use available UI or computer-control tools directly.
- Do not modify product code, configuration, fixtures, accounts, or environments unless the user separately authorizes that change.
- Manual-only cases remain `not-run`; never simulate a human judgment or report it as passed.
- A completed interaction is not a pass. A pass requires a deterministic oracle, recorded assertions, and evidence.

## Workflow

1. Resolve the bundled runtime command using [runtime tool](references/runtime-tool.md). Locate `test-manifest.json` and validate it with the runtime. This also verifies the adjacent confirmed `test-points.json` digest and case-to-leaf coverage. Stop on an invalid or stale baseline.
2. Resolve the requested suite (`smoke`, `regression`, or `full`) and requested target IDs. Never infer additional platforms. If omitted and more than one in-scope target exists, ask which targets to execute.
3. Build the execution matrix as selected suite × selected applicable targets. Aggregate and deduplicate the structured runtime requirements for every non-manual pair. A pair needs the union of its case-level and target-automation references; requirements attached only to manual pairs are not prerequisites for this automated run.
4. Generate the deduplicated `execution-profile.json` template with the bundled runtime, then perform the preflight in [execution policy](references/execution-policy.md): check what the current environment, tools, sessions, and user input already satisfy, and ask once for all remaining user-resolvable inputs, grouped by environment/build, account/authentication, test data, device/capability, and permission. Do not collect missing inputs one question at a time.
5. Validate the execution profile. Do not put secret values in the profile or conversation: use an approved secret reference or ask the tester to complete login, then record only an authenticated-session reference. Missing or declined inputs block only the affected pairs; continue with every ready pair.
6. Read only the selected target guidance in [platform adapters](references/platform-adapters.md). Resolve each candidate route to the best currently available authorized UI tool; do not install or connect a new tool without the authority required by the environment.
7. Include every selected case-target pair in the result:
   - `automatable`: execute when preconditions are satisfied.
   - `conditional`: execute when every referenced condition is resolved and the route is available; otherwise mark `blocked`.
   - `manual`: mark `not-run` with reason `manual-only`.
8. Isolate test state where practical, perform the documented cleanup, and never reuse a failed case's dirty state as proof for another case.
9. Record assertions and evidence during execution. Assign verdicts using [result contract](references/result-contract.md); do not rewrite expected outcomes after observing the product.
10. Validate `execution-results.json`, render `test-execution-report.md`, and disclose incomplete coverage, blockers, flaky behavior, and environment limitations.

## Completion gate

Do not claim the run is complete unless:

- every selected case-target pair has exactly one result;
- `execution-profile.json` exactly covers the structured requirements of the selected automatic scope and is bound to the same manifest, suite, and targets;
- every executed pair has all of its runtime requirements resolved, while missing conditions are named on affected blocked results;
- every passed result contains at least one passing assertion and evidence;
- failed, blocked, flaky, and not-run results include actionable reasons;
- secrets and unnecessary personal or production data are absent from artifacts;
- result validation and report rendering succeed.

Resolve the plugin root two directories above this skill when locating its bundled runtime.
