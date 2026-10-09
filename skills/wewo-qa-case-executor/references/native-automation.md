# Project-native acceptance automation

## Resolve the runner from the actual repository

Read task-relevant source, existing test paths/config/scripts, fixtures/page objects and lockfiles. Verify deployed build alignment. Reuse the established Playwright Test, Cypress, pytest, mobile/desktop framework or other appropriate runner; language alone is not a selection rule. Keep UI-visible business assertions in UI tests. API acceptance is suitable only for interface-defined behavior or supported setup/checks that preserve the case's evidence. Do not replace an end-to-end flow with mocked unit tests.

Generated code lives in normal project test paths and includes stable case/AS identifiers. For a case spanning multiple confirmed leaves, bind every planned `AS-*` to the exact post-step observation for that leaf, including related-object changes and unchanged invariants; a single final success check does not replace them. Reuse helpers, deterministic waits, independent data and cleanup. Source code is read-only except test assets/config. Product defects remain reported defects. Current case oracles stay frozen even if the implementation does something else.

## Plan and evidence

A native plan is agent-owned JSON under private run state:

```json
{
  "repository": "<authorized project root>",
  "runner": "<actual existing runner>",
  "manifest_sha256": "<frozen manifest hash>",
  "profile_sha256": "<frozen execution profile hash>",
  "report_format": "junit",
  "argv": ["<existing runner command>", "<selected test scope>", "<report option using {report}>"],
  "bindings": [{
    "case_id": "<case ID>", "target_id": "<target>",
    "asset": "<repository-relative test file>", "asset_sha256": "<hash>",
    "test_id": "<exact native report identifier>",
    "route": "<case-preserving evidence surface>",
    "assertion_ids": ["<all planned AS IDs for this target>"]
  }]
}
```

The agent supplies the real repository command, not a shell string. The tool does not create the tests or choose their runner. `{report}`, `{output_dir}`, `{observations}` expand to fresh invocation-local paths. Environment variables `WEWO_QA_RUN_ID`, `WEWO_QA_REPORT_FILE`, `WEWO_QA_OBSERVATIONS_FILE` expose those non-secret locations to the tests. Framework credentials remain safe references/session setup, never plan arguments or artifacts.

Instrument the generated tests to append original observed values to the observation JSONL as they execute. Each line has `run_id`, `case_id`, `target_id`, exact `test_id`, `assertion_id`, `attempt` (1 per invocation), `phase` (before/after), `subject`, `location`, ISO `captured_at`, and `value`. Use actual response/element/object values, not expected values or seeded data as a substitute for post-action observations. Keep independent before/after values for delta/unchanged checks. Preserve assertion failure evidence before cleanup. No observation emitted means the assertion was not evaluated.

Optional `attachments` on an event have type/path/description; paths must stay in the fresh output directory. Preserve real screenshots/traces as required. Visual/semantic criteria additionally require explicit reasoned review; a process return code alone cannot judge them. The collector initially marks checks requiring further review blocked; complete their actual evidence/judgments before judging/reporting.

```text
<qa-tool> run-native-tests <manifest> <run>/execution-profile.json <run>/native-plan.json --environment <run>/environment.json
<qa-tool> validate-execution-results <run>/execution-results.<invocation>.json <manifest>
<qa-tool> render-execution-report <results> <manifest> --output <public-root>/test-execution-report.xlsx
```

The verified non-secret environment JSON has `name`, `kind` (test/staging/preview), `build`, and optional `base_url`/notes. This command does execute the supplied runner in the authorized project. Environment/data preflight and action authorization must happen first. Existing authorization for ordinary test execution applies; ask only about genuinely missing inputs or consequential actions outside it.

Built-in native report collection supports JUnit XML (pytest/Cypress and other established reporters) and Playwright JSON. JUnit test identifiers are `classname::name`. Playwright identifiers are suite/spec titles joined by ` > ` followed by ` [projectName]`. Resolve these from actual native reports/discovery; do not guess. Preserve the project's native human reporter, including Playwright HTML when used. Other established formats require a small specific adapter with preserved original report/exit/observations, not replacing the runner or fabricating a passing UI record.

Missing/duplicate test IDs, skipped tests, zero discovery, ambiguous hidden retries, missing assertions and startup failures do not pass. Disable runner retries for collection. A justified rerun creates a separate invocation and report; preserve the initial report and explain its classification in the final report. The native collector does not merge invocations into one attempt history. An unexplained fail/pass difference remains unresolved or flaky, never a clean pass. `run-native-tests` saves immutable invocation directories, code snapshots, stdout/stderr, report, observed values and a receipt, compares every assertion, and records unmapped/manual pairs. It does not prove that incorrect generated tests faithfully interacted with the product; semantic review and actual native execution are both required.

Framework reporter references: [Playwright](https://playwright.dev/docs/test-reporters), [pytest](https://docs.pytest.org/en/stable/how-to/output.html), [Cypress](https://docs.cypress.io/app/tooling/reporters).
