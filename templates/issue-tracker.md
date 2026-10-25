# 工单索引 (issue-tracker.md，可选)

> 工单的唯一事实来源是 `/to-tickets` 发布到 tracker 的工单本身（本地 `.scratch/<spec-slug>/issues/<NN>-<slug>.md`，或 GitHub/Linear issue）。本文件只是给人看的索引视图，**状态以工单本身为准**；若与工单不一致，以工单为准并修正本文件。不需要时可以不建。

## Spec：<spec-slug>（<tracker 链接>）

| 工单 | 标题 | 前置工单 | 状态 | 最新评审记录 |
| :--- | :--- | :--- | :--- | :--- |
| 01 | <标题> | 无 | `completed` | `docs/reviews/<spec-slug>/01-acceptance-round2.md` |
| 02 | <标题> | 01 | `in_progress` | `docs/reviews/<spec-slug>/02-submission-round1.md` |
| 03 | <标题> | 01 | `ready-for-agent` | - |

## 状态
- `ready-for-agent`：已发布、未开工（`/to-tickets` 的初始状态）
- `in_progress`：执行中、提审中或返修中
- `completed`：Reviewer 已出具 ACCEPTED
- `superseded`：因规划阶段修订 Spec 而被新工单替代
