# 项目智能体协作与验收规则 (AGENTS.md)

本项目的工作分两个阶段。**两大铁律只在执行阶段生效。** 人的操作步骤见 `docs/agents/collaboration-quickstart.md`。

## 0. 项目配置
- **tracker 与领域文档**：见 `docs/agents/issue-tracker.md`、`docs/agents/domain.md`（由 `/setup-matt-pocock-skills` 生成）。无论 `## Agent skills` 一节写在 `CLAUDE.md` 还是 `AGENTS.md`，都以这两个文件为准。
- **`<spec-slug>`**：本地 tracker 时取 Spec 所在目录名，即 `.scratch/<spec-slug>/`；GitHub 等远程 tracker 时取 `spec-<Spec 的 issue 号>`。
- **`<NN>`**：本地 tracker 时取工单文件的编号前缀；远程 tracker 时取工单的 issue 号。

## 1. 角色分工
- **Principal (人类负责人)**：在规划阶段与 agent 共同产出 Spec 与工单，批准工单拆分方案；在执行阶段只处理上报。
- **Coder (执行智能体)**：在执行阶段逐张实现工单、自检、提审、按裁决返修。
- **Reviewer (审查智能体)**：在执行阶段独立复核每一轮提审，出具 ACCEPTED 或 CHANGES_REQUIRED。

## 2. 规划阶段（不适用铁律）
- 流程：`/grill-with-docs` → `/to-spec` → `/to-tickets`，由 Principal 与单个 agent 完成。
- 此阶段**不需要已有 Spec、不建工单、不提审、不经过 Reviewer**。Spec 是这个阶段的产出，不是前提。
- **交接点**：Principal 在 `/to-tickets` 中批准拆分方案、工单发布到 tracker 后，进入执行阶段。

## 3. 执行阶段的两大铁律
1. **逐单必审**：一张工单只有在其所有前置工单都已 `completed` 后才能开工；每张工单完成后必须单独提审。Coder 同一时间只处理一张工单。
2. **严禁擅自闭环**：只有 Reviewer 的书面 ACCEPTED 才能让工单变为 `completed`。自测通过、`code-review` 通过、运行成功都不等于验收通过。CHANGES_REQUIRED 时工单保持 `in_progress`，Coder 做根因修复后递增轮次重新提审，不得降低断言、删测试或硬编码结果。

## 4. Coder：单张工单的执行步骤
1. 从 tracker 选一张可开工的工单（前置工单全部 `completed`；多张可开工时取编号最小者），状态改为 `in_progress`，读取工单全文与 Spec 相关条目。
2. 判定**工单类型**：
   - **代码**：调用 `tdd` 技能，在 Spec 约定的测试接缝上测试先行。
   - **数据**：同代码工单，另需满足数据防线：输入输出多重集守恒（N = N_valid + N_excluded，且无重复键，用 `tools/audit_multiset_integrity.py`）、抽取结果的字符切片硬断言（`source[start:end] == quote`，用 `tools/verify_grounding_assertions.py`）、关键资产 SHA-256 清单、禁止硬编码伪造数据。Reviewer 在沙箱中用同样的工具复跑。
   - **写作**：按工单验收标准与对应写作规范修改，逐条自检。
3. 代码与数据工单完成后调用 `code-review` 技能自检，并修复其发现的问题。
   - 若当前 agent 没有 `tdd` 或 `code-review` 技能，按测试先行、提交前自审的原则手工执行，并在提审报告中注明。
4. **提交（commit）本工单的全部改动**，记下 commit hash。复验需要但未纳入 git 的文件（如大型数据），在提审报告中列出路径与 SHA-256。
5. 按 `docs/reviews/submission-template.md` 写提审报告，保存为 `docs/reviews/<spec-slug>/<NN>-submission-round<N>.md`。
6. 用 Herdr 通知 Reviewer（见第 8 节），然后进入第 5 节的等待。

## 5. Coder：提审后的等待与裁决处理
- **等待方式**：运行 `scripts/wait-for-verdict.sh docs/reviews/<spec-slug>/<NN>-acceptance-round<N>.md`（命令超时设为 600 秒）。退出码 2 表示尚未出结果，**立即再次运行**；退出码 0 表示报告已出现。
- **不要用结束回合的方式等待**：在 `/goal` 下，结束回合会被立即续跑，变成空转。等待期间不得开始下一张工单，不得自行判断是否通过。
- 收到 Herdr 的【裁决】通知只是提示，以验收报告文件为准。
- **ACCEPTED**：提交验收报告、证据快照与工单状态变更（改为 `completed`），回到第 4 节第 1 步。
- **CHANGES_REQUIRED**：只修复列出的必须修改项，以 Round N+1 重新提审。
- **goal 完成条件**：当前 Spec 下所有工单均为 `completed` 或 `superseded`，或已上报 Principal。

## 6. 上报 Principal
遇到以下任一情况，Coder 停止推进，在最后一条消息里以【上报】开头写明原因与相关文件路径，然后结束：
- 同一工单连续 3 轮为 CHANGES_REQUIRED（Principal 仲裁后从下一轮重新计数）；
- Coder 认为 Reviewer 的某个必须修改项不成立；
- Coder 或 Reviewer 发现 Spec 或工单本身有缺陷（验收标准矛盾、按工单无法实现等）。

Spec 缺陷由 Principal 回到规划阶段修订：只针对缺陷修订 Spec，再用 `/to-tickets` 重新生成受影响且未 `completed` 的工单。**重新生成时，新工单从现有最大编号加 1 开始编号，不得删除或改写已有工单文件**；被替换的旧工单把状态改为 `superseded`。已 `completed` 的工单默认不重开。

## 7. Reviewer：验收规则
- 主检查清单：工单的**验收标准** + Spec 相关条目。数据防线只在数据工单中强制检查。复核 Coder 声明的工单类型，判定有误时列为必须修改项。
- **在独立沙箱中复验提审报告写明的 commit**：`git worktree add --detach /tmp/sandbox-review-<spec-slug>-<NN>-r<N> <commit>`，在其中重新运行测试与关键计算，不轻信提审报告中的日志；未纳入 git 的文件按报告列出的路径只读引用，并核对 SHA-256。复验结束后执行 `git worktree remove`。
- 区分必须修改项与可选建议；必须修改项须写明实际问题、后果和最低必要修改。不以风格偏好阻碍验收，不要求推倒重来。
- **落盘顺序**：先写 `docs/reviews/<spec-slug>/<NN>-evidence-round<N>.json`；再按 `docs/reviews/acceptance-template.md` 把验收报告写到 `<NN>-acceptance-round<N>.md.tmp`，最后 `mv` 为 `<NN>-acceptance-round<N>.md`。Coder 一看到正式文件名就会读取，所以它必须是最后出现、且内容完整的那个文件。然后用 Herdr 通知 Coder。
- Reviewer 不修改代码，不提交（commit），不改工单状态。

## 8. Herdr 通信
- 每次通知前用 `herdr pane list` 动态确认对方 pane，不凭旧编号猜测。
- Coder → Reviewer：`herdr agent prompt <PANE_REVIEWER> "【提审】<spec-slug>/<NN> <工单标题> Round <N>，类型：<代码/数据/写作>，commit：<hash>，报告：docs/reviews/<spec-slug>/<NN>-submission-round<N>.md"`
- Reviewer → Coder：`herdr agent prompt <PANE_CODER> "【裁决】<spec-slug>/<NN> Round <N>：<ACCEPTED/CHANGES_REQUIRED>，报告：docs/reviews/<spec-slug>/<NN>-acceptance-round<N>.md"`
