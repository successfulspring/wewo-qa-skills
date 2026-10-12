# Test-point granularity and executable cases

## Stop by verifiability, not depth

Organize branches around the business flow/object and rule, then split by relevant operation, state/role, input partition and outcome. Use only levels that add meaning. A branch ends when the leaf specifies one concrete condition, one trigger and one independently judgeable outcome. Depth varies with complexity; do not force three/four levels or pad every branch to a fixed depth.

Split a leaf when it contains separable combinations, alternatives, independent validations or multiple states. Each resulting leaf carries `rule_refs`, `coverage_item_refs` and `verification={condition, action, expected}`. Setup is not a test point. Several checks proving one indivisible business outcome may remain together; independently observable outcomes need separate leaves. One case may verify several leaves as an explicit business flow.

Atomicity follows the business predicate, not the number of fixture records. A uniform invariant on one defined collection may be one outcome when its check compares the complete membership/value mapping, including every selected identity and duplicate count where relevant. For a confirmed association-preservation rule, compare the complete before/after mapping of member identities to their associated identities; checking only one member or a total count is insufficient. Collection size alone does not determine the number of leaves. Split members with different eligibility, rules, expected changes or action paths. Keep independent association, status and numeric predicates separate, even when one operation affects them together. Execution may inspect every member and preserve member-level evidence for one collection assertion.

Audit the entire visible path, not just the leaf's JSON. The current XMind renderer displays each node's `title` and puts `verification` in its note, so a hidden `expected` does not repair a vague visible topic. A parent must name a real business object, operation, rule or decisive condition; it must not be a chain of `precondition → step → expected` fields. Read the parent titles plus the leaf title as a sentence: can a tester identify the specific condition, trigger and business result without opening notes? Put the decisive missing words in the title or an immediately visible parent, and keep detailed source/derivation in the note. If a parent says only “state validation / exception testing” or a leaf says “correct result / normal processing”, rewrite it. A shallow branch is correct when it already passes this audit.

For each candidate leaf, ask: (1) can the condition hold in more than one relevant state, role, data range or mutually exclusive path? (2) can the trigger produce two independently judged results, including a rejection and an unchanged related object? (3) does a derived model row still lack its own outcome? Split on the specific difference and re-run the audit until each obligation has a leaf. Do not split merely to increase depth, count or title length. Do not merge cases solely because two different states, actors or operations have the same final text; merge only when the preparation, path and obligations are genuinely equivalent and each required assertion remains visible.

For illustration only, suppose the current UI requirement confirms that submitted records cannot be deleted and that rejection must preserve both the record and its displayed association:

```text
Record management
└─ Delete
   └─ Submitted record
      ├─ Delete → rejection message matches confirmed rule
      ├─ Delete rejected → record still present after refresh
      └─ Delete rejected → existing binding still displayed in related module
```

“Delete validation”, “check correct behavior”, or “abnormal data” alone is not an executable leaf. Exact message text should only be specified when the source/decision fixes it; otherwise specify the exact business meaning and observable rejection state.

“Allowed”, “rejected” or “enters the process” alone also needs an observable outcome in that leaf. Use the source-defined post-state, value, record visibility or objective rejection evidence; do not leave its only concrete check in another branch. Give each boundary/decision row its own applicable expectation instead of copying an alternative such as “empty or over-limit” into both rows. Preserve the source's limits on what is known: do not invent an error message or an observation mechanism to fill this gap. Resolve material business ambiguity during design; runtime UI routes remain Executor's readiness check.

## Select and derive coverage techniques

Start from each confirmed `RULE-*` and the whole-business map. For each applicable method, record the rule/source or decision, why the method applies, concrete rows in existing `design_models/items`, and each row's disposition. Do not require every method for every rule. A risk checklist yields an applicability decision or a clarification question, not an automatic business expectation. Check historical defects and common risks such as repeated submission, second confirmation, upload limits, interruption and downstream stale data only where this operation can encounter them; confirm their expected behavior from current source/project rules before making them required coverage.

| Confirmed rule shape | Derivation to perform before writing leaves |
| --- | --- |
| Required field, format, range or enumeration | Partition by *different expected behavior*, label valid/invalid classes, give each representative input and expected acceptance/rejection. Separate empty from over-limit or wrong-format when they have distinct causes. Do not claim every syntactic variation needs a new case without an applicable rule/risk. |
| Numeric, length, amount or time limit | Identify the exact limit, whether equality is included, the business unit and smallest meaningful change. Record below/on/above data and the result for each. A calendar day, character count, currency increment and discrete item count are not interchangeable. Unknown precision or exclusivity is a material question. |
| Several conditions jointly determine an outcome | Name factors and domains, enumerate disjoint decision rows (or a justified outcome-invariant wildcard), include the outcome and evidence for impossible combinations. Verify every declared combination is accounted for; revisit the factor list against the business map so a complete table with a missing factor is not mistaken for full coverage. |
| State-dependent event | Name relevant object states and events; for each pair record allowed/rejected, resulting state and unchanged state when rejected. Include preparation for each initial state. |
| Role, ownership or data scope | Cross the applicable roles and operations, then vary ownership/scope where it changes permission. For denial, check both denial evidence and protected business state; do not assume a particular error message. |
| Cross-object or cross-module effect | Name trigger, shared identifier and before/after state of each affected object, plus invariants and the actual business observation location. Check after the event has settled, and include rejection/rollback effects when the confirmed rule requires them. |
| Business journey | Trace basic, alternative and failure paths through upstream prerequisites and downstream consumers. Add impacted existing journeys to regression based on dependency, not page adjacency. |

Use source-confirmed historical defects as additional rows only after checking applicability and expected result. Format preferences and terminology can improve presentation but cannot override a current rule. If a prior decision is reused as context, verify project, version, object, scope and original source; ask again when any of these differ or are unknown.

Run the derivation in both directions. From each source rule, find its model rows, leaves, cases and step-bound assertions. From each leaf/assertion, find the supporting row and current source/decision. A link means traceability, not sufficient coverage: re-read the actual conditions, alternatives and downstream effects to find absent rows. The existing six coverage dimensions are an applicability ledger; `not-applicable` needs a concrete rule-specific reason, not a shortcut for an unexamined dimension.

## Coverage techniques

For each grounded rule, assess positive and reverse paths, equivalence partitions and relevant boundaries, valid/invalid state transitions, role/ownership scope and cross-object effects. For threshold N, consider the meaningful N−1/N/N+1 states with executable setup; distinguish count before and after the action. For selections, assess empty/single/multiple and mixed eligible/ineligible only where the operation supports them. For invalid inputs, verify both the error and preservation of prior business state when required.

Walk the full flow from input through intermediate state to downstream visible outcome. Check partial success, interrupted/repeated operations and cleanup if the source or actual flow makes them relevant. Use a decision table for interacting conditions; document infeasible combinations. Pairwise selection is insufficient for a known interacting business rule. Derive regression from affected object/state/data consumers, not simply all pages or a fixed count.

When supplied, reference XMind examples can guide meaningful nesting, concise titles and concrete leaves. Obtain business rules from the current requirement; do not copy example entities, limits, permissions or outcomes into it.

Save the concrete derivations below, not only dimension labels. Required obligations must reach leaves, cases and assertions.

## Detailed case readiness

Each case needs reproducible preconditions, concrete data values or uniquely resolvable selection criteria, numbered actions and expected results, leaf and source/decision references, suites, targets, cleanup, and planned assertions. Avoid boilerplate such as “prepare valid data / operate / result correct”. Give the tester the values, states, quantities and observation locations necessary to reproduce the outcome.

For every required outcome, define a stable `AS-*` assertion with target applicability, exact `expected`, `observation`, leaf references and required evidence. Bind it to the step that produces or checks it. Check that the prose step expectation and assertion oracle express the same rule. No planned leaf may be covered only by an action without an assertion.

Automation feasibility is assessed from the specified business interactions and required evidence surface, obtainable data, deterministic observable oracle and safe repeat/reset procedure. Product code and live execution are not required to make this design assessment. Describe `candidate_route` using the intended business interaction and record its basis; do not invent verified selectors, record IDs or execution evidence.

`automatable` is feasible without unresolved project-specific design conditions; declare external inputs using `RT-*` requirements. `conditional` names unresolved route/data/reset conditions and corresponding runtime requirements. `manual` names the human judgment or unavailable capability. An environment not yet deployed does not by itself make every case conditional: record the needed build/environment as runtime requirements. A missing business decision that changes the expected result must be clarified before finalizing the case, rather than hidden in an automation condition. Executor verifies actual readiness after deployment; an automatable label does not claim a successful run.

Before finalizing, audit for invented rules, duplicated generic cases, bundled leaves, wrong states, untested reverse outcomes, unsupported “automatable” labels and affected flows missing regression. Validators cannot perform this semantic review.

## Concrete derivation records

These are AI-maintained records in context schema 1.4. Choose techniques from each confirmed rule and risk, without requiring every technique for every project. Extract `requirement_items` first, then assess applicability and inventory `FAC-*` condition values from those facts. Sources/decisions belong to the parent rule; `rationale` explains method selection and scope. A scenario model suffices for a simple independent outcome. Interacting conditions need a decision table; a scenario label must not conceal combinations.

Each included rule has `design_models`. A model has `DM-*`, `method`, `rationale`, and `items`. Every item has `COV-*`, `dimensions`, concrete `condition/action/expected`, repeatable `setup`, `disposition`, `requirement_refs`, `factor_values`, `outcomes` and `test_point_refs`. Each factor value is one scalar from the corresponding `FAC-*`; combining several distinct category values into a list in one assignment is invalid. Assign every factor whose dimension this row exercises. Separate values when they create distinct behavior, preparation or paths. For decision tables only, a null value may represent an outcome-invariant wildcard when it matches `assignment` and has a source-grounded `reason`; this does not authorize combining different outcomes.

Each required item's `outcomes` enumerates independently observable business predicates as `{id: OUT-*, subject, observable, expected}`. Split different properties/fields/states even within the same object. Collection cardinality, the complete identity-to-attribute mapping, an aggregate invariant and an entity status are separate checks when the current rule requires them. Equal totals alone cannot prove that each member has the correct identity, association or value. A collection outcome must name the full set and a complete per-member oracle; a representative sample cannot prove it. Each outcome has exactly one linked leaf per item; the leaf's `outcome_ref` selects it, and its `verification` retains the row's condition/action plus that outcome's exact expected text. Different models may reuse the same outcome ID/leaf only for identical condition, action, assignment and outcome. Setup is preparation, not an outcome.

Before leaves exist, keep every `test_point_refs` empty and run `freeze-coverage-plan`. The frozen digest includes applicability, representatives, method rows and outcomes. Add leaf links afterward. Missing representatives, changed applicability or removed outcomes cannot be repaired by merely rewriting coverage from the smaller case list. Revise the plan explicitly and rerun source-first review. Excluded items have a source-grounded `reason`, no outcomes and no leaves; unavailable runtime setup alone does not make a business combination infeasible.

Every leaf has `coverage_item_refs` and one `outcome_ref`. A case can contain several leaves, with a distinct step-bound assertion for each. Mutually exclusive types/paths must remain independently reviewable case variants, each with its own data and expected results; their eventual test code may share a parameterized implementation. Do not use `evidence-review` to combine independent numeric, state and binding results into one assertion. Use deterministic comparisons for exact confirmed values; reserve evidence review for genuinely semantic/visual criteria.

Copy the leaf's canonical `verification.expected` into its assertion's `expected`; put case-specific comparison values in `check.expected_value` and subject/location details in `observation` and test data. Final export rejects a changed assertion expectation that was not reconciled with the point baseline. A pending Excel import can retain such an edit for review, without making it executable.

| Method | Save actual derivation data |
| --- | --- |
| `scenario` | Concrete setup, condition, action and observable result; explain why other techniques add no applicable obligations. |
| `equivalence-partition` | Each item's `partition` and representative `data`; split valid/invalid classes from the rule, rather than using one generic abnormal input. |
| `boundary` | Model `field` and `bounds`: `id`, decimal `value`, positive `resolution`, `basis`. Each item has `boundary_ref`, `value`, actual data/setup and expected outcome. Cover immediately below/on/above each limit at the supported resolution; identify inclusive/exclusive semantics. For dates/length/counts, explain the business unit and any numeric coordinate conversion in `basis`; preserve actual input in `data`. Missing limits or precision are questions, not guessed numbers. |
| `decision-table` | `factors` maps named conditions to distinct string domains. Every item has a full `assignment`; null covers all values of that factor only when outcome is invariant. Save each outcome or explicit infeasibility reason. Rows must be disjoint and collectively cover the declared domain product. Split the model by coherent interacting rule if the table grows too large; do not drop known interactions with pairwise sampling. |
| `state-transition` | `object_ref`, relevant declared `states`, `events`; items specify `from/event/to` and rejection or acceptance behavior. Cover each declared state/event pair, including forbidden pairs and preserved state. Explain relevant scope and setup for each state. Do not invent states from an assumed implementation. |
| `permission` | Relevant `roles`, `operations`; items have `role/operation`, ownership or data scope in condition, and allowed/denied observable outcome. Cover every declared pair. Add separate models/items when ownership changes the decision. |
| `cross-object` | Item `effects` identifies at least two grounded objects with `object_ref/before/after`, including values that must remain unchanged. Explain causal links, identifiers and observation locations through rule/model/setup; check the downstream result after the business event completes. |

Required boundary/state/role/cross-object dimensions need corresponding concrete models. A dimension's leaf list must equal its derived items' leaf links. Decision-table checks prove coverage only of declared factors; they cannot detect an omitted business factor. Matrix checks do not prove states/roles are complete. Source comparison and tester confirmation remain necessary.

A rule with `kind=transition` may describe a single transition via `transition`, or use a complete `state-transition` design model. A matrix does not need a duplicate top-level from/to pair. Source-explicit facts may have `status=confirmed` while the context review and XMind are still draft; `assumed` means an actual disclosed inference, not merely waiting for tree review. Keep review status/timestamp and the manifest's explicit tester-confirmed point baseline separate; never invent a confirmation response.

### Semantic review

Review three distinct questions: is the expected behavior grounded in the current source/decision, have all relevant variants been derived, and could another tester perform and judge the case? A correct reference ID, nonempty field or complete matrix over an incomplete factor list cannot answer these questions. Read the actual supporting clause for each rule/leaf; never bulk-copy a module's decision list onto unrelated leaves. Shared business conditions can justify shared references; actual semantic support is still required.

Before any XMind rendering, record `test-points.design_review`: `snapshot_sha256`, all `checked_leaf_refs`, an `atomicity_note` describing the independent predicates and repaired merges, and a `visible_path_note` describing the condition/action/result readability review. `<qa-tool> design-review-digest <test-points.json>` returns the current fingerprint without approving anything; a draft may start with `design_review={}`. Review every leaf's visible path and compare its oracle with its precise derivation/source. Changes to titles, leaves, decisions or context binding invalidate this review. Inspect exported topics/notes after rendering; semantic audit is also required for `--draft` trees. Rendering alone is not tester confirmation.

Before final Excel export, record `review.case_checks` for every case: `case_id`, `snapshot_sha256`, `walkthrough`, `oracle_basis`, and `suite_reason`. Obtain fingerprints using `<qa-tool> design-review-digest <test-manifest.json>`. `walkthrough` describes the actual preparation/data/action/check sequence verified and repairs, `oracle_basis` ties typed comparisons and prose expectations to specific confirmed leaves/rules, and `suite_reason` explains risk/criticality/change impact. Do not generate identical “checked” notes for all cases. A source-only field limit needs no invented roles or downstream effects; a coupled business operation needs applicable effects and preservation checks. Case fingerprints include baseline, inputs, steps, assertions, target/automation conditions and suite allocation, so edits require fresh review. The tool checks record freshness, not the truth of the prose.

The actual tester confirmation of the displayed XMind belongs in `test_points_baseline.response_ref/response_text`, alongside its hash/timestamp. An agent review or timestamp alone cannot supply that response. When a correction changes the tree, obtain confirmation of the current version before final cases.

For context and manifest, `review.checks` records `source-fidelity`, `coverage`, `executability`, `oracle-consistency` only after actually performing them. Begin with original source and decisions, enumerate their clauses/variants before consulting generated points/cases, and compare the inventories in both directions. In context, retain every origin's `source_checks` and the audited `plan_sha256` described in [design context](design-context.md). Check reverse outcomes, affected relationships and unchanged invariants; walk each case's data/setup/actions/assertions; compare all representations of the expected result. A complete matrix over an incomplete factor list fails this semantic audit even if its combinatorial validation succeeds.

`review.findings` records concrete issues with `id`, category, `scope_refs`, description, `status=open/resolved`, and a `resolution` when resolved. If no issue was found, an empty list is truthful; do not manufacture findings or claim a second independent reviewer. Final review rejects open findings. A resolution that changes a material business rule needs tester/owner confirmation recorded in decisions. Validation proves record consistency, not semantic correctness. After an Excel business edit, repeat checks for the new baseline; prior finding history is retained.

### Frozen comparisons

Manifest `assertion.check` has `kind`, `timing`, and the fields required below. Observation locations are business-visible and include which subject/value to inspect. Timing states the event/settled state to wait for; invent no fixed sleep or performance limit.

- `equals`: exact typed JSON `expected_value`; text and numbers differ. Use only source-fixed wording/values.
- `contains`: nonempty text `expected_value` in observed text; narrow enough to distinguish prohibited outcomes and the intended subject.
- `number-equals` / `number-delta`: finite decimal `expected_value`; delta requires before/after observations of the same subject/location. No implicit tolerance or formatting conversion.
- `unordered-equals`: expected list, ignoring order but retaining duplicate counts; use only when order is not part of the rule.
- `unchanged`: before/after typed values of the same subject/location; no expected_value.
- `evidence-review`: objective `criteria`, no expected_value. For semantic wording or visual outcomes, Executor reads original UI output/images and gives reasoned per-attempt judgments. This is agent evidence assessment, not a deterministic numeric/text comparator. Subjective taste or unverifiable business effects remain manual.

Keep human `expected`, typed comparison, step expectation, coverage item and source rule consistent. The validator cannot infer that two natural-language formulations have the same meaning. Automation labels must name a viable business observation route preserving the required UI/interface evidence and evidence; the comparison contract alone does not create a control capability.

## Executable tester cases

First reconstruct how a tester would perform the scenario. Then write the case.

- Preconditions describe the starting environment, permissions and business state.
- Test data gives the actual input/setup values, representative boundary values or reproducible selection/seeding criteria. Do not repeat the precondition under another heading or list post-action expected results as input data; those belong in step expectations/assertions.
- Steps follow the actual interaction sequence: establish the entry state, identify the subject, supply the concrete input, trigger the business action, wait for its stated completion, and inspect each required result. Describe UI, interface, command or device interactions according to the confirmed target. Combine actions only when the operation is genuinely indivisible; do not compress a multi-interaction flow into “execute the process”.
- Each step states its expected observable result. UI navigation/selection can have a simple state check; business checkpoints must retain specific requirement-derived assertions. If the prototype lacks exact UI details, describe known semantic actions and defer concrete locators to execution rather than inventing buttons.
- Cover applicable cross-module success and rejection effects through their confirmed business observation surfaces. Independent leaves may be asserted in one coherent end-to-end case; alternative mutually exclusive paths need separate cases or explicit parameter rows with their own expected outcomes.
- Negative cases name the concrete invalid input/state/role and its rejection/preservation checks. Boundary cases give below/on/above data from the confirmed bound; never copy a combined “empty or too large” expectation.
- State preparation and cleanup must be reproducible in the declared test environment. Unknown runtime record IDs are not missing business requirements, but unavailable required data setup makes automation conditional.
- Choose smoke for essential critical business journeys; regression for impacted and related existing behavior, permissions and data dependencies; full for all reviewed coverage. Do not classify by a fixed percentage or remove manual cases from the human suite files.

Semantic review should walk every case, with particular attention to success, rejection, boundary, permission and cross-module variants from their steps alone. For each, hide the title and notes while reading the preparation/data/steps/step expectations and ask whether another tester can reproduce the starting state, perform each action, know when to inspect, and judge every `AS-*`. Record a concrete missing instruction/oracle/data issue and repair it; do not just mark the checklist completed. One-step cases are acceptable for a genuinely single operation, not as a quota or export shortcut.

### Derivation pattern: state, authorization and related effects

Apply this pattern only when the current requirement defines state-dependent authorization or effects on related entities. Bind the operation, entity names, states, actor scope, identifiers and expected changes to actual source clauses or confirmed decisions. No particular business domain, approval process, role name or relationship is assumed.

Before deriving rows, establish the permitted starting states and actor scopes, the operation's success and rejection behavior, repeat-operation behavior where relevant, each affected entity's before/after values, and the business observation locations. Clarify any missing expected result. Choose the relevant state, permission, decision-table and cross-object models from those confirmed facts.

| Source-confirmed condition | Derivation obligation |
| --- | --- |
| Operation is permitted in the prepared state and scope | Record each independent resulting state, association or value as a separate outcome. |
| Operation is denied because the actor is outside the permitted scope | Record the confirmed denial observation and each protected state/value required to remain unchanged. |
| Operation is unavailable in the prepared state | Record the confirmed rejection and preservation behavior for that state. |
| Multiple conditions interact | Enumerate the applicable combinations and source-grounded infeasibility reasons; do not assume that a state rule settles permission behavior. |

Include only conditions supported by the current requirement. The table identifies how to derive coverage; it does not define product permissions, states or expected values. A rejection branch cannot be created merely because it appears in this pattern.

For a required scenario, identify a reproducible setup/reset method and a uniquely selectable primary entity with its relevant related entities. Use concrete starting values and the actual eligible actor. Write ordered steps to verify the starting state, capture any required before-values, perform the operation, observe its confirmed completion, and inspect each affected entity at its business observation location. Bind each independent result to its own leaf and step-bound `AS-*` assertion. Restore the prepared data through the declared cleanup method; if that method is not available, record the runtime condition.

One coherent case may cover several independent outcomes. Different initial states, actor scopes or action paths require separately reproducible cases even when some final values are equal. Group leaves by the project's actual entity, operation and decisive condition; avoid filler levels or a single “operation result correct” leaf.

### Derivation pattern: one bounded field

Apply this pattern when the current requirement defines a field limit. Establish the field, bound, inclusivity, measurement unit, supported precision, empty-value behavior, rejection observation and saved-state behavior. A length unit may be bytes, code points or user-perceived characters; use the confirmed definition. Do not infer a numeric limit, Unicode policy, error message or preservation rule from a reference example.

Let the confirmed upper bound be `N` and the smallest meaningful increment be `d`. Derive rows immediately below, at and above that bound: `N-d`, `N` and `N+d`, with separate expected results from the confirmed inclusion rule. Derive any other bounds similarly. Assess empty input as a separate partition with its confirmed outcome. These symbols explain the technique; replace them with actual values, units and reproducible input data before freezing coverage or exporting cases.

For accepted input, identify the confirmed persisted or otherwise observable value. For rejected input, keep the rejection observation separate from any required preservation check. Prepare a uniquely selectable test entity with a known prior value, enter the concrete boundary input, submit through the applicable interaction surface, observe the result at the specified completion point, and inspect the saved value when required. Bind rejection and preservation to separate assertions and use the declared reset method for cleanup.

The visible tree needs only the meaningful field/operation/condition levels. No fixed depth or number of cases follows from this pattern.

| Rough draft | Repair |
| --- | --- |
| `Exception testing → State validation → Correct result` | Name the confirmed condition, action and one observable outcome; split any independent related-entity checks. |
| `Empty or over-limit input fails validation` | Separate empty and boundary rows; derive each outcome from the confirmed rule instead of assuming both fail. |
| `Prepare data → Perform operation → Correct result` | Specify the starting subject, concrete input, ordered actions, completion condition, observation location and `AS-*` expected value. |
| `One case is linked, so the rule is covered` | Compare every applicable derivation row with leaves and step-bound assertions, including relevant states, scopes and related-entity invariants. |
