# Progressive requirement dialogue

Use this procedure for every requirement unit. The goal is for the tester and the agent to build the same understanding while producing the test-point tree.

## One conversational round

Present these sections in order:

1. **Source slice** — identify the source anchor and summarize only the current unit.
2. **Plain-language explanation** — explain the user-visible flow and why it matters without assuming product knowledge.
3. **Current understanding** — separate explicit facts from interpretations. Identify actors, preconditions, triggers, rules, state changes, visible outcomes, and applicable targets.
4. **Proposed test-point delta** — show the small branch being added or changed, not the entire map on every turn.
5. **Clarification batch** — ask the related questions that materially affect this unit.

Wait for the batch response. Then present:

- decisions confirmed or corrected;
- assumptions the user explicitly accepted;
- unanswered or contradictory items;
- test points added, changed, removed, or split;
- the next unit only after the current unit is closed.

## Batch construction

- Put only questions sharing the current business context in one batch. Do not mix unrelated modules merely to reach a target count.
- Default to 3–6 material questions when available. If fewer exist, ask fewer; never create filler questions. Do not send serial one-question turns when several related unknowns are already known.
- Cover both understanding and ambiguity: the user may correct stated facts as well as choose resolutions for missing rules.
- Do not ask the user to rediscover facts already explicit in the source. Present those as current understanding and make correction easy.
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

At the end of a module, show its accumulated test-point branch and a compact status table:

| 项目 | 状态 |
| --- | --- |
| 来源事实 | 已确认/有冲突 |
| 澄清问题 | 已回答/待回答 |
| 假设 | 无/已披露 |
| 测试点分支 | 待确认/已确认 |

The user may approve the whole module, correct individual items, or provide new information. Module confirmation is not the same as final XMind confirmation.

## Walkthrough ledger

Maintain `requirement-walkthrough.md` so another session can continue without replaying the whole conversation. For each unit record:

- unit ID, title, source anchors, and status;
- the plain-language understanding shown to the user;
- each question batch exactly as presented, including choices and recommendation basis;
- the user's selected options or free-form correction;
- resulting decision IDs and assumptions;
- test-point IDs added, changed, removed, or reopened;
- module confirmation and timestamp when available.

This ledger records the collaboration but does not replace the authoritative source or `test-points.json`.
