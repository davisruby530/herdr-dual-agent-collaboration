# 工单验收报告 (<NN>-acceptance-round<N>.md)

> **Spec**：<spec-slug>  
> **工单**：<NN> <工单标题>  
> **审查轮次**：Round <N>  
> **复验 commit**：`<hash>`（与提审报告一致）  
> **Reviewer**：<标识与模型>  
> **审查时间**：<YYYY-MM-DD HH:MM>  
> **证据快照**：`docs/reviews/<spec-slug>/<NN>-evidence-round<N>.json`  
> **裁决**：**<ACCEPTED / CHANGES_REQUIRED>**

---

## 一、复核范围
- **沙箱**：`git worktree add --detach /tmp/sandbox-review-<spec-slug>-<NN>-r<N> <commit>`；未纳入 git 的文件已核对 SHA-256：<是 / 不涉及>
- **工单类型复核**：Coder 声明为 <类型>，Reviewer <同意 / 不同意，理由>
- **本轮范围**：<Round 1 为全量复核；之后只复核前轮必须修改项及其影响面>

## 二、验收标准逐条复核

| # | 验收标准（原文） | 独立复核方式 | 观测结果 | 结论 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | <criterion> | <重跑命令 / 抽样方式> | <结果> | PASS / FAIL |

**Spec 相关条目复核**：<是否与相关用户故事和实现决策一致>

## 三、数据防线（仅数据工单）

| 防线 | 复核方式 | 观测结果 | 结论 |
| :--- | :--- | :--- | :--- |
| 多重集守恒 | 对账输入输出唯一键 | <结果> | PASS / FAIL |
| 字符切片断言 | 抽样校验 `source[start:end] == quote` | <结果> | PASS / FAIL |
| 资产清单 | 校验 SHA-256 与文件大小 | <结果> | PASS / FAIL |
| 反伪造 | 检查硬编码数据与伪造记录 | <结果> | PASS / FAIL |

## 四、裁决

### ACCEPTED
- Coder 可将工单改为 `completed`，并继续下一张可开工的工单。
- 可选建议（非阻断）：<如有>

### CHANGES_REQUIRED
工单保持 `in_progress`。必须修改项：
- **[M1]**
  - 实际问题：<文件、位置或错误数值>
  - 后果：<为何影响正确性、数据真实性或研究结论>
  - 最低必要修改：<改到什么程度即可通过>

下一轮只复核上述必须修改项。

### Spec / 工单缺陷（如有）
<若问题出在 Spec 或工单本身，而非 Coder 实现，在此说明；Coder 应据此上报 Principal>
