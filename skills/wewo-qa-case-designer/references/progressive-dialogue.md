# Progressive requirement dialogue

Use this procedure after building the whole-business draft in [design context](design-context.md). Discuss shared prerequisites before dependent behavior. The goal is a shared, testable business understanding; the number of rounds or questions does not determine completion.

## One business topic per round

Choose the unresolved topic with the greatest effect on scope, behavior or expected results. Explain the relevant source fact and current understanding briefly, then ask the related questions. Use natural, concise prose; source/background/impact are useful context, not five mandatory headings. Do not repeat the whole model or a status table every turn. Make corrections to stated facts easy.

Usually ask 2–5 closely related questions that can be answered together. This is a readability preference, never a quota or limit. Ask one when other questions depend on that answer; split a large topic. Do not mix independent modules or ask the user to rediscover facts already explicit in readable sources.

After each actual answer, reconcile it with the sources, update the affected understanding and inspect newly unlocked consequences. Briefly reflect consequential decisions/corrections and remaining uncertainty before the next topic. Propagate a shared rule to its consumers rather than asking it independently in each module. Continue independent topics while an owner answer is pending, keeping dependent outcomes open.

Follow the user's conversational language and maintain the [delivery language](artifact-contract.md#delivery-language) accordingly. A sustained English clarification can establish English delivery despite Chinese source material; an isolated quoted phrase does not change the selection. Preserve exact questions/replies in their original language when recording evidence.

## Questions and answers

- Give a new question a readable stable ID such as `Q1.1` or `Q1.2` (initial round and question). Keep that ID when following up the same decision in a later round; a newly discovered decision gets a new ID. Preserve existing IDs such as `Q-RU001-01` when resuming older work.
- Choose the answer form that fits the uncertainty. Use 2–4 lettered options only when meaningful alternatives are known, label single/multiple selection and ensure combinations make sense. Otherwise ask an open question, especially for an unknown flow, ownership rule or exception. Always accept a free-form answer.
- Recommend an option only when source evidence, a confirmed rule or an explained tradeoff supports it. State that basis and the material consequence. When the product rule is unknown, omit the recommendation; record the question for the responsible owner instead of inventing a safest testing default. Industry convention is not a confirmed product rule.
- Accept compact replies such as `Q1.1-B, Q1.2-A+C`. Free-form corrections take precedence over proposed options. “Follow all recommendations” applies only to unambiguous recommendations actually displayed in the referenced batch, not open questions, unrecommended choices, future consequences or final requirement confirmation.
- A partial reply resolves only its addressed questions. If its scope or meaning is ambiguous, clarify that part and keep the rest of the topic moving. “I don't know”, “not my decision” and silence leave the question pending; identify the owner or requested evidence without repeatedly asking the same person to guess.
- If a previous question needs narrower wording, a changed option or a corrected answer, reuse its ID and append a new question event linked to the prior occurrence. Do not overwrite the old wording or reassign the ID to another decision. Decisions must cite the actual reply to the applicable occurrence; a prior answer cannot close a renewed question.

When an answer establishes that an operation is allowed, inspect which consequences are still unknown: the affected entity's resulting state, related entities or associations, data changes and observable completion. Ask only about relationships supported by the current requirement. Do not infer those consequences from permission to perform the operation. Separate newly discovered decisions into related questions that can be answered together; defer any question whose premise remains unresolved.

## Expand, reconcile and checkpoint

For every material answer, follow its effects on actors/ownership, states, data, rejection/partial success, upstream prerequisites, downstream consumers and observable acceptance. Record a branch review even when no new material branch arises, with a reason. Add new unknowns with their parent decision and business impact. Expand product behavior relevant to this requirement, not hypothetical storage, API or implementation choices.

When a rule changes, retain the prior decision as superseded with its replacement ID, update every consumer and reopen affected units. Remove contradicted facts from active understanding while preserving their history. Existing source facts need another question only when new evidence or a conflict warrants it. Accepting an unresolved risk does not create a test oracle: clarify it or explicitly narrow the final scope and disclose the lost coverage.

At a meaningful topic boundary, or after a correction changes several modules, show a compact consolidation of the business rules and unresolved consequences so the user can correct it. Use a table only if it improves readability. These checkpoints do not require separate approval of every fact. Before proposing final confirmation, run all three [pre-summary audits](requirement-readiness.md#three-audits-before-the-final-summary), resolve material gaps, then present the consolidated requirements and request explicit confirmation. Module approval and individual answers do not replace that confirmation.

## Record and resume

Keep canonical units, exact visible exchanges, parsed decisions, branch reviews and open questions in `design-context.json`, following [requirement readiness](requirement-readiness.md). No test-point tree or separate Markdown history is needed during discovery. Later `test-points.json` projects current units/decisions instead of maintaining another understanding.

Preserve actual question/options/recommendation text and raw replies separately from interpretations. One reply addressing several questions or earlier batches is one event, referenced by all resulting decisions. Record only the questions actually addressed; unanswered items stay open. Unsolicited explicit user requirements may be anchored source segments with the actual message reference instead of an invented question. Save no private reasoning or credentials; use redaction markers and actual references for secrets.

Synchronize state after each actual exchange, before the next batch. A prepared question is a draft, not evidence that it was displayed: keep unsent text out of `dialogue_events`. On interruption/resume:

1. Read the saved context and reconcile it with available actual messages and current sources. Reuse the same event ID for an exchange already recorded; append missing verifiable events in actual chronological order. A retry must not duplicate a reply or turn a saved draft into a displayed question.
2. Prefer the host's actual message ID. If unavailable, use a local reference that distinguishes role, conversation/round and occurrence; preserve exact text. Identical words in different actual replies are different events. Do not invent platform IDs or fabricate inaccessible history.
3. Reconcile partial/late answers, corrections and open branches before choosing the next topic. Restore pending questions without restarting completed topics. If the last question was truly displayed and unanswered, continue that pending question instead of silently treating it as resolved or needlessly issuing another batch.
4. Treat historical conclusions as leads. Compare current project, version, scope and authority; generated files and old “confirmed” flags are not new approval. If essential history is missing, explain the specific gap, reuse verifiable facts and obtain the missing clarification/confirmation. Preserve original history; update active conclusions and stale downstream gates.

Final requirements, XMind review and case review are distinct states. Keep unanswered material facts visible and do not use draft rendering to bypass dialogue or confirmation.
