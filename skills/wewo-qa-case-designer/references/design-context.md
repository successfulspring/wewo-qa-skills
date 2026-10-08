# Business understanding and coverage

Use `schemas/design-context.schema.json`. This model preserves why the test tree contains each branch; it is an internal handoff artifact, not extra documentation testers must author manually.

## Build a whole-business draft first

Describe business objects and states, actor roles, the main end-to-end flow, ownership and cross-object dependencies. Include existing behavior that this change relies on or can affect. Ground it in readable requirements, prototypes, existing business documentation and tester or product-owner confirmations. Mark unknowns instead of guessing conventional rules.

Then refine coherent units in dependency order. When a unit changes a rule, revisit upstream prerequisites and downstream effects in the map. An unchanged page can still need regression when its data, permissions or states change.

Pure project context belongs in source segments/objects/relationships, with its reading disposition and note; it does not require a fabricated standalone test leaf. Requirement units describe testable behavior and may cite that context. A source section title alone is not a requirement unit with coverage obligations.

## Design evidence before implementation

Product source code is unavailable during case design. Do not request or inspect product code, repository internals, database schemas or implementation details to complete the business model. A test-artifact working folder is sufficient; a project repository and a running new feature are not required.

Existing test cases, defect records and supplied observations of an older product can identify dependencies and risks. Check their version and applicability; they do not automatically define the new requirement. A prototype describes intended behavior, not a verified implementation. Confirm material gaps in roles, states or cross-module effects with the tester or responsible owner, while continuing independent closed units.

Define expected results from confirmed rules before execution. Use business-visible observation locations and concrete data values or resolvable setup criteria. Actual selectors, available records, runtime sessions and implemented routes are checked by Executor after deployment. Do not claim these were exercised during generation or derive an expected result from what the implementation happens to do.

## Contract

- `sources`: provenance and scope plus `inventory_status`, `method`, and `reason` for incomplete/excluded material.
- `segments`: stable source anchors, actual content, reading status and disposition. Non-requirement dispositions need `review_note`.
- `decisions`: the same full decisions used in `test-points.json`, including unit/question references. Do not shorten the decision ledger here.
- `objects`: `OBJ-*`, description, states and grounded segment references. Include explicit roles in applicable rule conditions.
- `relationships`: `REL-*`, from/to objects, meaning and rule references. These describe actual business effects, not merely links between pages.
- `flows`: `FLOW-*`, ordered rule references and a visible business outcome.
- `rules`: `RULE-*`, condition, action, expected outcome, objects, source segment or decision references, confirmed/assumed/excluded status, optional state transition, coverage disposition and concrete `design_models` from [method records](method-records.md).
- `open_questions`: describe material unresolved facts. A final model cannot have an unresolved material question.
- `review`: draft/confirmed, confirmation timestamp, performed checks, findings and resolutions for the completed model.

Each rule has exactly six coverage entries: `positive`, `negative`, `boundary`, `state`, `role`, `cross-object`. `required` entries identify concrete leaf IDs; `not-applicable` entries explain why. Do not manufacture a boundary for a rule without a range, count, temporal limit or discrete partition. Do not apply an unrelated generic state template to a field.

A rule's coverage can refer to a leaf in another module or in an end-to-end branch. Grouping nodes do not count as coverage. State transitions must use known object states. Every relationship and flow must reference included, grounded rules. Every included requirement segment must have a rule; every included rule must have leaves.

## Review evidence

The tester confirms the interpreted rules through the progressive dialogue and final tree review. The agent performs a final semantic audit before setting `review.status=confirmed`; retain the facts, accepted assumptions and decisions that support it. `validate-design-context --draft` supports incomplete work; final validation requires closed coverage and reading gaps.

The validator proves references and declared coverage are consistent. It cannot prove that a relationship was understood correctly, that a leaf is truly atomic, or that a source was fully interpreted. Verify those against the original and the company's examples before confirming.
