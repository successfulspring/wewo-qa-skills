# Batched requirement dialogue

Read all available material and build the [whole-business understanding](design-context.md) before asking business questions. Default interaction points are business understanding plus the standalone clarification workbook, then the complete case draft plus the updated same workbook. These are delivery milestones, not a guaranteed fixed number of replies.

## Overall understanding

Explain who acts, prerequisites, operations, observable results, calculations, limits, exceptions and downstream effects in ordinary business language. Include scope and major contradictory clauses with source anchors. Make major contradictions concrete enough to correct; put every known detailed question, including local unknowns, into requirement-clarifications.xlsx and deliver it with this explanation before any cases. Ask the user to confirm/correct the whole understanding in one reply, without requiring every detail to be resolved first. Do not substitute headings or technical state dumps for the business explanation. The initial workbook must be complete, but answering every local detail is not a condition for agreeing on the overall baseline.

Distinguish a blocker preventing an agreed scope/main flow from a local missing oracle. Record blocking=true only for the former; settle it before using this baseline for design. Local material questions remain pending in an explicitly disclosed draft. Do not silently exclude behavior. Continue independent reading and analysis while a required answer is pending.

## Draft questions and answers

- Give questions stable readable IDs such as Q1.1 or Q-RU001-01. Retain an ID for the same decision; new decisions get new IDs. Write the concrete decision in `description`, not just a topic such as "permissions and state rules". For related decisions under an existing ID, use explicit numbered subquestions in that description so partial answers can be distinguished; unrelated decisions get separate IDs. Include source evidence, business impact and supported options. If the material does not establish alternatives, say exactly which rule or parameters the owner needs to supply instead of inventing options.
- Recommend an option only with a source, confirmed rule or explained tradeoff. Convention and convenience cannot establish a product oracle. Accept free-form corrections and compact replies such as Q1.1-B, Q1.2-A.
- After overall confirmation, autonomously finish known portions and deliver the draft without requesting permission to start or export. Accumulate new local uncertainties during design and mark affected expectations pending. Deliver XMind, all three case drafts and the updated independent clarification workbook together. The question workbook retains every expanded decision, its reply/status and current impact; the case workbooks retain only question references and pending markers. Each format needs no separate approval.
- One answer can resolve several questions. “Follow recommendations” covers only unambiguous recommendations actually displayed, not future implications or absent overall confirmation. Partial replies resolve only addressed decisions: if a question has several subquestions, retain its unanswered parts under the same ID while recording the supported facts. Do not close the whole question or repeat already answered parts. Silence, “unknown” and “not my decision” leave items pending; do not repeatedly ask the same person to guess.
- A later answer can introduce a material conflict. Review its effects and collect remaining questions into the next coherent batch. Interrupt only when affected work would otherwise invent a consequential fact.

Do not ask the tester to select methods, case counts, priorities or file layout. Designer decides these from confirmed scope and risks.

For each question, the independent workbook must contain the actual decision, source, business consequence and supported options or the specific information to provide. Before design, explain the affected business flow/rule and mark cases as not yet generated. After design, populate affected case IDs and readable titles. Grouping must not hide decisions or omit subquestions. If there are no open questions, say so without inventing a clarification round.

For example, "Q3.3: conversion precision" is not answerable. Ask which decimal precision and rounding method apply and whether totals are rounded before or after aggregation. Actual units and alternatives must come from the requirement. Do not force a recommendation when none is supported.

Before the initial reply, verify the business explanation and independent XLSX link are both present and that every known question is answerable in the workbook. Before draft/final delivery, verify five file links and the same workbook's current questions, replies, conclusions and real case links. Chat highlights key conflicts and remaining/new questions; a full duplicated chat list is optional unless requested. Follow the [workbook lifecycle](clarification-workbook.md) for editable answers, retained history and validation. The tester should not need to request a separate file or ask for detailed questions after case generation.

## Reconcile without repeated approvals

For each real answer, inspect supported effects on ownership, states, data, rejection, prerequisites and downstream consumers. Record one substantive branch review per answer, even if no new branch follows. Do not expand hypothetical implementation internals.

Update decisions, affected rules, points, assertions and the same clarification workbook together. Move resolved or explicitly excluded questions into closed_questions with their confirmed resolution_refs; retain their full provenance and do not delete their rows. Retain superseded history, removing it from active references. A current explicit business answer authorizes its scoped amendment, not unrelated changes. Preserve the initial summary as evidence. Reconfirm overall understanding only when the new message does not establish a coherent agreed scope/main flow. A local correction, tree presentation change, dialogue entry or Excel view alone does not require another round.

An accepted unresolved risk is not an expected result. Keep it pending in drafts or obtain a specific scope exclusion before finalization, disclosing lost coverage.

## Record and resume

Use existing design-context.json units, questions, exact exchanges, decisions and branch reviews. Points project these records instead of owning another history. Follow [requirement readiness](requirement-readiness.md) for snapshots and amendments.

When later documents supply an answer, use a document decision with the actual applicable approval and the latest displayed question reference. Do not manufacture another question or require the tester to repeat a documented approved answer. New sources without business changes need reading and internal review, not renewed user approval. Preserve unresolved conflicts and reuse the same question IDs across document and dialogue resolution. See [source updates](source-updates.md).

Preserve actual question/options text and raw replies separately from interpretations. A reply to several batches is one event. A combined confirmation and answer is one confirmation event with answer_to referencing its question batches. Record only addressed question IDs. An unsolicited explicit requirement can be an anchored source segment rather than an invented question.

Use actual message references. If no platform ID exists, use a local reference distinguishing conversation, role and occurrence; never invent platform IDs. Unsent questions are drafts, not dialogue evidence. Follow-ups reuse the question ID and append a new event whose revisits maps it to the latest prior occurrence. Current decisions use the latest applicable real answer.

On resume, reconcile state with actual available messages and source versions. Do not duplicate replies on retries, replay answered questions or treat inaccessible history as approval. Reuse verifiable facts and request only missing evidence. Save no private reasoning, credentials or sessions.

Follow the conversation and [delivery language](artifact-contract.md#delivery-language). Source facts, human confirmation, agent review and artifact stage are distinct states.
