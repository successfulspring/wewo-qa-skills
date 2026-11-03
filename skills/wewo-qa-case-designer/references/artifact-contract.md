# Tester delivery and machine state

```text
qa-artifacts/<feature>/
|-- requirement-clarifications.xlsx # first delivered before case design
|-- test-points.xmind
|-- test-cases.smoke.xlsx
|-- test-cases.regression.xlsx
|-- test-cases.full.xlsx
|-- test-execution-report.xlsx   # after execution
|-- test-report/                 # native human report if produced
`-- .qa-state/
    |-- design-context.json
    |-- test-points.json
    |-- test-manifest.json
    |-- source-cache/
    |-- work/                    # disposable authoring helpers, never deliverables
    `-- runs/<run-id>/           # frozen profiles/results/raw evidence
```

The tester first receives the business explanation and standalone requirement-clarifications.xlsx; after overall confirmation, XMind + three case Excel files accompany an updated copy of that same clarification workbook. The execution report follows execution. Keep technical handoff state under `.qa-state/` and retain it when transferring the reviewed artifact directory to Executor. Executor reuses an authorized automation workspace or creates persistent `qa-automation/<artifact-id>/` beside `qa-artifacts/`, following [independent acceptance automation](../../wewo-qa-case-executor/references/native-automation.md#workspace-and-implementation). Product source is not required.

No generation helpers, automation scripts, JSON baselines, caches or draft duplicates belong at the delivery root. `validate-deliverables` enforces the four case-design files plus the independent clarification workbook and their agreement; it does not remove files. Preserve user inputs and older evidence during migration. Before case design, use `validate-clarification-workbook` for the initial standalone delivery.

Current contracts are context 1.6, points 1.6, manifest 1.8 and case Excel 1.6; the independent clarification workbook uses format 1.0. Existing context/points 1.5 and manifest 1.7 remain readable. Missing source roles stay unknown and existing decisions retain dialogue semantics. The importer also accepts existing 1.3 Chinese, 1.4 bilingual and 1.5 embedded-question workbooks. Preserve their edits before regenerating the separated 1.6 case layout. Earlier baselines are review input: reuse verifiable sources and actual dialogue, reconcile extraction and business confirmation, then regenerate. The old requirement digest included conversation history; do not simply relabel versions or rewrite approval hashes. Store actual overall confirmation separately from scoped amendments, internal reviews and artifact stage. No helper can invent a user response.

## Delivery language

The agent selects the language from the actual task; renderers use that recorded choice rather than guessing from individual strings. Apply this precedence:

1. An explicit user preference for deliverables takes priority, including a later request to change it.
2. Otherwise use the user's sustained language during requirement clarification. Quoted passages, code, identifiers or a brief reply in another language do not by themselves change it.
3. Before clarification establishes a language, use the predominant language of the supplied requirement material. If neither provides a clear choice, default to Chinese.

Record `project.output_language` as `zh-CN` or `en` in `design-context.json` and carry the same value into points and manifest. These are the currently supported fixed-label languages. Missing fields in existing baselines mean `zh-CN`; do not silently reinterpret an old workbook from its cell contents. State the selected language briefly as part of normal progress, without adding a separate confirmation gate when the evidence is clear. Keep an explicit preference until the user changes it; revisit an inferred choice if the subsequent clarification consistently establishes another language.

Chinese material with Chinese clarification normally produces Chinese artifacts. English clarification normally produces English artifacts even when the original material is Chinese. Write summaries, titles, conditions, steps, explanations and review text in the selected language. Preserve exact original source/dialogue evidence, proper names, interface fields, commands, IDs, literal inputs and expected values whose spelling is part of the test oracle; explain them in the selected language rather than translating their values. The English Skill instructions do not make English the default delivery language.

The bundled renderer localizes worksheet names, headers, fixed options, help text, validation prompts, and XMind sheet titles, note labels and draft notices. It does not translate authored business content; the agent must author and review that content in the selected language. Filenames, stable IDs, schema keys and machine enum values remain unchanged. Import reads the workbook's recorded locale and preserves typed values and original evidence. A language change requires reconciling edits, updating the context/points/manifest consistently and regenerating the five deliverables through the existing review and confirmation gates; never rename columns by hand or rewrite hashes to bypass a stale baseline.

## Three editable suite views

Smoke ⊆ regression ⊆ full. Each file contains only its cases and assertions/automation details, using shared case IDs from one manifest. Empty smoke/regression scope still gets a clearly identified empty workbook; it does not imply a passing execution gate. No arbitrary suite counts.

The case, required-assertion, automation-assessment and usage-guide worksheets are visible. Their displayed names and column labels follow the recorded delivery language; preserve the generated names during ordinary editing for import compatibility. Generated derivations/review and runtime definitions are hidden support sheets, available for inspection when useful. `_baseline` is internal metadata. Case steps and data are tester-readable; no JSON editing is required for ordinary scalar values. Sorting rows is a view change. Edit automated feasibility in its detail sheet. Retain IDs and the template structure.

`render-case-workbook` exports all three canonical files to the public root. `validate-case-workbook` checks all views, so editing a different suite cannot be silently ignored. `import-case-workbook` without `--workbook` merges all Excel deltas into pending state; conflicting changes to the same case or runtime need fail for reconciliation. An unchanged overlapping view never overrides an edited one. Review/import every changed view before rerendering; exporters reject unimported edits. Reviewed changes regenerate all files from the same baseline.

## Draft and final state

Prefer the native [structured authoring and combined delivery](efficient-authoring.md) workflow. `build-deliverables <root> --stage clarification|draft|final` performs the applicable existing validation, rendering and readback steps in one snapshot; do not repeat the unchanged full chain afterward. The individual commands below remain supported for diagnosis and legacy workflows. No combined command supplies business confirmation or semantic review.

Points and manifest use stage=draft/final, independent of their review status. Legacy absent stage means final. Use status=pending plus nonempty question_refs on affected rules, coverage items/outcomes, leaves and assertions. Omit unknown expected values; a pending assertion must not carry check. Known assertions keep their real expected and typed check. Pending leaf/outcome/assertion status and question references must agree.

The independent `requirement-clarifications.xlsx` is generated from context before case design and maintained through final delivery. It contains every detailed question, source, business impact, options, reply, status, conclusion and evidence. Initial case links say cases are not yet generated; real links are derived after design. All suite files show case/assertion pending status and question IDs; they do not contain the question inventory. A proposed expected value may be imported for a pending assertion without confirming it or making it executable.

Follow [clarification workbook](clarification-workbook.md) for early export, response import, partial answers, closed history and migration. Its only editable business column is Reply. The shared context remains the source for generated question content/status. Rerendering must not discard human cell edits. `render-open-questions` remains an optional complete Markdown view from a validated case manifest.

Local pending material questions and an unfrozen coverage plan are allowed for case draft export **after** overall confirmation. Final readiness, plan freezing, final exports and Executor reject unresolved business expectations. The initial clarification workbook is available **before** that confirmation, including unresolved overall blockers; it is not an execution baseline.

```text
<qa-tool> validate-design-context <root>/.qa-state/design-context.json --draft
<qa-tool> requirement-digest <root>/.qa-state/design-context.json --snapshot
<qa-tool> validate-requirement-readiness <root>/.qa-state/design-context.json --clarification
<qa-tool> render-clarification-workbook <root>/.qa-state/design-context.json
<qa-tool> validate-clarification-workbook <root>/.qa-state/design-context.json
# Deliver business explanation + clarification XLSX; record real confirmation/answers.
<qa-tool> import-clarification-workbook <root>/.qa-state/design-context.json
# Reconcile actual cell/chat replies, preserving unresolved local questions.
<qa-tool> validate-requirement-readiness <root>/.qa-state/design-context.json --draft --confirmed
# Derive the draft plan, then leaves and cases. Record the performed visible-tree review.
<qa-tool> design-review-digest <root>/.qa-state/test-points.json
<qa-tool> render-test-points-xmind <root>/.qa-state/test-points.json --draft
<qa-tool> render-case-workbook <root>/.qa-state/test-manifest.json --draft
<qa-tool> validate-case-workbook <root>/.qa-state/test-manifest.json --draft
<qa-tool> render-clarification-workbook <root>/.qa-state/design-context.json --draft
<qa-tool> validate-deliverables <root> --draft
# Deliver four case drafts and the updated same clarification XLSX together.
<qa-tool> import-clarification-workbook <root>/.qa-state/design-context.json
# Apply actual batch answers and retain closed question history.
# Import Excel edits before regeneration, then reconcile the pending candidate.
<qa-tool> import-case-workbook <root>/.qa-state/test-manifest.json
# Resolve pending facts using scoped amendments; refresh the requirement audit.
<qa-tool> validate-requirement-readiness <root>/.qa-state/design-context.json --confirmed
# Clear candidate leaf links before freezing; reattach preserved leaves afterward.
<qa-tool> freeze-coverage-plan <root>/.qa-state/design-context.json
# Renew source-first, visible-tree and case reviews; set stage=final.
<qa-tool> design-review-digest <root>/.qa-state/test-points.json
<qa-tool> design-review-digest <root>/.qa-state/test-manifest.json
<qa-tool> validate-design-context <root>/.qa-state/design-context.json
<qa-tool> validate-test-points <root>/.qa-state/test-points.json
<qa-tool> validate-test-manifest <root>/.qa-state/test-manifest.json
<qa-tool> render-test-points-xmind <root>/.qa-state/test-points.json
<qa-tool> render-case-workbook <root>/.qa-state/test-manifest.json
<qa-tool> render-clarification-workbook <root>/.qa-state/design-context.json
<qa-tool> validate-deliverables <root>
```

Overall understanding confirmation precedes case/XMind rendering, but follows the first independent clarification XLSX delivery. Deliver XMind and all three Excel drafts together using `--draft`; keep all five public filenames when refining and finalizing. Do not insert a separate XMind approval before cases. Use the final commands without `--draft` only after business questions are resolved and internal reviews are current.

Hashes bind context → points → manifest → suite files → run. Reconcile changed business facts through actual scoped answers, retaining the initial confirmation. Refresh affected file bindings and agent reviews; do not obtain approvals merely to refresh hashes. An Excel edit becomes pending for import/review. Validators establish structural consistency, not semantic correctness, actual human authorship or exhaustive coverage.

The execution handoff includes the entire reviewed artifact directory and its baselines. `candidate_route` describes the surface required by the case, not current execution readiness. Use `api` for an interface-defined acceptance target (`surface: api`); do not substitute it for a UI expectation. Executor discovers accounts, data, tools and environment access against the deployed target, without requiring product source.

Later-source updates retain pre-update context, points and manifest in `.qa-state/history/<update-id>/`, after importing user edits. `source_updates.base_context_ref` points to that retained context. Carry the history with the private state during handoff so stopped coverage and amendments remain inspectable. Preserve the four case-design files and the same independent clarification workbook. Deliver a concise change explanation and update that workbook; no second question inventory is required. See [source updates](source-updates.md) for document decisions, evidence-only changes and source branch reviews.
