# Preserved UI observations

Record real tool execution, never synthesize expected values as observations. Tool availability, valid case design and a matching JSON file are separate facts. Run the original UI steps, wait for the specified observable timing, and inspect the correct subject/location on the selected test build.

For every evaluated assertion, preserve a JSON file in this run's evidence directory using `schemas/ui-observation.schema.json`:

```json
{
  "format": "wewo-qa-ui-observation/1",
  "run_id": "run-001", "case_id": "TC-001", "target_id": "target-001",
  "attempt": 1, "subject": "test-record-identifier",
  "location": "business-visible quantity field",
  "captured_at": "2026-10-08T10:00:00+08:00",
  "tool": "actual-ui-tool-name",
  "raw": {"value": "original output returned by that tool"}
}
```

`raw` is the original tool result, which may be an object, list or text. The example shape is illustrative: do not add a fabricated `value` field to make a pointer resolve. Preserve original output; if it contains secrets, obtain a narrowly scoped non-sensitive observation from the UI instead. If the needed value is available only in pixels, preserve the actual screenshot and relevant original tool response, and use a previously designed evidence-review check. A frozen deterministic check whose observation route cannot be resolved is blocked and returned to Designer; do not change its method during execution.

If screenshot, rendered text and DOM/accessibility observations conflict, inspect the current settled UI and preserve the conflicting evidence. Do not select the favorable representation. Resolve whether the captures describe different moments/subjects; if the required timing or observation cannot be established, leave the affected check unevaluated with a blocker.

Evidence entries have id, `type=tool-output`, local path, description and exact file `sha256`. All other evidence files also have SHA256. Each evaluated result assertion has `observations` with `attempt`, `phase=after` (plus before for delta/unchanged), `evidence_id`, and JSON Pointer under `/raw`. Link these IDs in `evidence_refs` alongside the assertion's required screenshots or other evidence. Compare values from original output, not the agent's prose.

`actual` is the last attempt's observed text, or JSON serialization for a non-text value. For before/after checks it is a sorted-key JSON object containing `after` and `before`; the runtime requires it to agree with preserved values. Every controlled attempt has its own observations. Preserve matching subject/location, the same field pointer, and chronological before/after timestamps. Evaluated assertions require observations for all recorded attempts; interrupted missing checks remain not-evaluated with reasons.

Deterministic kinds are recomputed during result validation. An assertion is passed only if every recorded attempt passed; otherwise its aggregate is failed. A case with both complete passing and failing attempts is flaky, even if its last attempt passed. For `evidence-review`, include `judgments=[{attempt,status,reason}]` in attempt order; reasons tie actual pixels/text to frozen objective criteria. These judgments remain agent assessments and are displayed separately in Excel. They must not replace a deterministic comparator.

Hashes and metadata reject accidental changes, stale runs, mismatched subjects and inconsistent declarations. They cannot prove a fabricated tool result authentic, prove the stated check timing was actually awaited, or independently verify a visual judgment. Truthful UI execution and inspection are still required. Missing tool/data/access/evidence causes blocking or unchecked coverage; an observed product mismatch cannot be hidden as a tool blocker.

## Native test observations

`wewo-qa-native-observation/1` additionally links its original runner-produced JSONL line to an immutable native-run receipt. The validator checks receipt/profile/manifest, exact test mapping, native report status, archived executable asset hashes, observed value, subject/time and report/log hashes. `run-native-tests` creates these records from actual process execution; do not fabricate UI wrapper records to represent generated code. Native report adapters are described in [native automation](native-automation.md).
