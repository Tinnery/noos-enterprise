# 10 — PR Change Assurance：经过校准的研究设计

**研究状态：** Experiment 0 完成，后续实验设计已校准  
**研究日期：** 2026-11-12  
**研究领域：** AI-assisted Software Change Assurance  
**技术分支：** Regression Testing、Test Effectiveness、CI Evidence、Requirements Traceability

---

## 1. 研究问题

**核心问题：** 对于一项具有明确行为要求的代码变更，我们能否证明相关测试确实验证了该要求，而不是仅仅证明 CI 执行成功？

**子问题：**
1. 现有 CI 工作流（如 FastAPI 的 base 重放）能提供什么程度的验证证据？
2. 这些证据的边界在哪里？哪些主张无法从现有机制中证明？
3. 是否存在可以机械化、重复执行的证据收集工作？

---

## 2. Experiment 0 的主要发现

### 2.1 需求来源的差异

**[Fact]** 五个 FastAPI PR 均无关联 Issue，需求隐含在 PR 标题和测试断言中。pytest #15255 有关联 Issue，包含可复现的参数化用例和性能数据。

**[Judgment]** 这意味着 FastAPI 案例的 Test Oracle 和测试代码**同源**——都是 PR 作者同时编写的。无法独立验证"测试是否真的验证了需求"，因为需求本身没有独立于测试的表述。

### 2.2 Base / Head 测试可比性

**[Fact]** FastAPI 的 `regression-test` Job 与 `test` 矩阵不是同条件对照：

| 维度 | Base（regression-test） | Head（test 矩阵） |
|------|------------------------|-------------------|
| 代码版本 | PR 的 base SHA（旧代码） | PR 的 head SHA（新代码） |
| 测试集 | 仅新增/修改的 `test_*.py` 文件 | 完整测试套件 |
| 执行环境 | 单独 Job | 多平台多版本矩阵 |
| 失败判定 | 非零退出码 = "预期失败" | 零退出码 = "通过" |

**[Judgment]** "Base 失败 + Head 通过"证明的是：新测试能在旧代码上检测到某种异常，且新代码的完整测试套件通过。它不证明新测试 specifically 因为新代码而通过，也不证明旧代码的失败 exclusively 由本次修复解决。

### 2.3 失败分类的缺失

**[Fact]** FastAPI 工作流不区分以下失败性质：

1. **AssertionError**：测试断言明确失败（行为回归的强证据）
2. **Snapshot mismatch**：`inline_snapshot` 检测到输出差异（行为变化的证据，但需要审查差异内容）
3. **EOFError / 交互式提示**：`inline_snapshot` 在非交互环境中等待输入（测量工具本身的问题）
4. **Collection error**：测试文件无法加载（环境问题）
5. **其他非零退出码**：原因不明

**[Judgment]** PR #16555 和 #16560 的基线重放日志以 snapshot 交互提示结束，Job 仍报告 success。这不是"基线行为失败"的明确证据，而是"日志诊断不充分"。

### 2.4 证据强度分级

**[Fact]** 基于 Experiment 0 的六个案例：

| 案例 | 需求可追溯性 | 代码变更可审查性 | 基线失败性质 | 测试-需求映射 |
|------|------------|----------------|------------|-------------|
| #16557 | ⚠️ 无 Issue | ✅ 单文件逻辑变更 | ✅ AssertionError | ✅ 测试直接覆盖 |
| #16559 | ⚠️ 无 Issue | ✅ 单文件逻辑变更 | ✅ AssertionError | ✅ 测试直接覆盖 |
| #16564 | ⚠️ 无 Issue | ✅ 重构级变更 | ✅ AssertionError | ✅ 测试覆盖错误位置 |
| #16555 | ⚠️ 无 Issue | ✅ 多文件重构 | ❌ Snapshot 交互异常 | ⚠️ 失败性质不明 |
| #16560 | ⚠️ 无 Issue | ✅ 单文件逻辑变更 | ❌ Snapshot 交互异常 | ⚠️ 失败性质不明 |
| pytest #15255 | ✅ Issue + 复现 | ✅ 新算法 + 结构性测试 | ❌ 无基线重放 | ✅ 结构性不变量 |

### 2.5 对照案例的价值

**[Judgment]** pytest #15255 展示了**不同类型的变更需要不同类型的验证证据**：

| 变更类型 | 合适的验证证据 |
|---------|--------------|
| 功能修复 | 错误输入在旧版本失败，在新版本满足预期行为 |
| 性能优化 | 可复现负载、基准条件、重复测量和结构性复杂度不变量 |
| 资源/文件系统行为 | 碰撞、权限错误、并发和平台差异测试 |
| 兼容性修改 | 旧输入、边界输入和接口契约的行为矩阵 |

---

## 3. 经过校准的研究假设

基于 Experiment 0 的发现，以下假设需要修正：

### H1：Test Oracle Independence

**原始假设：** 可以独立验证测试是否真的验证了需求。

**校准后：** 在 FastAPI 案例中，Test Oracle 和测试代码同源（PR 作者同时编写）。只有 pytest #15255 有独立的 Issue 定义预期行为。

**[Judgment]** 对于大多数开源 PR，Test Oracle Independence 可能是一个不切实际的标准。更现实的问题是：**测试断言是否与代码变更的逻辑一致？**

### H2：Base 重放作为验证机制

**原始假设：** Base 重放是验证代码变更的核心机制。

**校准后：** Base 重放只能证明"新测试能在旧代码上检测到异常"，不能证明"新测试 specifically 因为新代码而通过"。此外，两个案例（#16555、#16560）的 Base 重放日志诊断不充分，无法作为有效证据。

**[Judgment]** Base 重放是有用的证据之一，但不是充分证据。需要结合失败分类和测试-代码映射。

### H3：失败分类可以自动化

**原始假设：** 可以开发工具自动分类测试失败。

**校准后：** Experiment 0 确认至少需要五种分类（AssertionError、Snapshot mismatch、EOFError、Collection error、其他）。其中 AssertionError 可以自动识别，但 Snapshot mismatch 需要审查差异内容，EOFError 需要识别为无效证据。

**[Judgment]** 第一版可以自动识别 AssertionError 和 Collection error，但 Snapshot mismatch 和 EOFError 需要人工判断或更复杂的解析逻辑。

### H4：Mutation Testing 的必要性

**原始假设：** 应该引入 Mutation Testing 验证测试覆盖。

**校准后：** 在现有六个案例中，Mutation Testing 的价值有限。FastAPI 案例的测试已经直接针对修复行为，pytest 案例的测试验证结构性不变量。

**[Judgment]** 第一版不引入 Mutation Testing，先验证更基础的证据链是否成立。

---

## 4. 后续实验设计

### Experiment 1：离线 Evidence Packet

**目标：** 开发最小原型，解析固定的原始数据，提取代码和测试变更，组织 Base / Head 执行证据，输出 Claim / Evidence / Unknown 记录。

**输入：**
- PR 元数据（SHA、文件列表、AI 披露）
- 代码 diff（生产代码和测试代码的变更）
- CI Job 状态和摘要统计
- CI 日志中的具体失败输出

**输出：**
- Claim：本次变更声称修复了什么？
- Evidence：哪些测试验证了这些声称？
- Unknown：哪些主张没有证据支持？

**不做：**
- LLM 裁决
- Web UI
- 数据库
- 通用 PR 自动审查
- GitHub Action
- SaaS

**验收条件：**
1. 能够解析 FastAPI 的 `regression-test` Job 日志
2. 能够识别 AssertionError 和 EOFError
3. 能够提取代码 diff 中的函数级变更
4. 能够生成 Claim / Evidence / Unknown 记录

### Experiment 2：负面控制和 Mutation Testing（暂缓）

**目标：** 检验工具是否会把环境错误误判为有效证据。

**暂缓原因：** Experiment 0 显示现有六个案例中，两个案例（#16555、#16560）已经是"日志诊断不充分"的情况。先验证 Experiment 1 能否正确处理这些情况，再决定是否引入 Mutation Testing。

**下一阶段需要寻找的负面控制样本：**
- 测试在 Base 上通过但 Head 上失败的案例（反向 red-green）
- 测试在 Base 和 Head 上都通过但需求未被满足的案例（遗漏覆盖）
- 测试失败但失败原因与本次修复无关的案例（噪声干扰）

### Experiment 3：独立复核（暂缓）

**目标：** 检查报告是否让另一个评估者能够得到相同判断。

**暂缓原因：** 需要先完成 Experiment 1，确定报告的实际内容和格式。

---

## 5. 研究范围

**[Judgment]** 基于 Experiment 0 的发现，研究范围调整为：

**包括：**
- 具有明确行为要求的代码变更（Bug Fix、性能优化）
- 有测试变更的 PR
- 有 CI 执行记录的 PR

**不包括：**
- 没有测试变更的 PR
- 没有 CI 记录的 PR
- 重构、文档、配置变更

**样本：**
- 现有六个案例（五个 FastAPI + 一个 pytest）
- 下一阶段寻找 3-5 个负面控制案例

---

## 6. 验收条件

### Experiment 1 验收条件

1. 能够解析 FastAPI 的 `regression-test` Job 日志，提取失败数量和类型
2. 能够识别 AssertionError（行为回归的强证据）
3. 能够识别 EOFError（测量工具问题，无效证据）
4. 能够提取代码 diff 中的函数级变更
5. 能够生成 Claim / Evidence / Unknown 记录
6. 对六个案例中的至少四个生成合理的证据记录

### 最终研究验收条件

1. 能够回答核心问题：现有 CI 工作流能提供什么程度的验证证据？
2. 能够明确证据的边界：哪些主张无法从现有机制中证明？
3. 能够判断是否存在可以机械化的证据收集工作
4. 能够给出最终决策：Adopt / Adopt with boundary / Keep separate / Reject

---

## 7. 交付物

### 已完成

- `experiments/pr-change-assurance/README.md` — Experiment 0 总结
- `experiments/pr-change-assurance/evidence/fastapi-16557.md` — C1 证据记录
- `experiments/pr-change-assurance/evidence/fastapi-16559.md` — C2 证据记录
- `experiments/pr-change-assurance/evidence/fastapi-16564.md` — C3 证据记录
- `experiments/pr-change-assurance/evidence/fastapi-16555.md` — C4 证据记录
- `experiments/pr-change-assurance/evidence/fastapi-16560.md` — C5 证据记录
- `experiments/pr-change-assurance/evidence/pytest-15255.md` — C6 证据记录

### 待完成

- Experiment 1：离线 Evidence Packet 原型
- 负面控制案例收集
- 最终研究报告

---

## 8. 外部标准依据

**[Judgment]** 本研究的设计参考了以下外部标准，但不声称完全符合：

- **ISO/IEC/IEEE 29148:2018**（需求工程）：需求应可追溯、可验证
- **ISO/IEC/IEEE 29119**（测试过程）：测试应覆盖需求，结果应可解释
- **ISO/IEC 25010:2023**（产品质量）：功能完整性、性能效率
- **SLSA Provenance**（供应链安全）：构建过程应可追溯
- **in-toto Attestation**（软件供应链）：构建步骤应有证据

本研究关注的是**测试证据的可解释性和可追溯性**，而非完整的软件供应链安全。

---

## 9. 决策

**决定：继续实证研究，进入 Experiment 1。**

理由：
- Experiment 0 已建立人工证据账本，明确了证据的边界
- 发现 Base 重放是有用但不充分的证据机制
- 发现失败分类和测试-代码映射是可以机械化的工作
- 发现 Test Oracle Independence 在大多数开源 PR 中不切实际

下一步：
1. 开发离线 Evidence Packet 原型
2. 对六个案例生成 Claim / Evidence / Unknown 记录
3. 寻找负面控制案例
4. 根据 Experiment 1 的结果决定是否继续

---

## 10. 原始来源

所有结论均基于以下公开材料，固定到指定 SHA：

- GitHub PR 页面、diff 文件和 Actions 日志
- `09-change-assurance-pilot.md` 中已记录的初步发现
- `experiments/pr-change-assurance/evidence/` 中的证据记录

未来仓库版本变化后，必须重新固定 SHA 和采集记录。
