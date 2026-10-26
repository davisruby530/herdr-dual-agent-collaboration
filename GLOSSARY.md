# Coder–Reviewer 双智能体协作

一套把"从想法到 Spec 到工单"的规划流程，与"逐单执行、独立验收"的执行流程衔接起来的多智能体协作框架。

## 阶段

**规划阶段 (Planning Phase)**:
Principal 与单个 agent 通过 grill-with-docs → to-spec → to-tickets 产出 Spec 与工单的阶段；不建工单、不提审，两大铁律不适用。
_Avoid_: 方案设计阶段、前期准备

**执行阶段 (Execution Phase)**:
工单发布之后，Coder 逐单实现、Reviewer 逐单验收的阶段；两大铁律只在此阶段生效。
_Avoid_: 开发阶段、工单循环

**交接点 (Handoff)**:
Principal 批准 to-tickets 拆分方案的时刻，标志规划阶段结束、执行阶段开始。

## 产物

**Spec**:
规划阶段由 to-spec 从 grill 对话综合出的规格文档，发布于项目 issue tracker；是规划阶段的产出，而非外部输入。
_Avoid_: 研究指南、技术规格、任务规范

**工单 (Ticket)**:
to-tickets 产出的一个垂直切片，声明其前置工单；以 tracker 中的工单本身为唯一事实来源。
_Avoid_: Issue、任务、`Ticket-01` 式总账条目

**工单类型 (Ticket Type)**:
代码、数据或写作三者之一，由 Coder 在提审时声明、Reviewer 复核；决定执行步骤与适用的数据防线。
_Avoid_: 工单分类、任务类别

**superseded**:
因规划阶段修订 Spec 而被新工单替代的工单状态；已 `completed` 的工单默认不转为此状态。
_Avoid_: 已废弃、作废

**前置工单 (Blocker)**:
某工单开工前必须已 ACCEPTED 的其他工单。
_Avoid_: 依赖、前序工单

**可开工集 (Frontier)**:
所有前置工单均已 ACCEPTED、自身尚未开工的工单集合。

## 验收

**提审 (Submission)**:
Coder 就某工单某一轮向 Reviewer 提交的书面报告加 Herdr 通知；提审后 Coder 停止推进，直到收到裁决。
_Avoid_: 提交、送审

**验收标准 (Acceptance Criteria)**:
工单中列出的可核验条件，与 Spec 相关条目一起构成 Reviewer 的主检查清单。
_Avoid_: 验收指标、自检指标

**上报 (Escalation)**:
Coder 暂停 goal 并请求 Principal 裁决的动作；触发于同一工单第 3 轮仍 CHANGES_REQUIRED、Coder 不认可某必须修改项，或发现 Spec/工单本身有缺陷。
_Avoid_: 求助、人工介入

**ACCEPTED**:
Reviewer 对某工单某一轮提审出具的书面通过结论；是工单进入 `completed` 的唯一条件。
_Avoid_: 通过、自测通过、review 通过

**CHANGES_REQUIRED**:
Reviewer 出具的书面退回结论；工单保持 `in_progress`，Coder 修复后递增轮次重新提审。
_Avoid_: 驳回、打回
