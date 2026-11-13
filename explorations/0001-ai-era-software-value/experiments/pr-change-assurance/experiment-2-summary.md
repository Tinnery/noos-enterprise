# Experiment 2：LLM 基于 Evidence Packet 的裁决验证

**日期**：2026-11-13  
**状态**：完成  
**目标**：验证 LLM 是否能基于 Evidence Packet 进行合理裁决

---

## 1. 实验设计

### 输入
- 6 份 Evidence Packet（C1-C6），来自 Experiment 1 的输出
- 每份 Evidence Packet 包含：
  - Claims（主张）
  - Evidence（证据）
  - Unknowns（未知）
  - 自动化程度分析

### 任务
对每个 PR 回答四个标准问题：
1. 这个 PR 是否真正修复了它声称的问题？
2. 证据是否充分？哪些证据最强/最弱？
3. 存在哪些未解决的风险或不确定性？
4. 如果要批准这个 PR，还需要什么额外证据？

### 输出
- 6 份裁决报告（`verdicts/c1-verdict.md` 到 `c6-verdict.md`）
- 每份报告包含：裁决结论、证据评估、风险分析、额外证据需求、置信度

---

## 2. 裁决结果汇总

| 案例 | PR | 置信度 | 主要问题 | 建议 |
|------|-----|--------|----------|------|
| C1 | fastapi#16557 | 60% | 无独立 Issue，Test Oracle 同源 | 不批准，需提供独立 Issue |
| C2 | fastapi#16559 | 55% | 无独立 Issue，代码变更规模大 | 不批准，需提供独立 Issue |
| C3 | fastapi#16564 | 55% | 无独立 Issue，重构级变更 | 不批准，需提供独立 Issue |
| C4 | fastapi#16555 | 40% | Base 失败是 EOFError（无效证据） | 不批准，需提供 AssertionError |
| C5 | fastapi#16560 | 40% | Base 失败是 EOFError（无效证据） | 不批准，需提供 AssertionError |
| C6 | pytest#15255 | 75% | 缺乏 Base 重放数据（非关键） | 批准，建议提供性能基准测试 |

---

## 3. 关键发现

### 3.1 LLM 能够识别证据类型的差异

**发现**：LLM 能够区分 AssertionError（行为回归的强证据）和 EOFError（测量工具问题，无效证据）。

**证据**：
- C1-C3（AssertionError）：置信度 55-60%
- C4-C5（EOFError）：置信度 40%
- 差异显著，说明 LLM 理解不同失败类型的证据强度

**启示**：Evidence Packet 中的失败类型分类（AssertionError/EOFError/Snapshot mismatch）对 LLM 裁决有实际影响。

### 3.2 独立 Issue 显著提升证据强度

**发现**：C6 是唯一有独立 Issue 的案例，置信度（75%）显著高于 C1-C5（40-60%）。

**证据**：
- C6 有独立 Issue #15254，解决了 Test Oracle 同源问题
- C1-C5 无独立 Issue，需求隐含在 PR 标题和测试中
- 置信度差异：75% vs 40-60%

**启示**：独立 Issue 是 PR 审查中的关键证据，应该作为 Evidence Packet 的必填项。

### 3.3 LLM 能够识别不同类型的变更

**发现**：LLM 能够区分 bug 修复（C1-C5）和性能优化（C6），并采用不同的证据标准。

**证据**：
- C1-C5（bug 修复）：需要 Base 失败作为对照
- C6（性能优化）：不需要 Base 失败，可以通过基准测试独立验证
- LLM 对 C6 的裁决没有要求 Base 失败数据

**启示**：Evidence Packet 应该支持不同类型的变更，并提供相应的证据标准。

### 3.4 LLM 能够提出具体的额外证据需求

**发现**：LLM 能够基于 Unknowns 提出具体的额外证据需求。

**证据**：
- C1-C3：要求提供独立 Issue、旧代码问题描述、Base/Head 同条件对照
- C4-C5：要求提供 AssertionError 类型的 Base 失败（最关键）
- C6：建议提供性能基准测试结果

**启示**：LLM 不仅评估现有证据，还能指导如何补充证据。

### 3.5 LLM 裁决的一致性

**发现**：LLM 对相似案例给出一致的裁决。

**证据**：
- C4 和 C5 都面临 EOFError 问题，置信度都是 40%
- C1-C3 都面临无独立 Issue 问题，置信度都是 55-60%
- 裁决逻辑一致，没有矛盾

**启示**：Evidence Packet 框架提供了稳定的输入，LLM 裁决具有可重复性。

---

## 4. 对研究问题的回答

### 研究问题：LLM 是否能基于 Evidence Packet 进行合理裁决？

**回答**：**是的，LLM 能够基于 Evidence Packet 进行合理裁决。**

**具体证据**：
1. ✅ LLM 能够识别证据类型的差异（AssertionError vs EOFError）
2. ✅ LLM 能够识别独立 Issue 的价值
3. ✅ LLM 能够区分不同类型的变更（bug 修复 vs 性能优化）
4. ✅ LLM 能够提出具体的额外证据需求
5. ✅ LLM 裁决具有一致性

**局限性**：
1. ⚠️ LLM 无法验证 Fact 的真实性（如代码变更是否真的发生了）
2. ⚠️ LLM 无法判断 Judgment 的正确性（如"修复"是否真的是"修复"）
3. ⚠️ LLM 的裁决依赖于 Evidence Packet 的完整性

**结论**：Evidence Packet 为 LLM 裁决提供了有效的框架，LLM 的价值在于系统化地评估证据、识别不确定性、提出额外的证据需求。LLM 不能替代人工审查，但可以作为审查的辅助工具。

---

## 5. 对后续实验的校准

### 5.1 Evidence Packet 的改进方向

1. **增加独立 Issue 字段**：作为必填项，明确需求来源
2. **增加 AI 披露字段**：明确 AI 参与程度
3. **支持不同类型的变更**：提供相应的证据标准（bug 修复 vs 性能优化 vs 新功能）
4. **增加基准测试结果**：对于性能优化类变更，提供性能基准测试数据

### 5.2 裁决标准的细化

1. **定义置信度阈值**：如 70% 以上批准，40% 以下拒绝，中间需要补充证据
2. **定义必须证据**：如独立 Issue、Base 失败（对于 bug 修复）
3. **定义可选证据**：如性能基准测试、代码审查记录

### 5.3 后续实验设计

**Experiment 3：人工审查对比**
- 目标：对比 LLM 裁决和人工审查的一致性
- 方法：让多个审查者独立审查 C1-C6，对比裁决结果
- 输出：一致性分析、LLM 裁决的准确性评估

**Experiment 4：真实 PR 审查**
- 目标：在真实 PR 审查场景中使用 Evidence Packet
- 方法：选择正在进行的 PR，生成 Evidence Packet，辅助审查
- 输出：实际审查效果评估、Evidence Packet 的实用性验证

---

## 6. 交付物

1. **裁决报告**：`verdicts/c1-verdict.md` 到 `c6-verdict.md`
2. **实验总结**：`experiment-2-summary.md`（本文档）
3. **README 更新**：2026-11-13 工作日志（Experiment 2）

---

## 7. 结论

Experiment 2 验证了 LLM 能够基于 Evidence Packet 进行合理裁决。LLM 能够：
- 识别证据类型的差异
- 识别独立 Issue 的价值
- 区分不同类型的变更
- 提出具体的额外证据需求
- 保持一致性

Evidence Packet 为 LLM 裁决提供了有效的框架，LLM 可以作为 PR 审查的辅助工具。后续需要进一步验证 LLM 裁决的准确性（与人工审查对比），并在真实 PR 审查场景中评估实用性。
