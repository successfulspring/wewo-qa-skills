---
name: wewo-qa-case-executor
description: Execute reviewed test cases against a deployed test environment by discovering missing access, data and tooling, preparing an independent automation workspace, writing and running durable acceptance tests, and reporting every result with evidence. Use for smoke, regression or full acceptance execution; product source code is not required.
---

# Wewo QA Case Executor

Start with the Designer artifact directory and the test environment entry point. Identify execution needs, inspect what is available, ask the tester for the remaining gaps, then write and run repeatable tests and deliver an evidence-backed report.

Keep Skill instructions and examples in English. Follow the user's conversation language; inherit `project.output_language` for the report and authored readiness details, failure explanations and review notes, defaulting to Chinese for legacy cases. Preserve literal expected values, source quotations and identifiers.

## Boundaries

- Confirmed cases define correct behavior. Resolve live locators, accounts, records and setup here; return missing or conflicting business expectations to Designer.
- Product source and a product repository are not prerequisites. Reuse an authorized automation workspace or create a persistent independent test workspace beside the artifact directory. Inspect only supplied test assets, authorized documentation and live test surfaces. Do not request product source to unblock routine acceptance testing or modify production implementation.
- Preserve the case's observation surface. UI expectations require actual UI observations; interface expectations use the specified interface. Supporting API setup does not replace required UI checks. Mocked/unit-only checks cannot prove deployed business behavior.
- Use mature frameworks and declared dependencies. The bundled artifact executable needs no tester-installed language runtime; actual tests still need suitable runtime, browsers/devices and access. Discover existing or host-provided capabilities, configure available dependencies inside the test workspace, and disclose concrete unavailable infrastructure.

## Workflow

1. Resolve the [runtime](../runtime-tool.md). Validate the Designer baseline and all three editable Excel views; reconcile edits before execution. Select suite and targets from the request. Read each selected case's preparation, steps, every target-applicable assertion and cleanup. Keep manual cases in the selected inventory.
2. Inspect the supplied environment without performing unprepared business mutations: reachability, login entry, identifiable build, relevant documented interfaces and available control/runtime capabilities. Inspect provided automation assets if any. Record actual observations separately from user-supplied claims. See [execution preflight](references/execution-policy.md).
3. Prepare the execution profile. Derive needs from the cases and add newly discovered runtime requirements there, without altering confirmed business rules. Group unresolved account/role, data, access, device and tooling needs into one concise request. Reuse information already supplied. Accept partial answers, recheck affected conditions and ask follow-ups only for specific remaining or newly discovered gaps. Do not ask the tester to invent locators or write scripts.
4. Verify readiness per case-target, including interaction, observation, data preparation, cleanup and tooling. An automation assessment is a design estimate, not proof of current readiness. Preserve concrete blockers; continue independent ready cases. A manual assessment may be reconsidered with new evidence through a reviewed baseline update, never silently overridden.
5. Prepare the independent automation workspace and implement the selected ready cases following [native automation](references/native-automation.md). Reuse suitable existing tests/helpers. Map every case-target and assertion to a real test identifier and evidence location. Discover actual locators or interface paths from the authorized live surface and documentation; no guessed selectors, APIs or product rules. Use [platform guidance](references/platform-adapters.md) for the selected surface.
6. Walk generated code against the case: preparation and reset, concrete data, business action sequence, completion waits, every expected result, and cleanup. Freeze the plan, workspace assets, profile and environment identity. Run a focused check to repair test implementation errors, then execute the selected scope. Reuse the same reviewed tests on later runs when their dependencies and expected behavior remain valid.
7. Preserve runner reports, original observations, preparation/cleanup outcomes and failure evidence as execution happens. Attribute failures to product behavior, test implementation, data, environment or requirement conflict using actual evidence. Fix test defects within scope; do not weaken assertions or fix product code. Preserve every attempt and record reasons for repeats and test repairs. A changed deployment starts a new run.
8. Recompute deterministic comparisons; explicitly inspect original evidence for objective visual/semantic checks. Missing checks stay unchecked. Complete the review process in [observation evidence](references/observation-evidence.md), then aggregate every invocation, including earlier failures and cases that never ran, using [result contract](references/result-contract.md).
9. Validate and deliver `test-execution-report.xlsx`, links to native reports/evidence and the reusable test workspace, tested environment/build, counts, actionable failures/blockers, cleanup issues and manual scope. Inherit the delivery language. Preserve private records under `.qa-state/runs/`; keep automation source in its persistent workspace.

Completion requires actual test-code execution and a truthful report covering the entire selected scope. Generation, screenshots without the required checks, a runner exit code alone, or zero executed cases cannot establish a pass. A fully blocked run still receives an incomplete report listing the required next inputs.
