# NOOS ENTERPRISE

[在线研究档案（GitHub Pages）](https://tinnery.github.io/noos-enterprise/) · [GitHub 仓库](https://github.com/Tinnery/noos-enterprise)

> *Explore. Discover. Create.*
> 
> *To boldly go where no one has gone before.*

**Noos Enterprise** 是一艘驶向未知领域的星际探索飞船。

在 AI 让软件开发成本急剧下降的时代，我们不是在寻找更多的应用创意，而是在探索：**什么产品仍然值得存在？什么产品能真正改善用户生活，给社会创造长期价值？**

## 核心使命

这不是一个实验室，不是一个孵化器，不是一个点子工厂。

这是一次持续探索任务：
- **发现**被忽视的真实问题
- **验证**哪些需求值得被满足
- **构建**可能改变用户生活的产品原型
- **检验**我们的假设是否成立

Agent 不是等待指令的工具，而是能够自主探索、调查、构建和验证的船员。

## 核心问题

> 哪些需求过去因为成本太高而无人服务，现在终于可以被满足了？
> 
> 哪些产品即使 AI 能写出代码，也仍然需要长期的专业知识、数据、信任和运营？
> AI 产业自身的模型、推理、数据、Agent、评估、安全和开发工具链，还存在哪些值得深入解决的工程问题？

## 当前探索任务

### Exploration 0001: AI 时代软件价值的初步研究

**状态**：进行中

**研究问题**：
- AI 写代码的成本下降后，软件的竞争优势从哪里来？
- 哪些产品形态可能取代传统 SaaS？
- 消费者和企业对 AI 软件的信任如何建立？
- 哪些人群可能被技术进步遗漏？

**当前研究判断（尚待真实用户检验）**：
- 软件价值可能更多依赖工作流、专有数据、集成和信任，而不仅是代码
- Agent 可能改变传统 SaaS 的使用和收费方式
- Agent 的自主性增加了透明度、授权边界和问责机制的需求
- AI 使用在不同规模企业和人群间存在差异；宏观采用差异不能代替具体产品需求证据

**第一个研究案例**：花叔的三个项目
- **女娲.skill**：把人的思维方式变成 Agent 可调用的结构
- **Huashu Design**：把设计师的工作方法变成 Agent 可执行的工作流
- **达尔文.skill**：把"能力是否变好"变成可验证的循环

这三个项目提出了一个值得继续检验的产品形态假设：**软件的一种可能形态，是被 Agent 加载、组合、执行和持续改进的知识资产。** 目前这只是基于公开案例形成的推断，尚未由真实用户使用、专业任务质量或付费行为验证。

[查看完整探索文档](explorations/0001-ai-era-software-value/README.md)  
[查看软件产业分类图谱](explorations/0001-ai-era-software-value/frameworks/software-landscape-taxonomy.md)（含 AI & Model Systems 研究领域与 Security, Assurance & Trust 横切主题）  
[查看 AI Systems & Engineering 技术与问题地图](explorations/0001-ai-era-software-value/frameworks/ai-systems-industry.md)

### Exploration 0002: 信号检测与社区情报系统

**状态**：进行中

**研究问题**：
- 如何从技术变化和工程实践中发现值得深入研究的领域与细分分支？
- 如何从公开技术信号进一步找到具体工作问题，而不是把热度当成需求？
- 如何用历史结果和现实证据检验信号质量？

**研究方向**：
- **AI & Model Systems**：模型、推理、Agent、RAG、评估、安全与开发工具
- **软件工程基础分支**：程序分析、形式化方法、软件供应链、数据工程、分布式系统和可观测性
- **问题线索**：从维护、迁移、失败、人工补救和成本讨论中识别待验证问题
- **反馈验证**：技术信号只有经过具体任务、替代方案和经济后果调查，才能进入机会研究

**数据源状态**：
- **当前实现**：arXiv（论文元数据）→ GitHub（项目与 Star）→ Hacker News（帖子与评论）
- **规划中**：采购、招聘、市场和真实用户行为数据；尚未接入，且涉及用户研究的行为需先获得明确授权

**预期产出**：
- 信号检测系统原型（Python 脚本套件）
- 技术社区网络图谱
- 机会发现报告生成机制

[查看完整探索文档](explorations/0002-signal-detection-community-intelligence/README.md)

**AI 自身产业研究**：Exploration 0001 已新增 AI Systems & Engineering 独立研究地图，覆盖模型、推理、数据/上下文、Agent、评估、安全、开发者工具和专业系统。地图中的问题候选尚未被验证为产品需求。

## 公开规范

本仓库是 Public，但用户访谈资料必须脱敏，第三方资料需注明出处，公开发布前需获得授权。详见 [AGENTS.md](AGENTS.md#关于-public-仓库)。

## 项目结构

```
noos-enterprise/
├── README.md                    # 本文件
├── AGENTS.md                    # Agent 探索规则
├── VISION.md                    # 项目愿景和价值原则
├── LICENSE                      # Apache 2.0 许可证
├── dashboard/                   # repo 级探索看板前端（静态构建，GitHub Pages 部署）
├── explorations/                # 探索任务
│   ├── 0001-ai-era-software-value/
│   │   ├── README.md           # 第一个探索任务
│   │   ├── frameworks/         # 分类框架与分析工具
│   │   ├── hypotheses/         # 产品假设文档（待验证）
│   │   ├── deep-research/      # 深度研究文档（证伪框架、反事实基线、三角验证等）
│   │   └── validation/         # 假设验证工具包（用户访谈等）
│   └── 0002-signal-detection-community-intelligence/
│       ├── README.md           # 第二个探索任务
│       ├── frameworks/         # 信号检测框架
│       ├── scripts/            # 信号检测脚本套件
│       └── data/               # 数据存储（运行时生成）
├── skills/                      # Agent Skills 目录
│   ├── README.md               # Skills 说明
│   └── nuwa-skill/             # 女娲.skill（花叔）
└── templates/                   # 模板
    ├── hypothesis-template.md   # 机会假设模板
    └── experiment-template.md   # 实验记录模板
```

## 当前研究状态

现有五份产品假设尚未获得真实用户行为证据。下一阶段暂停继续扩写假设，优先观察目标用户过去实际完成任务的方式、耗时、替代方案和已发生的支出。任何访谈、招募、个人信息收集或付费活动，都必须先取得 AGENTS.md 要求的人类明确授权。

**在线浏览状态**：dashboard/ 是只读静态研究档案入口，通过 GitHub Actions 构建并发布到 GitHub Pages。页面提供项目规则、探索总览、产业分类图谱、产品假设和研究材料的导航；文档原文仍以 Git 仓库中的 Markdown 为准。该站点不提供后端 API，也不代表假设已获得现实验证。

## 探索日志

- **2026-11-09**：仓库初始化
- **2026-11-10**：启动 Exploration 0001；集成花叔的女娲 skill；许可证更新为 Apache 2.0
- **2026-11-10**：启动 Exploration 0002 - 信号检测与社区情报系统；设计四层架构（信号检测、社区分析、实践参与、反馈循环）；实现信号检测脚本套件（arXiv/GitHub/Hacker News 数据采集 + 四种弱信号检测算法）
- **2026-11-10**：分类图谱引入 Security, Assurance & Trust 横切研究主题（七个可信基础方向 + 信任链；核实 NIST NICE 2.2.0 / OWASP ASVS 5.0.0 / ACSC Secure by Design 等引用）；完成检测器测试套件（13 项）并集成 CI
- **2026-11-10**：新增漏洞研究产业框架（产业关系、上报市场运行规则、合规边界、黑灰产经济作用）；图谱第 3 节拆分为漏洞研究产业与软件可信度产业双主题
- **2026-11-10**：新增 AI Systems & Engineering 独立产业与技术机会图谱；扩展 arXiv/GitHub 采集覆盖，增加配置测试，并明确技术信号与真实需求之间的证据边界

---

> "Software is a great method of doing things, but it's not a great reason for doing them."
> 
> — Seth Godin

我们探索的不是技术能做什么，而是人类需要什么。
