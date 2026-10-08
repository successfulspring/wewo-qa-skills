---
name: wewo-qa-case-executor
description: Execute reviewed tester-facing Excel black-box cases marked automatable for selected project targets, verify every planned assertion using available UI tools, and produce an Excel report with linked evidence. Use for smoke, regression or full QA execution; not case design, developer tests, automation-code generation or product repair.
---

# Wewo QA Case Executor

Execute the confirmed tester-owned cases against the actual test environment. Primary execution output is `test-execution-report.xlsx` with preserved evidence.

## Scope and verdicts

- Use tester-visible interfaces on the project's selected targets. Exclude unit, API, component, contract and developer self-tests; do not generate test code or modify the product.
- Test the implemented product running in the identified test environment. Product source-code access is not required. Resolve the Designer's planned routes, data criteria and runtime requirements against the actual interface; keep the requirement-derived expected results frozen. Design feasibility is not proof of runtime readiness.
- Use available authorized UI/control capabilities. Manual cases remain `not-run`; unavailable tools or ambiguous oracles block the affected pair.
- An action completing does not establish a pass. Every planned assertion applicable to the target must be evaluated against its frozen oracle with linked evidence.
- Do not rewrite the oracle to match observations or repair test data/environment without authorization. Keep secrets outside artifacts.

## Workflow

1. Resolve the executable through [runtime tool](references/runtime-tool.md). Validate `test-manifest.json` and `test-cases.xlsx`; this also verifies context, confirmed point hashes, coverage and case review. If Excel differs, route its edits to Designer for import and review. Stop dependent execution until it matches; do not run the old JSON or discard the edits.
2. Resolve requested suite and actual target IDs. For multiple possible targets, clarify the selected scope. Build selected suite × applicable selected targets; do not infer extra platforms.
3. Aggregate deduplicated runtime requirements for non-manual pairs and generate `execution-profile.json`. Follow [execution policy](references/execution-policy.md): inspect current tools/sessions first, then ask once for remaining user-resolvable inputs. Validate and freeze the profile, manifest and workbook hashes before product interaction.
4. Use only the relevant [platform adapters](references/platform-adapters.md). Resolve each feasible route to an available authorized tool. Automatable pairs execute when ready; conditional pairs execute only after conditions are resolved; manual pairs remain `not-run`. Continue independent ready pairs when others are blocked.
5. Execute the case steps using the documented state/data. Wait for each frozen check timing and inspect the specified subject/location. Preserve original UI tool output and required images before cleanup using [observation evidence](references/observation-evidence.md). Bind extracted values to the original output by JSON Pointer; compare using the frozen method. Evidence-review checks require per-attempt objective reasons. Isolate/reset state without treating a previous case's dirty state as setup evidence.
6. Record a result for every selected pair. Retain the planned assertion IDs and expected values; record actual observation, passed/failed/not-evaluated status and evidence references for each. When interrupted after starting, retain every planned assertion and give reasons for those not evaluated. Missing checks cannot yield passed.
7. Use `judge-execution-results` to derive actual text and verdicts from preserved observations into a separate reviewed result file, then validate it and render the Excel report using [result contract](references/result-contract.md). The command compares evidence; it performs no product actions and cannot fill missing observations. Report failures, incomplete assertion coverage, blockers, manual work and environment limits. A zero-eligible-case run cannot have a passing automation gate.

Completion means every selected pair has a truthful validated result and the report has been generated; it does not imply that blocked/manual coverage was executed. A passed pair requires all applicable planned assertions passed, matching original oracles and existing linked evidence. A valid artifact proves declared evidence consistency; it does not prove exhaustive business coverage or the authenticity of observations without actual tool execution.

Resolve the plugin root two directories above this skill for its bundled runtime. A tester must not need to install language runtimes or dependencies.
