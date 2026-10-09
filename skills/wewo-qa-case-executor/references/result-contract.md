# Execution results and assertion completeness

## Outputs

```text
qa-artifacts/<artifact-slug>/.qa-state/runs/<run-id>/
|-- execution-profile.json
|-- execution-results.json
|-- test-execution-report.xlsx
`-- evidence/
```

Use schema versions profile 1.1 and results 1.3. Freeze the run profile before interacting; bind results to the exact manifest, case workbook and profile SHA256 digests. Evidence paths resolve inside this run directory, never another run. Preserve prior run files.

## Assertion contract

For each case-target pair, derive the complete required assertion set from manifest `case.assertions` filtered by `target_ids`. Result assertion IDs must equal that set after execution starts, including interrupted or failed attempts. Never report only the successful subset. Each entry has `assertion_id`, description, original expected value, actual observation, status, observations and evidence references. Follow [observation evidence](observation-evidence.md) for raw tool output, per-attempt comparisons and evidence-review judgments.

- `passed`/`failed` assertions need a non-empty actual observation and existing evidence IDs whose types cover that planned assertion's `required_evidence`.
- `not-evaluated` needs a reason and cannot establish a case pass. A blocked/not-run pair with zero attempts can omit assertion entries; the report still lists its planned assertions as unchecked.
- Evidence entries have a unique `id`, type, description, local path and SHA256. Bind each evaluated assertion to its proof, not just an unrelated screenshot attached to the case.
- Preserve both attempted outcomes and evidence in a controlled retry. For `flaky`, record the inconsistency and both attempts in the observations/evidence; never silently convert it to passed.

A case is `passed` only if all planned target assertions pass and case-level required evidence exists. `failed` requires a deterministic failing assertion, failure reason and evidence. `blocked` describes prerequisites, tool failures, unclear oracle or unauthorized actions. `flaky` requires equivalent controlled attempts with inconsistent outcomes. `not-run` requires zero attempts and a concrete reason, including manual-only. Tool failure is not proof of a product defect.

## Report

Excel sheets contain execution summary, one row per selected case-target, all planned assertion results (including unchecked), and a linked evidence index. The summary includes the automatic gate, counts and evaluated/required assertion ratio. Gate values are `PASSED`, `FAILED`, `INCOMPLETE`, `NO_CODE_EXECUTION`, or `NO_AUTOMATABLE_CASES`. Manual scope remains visible and is excluded only from the automatic gate.

```text
<qa-tool> validate-execution-results <run-dir>/execution-results.json <public-root>/.qa-state/test-manifest.json
<qa-tool> render-execution-report <run-dir>/execution-results.judged.json <public-root>/.qa-state/test-manifest.json --output <public-root>/test-execution-report.xlsx
```

The renderer validates first. Correct structured records using actual execution evidence; never edit the report to hide a failed gate. JSON validation cannot establish that a UI action happened or that a screenshot proves the declared actual result; the execution agent must read the evidence and compare it to each frozen assertion.

After collecting real observations, `<qa-tool> judge-execution-results <run-dir>/execution-results.json <public-root>/.qa-state/test-manifest.json` derives deterministic verdicts and observed actual values into `execution-results.judged.json`. Use that file in the validation/render commands above. Judging rejects an existing output; `--output` selects another separate JSON filename in the same run. It never creates observations or changes a frozen check. Evidence-review verdicts use explicitly reasoned judgments; missing/invalid evidence causes an error, not a fabricated pass. The Excel report shows comparison/timing, per-attempt pointers, review reasons and evidence hashes.

## Generated-code execution

A formal automation pass requires `native_test` for each eligible case-target, tied to the frozen native receipt, repository test asset, native test ID and evidence route. The report includes an 自动化实现 sheet. Legacy live-UI-only results can support diagnosis but their automation gate is `NO_CODE_EXECUTION`. Native success must also satisfy every planned assertion; skipped/undiscovered tests and missing observations cannot pass. Keep raw state/evidence private and export `test-execution-report.xlsx` to the public root, with links to the native human report.
