# One clarification workbook from understanding through final cases

`requirement-clarifications.xlsx` is a separate public workbook, first delivered with the whole-business explanation **before overall confirmation or any test points/cases**. Keep this same file through drafting and finalization. Do not embed the inventory in `test-cases.full.xlsx` or create a new question file for each round.

## First delivery

After reading all authorized material, extracting the business and performing the three requirement audits, author every known uncertainty as an answerable `open_questions` entry. Include stable ID, actual decision wording (number related subquestions), source, business impact, and supported options or the specific rule the owner must supply. Distinguish a scope/main-flow blocker from a localized unknown. Do not ask questions while still reading or defer known detailed questions until after case design.

```text
<qa-tool> validate-requirement-readiness <state>/design-context.json --clarification
<qa-tool> render-clarification-workbook <state>/design-context.json
<qa-tool> validate-clarification-workbook <state>/design-context.json
```

These commands need context and a current reading audit, but no confirmation, design plan, points or cases. Overall blockers are allowed here because this workbook is how they are clarified. They still block subsequent case design. Do not manufacture a manifest or test-point IDs to generate this workbook. The early case column explicitly says cases have not been designed; the impact column explains the affected business scope/flow/rule.

Deliver the business explanation, scope, key rules and major contradictions in chat, plus a clickable link to the actual workbook containing **all** known detailed questions. Ask for overall confirmation/corrections and one batch of answers in that same delivery. The tester can edit the yellow Reply column or answer by ID in chat. Allow local items to remain undecided. An empty inventory still produces the same workbook, with no invented questions.

Record the actual displayed workbook questions as one question event, retaining their wording/options, workbook location and message reference. A saved file that was never delivered is not a displayed question event. Overall confirmation is still an actual reply to the business summary; filling a spreadsheet cell does not supply it automatically.

## Read answers and preserve evidence

Before rerendering or applying later documents, read edits using:

```text
<qa-tool> import-clarification-workbook <state>/design-context.json
```

This returns a read-only evidence packet: workbook path, file hash, and exact changed `responses` (`question_id`, `text`). It does not change the context, confirm rules or close questions. Retain the submitted workbook or packet privately. Reconcile a returned older workbook against the displayed question wording; changed questions cannot silently consume old answers. If the tester returned a differently named copy, compare its baseline with the current canonical file and preserve both before replacing the canonical input.

For an actual returned workbook, record one answer event for that submission, with the real message/file reference, exact raw response text and its `responses` array. Link it to the previously displayed question batch(es), and include only addressed `question_ids`. For chat answers, preserve the exact reply as usual; `responses` is optional when no cells were submitted. Do not invent an answer event from generated cells, an unchanged workbook or inferred agreement. Imports can be retried without creating another event for the same reply.

Interpret the real answer into existing decisions and branch reviews, and update affected rules/points/cases through existing evidence and scoped-amendment checks. Ambiguous, partial or undecided answers remain open; retain answered facts and narrow only the unresolved subquestions. A cell edit is evidence to interpret, not an automatic confirmed decision. Corrections supersede the corresponding earlier decisions.

When resolved or explicitly excluded, move the question from `open_questions` to `closed_questions`, retaining its ID, description, source, impact and options. Add `disposition: resolved|excluded` and `resolution_refs` referencing its current confirmed decision(s). Preserve original fuller wording in the displayed question events when subquestions were narrowed. Exclusion requires an explicit supported decision and disclosed lost coverage. Do not just delete answered rows. Reopening moves the same decision back into the open queue; a genuinely different decision gets a new ID.

The workbook derives status, current reply, resolution, evidence and case links from this shared context. Previous raw replies remain in the event history. User cells cannot override generated status or question definitions. Rerendering refuses to discard unrecorded answer edits or omit previously tracked questions.

## Update alongside cases

After real overall confirmation, finish known case design without another permission-to-generate prompt. Keep local pending assertions non-executable. Accumulate new questions and continue independent work. After updating and validating the manifest, run:

```text
<qa-tool> render-clarification-workbook <state>/design-context.json --draft
<qa-tool> validate-clarification-workbook <state>/design-context.json --draft
```

The renderer discovers a sibling manifest when present and validates its bindings and confirmation; stale cases cannot supply current impacts. The same workbook gains real case IDs/titles and point links, updated conclusions and new questions. Retain old question IDs and actual responses. Deliver its link **again**, together with XMind and the three suite files. Highlight newly added/remaining questions and request one batch response. The independent clarification workbook contains the complete details; chat should explain the business and changes, not duplicate every spreadsheet cell. `render-open-questions` remains available for an expanded chat view when useful or requested.

Before final delivery, reconcile responses, resolve included material expectations, regenerate this workbook without `--draft`, and validate it with the four design files. Closed rows remain as history. There is no extra spreadsheet-format approval or independent question-sheet confirmation round.

For an existing baseline from an earlier version, import case edits first and preserve the old full-workbook question rows before replacing its format. Reuse real recorded questions/answers to populate active and closed context records. Generate the independent workbook from this baseline; do not require a new overall confirmation merely to move the question inventory.
