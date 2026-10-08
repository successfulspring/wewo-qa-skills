# QA artifact contract and Excel round trip

## Primary outputs and internal handoff

```text
qa-artifacts/<artifact-slug>/
|-- test-points.xmind             # tester-reviewed test points
|-- test-cases.xlsx               # tester-editable cases
|-- design-context.json           # intake, business model, coverage and decisions
|-- test-points.json              # tree plus context baseline digest
|-- test-manifest.json            # reviewed cases and assertions
|-- source-cache/                 # extracted sources/assets as needed
`-- runs/<run-id>/                # Executor-owned execution artifacts
```

No Markdown case documents are required. Human-readable explanation stays in the conversation and Excel. Preserve concise unit explanations/decisions in the context and point JSON so another session can continue.

Schema versions: context 1.1, points 1.2, manifest 1.4. Points bind to the adjacent `design-context.json` SHA256; the manifest binds to the adjacent confirmed `test-points.json` SHA256 and confirmation timestamp. Do not silently reinterpret older manifests lacking the new coverage/assertion contract. Read them as source material and redesign/review the missing information before generating the current baseline.

## Workbook

One `测试用例` row per case; use the 冒烟/回归/全量 filters instead of duplicating three suite files. Include stable case ID, module path, title, priority/risk, suite membership, targets, per-target automation summary, preconditions, data, actions, expected results, leaf/source/runtime references, safety, cleanup and notes.

`必检断言` has one planned assertion per row, including case/step/target/leaf links, check, observation location, expected result and evidence types. `自动化评估` holds editable per-case-target feasibility, route, conditions and reasons. `运行条件` defines deduplicated `RT-*` needs and safe collection methods. `设计依据` and `设计复查` expose generated coverage derivations and semantic review records. `使用说明` explains editing. `_baseline` is internal metadata; preserve it.

Keep original IDs when editing. Edit automation details in `自动化评估`; the main-table summary and module paths are generated columns. Number action/expected and textual list entries as `1.`, `2.`; indent continuation lines three spaces. Write multiple reference IDs one per line. No formulas in case fields. Review long cells in the formula bar; formatting cannot display unlimited text on a printed page.

## Review and handoff

During dialogue, validate points with `--draft` and render with `--draft` to `test-points.draft.xmind`; the root is visibly labeled 草案（待确认）. Keep known checks concrete and open material questions in the context. Draft validation does not close coverage or enable final cases.

1. Complete source/business/coverage audit and validate context/points; render XMind.
2. Obtain explicit tester confirmation of the rendered tree. Record the exact points digest and time in the manifest.
3. Design detailed cases and planned assertions, then semantically review them. Record checks/findings/resolutions and set manifest `review.status=confirmed` with `reviewed_at`; this records the completed case review, not a fabricated tester response.
4. Validate manifest, render Excel, and validate the Excel readback. Show the tester the two primary outputs.
5. When Excel is edited, import it to `test-manifest.pending.json`. Changed content is marked pending and cannot execute. Compare the delta to requirements, points, step expectations, assertions, targets and safety. Ask only about material unresolved rule changes. Update/confirm affected points if needed, review the candidate, replace the canonical manifest and rerender the workbook.
6. Validate the workbook against the active manifest before execution. A stale baseline or unreviewed Excel edit is a blocking error; do not overwrite edits to make validation pass. Archive previous reviewed baselines when retaining version history is needed.

Internal JSON is a machine handoff; testers work in XMind/Excel. Editing XMind also requires reading the changes back into the tree and business coverage, validating and confirming affected branches. The renderer is not an XMind editor importer: use source extraction/semantic reconciliation and preserve IDs found in labels/notes.

## Runtime requirements and validators

Cases reference shared needs using `runtime_requirement_refs`; automation assessments add only their target's needs. Define environment/build/account/data/device/capability/permission needs at the narrowest applicable scope. Definitions contain no live credentials. Run-time values/session references belong to `execution-profile.json`.

Validators enforce unique IDs, known source anchors and leaves, complete declared rule and leaf coverage, nested suites, target assessments, runtime scopes, planned assertions per step/target/leaf, reviews and baseline hashes. They do not certify the interpretation or completeness of requirements.

```text
<qa-tool> validate-design-context <artifact-dir>/design-context.json
<qa-tool> validate-test-points <artifact-dir>/test-points.json
<qa-tool> render-test-points-xmind <artifact-dir>/test-points.json
<qa-tool> validate-test-manifest <artifact-dir>/test-manifest.json
<qa-tool> render-case-workbook <artifact-dir>/test-manifest.json
<qa-tool> validate-case-workbook <artifact-dir>/test-manifest.json
<qa-tool> import-case-workbook <artifact-dir>/test-manifest.json --workbook <artifact-dir>/test-cases.xlsx
```

The default XMind package is legacy/XMind 8; `--format zen` selects modern JSON. Recursion supports meaningful deep branches with no design depth cap. All generated files use validated canonical data.
