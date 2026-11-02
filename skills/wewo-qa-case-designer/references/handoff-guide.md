# Product and development handoff

Use this guide when someone asks what to provide or how to summarize upstream work. These are content suggestions, not a required Markdown template. Read usable existing documents without requiring a rewrite.

## Shared information

Identify the requirement, applicable version/scope, owner, confirmation status, related materials and unresolved issues. Preserve source references when available. Missing metadata is unknown; ask about it only when it affects a business decision.

## Product material

Include the goal, actors, main flow, business rules, calculations, exceptions and acceptance expectations. Include final decisions made outside the PRD, with their conditions and approval evidence. Distinguish accepted decisions from proposals and abandoned alternatives.

## Development material

Include implemented and unimplemented scope, differences from the requirement and whether those differences were approved, observable interfaces and state changes, necessary configuration/data prerequisites and known limitations. A claim about implementation is not an acceptance result or permission to change a business expectation.

## Suggested summarization prompt

> Summarize the final requirement or development handoff from the supplied material for test design. Identify the applicable requirement and version. Separate confirmed decisions, implementation descriptions, proposals, abandoned alternatives and unresolved questions. Preserve important conditions, numbers, exceptions and source references. Identify differences from the product requirement and the actual evidence approving any change. Do not invent missing information, approvals or test results. Mark unknowns explicitly. The responsible owner should review the resulting document before handoff.

Product material may arrive first. Do not wait for a development handoff before designing cases. For later material, use [source updates](source-updates.md).
