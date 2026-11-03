# Requirement readiness and confirmation

This requirement-only gate needs no test tree, plan or cases. Draft readiness means the whole scoped understanding was read and reviewed with local unknowns disclosed. Final readiness also requires resolved material business expectations.

Use `record-design-dialogue` for mechanical event linkage and baseline capture, following [structured authoring](efficient-authoring.md). Supply the exact actual display/reply, its real message reference and the authored interpretation. The tool cannot decide that a reply approves a rule, cannot close questions by itself, and must preserve the initial confirmation for scoped changes.

The pre-confirmation `--clarification` route checks complete reading and audits while allowing overall blockers to be presented for clarification. It cannot be combined with `--confirmed` or replace the later design gate. See [independent workbook](clarification-workbook.md).

## Three audits before the summary

1. **Business coverage**: compare original text, tables, notes and diagrams with the full journey: scope, actors, ownership, prerequisites, actions, limits, states, data changes, exceptions, downstream effects and observable results. Keep independently defined lifecycles separate. Record meaningful gaps instead of guessing them.
2. **Branch expansion**: inspect consequences of answers and shared rules across consumers, including unchanged surfaces. Record unanswered consequential branches with impact. Expand requirement-supported behavior, not hypothetical implementation internals.
3. **Decision provenance**: read each rule's exact source, current real answer or applicable document approval. IDs alone do not prove semantic support. Resolve authority conflicts or disclose them in the question list. Recommendations, reported implementation and industry convention are not product oracles. A clear implementation gap keeps the confirmed requirement intact; only ambiguity about correct behavior makes an oracle pending.

Perform these before showing the overall explanation. Local unresolved findings remain visible and pending; they do not prevent a useful draft. An ambiguity preventing agreement on scope/main flow blocks that baseline. Before finalization resolve included material questions or obtain explicit exclusions, disclosing lost coverage.

## Private state contract

Context schema 1.6 retains the existing records and accepts legacy dialogue evidence:

- requirement_units hold current id/title/source_refs/understanding/confirmed_facts, depends_on and rule_refs. Status is unreviewed, discussing, waiting, confirmed or excluded. Confirmed means known material facts, not a separate user approval. Excluded units need an exclusion_reason and no active rules.
- open_questions carry id, unit_id, description, impact, material and optional parent_decision_ref, source_refs, options and blocking. Use blocking only when an agreed overall baseline is impossible. Local material questions remain blocking=false or omitted. Move resolved items into optional closed_questions only after recording their answer and updating affected expectations. Closed entries preserve the question fields and add disposition=resolved|excluded and resolution_refs to current confirmed decisions for that same question; they cannot also remain open.
- dialogue_events preserve actual chronological id/kind/text/message_ref. A saved draft is not a displayed exchange.
  - question has question_ids. A repeated ID uses revisits to identify its latest previous question event.
  - answer uses in_reply_to for one earlier question event or an array of batches. question_ids identifies only addressed questions, required for multi-question batches. Preserve a real reply once. Returned clarification workbooks may add responses=[{question_id,text}] for the exact per-question cell text in that single answer event; these must match addressed question_ids and do not automatically confirm decisions.
  - summary binds its displayed business understanding to snapshot_sha256.
  - confirmation has one summary ID in in_reply_to. When the same reply also answers questions, answer_to lists earlier question event IDs and question_ids lists addressed IDs. Decisions may cite that combined reply. Do not split it into fabricated separate messages.
- decisions preserve parsed resolutions and their evidence_kind. Dialogue decisions cite the latest real answer to the latest question occurrence through response_event_ref. Document decisions cite requirement_refs, approval_refs, approved_by and applicability as specified in source updates; no synthetic reply is needed. Superseded decisions retain superseded_by but cannot support active rules/extraction/points. Assumed decisions never become confirmed by a bulk status change.
- branch_reviews describe each actual answer or source update's impacted unit_refs and substantive opened/eliminated consequences. Use exactly one of answer_event_ref or source_update_ref. A multi-question reply has one review.
- requirement_review has status=ready, current snapshot_sha256 and three checks: business-coverage, branch-expansion, decision-provenance. Each accounts for all current units. This is agent audit evidence, not approval.

Continue extraction while reading. Empty rules, factors and design_models are valid before design; never fabricate a plan for a digest. Extract every included source clause and active decision. Use explicit pending dispositions for ambiguities rather than dropping them.

## Overall confirmation

1. Complete reading and audits. Run requirement-digest with --snapshot to obtain snapshot_sha256 and the per-entity baseline. Store the current digest in requirement_review.
2. Run validate-requirement-readiness with --draft. Display one business explanation with scope, rules, main contradictions and local pending items; preserve the exact text as a summary event.
3. On actual overall agreement, record the confirmation event and requirement_confirmation: status=confirmed, confirmed_at, actual response_ref/response_text, summary_event_ref, response_event_ref, snapshot_sha256 and baseline from that displayed snapshot. An explicit correcting answer can confirm the understood remainder and supply scoped amendments; ambiguity about overall agreement still needs clarification.
4. Run validate-requirement-readiness with --draft --confirmed. Then derive the plan, points and cases. Draft export permits local pending rules/outcomes/assertions; final readiness, freezing and execution do not.

Overall agreement never confirms a missing expected value. Do not render design artifacts before this overall gate, but do not impose full oracle closure before draft export.

## Scoped amendments

For later product/development documents, follow [source updates](source-updates.md). An evidence-only addition does not need another human reply; a business change needs a scoped confirmed dialogue or document decision. Document decisions preserve anchored business clauses and actual approval evidence, not synthetic question/answer events. Source-triggered branch reviews complement the existing reviews of actual answers. Keep the original overall confirmation and use draft-only pending amendments for local unresolved changes.

The business snapshot fingerprints PROJECT and each source, segment, object, relationship, flow, requirement unit and rule. It excludes output language, dialogue bookkeeping, question queues, decision references and later test derivations. A later message, question entry or language change alone therefore does not invalidate overall agreement. File hashes still bind current artifacts and must be updated after real changes and reviews.

Keep the original summary, reply, baseline and digest intact. Business amendments carry ref (the changed entity ID), sha256 (its current fingerprint, or null for deletion), and decision_refs to supporting confirmed dialogue or document decisions. Actual answers must follow the displayed summary; they may be the same combined confirmation reply. An approved document may predate its later intake when its content is still applicable. A rule amendment must reference its owning unit's decision and include that decision in the rule. Evidence and pending amendments instead require source_update_ref and the restrictions in source updates; preserve before for an entity present in the original baseline. Update all affected entities, not just the question queue. Run requirement-digest --snapshot to compute current fingerprints; this command never writes approval.

Refresh the agent requirement review after reconciling changes. An unrecorded business change, stale resolution or unrelated-unit decision fails validation. Semantic review must also check that the cited evidence supports each change; hashes cannot establish that meaning. Do not rewrite the initial summary hash to make changed facts appear previously approved.

If no baseline map exists, a matching original snapshot still works for unchanged content. Recover its baseline map before applying changes; only a new overall confirmation can replace unrecoverable overall evidence. Changed business facts need actual scoped answers or document approvals, while evidence-only intake preserves business meaning. Legacy 1.4 digest semantics included conversation history: treat those records as review input, reuse verifiable history and preserve the original evidence; do not simply relabel versions or invent old confirmation.

Final readiness (without --draft) requires complete extraction, current decisions and branch reviews, resolved units/material questions and no assumed or pending business rule. It precedes freezing the final plan and final artifact validation. No additional XMind-specific human confirmation is required.
