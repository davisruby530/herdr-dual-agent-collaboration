---
name: herdr-dual-agent
description: 在项目中建立并启动 Herdr 双智能体协作（Coder 逐单实现，Reviewer 独立沙箱复验）。用户要求用双 agent、Coder–Reviewer、逐单验收的方式推进项目，或要把这套机制装进某个项目时使用。
---

# Herdr 双智能体协作（Coder–Reviewer）

规划阶段由 Principal（用户）与一个 agent 完成；执行阶段由 Coder 逐单实现并提交，Reviewer 按 commit 独立复验，只有书面 ACCEPTED 能关单。规则全文以项目根目录的 `AGENTS.md` 为准：装好之后读它并照做，本技能只管安装与启动。

## 先判断处在哪一步

- 项目 `AGENTS.md` 里已有“执行阶段的两大铁律”：跳到“启动执行阶段”，或按你的角色读 `AGENTS.md` 第 4–5 节（Coder）、第 7 节（Reviewer）。
- 否则从“安装”开始。

## 安装

1. 确认项目是 git 仓库。
2. `cp -rn <本技能目录>/assets/project/. <项目根目录>/`。完成标准：逐个核对骨架文件，被 `-n` 跳过的同名文件（常见是 `AGENTS.md`、`CLAUDE.md`、`.gitignore`）已把骨架内容手工合并进去。
3. 配置 tracker（`docs/agents/issue-tracker.md`、`domain.md`）：请用户运行 `/setup-matt-pocock-skills`；用户选择沿用现有本地约定时，在回复里说明缺这两个文件。
4. 与用户确认角色分工是否照模板。分工有变（例如正文由 Reviewer 执笔、Coder 只核对），在 `AGENTS.md` 末尾增一节写明适用范围、执笔、核对、通过条件，执笔者不得自行判定通过。

## 规划

`grill-with-docs` → `to-spec` → `to-tickets`。用户批准工单拆分之前，不向 Coder 发任何开工指令。论文修改类项目拆工单时读 `references/academic_paper_workflow.md`；需要给人看的工单总览时用 `references/ticket-index.md`。

## 启动执行阶段

1. 提交 Spec、工单和规则文件：Reviewer 在 worktree 里按 commit 复验，未提交的内容它看不到。
2. 确认在 Herdr 内（`HERDR_ENV=1`），用 `herdr pane list` 按标签和工作目录找对方窗格；同一台机器上常有别的项目的 coder、reviewer。
3. `herdr agent prompt <窗格> "<指令>"` 发出角色指令，写明：角色、Spec 路径、基线 commit、己方窗格号、什么情况下上报。Claude Code 的 Coder 可在指令前加 `/goal`；其他 agent（如 agy、codex）按普通指令发。
4. 用 `herdr agent read <窗格>` 确认指令已被提交并开始执行。完成标准：看到对方在处理它。
5. 己方是 Reviewer：结束回合，等【提审】通知。

## 运行中的注意点

- 每次通知前重新查窗格号。
- 被 `.gitignore` 排除的复验材料（数据、DOCX、PDF、私有语料）在提审报告里列路径与 SHA-256。
- 对方长时间无动静时先读它的窗格，常见原因是停在权限确认上。
- 需要用户本人完成的事项（裁定、盲判、手改稿）在工单里写明由谁做，Coder 不得代填，缺材料时按【上报】停下。

## 参考

- `references/guide.md`：完整指南，处理上报、修订 Spec、重出工单时读。
- `references/glossary-and-adr.md`：术语，以及为什么分两阶段、为什么阻塞等待。修改机制本身前读。
