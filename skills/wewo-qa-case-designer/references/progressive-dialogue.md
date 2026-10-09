# Progressive requirement dialogue

Use this procedure for every requirement unit after building the whole-business draft in [design context](design-context.md). Order units by shared prerequisites and object/flow dependencies, not only by document or page order. The goal is for the tester and the agent to build the same understanding before producing test artifacts.

## One conversational round

Present these sections in order:

1. **Source slice** — identify the source anchor and summarize only the current unit.
2. **Plain-language explanation** — explain the user-visible flow and why it matters without assuming product knowledge.
3. **Current understanding** — separate explicit facts from interpretations. Identify actors, preconditions, triggers, rules, state changes, visible outcomes, and applicable targets.
4. **Business understanding delta** — show changed rules; affected objects, states and data; upstream prerequisites; downstream modules and existing flows; and what must stay unchanged. Name the source or decision supporting each effect. Do not generate test artifacts here.
5. **Clarification batch** — ask the related questions that materially affect this unit.

Wait for the batch response. Then present:

- decisions confirmed or corrected;
- assumptions the user explicitly accepted;
- unanswered or contradictory items;
- business rules and dependencies added, changed or reopened;
- the next unit only after the current unit is closed.

## Batch construction

- Put only questions sharing the current business context in one batch. Do not mix unrelated modules merely to reach a target count.
- Default to 3–6 material questions when available. If fewer exist, ask fewer; never create filler questions. Do not send serial one-question turns when several related unknowns are already known.
- Cover both understanding and ambiguity: the user may correct stated facts as well as choose resolutions for missing rules.
- Do not ask the user to rediscover facts already explicit in the source. Present those as current understanding and make correction easy.
- Ask about a common rule once, then show where the answer propagates. If its answer changes a previously discussed module, reopen that module's affected facts and obtain the needed correction before final confirmation.
- Split a large unit before sending a long questionnaire.

## Question contract

Give every question a stable ID such as `Q-RU001-01` and include:

```markdown
### Q-RU001-01（单选）：未登录用户点击“立即购买”后如何处理？

背景：当前片段只描述了登录用户的购买流程。

影响：答案会改变登录拦截、购物车保留和结算流程的测试点。

A. 立即跳转登录页
B. 可以进入结算页，提交订单前要求登录
C. 支持游客完成下单
D. 当前版本不允许未登录用户进入商品详情页

推荐：A
依据：它与来源中的登录前置条件最一致；这是临时建议，不代表已确认规则。

也可以不选以上答案，直接说明实际规则。
```

Use 2–4 meaningful options, normally lettered `A` through `D`. State `单选` or `多选`. For multiple selection, make option combinations logically valid.

The recommendation must cite one of these bases:

- explicit source evidence;
- consistency with another confirmed rule;
- lower product or release risk;
- a clearly labeled provisional assumption pending the responsible owner.

Never present an industry convention as a confirmed Wewo rule. When no defensible product recommendation exists, recommend obtaining owner confirmation and state the safest provisional testing assumption separately.

Accept compact replies such as `Q1-B，Q2-A+C` and free-form corrections. A free-form answer overrides the proposed options. If an answer changes a previously confirmed unit, reopen it and show downstream test-point changes.

## Module checkpoint

At the end of a module, show its consolidated business understanding and a compact status table:

| 项目 | 状态 |
| --- | --- |
| 来源事实 | 已确认/有冲突 |
| 澄清问题 | 已回答/待回答 |
| 假设 | 无/已披露 |
| 业务理解 | 已理解/待澄清 |

The user may approve the whole module, correct individual items, or provide new information. Module confirmation is not the final requirement confirmation. After all modules, present the consolidated final requirements, ask for explicit confirmation, preserve the actual response/ref/digest, and only then derive XMind points.

## Persistent understanding

Maintain unit status/understanding in `test-points.json`; preserve decisions with question ID, selected options/free-text resolution, rationale and impacted rule/point IDs in the business model. Keep accepted assumptions and remaining material questions visible. Do not require a separate Markdown walkthrough.

The whole-business draft establishes dependencies before these rounds. A changed answer may reopen a rule in another module; show the downstream rule/flow/relationship changes before any test-point revision. Do not ask for an answer to a rule already explicit in a readable source. Historical decisions are leads only: compare project, version, object, scope and original authority; similar wording or a remembered formatting preference cannot confirm today's business rule. A module checkpoint is a correction opportunity, while the final requirement summary and later XMind baseline each need their own explicit confirmation.

Do not use test-point rendering to bypass requirement dialogue. Final requirements, XMind review and case review are distinct states. Keep unanswered material facts in `open_questions`; silence and generated notes never constitute confirmation.
