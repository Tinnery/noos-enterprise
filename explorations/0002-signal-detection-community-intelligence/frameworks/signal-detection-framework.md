# 信号检测框架

**版本**: 1.0  
**创建日期**: 2026-03-18  
**最后更新**: 2026-03-18

---

## 1. 框架概述

本框架定义了如何系统性地检测和识别技术行业中的弱信号，使其能够在信息成为主流之前被捕获。框架分为四个核心模块：

1. **数据采集层**：定义数据源、采集频率、存储格式
2. **信号识别层**：定义弱信号类型、识别算法、阈值设置
3. **社区分析层**：定义社会网络分析方法、关键人物识别
4. **反馈评估层**：定义预测追踪、准确性评估、方法论迭代

---

## 2. 数据采集层

### 2.1 数据源规范

#### 2.1.1 学术层（arXiv）

**数据内容**：
- 论文元数据（标题、摘要、作者、发布日期）
- 引用关系（参考文献列表）
- 分类标签（arXiv categories）

**采集方法**：
```python
# 使用 arXiv API
import arxiv

# 搜索最近 7 天的论文
search = arxiv.Search(
    query="cat:cs.AI OR cat:cs.LG",
    max_results=100,
    sort_by=arxiv.SortCriterion.SubmittedDate
)

for result in search.results():
    # 提取：title, summary, authors, published, categories, references
    pass
```

**采集频率**：每日  
**存储格式**：JSON（每篇论文一个对象）  
**关键字段**：
```json
{
  "id": "arxiv_id",
  "title": "论文标题",
  "abstract": "摘要",
  "authors": ["作者1", "作者2"],
  "published": "2026-03-18T00:00:00Z",
  "categories": ["cs.AI", "cs.LG"],
  "references": ["ref1", "ref2"],
  "citations": []
}
```

#### 2.1.2 开源层（GitHub）

**数据内容**：
- 项目元数据（名称、描述、语言、star 数、fork 数）
- star 历史（每日 star 增长）
- PR/Issue 活动（新 PR、新 Issue、合并/关闭状态）
- 贡献者网络（谁贡献了什么）

**采集方法**：
```python
# 使用 GitHub REST API
import requests

# 获取项目信息
url = "https://api.github.com/repos/{owner}/{repo}"
headers = {"Authorization": "token {token}"}
response = requests.get(url, headers=headers)

# 获取 star 历史（需要第三方服务或自行追踪）
# 建议：每日记录 star 数，构建时间序列
```

**采集频率**：每日  
**存储格式**：JSON + 时间序列 CSV  
**关键字段**：
```json
{
  "repo": "owner/repo",
  "description": "项目描述",
  "language": "Python",
  "stars": 150,
  "forks": 20,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-03-18T00:00:00Z",
  "daily_stars": [
    {"date": "2026-03-17", "count": 5},
    {"date": "2026-03-18", "count": 12}
  ]
}
```

#### 2.1.3 社交层（Hacker News）

**数据内容**：
- 帖子（标题、URL、分数、评论数、作者）
- 评论（内容、作者、时间、父评论 ID）
- 用户（karma、提交历史）

**采集方法**：
```python
# 使用 Hacker News Firebase API
import requests

# 获取热门帖子
url = "https://hacker-news.firebaseio.com/v0/topstories.json"
story_ids = requests.get(url).json()[:100]

for story_id in story_ids:
    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
    story = requests.get(story_url).json()
    # 提取：title, url, score, descendants, by, time
```

**采集频率**：每日  
**存储格式**：JSON  
**关键字段**：
```json
{
  "id": 12345678,
  "title": "帖子标题",
  "url": "https://example.com",
  "score": 150,
  "descendants": 45,
  "by": "username",
  "time": 1710720000
}
```

### 2.2 数据存储规范

**目录结构**：
```
data/
├── arxiv/
│   ├── papers/
│   │   ├── 2026-03-18.json
│   │   └── 2026-03-19.json
│   └── citations/
│       └── citation_graph_2026-03-18.json
├── github/
│   ├── repos/
│   │   └── repo_metadata.json
│   ├── stars/
│   │   └── star_history.csv
│   └── activity/
│       └── pr_activity_2026-03-18.json
├── hackernews/
│   ├── stories/
│   │   └── stories_2026-03-18.json
│   └── comments/
│       └── comments_2026-03-18.json
└── signals/
    └── detected_signals.json
```

**数据库设计**（SQLite）：
```sql
-- 论文表
CREATE TABLE papers (
    id TEXT PRIMARY KEY,
    title TEXT,
    abstract TEXT,
    published DATE,
    categories TEXT,
    authors TEXT
);

-- 引用关系表
CREATE TABLE citations (
    paper_id TEXT,
    cited_paper_id TEXT,
    FOREIGN KEY (paper_id) REFERENCES papers(id),
    FOREIGN KEY (cited_paper_id) REFERENCES papers(id)
);

-- GitHub 项目表
CREATE TABLE github_repos (
    repo TEXT PRIMARY KEY,
    description TEXT,
    language TEXT,
    stars INTEGER,
    forks INTEGER,
    created_at DATE,
    updated_at DATE
);

-- Star 历史表
CREATE TABLE star_history (
    repo TEXT,
    date DATE,
    stars INTEGER,
    PRIMARY KEY (repo, date)
);

-- HN 帖子表
CREATE TABLE hn_stories (
    id INTEGER PRIMARY KEY,
    title TEXT,
    url TEXT,
    score INTEGER,
    comments INTEGER,
    author TEXT,
    time INTEGER
);

-- 信号表
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_type TEXT,
    source TEXT,
    description TEXT,
    detected_date DATE,
    confidence REAL,
    metadata TEXT
);
```

---

## 3. 信号识别层

### 3.1 弱信号类型定义

#### 3.1.1 引用网络变化信号

**定义**：某篇论文在短时间内被多个不相关领域的论文引用

**识别算法**：
```python
import networkx as nx
from collections import defaultdict

def detect_citation_anomaly(citation_graph, time_window_days=7):
    """
    检测引用网络中的异常增长
    
    Args:
        citation_graph: NetworkX 有向图，节点是论文，边是引用关系
        time_window_days: 时间窗口（天）
    
    Returns:
        list of (paper_id, anomaly_score, citing_categories)
    """
    anomalies = []
    
    for node in citation_graph.nodes():
        # 获取最近 time_window_days 内的引用
        recent_citations = [
            edge for edge in citation_graph.in_edges(node)
            if is_recent(edge, time_window_days)
        ]
        
        if len(recent_citations) < 3:
            continue
        
        # 计算引用来源的类别多样性
        citing_categories = set()
        for citing_paper, _ in recent_citations:
            citing_categories.add(get_paper_category(citing_paper))
        
        # 如果引用来自 3+ 个不同类别，可能是跨领域影响
        if len(citing_categories) >= 3:
            anomaly_score = len(recent_citations) * len(citing_categories)
            anomalies.append((node, anomaly_score, citing_categories))
    
    return sorted(anomalies, key=lambda x: x[1], reverse=True)
```

**阈值设置**：
- 最低引用数：3 次/周
- 最低类别多样性：3 个不同 arXiv 类别
- 异常分数阈值：> 10

#### 3.1.2 低星项目 trending 信号

**定义**：GitHub 上 10-100 星的项目在短时间内 star 增长异常

**识别算法**：
```python
import pandas as pd
from scipy.stats import zscore

def detect_github_trending(star_history_df, z_threshold=2.0):
    """
    检测 GitHub 项目的异常 star 增长
    
    Args:
        star_history_df: DataFrame，列：repo, date, stars
        z_threshold: Z-score 阈值
    
    Returns:
        list of (repo, growth_rate, z_score)
    """
    trends = []
    
    for repo in star_history_df['repo'].unique():
        repo_data = star_history_df[star_history_df['repo'] == repo].copy()
        repo_data = repo_data.sort_values('date')
        
        # 计算每日 star 增长
        repo_data['daily_growth'] = repo_data['stars'].diff()
        
        # 只关注 10-100 星的项目
        current_stars = repo_data['stars'].iloc[-1]
        if not (10 <= current_stars <= 100):
            continue
        
        # 计算最近 7 天的平均增长
        recent_growth = repo_data['daily_growth'].tail(7).mean()
        
        # 计算历史平均增长和标准差
        historical_mean = repo_data['daily_growth'].mean()
        historical_std = repo_data['daily_growth'].std()
        
        if historical_std == 0:
            continue
        
        # 计算 Z-score
        z_score = (recent_growth - historical_mean) / historical_std
        
        if z_score > z_threshold:
            trends.append((repo, recent_growth, z_score))
    
    return sorted(trends, key=lambda x: x[2], reverse=True)
```

**阈值设置**：
- Star 范围：10-100
- Z-score 阈值：> 2.0
- 最低增长率：> 5 stars/天

#### 3.1.3 "放弃叙事"信号

**定义**：技术博客、Stack Overflow 中出现"放弃 X 工具"类内容

**识别算法**：
```python
from bertopic import BERTopic
import re

def detect_abandonment_narratives(texts, keywords=None):
    """
    检测"放弃 X 工具"类叙事
    
    Args:
        texts: list of str，文本内容
        keywords: list of str，关键词列表
    
    Returns:
        list of (topic, frequency, example_texts)
    """
    if keywords is None:
        keywords = [
            r"migrat(?:e|ing|ion) from (\w+)",
            r"switch(?:ed|ing) from (\w+)",
            r"abandon(?:ing)? (\w+)",
            r"replace(?:d|ing)? (\w+)",
            r"(\w+) alternative",
            r"better than (\w+)"
        ]
    
    # 提取工具名称
    tool_mentions = defaultdict(list)
    
    for text in texts:
        for pattern in keywords:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                tool_name = match.group(1)
                tool_mentions[tool_name].append(text)
    
    # 主题建模
    topic_model = BERTopic()
    topics, probs = topic_model.fit_transform(texts)
    
    # 识别高频工具提及
    narratives = []
    for tool, mentions in tool_mentions.items():
        if len(mentions) >= 3:  # 至少 3 次提及
            narratives.append({
                'tool': tool,
                'frequency': len(mentions),
                'examples': mentions[:3]
            })
    
    return sorted(narratives, key=lambda x: x['frequency'], reverse=True)
```

**阈值设置**：
- 最低提及次数：3 次/周
- 关键词匹配模式：迁移、切换、放弃、替代

#### 3.1.4 小众论坛重复话题信号

**定义**：某话题在多个独立社区中重复出现

**识别算法**：
```python
from collections import Counter

def detect_recurring_topics(posts_by_community, min_communities=3, min_occurrences=5):
    """
    检测跨社区的重复话题
    
    Args:
        posts_by_community: dict，{community: [posts]}
        min_communities: 最少涉及的社区数
        min_occurrences: 最少出现次数
    
    Returns:
        list of (topic, communities, occurrences)
    """
    # 提取每个社区的关键词
    community_keywords = {}
    
    for community, posts in posts_by_community.items():
        # 使用 TF-IDF 或关键词提取
        keywords = extract_keywords(posts)
        community_keywords[community] = set(keywords)
    
    # 找出跨社区的共同关键词
    all_keywords = Counter()
    keyword_communities = defaultdict(set)
    
    for community, keywords in community_keywords.items():
        for keyword in keywords:
            all_keywords[keyword] += 1
            keyword_communities[keyword].add(community)
    
    # 筛选符合条件的关键词
    recurring = []
    for keyword, count in all_keywords.items():
        communities = keyword_communities[keyword]
        if len(communities) >= min_communities and count >= min_occurrences:
            recurring.append({
                'topic': keyword,
                'communities': list(communities),
                'occurrences': count
            })
    
    return sorted(recurring, key=lambda x: x['occurrences'], reverse=True)
```

**阈值设置**：
- 最少涉及社区：3 个
- 最少出现次数：5 次/周

### 3.2 信号优先级评估

**评估维度**：

1. **新颖性**（Novelty）：信号是否代表新出现的趋势
   - 高：首次在多个来源检测到
   - 中：在单一来源检测到，但增长迅速
   - 低：已知趋势的延续

2. **影响力**（Impact）：信号可能影响的领域范围
   - 高：跨多个行业/领域
   - 中：影响单一行业
   - 低：影响特定技术栈

3. **可信度**（Credibility）：信号来源的可靠性
   - 高：学术论文 + 开源项目 + 社区讨论
   - 中：单一来源但质量高
   - 低：来源不明或质量低

4. **行动性**（Actionability）：是否可以基于信号采取行动
   - 高：可以立即启动原型或实验
   - 中：需要进一步验证
   - 低：仅为观察性信息

**优先级公式**：
```
Priority = (Novelty * 0.3) + (Impact * 0.3) + (Credibility * 0.2) + (Actionability * 0.2)
```

---

## 4. 社区分析层

### 4.1 社会网络构建

**节点定义**：
- 个人（开发者、研究者、意见领袖）
- 项目（GitHub 仓库）
- 组织（公司、研究机构）

**边定义**：
- 关注关系（Twitter、GitHub）
- 协作关系（共同作者、PR 贡献）
- 引用关系（论文引用、项目依赖）
- 互动关系（评论、转发、提及）

**网络构建代码**：
```python
import networkx as nx

def build_community_network(github_contributors, paper_authors, twitter_interactions):
    """
    构建社区网络图
    
    Args:
        github_contributors: list of (user, repo, contribution_type)
        paper_authors: list of (author, paper_id)
        twitter_interactions: list of (user1, user2, interaction_type)
    
    Returns:
        NetworkX Graph
    """
    G = nx.Graph()
    
    # 添加 GitHub 协作边
    for user, repo, contrib_type in github_contributors:
        G.add_node(user, type='person', platform='github')
        G.add_node(repo, type='project')
        G.add_edge(user, repo, relation='contributes')
    
    # 添加论文共同作者边
    author_papers = defaultdict(list)
    for author, paper_id in paper_authors:
        author_papers[author].append(paper_id)
        G.add_node(author, type='person', platform='academic')
    
    for paper_id in set(paper_id for _, paper_id in paper_authors):
        co_authors = [author for author, pid in paper_authors if pid == paper_id]
        for i, author1 in enumerate(co_authors):
            for author2 in co_authors[i+1:]:
                if G.has_edge(author1, author2):
                    G[author1][author2]['weight'] += 1
                else:
                    G.add_edge(author1, author2, relation='co-author', weight=1)
    
    # 添加 Twitter 互动边
    for user1, user2, interaction in twitter_interactions:
        G.add_node(user1, type='person', platform='twitter')
        G.add_node(user2, type='person', platform='twitter')
        if G.has_edge(user1, user2):
            G[user1][user2]['weight'] += 1
        else:
            G.add_edge(user1, user2, relation='interacts', weight=1)
    
    return G
```

### 4.2 关键人物识别

**中心性指标**：

1. **Degree Centrality**（度中心性）：连接数量
   ```python
   degree_centrality = nx.degree_centrality(G)
   ```

2. **Betweenness Centrality**（中介中心性）：桥接不同社区的能力
   ```python
   betweenness_centrality = nx.betweenness_centrality(G)
   ```

3. **Closeness Centrality**（接近中心性）：到达所有其他节点的容易程度
   ```python
   closeness_centrality = nx.closeness_centrality(G)
   ```

4. **PageRank**：影响力传播
   ```python
   pagerank = nx.pagerank(G)
   ```

**关键人物分类**：

```python
def classify_key_figures(G, centrality_metrics):
    """
    分类关键人物
    
    Returns:
        dict: {
            'opinion_leaders': [...],
            'information_hubs': [...],
            'emerging_voices': [...]
        }
    """
    opinion_leaders = []
    information_hubs = []
    emerging_voices = []
    
    for node in G.nodes():
        if G.nodes[node].get('type') != 'person':
            continue
        
        degree = centrality_metrics['degree'].get(node, 0)
        betweenness = centrality_metrics['betweenness'].get(node, 0)
        pagerank = centrality_metrics['pagerank'].get(node, 0)
        
        # 意见领袖：高 PageRank + 高度中心性
        if pagerank > 0.01 and degree > 0.1:
            opinion_leaders.append(node)
        
        # 信息枢纽：高中介中心性
        elif betweenness > 0.05:
            information_hubs.append(node)
        
        # 新兴声音：近期活跃度上升
        # 需要时间序列数据
        # if recent_activity_increase > threshold:
        #     emerging_voices.append(node)
    
    return {
        'opinion_leaders': opinion_leaders,
        'information_hubs': information_hubs,
        'emerging_voices': emerging_voices
    }
```

### 4.3 社区检测

**算法选择**：

1. **Louvain**：适用于大规模网络
   ```python
   from community import community_louvain
   partition = community_louvain.best_partition(G)
   ```

2. **Label Propagation**：快速，适用于动态网络
   ```python
   from networkx.algorithms.community import label_propagation_communities
   communities = list(label_propagation_communities(G))
   ```

**社区可视化**：
```python
import matplotlib.pyplot as plt

def visualize_communities(G, partition):
    """
    可视化社区结构
    """
    pos = nx.spring_layout(G)
    
    # 按社区着色
    colors = [partition[node] for node in G.nodes()]
    
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, node_color=colors, node_size=100, with_labels=False)
    plt.title("Community Structure")
    plt.show()
```

### 4.4 跨社区传播追踪

**追踪方法**：

```python
def track_cross_community_spread(signal, communities, time_series):
    """
    追踪信号在不同社区间的传播
    
    Args:
        signal: str，信号标识
        communities: list of community_id
        time_series: dict，{community: [timestamps]}
    
    Returns:
        list of (from_community, to_community, time_lag_days)
    """
    spread_paths = []
    
    # 找出信号首次出现的社区
    first_appearance = {}
    for community, timestamps in time_series.items():
        if timestamps:
            first_appearance[community] = min(timestamps)
    
    # 按时间排序
    sorted_communities = sorted(first_appearance.items(), key=lambda x: x[1])
    
    # 计算传播路径和时滞
    for i in range(len(sorted_communities) - 1):
        from_comm, from_time = sorted_communities[i]
        to_comm, to_time = sorted_communities[i + 1]
        
        time_lag = (to_time - from_time).days
        spread_paths.append((from_comm, to_comm, time_lag))
    
    return spread_paths
```

---

## 5. 反馈评估层

### 5.1 预测追踪

**追踪机制**：

```python
class SignalTracker:
    def __init__(self, db_path):
        self.db = sqlite3.connect(db_path)
    
    def log_signal(self, signal_id, signal_type, description, confidence):
        """
        记录检测到的信号
        """
        self.db.execute("""
            INSERT INTO signals (signal_type, description, confidence, detected_date, status)
            VALUES (?, ?, ?, ?, ?)
        """, (signal_type, description, confidence, datetime.now(), 'detected'))
        self.db.commit()
    
    def update_signal_status(self, signal_id, status, outcome=None):
        """
        更新信号状态
        
        Args:
            status: 'validated' | 'invalidated' | 'pending'
            outcome: 实际结果描述
        """
        self.db.execute("""
            UPDATE signals
            SET status = ?, outcome = ?, validated_date = ?
            WHERE id = ?
        """, (status, outcome, datetime.now(), signal_id))
        self.db.commit()
    
    def calculate_accuracy(self, time_window_days=180):
        """
        计算预测准确性
        """
        cursor = self.db.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'validated' THEN 1 ELSE 0 END) as validated,
                SUM(CASE WHEN status = 'invalidated' THEN 1 ELSE 0 END) as invalidated
            FROM signals
            WHERE detected_date >= date('now', '-{} days')
        """.format(time_window_days))
        
        total, validated, invalidated = cursor.fetchone()
        
        if total == 0:
            return 0.0
        
        accuracy = validated / total if total > 0 else 0.0
        return accuracy
```

### 5.2 准确性评估

**评估指标**：

1. **预测准确性**（Prediction Accuracy）
   - 定义：提前 6-12 个月识别的趋势中，最终成为主流的比例
   - 目标：> 70%
   - 计算：`validated_signals / total_signals`

2. **信息时滞**（Information Lag）
   - 定义：从信号出现到我们捕获的时间
   - 目标：< 7 天
   - 计算：`capture_date - signal_emergence_date`

3. **误报率**（False Positive Rate）
   - 定义：识别的信号中，未成为趋势的比例
   - 目标：< 30%
   - 计算：`invalidated_signals / total_signals`

4. **漏报率**（False Negative Rate）
   - 定义：成为主流但未被提前捕获的趋势比例
   - 目标：< 20%
   - 计算：`missed_trends / total_trends`（需要外部基准）

### 5.3 方法论迭代

**迭代流程**：

1. **定期回顾**（每月）
   - 审查检测到的信号
   - 评估预测准确性
   - 识别误报和漏报案例

2. **根因分析**
   - 误报原因：阈值过低？数据源噪声？
   - 漏报原因：数据源覆盖不足？算法灵敏度不足？

3. **参数调整**
   - 调整信号识别阈值
   - 添加/移除数据源
   - 优化算法参数

4. **文档更新**
   - 更新本框架文档
   - 记录方法论变更
   - 分享经验教训

---

## 6. 实施路线图

### Phase 1: 基础设施（第 1-2 周）

- [ ] 搭建数据采集脚本（arXiv、GitHub、HN）
- [ ] 设计数据库 schema
- [ ] 实现数据存储和查询接口
- [ ] 构建基础可视化（信号列表、时间序列图）

### Phase 2: 信号识别（第 3-4 周）

- [ ] 实现引用网络变化检测
- [ ] 实现低星项目 trending 检测
- [ ] 实现"放弃叙事"检测
- [ ] 实现跨社区重复话题检测

### Phase 3: 社区分析（第 5-6 周）

- [ ] 构建社区网络图
- [ ] 实现关键人物识别
- [ ] 实现社区检测算法
- [ ] 实现跨社区传播追踪

### Phase 4: 反馈循环（第 7-8 周）

- [ ] 实现信号追踪系统
- [ ] 实现准确性评估
- [ ] 建立定期回顾机制
- [ ] 文档化方法论

---

## 7. 参考资源

- **NetworkX 文档**: https://networkx.org/
- **BERTopic 文档**: https://maartengr.github.io/BERTopic/
- **arXiv API 文档**: https://arxiv.org/help/api
- **GitHub API 文档**: https://docs.github.com/en/rest
- **Hacker News API 文档**: https://github.com/HackerNews/API

---

**文档维护**: 本框架随实践迭代更新，每次重大方法论变更后修订版本。
