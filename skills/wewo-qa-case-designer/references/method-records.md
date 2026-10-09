# Concrete derivation records

These are AI-maintained records in context schema 1.2. Choose techniques from each confirmed rule and risk, without requiring every technique for every project. Sources/decisions belong to the parent rule; `rationale` explains method selection and declared scope. A scenario model is sufficient for a simple independent outcome. Interacting conditions need a decision table; a scenario label must not conceal their combinations.

Each included rule has `design_models`. A model has `DM-*`, `method`, `rationale`, and `items`. Every item has `COV-*`, `dimensions`, concrete `condition/action/expected`, repeatable `setup`, `disposition` and `test_point_refs`. Required items link to atomic leaves. Excluded items have a source-grounded `reason` and no leaves; unavailable setup alone is a runtime limitation, not proof a combination is infeasible. Every leaf has `coverage_item_refs`. Mutually exclusive values/rows from the same model must use separate leaves. Several independently observable outcomes of one row may have separate leaves.

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

## Semantic review

For context and manifest, `review.checks` records `source-fidelity`, `coverage`, `executability`, `oracle-consistency` only after actually performing them. Re-read source and decisions; check reverse outcomes, affected relationships and unchanged invariants; walk each case's data/setup/actions/assertions; compare all representations of the expected result.

`review.findings` records concrete issues with `id`, category, `scope_refs`, description, `status=open/resolved`, and a `resolution` when resolved. If no issue was found, an empty list is truthful; do not manufacture findings or claim a second independent reviewer. Final review rejects open findings. A resolution that changes a material business rule needs tester/owner confirmation recorded in decisions. Validation proves record consistency, not semantic correctness. After an Excel business edit, repeat checks for the new baseline; prior finding history is retained.

## Frozen comparisons

Manifest `assertion.check` has `kind`, `timing`, and the fields required below. Observation locations are business-visible and include which subject/value to inspect. Timing states the event/settled state to wait for; invent no fixed sleep or performance limit.

- `equals`: exact typed JSON `expected_value`; text and numbers differ. Use only source-fixed wording/values.
- `contains`: nonempty text `expected_value` in observed text; narrow enough to distinguish prohibited outcomes and the intended subject.
- `number-equals` / `number-delta`: finite decimal `expected_value`; delta requires before/after observations of the same subject/location. No implicit tolerance or formatting conversion.
- `unordered-equals`: expected list, ignoring order but retaining duplicate counts; use only when order is not part of the rule.
- `unchanged`: before/after typed values of the same subject/location; no expected_value.
- `evidence-review`: objective `criteria`, no expected_value. For semantic wording or visual outcomes, Executor reads original UI output/images and gives reasoned per-attempt judgments. This is agent evidence assessment, not a deterministic numeric/text comparator. Subjective taste or unverifiable business effects remain manual.

Keep human `expected`, typed comparison, step expectation, coverage item and source rule consistent. The validator cannot infer that two natural-language formulations have the same meaning. Automation labels must name a viable business observation route preserving the required UI/interface evidence and evidence; the comparison contract alone does not create a control capability.
