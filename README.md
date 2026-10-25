# 基于 Herdr 的 Coder–Reviewer 双智能体协作框架

一套多智能体协作框架，分为两个阶段：

- **规划阶段**：Principal 与 agent 用 `grill-with-docs → to-spec → to-tickets` 产出 Spec 与工单；
- **执行阶段**：由 `/goal` 驱动 Coder 逐张实现工单，每张都由独立的 Reviewer 通过 [Herdr](https://herdr.dev) 沙箱复验并书面验收。

**完整指南**：[`docs/agents/coder-reviewer-herdr-collaboration-guide.md`](./docs/agents/coder-reviewer-herdr-collaboration-guide.md)

## 快速上手

1. 把项目骨架复制到项目根目录（`-n` 不覆盖已有文件）：
   ```bash
   cp -rn templates/project/. <你的项目>/
   ```
   这会放入 `AGENTS.md`、`CLAUDE.md`、`docs/reviews/` 下的两份评审模板，以及给人看的操作说明 `docs/agents/collaboration-quickstart.md`。路径与 `AGENTS.md` 中的引用一致，无需改名。
2. 规划：`/grill-with-docs` → `/to-spec` → `/to-tickets`，批准拆分方案。
3. 执行：启动 Herdr 的 Coder 与 Reviewer 两个窗格。在 Reviewer 窗格发出启动语：
   ```
   你是本项目的 Reviewer。按 AGENTS.md 第 7 节工作，等待 Herdr 的【提审】通知后开始复核；未收到通知时不做任何事。
   ```
   在 Coder 窗格发出：
   ```
   /goal 你是本项目的 Coder。按 AGENTS.md 执行阶段规则，推进 Spec <链接> 下的全部工单，直至全部 completed 或需要上报。
   ```

## 仓库内容

| 路径 | 用途 |
| :--- | :--- |
| [`GLOSSARY.md`](./GLOSSARY.md) | 框架术语（规划阶段、执行阶段、工单、提审、上报等） |
| [`docs/adr/`](./docs/adr/) | 架构决策记录 |
| [`templates/project/`](./templates/project/) | 项目骨架，目录结构与落地后一致，整体复制即可 |
| ├ [`AGENTS.md`](./templates/project/AGENTS.md) | 项目协作规则：两大铁律、单张工单的执行步骤、上报条件 |
| ├ [`CLAUDE.md`](./templates/project/CLAUDE.md) | 让 Claude Code 加载 `AGENTS.md` |
| ├ [`docs/reviews/submission-template.md`](./templates/project/docs/reviews/submission-template.md) | Coder 提审报告模板 |
| ├ [`docs/agents/collaboration-quickstart.md`](./templates/project/docs/agents/collaboration-quickstart.md) | 给人看的操作说明：每一步做什么、如何处理上报 |
| └ [`docs/reviews/acceptance-template.md`](./templates/project/docs/reviews/acceptance-template.md) | Reviewer 验收报告模板 |
| [`templates/issue-tracker.md`](./templates/issue-tracker.md) | 可选的工单索引视图 |
| [`templates/academic_paper_workflow.md`](./templates/academic_paper_workflow.md) | 学术论文修改的预制工单骨架 |
| [`tools/`](./tools/README.md) | 通用工具：多重集守恒审计、字符切片断言、学术 Word 排版、分发打包 |
