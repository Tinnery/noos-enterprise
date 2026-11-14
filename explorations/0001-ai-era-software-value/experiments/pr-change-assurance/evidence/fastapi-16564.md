# C3 — FastAPI #16564：Form 与 File 的验证错误位置

**研究用途：** 基线行为失败案例  
**状态：** 证据重建完成

---

## 0. 版本标识

| 字段 | 值 |
|------|-----|
| PR | [#16564](https://github.com/fastapi/fastapi/pull/16564) |
| 标题 | 🐛 Fix validation error locations for form and file `AliasChoices` |
| 作者 | tiangolo |
| Base SHA | `3b39c91cd1f221042313634db901c64615bb4fb5` |
| Head SHA | `3d92fbb407ca10c1e58f44ef13c53888a94aaaf8` |
| Merge SHA | `1282e9a9f1ac0647cb2031c6dd9c1d5631ade4d4` |
| 合并日期 | 2026-10-21 |
| 分支 | `codex/form-alias-error-locations` → `master` |

---

## 1. 原始需求

**[Judgment]** 无关联 Issue，无独立验收条件文档。

需求隐含在 PR 标题中：修复 Form 和 File 参数在使用 `AliasChoices` 时，验证错误的位置（`loc` 字段）应使用实际选中的别名，而非固定的第一个别名或字段名。

这是对 #16557 和 #16559 的后续修复——前两个 PR 解决了值选择逻辑，但错误位置仍然不正确。

---

## 2. 生产代码变更

**文件：** `fastapi/dependencies/utils.py`

**[Fact]** 这是一次**重构级变更**，涉及多个函数的结构调整：

### 修改 1：`_extract_form_items` 移除冗余逻辑

删除了旧代码中对 `field.config is None` 的特殊处理（单独添加 `get_validation_alias` 到 `field_aliases`），统一由别名遍历逻辑处理。

### 修改 2：`_extract_form_body` 从 dict 返回改为 async iterator

```python
# 旧代码
async def _extract_form_body(...) -> dict[str, Any]:
    values: dict[str, Any] = {}
    # ...
    values[alias] = value
    return values

# 新代码
async def _extract_form_body(...) -> AsyncIterator[tuple[str, Any, ModelField | None]]:
    # ...
    yield alias, value, field
```

**行为变化：** 不再返回完整的 dict，而是逐个 yield `(alias, value, field)` 元组，使调用方能够追踪每个值对应的字段和实际使用的别名。

### 修改 3：`request_body_to_args` 使用 `form_values` 追踪

```python
# 新代码
form_values: dict[str, tuple[str, Any]] = {}
# ...
async for alias, value, field in _extract_form_body(fields_to_extract, received_body):
    if single_not_embedded_field:
        body_to_process[alias] = value
    elif field is not None:
        form_values[field.name] = (alias, value)
# ...
if isinstance(received_body, FormData):
    alias, value = form_values.get(field.name, (aliases[0], Undefined))
    loc = ("body", alias)
```

**行为变化：** 对 FormData，使用 `form_values` 字典追踪每个字段实际使用的别名和值，确保错误位置使用正确的别名。

### 修改 4：`fastapi/_compat/v2.py` 和 `fastapi/openapi/utils.py`

- `get_schema_from_model_field` 新增 `field_alias` 参数，允许覆盖默认的 validation_alias
- `_get_openapi_operation_parameters` 使用 `_get_param_aliases` 获取第一个别名作为 OpenAPI 参数名

---

## 3. 测试代码变更

**文件：**
- `tests/test_request_params/test_file/test_nullable_and_defaults.py`（+106 行）
- `tests/test_request_params/test_form/test_nullable_and_defaults.py`（+65 行，修改 8 行）

**[Fact]** 新增测试：

### `test_file_alias_choices_errors_use_selected_aliases`

验证 File 参数的验证错误位置使用实际选中的别名：
- 使用 `secondary` 别名发送有效值 → 200
- 使用 `secondary` 发送无效值 → 错误位置为 `["body", "secondary"]`
- 使用 `primary` 发送无效值 → 错误位置为 `["body", "primary"]`
- 缺失必填字段 → 错误位置为 `["body", "primary"]`（第一个别名）

### `test_unselected_file_alias_choices_use_the_next_alias`

验证当第一个别名未提供时，使用下一个别名。

### `test_form_list_alias_choices_error_uses_selected_alias`

验证 Form 列表参数的错误位置使用选中别名。

### `test_individual_form_parameters_can_share_an_alias_choice`

验证多个独立 Form 参数可以共享别名选择。

### 修改的测试

- `test_required_form_alias_choices_preserve_validation_precedence`：移除参数化的 `error_alias`，统一检查第一个别名
- `test_checkbox_alias_choices_preserve_validation_precedence`：同上

---

## 4. Base 和 Head 执行结果

### Base（regression-test Job）

**[Fact]** [Job 日志](https://github.com/fastapi/fastapi/actions/runs/39565876493/job/119107903012)

```
6 failed, 179 passed, 3 skipped, 1.77s
```

**[Judgment]** 六项失败集中在本次新增或修改的测试中。失败性质为 **AssertionError**——旧代码的错误位置使用错误的别名（如 legacy 字段名而非实际选中的 alias）。

### Head（test 矩阵）

**[Fact]** [Job 日志](https://github.com/fastapi/fastapi/actions/runs/39565876493/job/119107976376)

```
4414 passed, 20 skipped, 5 xfailed, 110.37s
```

（Ubuntu / Python 3.13 coverage Job）

---

## 5. 测试失败性质

**[Judgment]**

- **失败类型：** AssertionError
- **失败原因：** 旧代码的错误位置（`loc`）使用 `get_validation_alias(field)` 返回的第一个别名或字段名，而非实际选中的别名
- **失败规模：** 6 项，集中在错误位置断言

**[Unknown]** 具体失败输出的详细内容未从日志中提取。

---

## 6. 测试是否验证了原始需求？

**[Judgment]** 部分验证。

**验证的部分：**
- ✅ 验证错误位置使用实际选中的别名
- ✅ File 和 Form 参数均覆盖
- ✅ 缺失字段、无效值、共享别名等场景

**未验证的部分：**
- ❓ 没有独立 Issue 定义"正确行为"
- ❓ 这是第三次迭代修复（#16557 → #16559 → #16564），说明前两次修复不完整
- ❓ 无法确认是否还有其他错误位置不正确的场景

---

## 7. 没有证据支持的主张

| 主张 | 证据状态 |
|------|----------|
| "修复了验证错误位置" | ✅ 有代码重构和 6 项基线失败支持 |
| "旧代码的错误位置不正确" | ✅ 测试断言可直接验证 |
| "修复不影响其他行为" | ✅ Head 4414 项测试通过 |
| "这是完整的修复" | ⚠️ 无法确认，已经是第三次迭代 |
| "AI 辅助了代码编写" | ✅ PR 正文披露 Codex（gpt-6-astra）参与开发并经人工审阅（分支名 `codex/` 亦印证） |

---

## 8. 证据分级总结

| 项目 | 分级 |
|------|------|
| 代码变更内容 | **Fact**（diff 可审查） |
| 基线失败 6 项 | **Fact**（日志可查） |
| Head 4414 项通过 | **Fact**（日志可查） |
| 失败性质为 AssertionError | **Judgment**（基于 09 描述和 diff 推断） |
| 测试验证了修复行为 | **Judgment**（测试覆盖错误位置场景，但需求无独立定义） |
| AI 参与程度 | **Fact**（PR 正文披露 Codex 辅助 + 人工审阅） |
