# Independent acceptance automation

## Workspace and implementation

Reuse an authorized existing test workspace; otherwise create a persistent `qa-automation/<artifact-id>/` workspace beside `qa-artifacts/`. It need not be a Git repository or contain product source. Keep tests, helpers, dependency manifests/locks and test-only configuration there. Do not put scripts among tester-facing deliverables.

Select a mature runner from actual target/control needs and available tooling. Reuse existing suitable infrastructure. Inspect live UI and supplied interface documentation for real operations/locators. An interface contract is not product source. Use deterministic waits, isolated data and cleanup. Existing fixtures/helpers are useful only when their behavior preserves the current case.

Map each case-target to one native test ID and every required assertion. One coherent journey may check multiple leaves; a final success message cannot replace independent business checks. Keep the expected values frozen.

## Plan and runtime binding

Native plan 2 uses `workspace`, `runner`, explicit `argv`, `manifest_sha256`, `profile_sha256`, `report_format` and `bindings`. Each binding has case_id, target_id, asset, asset_sha256, test_id, route, assertion_ids and `review` describing the actual step/assertion walkthrough. `support_files` archives local helpers, runner configuration and dependency locks used by the entry assets, with path and SHA256. Scope these assets to the authorized workspace. Preserve source paths in the archived tree.

The actual route must match the reviewed candidate surface. Native report collection supports JUnit XML and Playwright JSON. Resolve test IDs from real discovery/report output; JUnit uses classname::name and Playwright uses suite/spec titles with [projectName]. Additional runners need an appropriate established reporter/adapter preserving the same evidence, not a fabricated report.

Use collection/list mode to inspect test IDs before running business steps. Execute focused checks, full runs and repair verification through `run-native-tests`; they all belong to the preserved invocation history. Do not run an unrecorded business trial and report only the later successful attempt.

The runner receives `WEWO_QA_PROFILE_FILE` pointing to the frozen profile. Generated tests read their target's verified entry/build and safe bindings from that profile. Record the actual target entry/build in the lifecycle record and check it against the profile; do not merely label results with an unrelated environment JSON.

```text
<qa-tool> run-native-tests <manifest> <run>/execution-profile.json <run>/native-plan.json
```

The command expands {report}, {output_dir}, {observations}; it sets WEWO_QA_RUN_ID, WEWO_QA_REPORT_FILE and WEWO_QA_OBSERVATIONS_FILE. argv is an argument array, never a composed shell command. Credentials are obtained through approved references/session setup, never command arguments.

## Original observations

Each assertion JSONL event has run_id, case_id, target_id, test_id, assertion_id, attempt=1, phase=before/after, subject, location, captured_at and the actual value. Emit values observed from the deployed system, not copied expectations or seed data. `number-delta` and `unchanged` require exactly one before and one after event with the same subject/location. Other comparators, including `equals` and `evidence-review`, require exactly one after event; an extra before event makes the comparison invalid. Capture other diagnostic state in separate attachments.

A lifecycle event uses `event="lifecycle"`, the same run/case/target/test identity, phase=environment/preparation/cleanup and status=passed/failed/not-required, detail and captured_at. Environment events additionally contain the actual entry and build. Cleanup not-required needs a concrete reason; failed cleanup stays visible. Preserve real event order and capture evidence before cleanup.

Attachments carry type/path/description, are relative to the invocation directory and must exist there. Keep native HTML reports where supported. Tests emit each available assertion before applying a failing framework assertion, so the original mismatch survives an early stop. Subsequent unperformed checks remain unchecked.

## Repeats and repair

Disable hidden runner retries. Each invocation is immutable. Repeating a mapped pair requires `rerun` on that binding: previous_receipt_sha256, kind (repeat/retry/test-repair), reason and reset_note. The previous hash identifies its latest actual attempt in this run. State why rerunning is warranted and how the same initial state was restored. Test-repair additionally documents the test defect and why the change preserves the frozen oracle.

Use one controlled retry to diagnose a transient outcome; do not loop until passing. A changed deployment/profile begins another run, linked in its notes to the earlier run. A legitimate script repair preserves the old code/observations and records the new code; it is not evidence of a product fix.

`summarize-execution` gathers all invocation results for the run and rejects missing history. Unexplained fail/pass changes remain incomplete or flaky. Equivalent passing/failing runs are flaky; documented test repairs remain visible even when the current tests pass. Only actual new-version execution can verify a product repair.
