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

Context schema is 1.2, points 1.2, manifest 1.4, Excel format 1.3. Older requirements without explicit final confirmation are review input, not a current approved baseline. Store the actual final-requirement confirmation response/ref/digest separately from source fact status and from later XMind confirmation. No helper can legitimately invent a user response.

## Three editable suite views

Smoke ⊆ regression ⊆ full. Each file contains only its cases and assertions/automation details, using shared case IDs from one manifest. Empty smoke/regression scope still gets a clearly identified empty workbook; it does not imply a passing execution gate. No arbitrary suite counts.

`测试用例`, `必检断言`, `自动化评估` and `使用说明` are visible. Generated derivations/review and runtime definitions are hidden support sheets, available for inspection when useful. `_baseline` is internal metadata. Case steps and data are tester-readable; no JSON editing is required for ordinary scalar values. Sorting rows is a view change. Edit automated feasibility in its detail sheet. Retain IDs and the template structure.

`render-case-workbook` exports all three canonical files to the public root. `validate-case-workbook` checks all views, so editing a different suite cannot be silently ignored. `import-case-workbook` without `--workbook` merges all Excel deltas into pending state; conflicting changes to the same case or runtime need fail for reconciliation. An unchanged overlapping view never overrides an edited one. Review/import every changed view before rerendering; exporters reject unimported edits. Reviewed changes regenerate all files from the same baseline.

```text
<qa-tool> validate-design-context <root>/.qa-state/design-context.json
<qa-tool> validate-test-points <root>/.qa-state/test-points.json
<qa-tool> render-test-points-xmind <root>/.qa-state/test-points.json
<qa-tool> validate-test-manifest <root>/.qa-state/test-manifest.json
<qa-tool> render-case-workbook <root>/.qa-state/test-manifest.json
<qa-tool> validate-case-workbook <root>/.qa-state/test-manifest.json
<qa-tool> import-case-workbook <root>/.qa-state/test-manifest.json
<qa-tool> validate-deliverables <root>
```

Final requirements precede rendering. Show and confirm the XMind before deriving final cases. When presenting an unconfirmed tree for its review, use `--draft --output <root>/test-points.xmind`, with the draft label; after confirmation rerender the same public filename. Do not accumulate public draft files.

Hashes bind context → points → manifest → suite files → run. A source/business change invalidates its confirmation; an Excel edit becomes pending; affected requirements/points need reconfirmation. Validators establish structural consistency, not semantic correctness, actual human authorship or exhaustive coverage.
