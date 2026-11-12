# C2 — FastAPI #16559：命名 JSON Body 参数的 AliasChoices

**研究用途：** 基线行为失败案例  
**状态：** 证据重建完成

---

## 0. 版本标识

| 字段 | 值 |
|------|-----|
| PR | [#16559](https://github.com/fastapi/fastapi/pull/16559) |
| 标题 | 🐛 Fix `AliasChoices` for named JSON body parameters |
| 作者 | tiangolo |
| Base SHA | `37f916101f36c4ed4faee1004d07a818c1330d63` |
| Head SHA | `6b1599a09f3ecb1a7fb90a37ed5d8a0d2763c212` |
| Merge SHA | `2d1851f35da7025273b51fc3aa3deb88839a6a33` |
| 合并日期 | 2026-10-20 |
| 分支 | `codex/body-alias-choices` → `master` |

---

## 1. 原始需求

**[Judgment]** 无关联 Issue，无独立验收条件文档。

需求隐含在 PR 标题和代码变更中：修复命名 JSON Body 参数对 `AliasChoices` 的处理。从 diff 推断，问题是旧代码只使用 `get_validation_alias(field)` 获取单个别名，不支持 `AliasChoices` 的多别名选择逻辑。

**[Unknown]** 无法确认具体的用户报告场景或 bug 触发条件。

---

## 2. 生产代码变更

**文件：** `fastapi/dependencies/utils.py`（`request_body_to_args` 函数）

**[Fact]** 核心修改：

```python
# 旧代码
loc = ("body", get_validation_alias(field))
value = body_to_process.get(get_validation_alias(field), Undefined)

# 新代码
if isinstance(received_body, FormData):
    aliases = [get_validation_alias(field)]
else:
    aliases = [alias for alias, _ in _get_param_aliases(field)]
loc = ("body", aliases[0])
# ...
try:
    for alias in aliases:
        value = body_to_process.get(alias, Undefined)
        if value is not Undefined:
            loc = ("body", alias)
            break
```

**行为变化：**
1. 对非 FormData（JSON body），遍历 `AliasChoices` 中的所有别名，找到第一个有值的别名
2. 错误位置（`loc`）使用实际选中的别名，而非固定的第一个别名
3. FormData 仍使用预提取的规范别名（由 `_extract_form_items` 决定）

---

## 3. 测试代码变更

**文件：**
- `tests/test_body_alias_choices.py`（**新增**，392 行）
- `tests/test_request_params/test_file/test_nullable_and_defaults.py`（部分修改）

**[Fact]** 新增测试文件覆盖以下场景：

| 测试函数 | 验证行为 |
|----------|----------|
| `test_embedded_body_alias_choices` | 嵌入 body 参数的别名选择 |
| `test_invalid_choice_uses_selected_alias` | 无效值时使用选中别名的错误位置 |
| `test_required_body_missing_uses_first_alias` | 缺失字段时使用第一个别名 |
| `test_multiple_body_params_alias_choices` | 多个 body 参数的别名选择 |
| `test_null_and_default_values` | null 值和默认值处理 |
| `test_list_body_alias_choices` | 列表类型 body 的别名选择 |
| `test_nested_model_errors` | 嵌套模型的错误位置 |
| `test_openapi_schema` | OpenAPI schema 使用选中别名 |

测试使用 `inline_snapshot` 验证 OpenAPI schema 输出。

---

## 4. Base 和 Head 执行结果

### Base（regression-test Job）

**[Fact]** [Job 日志](https://github.com/fastapi/fastapi/actions/runs/39509723184/job/118927451731)

```
26 failed, 37 passed, 3 skipped, 1.15s
```

**[Judgment]** 26 项失败集中在新增的 `test_body_alias_choices.py` 中。失败性质为 **AssertionError**——旧代码不支持多别名遍历，导致：
- 无法从第二、第三别名获取值
- 错误位置使用错误的别名

### Head（test 矩阵）

**[Fact]** PR 版本测试矩阵成功。

---

## 5. 测试失败性质

**[Judgment]**

- **失败类型：** AssertionError
- **失败原因：** 旧代码 `body_to_process.get(get_validation_alias(field), Undefined)` 只查询第一个别名，当 JSON body 使用第二或第三别名时返回 `Undefined`
- **失败规模：** 26 项，覆盖几乎所有新增测试

**[Unknown]** 具体失败输出的详细内容未从日志中提取。

---

## 6. 测试是否验证了原始需求？

**[Judgment]** 部分验证。

**验证的部分：**
- ✅ JSON body 参数的多别名选择行为
- ✅ 错误位置使用实际选中的别名
- ✅ 嵌入 body、多参数、列表类型等变体
- ✅ OpenAPI schema 反映选中别名

**未验证的部分：**
- ❓ 没有独立 Issue 定义"正确行为"
- ❓ 测试与生产代码同源（PR 作者同时编写）
- ❓ 无法确认是否存在未被覆盖的边界情况

---

## 7. 没有证据支持的主张

| 主张 | 证据状态 |
|------|----------|
| "修复了 JSON body 的 AliasChoices" | ✅ 有代码变更和 26 项基线失败支持 |
| "旧代码不支持多别名" | ✅ diff 可直接验证 |
| "修复不影响现有行为" | ⚠️ Head 测试通过支持 |
| "AI 辅助了代码编写" | ⚠️ 分支名含 `codex/`，但 PR 正文无明确 AI 披露 |

---

## 8. 证据分级总结

| 项目 | 分级 |
|------|------|
| 代码变更内容 | **Fact**（diff 可审查） |
| 基线失败 26 项 | **Fact**（日志可查） |
| 失败性质为 AssertionError | **Judgment**（基于 09 描述和 diff 推断） |
| 测试验证了修复行为 | **Judgment**（测试覆盖多别名场景，但需求无独立定义） |
| AI 参与程度 | **Unknown**（无明确披露） |
