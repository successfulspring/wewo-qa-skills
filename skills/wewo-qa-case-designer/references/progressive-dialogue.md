# Batched requirement dialogue

Read all available material and build the [whole-business understanding](design-context.md) before asking business questions. Default interaction points are overall understanding with major gaps, then the complete case draft with accumulated questions. These are delivery milestones, not a guaranteed fixed number of replies.

## Overall understanding

Explain who acts, prerequisites, operations, observable results, calculations, limits, exceptions and downstream effects in ordinary business language. Include scope and major contradictory clauses with source anchors. Present known material questions together, grouped by business relationship where helpful. Ask the user to confirm/correct the whole understanding in one reply. Do not substitute headings or technical state dumps.

Distinguish a blocker preventing an agreed scope/main flow from a local missing oracle. Record blocking=true only for the former; settle it before using this baseline for design. Local material questions remain pending in an explicitly disclosed draft. Do not silently exclude behavior. Continue independent reading and analysis while a required answer is pending.

## Draft questions and answers

- Give questions stable readable IDs such as Q1.1 or Q-RU001-01. Retain an ID for the same decision; new decisions get new IDs. Explain ambiguity, source evidence, impact on rules/points/cases and possible treatments. Offer options only when meaningful alternatives are known; otherwise request the actual owner-defined rule.
- Recommend an option only with a source, confirmed rule or explained tradeoff. Convention and convenience cannot establish a product oracle. Accept free-form corrections and compact replies such as Q1.1-B, Q1.2-A.
- Accumulate local uncertainties during design, mark affected expectations pending, and finish known portions. Deliver XMind, all three Excel drafts and the grouped list together. The full workbook contains the shared question sheet; each format needs no separate approval.
- One answer can resolve several questions. “Follow recommendations” covers only unambiguous recommendations actually displayed, not future implications or absent overall confirmation. Partial replies resolve only addressed questions. Silence, “unknown” and “not my decision” leave items pending; do not repeatedly ask the same person to guess.
- A later answer can introduce a material conflict. Review its effects and collect remaining questions into the next coherent batch. Interrupt only when affected work would otherwise invent a consequential fact.

Do not ask the tester to select methods, case counts, priorities or file layout. Designer decides these from confirmed scope and risks.

## Reconcile without repeated approvals

For each real answer, inspect supported effects on ownership, states, data, rejection, prerequisites and downstream consumers. Record one substantive branch review per answer, even if no new branch follows. Do not expand hypothetical implementation internals.

Update decisions, affected rules, points and assertions together. Retain superseded history, removing it from active references. A current explicit business answer authorizes its scoped amendment, not unrelated changes. Preserve the initial summary as evidence. Reconfirm overall understanding only when the new message does not establish a coherent agreed scope/main flow. A local correction, tree presentation change, dialogue entry or Excel view alone does not require another round.

An accepted unresolved risk is not an expected result. Keep it pending in drafts or obtain a specific scope exclusion before finalization, disclosing lost coverage.

## Record and resume

Use existing design-context.json units, questions, exact exchanges, decisions and branch reviews. Points project these records instead of owning another history. Follow [requirement readiness](requirement-readiness.md) for snapshots and amendments.

When later documents supply an answer, use a document decision with the actual applicable approval and the latest displayed question reference. Do not manufacture another question or require the tester to repeat a documented approved answer. New sources without business changes need reading and internal review, not renewed user approval. Preserve unresolved conflicts and reuse the same question IDs across document and dialogue resolution. See [source updates](source-updates.md).

Preserve actual question/options text and raw replies separately from interpretations. A reply to several batches is one event. A combined confirmation and answer is one confirmation event with answer_to referencing its question batches. Record only addressed question IDs. An unsolicited explicit requirement can be an anchored source segment rather than an invented question.

Use actual message references. If no platform ID exists, use a local reference distinguishing conversation, role and occurrence; never invent platform IDs. Unsent questions are drafts, not dialogue evidence. Follow-ups reuse the question ID and append a new event whose revisits maps it to the latest prior occurrence. Current decisions use the latest applicable real answer.

On resume, reconcile state with actual available messages and source versions. Do not duplicate replies on retries, replay answered questions or treat inaccessible history as approval. Reuse verifiable facts and request only missing evidence. Save no private reasoning, credentials or sessions.

Follow the conversation and [delivery language](artifact-contract.md#delivery-language). Source facts, human confirmation, agent review and artifact stage are distinct states.
