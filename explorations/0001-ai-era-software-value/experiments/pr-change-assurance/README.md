# Experiment 0 — 人工证据重建

**状态：** 完成  
**日期：** 2026-11-12  
**研究问题：** 对六个已公开的 PR，逐一建立需求—代码—测试—执行结果之间的证据关系，区分 Fact / Evidence / Judgment / Unknown。

---

## 1. 目的

在不开发任何解析器或自动化工具的前提下，对六个案例逐项回答七个问题：

1. 原始需求到底是什么？是否有 Issue、验收条件或明确的行为规范？
2. 生产代码具体改变了什么？
3. 测试代码具体改变了什么？
4. Base 和 Head 实际执行了哪些测试？
5. 测试失败究竟是什么性质？
6. 这些测试是否真的验证了原始需求？
7. 还有哪些主张没有证据支持？

特别检查：Base 上执行的变更测试与 Head 上通过的测试，是否具有足够的测试身份和执行条件可比性。

## 2. 样本清单

| 编号 | 案例 | 研究用途 | 证据文件 |
|------|------|----------|----------|
| C1 | FastAPI #16557 | 基线行为失败案例 | `evidence/fastapi-16557.md` |
| C2 | FastAPI #16559 | 基线行为失败案例 | `evidence/fastapi-16559.md` |
| C3 | FastAPI #16564 | 基线行为失败案例 | `evidence/fastapi-16564.md` |
| C4 | FastAPI #16555 | Snapshot 交互异常案例 | `evidence/fastapi-16555.md` |
| C5 | FastAPI #16560 | Snapshot 交互异常案例 | `evidence/fastapi-16560.md` |
| C6 | pytest #15255 | 性能验证方法的边界对照 | `evidence/pytest-15255.md` |

## 3. 版本标识

| PR | Base SHA | Head SHA | Merge SHA |
|---|---|---|---|
| FastAPI #16555 | `44cc7420` | `b6c0e4e4` | `dfb3b91b` |
| FastAPI #16557 | `e08d28df` | `5bcf22c9` | `75f3a149` |
| FastAPI #16559 | `37f91610` | `6b1599a0` | `2d1851f3` |
| FastAPI #16560 | `b2ce629a` | `3f949588` | `89317c70` |
| FastAPI #16564 | `3b39c91c` | `3d92fbb4` | `1282e9a9` |
| pytest #15255 | `ae37a013` | `22705a59` | `082ed70e` |

完整 SHA 见各证据文件。

## 4. 跨案例发现摘要

### 4.1 需求来源的差异

- **FastAPI 五个 PR**：均无关联 Issue。需求隐含在 PR 标题和测试断言中，没有独立的验收条件文档。
- **pytest #15255**：有关联 Issue #15254，包含可复现的参数化用例、运行环境和性能数据。

### 4.2 Base / Head 测试可比性

FastAPI 的 `regression-test` Job 与 `test` 矩阵**不是同条件对照**：

| 维度 | Base（regression-test） | Head（test 矩阵） |
|------|------------------------|-------------------|
| 代码版本 | PR 的 base SHA（旧代码） | PR 的 head SHA（新代码） |
| 测试集 | 仅新增/修改的 `test_*.py` 文件 | 完整测试套件 |
| 执行环境 | 单独 Job | 多平台多版本矩阵 |
| 失败判定 | 非零退出码 = "预期失败" | 零退出码 = "通过" |

因此，"Base 失败 + Head 通过"证明的是：**新测试能在旧代码上检测到某种异常，且新代码的完整测试套件通过。** 它不证明新测试 specifically 因为新代码而通过，也不证明旧代码的失败 exclusively 由本次修复解决。

### 4.3 失败分类的缺失

FastAPI 工作流不区分以下失败性质：

- **AssertionError**：测试断言明确失败（行为回归的强证据）
- **Snapshot mismatch**：`inline_snapshot` 检测到输出差异（行为变化的证据，但需要审查差异内容）
- **EOFError / 交互式提示**：`inline_snapshot` 在非交互环境中等待输入（测量工具本身的问题）
- **Collection error**：测试文件无法加载（环境问题）
- **其他非零退出码**：原因不明

PR #16555 和 #16560 的基线重放日志以 snapshot 交互提示结束，Job 仍报告 success。这不是"基线行为失败"的明确证据，而是"日志诊断不充分"。

### 4.4 证据强度分级

| 案例 | 需求可追溯性 | 代码变更可审查性 | 基线失败性质 | 测试-需求映射 |
|------|------------|----------------|------------|-------------|
| #16557 | ⚠️ 无 Issue，需求隐含 | ✅ 单文件逻辑变更 | ✅ AssertionError 行为失败 | ✅ 测试直接覆盖修复行为 |
| #16559 | ⚠️ 无 Issue，需求隐含 | ✅ 单文件逻辑变更 | ✅ AssertionError 行为失败 | ✅ 测试直接覆盖修复行为 |
| #16564 | ⚠️ 无 Issue，需求隐含 | ✅ 重构级变更 | ✅ AssertionError 行为失败 | ✅ 测试覆盖错误位置修复 |
| #16555 | ⚠️ 无 Issue，需求隐含 | ✅ 多文件重构 | ❌ Snapshot 交互异常 | ⚠️ 测试覆盖但失败性质不明 |
| #16560 | ⚠️ 无 Issue，需求隐含 | ✅ 单文件逻辑变更 | ❌ Snapshot 交互异常 | ⚠️ 测试覆盖但失败性质不明 |
| pytest #15255 | ✅ Issue + 复现 + 性能数据 | ✅ 新算法 + 结构性测试 | ❌ 无基线重放 | ✅ 结构性不变量测试 |

## 5. 对后续实验设计的校准

基于 Experiment 0 的发现，以下判断需要修正或确认：

### 5.1 研究范围是否仍限于 Bug Fix PR？

五个 FastAPI PR 属于同一功能问题簇（AliasChoices），pytest 案例是性能优化。如果研究问题限定为"具有明确行为要求的代码变更"，pytest #15255 应当保留为对照案例，因为它展示了**不同类型的变更需要不同类型的验证证据**。

### 5.2 Test Oracle Independence 是否可判断？

在现有六个案例中，Test Oracle 的来源是：
- FastAPI：测试断言本身（无独立 Issue 定义预期行为）
- pytest：Issue #15254 中的性能数据和结构性要求

对于 FastAPI 案例，Test Oracle 和测试代码**同源**——都是 PR 作者同时编写的。这意味着无法独立验证"测试是否真的验证了需求"，因为需求本身没有独立于测试的表述。

### 5.3 失败分类体系是否需要修改？

Experiment 0 确认至少需要以下分类：
1. **AssertionError（行为断言失败）** — 强证据
2. **Snapshot mismatch（快照差异）** — 中等证据，需审查差异内容
3. **Interactive prompt / EOFError** — 无效证据，测量工具问题
4. **Collection error** — 无效证据，环境问题
5. **其他非零退出码** — 未知，需进一步诊断

### 5.4 哪些证据可以自动提取？

- ✅ PR 元数据（SHA、文件列表、AI 披露）
- ✅ 代码 diff（生产代码和测试代码的变更）
- ✅ CI Job 状态和摘要统计（passed/failed/skipped 数量）
- ⚠️ CI 日志中的具体失败输出（需要解析 pytest 输出格式）
- ❌ 失败性质分类（需要理解断言内容和上下文）
- ❌ 需求-测试映射（需要理解需求意图）

### 5.5 Mutation Testing 是否必要？

在现有六个案例中，Mutation Testing 的价值有限：
- FastAPI 案例的测试已经直接针对修复行为，mutation 不太可能揭示新的覆盖缺口
- pytest 案例的测试验证结构性不变量，mutation 的价值取决于能否构造有意义的变异体

建议：**第一版不引入 Mutation Testing**，先验证更基础的证据链是否成立。

### 5.6 下一阶段需要什么样的负面控制样本？

Experiment 0 已经包含两个"日志诊断不充分"的案例（#16555、#16560），但它们不是真正的负面控制（即"测试应该通过但实际上不应该"的案例）。

建议下一阶段寻找：
- 测试在 Base 上通过但 Head 上失败的案例（反向 red-green）
- 测试在 Base 和 Head 上都通过但需求未被满足的案例（遗漏覆盖）
- 测试失败但失败原因与本次修复无关的案例（噪声干扰）

## 6. 交付物

- `evidence/fastapi-16557.md` — C1 证据记录
- `evidence/fastapi-16559.md` — C2 证据记录
- `evidence/fastapi-16564.md` — C3 证据记录
- `evidence/fastapi-16555.md` — C4 证据记录
- `evidence/fastapi-16560.md` — C5 证据记录
- `evidence/pytest-15255.md` — C6 证据记录

## 7. 原始来源

所有结论均基于以下公开材料，固定到指定 SHA：

- GitHub PR 页面、diff 文件和 Actions 日志
- `09-change-assurance-pilot.md` 中已记录的初步发现

未来仓库版本变化后，必须重新固定 SHA 和采集记录。
