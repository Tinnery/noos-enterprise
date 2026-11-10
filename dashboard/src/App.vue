<script setup lang="ts">
type DocumentLink = {
  title: string
  description: string
  path: string
}

type DocumentGroup = {
  title: string
  description: string
  documents: DocumentLink[]
}

const repositoryUrl = 'https://github.com/Tinnery/noos-enterprise'

function sourceUrl(path: string): string {
  return `${repositoryUrl}/blob/main/${path}`
}

const projectDocuments: DocumentLink[] = [
  {
    title: 'README',
    description: '项目入口、当前探索和交付物索引',
    path: 'README.md',
  },
  {
    title: 'VISION',
    description: '项目愿景、价值判断与长期方向',
    path: 'VISION.md',
  },
  {
    title: 'AGENTS',
    description: 'Agent 工作规则、授权边界与证据标准',
    path: 'AGENTS.md',
  },
]

const explorationGroups: DocumentGroup[] = [
  {
    title: 'Exploration 0001 · AI 时代软件价值',
    description: '研究软件价值变化、可证伪产品假设、产业观察标签和验证方式。所有假设仍需现实证据检验。',
    documents: [
      { title: '探索总览', description: '研究问题、阶段记录与当前行动', path: 'explorations/0001-ai-era-software-value/README.md' },
      { title: '软件产业分类图谱', description: '十类产品功能标签 + AI & Model Systems 研究领域 + Security, Assurance & Trust 横切主题；不代表互斥市场或市场规模', path: 'explorations/0001-ai-era-software-value/frameworks/software-landscape-taxonomy.md' },
      { title: '漏洞研究产业框架', description: '漏洞市场参与者、上报规则、合规边界与黑灰产经济作用（研究框架，非行为指导）', path: 'explorations/0001-ai-era-software-value/frameworks/vulnerability-research-industry.md' },
      { title: 'AI Systems & Engineering', description: '模型、推理、数据、Agent、评估、安全与开发工具链的产业和问题地图', path: 'explorations/0001-ai-era-software-value/frameworks/ai-systems-industry.md' },
      { title: 'HYP-001 · 小企业 AI 工作流', description: '问题假设与待验证条件', path: 'explorations/0001-ai-era-software-value/hypotheses/HYP-001-small-business-ai-workflow.md' },
      { title: 'HYP-002 · Family OS', description: '家庭协调任务与待验证条件', path: 'explorations/0001-ai-era-software-value/hypotheses/HYP-002-family-os.md' },
      { title: 'HYP-003 · 农业 AI 助手', description: '农业任务与专业边界', path: 'explorations/0001-ai-era-software-value/hypotheses/HYP-003-agriculture-ai-assistant.md' },
      { title: 'HYP-004 · 老年人数字助手', description: '数字服务任务与授权边界', path: 'explorations/0001-ai-era-software-value/hypotheses/HYP-004-elderly-digital-assistant.md' },
      { title: 'HYP-005 · 蓝领技能助手', description: '维修知识支持与安全边界', path: 'explorations/0001-ai-era-software-value/hypotheses/HYP-005-blue-collar-ai-assistant.md' },
    ],
  },
  {
    title: 'Exploration 0001 · 研究与验证材料',
    description: '分析框架和验证工具包属于研究设计材料，不应被误读为真实用户研究结果。',
    documents: [
      { title: '可证伪框架', description: '各假设的证伪条件', path: 'explorations/0001-ai-era-software-value/deep-research/01-falsification-framework.md' },
      { title: '反事实基线', description: '与现有方案和不开发软件的情形比较', path: 'explorations/0001-ai-era-software-value/deep-research/02-counterfactual-baseline.md' },
      { title: '领先指标', description: '可能值得观察的先行指标', path: 'explorations/0001-ai-era-software-value/deep-research/03-leading-indicators.md' },
      { title: '分层时间预测', description: '预测框架，不等同于已验证里程碑', path: 'explorations/0001-ai-era-software-value/deep-research/04-time-layered-predictions.md' },
      { title: '替代弹性', description: '任务替代与工作流变化的分析框架', path: 'explorations/0001-ai-era-software-value/deep-research/05-substitution-elasticity.md' },
      { title: '利益相关者视角', description: '不同参与方的激励和约束', path: 'explorations/0001-ai-era-software-value/deep-research/06-stakeholder-perspectives.md' },
      { title: '证据升级路径', description: '证据采集与质量提升的研究设计', path: 'explorations/0001-ai-era-software-value/deep-research/07-evidence-upgrade-path.md' },
      { title: '三角验证框架', description: '多来源交叉检验方法', path: 'explorations/0001-ai-era-software-value/deep-research/08-triangulation-framework.md' },
      { title: '代码变更可信验证试点', description: 'FastAPI + pytest 公开 PR 对照；基线重放、结构性测试、失败归因和 CI 证据边界（Pilot，非市场结论）', path: 'explorations/0001-ai-era-software-value/deep-research/09-change-assurance-pilot.md' },
      { title: 'HYP-001 验证工具包', description: '小企业工作任务观察与验证计划', path: 'explorations/0001-ai-era-software-value/validation/hyp-001-toolkit.md' },
      { title: 'HYP-005 验证工具包', description: '维修场景研究与专业边界', path: 'explorations/0001-ai-era-software-value/validation/hyp-005-toolkit.md' },
      { title: 'Opportunity Brief 模板', description: '把技术信号转为具体角色、任务、当前替代方案、成本与反证', path: 'templates/opportunity-brief-template.md' },
    ],
  },
  {
    title: 'Exploration 0002 · 信号检测与社区情报',
    description: '跨 AI、软件工程与安全分支的公开技术信号采集；信号只是研究线索，不代表真实用户需求。',
    documents: [
      { title: '探索总览', description: '目标、方法框架和当前阶段', path: 'explorations/0002-signal-detection-community-intelligence/README.md' },
      { title: '信号检测框架', description: '信号类型、数据源与检测思路', path: 'explorations/0002-signal-detection-community-intelligence/frameworks/signal-detection-framework.md' },
      { title: '脚本使用说明', description: '当前采集和检测脚本入口', path: 'explorations/0002-signal-detection-community-intelligence/scripts/README.md' },
    ],
  },
]

const allDocumentCount = projectDocuments.length + explorationGroups.reduce(
  (total, group) => total + group.documents.length,
  0,
)
</script>

<template>
  <main class="site-shell">
    <header class="topbar">
      <a class="brand" href="#top" aria-label="Noos Enterprise 首页">
        <span class="brand-mark">N</span>
        <span>NOOS ENTERPRISE</span>
      </a>
      <a class="repo-link" :href="repositoryUrl" target="_blank" rel="noreferrer">
        GitHub Repository <span aria-hidden="true">↗</span>
      </a>
    </header>

    <section id="top" class="hero">
      <p class="eyebrow">AI RESEARCH AGENT · OPEN EXPLORATION</p>
      <h1>研究模型由 Agent 建立，<br /><span>由现实世界检验。</span></h1>
      <p class="hero-copy">
        Noos Enterprise 探索 AI 时代真正值得解决的软件问题。
        这里汇集研究方向、产品假设、产业观察框架与验证材料。
      </p>
      <div class="hero-meta">
        <span><i class="status-dot"></i> Git-native research</span>
        <span>只读静态站点 · 无后端服务</span>
        <span>{{ allDocumentCount }} 项文档入口</span>
      </div>
    </section>

    <section class="project-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">FOUNDATION</p>
          <h2>项目原则</h2>
        </div>
        <p>先明确规则，再阅读具体探索。</p>
      </div>
      <div class="project-grid">
        <a
          v-for="doc in projectDocuments"
          :key="doc.path"
          class="project-card"
          :href="sourceUrl(doc.path)"
          target="_blank"
          rel="noreferrer"
        >
          <span class="card-kicker">PROJECT DOCUMENT</span>
          <strong>{{ doc.title }}</strong>
          <span class="card-description">{{ doc.description }}</span>
          <span class="card-arrow">阅读原文 ↗</span>
        </a>
      </div>
    </section>

    <section class="explorations-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">EXPLORATIONS</p>
          <h2>研究档案</h2>
        </div>
        <p>按探索主题组织，而不是按技术组件组织。</p>
      </div>

      <article v-for="(group, index) in explorationGroups" :key="group.title" class="exploration-group">
        <div class="group-heading">
          <span class="group-number">{{ String(index + 1).padStart(2, '0') }}</span>
          <div>
            <h3>{{ group.title }}</h3>
            <p>{{ group.description }}</p>
          </div>
        </div>
        <div class="document-list">
          <a
            v-for="doc in group.documents"
            :key="doc.path"
            class="document-row"
            :href="sourceUrl(doc.path)"
            target="_blank"
            rel="noreferrer"
          >
            <span class="document-copy">
              <strong>{{ doc.title }}</strong>
              <span>{{ doc.description }}</span>
            </span>
            <span class="document-arrow" aria-hidden="true">↗</span>
          </a>
        </div>
      </article>
    </section>

    <footer class="footer">
      <div>
        <strong>NOOS ENTERPRISE</strong>
        <p>研究内容与版本历史以 Git 仓库为准。此页面只提供公开资料导航，不代表任何假设已经得到现实验证。</p>
      </div>
      <a :href="repositoryUrl" target="_blank" rel="noreferrer">查看仓库 ↗</a>
    </footer>
  </main>
</template>

<style>
:root {
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #e8eaf0;
  background: #101318;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
}
* { box-sizing: border-box; }
html { min-width: 320px; scroll-behavior: smooth; }
body { margin: 0; min-width: 320px; min-height: 100vh; }
a { color: inherit; text-decoration: none; }
.site-shell { max-width: 1160px; margin: 0 auto; padding: 0 32px; }
.topbar { height: 76px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #29303a; }
.brand { display: inline-flex; gap: 11px; align-items: center; font-size: 12px; font-weight: 750; letter-spacing: .16em; }
.brand-mark { display: grid; width: 28px; height: 28px; place-items: center; border: 1px solid #7586a2; border-radius: 8px; color: #b6c8e8; font-size: 14px; }
.repo-link,.footer>a { color: #b8c9e5; font-size: 12px; }
.hero { padding: 100px 0 86px; border-bottom: 1px solid #29303a; }
.eyebrow { margin: 0 0 16px; color: #8fa6c8; font-size: 10px; font-weight: 750; letter-spacing: .2em; }
.hero h1 { max-width: 850px; margin: 0; font-size: clamp(40px, 6.6vw, 72px); line-height: 1.12; letter-spacing: -.055em; font-weight: 680; }
.hero h1 span { color: #8fa6c8; }
.hero-copy { max-width: 650px; margin: 26px 0 30px; color: #a6afbc; font-size: 16px; line-height: 1.9; }
.hero-meta { display: flex; flex-wrap: wrap; gap: 10px 24px; color: #7e8998; font-size: 11px; }
.status-dot { display: inline-block; width: 7px; height: 7px; margin-right: 7px; border-radius: 50%; background: #80c9a5; }
.project-section,.explorations-section { padding: 62px 0 22px; }
.section-heading { display: flex; justify-content: space-between; align-items: end; gap: 20px; margin-bottom: 24px; }
.section-heading .eyebrow { margin-bottom: 9px; }
.section-heading h2 { margin: 0; font-size: 25px; letter-spacing: -.03em; }
.section-heading>p { margin: 0 0 3px; color: #7e8998; font-size: 12px; }
.project-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 14px; }
.project-card { min-height: 164px; display: flex; flex-direction: column; padding: 21px; border: 1px solid #2b3440; border-radius: 12px; background: #171d25; transition: border-color .18s, transform .18s; }
.project-card:hover,.document-row:hover { border-color: #7189aa; transform: translateY(-1px); }
.card-kicker { color: #798ba6; font-size: 9px; font-weight: 700; letter-spacing: .15em; }
.project-card strong { margin-top: 16px; font-size: 17px; }
.card-description { margin-top: 8px; color: #929eae; font-size: 12px; line-height: 1.65; }
.card-arrow { margin-top: auto; padding-top: 16px; color: #a9bfdf; font-size: 11px; }
.exploration-group { padding: 26px 0 30px; border-top: 1px solid #29303a; }
.group-heading { display: grid; grid-template-columns: 42px 1fr; gap: 12px; margin-bottom: 17px; }
.group-number { color: #7188a7; font-size: 13px; font-variant-numeric: tabular-nums; padding-top: 4px; }
.group-heading h3 { margin: 0; font-size: 17px; }
.group-heading p { max-width: 760px; margin: 7px 0 0; color: #8793a3; font-size: 12px; line-height: 1.7; }
.document-list { margin-left: 54px; border-top: 1px solid #242c36; }
.document-row { display: flex; gap: 20px; align-items: center; justify-content: space-between; padding: 13px 14px; border-bottom: 1px solid #242c36; transition: border-color .18s, transform .18s; }
.document-copy { display: flex; flex-direction: column; gap: 4px; }
.document-copy strong { font-size: 12px; font-weight: 650; }
.document-copy span { color: #8290a1; font-size: 11px; line-height: 1.5; }
.document-arrow { color: #9eb4d4; font-size: 14px; }
.footer { display: flex; justify-content: space-between; gap: 30px; align-items: center; margin-top: 44px; padding: 28px 0 40px; border-top: 1px solid #29303a; }
.footer strong { font-size: 10px; letter-spacing: .16em; }
.footer p { max-width: 710px; margin: 8px 0 0; color: #7f8b9a; font-size: 11px; line-height: 1.7; }
@media (max-width: 720px) {
  .site-shell { padding: 0 19px; }
  .topbar { height: 64px; }
  .hero { padding: 72px 0 58px; }
  .hero-copy { font-size: 14px; }
  .section-heading { align-items: start; flex-direction: column; gap: 8px; }
  .project-grid { grid-template-columns: 1fr; }
  .document-list { margin-left: 0; }
  .group-heading { grid-template-columns: 32px 1fr; }
  .footer { align-items: start; flex-direction: column; }
}
</style>
