# 09 — 代码变更可信验证：FastAPI 公开 PR 试点

**研究状态：** Pilot 完成；问题假设需要收窄，尚未形成产品结论  
**研究日期：** 2026-11-10  
**研究领域：** AI-assisted Software Change Assurance  
**技术分支：** Regression Testing、Test Effectiveness、CI Evidence  
**问题 / Job：** 程序员怎样判断一次代码变更已有足够且可信的验证证据？

---

## 1. 本轮要回答的问题

此前的产品假设是：程序员使用 AI 修改代码后，需要一种低成本方式，判断变更是否满足需求、是否引入回归，以及测试是否真正验证了变更。

本轮不预设市场存在空白，而是先检查成熟开源项目是否已经解决了其中最基础的一环：

> 新增或修改的回归测试，能否在未包含修复的基线版本上失败，并在包含修复的版本上通过？

如果成熟项目已经稳定解决这一问题，那么“自动重跑测试”或“给 PR 生成测试报告”本身就不构成足够有力的产品差异。

本轮只使用公开 GitHub 仓库、Pull Request、代码差异和 Actions 日志。没有联系作者、访谈用户、收集个人数据或产生付费。

## 2. 样本选择与限制

选择 FastAPI 在 2026-10-20 至 2026-10-21 期间围绕 Pydantic 的 AliasChoices 行为提交的一组已合并修复 PR。

纳入条件：

1. PR 已合并，代码差异和 CI 记录公开可查。
2. PR 正文明确披露使用 AI 辅助，并说明人工审阅。
3. 修复涉及运行时行为，且 PR 同时修改或新增测试。
4. 能取得 base SHA、head SHA、文件差异和 Actions 记录。

这是一组**目的性案例样本**，不是随机样本，也不是独立程序员总体的代表性样本。五个 PR 属于同一个项目、同一功能问题簇，提交者均为 FastAPI 项目维护者 tiangolo；不能把五个 PR 当成五个独立开发者，更不能据此估计整个行业的发生率。

AI 来源来自 PR 作者的自我披露：使用 Codex、gpt-6-astra，并由作者人工审阅。该披露能够证明作者公开作出了此项声明，不能独立证明 AI 参与了哪些具体代码行，也不能客观衡量人工审阅深度。

## 3. 样本清单

| PR | 修复内容 | 文件变化 | PR 正文的 AI 披露 | Actions 结果 |
|---|---|---:|---|---|
| [#16555](https://github.com/fastapi/fastapi/pull/16555) | Query、Header、Cookie 的 AliasChoices | 5 个文件，+1191 / -42 | Codex 辅助、人工审阅 | Test 检查成功；基线重放日志出现 snapshot 交互异常，未计作明确行为红灯 |
| [#16557](https://github.com/fastapi/fastapi/pull/16557) | Form Model 的 AliasChoices 提取 | 4 个文件，+141 / -23 | Codex 辅助、人工审阅 | Test 检查成功；基线重放 9 项失败 |
| [#16559](https://github.com/fastapi/fastapi/pull/16559) | 命名 JSON Body 参数的 AliasChoices | 3 个文件，+422 / -2 | Codex 辅助、人工审阅 | Test 检查成功；基线重放 26 项失败 |
| [#16560](https://github.com/fastapi/fastapi/pull/16560) | Path 参数的 AliasChoices | 3 个文件，+304 / -4 | Codex 辅助、人工审阅 | Test 检查成功；基线重放日志出现 snapshot 交互异常，未计作明确行为红灯 |
| [#16564](https://github.com/fastapi/fastapi/pull/16564) | Form 与 File 的验证错误位置 | 3 个文件，+216 / -27 | Codex 辅助、人工审阅 | Test 检查成功；基线重放 6 项失败 |

### 原始版本标识

| PR | Base SHA | Head SHA | Merge SHA |
|---|---|---|---|
| #16555 | 44cc7420b798b70b406516f5f0abf039f99edbe3 | b6c0e4e43362a1e9b5a25d1b8ced3eb681d251e8 | dfb3b91b7c6102cddde6e2cb1422d0faaa273be5 |
| #16557 | e08d28df250b4e810862723166c83d2919944ed1 | 5bcf22c97909f35bf0ee8dda0b655e7113501473 | 75f3a149359bfd39665aaf81dc223fb6fc28da23 |
| #16559 | 37f916101f36c4ed4faee1004d07a818c1330d63 | 6b1599a09f3ecb1a7fb90a37ed5d8a0d2763c212 | 2d1851f35da7025273b51fc3aa3deb88839a6a33 |
| #16560 | b2ce629ace6bdd152d577e5f5e256a079ac1e4fd | 3f9495882ebf29c25bb1c014d7e7cac4a9570669 | 89317c7003d0cca25e56b5acbfc11aa2c1810e08 |
| #16564 | 3b39c91cd1f221042313634db901c64615bb4fb5 | 3d92fbb407ca10c1e58f44ef13c53888a94aaaf8 | 1282e9a9f1ac0647cb2031c6dd9c1d5631ade4d4 |

## 4. 最有价值的发现：FastAPI 已经实现了基线重放

FastAPI 在该时间点的工作流文件：

[.github/workflows/test.yml（固定到 PR #16564 的 head SHA）](https://github.com/fastapi/fastapi/blob/3d92fbb407ca10c1e58f44ef13c53888a94aaaf8/.github/workflows/test.yml)

其中存在 regression-test Job，主要步骤为：

1. 取出 PR 版本。
2. 用 Git diff 找到 tests 目录下新增或修改、文件名符合 test_*.py 的测试文件。
3. 单独保存 tests 目录的差异补丁。
4. 检出 PR 的 base SHA。
5. 将测试补丁应用到 base 代码上。
6. 在 base 代码上运行这些变更测试。
7. 如果 pytest 返回 0，发出警告；如果返回非零，则输出“changed tests fail on base as expected”。

PR 正常测试矩阵则在 PR 版本上运行完整测试套件。这构成了一个基本的 red-on-base / green-on-head 对照：

- base 运行新测试，检查修复前的代码是否暴露预期问题；
- PR 版本运行完整测试，检查补丁版本是否通过项目测试。

因此，最初的产品设想需要修正：**对于有成熟 CI 的项目，简单地在旧版本上重跑新测试并非新能力。**

### 4.1 可明确复核的基线失败

#### PR #16564

[Regression Job 日志](https://github.com/fastapi/fastapi/actions/runs/39565876493/job/119107903012)

原始日志显示，在 base 版本上运行变更测试：

- 6 failed
- 179 passed
- 3 skipped
- 1.77 秒

六项失败集中在本次新增或修改的 File / Form AliasChoices 测试中。日志中的差异不是笼统的“测试失败”，而是旧代码产生的验证错误位置与测试期望不一致，例如旧代码返回 legacy 字段名，而测试要求返回实际选中的 alias。

同一 Actions Run 的 PR 版本测试矩阵成功。一个 Ubuntu / Python 3.13 coverage Job 的日志显示：

- 4414 passed
- 20 skipped
- 5 xfailed
- 110.37 秒

[PR #16564 完整测试 Job](https://github.com/fastapi/fastapi/actions/runs/39565876493/job/119107976376)

这一案例明确展示了：新增行为测试在旧版本失败，补丁版本的项目测试通过。

#### PR #16559

[Regression Job 日志](https://github.com/fastapi/fastapi/actions/runs/39509723184/job/118927451731)

基线重放得到：

- 26 failed
- 37 passed
- 3 skipped
- 1.15 秒

新增测试覆盖 embedded body、多个 alias 的选择顺序、无效值、缺失字段、显式 null、默认值、列表错误位置、嵌套模型错误和 OpenAPI schema 等行为。失败输出中可看到旧代码对某些输入返回错误状态码或错误数据，与测试规定的行为不一致。

#### PR #16557

[Regression Job 日志](https://github.com/fastapi/fastapi/actions/runs/39506409538/job/118916329214)

基线重放得到：

- 9 failed
- 211 passed
- 3 skipped
- 3.04 秒

失败涉及 Form Model 对别名选择、重复字段和 extra 字段形态的处理。

### 4.2 两个结果不应被过度解读

PR #16560 和 #16555 的基线重放日志以 inline snapshot 的交互提示结束，出现了 “Do you want to fix these snapshots?” 和 EOFError。对应 Job 最终仍为 success，但日志未给出足够稳定、可直接归类的 pytest 失败摘要。

本研究不把这两次记录算作明确的行为回归失败。它们被标记为**日志诊断不充分**。

这两个样本反而暴露了一个测量问题：CI Job 的 success/failure 不能替代对测试输出和失败类型的检查。

## 5. 现有机制的边界

检查工作流实现后，发现至少四个值得继续研究的边界。

### 5.1 以文件为单位，而不是以测试用例为单位

工作流选择的是新增或修改的 test_*.py 文件，然后把整个文件交给 pytest。

它没有在这段工作流中逐个区分：

- 哪些测试是本次新增的；
- 哪些测试是本次修改的；
- 哪些测试是文件中原本就存在的；
- 哪些失败由本次行为变更导致。

这不意味着样本中的红灯是错误的；#16564、#16559、#16557 的失败都能从测试输出中找到合理的行为差异。但对于自动判定系统，文件级选择不是精确的测试级归因。

### 5.2 任意非零退出码都会被当成预期红灯

工作流执行 pytest 时暂时关闭 shell 的自动失败处理，获取退出码后只判断：

- 退出码为 0：警告，base 已经通过；
- 退出码非 0：输出 base 按预期失败。

它没有在该步骤中进一步分类 AssertionError、collection error、依赖安装失败、环境错误、超时、崩溃或交互式工具异常。

因此，非零退出码只能证明 pytest 命令没有以成功状态结束，不能单独证明“新增回归测试准确捕获了本次修复”。

PR #16560 / #16555 的 snapshot 交互日志说明这种区分并非纸面问题。

### 5.3 没有新增或修改测试文件时，回归证明不适用

该 Job 只筛选 tests 目录中新增或修改的 test_*.py 文件。如果没有找到，步骤输出 “No added or modified test files; regression proof is not applicable.”

这说明该机制验证的是“变更测试能否在基线上失败”，不是“每一项生产代码变更是否都有对应测试”。

它不会自动回答：

- 这次生产代码修改是否应当新增测试；
- 没有测试是合理的，还是遗漏；
- 测试是否覆盖了变更的关键行为；
- 需求中的验收条件是否转化为了测试。

### 5.4 它不证明测试完整，也不证明代码绝对正确

该工作流没有在这组 PR 中提供 Mutation Testing 结果，也没有建立需求句子到测试断言的系统追踪。完整测试套件通过只能证明该测试套件在当次环境和输入下通过，不能证明所有需求、边界和未来状态均正确。

这些是本研究可继续验证的边界，不应直接包装成 FastAPI 的缺陷或用户痛点。

## 6. 证据分层：目前可以说什么

| 观察 | 当前证据 | 可以支持的结论 | 不能支持的结论 |
|---|---|---|---|
| PR 使用 AI 辅助 | 五个 PR 正文均有 AI Disclaimer | 作者公开披露 Codex 辅助并人工审阅 | 无法验证 AI 具体贡献比例或审阅深度 |
| 基线重放机制存在 | 固定 SHA 的工作流源码 | FastAPI 有 changed-tests-on-base 检查 | 不能推断多数项目都有此机制 |
| 三个 PR 有明确基线行为失败 | #16564、#16559、#16557 原始日志 | 对应测试能在旧代码上暴露可见行为差异 | 不能证明所有测试都有效或需求完整 |
| 两个 PR 日志诊断不足 | #16560、#16555 的 snapshot prompt / EOFError | Job 状态需要结合日志解读 | 不能将其计作明确的 red-on-base 证据 |
| PR 版本测试成功 | Actions Test 检查记录 | 此次 PR 版本在所执行的测试矩阵中通过 | 不能证明没有生产回归或代码绝对正确 |
| 人工审阅 | PR 正文声明；GitHub Review API 未发现正式 Review 记录 | 作者声明进行了人工审阅 | 不能据此确认审阅过程、时间或质量 |
| 商业需求 | 本轮没有用户行为或付费数据 | 尚未取得商业需求证据 | 不能声称有市场、愿付费或产品机会成立 |

## 7. 本轮结论：收窄，而不是扩大产品假设

### 已被反证削弱的初始假设

> “程序员需要一个工具，帮他们在 base 版本上重跑 PR 新增测试，并生成是否回归的报告。”

这不是完全不存在的需求，但它已经是成熟 CI 工作流可以实现的基础能力。单纯包装成 CLI、GitHub Action 或报告界面，差异化不足。

### 值得继续检验的更窄假设

> “个人程序员缺少一种低成本方式，判断 PR 中的验证证据是否足以支持合并决定；现有 CI 虽能报告测试状态，却未必能清楚区分有效的行为回归证据、无关测试失败、执行异常、未测试变更和未覆盖的需求。”

可能研究的具体能力：

1. 把生产代码 Diff、需求/Issue 和测试 Diff 建立可审查的关联，而不是只按文件筛选。
2. 对 base 重放结果做失败分类和测试级归因，不把任意非零退出码算作有效证据。
3. 检查新增测试是否能在 base 失败、在 head 通过，并说明实际差异。
4. 标记没有测试变更的生产代码修改，但不自动判定为缺陷。
5. 在风险合适时加入 Mutation Testing 或 Property-based Testing，而不是对所有 PR 机械执行高成本检查。
6. 把“已验证、证据不足、未执行、执行异常”明确分开。

以上是下一轮研究方向，不是已经确定的产品规格。

## 8. 下一轮实证研究设计

### 研究问题

在不同规模、不同工程成熟度的公开软件仓库中，代码变更的验证证据到底有哪些常见缺口？这些缺口是否会给个人程序员带来可观察、重复且有成本的额外工作？

### 样本扩展

建议下一轮收集 30–50 个 PR，覆盖 5–10 个不同仓库，分层纳入：

- 生产代码和测试都改变的 PR；
- 生产代码改变、测试未改变的 PR；
- 测试改变但没有清晰需求/Issue 关联的 PR；
- 明确披露 AI 参与的 PR；
- AI 来源不明确的 PR（单独分层，不得标为 AI 生成）。

优先考虑个人维护者和小型项目，避免继续只研究大型成熟项目。

### 每个 PR 的原始记录

- 仓库、PR URL、采集日期；
- Base SHA、Head SHA、Merge SHA；
- PR 正文、关联 Issue、验收描述；
- Changed file list 与 patch；
- 测试文件新增/修改/删除情况；
- CI workflow 源码和固定版本；
- base 重放日志与 head 测试日志；
- 失败类型、失败测试标识和退出码；
- coverage / mutation / property-based 产物（若项目实际提供）；
- 后续 Bug、Revert、Hotfix（仅在公开资料可追溯时记录）。

不得把缺失数据填成“没有问题”。未知、未公开、未执行和不适用必须分别标记。

### 每个样本的人工判定字段

1. 是否有可明确识别的需求或行为描述？
2. 生产代码变化能否映射到需求？
3. 是否存在新增或修改的行为测试？
4. 测试在 base 上是否失败？
5. 失败是否来自与变更相关的断言？
6. 测试在 head 上是否通过？
7. 是否有执行错误、交互异常或环境噪声？
8. 有哪些行为仍然没有证据？
9. 复核这些证据需要多少人工时间？

至少对一部分样本进行双人独立判定，记录分歧及裁决理由，避免单个 Agent 的分类直接成为标签真值。

### 下一轮停止条件

若跨仓库样本显示：

- 绝大多数目标项目已有可靠的测试级归因与失败分类；
- 现有工具可以低成本覆盖这些缺口；
- 缺口很少出现，或人工复核成本很低；
- 个人开发者没有重复遇到该问题；

则应放弃“PR 可信验证工具”这一产品假设，保留研究结论。

若缺口稳定存在，也只能进入下一阶段的真实使用流程研究。联系开发者、用户访谈、招募或收集个人资料前，必须按 AGENTS.md 取得明确授权。

## 9. 决策

**决定：继续实证研究；暂不开发产品。**

理由：

- 已确认成熟开源项目中存在基线重放机制，初始产品切口过于基础。
- 已发现该机制在失败分类、测试级归因、无测试变更的解释、需求追踪方面存在可研究边界。
- 当前只有一个项目、一个功能问题簇、五个相关 PR，不足以估计问题普遍性。
- 没有个人程序员使用行为、时间成本、替代方案满意度或付费证据。

下一步不是搭建 SaaS，而是跨仓库扩大样本，并把日志中“Job 绿色”与“证据真实有效”分开测量。

---

## 10. 原始来源

### FastAPI Pull Requests

- [PR #16555](https://github.com/fastapi/fastapi/pull/16555)
- [PR #16557](https://github.com/fastapi/fastapi/pull/16557)
- [PR #16559](https://github.com/fastapi/fastapi/pull/16559)
- [PR #16560](https://github.com/fastapi/fastapi/pull/16560)
- [PR #16564](https://github.com/fastapi/fastapi/pull/16564)

### CI 工作流与原始执行记录

- [test.yml at PR #16564 head SHA](https://github.com/fastapi/fastapi/blob/3d92fbb407ca10c1e58f44ef13c53888a94aaaf8/.github/workflows/test.yml)
- [PR #16564 regression-test Job](https://github.com/fastapi/fastapi/actions/runs/39565876493/job/119107903012)
- [PR #16564 Ubuntu / Python 3.13 full test Job](https://github.com/fastapi/fastapi/actions/runs/39565876493/job/119107976376)
- [PR #16559 regression-test Job](https://github.com/fastapi/fastapi/actions/runs/395097232)
- [PR #16557 regression-test Job](https://github.com/fastapi/fastapi/actions/runs/395064097)

所有结论均限定于上述公开版本、工作流和日志。未来仓库版本变化后，必须重新固定 SHA 和采集记录。