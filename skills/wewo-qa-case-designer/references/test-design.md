# Tester-facing black-box design

## Project target model

Define only targets that the project actually supports. Keep product surface separate from operating system:

- `web`: browser-delivered product.
- `mobile-app`: Android or iOS application, on a simulator/emulator or real device.
- `desktop-app`: native Windows, macOS, or Linux client.
- `mini-program`: host-platform mini application.
- `other`: a tester-visible surface that does not fit the above; describe it precisely.

A web page tested on Windows is not a Windows desktop application. Do not create cases for excluded platforms. For multi-platform products, share one business case across targets and add a variant only when actions, permissions, presentation, or expected results differ.

## Test-point tree and coverage map

Build the test-point tree progressively from confirmed requirement units before writing detailed cases. Prefer business-readable hierarchy such as `module → feature/flow → rule or state → condition/data → observable behavior`. Internal grouping nodes organize the map; leaf nodes are the concrete verification obligations that detailed cases must cover.

For every unit, consider the relevant dimensions without turning generic testing techniques into repetitive top-level branches:

- primary user journeys and release-blocking paths;
- roles, permissions, ownership, tenancy, and visibility;
- valid, invalid, empty, boundary, duplicate, and conflicting inputs;
- decision rules and meaningful condition combinations;
- state transitions, persistence, refresh, retry, cancellation, and recovery;
- repeated submission, concurrency, ordering, asynchronous completion, timeout, and error feedback;
- cross-screen or cross-system outcomes visible to the tester;
- platform, browser, device, orientation, locale, or accessibility requirements only when in scope;
- historical defects and changed dependencies when selecting regression coverage.

Use equivalence partitioning and boundary analysis for inputs, decision tables for interacting rules, state-transition analysis for lifecycle behavior, and pairwise reduction only when exhaustive combinations are disproportionate. Pairwise output never replaces explicitly high-risk combinations.

Keep test points concise. They state what must be verified and the observable outcome, not full preconditions, data, and step-by-step execution. One leaf test point may expand into several cases for meaningful state, data, or platform variants; one case may cover multiple tightly coupled leaf points when the steps and oracle remain clear.

Assign stable `TP-*` IDs. Do not renumber unchanged points when the tree is reorganized. Trace every non-root node to a requirement unit and a source or confirmed decision.

## Test oracle rules

Every expected result must be observable and falsifiable. Name the visible state, message, navigation, permission effect, persisted value, generated artifact, or external tester-visible outcome. Avoid weak phrases such as “works correctly,” “normal,” or “successful” without a concrete oracle.

Do not use implementation details as the sole oracle. Logs, network traffic, and storage may be supporting evidence when the product result remains externally observable.

## Suite membership

- `smoke`: the smallest release-blocking set proving the build and critical journeys are testable. Favor short P0 paths and essential environment readiness.
- `regression`: cases affected by the current change, dependencies, risk, or relevant defect history. It includes every smoke case.
- `full`: every confirmed tester-facing case in the current requirement baseline.

Do not populate suites by fixed percentage. Select from risk and change impact. The canonical case carries membership; the three Markdown files are projections, not independent copies.

## Automation feasibility per target

Assess each applicable target independently:

- `automatable`: the environment, data, actions, and oracle can be controlled and determined by an available UI tool.
- `conditional`: automation is viable only after a stated condition is met, such as device access, a test account, seeded data, or an authorized bypass for a human verification step.
- `manual`: reliable judgment or interaction requires a person or unavailable physical/external capability; state the reason.

Choose a candidate route from `browser-ui`, `mobile-ui`, `desktop-ui`, `computer-use`, or `none`. This is a capability hint, not permission to install a tool or execute the case. Never give one global automation flag to a multi-target case.

The test-point tree may flag an automation candidate, but final feasibility belongs to the detailed case because it depends on target, data, controllable actions, and deterministic oracle.

## Runtime readiness declaration

Translate every external prerequisite needed during execution into a reusable `RT-*` runtime requirement. Examples include the test-environment address, build identifier, account identity, credential channel, seeded data, device, control capability, and permission for side effects. Keep the readable `preconditions` and `test_data` fields, but do not rely on their prose as the executor's only input.

- Put requirements shared by every applicable target of a case in the case's `runtime_requirement_refs`.
- Put device-, platform-, or route-specific requirements in that target automation assessment's `runtime_requirement_refs`.
- Set scope to `run`, `target`, or `case` according to the narrowest reusable lifetime. Target-scoped requirements name their target IDs.
- Deduplicate equivalent requirements across cases. Do not create a separate base-URL or account requirement for every case.
- A `conditional` automation assessment must identify the structured requirement that makes it executable; its prose `condition` only explains that dependency.
- Separate a non-secret account identifier from its sensitive credential. Never store a password, token, cookie, one-time code, or private key. Sensitive requirements use only `secret-reference` or `authenticated-session` collection.

`required_evidence` contains the smallest set of evidence types actually required to prove the oracle, not every type a tool could capture. Add multiple types only when each proves a distinct required assertion.
