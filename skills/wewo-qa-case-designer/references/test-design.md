# Test-point granularity and executable cases

## Stop by verifiability, not depth

Organize branches around the business flow/object and rule, then split by relevant operation, state/role, input partition and outcome. Use only levels that add meaning. A branch ends when the leaf specifies one concrete condition, one trigger and one independently judgeable outcome. Depth varies with complexity; do not force three/four levels or pad every branch to a fixed depth.

Split a leaf when it contains separable combinations, alternatives, independent validations or multiple states. Each resulting leaf carries `rule_refs`, `coverage_item_refs` and `verification={condition, action, expected}`. Setup is not a test point. Assertions sharing one business outcome may remain together; unrelated outcomes need separate leaves. One case may verify several leaves as an explicit business flow.

For example, given a confirmed rule “submitted records cannot be deleted, and failed deletion must preserve their binding”:

```text
Record management
└─ Delete
   ├─ Draft record
   │  └─ No binding → delete → record absent from list [only if authorized by source]
   └─ Submitted record
      ├─ Delete → rejection message matches confirmed rule
      ├─ Delete rejected → record still present after refresh
      └─ Delete rejected → existing binding still displayed in related module
```

“Delete validation”, “check correct behavior”, or “abnormal data” alone is not an executable leaf. Exact message text should only be specified when the source/decision fixes it; otherwise specify the exact business meaning and observable rejection state.

“Allowed”, “rejected” or “enters the process” alone also needs an observable outcome in that leaf. Use the source-defined post-state, value, record visibility or objective rejection evidence; do not leave its only concrete check in another branch. Give each boundary/decision row its own applicable expectation instead of copying an alternative such as “empty or over-limit” into both rows. Preserve the source's limits on what is known: do not invent an error message or an observation mechanism to fill this gap. Resolve material business ambiguity during design; runtime UI routes remain Executor's readiness check.

## Coverage techniques

For each grounded rule, assess positive and reverse paths, equivalence partitions and relevant boundaries, valid/invalid state transitions, role/ownership scope and cross-object effects. For threshold N, consider the meaningful N−1/N/N+1 states with executable setup; distinguish count before and after the action. For selections, assess empty/single/multiple and mixed eligible/ineligible only where the operation supports them. For invalid inputs, verify both the error and preservation of prior business state when required.

Walk the full flow from input through intermediate state to downstream visible outcome. Check partial success, interrupted/repeated operations and cleanup if the source or actual flow makes them relevant. Use a decision table for interacting conditions; document infeasible combinations. Pairwise selection is insufficient for a known interacting business rule. Derive regression from affected object/state/data consumers, not simply all pages or a fixed count.

Company XMind examples guide meaningful nesting, concise titles and concrete leaves. They are not evidence that every example rule belongs in this project.

Save actual technique derivations using [method records](method-records.md), not only dimension labels. Required obligations must reach leaves, cases and assertions.

## Detailed case readiness

Each case needs reproducible preconditions, concrete data values or uniquely resolvable selection criteria, numbered actions and expected results, leaf and source/decision references, suites, targets, cleanup, and planned assertions. Avoid boilerplate such as “prepare valid data / operate / result correct”. Give the tester the values, states, quantities and observation locations necessary to reproduce the outcome.

For every required outcome, define a stable `AS-*` assertion with target applicability, exact `expected`, `observation`, leaf references and required evidence. Bind it to the step that produces or checks it. Check that the prose step expectation and assertion oracle express the same rule. No planned leaf may be covered only by an action without an assertion.

Automation feasibility is assessed from the specified UI interactions, obtainable data, deterministic observable oracle and safe repeat/reset procedure. Product code and live execution are not required to make this design assessment. Describe `candidate_route` using the intended business interaction and record its basis; do not invent verified selectors, record IDs or execution evidence.

`automatable` is feasible without unresolved project-specific design conditions; declare external inputs using `RT-*` requirements. `conditional` names unresolved route/data/reset conditions and corresponding runtime requirements. `manual` names the human judgment or unavailable capability. An environment not yet deployed does not by itself make every case conditional: record the needed build/environment as runtime requirements. A missing business decision that changes the expected result must be clarified before finalizing the case, rather than hidden in an automation condition. Executor verifies actual readiness after deployment; an automatable label does not claim a successful run.

Before finalizing, audit for invented rules, duplicated generic cases, bundled leaves, wrong states, untested reverse outcomes, unsupported “automatable” labels and affected flows missing regression. Validators cannot perform this semantic review.
