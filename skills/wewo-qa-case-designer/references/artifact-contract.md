# Tester delivery and machine state

```text
qa-artifacts/<feature>/
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

The tester receives XMind + three Excel files, then the execution report. Technical handoffs remain private. Project automation code belongs in the actual project's test directories. No generation Python files, JSON baselines, caches or draft duplicates belong at the delivery root. `validate-deliverables` enforces the four design files and their agreement; it does not remove files. Preserve user inputs and older evidence during migration.

Context schema is 1.4, points 1.4, manifest 1.6, Excel format 1.4. The importer also accepts existing Chinese format 1.3 workbooks. Earlier requirement baselines are review input: reread sources, reconcile verifiable dialogue/current units, complete requirement readiness, backfill clause extraction, derive/freeze coverage and split independent outcomes before reexport; do not just change version numbers or invent confirmations. Store the actual final-requirement confirmation response/ref/digest separately from source fact status, coverage-plan freezing and later XMind confirmation. No helper can legitimately invent a user response.

## Delivery language

The agent selects the language from the actual task; renderers use that recorded choice rather than guessing from individual strings. Apply this precedence:

1. An explicit user preference for deliverables takes priority, including a later request to change it.
2. Otherwise use the user's sustained language during requirement clarification. Quoted passages, code, identifiers or a brief reply in another language do not by themselves change it.
3. Before clarification establishes a language, use the predominant language of the supplied requirement material. If neither provides a clear choice, default to Chinese.

Record `project.output_language` as `zh-CN` or `en` in `design-context.json` and carry the same value into points and manifest. These are the currently supported fixed-label languages. Missing fields in existing baselines mean `zh-CN`; do not silently reinterpret an old workbook from its cell contents. State the selected language briefly as part of normal progress, without adding a separate confirmation gate when the evidence is clear. Keep an explicit preference until the user changes it; revisit an inferred choice if the subsequent clarification consistently establishes another language.

Chinese material with Chinese clarification normally produces Chinese artifacts. English clarification normally produces English artifacts even when the original material is Chinese. Write summaries, titles, conditions, steps, explanations and review text in the selected language. Preserve exact original source/dialogue evidence, proper names, interface fields, commands, IDs, literal inputs and expected values whose spelling is part of the test oracle; explain them in the selected language rather than translating their values. The English Skill instructions do not make English the default delivery language.

The bundled renderer localizes worksheet names, headers, fixed options, help text, validation prompts, and XMind sheet titles, note labels and draft notices. It does not translate authored business content; the agent must author and review that content in the selected language. Filenames, stable IDs, schema keys and machine enum values remain unchanged. Import reads the workbook's recorded locale and preserves typed values and original evidence. A language change requires reconciling edits, updating the context/points/manifest consistently and regenerating the four deliverables through the existing review and confirmation gates; never rename columns by hand or rewrite hashes to bypass a stale baseline.

## Three editable suite views

Smoke ⊆ regression ⊆ full. Each file contains only its cases and assertions/automation details, using shared case IDs from one manifest. Empty smoke/regression scope still gets a clearly identified empty workbook; it does not imply a passing execution gate. No arbitrary suite counts.

The case, required-assertion, automation-assessment and usage-guide worksheets are visible. Their displayed names and column labels follow the recorded delivery language; preserve the generated names during ordinary editing for import compatibility. Generated derivations/review and runtime definitions are hidden support sheets, available for inspection when useful. `_baseline` is internal metadata. Case steps and data are tester-readable; no JSON editing is required for ordinary scalar values. Sorting rows is a view change. Edit automated feasibility in its detail sheet. Retain IDs and the template structure.

`render-case-workbook` exports all three canonical files to the public root. `validate-case-workbook` checks all views, so editing a different suite cannot be silently ignored. `import-case-workbook` without `--workbook` merges all Excel deltas into pending state; conflicting changes to the same case or runtime need fail for reconciliation. An unchanged overlapping view never overrides an edited one. Review/import every changed view before rerendering; exporters reject unimported edits. Reviewed changes regenerate all files from the same baseline.

```text
<qa-tool> validate-design-context <root>/.qa-state/design-context.json --draft
<qa-tool> requirement-digest <root>/.qa-state/design-context.json
<qa-tool> validate-requirement-readiness <root>/.qa-state/design-context.json
# Present and preserve the actual summary; wait for and record the real confirmation.
<qa-tool> validate-requirement-readiness <root>/.qa-state/design-context.json --confirmed
# Then derive coverage with empty leaf links.
<qa-tool> freeze-coverage-plan <root>/.qa-state/design-context.json
# Attach one leaf per independent outcome and perform source-first / visible-tree reviews.
<qa-tool> design-review-digest <root>/.qa-state/test-points.json
# Record performed tree review against this fingerprint.
<qa-tool> validate-design-context <root>/.qa-state/design-context.json
<qa-tool> validate-test-points <root>/.qa-state/test-points.json
<qa-tool> render-test-points-xmind <root>/.qa-state/test-points.json
# Preserve the actual XMind confirmation, author and walk every case.
<qa-tool> design-review-digest <root>/.qa-state/test-manifest.json
# Record performed per-case reviews against these fingerprints.
<qa-tool> validate-test-manifest <root>/.qa-state/test-manifest.json
<qa-tool> render-case-workbook <root>/.qa-state/test-manifest.json
<qa-tool> validate-case-workbook <root>/.qa-state/test-manifest.json
<qa-tool> import-case-workbook <root>/.qa-state/test-manifest.json
<qa-tool> validate-deliverables <root>
```

Final requirements precede rendering. Show and confirm the XMind before deriving final cases. When presenting an unconfirmed tree for its review, use `--draft --output <root>/test-points.xmind`, with the draft label; after confirmation rerender the same public filename. Do not accumulate public draft files.

Hashes bind context → points → manifest → suite files → run. A source/business change invalidates its confirmation; an Excel edit becomes pending; affected requirements/points need reconfirmation. Validators establish structural consistency, not semantic correctness, actual human authorship or exhaustive coverage.
