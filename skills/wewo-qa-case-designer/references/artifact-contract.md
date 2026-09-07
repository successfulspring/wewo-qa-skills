# QA design artifact contract

## Output layout

Write one artifact set per requirement or release:

```text
qa-artifacts/<artifact-slug>/
|-- requirement-walkthrough.md
|-- test-points.json
|-- test-points.xmind
|-- test-manifest.json
|-- smoke-test-cases.md
|-- regression-test-cases.md
`-- full-test-cases.md
```

`requirement-walkthrough.md` is the human-readable ledger of units, dialogue batches, answers, corrections, assumptions, and module confirmations. Maintain it during the conversation.

`test-points.json` is the authoritative confirmed test-point baseline. `test-points.xmind` is its deterministic visual projection and must be reviewed before case generation.

`test-manifest.json` is the authoritative detailed-case baseline. The three case Markdown documents are deterministic suite projections. Never edit generated views independently.

The manifest also owns the execution-readiness contract:

- `runtime_requirements` declares reusable `RT-*` needs without their live values;
- case-level `runtime_requirement_refs` applies to all of that case's targets;
- each automation assessment's `runtime_requirement_refs` adds only that target's needs;
- live non-secret values and safe secret/session references belong in a run's `execution-profile.json`, never in the manifest.

## Stage gates

1. Do not finalize `test-points.json` while a material requirement unit is unresolved.
2. Validate `test-points.json` and render `test-points.xmind`.
3. Obtain explicit user confirmation of the rendered test-point baseline.
4. Only then create `test-manifest.json` and its Markdown projections.

If the user corrects a requirement after the XMind confirmation, update the walkthrough and test-point baseline, render it again, reconfirm affected branches, and then update cases while preserving unaffected IDs.

## Canonical contracts

Use `references/schemas/test-points.schema.json` and `references/schemas/test-manifest.schema.json` from this Skill. The validators additionally enforce:

- stable, unique source, decision, requirement-unit, test-point, target, and case IDs;
- every non-root test-point node traces to a requirement unit and a source or decision;
- every assumed unit, decision, or test point includes rationale;
- no unresolved material unit in a final baseline;
- the manifest references the exact SHA-256 of adjacent `test-points.json`;
- every case references known leaf test points;
- every included leaf test point is covered by at least one case;
- source, target, automation, safety, and `smoke ⊆ regression ⊆ full` invariants.
- unique runtime-requirement IDs, valid scopes and target associations, known references, no unused declarations, and safe collection paths for sensitive credentials.

Use source references such as `SRC-001#支付规则` and decision references such as `DEC-003`.

## Commands

```powershell
<qa-tool> validate-test-points <artifact-dir>/test-points.json
<qa-tool> render-test-points-xmind <artifact-dir>/test-points.json --output <artifact-dir>/test-points.xmind
<qa-tool> validate-test-manifest <artifact-dir>/test-manifest.json
<qa-tool> render-case-docs <artifact-dir>/test-manifest.json --output-dir <artifact-dir>
```

The XMind renderer defaults to the XMind 8-compatible legacy package used by the supplied Wewo sample. Use `--format zen` only when the user or project requires the modern format.

If validation fails, fix the canonical JSON and rerender. Do not patch generated files to hide inconsistency.
