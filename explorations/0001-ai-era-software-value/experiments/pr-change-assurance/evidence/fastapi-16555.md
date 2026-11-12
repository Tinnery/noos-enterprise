# C4 — FastAPI #16555：Query、Header、Cookie 的 AliasChoices

**研究用途：** Snapshot 交互异常案例  
**状态：** 证据重建完成

---

## 0. 版本标识

| 字段 | 值 |
|------|-----|
| PR | [#16555](https://github.com/fastapi/fastapi/pull/16555) |
| 标题 | 🐛 Fix `AliasChoices` for query parameters, headers, and cookies |
| 作者 | tiangolo |
| Base SHA | `44cc7420b798b70b406516f5f0abf039f99edbe3` |
| Head SHA | `b6c0e4e43362a1e9b5a25d1b8ced3eb681d251e8` |
| Merge SHA | `dfb3b91b7c6102cddde6e2cb1422d0faaa273be5` |
| 合并日期 | 2026-10-20 |
| 分支 | `codex/query-alias-choices` → `master` |
| 提交数 | 2 |

---

## 1. 原始需求

**[Judgment]** 无关联 Issue，无独立验收条件文档。

需求隐含在 PR 标题中：修复 Query、Header、Cookie 参数对 `AliasChoices` 的处理。从 diff 推断，问题是旧代码只使用 `get_validation_alias(field)` 获取单个别名，不支持多别名选择逻辑，且 OpenAPI schema 生成也不正确。

---

## 2. 生产代码变更

**文件：**
- `fastapi/dependencies/utils.py`（新增 `_get_param_aliases` 函数，修改 `request_params_to_args`）
- `fastapi/openapi/utils.py`（修改 `_get_openapi_operation_parameters`）
- `fastapi/_compat/v2.py`（修改 `get_schema_from_model_field`）

**[Fact]** 核心修改：

### 新增 `_get_param_aliases` 函数

```python
def _get_param_aliases(
    field: ModelField,
    convert_underscores: bool = False,
) -> list[tuple[str, str]]:
    """Return (alias, request_name) pairs for a query/header/cookie field."""
    # ...
    if isinstance(validation_alias, AliasChoices):
        for choice in validation_alias.choices:
            if isinstance(choice, str):
                name = _resolve_alias_name(choice, ...)
                aliases.append((name, request_name))
    # ...
```

**行为变化：** 为 Query/Header/Cookie 参数提供统一的别名列表提取，支持 `AliasChoices` 的多别名遍历。

### 修改 `request_params_to_args`

使用 `_get_param_aliases` 遍历所有别名，找到第一个有值的别名。

### 修改 OpenAPI schema 生成

使用 `_get_param_aliases` 的第一个别名作为 OpenAPI 参数名和 schema 的 `field_alias`。

---

## 3. 测试代码变更

**文件：**
- `tests/test_query_alias_choices.py`（**新增**，466 行）
- `tests/test_header_cookie_alias_choices.py`（**新增**，649 行）

**[Fact]** 新增测试文件覆盖以下场景：

### `test_query_alias_choices.py`

| 测试函数 | 验证行为 |
|----------|----------|
| `test_individual_query_alias_choices` | 独立 Query 参数的别名选择 |
| `test_model_query_alias_choices` | Model 绑定的 Query 参数别名选择 |
| `test_invalid_choice_uses_selected_alias` | 无效值时使用选中别名 |
| `test_missing_field_uses_first_alias` | 缺失字段时使用第一个别名 |
| `test_list_query_alias_choices` | 列表类型的别名选择 |
| `test_openapi_schema` | OpenAPI schema 使用选中别名 |

### `test_header_cookie_alias_choices.py`

| 测试函数 | 验证行为 |
|----------|----------|
| `test_header_alias_choices` | Header 参数的别名选择 |
| `test_cookie_alias_choices` | Cookie 参数的别名选择 |
| `test_path_alias_choices_are_unchanged` | Path 参数不受影响 |
| `test_openapi_schema` | OpenAPI schema 使用选中别名 |

测试大量使用 `inline_snapshot` 验证 OpenAPI schema 输出。

---

## 4. Base 和 Head 执行结果

### Base（regression-test Job）

**[Fact]** 日志未在 09 中详细记录。根据 09 的描述：

> 基线重放日志以 inline snapshot 的交互提示结束，出现了 "Do you want to fix these snapshots?" 和 EOFError。对应 Job 最终仍为 success。

**[Judgment]** 这不是明确的行为回归失败。`inline_snapshot` 在非交互环境中检测到 snapshot 差异时，会尝试提示用户确认更新，但由于 stdin 不可用，触发 EOFError。Job 报告 success 可能是因为退出码被特殊处理。

### Head（test 矩阵）

**[Fact]** PR 版本测试矩阵成功。

---

## 5. 测试失败性质

**[Judgment]**

- **失败类型：** EOFError（`inline_snapshot` 交互式提示）
- **失败原因：** `inline_snapshot` 检测到 snapshot 差异，尝试在终端提示用户确认更新，但 CI 环境无 stdin
- **失败规模：** 未知（日志未给出完整的 pytest 摘要）

**关键问题：** 这**不是** AssertionError。`inline_snapshot` 的交互提示意味着 snapshot 输出与预期不同，但差异内容未被记录。无法判断：
1. 差异是否由本次修复引起
2. 差异是否属于预期行为变化
3. 差异是否属于 snapshot 需要更新

---

## 6. 测试是否验证了原始需求？

**[Judgment]** 无法确定。

**验证的部分：**
- ✅ Head 测试矩阵通过，说明新代码在 snapshot 更新后通过
- ✅ 测试覆盖了 Query/Header/Cookie 的别名选择行为

**未验证的部分：**
- ❓ Base 的 snapshot 差异性质不明
- ❓ 无法确认 Base 失败是否由本次修复引起
- ❓ 无法确认 snapshot 差异是否属于预期行为变化

**[Unknown]** Base 的 snapshot 差异内容。如果差异是 OpenAPI schema 的变化（因为新代码修改了 schema 生成逻辑），那么这是预期行为，不是回归。

---

## 7. 没有证据支持的主张

| 主张 | 证据状态 |
|------|----------|
| "修复了 Query/Header/Cookie 的 AliasChoices" | ✅ 有代码变更支持 |
| "Base 上测试失败" | ❌ 日志诊断不充分，无法确认 |
| "snapshot 差异由本次修复引起" | ❌ 无法确认 |
| "snapshot 差异属于预期行为" | ❌ 无法确认 |
| "AI 辅助了代码编写" | ⚠️ 分支名含 `codex/`，但 PR 正文无明确 AI 披露 |

---

## 8. 证据分级总结

| 项目 | 分级 |
|------|------|
| 代码变更内容 | **Fact**（diff 可审查） |
| Base 日志含 snapshot 交互提示 | **Fact**（09 记录） |
| Base 失败性质为行为回归 | **Unknown**（snapshot 差异性质不明） |
| Head 测试通过 | **Fact**（Actions 记录） |
| 测试验证了修复行为 | **Judgment**（测试覆盖别名选择场景） |
| AI 参与程度 | **Unknown**（无明确披露） |

---

## 9. 方法论启示

这个案例暴露了一个测量问题：**CI Job 的 success/failure 不能替代对测试输出和失败类型的检查。**

`inline_snapshot` 的交互提示在 CI 环境中是噪声，不是有效的行为回归证据。如果自动化工具只看退出码，会把这个案例误判为"基线通过"或"基线失败"，而实际上两者都不准确。
