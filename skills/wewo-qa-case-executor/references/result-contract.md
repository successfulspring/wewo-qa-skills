# Execution results and complete run reporting

## Outputs and versions

```text
qa-artifacts/<artifact-slug>/
|-- test-execution-report.xlsx
`-- .qa-state/runs/<run-id>/
    |-- execution-profile.json
    |-- native-plan.json
    |-- execution-results.<invocation-id>.json
    |-- execution-results.<invocation-id>.judged.json
    |-- execution-summary.json
    `-- native/<invocation-id>/
        |-- receipt.json
        |-- assets/
        |-- report.xml or report.json
        |-- observations.jsonl
        `-- logs and attachments
```

New runs use profile 1.2, native plan 2, receipt `wewo-qa-native-run/2` and results 1.4. Freeze the profile before the first runner invocation; results bind to the exact manifest, case workbook, profile and archived test assets. Every target has a verified environment entry and build; the legacy single `run.environment` field mirrors the first target only. Environment details are read from `run.environments`.

Keep each invocation immutable, including failed startup, interrupted checks and original results. A judged result is a separate file; summaries and reports are derived views that may be regenerated. Historical profile 1.1/results 1.3 remain readable, but cannot initiate new execution. A changed deployment, scope or profile starts another run; preserve earlier runs and link their context in profile notes.

## Assertions and lifecycle

The required assertion set equals manifest `case.assertions` filtered by target. After execution starts, include every planned assertion even when a failure interrupts later steps. Each entry retains assertion ID, description, original expected value, actual observation, status, observations and evidence references.

- Evaluated assertions need original observed values and existing, hashed evidence of all required types. Follow [observation evidence](observation-evidence.md).
- `not-evaluated` requires a reason. A zero-attempt blocked/manual pair may omit assertions; the report still lists its planned checks as unchecked.
- Runner lifecycle events preserve actual environment identity, preparation and cleanup. Unverified environment or preparation leaves business checks unevaluated; failed cleanup prevents an overall pass while preserving any valid business findings.
- Each case-target maps to its exact native test, route, code asset and receipt. A runner exit code alone cannot prove success; skipped/undiscovered tests and incomplete observations remain incomplete.

`passed` requires every planned assertion, evidence, native outcome and lifecycle check to pass. `failed` requires a demonstrated mismatch with the frozen expectation and failure evidence. `blocked` identifies missing prerequisites, tool/test errors, incomplete evidence or unresolved expectations. `not-run` requires zero attempts and a concrete reason. Classify the cause from evidence; a tool error is not proof of a product defect.

## Review and aggregate

Native collection derives deterministic verdicts immediately. For checks requiring objective evidence review, inspect the original attachments, create the canonical `execution-results.<invocation-id>.judged.json` copy, and fill only supported judgments/actuals/statuses as described in [observation evidence](observation-evidence.md). Preserve IDs, checks, observations and original results. Deterministic judging can also write this separate copy; it refuses to overwrite an existing file.

```text
<qa-tool> judge-execution-results <run>/execution-results.<invocation-id>.json <manifest>
<qa-tool> validate-execution-results <run>/execution-results.<invocation-id>.judged.json <manifest>
<qa-tool> summarize-execution <manifest> <run>/execution-profile.json
<qa-tool> render-execution-report <run>/execution-summary.json <manifest> --output <public-root>/test-execution-report.xlsx
```

The summary gathers **every** preserved invocation, validates original and canonical judged results, checks retry links and includes all selected case-targets. Later unmapped rows do not erase earlier execution. Earlier failure followed by pass with equivalent test assets is `flaky`; changed assets without a documented test repair stay blocked. A legitimate test repair records the defect, preserved oracle and reset evidence; the final report retains earlier failure and code revisions. Do not relabel retries to bypass the stopping condition.

The renderer recomputes the summary and rejects stale or modified summaries. New per-invocation results cannot be rendered as the final report; use the complete run summary. A zero-execution run can still be summarized and reported, with the specific inputs needed next. Individual invocation evidence is never rewritten to contain synthetic merged attempts.

## Report and delivery

Report labels follow the Designer output language. Sheets show summary, all selected case-targets, all planned assertions, evidence index, automation implementation, environment/readiness, preparation/cleanup and execution history. Assertion rows describe the latest effective result; history links preserve each invocation's full assertions, observations and archived code. Manual scope remains visible and is excluded only from the automatic gate.

Report the selected/executed/blocked/manual counts, evaluated/required assertions, environment/build, test workspace, actionable failures and cleanup issues. Gates are `PASSED`, `FAILED`, `INCOMPLETE`, `NO_CODE_EXECUTION` or `NO_AUTOMATABLE_CASES`; zero executed cases cannot pass. Link existing native human reports when available. Keep raw records private under `.qa-state/` and export the workbook to the public artifact directory.

Validation checks structure, comparisons, provenance links and completeness. It cannot prove fabricated observations authentic or independently verify a visual judgment. Actual execution, truthful evidence and code/evidence inspection remain necessary; never edit the workbook to hide a gate failure.
