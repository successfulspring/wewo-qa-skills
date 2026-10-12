# Execution preflight and readiness

## Inputs and discovery

Accept the Designer artifact directory, environment entry point and requested suite/targets. Infer unambiguous supplied scope; ask only when the choice materially changes execution. Validate all workbook views and the reviewed baseline before using them.

Inspect reachability, login entry, deployed version evidence, authorized interface documentation and available browser/device/runtime tools. Product code is not an input requirement. Observe first; do not create or delete business data until its case prerequisites and existing authorization are understood.

Use `prepare-execution-profile` to create draft profile 1.2. It records:
- `environments`: one identity per target, with entry, build and verification evidence. A supplied build string is a claim until checked against a version surface, deployment record or package identity. Unknown identity remains pending.
- `discovered_requirements`: additional execution-only needs found during reconnaissance, using the same runtime requirement shape as the manifest. Use distinct RT IDs and attach them to the affected case readiness records.
- `bindings`: current availability and safe values/references for manifest and discovered requirements.
- `case_readiness`: every selected case-target, with candidate route, additional requirement refs and actual checks for interaction, observation, data, cleanup and tooling.

A check contains area, status and substantive detail. Record pending/blocked until inspected. Use not-applicable only with a case-specific reason; interaction, observation and tooling must be verified before automation. A ready pair requires all its bindings resolved and a verified target environment. Manual pairs remain manual until the design assessment is reviewed and changed upstream.

Build the union of needs, deduplicate shared requirements, then ask one grouped batch for actual gaps: account/role/login authorization, data or permission to prepare it, environment/services, device access and capabilities. A URL is a value request, not an artificial multiple-choice question. Preserve the user's answers and the checks they resolve. Partial answers resolve only their covered needs; unavailable resources are not repeatedly requested without new evidence. Continue independent ready pairs.

Secrets stay in approved secret/session references. When a safe credential mechanism is unavailable, let the tester log in and reuse the authorized session. Profiles, code, reports and evidence must not contain passwords, cookies, tokens or one-time codes.

## Prepare and freeze

```text
<qa-tool> prepare-execution-profile <manifest> --suite <suite> --target <target> --output <run>/execution-profile.json
<qa-tool> validate-execution-profile <run>/execution-profile.json <manifest>
```

Preparation creates pending records, not evidence that a check happened. The validation command reports ready/blocked counts; structurally valid does not mean ready. Add discovered requirements and bindings as actual discovery proceeds. Never edit the business expectation to make a requirement disappear.

Before the first runner invocation, freeze the profile by using its digest in the plan. After execution starts, do not rewrite that profile; newly resolved conditions require a new run with preserved prior evidence. A new build also starts a new run. Each ready binding is verified independently, so an unavailable unrelated target does not stop it.

Legacy profile 1.1 is readable for historical evidence, but a new execution requires fresh 1.2 preflight. Do not upgrade old records by inventing successful checks.

## Data and action boundaries

Use reproducible starting data identified by stable non-sensitive keys. Prepare isolated data through authorized interfaces/UI or existing fixtures; verify it before the business action. Track created/changed records and cleanup responsibility. Do not assume database or admin access.

Apply existing authorization for ordinary scoped testing. Obtain additional authorization only for consequential actions outside it or when required by the confirmed case. If the entry appears to be production or differs from the authorized target, stop affected mutations.

Tests emit preparation and cleanup lifecycle observations. Verify cleanup before relying on restored state; an attempted delete is not proof of cleanup. Capture failure evidence before cleanup. A cleanup failure remains visible and prevents an overall clean pass; stop dependent tests whose starting state may be contaminated.

## Runtime readiness

Reuse declared automation tooling, mature runners and host-provided runtimes. If missing dependencies can be configured in the authorized independent workspace, do so and verify an actual launch. Do not claim a browser install, device connection or login worked without checking. Avoid modifying global development environments unnecessarily.

Missing capabilities leave affected pairs blocked with the exact resource/action needed. Lack of product source is not a blocker. Missing business rules return to Designer; ordinary runtime setup belongs here.
