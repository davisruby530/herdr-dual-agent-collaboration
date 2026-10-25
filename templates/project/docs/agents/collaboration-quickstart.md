# 协作操作说明（给人看）

本项目采用 Coder–Reviewer 双智能体协作框架。agent 遵守的规则在根目录 `AGENTS.md`，本文件说明**人**每一步该做什么。

框架来源与完整指南：`herdr-dual-agent-collaboration` 仓库的 `docs/agents/coder-reviewer-herdr-collaboration-guide.md`。

---

## 一次性准备

1. **骨架已就位**：本文件随项目骨架（`templates/project/`）复制而来，同时到位的还有 `AGENTS.md`、`CLAUDE.md`、`docs/reviews/` 下的两份评审模板。如果项目原本就有 `AGENTS.md` 或 `CLAUDE.md`，复制时会被跳过，需要手工把规则合并进去。
2. **配置 tracker**：在项目里运行 `/setup-matt-pocock-skills`，选本地 `.scratch` 或 GitHub。Spec 和工单都会发布到这里。

## 每个 Spec 的流程

### 1. 开 Herdr 窗格
开两个窗格，都进入项目根目录：
- **Coder 窗格**：任选 Claude、pi、Codex；
- **Reviewer 窗格**：推荐推理更强的模型。

用 `herdr pane list` 确认两个窗格都在。

在 **Reviewer 窗格**发出启动语（每次新开 Reviewer 会话都要发）：

```
你是本项目的 Reviewer。按 AGENTS.md 第 7 节工作，等待 Herdr 的【提审】通知后开始复核；未收到通知时不做任何事。
```

### 2. 规划阶段（在 Coder 窗格进行，Reviewer 不参与）
1. `/grill-with-docs <你的想法>`：逐轮回答问题。这一步**不需要已有 Spec**。
2. `/to-spec`：把讨论结果整理成 Spec，发布到 tracker。
3. `/to-tickets`：审核拆分方案，检查粒度和前置工单是否正确，满意后批准。

批准就是**交接点**。建议随后在 Coder 窗格 `/clear`，让执行阶段从干净的上下文开始，因为 Spec 和工单都已经落盘。

> **写论文时**：grill 的内容是目标期刊、论文现状和本轮修改重点；`/to-tickets` 时让它以框架仓库里 `templates/academic_paper_workflow.md` 的【1】–【7】为骨架拆分，【0】写进 Spec 作为通用写作规范。

### 3. 执行阶段
在 **Coder 窗格**发出：

```
/goal 你是本项目的 Coder。按 AGENTS.md 执行阶段规则，推进 Spec <链接> 下的全部工单，直至全部 completed 或需要上报。
```

之后 Coder 会自动循环：实现工单 → 自检 → 提审，然后等待 Reviewer 裁决，通过后进入下一张，退回则修复后重新提审。评审记录在 `docs/reviews/<spec-slug>/`。

### 4. 你只需要处理上报
Coder 遇到以下情况会暂停并通知你：

| 上报原因 | 你要做的 |
| :--- | :--- |
| 同一工单第 3 轮仍为 CHANGES_REQUIRED | 读最新的 submission 和 acceptance，裁定由谁让步，然后让 Coder 继续 |
| Coder 不认可某个必须修改项 | 在 Coder 与 Reviewer 之间仲裁，把结论告诉双方 |
| Spec 或工单有缺陷 | 回到规划阶段：`/grill-with-docs` 只针对缺陷修订 Spec，`/to-tickets` 重新生成受影响且未完成的工单，旧工单标为 `superseded`，再重新发 `/goal` |

已经 `completed` 的工单默认不重开。

## 常见问题

- **Coder 没等裁决就开始下一张工单**：违反了 `AGENTS.md` 第 5 节。让它把这张工单退回 `in_progress`，并提醒它提审后要结束回合。
- **Reviewer 没反应**：先用 `herdr pane list` 检查窗格还在不在；如果会话是新开的，重发上面的启动语。
- **想看进度**：查 tracker 里各工单的 `Status`，或者看 `docs/reviews/<spec-slug>/` 下编号最大的那一轮。
