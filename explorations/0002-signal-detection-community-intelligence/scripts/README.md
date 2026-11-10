# 信号检测系统使用指南

## 概述

信号检测系统是一个自动化工具，用于从多个数据源（arXiv、GitHub、Hacker News）采集数据，并识别技术行业中的弱信号。

## 安装依赖

```bash
cd scripts
pip install -r requirements.txt
```

## 快速开始

### 完整运行（数据采集 + 信号检测 + 报告生成）

```bash
python main.py
```

### 仅运行数据采集

```bash
python main.py --collection-only
```

### 仅运行信号检测

```bash
python main.py --detection-only
```

### 自定义参数

```bash
# 获取最近 14 天的数据
python main.py --days 14

# 跳过 GitHub 数据采集
python main.py --skip-github

# 跳过 Hacker News 数据采集
python main.py --skip-hackernews

# 不生成报告
python main.py --no-report
```

## 模块说明

### 数据采集模块

#### arXiv 论文采集

```python
from fetch_arxiv import fetch_and_store_arxiv

# 获取最近 7 天的论文
papers = fetch_and_store_arxiv(days_back=7)
```

#### GitHub 项目采集

```python
from fetch_github import fetch_and_store_github

# 获取 trending 项目
repos = fetch_and_store_github()
```

#### Hacker News 数据采集

```python
from fetch_hackernews import fetch_and_store_hackernews

# 获取热门帖子和评论
stories = fetch_and_store_hackernews(fetch_comments_for_top=10)
```

### 信号检测模块

```python
from detect_signals import SignalDetector

detector = SignalDetector()

# 运行所有检测算法
signals = detector.run_all_detections()

# 或单独运行某个检测
citation_anomalies = detector.detect_citation_anomalies(days_back=7)
github_trends = detector.detect_github_trending()
abandonment_narratives = detector.detect_abandonment_narratives()
recurring_topics = detector.detect_recurring_topics()

detector.close()
```

## 信号类型

### 1. 引用网络异常 (citation_anomaly)

**定义**：某篇论文在短时间内被多个不相关领域的论文引用

**识别标准**：
- 最低引用数：3 次/周
- 最低类别多样性：3 个不同 arXiv 类别
- 异常分数阈值：> 10

**意义**：可能代表跨领域影响，某项技术开始被多个领域关注

### 2. GitHub Trending (github_trending)

**定义**：10-100 星的项目在短时间内 star 增长异常

**识别标准**：
- Star 范围：10-100
- Z-score 阈值：> 2.0
- 最低增长率：> 5 stars/天

**意义**：可能代表新兴技术或工具，在早期阶段获得快速增长

### 3. 放弃叙事 (abandonment_narrative)

**定义**：技术博客、Stack Overflow 中出现"放弃 X 工具"类内容

**识别标准**：
- 最低提及次数：3 次/周
- 关键词匹配：迁移、切换、放弃、替代

**意义**：可能代表技术衰退信号，用户正在离开某个工具或平台

### 4. 跨社区重复话题 (recurring_topic)

**定义**：某话题在多个独立社区中重复出现

**识别标准**：
- 最少涉及社区：3 个
- 最少出现次数：5 次/周

**意义**：可能代表行业关注焦点，多个社区同时关注某个话题

## 数据存储

### 目录结构

```
data/
├── arxiv/
│   ├── papers/          # 论文 JSON 文件
│   └── citations/       # 引用关系数据
├── github/
│   ├── repos/           # 项目元数据
│   ├── stars/           # Star 历史
│   └── activity/        # PR/Issue 活动
├── hackernews/
│   ├── stories/         # 帖子数据
│   └── comments/        # 评论数据
└── signals/
    ├── signals.db       # SQLite 数据库
    └── report_*.md      # 检测报告
```

### 数据库 Schema

主要表：
- `papers`: 论文信息
- `citations`: 引用关系
- `github_repos`: GitHub 项目
- `star_history`: Star 历史
- `hn_stories`: HN 帖子
- `hn_comments`: HN 评论
- `signals`: 检测到的信号
- `key_figures`: 关键人物
- `communities`: 社区

## 配置

编辑 `config.py` 文件自定义配置：

### API 配置

```python
ARXIV_CONFIG = {
    "categories": ["cs.AI", "cs.LG", "cs.CL", "cs.CV"],
    "max_results": 100,
}

GITHUB_CONFIG = {
    "token": "your_github_token",  # 设置环境变量 GITHUB_TOKEN
    "topics": ["artificial-intelligence", "machine-learning"],
}
```

### 信号检测阈值

```python
SIGNAL_THRESHOLDS = {
    "citation_anomaly": {
        "min_citations": 3,
        "min_categories": 3,
        "anomaly_score_threshold": 10,
    },
    "github_trending": {
        "min_stars": 10,
        "max_stars": 100,
        "z_score_threshold": 2.0,
        "min_daily_growth": 5,
    },
}
```

## 定时运行

### Linux/macOS (cron)

```bash
# 每天凌晨 2 点运行
0 2 * * * cd /path/to/0002-signal-detection-community-intelligence/scripts && python main.py
```

### Windows (任务计划程序)

1. 打开任务计划程序
2. 创建基本任务
3. 设置触发器（每天）
4. 设置操作：启动程序
   - 程序：`python`
   - 参数：`main.py`
   - 起始于：`C:\dev\noos-enterprise\explorations\0002-signal-detection-community-intelligence\scripts`

## 故障排查

### 问题：GitHub API 速率限制

**解决方案**：
1. 设置 GitHub Token（环境变量 `GITHUB_TOKEN`）
2. 减少采集频率
3. 增加请求间隔

### 问题：数据库连接失败

**解决方案**：
1. 检查 `data/signals.db` 文件是否存在
2. 运行 `python init_db.py` 重新初始化数据库
3. 检查文件权限

### 问题：信号检测结果为空

**解决方案**：
1. 确认数据采集成功运行
2. 检查数据库中是否有数据
3. 调整信号检测阈值（降低阈值）

## 扩展开发

### 添加新的数据源

1. 创建新的采集模块（如 `fetch_reddit.py`）
2. 在 `config.py` 中添加配置
3. 在 `init_db.py` 中添加数据库表
4. 在 `main.py` 中集成

### 添加新的信号类型

1. 在 `detect_signals.py` 中添加检测方法
2. 在 `SIGNAL_THRESHOLDS` 中添加阈值配置
3. 在 `run_all_detections()` 中调用新方法
4. 在 `generate_report()` 中添加报告格式

## 性能优化

### 数据库优化

```python
# 添加索引
CREATE INDEX idx_papers_published ON papers(published);
CREATE INDEX idx_star_history_date ON star_history(date);
CREATE INDEX idx_hn_stories_detected ON hn_stories(detected_date);
```

### 采集优化

- 使用异步 IO（aiohttp）并发请求
- 增量采集（只获取新数据）
- 数据缓存（避免重复请求）

## 许可证

本项目遵循主项目许可证。

## 贡献

欢迎提交 Issue 和 Pull Request。
