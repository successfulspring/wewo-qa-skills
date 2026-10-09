# Test-point granularity and executable cases

## Stop by verifiability, not depth

Organize branches around the business flow/object and rule, then split by relevant operation, state/role, input partition and outcome. Use only levels that add meaning. A branch ends when the leaf specifies one concrete condition, one trigger and one independently judgeable outcome. Depth varies with complexity; do not force three/four levels or pad every branch to a fixed depth.

Split a leaf when it contains separable combinations, alternatives, independent validations or multiple states. Each resulting leaf carries `rule_refs`, `coverage_item_refs` and `verification={condition, action, expected}`. Setup is not a test point. Several checks proving one indivisible business outcome may remain together; independently observable outcomes need separate leaves. One case may verify several leaves as an explicit business flow.

Audit the entire visible path, not just the leaf's JSON. The current XMind renderer displays each node's `title` and puts `verification` in its note, so a hidden `expected` does not repair a vague visible topic. A parent must name a real business object, operation, rule or decisive condition; it must not be a chain of `precondition → step → expected` fields. Read the parent titles plus the leaf title as a sentence: can a tester identify the specific condition, trigger and business result without opening notes? Put the decisive missing words in the title or an immediately visible parent, and keep detailed source/derivation in the note. If a parent says only “状态校验/异常测试” or a leaf says “结果正确/正常处理”, rewrite it. A shallow branch is correct when it already passes this audit.

For each candidate leaf, ask: (1) can the condition hold in more than one relevant state, role, data range or mutually exclusive path? (2) can the trigger produce two independently judged results, including a rejection and an unchanged related object? (3) does a derived model row still lack its own outcome? Split on the specific difference and re-run the audit until each obligation has a leaf. Do not split merely to increase depth, count or title length. Do not merge cases solely because two different states, actors or operations have the same final text; merge only when the preparation, path and obligations are genuinely equivalent and each required assertion remains visible.

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

## Select and derive coverage techniques

Start from each confirmed `RULE-*` and the whole-business map. For each applicable method, record the rule/source or decision, why the method applies, concrete rows in existing `design_models/items`, and each row's disposition. Do not require every method for every rule. A risk checklist yields an applicability decision or a clarification question, not an automatic business expectation. Check historical defects and common risks such as repeated submission, second confirmation, upload limits, interruption and downstream stale data only where this operation can encounter them; confirm their expected behavior from current source/project rules before making them required coverage.

| Confirmed rule shape | Derivation to perform before writing leaves |
| --- | --- |
| Required field, format, range or enumeration | Partition by *different expected behavior*, label valid/invalid classes, give each representative input and expected acceptance/rejection. Separate empty from over-limit or wrong-format when they have distinct causes. Do not claim every syntactic variation needs a new case without an applicable rule/risk. |
| Numeric, length, amount or time limit | Identify the exact limit, whether equality is included, the business unit and smallest meaningful change. Record below/on/above data and the result for each. A calendar day, character count, currency cent and stock unit are not interchangeable. Unknown precision or exclusivity is a material question. |
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

Company XMind examples guide meaningful nesting, concise titles and concrete leaves. They are not evidence that every example rule belongs in this project.

Save the concrete derivations below, not only dimension labels. Required obligations must reach leaves, cases and assertions.

## Detailed case readiness

Each case needs reproducible preconditions, concrete data values or uniquely resolvable selection criteria, numbered actions and expected results, leaf and source/decision references, suites, targets, cleanup, and planned assertions. Avoid boilerplate such as “prepare valid data / operate / result correct”. Give the tester the values, states, quantities and observation locations necessary to reproduce the outcome.

For every required outcome, define a stable `AS-*` assertion with target applicability, exact `expected`, `observation`, leaf references and required evidence. Bind it to the step that produces or checks it. Check that the prose step expectation and assertion oracle express the same rule. No planned leaf may be covered only by an action without an assertion.

Automation feasibility is assessed from the specified business interactions and required evidence surface, obtainable data, deterministic observable oracle and safe repeat/reset procedure. Product code and live execution are not required to make this design assessment. Describe `candidate_route` using the intended business interaction and record its basis; do not invent verified selectors, record IDs or execution evidence.

`automatable` is feasible without unresolved project-specific design conditions; declare external inputs using `RT-*` requirements. `conditional` names unresolved route/data/reset conditions and corresponding runtime requirements. `manual` names the human judgment or unavailable capability. An environment not yet deployed does not by itself make every case conditional: record the needed build/environment as runtime requirements. A missing business decision that changes the expected result must be clarified before finalizing the case, rather than hidden in an automation condition. Executor verifies actual readiness after deployment; an automatable label does not claim a successful run.

Before finalizing, audit for invented rules, duplicated generic cases, bundled leaves, wrong states, untested reverse outcomes, unsupported “automatable” labels and affected flows missing regression. Validators cannot perform this semantic review.

## Concrete derivation records

These are AI-maintained records in context schema 1.2. Choose techniques from each confirmed rule and risk, without requiring every technique for every project. Sources/decisions belong to the parent rule; `rationale` explains method selection and declared scope. A scenario model is sufficient for a simple independent outcome. Interacting conditions need a decision table; a scenario label must not conceal their combinations.

Each included rule has `design_models`. A model has `DM-*`, `method`, `rationale`, and `items`. Every item has `COV-*`, `dimensions`, concrete `condition/action/expected`, repeatable `setup`, `disposition` and `test_point_refs`. Required items link to atomic leaves. Excluded items have a source-grounded `reason` and no leaves; unavailable setup alone is a runtime limitation, not proof a combination is infeasible. Every leaf has `coverage_item_refs`. Mutually exclusive values/rows from the same model must use separate leaves. Several independently observable outcomes of one row require separate leaves; they may be checked in one coherent case with distinct assertions.

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

For context and manifest, `review.checks` records `source-fidelity`, `coverage`, `executability`, `oracle-consistency` only after actually performing them. Re-read source and decisions; check reverse outcomes, affected relationships and unchanged invariants; walk each case's data/setup/actions/assertions; compare all representations of the expected result.

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
- Steps follow the actual interaction sequence: open the relevant entry, locate the target record, supply fields/selections, trigger the business action, wait for its stated completion, and inspect each required result. Combine actions only when the operation is genuinely indivisible; do not compress a multi-page flow into “execute the process”.
- Each step states its expected observable result. UI navigation/selection can have a simple state check; business checkpoints must retain specific requirement-derived assertions. If the prototype lacks exact UI details, describe known semantic actions and defer concrete locators to execution rather than inventing buttons.
- Cover cross-module success and rejection effects, not merely the final screen. Independent leaves may be asserted in one coherent end-to-end case; alternative mutually exclusive paths need separate cases or explicit parameter rows with their own expected outcomes.
- Negative cases name the concrete invalid input/state/role and its rejection/preservation checks. Boundary cases give below/on/above data from the confirmed bound; never copy a combined “empty or too large” expectation.
- State preparation and cleanup must be reproducible in the declared test environment. Unknown runtime record IDs are not missing business requirements, but unavailable required data setup makes automation conditional.
- Choose smoke for essential critical business journeys; regression for impacted and related existing behavior, permissions and data dependencies; full for all reviewed coverage. Do not classify by a fixed percentage or remove manual cases from the human suite files.

Semantic review should simulate executing representative success, rejection, boundary, permission and cross-module cases from their steps alone. For each, hide the title and notes while reading the preparation/data/steps/step expectations and ask whether another tester can reproduce the starting state, perform each action, know when to inspect, and judge every `AS-*`. Record a concrete missing instruction/oracle/data issue and repair it; do not just mark the checklist completed. One-step cases are acceptable for a genuinely single operation, not as a quota or export shortcut.

### Worked derivation A: linked state, role and inventory effects (synthetic)

This is a method example, **not a Wewo rule or a real tester confirmation**. Raw requirement: “审批调拨单后更新两个仓库库存。” Before design, ask which state permits approval, whose permission applies, how quantity is counted, what happens to both warehouses on approval/denial, how the same transfer is identified, and which business view shows inventory. For the example alone, suppose a simulated tester confirms: only a manager responsible for the source warehouse may approve a pending transfer; approving quantity 2 changes source available stock 5→3, destination available stock 1→3 and transfer state pending→approved; attempts by a manager outside that scope are rejected, with transfer and both stocks unchanged. A previously approved transfer cannot be approved again and remains unchanged. No message wording is fixed. These synthetic answers would require real confirmation in a live task.

Record an applicable decision table for `state={pending,approved}` × `manager scope={source,other}` with action `approve`:

| State | Scope | Result and required observation |
| --- | --- | --- |
| pending | source | approval accepted; transfer approved; source 5→3; destination 1→3 |
| pending | other | approval rejected; transfer pending; both stocks unchanged |
| approved | source | repeat rejected; transfer approved; both stocks unchanged from prepared values |
| approved | other | approval rejected; transfer approved; both stocks unchanged from prepared values |

The 5/1 starting stocks apply only to the prepared pending success row. Record state/event and permission rows where applicable, and a `cross-object` item with the transfer ID and both warehouses' before/after values plus their inventory views. `COV-*` rows link to leaves such as “待审批＋来源仓负责人审批 → 调拨单变已批准”, “待审批＋来源仓负责人审批 → 来源仓可用库存 5→3”, “待审批＋来源仓负责人审批 → 目标仓可用库存 1→3”, “待审批＋非负责人审批被拒 → 调拨单仍待审批”, and separate leaves for source/destination stock staying unchanged. A generic “审批结果正确” leaf loses these independent checks. Group by `调拨单审批` and meaningful state/scope parents; no layer is added just to show fields.

One approval case can cover the three success leaves. In this synthetic environment, prepare the named resettable dataset `T-A2` through its tester data console: one pending transfer `T` from warehouse A to B, quantity 2, A available 5, B available 1, and a manager account responsible for A. Select `T` by its unique dataset tag and verify the initial values before acting. Data: transfer ID `T`, warehouse IDs A/B, quantity 2, starting values 5/1. Steps: (1) open `T` as that manager and confirm its pending state, quantity and A/B identifiers; (2) record A=5 and B=1 in the business inventory views; (3) approve `T` and wait for the operation's settled state; (4) reopen `T` and check approved; (5) inspect A and B inventory views and check 3/3. `AS-*` assertions separately bind transfer state, A delta −2 and B delta +2 to steps 4/5 and the three leaves. Clean up by restoring dataset `T-A2` through the tester console and checking the initial stocks; if a real task lacks a repeatable reset, record a runtime condition. The scope-denial and repeat paths need their own preparations and cases because the action route/starting state differs, even though both leave stock unchanged.

### Worked derivation B: one short field rule (synthetic)

Raw requirement: “备注最多 10 字。” Clarify whether blank is allowed, what counts as one character, whether 10 is inclusive, how rejection is shown, and what remains after a rejected save. Suppose the simulated answer is “blank allowed; count Unicode characters; 10 included; 11 produces a visible over-limit rejection without changing the saved remark; exact wording is not fixed.” Record a boundary model with unit one character and rows 9 (`甲乙丙丁戊己庚辛壬`), 10 (`甲乙丙丁戊己庚辛壬癸`) and 11 (`甲乙丙丁戊己庚辛壬癸子`), each with its own expected saved value or rejection/preservation; an equivalence row covers blank as an allowed input. The visible leaves can sit directly under `备注保存`, for example “空备注保存 → 再打开仍为空”, “9 字备注保存 → 再打开仍为输入值”, “10 字备注保存 → 再打开仍为输入值”, “11 字备注保存被拒 → 显示超限含义”, and “11 字保存被拒 → 原备注仍为旧备注”. Do not manufacture five or eight levels. For the 11-character case, reset a uniquely tagged test record `NOTE-01` to saved remark `旧备注`, enter `甲乙丙丁戊己庚辛壬癸子`, save, inspect the rejection after submission, reopen `NOTE-01` and check `旧备注`; bind rejection and preservation to their own `AS-*` assertions and restore the record via the same reset method. The simulated answers are illustrative only and cannot be carried into another project.

| Rough draft | Repair |
| --- | --- |
| `异常测试 → 状态校验 → 结果正确` | `待审批＋非负责人审批被拒 → 调拨单仍待审批` plus separate leaves for each warehouse's unchanged stock. |
| `备注为空或超长时校验失败` | Separate blank and 11-character rows; blank's outcome follows the confirmed rule, not a guessed failure. |
| `准备数据 → 执行操作 → 结果正确` | Name the unique starting record, exact input, ordered save/reopen steps, settled condition, business observation and `AS-*` expected value. |
| `已关联一条用例，所以规则已覆盖` | Compare every applicable derivation row with leaves and step-bound assertions, including roles/states and related-object invariants. |
