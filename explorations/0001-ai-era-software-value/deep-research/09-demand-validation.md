# 需求验证研究（Demand Validation for AI Agents）

**所属探索**：Exploration 0001 — AI 时代软件价值的初步研究  
**阶段**：阶段 1 - 发现与理解  
**创建日期**：2026-11-10  
**最后更新**：2026-11-10  
**本文档目的**：将 `demand-fulfillment-methodology.md` 的方法论适配到 AI Agent 场景，提供可直接使用的研究工具。

**前置依赖**：
- `frameworks/demand-fulfillment-methodology.md`（方法论基础）
- `deep-research/06-stakeholder-perspectives.md`（利益相关者假设）
- `frameworks/software-landscape-taxonomy.md`（软件产业分类图谱）

---

## 0. 本文档在研究体系中的位置

```
demand-fulfillment-methodology.md（方法论基础）
    ↓ 适配
09-demand-validation.md（本文档：AI Agent 场景工具包）
    ↓ 应用
06-stakeholder-perspectives.md（HYP-001~005 验证）
```

本文档不重复方法论的理论基础，只提供**可直接使用的研究工具**。

---

## 1. AI Agent 的 Job Map 模板

### 1.1 通用 Job Map（适用于所有 AI Agent 场景）

| 步骤 | 定义 | AI Agent 场景的适配 | 典型失败模式 |
|------|------|-------------------|------------|
| **1. Define** | 定义目标 | 用户向 Agent 表达意图 | 意图模糊、Agent 误解 |
| **2. Locate** | 定位所需资源 | Agent 识别需要的数据/工具/API | 权限不足、数据不可达 |
| **3. Prepare** | 准备条件 | Agent 组装上下文、调用工具 | 上下文缺失、工具调用失败 |
| **4. Confirm** | 确认方向 | Agent 向用户确认理解 | 确认过多（烦扰）、确认过少（误解） |
| **5. Execute** | 执行任务 | Agent 完成任务 | 执行错误、质量不达标 |
| **6. Monitor** | 监控进展 | 用户验证 Agent 输出 | 用户无法判断输出质量 |
| **7. Modify** | 调整偏差 | 用户要求 Agent 修正 | 修正循环（Agent 反复出错） |
| **8. Conclude** | 完成并验证 | 用户接受结果 | 用户不确定是否该信任结果 |

### 1.2 具体场景 Job Map 示例

#### 场景 A：AI Agent 帮助预订餐厅

| 步骤 | 用户任务 | Agent 任务 | 失败风险 |
|------|---------|-----------|---------|
| Define | "我想今晚吃日料" | 解析意图：时间=今晚、菜系=日料 | 未捕捉隐含约束（预算、距离） |
| Locate | — | 查询附近日料店、可用性 | API 不可用、数据过时 |
| Prepare | — | 筛选评分 > 4.0、有空位的店 | 筛选标准不透明 |
| Confirm | "推荐 Sushi X，19:00 有空位" | 确认用户接受 | 用户不知道如何评估推荐 |
| Execute | — | 调用预订 API | API 失败、预订被拒 |
| Monitor | 收到确认邮件 | 通知用户预订成功 | 用户未收到通知 |
| Modify | "改到 19:30" | 重新查询、修改预订 | 19:30 无空位，需要重新推荐 |
| Conclude | 前往餐厅 | — | 用户不确定推荐是否可靠 |

#### 场景 B：AI Agent 帮助编写代码

| 步骤 | 用户任务 | Agent 任务 | 失败风险 |
|------|---------|-----------|---------|
| Define | "写一个 Python 函数处理 CSV" | 解析意图：语言=Python、输入=CSV | 未捕捉隐含约束（编码、分隔符） |
| Locate | — | 识别需要的库（pandas?） | 库选择错误 |
| Prepare | — | 生成代码草稿 | 代码风格不匹配项目 |
| Confirm | "用 pandas 还是 csv 模块？" | 确认技术选择 | 用户不知道如何回答 |
| Execute | — | 生成完整代码 | 代码有 bug、边界条件未处理 |
| Monitor | 阅读代码、运行测试 | 提供解释 | 用户无法判断代码质量 |
| Modify | "这个函数没处理空值" | 修正代码 | 修正引入新 bug |
| Conclude | 提交代码 | — | 用户不确定是否该信任代码 |

### 1.3 Job Map 使用方法

**步骤 1**：选择目标场景（如"AI Agent 帮助预订餐厅"）

**步骤 2**：填写上表的每一列
- 用户任务：用户在这个步骤做什么？
- Agent 任务：Agent 在这个步骤做什么？
- 失败风险：什么可能出错？

**步骤 3**：识别高失败率步骤
- 哪些步骤最常出错？
- 哪些步骤出错后修复成本最高？

**步骤 4**：计算 Opportunity 分数
- 对每个步骤，让用户评分 Importance（1-10）和 Satisfaction（1-10）
- 计算 Opportunity = Importance × (Importance - Satisfaction)
- 高分步骤 = 高机会

---

## 2. Switch Interview Protocol（AI Agent 版本）

### 2.1 访谈目标

识别用户在什么情境下从传统软件切换到 AI Agent，以及为什么。

### 2.2 招募标准

- **必须**：在过去 6 个月内使用过 AI Agent（ChatGPT、Claude、Copilot、Cursor 等）
- **必须**：在此之前使用过传统软件完成同类任务
- **优先**：有明确的"切换时刻"（不是渐进式采用）

### 2.3 访谈大纲（45-60 分钟）

#### 阶段 1：切换时刻（20 分钟）

**开场**：
> "我想了解你第一次使用 [AI Agent] 时的经历。你能回忆一下那是什么时候吗？当时发生了什么？"

**核心问题**：
1. "在那一刻之前，你用什么工具完成这个任务？"
2. "那个工具哪里不够好？你能给我一个具体的例子吗？"
3. "是什么让你决定尝试 AI Agent？"
4. "有没有什么差点让你放弃？"

**追问**：
- "你能描述一下那个'不够好'的具体情境吗？你在哪里？当时有多急？"
- "你尝试过其他替代方案吗？为什么没选它们？"

#### 阶段 2：被动不满期（10 分钟）

**核心问题**：
1. "在决定尝试 AI Agent 之前，你忍受了多久？"
2. "什么让你意识到'不能再这样了'？"
3. "你有没有想过'也许就这样吧'？"

**追问**：
- "有没有一个具体的时刻让你觉得'受够了'？"

#### 阶段 3：主动寻找期（10 分钟）

**核心问题**：
1. "你考虑了哪些替代方案？"
2. "你为什么最终选择了这个 AI Agent？"
3. "有没有什么让你犹豫？"

**追问**：
- "你是怎么知道这个 AI Agent 的？"
- "你做了多少研究？还是直接试了？"

#### 阶段 4：决策时刻（10 分钟）

**核心问题**：
1. "是什么让你最终决定使用？"
2. "第一次使用时，有什么意外吗？"
3. "现在回头看，你觉得这个决定对吗？"

**追问**：
- "如果当时没有 AI Agent，你现在会用什么？"

### 2.4 数据记录模板

| 字段 | 内容 |
|------|------|
| 受访者编号 | P01, P02, ... |
| 访谈日期 | YYYY-MM-DD |
| AI Agent | ChatGPT / Claude / Copilot / Cursor / ... |
| 任务类型 | 预订 / 写作 / 编程 / 数据分析 / ... |
| 切换时刻 | [具体日期或时间段] |
| 旧方案 | [用户之前用的工具] |
| 触发条件 | [时间压力 / 社交需求 / 情绪状态 / ...] |
| 旧方案痛点 | [具体描述，不是抽象的"不够智能"] |
| 决策理由 | [为什么选择 AI Agent] |
| 犹豫点 | [什么差点让用户放弃] |
| 事后评估 | [用户认为这个决定对吗] |

### 2.5 分析方法

**步骤 1**：转录访谈，提取 switch events

**步骤 2**：聚类分析
- 哪些触发条件最常出现？
- 哪些旧方案痛点最常被提及？
- 哪些决策理由最常见？

**步骤 3**：识别情境模式
- 用户在什么情境下倾向于切换？
- 有没有"临界点"（如时间压力超过某个阈值）？

**步骤 4**：与 Job Map 对照
- 切换主要发生在 Job Map 的哪个步骤？
- 哪些步骤的失败率最高？

---

## 3. Opportunity Algorithm（AI Agent 版本）

### 3.1 问卷设计

**目标**：测量 AI Agent 各 job step 的 Importance 和 Satisfaction。

**问卷结构**：

**Part 1：任务识别**
1. "你使用 AI Agent 完成过哪些任务？"（开放题）
2. "请列出你最常使用的 3 个任务。"

**Part 2：Job Step 评分**（对每个任务）

对 Job Map 的 8 个步骤，让用户评分：

| 步骤 | 问题 | Importance（1-10） | Satisfaction（1-10） |
|------|------|-------------------|---------------------|
| Define | "准确表达你的意图有多重要？" | [ ] | "AI Agent 在理解你的意图上表现如何？" | [ ] |
| Locate | "找到所需数据/工具有多重要？" | [ ] | "AI Agent 在定位资源上表现如何？" | [ ] |
| Prepare | "准备上下文有多重要？" | [ ] | "AI Agent 在组装上下文上表现如何？" | [ ] |
| Confirm | "确认理解有多重要？" | [ ] | "AI Agent 在确认方向上表现如何？" | [ ] |
| Execute | "正确执行有多重要？" | [ ] | "AI Agent 在执行任务上表现如何？" | [ ] |
| Monitor | "验证输出有多重要？" | [ ] | "AI Agent 在提供可验证输出上表现如何？" | [ ] |
| Modify | "修正错误有多重要？" | [ ] | "AI Agent 在修正错误上表现如何？" | [ ] |
| Conclude | "信任结果有多重要？" | [ ] | "AI Agent 在让你信任结果上表现如何？" | [ ] |

**Part 3：开放题**
1. "AI Agent 在哪个步骤上最让你沮丧？"
2. "如果只能改进一个步骤，你会选哪个？为什么？"

### 3.2 Opportunity 计算

**公式**：
```
Opportunity_i = Importance_i × (Importance_i - Satisfaction_i)
```

**示例**：
- 步骤：Monitor（验证输出）
- Importance: 9
- Satisfaction: 4
- Opportunity: 9 × (9 - 4) = 45

**分类**：

| Opportunity 分数 | 市场状态 | 策略建议 |
|-----------------|---------|---------|
| > 50 | **Underserved** | 高机会：用户想要但得不到 |
| 20-50 | **Appropriately served** | 渐进式改进 |
| < 20 | **Overserved** | 不需要更好，需要更简单 |

### 3.3 样本量要求

- **最小样本**：50 份有效问卷
- **推荐样本**：100-200 份
- **分层抽样**：按任务类型（编程 / 写作 / 数据分析 / ...）分层

### 3.4 统计检验

**信度检验**：
- Cronbach's Alpha > 0.7（Importance 和 Satisfaction 量表内部一致性）

**效度检验**：
- 与"整体满意度"做相关分析，Pearson r > 0.5（收敛效度）
- 与"推荐意愿"做相关分析，Pearson r > 0.5（预测效度）

---

## 4. 验证标准与外部基准

### 4.1 可预测性验证

**假设**：基于 Job Map 和 Opportunity Algorithm 设计的 AI Agent 产品，市场成功率高于随机。

**验证方法**：
- 追踪 50+ 基于 Job Map 设计的 AI Agent 产品
- 计算 12 个月存活率
- 与行业基准比较

**基准**：
- AI Agent 新产品失败率约 60-70%（行业估计，待核实）
- 基于 Job Map 设计的产品失败率应低于 40%

**外部数据来源**：
- 待确定（需要找到 AI Agent 市场失败率的可靠数据）

### 4.2 可复现性验证

**假设**：不同研究者用同样的 Job Map 方法，对同一 AI Agent 得到相同的 job 列表。

**验证方法**：
- 两组独立研究者对同一 AI Agent 进行 Job Map
- 计算 Cohen's Kappa

**基准**：
- Cohen's Kappa > 0.7

**外部数据来源**：
- Ulwick (2005) 报告一致性 > 85%，但针对传统软件，AI Agent 场景待验证

### 4.3 收敛效度验证

**假设**：Opportunity Algorithm 的高分 job 与用户留存率正相关。

**验证方法**：
- 计算每个 job step 的 Opportunity 分数
- 与 AI Agent 产品的 30 天留存率做相关分析

**基准**：
- Pearson r > 0.5

**外部数据来源**：
- 产品分析工具（Amplitude, Mixpanel）的用户行为日志
- 需要与具体 AI Agent 产品合作获取数据

### 4.4 反事实检验

**假设**：如果移除 AI Agent 的高 Opportunity job step，用户会回到传统软件。

**验证方法**：
- A/B 测试：移除某个功能（如"确认理解"步骤），观察流失率
- 自然实验：AI Agent 产品下线某个功能后的用户行为

**基准**：
- > 70% 用户会回到传统软件

**外部数据来源**：
- 产品分析工具的行为日志
- 需要与具体 AI Agent 产品合作获取数据

---

## 5. 与 HYP-001~005 的连接

### 5.1 HYP-001（AI 自动化助手）

**Job Map 应用**：
- Define: 用户表达任务意图
- Execute: Agent 自动完成任务
- Monitor: 用户验证输出

**Opportunity 预测**：
- Monitor 步骤可能是高 Opportunity（用户不确定是否该信任 Agent 输出）

**验证方法**：
- Switch Interview：用户在什么情境下从手动操作切换到 AI 自动化？
- Opportunity Algorithm：Monitor 步骤的 Importance 和 Satisfaction 评分

### 5.2 HYP-002（工作流集成平台）

**Job Map 应用**：
- Locate: Agent 识别需要的工具和数据
- Prepare: Agent 组装上下文

**Opportunity 预测**：
- Locate 步骤可能是高 Opportunity（Agent 找不到需要的工具）

**验证方法**：
- Switch Interview：用户在什么情境下从手动集成切换到 AI 集成？
- Opportunity Algorithm：Locate 步骤的 Importance 和 Satisfaction 评分

### 5.3 HYP-003（小型组织数字化工具）

**Job Map 应用**：
- Define: 用户表达业务需求
- Execute: Agent 生成解决方案

**Opportunity 预测**：
- Define 步骤可能是高 Opportunity（用户不知道如何表达需求）

**验证方法**：
- Switch Interview：小型组织在什么情境下从通用工具切换到定制工具？
- Opportunity Algorithm：Define 步骤的 Importance 和 Satisfaction 评分

### 5.4 HYP-004（个人生活管理）

**Job Map 应用**：
- Locate: Agent 识别个人数据（日程、财务、健康）
- Monitor: 用户验证 Agent 建议

**Opportunity 预测**：
- Monitor 步骤可能是高 Opportunity（用户不确定是否该信任 Agent 建议）

**验证方法**：
- Switch Interview：个人在什么情境下从手动管理切换到 AI 管理？
- Opportunity Algorithm：Monitor 步骤的 Importance 和 Satisfaction 评分

### 5.5 HYP-005（无障碍与包容性工具）

**Job Map 应用**：
- Define: 用户表达无障碍需求
- Execute: Agent 生成无障碍解决方案

**Opportunity 预测**：
- Define 步骤可能是高 Opportunity（用户不知道如何表达无障碍需求）

**验证方法**：
- Switch Interview：残障用户在什么情境下从通用工具切换到无障碍工具？
- Opportunity Algorithm：Define 步骤的 Importance 和 Satisfaction 评分

---

## 5.5 个人工程师约束下的验证路径

### 约束前提

本 repo 的起步约束是**只有一个工程师**（详见 `AGENTS.md` "起步约束：个人工程师"）。这意味着：
- 无法招募 50+ 样本进行大规模问卷
- 无法支付招募费或田野调研费
- 验证路径 = 自我观察 + 同类人访谈（5-10 人）

### 样本量调整

| 标准方法 | 个人工程师版本 | 保真度 |
|---------|--------------|--------|
| 50-100 份问卷 | 5-10 人深度访谈 + 自我观察 | 中等：模式识别有效，统计推断受限 |
| 分层抽样 | 选择与自己相似的工程师（同类用户） | 中等：结论适用于"同类工程师"，不一定适用于其他群体 |
| Cronbach's Alpha > 0.7 | 模式识别（重复出现的痛点 = 强信号） | 中等：可识别高机会需求，无法精确排序 |

### 个人工程师的验证策略

```
第一层：自我观察（最高优先级）
├── 记录自己的 Switch Events（何时从旧方案切换到 AI Agent）
├── 识别自己的 Compensating Behaviors（没有 AI Agent 时如何凑合）
├── 评估自己的 Abandonment Points（在哪个步骤放弃使用 AI Agent）
└── 用自己的行为数据填充 Job Map

第二层：同行深度访谈（5-10 人）
├── 选择标准：与自己相似的工程师（同类用户）
├── 访谈方式：Switch Interview 简化版（聚焦关键事件，30 分钟）
├── 分析方法：模式识别（重复出现的痛点 = 强信号）
└── 验证标准：>60% 的受访者报告相同痛点 = 可行动信号

第三层：公开数据交叉验证
├── GitHub Issues / Discussions（开发者抱怨什么？）
├── Stack Overflow 问题（哪些任务最难？）
├── Reddit / Hacker News 讨论（AI Agent 的痛点是什么？）
└── 竞品用户评论（用户为什么放弃某个 AI Agent？）
```

### 个人工程师可行性筛选

在应用本文档的研究工具之前，先用以下问题筛选：

| 问题 | 如果答案 | 行动 |
|------|---------|------|
| 我自己是目标用户吗？ | 是 | ✅ 可以推进，自我观察是第一手数据 |
| 我能在一个周末做出 MVP 吗？ | 能 | ✅ 可以推进，快速验证 |
| 验证需要大规模招募吗？ | 需要 | ❌ 暂缓，寻找替代验证路径 |
| 验证需要进入特定社区吗？ | 需要 | ❌ 暂缓，或寻找公开数据替代 |

### HYP-001~005 的个人工程师可行性评估

| 假设 | 个人工程师可行性 | 理由 |
|------|----------------|------|
| HYP-001（AI 自动化助手） | ✅ 可行 | 工程师自己就是用户，可以自我观察 |
| HYP-002（工作流集成平台） | ✅ 可行 | 工程师自己的开发工作流是观察对象 |
| HYP-003（小型组织数字化工具） | ⚠️ 部分可行 | 工程师可以作为"小型组织"的代表，但需要同行验证 |
| HYP-004（个人生活管理） | ✅ 可行 | 工程师自己的生活管理是观察对象 |
| HYP-005（无障碍与包容性工具） | ❌ 不可行 | 除非工程师本身是残障人士，否则无法自我观察 |

---

## 6. 研究诚实性声明

### 6.1 已核实的研究基础

本文档引用的方法论基础已在 `demand-fulfillment-methodology.md` 第 7 节核实。

### 6.2 待验证的推论（Agent-generated）

以下推论基于方法论框架，但**尚未在本项目中验证**：

- **推论 1**：AI Agent 的 Monitor 步骤是高 Opportunity（用户不确定是否该信任 Agent 输出）
- **推论 2**：AI Agent 的 Locate 步骤是高 Opportunity（Agent 找不到需要的工具）
- **推论 3**：AI Agent 的 Define 步骤是高 Opportunity（用户不知道如何表达需求）

**验证方法**：必须通过 Switch Interview Protocol 和 Opportunity Algorithm 收集实证数据。

### 6.3 方法论边界

- **样本偏差**：Switch Interview 依赖用户回忆，可能存在回忆偏差
- **社会期望偏差**：用户可能夸大 AI Agent 的使用频率或效果
- **情境变化**：AI Agent 技术快速迭代，2026 年的数据可能在 2027 年过时

---

## 7. 下一步行动

1. **获得人类授权**：联系真实用户进行 Switch Interview（需要 AGENTS.md 授权）
2. **设计问卷**：基于 Part 2 的 Job Step 评分模板，设计在线问卷
3. **收集数据**：目标 100 份有效问卷 + 20 份 Switch Interview
4. **分析数据**：计算 Opportunity 分数，识别高 Opportunity 步骤
5. **验证推论**：检验推论 1-3 是否成立
6. **更新 HYP-001~005**：基于实证数据更新假设文档

---

**文档版本**：1.0  
**作者**：Noos Enterprise Agent  
**审核状态**：待人类审核
