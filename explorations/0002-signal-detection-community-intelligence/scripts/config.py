"""
信号检测系统配置文件
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "signals.db"

# 确保数据目录存在
DATA_DIR.mkdir(exist_ok=True)
(DATA_DIR / "arxiv" / "papers").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "arxiv" / "citations").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "github" / "repos").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "github" / "stars").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "github" / "activity").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "hackernews" / "stories").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "hackernews" / "comments").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "signals").mkdir(parents=True, exist_ok=True)

# API 配置
ARXIV_CONFIG = {
    # AI 自身 + 安全、软件工程、数据系统、分布式系统和编程语言等技术分支。
    "categories": [
        "cs.AI", "cs.LG", "cs.CL", "cs.CV",
        "cs.CR", "cs.SE", "cs.DB", "cs.DC", "cs.PL", "cs.IR",
    ],
    # 每个类别独立采样，避免一个大类吞没其他技术分支。
    "max_results_per_category": 20,
    "sort_by": "submittedDate",
}

GITHUB_CONFIG = {
    "token": os.getenv("GITHUB_TOKEN", ""),  # 设置环境变量 GITHUB_TOKEN
    # 主题覆盖是研究采样范围，不代表领域完整性或需求强度。
    "topics": [
        "artificial-intelligence", "ai-agents", "inference", "rag",
        "llm-evaluation", "cybersecurity", "software-supply-chain",
        "developer-tools", "data-engineering", "observability",
    ],
    "min_stars": 10,
    "max_stars": 100,
    # GitHub 搜索 API 有配额限制；每个 Topic 仅采第一页。
    "max_pages_per_topic": 1,
    "max_repos_per_topic": 30,
    "search_delay_seconds": 2 if os.getenv("GITHUB_TOKEN") else 7,
}

HACKERNEWS_CONFIG = {
    "top_stories_count": 100,
    "new_stories_count": 100,
}

# 信号检测阈值
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
    "abandonment_narrative": {
        "min_mentions": 3,
    },
    "recurring_topic": {
        "min_communities": 2,  # 当前系统仅采集 hackernews + github 两个来源
        "min_occurrences": 5,
    },
}

# 数据库 Schema
DB_SCHEMA = """
-- 论文表
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    title TEXT,
    abstract TEXT,
    published DATE,
    categories TEXT,
    authors TEXT,
    "references" TEXT
);

-- 引用关系表
CREATE TABLE IF NOT EXISTS citations (
    paper_id TEXT,
    cited_paper_id TEXT,
    PRIMARY KEY (paper_id, cited_paper_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id),
    FOREIGN KEY (cited_paper_id) REFERENCES papers(id)
);

-- GitHub 项目表
CREATE TABLE IF NOT EXISTS github_repos (
    repo TEXT PRIMARY KEY,
    description TEXT,
    language TEXT,
    stars INTEGER,
    forks INTEGER,
    created_at DATE,
    updated_at DATE,
    topics TEXT
);

-- Star 历史表
CREATE TABLE IF NOT EXISTS star_history (
    repo TEXT,
    date DATE,
    stars INTEGER,
    PRIMARY KEY (repo, date),
    FOREIGN KEY (repo) REFERENCES github_repos(repo)
);

-- HN 帖子表
CREATE TABLE IF NOT EXISTS hn_stories (
    id INTEGER PRIMARY KEY,
    title TEXT,
    url TEXT,
    score INTEGER,
    descendants INTEGER,
    author TEXT,
    time INTEGER,
    detected_date DATE
);

-- HN 评论表
CREATE TABLE IF NOT EXISTS hn_comments (
    id INTEGER PRIMARY KEY,
    story_id INTEGER,
    author TEXT,
    text TEXT,
    time INTEGER,
    parent INTEGER,
    FOREIGN KEY (story_id) REFERENCES hn_stories(id)
);

-- 信号表
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_type TEXT,
    source TEXT,
    description TEXT,
    detected_date DATE,
    confidence REAL,
    status TEXT DEFAULT 'detected',
    outcome TEXT,
    metadata TEXT,
    validated_date DATE
);

-- 关键人物表
CREATE TABLE IF NOT EXISTS key_figures (
    id TEXT PRIMARY KEY,
    name TEXT,
    platform TEXT,
    type TEXT,
    degree_centrality REAL,
    betweenness_centrality REAL,
    pagerank REAL,
    last_updated DATE
);

-- 社区表
CREATE TABLE IF NOT EXISTS communities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    members TEXT,
    detected_date DATE
);
"""
