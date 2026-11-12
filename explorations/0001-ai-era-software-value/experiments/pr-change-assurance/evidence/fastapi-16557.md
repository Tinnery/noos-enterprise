# C1 — FastAPI #16557：Form Model 的 AliasChoices 提取

**研究用途：** 基线行为失败案例  
**状态：** 证据重建完成

---

## 0. 版本标识

| 字段 | 值 |
|------|-----|
| PR | [#16557](https://github.com/fastapi/fastapi/pull/16557) |
| 标题 | 🐛 Fix `AliasChoices` extraction for form models |
| 作者 | tiangolo |
| Base SHA | `e08d28df250b4e810862723166c83d2919944ed1` |
| Head SHA | `5bcf22c97909f35bf0ee8dda0b655e7113501473` |
| Merge SHA | `75f3a149359bfd39665aaf81dc223fb6fc28da23` |
| 合并日期 | 2026-10-20 |
| 分支 | `codex/form-model-alias-choices` → `master` |

---

## 1. 原始需求

**[Judgment]** 无关联 Issue，无独立验收条件文档。

需求隐含在 PR 标题和代码变更中：修复 Form Model 对 `AliasChoices` 的提取逻辑。从 diff 推断，问题涉及以下行为：

1. **`validate_by_alias=False` 时的别名选择逻辑错误**：旧代码先检查 `validate_by_name`，再检查 `validate_by_alias`，导致在 `validate_by_alias=False` 时仍然可能使用别名而非字段名。
2. **多字段共享别名时的值选择逻辑**：旧代码在所有别名中遍历寻找第一个有值的别名，但没有在找到值后 `break`，导致后续别名可能覆盖前面的选择。

**[Unknown]** 无法确认这些行为是否在 Issue 或讨论中被独立记录。PR 正文仅包含 CodSpeed 性能报告，没有行为描述。

---

## 2. 生产代码变更

**文件：** `fastapi/dependencies/utils.py`（`_extract_form_items` 函数）

**[Fact]** 两处逻辑修改：

### 修改 1：`validate_by_alias` 检查顺序

```python
# 旧代码
if config.get("validate_by_name", config.get("populate_by_name", False)):
    if config.get("validate_by_alias") is False:
        aliases = [field.name]
    elif field.name not in aliases:
        aliases.append(field.name)

# 新代码
if config.get("validate_by_alias") is False:
    aliases = [field.name]
elif (
    config.get("validate_by_name", config.get("populate_by_name", False))
    and field.name not in aliases
):
    aliases.append(field.name)
```

**行为变化：** 当 `validate_by_alias=False` 时，无论 `validate_by_name` 如何设置，都只使用字段名。旧代码在 `validate_by_name=True` 且 `validate_by_alias=False` 时，会先尝试别名列表，再添加字段名。

### 修改 2：值选择后添加 `break`

```python
# 旧代码
selected_alias = aliases[0]
for alias in aliases:
    if _get_multidict_value(field, received_body, alias=alias) is not Undefined:
        selected_alias = alias
        break
aliases = [selected_alias]

# 新代码
for alias in aliases:
    field_aliases.add(alias)
    # ... 值提取逻辑 ...
    if value is not Undefined:
        yield alias, value, field
        break  # 新增
```

**行为变化：** 旧代码先遍历所有别名找到第一个有值的别名，然后只处理该别名。新代码在遍历过程中直接处理，找到第一个有值的别名后立即 `break`，不再处理后续别名。

**[Judgment]** 这两处修改解决的是同一个问题：当多个字段共享一个别名（如 `AliasChoices("names", "legacy")` 和 `AliasChoices("text", "legacy")`）时，旧代码的遍历逻辑可能导致值被错误地分配给字段。

---

## 3. 测试代码变更

**文件：**
- `tests/test_request_params/test_file/test_nullable_and_defaults.py`（+31 行）
- `tests/test_request_params/test_form/test_nullable_and_defaults.py`（+80 行，修改 4 行）
- `tests/test_union_form_normalization.py`（修改 4 行）

**[Fact]** 新增测试：

### `test_model_files_can_share_an_unused_alias_choice`

测试两个 File 字段共享 `legacy` 别名时的行为：
- 发送 `legacy`（两次）和 `file`
- 期望 `files` 接收两个 `legacy` 值，`file` 接收 `file` 值

### `test_form_model_fields_can_share_an_unused_alias_choice`

测试两个 Form 字段共享 `legacy` 别名时的行为：
- 发送 `legacy`（两次）和 `text`
- 期望 `names` 接收两个 `legacy` 值，`text` 接收 `text` 值
- 参数化：urlencoded 和 multipart

### `test_unused_form_alias_choice_keeps_extra_value_shape`

测试当 `extra="allow"` 时，未使用的别名值保留在 extra 中：
- 发送 `names`、`text`、`legacy-names`、`legacy-text`
- 期望 `names` 和 `text` 使用主别名值，`legacy-*` 保留在 extra 中
- 参数化：urlencoded/multipart × unused="unused"/""

### 修改的测试

- `test_unchecked_checkbox_with_alias_choices_overrides_defaults`：参数化增加 `validate_by_alias=False` 配置
- `test_union_form_normalization`：修改断言中的错误位置从 `extra` 改为 `secondary`

---

## 4. Base 和 Head 执行结果

### Base（regression-test Job）

**[Fact]** [Job 日志](https://github.com/fastapi/fastapi/actions/runs/39506409538/job/118916329214)

```
9 failed, 211 passed, 3 skipped, 3.04s
```

**[Judgment]** 九项失败集中在本次新增或修改的测试中，涉及 Form Model 对别名选择、重复字段和 extra 字段形态的处理。失败性质为 **AssertionError**（测试断言明确失败），属于行为回归的强证据。

### Head（test 矩阵）

**[Fact]** PR 版本测试矩阵成功（具体 Job 日志未在 09 中记录，需从 Actions 页面获取）。

---

## 5. 测试失败性质

**[Judgment]** 基于 09 的描述和 diff 分析：

- **失败类型：** AssertionError
- **失败原因：** 旧代码的别名选择逻辑导致值被错误分配，测试断言检测到行为不符合预期
- **失败位置：** 新增测试中检查共享别名行为的断言

**[Unknown]** 具体失败输出的详细内容未从日志中提取，无法确认每个失败测试的具体断言差异。

---

## 6. 测试是否验证了原始需求？

**[Judgment]** 部分验证。

**验证的部分：**
- ✅ 多字段共享别名时的值分配行为
- ✅ `validate_by_alias=False` 时的别名选择行为
- ✅ extra 字段的值形态保留

**未验证的部分：**
- ❓ 没有独立 Issue 定义"正确行为"，测试断言本身就是需求定义
- ❓ 无法确认修复是否覆盖了所有相关的边界情况（如嵌套模型、默认值、null 值）

**[Unknown]** 是否存在其他未被测试覆盖的 AliasChoices 行为。

---

## 7. 没有证据支持的主张

| 主张 | 证据状态 |
|------|----------|
| "修复了 Form Model 的 AliasChoices 提取" | ✅ 有代码变更和测试支持 |
| "旧代码存在 bug" | ⚠️ 有测试失败支持，但无独立 Issue 记录 bug 的具体表现 |
| "修复不影响其他行为" | ⚠️ Head 测试通过支持，但完整测试矩阵的具体结果未核验 |
| "AI 辅助了代码编写" | ✅ PR 正文有 CodSpeed 报告，分支名含 `codex/`，但无明确 AI 披露声明 |

---

## 8. 证据分级总结

| 项目 | 分级 |
|------|------|
| 代码变更内容 | **Fact**（diff 可审查） |
| 基线失败 9 项 | **Fact**（日志可查） |
| 失败性质为 AssertionError | **Judgment**（基于 09 描述，未直接查看日志） |
| 测试验证了修复行为 | **Judgment**（测试覆盖共享别名场景，但需求无独立定义） |
| AI 参与程度 | **Unknown**（无明确披露） |
