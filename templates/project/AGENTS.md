# 项目智能体协作与验收规则 (AGENTS.md)

本项目的工作分两个阶段。**两大铁律只在执行阶段生效。** 人的操作步骤见 `docs/agents/collaboration-quickstart.md`。

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
   - **数据**：同代码工单，另需满足数据防线：输入输出多重集守恒（N = N_valid + N_excluded）、抽取结果的字符切片硬断言（`source[start:end] == quote`）、关键资产 SHA-256 清单、禁止硬编码伪造数据。
   - **写作**：按工单验收标准与对应写作规范修改，逐条自检。
3. 代码与数据工单完成后调用 `code-review` 技能自检，并修复其发现的问题。
4. 按 `docs/reviews/submission-template.md` 写提审报告，保存为 `docs/reviews/<spec-slug>/<NN>-submission-round<N>.md`。
5. 用 Herdr 通知 Reviewer（见第 8 节），然后**结束当前回合**。

## 5. Coder：提审后的等待与裁决处理
- 提审后不得开始下一张工单，不得自行判断是否通过。被 goal 续跑唤醒时，只检查本轮 `-acceptance-round<N>.md` 是否已存在；不存在就再次结束回合。
- **ACCEPTED**：工单状态改为 `completed`，回到第 4 节第 1 步。
- **CHANGES_REQUIRED**：只修复列出的必须修改项，以 Round N+1 重新提审。
- **goal 完成条件**：当前 Spec 下所有工单均为 `completed` 或 `superseded`。

## 6. 上报 Principal
遇到以下任一情况，Coder 停止推进、通知 Principal 并等待，不再自行处理：
- 同一工单第 3 轮仍为 CHANGES_REQUIRED；
- Coder 认为 Reviewer 的某个必须修改项不成立；
- Coder 或 Reviewer 发现 Spec 或工单本身有缺陷（验收标准矛盾、按工单无法实现等）。

Spec 缺陷由 Principal 回到规划阶段修订：只针对缺陷修订 Spec，用 `/to-tickets` 重新生成受影响且未 `completed` 的工单，被替换的旧工单标为 `superseded`。已 `completed` 的工单默认不重开。

## 7. Reviewer：验收规则
- 主检查清单：工单的**验收标准** + Spec 相关条目。数据防线只在数据工单中强制检查。复核 Coder 声明的工单类型，判定有误时列为必须修改项。
- 在独立临时目录（如 `/tmp/sandbox-review-*`）重新运行测试与关键计算，不轻信提审报告中的日志。
- 区分必须修改项与可选建议；必须修改项须写明实际问题、后果和最低必要修改。不以风格偏好阻碍验收，不要求推倒重来。
- 先保存 `docs/reviews/<spec-slug>/<NN>-acceptance-round<N>.md`（按 `docs/reviews/acceptance-template.md`）与 `<NN>-evidence-round<N>.json`，再用 Herdr 通知 Coder。

## 8. Herdr 通信
- 每次通知前用 `herdr pane list` 动态确认对方 pane，不凭旧编号猜测。
- Coder → Reviewer：`herdr agent prompt <PANE_REVIEWER> "【提审】<spec-slug>/<NN> <工单标题> Round <N>，类型：<代码/数据/写作>，报告：docs/reviews/<spec-slug>/<NN>-submission-round<N>.md"`
- Reviewer → Coder：`herdr agent prompt <PANE_CODER> "【裁决】<spec-slug>/<NN> Round <N>：<ACCEPTED/CHANGES_REQUIRED>，报告：docs/reviews/<spec-slug>/<NN>-acceptance-round<N>.md"`
