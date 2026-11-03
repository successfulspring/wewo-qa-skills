# Structured authoring and measured delivery

Use the native tools below for mechanical writing, confirmation bookkeeping and export. The agent still reads all scoped material, derives every applicable scenario and oracle, and actually reviews the business coverage and every case. No command infers an approval or performs semantic review. Do not reimplement ID allocation, reciprocal links, baseline hashes, confirmation bookkeeping, validators or exporters in a project-specific program.

For substantial repeated business input, use concise authored scenario tables, the batch defaults below and, when useful, a small data constructor in an already available or agent-provided runtime. It may assemble literal records from explicitly designed rows and shared scaffolding, then submit the request to `apply-design`; it must not write canonical state directly or decide business expectations, approvals, applicability, priorities or reviews from heuristics. Every required scenario and independent result must remain explicit and be reviewed after expansion. Keep such request-authoring aids private, reuse them for affected input when useful, and never require the tester to install a language runtime. This is permission to avoid repetitive serialization, not to generate coverage by a case-count target or manufacture review notes.

Read this reference during initial intake. Read the detailed test-design methodology after overall confirmation; source-updates and legacy migration are conditional. Inspect selected schema definitions or units instead of repeatedly dumping entire schemas and multi-megabyte state files into the conversation.

## Inspect and initialize

```text
<qa-tool> inspect-design --schema authoring-request
<qa-tool> inspect-design --schema list
<qa-tool> inspect-design --schema design-context:open_questions
<qa-tool> inspect-design --schema test-manifest:project
<qa-tool> inspect-design --schema rule
<qa-tool> inspect-design --schema coverage_item
<qa-tool> inspect-design <state>/design-context.json
<qa-tool> inspect-design <state>/design-context.json --unit RU-001
```

The unit view includes its declared dependencies and exact linked source text. It does not replace the initial reading of all material or the final source-first omission audit. Schema names are exact definitions or top-level properties in the existing context, points and manifest contracts (for example `design_model`, `factor`, `test_case`, `assertion`, `open_questions`). Use `list` to discover them and `document:name` to disambiguate names shared by several contracts. Packaged schema files also remain under this reference's `schemas/` directory.

`apply-design` accepts a JSON change request conforming to `schemas/authoring-request.schema.json`. Keep requests under `.qa-state/work/`. The canonical business state remains the existing context/points/manifest; requests are not another maintained baseline.

```json
{
  "format": "wewo-qa-authoring/1",
  "base_sha256": null,
  "project": {"name": "User supplied project", "artifact_id": "user-project", "output_language": "en"},
  "upsert": {"sources": []}
}
```

This is a shape illustration, not a valid completed intake: supply actual source inventory records and at least one real extracted segment for every included source before applying. An extracted but uninterpreted segment keeps `read_status=needs-review`; do not invent placeholder text. For a new context, `base_sha256` is null and `project` is required. The tool initializes empty discovery records and draft statuses, never a design plan, review or confirmation. For an existing context, use the current hash returned by `inspect-design` or the last successful write. Unknown fields and stale writes fail.

```text
<qa-tool> apply-design <state>/design-context.json --input <state>/work/intake.json
```

`upsert` supports sources, segments, requirement_items, objects, relationships, flows, rules, requirement_units, open_questions, closed_questions, decisions and source_updates. Existing record IDs keep their identity; supplied fields update those records and omitted fields are preserved. Arrays inside an updated record are explicit replacements. An omitted record is not deleted. Retire business coverage only through the existing authorized exclusion/supersession workflow.

Canonical IDs can be supplied directly. New records may use `id: "@meaningful-key"`; other reference fields may use the same alias. The tool allocates compatible stable IDs in `.qa-state/authoring-index.json`. Use a distinct key for each entity; do not reuse one across record types. Literal business text containing `@` is not rewritten. Repeating an identical successful request is a no-op only while all its resulting baselines are unchanged.

For an extracted source segment, provide `id`, `cache_ref` (relative to state or an absolute local path), `cache_segment_id`, and the actually verified `read_status`, `disposition`, and applicable `review_note`. The tool copies the exact source_id/anchor/kind/content from that cache; reading status is never inferred from extraction. Alternatively supply the canonical segment directly.

An extraction item can supply `origin_ref`, a literal `quote`, `disposition`, explicit `rule_refs`, and any required reason. `statement` defaults to the exact quote. The tool calculates start/end Unicode offsets. A repeated quote requires zero-based `occurrence`; it never silently picks the first match. Keep every behavioral clause independently accounted for. Whole nonbehavioral blocks may be context records after actual interpretation; do not classify difficult behavior as context. Required reciprocal rule/extraction links are maintained from the explicitly authored `rule_refs`.

Preserve the existing intake distinctions: a unit's `source_refs` contains source IDs, while rule `segment_refs` supplies anchored evidence. Pending rules need an authored rationale and question links. Pending extraction items use their question link and reason with empty `rule_refs`; they are not resolved rule extractions. Source exclusions still need their actual exclusion/extraction evidence. The helper does not infer these semantic classifications.

## Initial explanation and workbook

Finish source reading and the three real requirement audits. Supply their actual `kind`, `unit_refs` and `note` as `requirement_checks`; the tool binds these reviewer-authored checks to the current business digest. This records the agent's work, not user agreement.

```text
<qa-tool> build-deliverables <root> --stage clarification
```

This validates and returns the independent clarification XLSX before any case design. The workbook preserves all concrete questions, source links, impacts and options. Deliver its link with the whole-business explanation and invite one consolidated confirmation/answer. Do not create cases here.

Keep a prepared explanation as draft text until it is actually shown. On the following turn, preserve the exact displayed summary and question batch using `record-design-dialogue` before recording the actual user reply:

```text
<qa-tool> record-design-dialogue <state>/design-context.json --input <state>/work/dialogue-event.json
```

The request contains `base_sha256` and an `event` in the existing dialogue schema: `id`, `kind`, exact `text`, actual `message_ref`, and applicable reply/question links. A summary gets its current snapshot and retained baseline automatically. A question batch gets mechanical revisits automatically. A `confirmation` must identify its displayed summary in `in_reply_to`; it preserves that summary's original baseline. A combined confirmation/answer uses `answer_to`, `question_ids` and, for cell replies, exact `responses` from `import-clarification-workbook`. It remains one real user event. Answers need an authored `branch_review` with affected `unit_refs` and substantive `note`.

The caller must establish that a message is actually a confirmation; the tool does not classify "yes" or spreadsheet edits on its own. Confirmation alone leaves all open questions and unknown expectations unchanged. Later business changes retain the initial confirmation and use explicit `amendments` and source/decision provenance. An amendment's ref and supporting decisions remain authored; its current sha256 may be omitted for mechanical calculation. Never overwrite the initial confirmation to refresh a hash.

## Design one coherent unit at a time

After actual overall confirmation, use `apply-design` for coherent batches of rule derivations and their cases. Read [test design](test-design.md) for applicability, factors, methods and independent outcomes. The author still supplies method choices, actual scenario rows, representative data, conditions, actions and outcomes. The tool does not decide which combinations matter or invent expected values. Do not impose case quotas.

Each batch can upsert a unit's rules with factors, coverage and design_models, together with `design.cases`. The first design batch needs `design.project` with the existing project fields plus requirement, baseline and explicit target definitions. Later batches reuse it. `design.runtime_requirements` is an explicit upsert list. Use stage=draft until the existing finalization obligations are met.

The tool derives one leaf per authored item/outcome, retains existing leaf IDs for unchanged pairs, links coverage dimensions, and derives tree/source/unit views. It preserves known outcomes and pending question references. Default visible branches follow the authored business rules; refine the tree through the canonical contract when an actual flow needs another meaningful organization, and review it before delivery. Never pad the hierarchy to a fixed depth.

Every method row needs its own `COV-*` ID. To reuse the same result across different models, use distinct row IDs and the same `OUT-*` ID with identical condition, action, factor assignments and outcome content. Across rules, a shared `FAC-*` requires an identical factor object, including its evidence, and every rule must include that evidence in its requirement references. The tool shares the leaf while retaining every derivation link; it preserves already separate legacy leaf IDs. A shared leaf appears once and carries all applicable rule/unit/source references. Do not mark a required decision row `excluded` merely because another method covers it. Different conditions or factor assignments need distinct outcomes and leaves even when their expected text is equal.

Cases still need an ID/key, title, priority, risk, suite_membership, applicable_targets, preconditions, test_data, ordered steps, automation assessment and safety/cleanup. These are business/test-design choices, not tool defaults.

When every case in a coherent batch shares the same preparation and execution conditions, author those once in `design.case_defaults`: only `preconditions`, `applicable_targets`, `automation`, `runtime_requirement_refs` and `safety` are allowed. Each case receives a full copy; a field explicitly supplied by that case replaces the default field (arrays are replaced, not appended). These defaults apply only to the cases in this request, never to existing cases or later batches. Keep case-specific state/data explicit. Title, priority, risk, suites, test data, actions, expectations and review notes remain individually authored. The final manifest and workbooks contain complete cases, with no template dependency.

For example, `"case_defaults": {"applicable_targets": ["AUTHORED-TARGET"], "runtime_requirement_refs": []}` can remove repeated target bookkeeping from a batch. Supply the actual shared preparation, target assessment and cleanup only after checking that they apply to every affected case. Do not use defaults to make unknown prerequisites or business outcomes appear resolved.

A compact assertion can contain:

```json
{
  "point": "OUT-AUTHORED-RESULT",
  "observation": "Actual business-visible observation location",
  "required_evidence": ["screenshot"],
  "check": {"kind": "equals", "expected_value": "Confirmed literal value", "timing": "The specified business event has completed"}
}
```

`point` identifies a leaf or an outcome with exactly one leaf. If an outcome is reused in multiple scenarios, use the specific point ID. The tool supplies assertion ID, leaf references, canonical expected text and case source/point links. It copies case target IDs unless assertion targets are explicitly supplied. For a pending outcome, omit the check; a supplied executable check is rejected. Never use this illustration as project evidence.

A step can use `points: ["OUT-AUTHORED-RESULT"]` instead of manually repeating assertion IDs; the tool binds those specific assertions. Navigation/preparation steps may omit points. Step action and step expected result remain authored. Multiple independently judgeable results remain distinct assertions even within one coherent case.

Each batch is checked before writing for malformed derivations, wrong references, missing comparisons, pending-state mismatches and case coverage of the currently derived leaves. Review completion is deliberately deferred; the command's successful write is not delivery readiness. Failed requests leave the earlier state intact. Read the full diagnostic list and fix the affected batch rather than regenerating every module.

## Actual review, then one export

After the complete design is stable, perform the source-first omission review, visible-tree review and every case walkthrough. Submit actual notes with `review`:

- `context`: existing authored review fields, source checks and findings. No generic "checked" placeholders.
- `points`: explicit `checked_leaf_refs`, `atomicity_note`, `visible_path_note`.
- `cases`: one entry per case with `case_id`, actual `walkthrough`, `oracle_basis`, `suite_reason`.
- `manifest`: existing review status/checks/findings/notes as applicable.

The tool computes fingerprints and file bindings for those records after mechanical synchronization. It does not supply review prose, decide that a case was reviewed, or weaken review invalidation. A changed tree/case must be actually reviewed again under the existing rules.

```text
<qa-tool> build-deliverables <root> --stage draft
```

This runs the existing gates with operation-local reuse, checks existing human edits, renders XMind and three suite workbooks, updates the same clarification workbook, reads them back, checks layout and publishes the batch. Read its private performance report and any layout-risk locations. Inspect representative normal, rejection, boundary, pending and long-text content; do not reauthor the workbook with another library just to repeat deterministic formatting.

All five existing public names and schema/edit semantics are preserved. Failed generation does not replace previous public files. Transaction journals remain in private work storage with recoverable originals. No process-local cached result survives a command or grants permission; input changes invalidate reuse, and standalone validators remain complete.

## Answers and finalization

Import edited clarification/case workbooks before regeneration. Interpret actual replies, write decisions and scoped amendments, update all affected facts/derivations/cases. To archive questions, upsert complete closed_questions entries with disposition/resolution_refs and explicitly list their IDs in `archive_questions`; no implicit deletion or closure occurs. The existing validators check the resolution authority.

When an authorized correction retires a rule, remove it from active unit `rule_refs` while retaining its evidence and decision. Preserve the original confirmed unit as `before` in that unit's amendment; its baseline fingerprint proves historical ownership without treating the retired rule as active coverage.

Finalization still requires resolved material questions, complete extraction, frozen coverage and current actual reviews. Follow the existing freeze sequence: clear provisional leaf links, freeze the resolved plan, restore preserved links, and review the final tree/cases. `design.stage=final` does not waive these obligations. After final review use `build-deliverables <root> --stage final`; the same five-file output is checked by the full final gates. Executor still rejects drafts and pending business assertions.

## Performance evidence

The private report separates snapshot/edit protection, case validation/rendering, clarification/readback, layout and publication, with elapsed seconds and cache counters. Report layout limits explicitly; do not truncate text or keep adjusting forever. Tool timings exclude model reading/reasoning/authoring; do not present a faster export as an end-to-end result. Retain scope, coverage and oracle checks when comparing runs.
