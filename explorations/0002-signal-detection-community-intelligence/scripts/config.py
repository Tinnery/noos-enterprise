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
    "categories": ["cs.AI", "cs.LG", "cs.CL", "cs.CV"],
    "max_results": 100,
    "sort_by": "submittedDate",
}

GITHUB_CONFIG = {
    "token": os.getenv("GITHUB_TOKEN", ""),  # 设置环境变量 GITHUB_TOKEN
    "topics": ["artificial-intelligence", "machine-learning", "llm", "agent"],
    "min_stars": 10,
    "max_stars": 100,
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
        "min_communities": 3,
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
