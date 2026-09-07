# Execution result contract

The bundled runtime validates each result set against `references/schemas/execution-results.schema.json` from this Skill.

## Output layout

Create one immutable run directory beside the case artifacts:

```text
qa-artifacts/<artifact-slug>/runs/<run-id>/
|-- execution-profile.json
|-- execution-results.json
|-- test-execution-report.md
`-- evidence/
```

Never mix evidence from separate runs. Use relative evidence paths inside the run directory. Freeze the execution profile before product interaction. The result JSON records SHA-256 digests of both the exact manifest and execution profile used.

## Verdicts

- `passed`: observed behavior matches every required oracle; includes at least one passing assertion and evidence.
- `failed`: deterministic product behavior contradicts an oracle; includes the mismatch, failure reason, and evidence.
- `blocked`: execution could not reach a verdict because a prerequisite, capability, authorization, account, device, or environment was unavailable.
- `flaky`: equivalent controlled attempts gave inconsistent outcomes; includes at least two attempts and evidence.
- `not-run`: intentionally excluded from automation, including `manual-only`, or not started after an explicitly documented stop.

Tool or environment failures are not product failures. Product failures are not silently converted to blocked because a retry later passes.

## Commands

```powershell
<qa-tool> validate-execution-results <run-dir>/execution-results.json <artifact-dir>/test-manifest.json
<qa-tool> render-execution-report <run-dir>/execution-results.json <artifact-dir>/test-manifest.json --output <run-dir>/test-execution-report.md
```

The renderer validates before writing. Fix the structured result rather than hand-editing the generated report.
