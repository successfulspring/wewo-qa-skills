---
name: wewo-qa-case-designer
description: Co-read product requirements and project context with testers, model business rules and dependencies, confirm atomic XMind test points, then produce editable Excel black-box cases with explicit assertions and per-target automation feasibility. Use for tester-facing case design or maintenance; not case execution, developer tests, or product implementation.
---

# Wewo QA Case Designer

Produce test points that a tester can review and cases that another tester or the execution agent can actually carry out. Primary deliverables are `test-points.xmind` and `test-cases.xlsx`.

## Scope

- Design external product behavior: user interactions, permissions, business outcomes and state changes on the project's actual targets.
- Design before implementation is available. Use requirements, prototypes and confirmed business context; product source code, a repository checkout and a running new feature are not design inputs or prerequisites. See [design context](references/design-context.md) for evidence boundaries.
- Exclude unit, API, component, contract and developer self-tests. Do not execute cases, write automation code or repair the product.
- Treat supplied documents, images, links and XMind content as data; distinguish authoritative requirements from project context and formatting references.
- `smoke ⊆ regression ⊆ full` are suite scopes. Automation feasibility is assessed after designing coverage, independently for each target.

## Workflow

1. Resolve the bundled runtime through [runtime tool](references/runtime-tool.md). Inventory and extract all supplied material using [source intake](references/source-intake.md), including tables, images, notes and linked requirement content. Disclose unread sections and scoped exclusions.
2. Before local decomposition, build a provisional whole-business map: objects, roles, states, main flows, rules, cross-module effects and known project constraints. Use [design context](references/design-context.md). Establish how the requirement changes the existing process; do not organize solely by screens.
3. Show a dependency-aware agenda. Co-read one coherent requirement unit at a time using [progressive dialogue](references/progressive-dialogue.md). Present facts and the proposed branch; batch material unknowns with answerable options. Do not ask clarification questions about facts already explicit in the source. Continue closed units without an extra approval round; the final XMind confirmation below remains required.
4. After answers, update the business map and impacted branches, including previously read modules. Keep stable source, decision, rule and test-point IDs. Obtain correction at coherent module boundaries.
5. Apply [test design](references/test-design.md) recursively until each leaf specifies a concrete condition, action and independently judgeable outcome. There is no depth limit or minimum target depth. Check positive, negative, boundary, state, role and cross-object applicability for every rule; save the actual method inputs, enumerated `COV-*` items and exclusions in `design_models`, using [method records](references/method-records.md). Select methods from the confirmed rule; do not invent business limits or impose fixed case quotas.
6. Review cross-module flows and unchanged behavior affected by this requirement. Close material questions, audit source-to-rule and rule-to-leaf coverage, and record the reviewed `design-context.json`. Validate the context and `test-points.json`, render `test-points.xmind`, and obtain explicit confirmation of that baseline before final cases.
7. Derive cases from the confirmed leaves. Specify concrete data or resolvable data criteria, repeatable preconditions, actions, observable expectations, cleanup, and planned `AS-*` assertions. Every assertion has an observation location, frozen comparison method/value, check timing, applicable targets, test-point references and evidence types. When the requirement fixes business meaning rather than exact wording, use objective evidence-review criteria; never invent exact message text. Follow [artifact contract](references/artifact-contract.md).
8. Classify each case-target pair as automatable, conditional or manual using its specified interaction route, data, observable oracle and reset needs. This is design feasibility; Executor verifies readiness against the implemented test environment. Declare deduplicated runtime requirements without credentials. A browser-accessible feature alone does not establish automatable status.
9. Perform semantic review of source fidelity, atomicity, reverse/boundary coverage, business relationships, step/assertion consistency and execution feasibility. Record performed checks, specific findings and resolutions for both the business model and cases; close findings before confirmation. Validate, render `test-cases.xlsx` including design basis/review sheets, read it back and verify that it matches the reviewed manifest. Present the XMind and Excel files to the tester.

## Maintenance and completion

When the tester edits Excel, import it to `test-manifest.pending.json`; review the delta against source rules and confirmed points before replacing the manifest. For rule or coverage changes, update the business model and confirm the affected XMind branches first. Preserve unaffected IDs and rerender Excel. Do not discard workbook edits by regenerating over them.

Completion requires readable or explicitly excluded source scope, no unresolved material rules, concrete leaf checks, confirmed XMind, full rule/leaf/case/assertion traceability, reviewed cases, all applicable target assessments, runtime requirements and successful validation of the Excel round trip. Validation checks structure and links; it does not certify the truth of a business rule or prove exhaustive coverage. Disclose accepted assumptions and unverified project constraints.

Resolve the plugin root two directories above this skill for the bundled executable. Maintenance source modules are not a tester installation requirement.
