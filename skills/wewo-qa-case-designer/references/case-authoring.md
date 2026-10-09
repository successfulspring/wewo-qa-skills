# Executable tester cases

First reconstruct how a tester would perform the scenario. Then write the case.

- Preconditions describe the starting environment, permissions and business state.
- Test data gives the actual input/setup values, representative boundary values or reproducible selection/seeding criteria. Do not repeat the precondition under another heading or list post-action expected results as input data; those belong in step expectations/assertions.
- Steps follow the actual interaction sequence: open the relevant entry, locate the target record, supply fields/selections, trigger the business action, wait for its stated completion, and inspect each required result. Combine actions only when the operation is genuinely indivisible; do not compress a multi-page flow into “execute the process”.
- Each step states its expected observable result. UI navigation/selection can have a simple state check; business checkpoints must retain specific requirement-derived assertions. If the prototype lacks exact UI details, describe known semantic actions and defer concrete locators to execution rather than inventing buttons.
- Cover cross-module success and rejection effects, not merely the final screen. Independent leaves may be asserted in one coherent end-to-end case; alternative mutually exclusive paths need separate cases or explicit parameter rows with their own expected outcomes.
- Negative cases name the concrete invalid input/state/role and its rejection/preservation checks. Boundary cases give below/on/above data from the confirmed bound; never copy a combined “empty or too large” expectation.
- State preparation and cleanup must be reproducible in the declared test environment. Unknown runtime record IDs are not missing business requirements, but unavailable required data setup makes automation conditional.
- Choose smoke for essential critical business journeys; regression for impacted and related existing behavior, permissions and data dependencies; full for all reviewed coverage. Do not classify by a fixed percentage or remove manual cases from the human suite files.

Semantic review should simulate executing representative success, rejection, boundary, permission and cross-module cases from their steps alone. Record a concrete missing instruction/oracle/data issue and repair it; do not just mark the checklist completed. One-step cases are acceptable for a genuinely single operation, not as a quota or export shortcut.
