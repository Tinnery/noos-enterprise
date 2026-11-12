# C6 — pytest #15255：tmp_path / mktemp 的 O(N²) 性能问题

**研究用途：** 性能验证方法的边界对照  
**状态：** 证据重建完成

---

## 0. 版本标识

| 字段 | 值 |
|------|-----|
| PR | [#15255](https://github.com/pytest-dev/pytest/pull/15255) |
| 标题 | tmpdir: hand out numbered dirs from a per-prefix counter |
| 作者 | RonnyPfannschmidt |
| Base SHA | `ae37a013763e9c4a143245eda1acdc3c27961685` |
| Head SHA | `22705a59e6b697edf6242ef96fb3abd933339259` |
| Merge SHA | `082ed70e314ee8e1ab117763d17fe801648f7508` |
| 关联 Issue | [#15254](https://github.com/pytest-dev/pytest/issues/15254) |
| AI 披露 | "Written by Claude Opus 5.5 via Claude Code for the pytest maintainers; I prompted it, it did the work, I read it." |
| Commit trailers | `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>` |

---

## 1. 原始需求

**[Fact]** 有关联 Issue #15254，包含：

1. **问题描述：** `TempPathFactory.mktemp()` 和 `tmp_path` 每次调用都列出整个 `basetemp` 目录以寻找下一个可用编号。随着测试数量增长，`basetemp` 中的条目越来越多，导致 O(N²) 的工作量。
2. **可复现的参数化用例：** Issue 提供了可运行的复现代码。
3. **性能数据：** 1000 / 2000 / 4000 个测试，main 分支分别为 3.53 / 10.10 / 34.35 秒。
4. **原有实现的限制：** 明确记录了 `make_numbered_dir` 的设计问题。

**[Judgment]** 这是六个案例中**唯一具有独立需求定义的案例**。Issue 不仅描述了问题，还提供了验证标准（性能数据）和复现方法。

---

## 2. 生产代码变更

**文件：**
- `src/_pytest/tmpdir.py`（核心修改）
- `changelog/15254.improvement.rst`（新增）

**[Fact]** 核心修改：

### 新增 `_make_counted_dir` 方法

```python
def _make_counted_dir(self, prefix: str) -> Path:
    root = self.getbasetemp()
    key = prefix.lower()
    number = self._next_number.get(key, 0)
    collisions = 0
    while True:
        path = root.joinpath(f"{prefix}{number}")
        try:
            path.mkdir(mode=0o700)
        except OSError as e:
            collisions += 1
            if collisions == 10:
                listed = max(map(parse_num, find_suffixes(root, prefix)), default=-1)
                number = max(number, listed) + 1
            elif collisions == 20:
                raise OSError(...) from e
            else:
                number += 1
        else:
            break
    self._next_number[key] = number + 1
    _force_symlink(root, prefix + "current", path)
    return path
```

**行为变化：**
1. 每个 prefix 维护一个计数器（`_next_number` 字典），从 0 开始递增
2. `mkdir` 决定唯一性——如果名称已存在（目录、文件或 dangling symlink），跳过
3. 连续 10 次冲突后，列出目录一次以跳过已占用的范围
4. 连续 20 次冲突后，抛出 OSError，防止无限循环
5. 不再依赖 `make_numbered_dir` 的全目录扫描

### 行为差异（PR 正文明确记录）

- `mktemp` 编号不再"大于任何已有编号"，而是跳过已存在名称
- 编号永不下降（main 分支中，被删除的编号可能被重用）
- 大小写敏感文件系统中，外来的 `X2` 不再把 `x` 推到 2 之后

---

## 3. 测试代码变更

**文件：** `testing/test_tmpdir.py`（+105 行）

**[Fact]** 新增测试验证**结构性不变量**，而非简单的输出快照：

| 测试函数 | 验证的不变量 |
|----------|-------------|
| `test_mktemp_does_not_list_basetemp` | mktemp 正常路径不扫描 basetemp（通过 monkeypatch 将 `find_suffixes` 设为 None） |
| `test_counted_dir_skips_unexpected_entries` | 已存在的目录、文件和 dangling symlink 都能被跳过 |
| `test_counted_dir_jumps_past_long_run` | 连续 50 个名字冲突后只执行一次目录扫描 |
| `test_counted_dir_overlapping_prefixes` | 重叠 prefix（`test_a` 和 `test_a1`）不产生名称冲突 |
| `test_counted_dir_gives_up` | 连续冲突达到上限后明确失败，不无限循环 |
| `test_counted_dir_retries_other_errors` | 其他 OSError（包括 Windows PermissionError）按策略重试 |

**[Judgment]** 这组测试的价值在于，它把性能优化背后的**结构性要求**变成可断言的不变量。例如：
- 通过 monkeypatch 替换 `find_suffixes`，直接判断正常路径没有扫描
- 通过构造 50 个已占用名称，验证只扫描一次
- 通过 monkeypatch `Path.mkdir` 始终抛异常，验证不会无限循环

这比依赖一个波动较大的 CI wall-clock 阈值更可审查。

---

## 4. Base 和 Head 执行结果

### Base

**[Fact]** 没有观察到独立的 base 重放 Job。pytest 项目没有类似 FastAPI 的 `regression-test` 工作流。

### Head（test 矩阵）

**[Fact]** [Ubuntu / Python 3.12 Job](https://github.com/pytest-dev/pytest/actions/runs/40217223246/job/121240985185)

```
4705 passed, 50 skipped, 13 xfailed, 7 xpassed, 2 warnings, 345.85s
```

**[Judgment]** 完整测试矩阵通过，但这只证明 PR 版本在所运行矩阵中的测试结果，不等于独立证明性能提升。

---

## 5. 测试失败性质

**[Judgment]** 不适用——没有 Base 重放，因此没有 Base 失败可供分类。

---

## 6. 测试是否验证了原始需求？

**[Judgment]** 部分验证，但验证方式与 FastAPI 案例根本不同。

**验证的部分：**
- ✅ 结构性不变量（不扫描、跳过冲突、有限重试、不无限循环）
- ✅ 边界情况（dangling symlink、PermissionError、重叠 prefix）
- ✅ 完整测试矩阵通过（无回归）

**未验证的部分：**
- ❓ 性能提升数据（Issue 和 PR 中的数字环境不同，不能合并）
- ❓ 独立复现的性能基准（本研究未重新运行）
- ❓ 在实际大规模测试套件中的表现

**[Judgment]** 这个案例展示了**不同类型的变更需要不同类型的验证证据**：
- 功能修复：错误输入在旧版本失败，在新版本满足预期行为
- 性能优化：可复现负载、基准条件、重复测量和结构性复杂度不变量

---

## 7. 没有证据支持的主张

| 主张 | 证据状态 |
|------|----------|
| "修复了 O(N²) 性能问题" | ⚠️ 有结构性测试支持算法正确性，但性能数据未独立复现 |
| "新算法保持正确行为" | ✅ 结构性不变量测试 + 完整测试矩阵 |
| "AI 辅助了代码编写" | ✅ PR 正文和 commit trailer 明确披露 |
| "人工审阅了 AI 代码" | ⚠️ 作者声明"我读了它"，但无法衡量审阅深度 |
| "不存在回归风险" | ⚠️ 完整测试矩阵通过支持，但不能证明绝对无回归 |

---

## 8. 证据分级总结

| 项目 | 分级 |
|------|------|
| 代码变更内容 | **Fact**（diff 可审查） |
| Issue #15254 存在 | **Fact**（公开可查） |
| 结构性不变量测试 | **Fact**（测试代码可审查） |
| 性能提升数据 | **Evidence**（作者提交，未独立复现） |
| Head 4705 项通过 | **Fact**（日志可查） |
| AI 参与 | **Fact**（作者公开披露） |
| 人工审阅深度 | **Unknown** |

---

## 9. 方法论启示

这个案例与 FastAPI 的五个案例形成对照：

| 维度 | FastAPI 案例 | pytest 案例 |
|------|-------------|-------------|
| 需求来源 | 隐含在 PR 标题中 | 独立 Issue + 复现用例 |
| 验证方式 | red-on-base / green-on-head | 结构性不变量 + 完整测试矩阵 |
| Base 重放 | 有（FastAPI 工作流） | 无 |
| 性能证据 | 不适用 | 有（但未独立复现） |
| AI 披露 | 不明确（分支名暗示） | 明确（PR 正文 + commit trailer） |

**关键发现：** 不能把 Base 重放作为唯一正确的验收方法。对于性能优化，合适的证据是结构性复杂度不变量，而非 wall-clock 阈值。
