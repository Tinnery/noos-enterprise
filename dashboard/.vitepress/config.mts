import { defineConfig } from 'vitepress'

const exploration0001 = '/explorations/0001-ai-era-software-value'
const exploration0002 = '/explorations/0002-signal-detection-community-intelligence'

export default defineConfig({
  lang: 'zh-CN',
  title: 'Noos Enterprise',
  description: '研究 AI 时代真正值得解决的软件问题。以真实问题为起点，以可追溯证据检验判断。',
  base: '/noos-enterprise/',
  srcDir: '..',
  srcExclude: [
    'dashboard/**',
    'skills/**',
    '.github/**',
    '**/node_modules/**',
    // This generated snapshot contains raw HTML fragments copied from community posts.
    // Keep the source data intact, but do not treat it as a reader-facing Markdown page.
    'explorations/0002-signal-detection-community-intelligence/data/signals/report_2026-11-10.md',
  ],
  lastUpdated: true,
  cleanUrls: false,
  themeConfig: {
    siteTitle: 'NOOS ENTERPRISE',
    nav: [
      { text: '研究首页', link: '/' },
      { text: '0001 · 软件价值', link: exploration0001 + '/README' },
      { text: '0002 · 信号检测', link: exploration0002 + '/README' },
      {
        text: '项目原则',
        items: [
          { text: '项目简介', link: '/README' },
          { text: '愿景', link: '/VISION' },
          { text: 'Agent 工作规则', link: '/AGENTS' },
        ],
      },
      { text: 'GitHub', link: 'https://github.com/Tinnery/noos-enterprise' },
    ],
    sidebar: {
      '/explorations/0001-ai-era-software-value/': [
        {
          text: 'EXPLORATION 0001',
          items: [
            { text: '探索总览', link: exploration0001 + '/README' },
          ],
        },
        {
          text: '研究框架',
          collapsed: false,
          items: [
            { text: '软件产业分类图谱', link: exploration0001 + '/frameworks/software-landscape-taxonomy' },
            { text: 'AI Systems & Engineering', link: exploration0001 + '/frameworks/ai-systems-industry' },
            { text: '漏洞研究产业框架', link: exploration0001 + '/frameworks/vulnerability-research-industry' },
          ],
        },
        {
          text: '产品假设',
          collapsed: true,
          items: [
            { text: 'HYP-001 · 小企业 AI 工作流', link: exploration0001 + '/hypotheses/HYP-001-small-business-ai-workflow' },
            { text: 'HYP-002 · Family OS', link: exploration0001 + '/hypotheses/HYP-002-family-os' },
            { text: 'HYP-003 · 农业 AI 助手', link: exploration0001 + '/hypotheses/HYP-003-agriculture-ai-assistant' },
            { text: 'HYP-004 · 老年人数字助手', link: exploration0001 + '/hypotheses/HYP-004-elderly-digital-assistant' },
            { text: 'HYP-005 · 蓝领技能助手', link: exploration0001 + '/hypotheses/HYP-005-blue-collar-ai-assistant' },
          ],
        },
        {
          text: '深度研究',
          collapsed: true,
          items: [
            { text: '01 · 可证伪框架', link: exploration0001 + '/deep-research/01-falsification-framework' },
            { text: '02 · 反事实基线', link: exploration0001 + '/deep-research/02-counterfactual-baseline' },
            { text: '03 · 领先指标', link: exploration0001 + '/deep-research/03-leading-indicators' },
            { text: '04 · 分层时间预测', link: exploration0001 + '/deep-research/04-time-layered-predictions' },
            { text: '05 · 替代弹性', link: exploration0001 + '/deep-research/05-substitution-elasticity' },
            { text: '06 · 利益相关者视角', link: exploration0001 + '/deep-research/06-stakeholder-perspectives' },
            { text: '07 · 证据升级路径', link: exploration0001 + '/deep-research/07-evidence-upgrade-path' },
            { text: '08 · 三角验证框架', link: exploration0001 + '/deep-research/08-triangulation-framework' },
            { text: '09 · 代码变更可信验证试点', link: exploration0001 + '/deep-research/09-change-assurance-pilot' },
          ],
        },
        {
          text: '验证工具包',
          collapsed: true,
          items: [
            { text: 'HYP-001 验证工具包', link: exploration0001 + '/validation/hyp-001-toolkit' },
            { text: 'HYP-005 验证工具包', link: exploration0001 + '/validation/hyp-005-toolkit' },
          ],
        },
      ],
      '/explorations/0002-signal-detection-community-intelligence/': [
        {
          text: 'EXPLORATION 0002',
          items: [
            { text: '探索总览', link: exploration0002 + '/README' },
            { text: '信号检测框架', link: exploration0002 + '/frameworks/signal-detection-framework' },
            { text: '脚本使用说明', link: exploration0002 + '/scripts/README' },
          ],
        },
        {
          text: '采集与分析报告',
          collapsed: false,
          items: [
            { text: '社区分析报告', link: exploration0002 + '/data/signals/community_report' },
            { text: '反馈循环报告', link: exploration0002 + '/data/signals/feedback_report' },
            { text: '参与机会报告', link: exploration0002 + '/data/signals/participation_report' },
          ],
        },
      ],
      '/': [
        {
          text: '项目',
          items: [
            { text: '项目简介', link: '/README' },
            { text: '项目愿景', link: '/VISION' },
            { text: 'Agent 工作规则', link: '/AGENTS' },
          ],
        },
        {
          text: '研究任务',
          items: [
            { text: '0001 · AI 时代软件价值', link: exploration0001 + '/README' },
            { text: '0002 · 信号检测与社区情报', link: exploration0002 + '/README' },
          ],
        },
        {
          text: '研究模板',
          items: [
            { text: '机会研究卡', link: '/templates/opportunity-brief-template' },
            { text: '产品假设模板', link: '/templates/hypothesis-template' },
            { text: '实验记录模板', link: '/templates/experiment-template' },
          ],
        },
      ],
    },
    outline: {
      level: [2, 3],
      label: '本页内容',
    },
    search: {
      provider: 'local',
      options: {
        locales: {
          root: {
            translations: {
              button: {
                buttonText: '搜索研究',
                buttonAriaLabel: '搜索研究内容',
              },
              modal: {
                noResultsText: '没有找到相关内容',
                resetButtonTitle: '清除搜索',
                footer: {
                  selectText: '选择',
                  navigateText: '切换',
                  closeText: '关闭',
                },
              },
            },
          },
        },
      },
    },
    docFooter: {
      prev: '上一篇',
      next: '下一篇',
    },
    lastUpdated: {
      text: '最后更新于',
      formatOptions: {
        dateStyle: 'medium',
        timeStyle: 'short',
      },
    },
    editLink: {
      pattern: 'https://github.com/Tinnery/noos-enterprise/edit/main/:path',
      text: '在 GitHub 上编辑此页',
    },
    footer: {
      message: '研究内容以仓库 Markdown 原文为准。公开资料推断不等于真实用户验证。',
      copyright: '© Noos Enterprise · Explore. Discover. Create.',
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/Tinnery/noos-enterprise' },
    ],
  },
})
