# Business understanding and coverage

Use `schemas/design-context.schema.json`. This model preserves why the test tree contains each branch; it is an internal handoff artifact, not extra documentation testers must author manually.

## Build a whole-business draft first

Describe the goal, in/out scope and existing context, then business objects and their identifiers/states, actor roles and ownership/data scope, the main end-to-end flow with alternative and failure paths, and cross-object dependencies. For each important operation, trace input and prior state → actor/trigger → changed object/state/data → downstream consumer and observable location → invariants that must remain unchanged. Include existing behavior that this change relies on or can affect. Ground each link in readable requirements, prototypes, existing business documentation and tester or product-owner confirmations. Mark unknown links rather than guessing conventional rules. A document's page/menu headings are source anchors, not the only business decomposition.

Then refine coherent units in dependency order: shared object/state/permission rules before the operations that consume them, and upstream changes before downstream outcomes. When a unit changes a shared rule, revisit every related `relationship`, `flow` and dependent rule, including rejection invariants and existing paths. An unchanged page can still need regression when its data, permissions or states change. Use `objects`, `relationships`, `flows` and `rules` for this trace; do not create a parallel business-map file.

Pure project context belongs in source segments/objects/relationships, with its reading disposition and note; it does not require a fabricated standalone test leaf. Requirement units describe testable behavior and may cite that context. A source section title alone is not a requirement unit with coverage obligations.

## Extract clauses before designing coverage

Keep `segments.content` as actual anchored text, or a faithful verified transcription of pictures/tables/flows. Preserve cell headings, conditions, notes and relations. Split large material into readable anchored segments; a compressed module overview cannot replace the source. Reading caches remain private.

Account for all non-whitespace content in every read, included segment and every active decision's `resolution` using `requirement_items`. Each `REQ-*` has `origin_ref` (`SEG-*` or `DEC-*`), zero-based Unicode character offsets `start/end` (end exclusive), a precise `statement`, `disposition`, and `rule_refs`. Offsets refer to the stored source string, not bytes or a paraphrase. Spans cannot overlap; separating whitespace may remain outside them. Split semantically: distinct operations, type-dependent requirements, exceptions and independent results need their own entries. Several entries may support one rule for the same trigger.

`requirement` entries have reciprocal links to included rules that also cite their origin. `context` and `excluded` entries have no rule links and a source/decision-grounded reason. `pending` records an ambiguity and needs a reason; resolve it through dialogue. Include exclusions in the final requirement summary. Do not classify inconvenient behavior as context or combine an entire paragraph into one item to conceal a clause. Span checks catch unaccounted recorded text; semantic rereading detects falsely broad items and missing source extraction.

## Design evidence before implementation

Product source code is unavailable during case design. Do not request or inspect product code, repository internals, database schemas or implementation details to complete the business model. A test-artifact working folder is sufficient; a project repository and a running new feature are not required.

Existing test cases, defect records and supplied observations of an older product can identify dependencies and risks. Check their version and applicability; they do not automatically define the new requirement. A prototype describes intended behavior, not a verified implementation. Confirm material gaps in roles, states or cross-module effects with the tester or responsible owner, while continuing independent closed units.

Define expected results from confirmed rules before execution. Use business-visible observation locations and concrete data values or resolvable setup criteria. Actual selectors, available records, runtime sessions and implemented routes are checked by Executor after deployment. Do not claim these were exercised during generation or derive an expected result from what the implementation happens to do.

## Contract

- `project.output_language`: the current delivery language (`zh-CN` or `en`), selected by the [delivery language policy](artifact-contract.md#delivery-language) and shared by the context, point baseline and case manifest. Missing legacy values mean `zh-CN`.
- `sources`: provenance and scope plus `inventory_status`, `method`, and `reason` for incomplete/excluded material.
- `segments`: stable source anchors, actual content, reading status and disposition. Non-requirement dispositions need `review_note`.
- `decisions`: complete dialogue-backed decision history, including superseded decisions; only current decisions project into `test-points.json`.
- `requirement_units`, `dialogue_events`, `branch_reviews`, `requirement_review`: canonical discovery state and requirement-only gates in [requirement readiness](requirement-readiness.md).
- `requirement_items`: clause-by-clause source/decision extraction and reciprocal rule links.
- `objects`: `OBJ-*`, description, states and grounded segment references. Include explicit roles in applicable rule conditions.
- `relationships`: `REL-*`, from/to objects, meaning and rule references. These describe actual business effects, not merely links between pages.
- `flows`: `FLOW-*`, ordered rule references and a visible business outcome.
- `rules`: `RULE-*`, condition, action, expected, objects, source segment/decision and `requirement_refs`, status, optional transition, `factors`, coverage dispositions and concrete `design_models` from [concrete derivations](test-design.md#concrete-derivation-records).
- `coverage_plan`: draft/frozen, with tool-generated timestamp and digest of requirements, applicability, factors, scenarios and outcomes, excluding later leaf links.
- `open_questions`: describe material unresolved facts. A final model cannot have an unresolved material question.
- `review`: draft/confirmed, confirmation timestamp, performed checks, findings and resolutions for the completed model.

Each rule has exactly six coverage entries: `positive`, `negative`, `boundary`, `state`, `role`, `cross-object`. Assess applicability before deriving scenarios, with `basis_refs` to that rule's `REQ-*` and a reason specific to this dimension and rule. `pending` is allowed during discovery, with no leaves; it blocks freezing/finalization. `required` entries receive leaf IDs only after freezing. `not-applicable` needs factual absence, a confirmed restriction or accepted exclusion; lack of generated scenarios, code access or runtime setup is not evidence of inapplicability. Do not manufacture boundaries or unrelated generic state/role templates.

Each `FAC-*` records a meaningful condition `name`, coverage `dimension`, representative `values` and `basis_refs`. Inventory it from source clauses and decisions, independently of already written examples. Every value needs a derived row or a grounded excluded row. A confirmed exception to a default format or validation rule needs its own representative; an example exercising only the default rule cannot establish exception coverage. Unknown expectations require clarification.

A rule's coverage can refer to a leaf in another module or an end-to-end branch. Grouping nodes do not count. State transitions use known object states. Relationships and flows reference grounded rules. Every included requirement clause has a rule; every included rule and planned independent outcome has leaf coverage.

## Review evidence

After final requirement confirmation, derive rows/outcomes with empty leaf links and run `freeze-coverage-plan`. It checks closed extraction, applicable derivations and factor representatives before storing the plan digest. Then attach leaves. Changing leaf links leaves the plan unchanged; changing factors, scenarios, applicability or outcomes invalidates it. For a revision, preserve evidence, clear the candidate's leaf links, reopen affected questions/confirmations, refreeze, regenerate and reconfirm the affected tree. Never stamp human approval or recalculate the plan hash by hand to bypass this order.

Before setting `review.status=confirmed`, reread sources and decisions first, without using generated cases as the inventory. Record `review.source_checks` for every included origin: `origin_ref`, SHA-256 of its UTF-8 content, all its `requirement_refs`, and a substantive `note` on clause completeness and relevant variants. Record omissions/over-merges and repairs in existing findings. Set `review.plan_sha256` to the audited plan digest. A stale/missing origin audit or plan review blocks finalization. `validate-design-context --draft` supports incomplete work; XMind review drafts already require a frozen plan.

Validation checks recorded-text accounting, representatives, frozen obligations, separate outcome links and audit freshness. It cannot prove complete source transcription, semantic atomicity or actual review performance. Verify these against the original and applicable company examples before confirming. Examples establish presentation/granularity standards, not undocumented product rules.
