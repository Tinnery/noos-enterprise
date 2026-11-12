# C5 — FastAPI #16560：Path 参数的 AliasChoices

**研究用途：** Snapshot 交互异常案例  
**状态：** 证据重建完成

---

## 0. 版本标识

| 字段 | 值 |
|------|-----|
| PR | [#16560](https://github.com/fastapi/fastapi/pull/16560) |
| 标题 | 🐛 Fix `AliasChoices` for path parameters |
| 作者 | tiangolo |
| Base SHA | `b2ce629ace6bdd152d577e5f5e256a079ac1e4fd` |
| Head SHA | `3f9495882ebf29c25bb1c014d7e7cac4a9570669` |
| Merge SHA | `89317c7003d0cca25e56b5acbfc11aa2c1810e08` |
| 合并日期 | 2026-10-21 |
| 分支 | `codex/path-alias-choices` → `master` |

---

## 1. 原始需求

**[Judgment]** 无关联 Issue，无独立验收条件文档。

需求隐含在 PR 标题中：修复 Path 参数对 `AliasChoices` 的处理。从 diff 推断，问题是 Path 参数的 `AliasChoices` 需要根据路由路径中的参数名来解析，而非简单遍历所有别名。

---

## 2. 生产代码变更

**文件：** `fastapi/dependencies/utils.py`（`analyze_param` 函数）

**[Fact]** 核心修改：

```python
# 新增逻辑
validation_alias = field_info.validation_alias
if (
    isinstance(field_info, params.Path)
    and isinstance(validation_alias, AliasChoices)
    and all(isinstance(choice, str) for choice in validation_alias.choices)
):
    for choice in cast(list[str], validation_alias.choices):
        if choice in path_param_names:
            # Resolve the route name for both validation and OpenAPI
            field_info = copy(field_info)
            field_info.validation_alias = choice
            break
```

**行为变化：**
1. 对 Path 参数，检查 `AliasChoices` 中哪个别名匹配路由路径中的参数名
2. 找到匹配后，将 `validation_alias` 替换为该单一别名（使用 `copy` 避免修改共享对象）
3. 这确保验证和 OpenAPI schema 使用正确的路径参数名

**[Judgment]** 这是一个特殊的解析逻辑——Path 参数的别名选择不是基于请求数据，而是基于路由定义。

---

## 3. 测试代码变更

**文件：**
- `tests/test_path_alias_choices.py`（**新增**，287 行）
- `tests/test_header_cookie_alias_choices.py`（修改 1 行：重命名测试函数）

**[Fact]** 新增测试文件覆盖以下场景：

| 测试函数 | 验证行为 |
|----------|----------|
| `test_dependency_alias_choices_follow_router_prefix` | Depends 中的 AliasChoices 跟随路由前缀 |
| `test_invalid_value_uses_route_parameter_name` | 无效值使用路由参数名作为错误位置 |
| `test_selected_alias_preserves_constraints` | 选中的别名保留验证约束（如 `ge=1`） |
| `test_individual_path_alias_choices` | 独立 Path 参数的别名选择 |
| `test_multiple_matching_choices_follow_declaration_order` | 多个匹配时按声明顺序 |
| `test_unmatched_choices_preserve_explicit_alias` | 无匹配时保留显式 alias |
| `test_alias_path_extraction_is_unchanged` | AliasPath 不受影响 |
| `test_websocket_dependency_uses_matching_alias` | WebSocket 依赖使用匹配别名 |
| `test_openapi` | OpenAPI schema 使用选中别名 |

测试使用 `inline_snapshot` 验证 OpenAPI schema 输出。

### 修改的测试

- `test_path_alias_choices_are_unchanged` → `test_unmatched_path_alias_choices_preserve_parameter_name`（重命名，更准确描述行为）

---

## 4. Base 和 Head 执行结果

### Base（regression-test Job）

**[Fact]** 日志未在 09 中详细记录。根据 09 的描述：

> 基线重放日志以 inline snapshot 的交互提示结束，出现了 "Do you want to fix these snapshots?" 和 EOFError。对应 Job 最终仍为 success。

**[Judgment]** 与 #16555 相同的情况——`inline_snapshot` 在非交互环境中触发 EOFError，不是明确的行为回归失败。

### Head（test 矩阵）

**[Fact]** PR 版本测试矩阵成功。

---

## 5. 测试失败性质

**[Judgment]**

- **失败类型：** EOFError（`inline_snapshot` 交互式提示）
- **失败原因：** 同 #16555
- **失败规模：** 未知

**关键问题：** 无法判断 Base 的 snapshot 差异是否由本次修复引起。

---

## 6. 测试是否验证了原始需求？

**[Judgment]** 部分验证。

**验证的部分：**
- ✅ Head 测试矩阵通过
- ✅ 测试覆盖了 Path 参数的特殊解析逻辑
- ✅ 测试覆盖了 Depends、WebSocket、OpenAPI 等场景

**未验证的部分：**
- ❓ Base 的 snapshot 差异性质不明
- ❓ 无法确认 Base 失败是否由本次修复引起

---

## 7. 没有证据支持的主张

| 主张 | 证据状态 |
|------|----------|
| "修复了 Path 参数的 AliasChoices" | ✅ 有代码变更支持 |
| "Base 上测试失败" | ❌ 日志诊断不充分 |
| "AI 辅助了代码编写" | ⚠️ 分支名含 `codex/`，但 PR 正文无明确 AI 披露 |

---

## 8. 证据分级总结

| 项目 | 分级 |
|------|------|
| 代码变更内容 | **Fact**（diff 可审查） |
| Base 日志含 snapshot 交互提示 | **Fact**（09 记录） |
| Base 失败性质为行为回归 | **Unknown** |
| Head 测试通过 | **Fact**（Actions 记录） |
| 测试验证了修复行为 | **Judgment** |
| AI 参与程度 | **Unknown** |

---

## 9. 方法论启示

与 #16555 相同。两个案例共同说明：**`inline_snapshot` 的交互提示在 CI 环境中是无效证据**，不能作为行为回归的判断依据。
