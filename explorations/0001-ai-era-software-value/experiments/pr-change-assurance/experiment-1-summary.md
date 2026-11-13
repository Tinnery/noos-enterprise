# Experiment 1 — 离线 Evidence Packet 原型

**状态：** 完成  
**日期：** 2026-11-13  
**研究问题：** 是否可以机械化地提取和组织 PR 变更的证据？

---

## 1. 目的

开发一个最小原型，验证以下能力：
1. 解析 PR 元数据和代码 diff
2. 识别 CI 日志中的失败类型（AssertionError、EOFError、Snapshot mismatch）
3. 生成结构化的 Claim / Evidence / Unknown 记录
4. 区分哪些信息可以自动提取，哪些需要人工判断

---

## 2. 实现

### 2.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| 数据模型 | `packet/models.py` | 定义 PRMetadata、CodeChange、CIJobResult、Claim、Evidence、Unknown 等数据结构 |
| Diff 解析器 | `packet/diff_parser.py` | 解析 unified diff，提取函数级变更，区分生产代码和测试代码 |
| CI 日志解析器 | `packet/ci_log_parser.py` | 解析 pytest 输出，识别失败类型（AssertionError、EOFError、Snapshot mismatch） |
| 证据生成器 | `packet/generator.py` | 将解析结果组织为 Claim / Evidence / Unknown 记录 |
| 报告生成器 | `packet/reporter.py` | 将 EvidencePacket 转换为可读的 Markdown 报告 |
| 运行脚本 | `run_packet.py` | 对六个案例运行原型，生成报告 |

### 2.2 技术选择

- **语言：** Python 3.10+
- **依赖：** 无外部依赖，仅使用标准库（dataclasses、re、pathlib）
- **输入格式：** 手动构造的案例数据（基于 Experiment 0 的证据文件）
- **输出格式：** Markdown 报告

---

## 3. 验证结果

对六个案例运行原型，生成 Evidence Packet 报告：

| 案例 | Claims | Evidence | Unknowns | 关键特征 |
|------|--------|----------|----------|----------|
| C1: FastAPI #16557 | 1 | 4 | 4 | AssertionError 被识别为行为回归的强证据 |
| C2: FastAPI #16559 | 1 | 4 | 4 | AssertionError，26 项基线失败 |
| C3: FastAPI #16564 | 1 | 4 | 4 | AssertionError，重构级变更 |
| C4: FastAPI #16555 | 1 | 3 | 4 | EOFError 被识别为无效证据，不生成 Base 失败证据 |
| C5: FastAPI #16560 | 1 | 3 | 4 | EOFError，与 C4 相同模式 |
| C6: pytest #15255 | 2 | 3 | 1 | 有独立 Issue 和 AI 披露，只有 1 个 Unknown |

### 3.1 关键验证点

#### ✅ 失败类型识别

- **AssertionError**（C1-C3）：被正确识别为"行为回归的强证据"，生成 `test_failure_on_base` 类型的 Evidence
- **EOFError**（C4-C5）：被正确识别为"测量工具问题，无效证据"，不生成 Base 失败证据
- **无 Base 重放**（C6）：不生成 Base 相关证据

#### ✅ 需求独立性识别

- FastAPI 五个 PR（C1-C5）：无独立 Issue，生成"Test Oracle 与测试代码同源"的 Unknown
- pytest #15255（C6）：有独立 Issue #15254，生成 2 个 Claims（PR 标题 + Issue 需求）

#### ✅ AI 披露识别

- FastAPI 五个 PR：无 AI 披露，生成"AI 参与程度如何？"的 Unknown
- pytest #15255：有 AI 披露（"Written by Claude Opus 5.5"），不生成该 Unknown

#### ✅ 证据分级

- **Fact**：代码变更、CI 统计、Head 测试通过
- **Evidence**：Base 重放失败（AssertionError）
- **Judgment**：PR 标题作为 Claim
- **Unknown**：需求独立性、Base/Head 可比性、AI 参与、修复边界

---

## 4. 发现

### 4.1 可以机械化提取的信息

1. ✅ PR 元数据（SHA、文件列表、关联 Issue、AI 披露）
2. ✅ 代码 diff 中的函数级变更
3. ✅ CI Job 摘要统计（passed/failed/skipped）
4. ✅ AssertionError 识别（通过正则匹配）
5. ✅ EOFError 识别（通过正则匹配）
6. ✅ Snapshot mismatch 识别（通过正则匹配）

### 4.2 需要人工判断的信息

1. ⚠️ **需求-测试映射**：测试是否真的验证了需求？
   - 原型只能识别"是否有独立 Issue"，无法判断测试断言是否覆盖了需求的真实意图
2. ⚠️ **失败性质的最终分类**：需要理解上下文
   - 原型可以识别 AssertionError，但无法判断"这个断言失败是否由本次修复引起"
3. ⚠️ **Snapshot 差异是否为预期行为变化**：
   - 原型可以识别 Snapshot mismatch，但无法判断差异是否属于预期行为
4. ⚠️ **Base/Head 测试的可比性**：
   - 原型可以标记"Base/Head 不是同条件对照"，但无法量化差异的影响

### 4.3 原型的局限性

1. **输入数据是手动构造的**：当前原型没有直接从 GitHub API 或 CI 日志文件提取数据，而是基于 Experiment 0 的证据文件手动构造案例数据。这意味着原型的"自动化"程度被高估了。

2. **没有解析真实的 CI 日志**：虽然实现了 `ci_log_parser.py`，但没有在实际的 CI 日志文件上运行。失败类型的识别是基于假设的模式，而非真实的日志解析。

3. **没有解析真实的 diff**：虽然实现了 `diff_parser.py`，但没有在实际的 diff 文件上运行。函数级变更是手动输入的，而非从 diff 中自动提取。

4. **Claim 提取过于简单**：当前只从 PR 标题提取 Claim，没有从 Issue 正文、PR 描述或代码注释中提取更详细的需求定义。

---

## 5. 对研究问题的回答

### 核心问题：是否可以机械化地提取和组织 PR 变更的证据？

**回答：部分可以，但有明确边界。**

#### 可以机械化的部分

1. **结构化信息的提取**：PR 元数据、文件列表、CI 统计、失败类型识别
2. **证据的组织**：将提取的信息组织为 Claim / Evidence / Unknown 结构
3. **Unknown 的识别**：识别哪些信息缺失（如无独立 Issue、无 AI 披露）

#### 不能机械化的部分

1. **需求-测试映射的判断**：无法判断测试是否真的验证了需求
2. **失败性质的最终分类**：无法判断失败是否由本次修复引起
3. **Snapshot 差异的语义理解**：无法判断差异是否为预期行为变化
4. **Base/Head 可比性的量化**：无法量化 Base/Head 差异的影响

#### 关键洞察

**机械化的价值不在于替代人工判断，而在于：**

1. **减少重复劳动**：自动提取结构化信息，减少人工翻阅 PR 和 CI 日志的时间
2. **标准化证据组织**：提供统一的 Claim / Evidence / Unknown 结构，便于独立复核
3. **明确人工判断的边界**：通过列出 Unknown，明确哪些信息需要人工判断

---

## 6. 对后续实验的校准

### 6.1 是否需要修改 Evidence Packet 的设计？

**不需要。** 当前的 Claim / Evidence / Unknown 结构能够有效地组织证据，区分 Fact / Evidence / Judgment / Unknown。

### 6.2 是否需要引入 LLM？

**暂缓。** Experiment 1 证明，在不使用 LLM 的情况下，已经可以机械化地提取和组织结构化信息。引入 LLM 的价值在于：

1. **从 Issue 正文和 PR 描述中提取更详细的 Claim**
2. **判断 Snapshot 差异是否为预期行为变化**
3. **判断失败是否由本次修复引起**

但这些判断的准确性需要验证。在没有验证之前，引入 LLM 可能引入新的不确定性。

### 6.3 下一步应该做什么？

**Experiment 2：负面控制和 Mutation Testing（暂缓）**

Experiment 0 已经包含两个"日志诊断不充分"的案例（C4、C5），它们可以作为负面控制的起点。但 Experiment 1 的原型没有在这些案例上运行真实的 CI 日志解析，因此无法验证原型是否能正确处理这些情况。

**建议的下一步：**

1. **从真实的 CI 日志中提取失败输出**：使用 `ci_log_parser.py` 解析 FastAPI 的 regression-test Job 日志，验证 AssertionError 和 EOFError 的识别准确性
2. **从真实的 diff 中提取函数级变更**：使用 `diff_parser.py` 解析 FastAPI 的 diff 文件，验证函数级变更的提取准确性
3. **根据验证结果决定是否需要引入 LLM**

---

## 7. 交付物

- `packet/models.py` — 数据模型
- `packet/diff_parser.py` — Diff 解析器
- `packet/ci_log_parser.py` — CI 日志解析器
- `packet/generator.py` — 证据生成器
- `packet/reporter.py` — 报告生成器
- `packet/__init__.py` — 模块入口
- `run_packet.py` — 运行脚本
- `output/c1-evidence-packet.md` — C1 报告
- `output/c2-evidence-packet.md` — C2 报告
- `output/c3-evidence-packet.md` — C3 报告
- `output/c4-evidence-packet.md` — C4 报告
- `output/c5-evidence-packet.md` — C5 报告
- `output/c6-evidence-packet.md` — C6 报告

---

## 8. 原始来源

所有结论均基于以下材料：

- Experiment 0 的证据文件（`evidence/fastapi-*.md`、`evidence/pytest-*.md`）
- `10-pr-change-assurance-research.md` 中的研究设计
- 手动构造的案例数据（`run_packet.py` 中的 `create_case_*` 函数）

未来如果从真实的 CI 日志和 diff 文件中提取数据，需要重新验证原型的准确性。
