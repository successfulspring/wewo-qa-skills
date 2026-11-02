---
name: wewo-qa-case-designer
description: Design and maintain tester-facing cases from product and development materials, including later handoffs. Confirm initial business understanding, deliver XMind and three Excel drafts with grouped questions, and update affected cases from approved evidence or batch answers. No product source or test execution is required.
---

# Wewo QA Case Designer

Default sequence: read all requirements → explain the business → obtain one overall confirmation → design autonomously → deliver the four draft files with one question list → incorporate batch answers and finalize. Do not turn every uncertainty, test-design choice or artifact format into another user approval.

If a usable design baseline already exists, follow [source updates](references/source-updates.md): reconcile Excel edits, read new material, compare with confirmed rules, update affected cases and deliver changes with grouped questions. Reuse prior confirmations; do not restart the initial workflow because another document arrived. Product material alone can start design. Read the [handoff guide](references/handoff-guide.md) only when upstream contributors need content guidance; do not require a fixed template or a development document.

Keep Skill instructions and examples in English. Select delivery language from explicit preference, then sustained conversation language, then source language, defaulting to Chinese. Apply [delivery language](references/artifact-contract.md#delivery-language) consistently; preserve original quotations, identifiers and literal test values.

## 1. Read and explain the whole business

Resolve the bundled [runtime](../runtime-tool.md) and [private state layout](references/artifact-contract.md). Read every authorized document, image, table, prototype and link before asking business questions. Inventory authority, versions and unread content using [source intake](references/source-intake.md). Inaccessible material needs a usable export, authorized viewing or an explicit scope exclusion. Consolidate access problems while continuing to read available material; never invent contents.

Preserve anchored source text, extract each clause into requirement_items and build [design context](references/design-context.md): objects, roles, ownership, states, flows, relationships and rules. Document headings are source anchors, not the business explanation. Product source, database internals and a running implementation are not design prerequisites. Examples supply techniques, never undocumented project facts.

Separate business requirements from implementation reports at clause level. Supplied development documents may explain observable contracts and preparation, but an implementation gap does not change a confirmed oracle. Reuse actual applicable approvals; source role, AI authorship and a newer date alone never authorize replacing requirements. Consolidate genuine conflicts about correct behavior; preserve known expectations when only the reported implementation differs.

Present one plain-language explanation covering who acts, prerequisites, ordered steps, changed state/data, observable results, important formulas with units/rounding/boundaries, exceptions and downstream effects. Include in/out scope and major contradictions or missing rules, with sources and impact. Run the three [requirement audits](references/requirement-readiness.md) first. The user should be able to correct the whole understanding in one reply.

## 2. Confirm understanding once

Use [batched dialogue](references/progressive-dialogue.md). Ask for overall confirmation and corrections in the same consolidated message as the explanation. Questions have stable IDs, explain ambiguity and impact, and offer meaningful options when supported. Do not ask the tester to choose testing techniques, tree depth, IDs, priorities or worksheet organization.

Overall confirmation approves the stated scope and known rules, not unknown expectations. Disclose localized unresolved items and keep them pending; they do not prevent a draft. Only ambiguity that prevents a meaningful agreed scope or main flow blocks the overall baseline. Consolidate such blockers. Reuse applicable confirmation; another message or artifact view is not a reason to ask again.

Preserve the displayed summary and actual reply with message references and the business snapshot, following [confirmation records](references/requirement-readiness.md). One real reply may both confirm the summary and answer its questions. Explicit corrections update affected facts through scoped amendments. A new overall summary is needed only when the reply does not establish an agreed overall scope/flow. Before design, run validate-requirement-readiness with --draft --confirmed. Never fabricate exchanges or approve facts for the user.

## 3. Design and keep progressing

Derive applicability, factors, scenarios and independent outcomes from source clauses and confirmed facts **before** leaves/cases, following [test design](references/test-design.md). Select methods, boundary partitions, priorities and suites autonomously from business risk. Keep one leaf per independent observable outcome; separate distinct inputs/states/action paths. A coherent case may contain several step-bound assertions. Do not impose fixed counts or depths.

For localized uncertainty, add one open_questions entry with source, impact and options. Mark affected rules/outcomes/leaves/assertions status=pending with matching question_refs; omit unknown expected values and executable comparisons. Display “Pending confirmation” in the delivery language. Continue known steps, data, outcomes and other cases. Never invent a business oracle or turn an entire case into a placeholder because one result is unknown. Keep coverage_plan.status=draft until obligations are resolved; drafts do not require freezing.

Write reproducible preparation, data or unique selection criteria, ordered actions, step expectations, observation locations, timing and cleanup. Assess automation per target after coverage design, preserving UI/interface evidence. Runtime IDs, selectors and sessions belong to Executor. Known comparisons stay concrete; pending business expectations are not runtime conditions.

Perform source-first omission and visible-tree reviews before rendering, including drafts. Review known case paths and disclose unresolved parts. Internal review records are agent work, not extra tester approval. Read [semantic review](references/test-design.md#semantic-review).

## 4. Deliver the draft and questions together

Set points and manifest stage=draft. Export test-points.xmind and all three test-cases.smoke.xlsx, test-cases.regression.xlsx and test-cases.full.xlsx with --draft; validate the four files together with validate-deliverables --draft. Smoke ⊆ regression ⊆ full, sharing stable case/point/assertion IDs. Keep these public filenames through refinement.

Deliver four clickable links, suite counts and one grouped question list in the same response. The full workbook's visible **Open Questions** sheet is the durable list; all case/assertion views carry question references and status. Each question states what is unclear, its source, affected rules/points/cases and possible treatments. For an entirely unknown decision, request the owner-defined rule instead of inventing options. Reconcile questions in context and regenerate views; the tester need not maintain separate lists for requirements, XMind and Excel.

Invite one batch answer. Partial answers resolve only addressed items; the remainder stays visible in the draft. New local questions accumulate for the next coherent delivery instead of interrupting each case. Do not promise exactly two replies when a real answer introduces a new material conflict.

## 5. Refine and finalize

Reuse the initial confirmation and actual batch answers. Update decisions, scoped amendments and all affected rules, outcomes, points and assertions together. Retain unchanged IDs, superseded history and question provenance. A business answer authorizes its supported changes; do not ask for separate summary, XMind and Excel approvals. Clarify only a remaining material conflict or genuinely ambiguous answer.

Before finalizing, resolve all included material questions or obtain an explicit scope exclusion with lost coverage disclosed. Remove pending markers only after authoritative resolution; fill concrete expectations/comparisons and reconcile extraction and current unit/decision views. Clear candidate leaf links, freeze the resolved coverage plan, then reattach preserved leaves and renew affected source/tree/case reviews. Set points and manifest stage=final. Run final validations and regenerate the same four files. No pending business assertion may enter Executor.

Import Excel edits before regeneration; reconcile conflicting overlapping views, preserve edits and review changed cases. An expectation proposed in Excel stays pending until business authority is established. Use [artifact contract](references/artifact-contract.md) for commands and legacy migration.

Keep JSON, caches and helpers under .qa-state/ or temporary storage. Do not delete user inputs to clean the delivery root. Inspect exported topic titles and representative normal, rejection, boundary and related-object workbook rows, and validate all readbacks. Final completion requires actual overall confirmation plus necessary scoped answers, closed material expectations, current semantic reviews and four consistent public files. Validation establishes consistency, not business truth or exhaustive coverage. Execution is a separate Skill.
