# Execution policy

The bundled runtime validates each run profile against `references/schemas/execution-profile.schema.json` from this Skill.

## Structured preflight

The manifest declares what execution needs; the run profile records what is actually available. Before interacting with the product:

1. Select the suite and targets, then collect the union of `case.runtime_requirement_refs` and the selected target automation assessment's `runtime_requirement_refs` for every non-manual pair.
2. Deduplicate by requirement ID. Inspect current tools, environment, and authorized sessions before asking the tester for anything discoverable automatically.
3. Generate `<run-dir>/execution-profile.json` with the command below. It creates exactly one `missing` binding for every selected requirement; do not delete a binding because it is inconvenient.
4. If user-resolvable items remain, ask once in a compact grouped batch. Group environment/build, account/authentication, test data, device/capability, and permissions. Ask for direct values where values are needed; when a genuine choice exists, provide lettered options, a recommendation and its basis, plus a free-text path. Do not invent A/B/C/D choices for a URL or account identifier.
5. Accept a combined response. Recheck what it resolves, validate the profile, state any remaining blockers, and begin every ready pair. Do not repeatedly interrogate the tester for items they marked unavailable or declined.

Typical run inputs include the test environment identity and URL, application build or installed package, account roles and non-secret identifiers, seeded test-data references, required device and control capability, and allowed side effects with cleanup responsibility.

```powershell
<qa-tool> prepare-execution-profile <artifact-dir>/test-manifest.json --suite <suite> --target <target-id> [--target <target-id> ...] --output <run-dir>/execution-profile.json
```

The profile stores live non-secret values and safe references only. Do not place passwords, cookies, tokens, one-time codes, private keys, or equivalent secrets in the manifest, profile, result JSON, screenshots, commands, report, or ordinary conversation. Resolve a sensitive requirement through the environment's approved secret reference. If none exists, ask the tester to perform login and reuse that authorized session; record only a session reference.

Validate the frozen preflight before product interaction:

```powershell
<qa-tool> validate-execution-profile <run-dir>/execution-profile.json <artifact-dir>/test-manifest.json
```

Supplying a runtime condition does not authorize unrelated environment changes or consequential side effects. Confirmation requirements below still apply just in time.

## Environment and safety

Default to an identified test environment. If the target appears to be production or its identity is uncertain, stop before mutation and obtain explicit authorization for that environment and action.

For a case marked `requires_confirmation`, obtain confirmation immediately before the consequential step. Examples include irreversible deletion, payment, outbound communication, public publishing, or changing shared/production data. Existing authorization for ordinary test execution does not authorize these effects.

Verify cleanup steps before execution. If cleanup cannot be performed safely, mark the case blocked rather than contaminating later cases.

## Determinism and evidence

- Prefer stable roles, labels, accessibility nodes, test IDs, and explicit states over coordinates or timing guesses.
- Wait on observable state transitions, not arbitrary sleeps.
- Use seeded or uniquely named test data and record only non-sensitive identifiers.
- Capture the minimum evidence sufficient to prove the assertion. Always capture failure state before cleanup when safe.
- Console, network, logs, or storage may supplement an externally observable outcome; they may not replace it or create an API test route.

## Retries and flaky results

Do not retry merely to obtain a pass. One controlled retry is allowed to distinguish transient tooling/environment behavior from a reproducible product failure when it does not repeat an irreversible effect. Record both attempts.

Use `flaky` only when equivalent controlled attempts produce inconsistent verdicts without a known intentional state change. A tool crash, missing device, expired account, or unavailable environment is `blocked`, not flaky. A consistent product mismatch is `failed`.

## Stop conditions

Stop the affected case or run when:

- the actual target or account differs from the authorized one;
- an unapproved consequential action is next;
- the oracle is ambiguous or contradicts the manifest;
- continuing could corrupt shared data or invalidate remaining evidence;
- the required tool, device, account, or environment is unavailable.

Preserve completed results and mark remaining pairs `blocked` or `not-run` with the concrete reason.
