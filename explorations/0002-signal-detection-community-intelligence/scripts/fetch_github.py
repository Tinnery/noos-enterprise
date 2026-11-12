"""
GitHub 数据采集模块
"""

import requests
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).parent))

from config import GITHUB_CONFIG, DATA_DIR, DB_PATH


def fetch_trending_repos(topic=None, min_stars=10, max_stars=100, max_pages=5):
    """
    获取 GitHub trending 项目
    
    Args:
        topic: 主题标签（如 "machine-learning"）
        min_stars: 最小 star 数
        max_stars: 最大 star 数
        max_pages: 最大页数
    
    Returns:
        list of dict: 项目列表
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    
    if GITHUB_CONFIG["token"]:
        headers["Authorization"] = f"token {GITHUB_CONFIG['token']}"
    
    repos = []
    
    # 构建查询
    query_parts = [f"stars:{min_stars}..{max_stars}"]
    if topic:
        query_parts.append(f"topic:{topic}")
    
    query = " ".join(query_parts)
    
    print(f"正在获取 GitHub 项目（主题: {topic or 'all'}）...")
    
    for page in range(1, max_pages + 1):
        url = "https://api.github.com/search/repositories"
        params = {
            "q": query,
            "sort": "updated",
            "order": "desc",
            "per_page": 100,
            "page": page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                break
            
            for item in items:
                repo = {
                    "repo": item["full_name"],
                    "description": item.get("description", ""),
                    "language": item.get("language"),
                    "stars": item["stargazers_count"],
                    "forks": item["forks_count"],
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                    "topics": item.get("topics", []),
                    "url": item["html_url"],
                }
                repos.append(repo)
            
            # 检查是否还有更多页
            if len(items) < 100:
                break
            
            # 避免触发速率限制
            time.sleep(1)
            
        except Exception as e:
            print(f"  ✗ 获取第 {page} 页失败: {e}")
            break
    
    print(f"✓ 获取到 {len(repos)} 个项目")
    return repos


def fetch_star_history(repo_name, days_back=30):
    """
    获取项目的 star 历史
    
    注意：GitHub API 不直接提供 star 历史，需要使用 stargazers API 分页获取
    使用 Accept: application/vnd.github.v3.star+json 获取 starred_at 时间戳
    
    时间序列语义说明：
    - "最近 7 天" 指的是日历日（calendar days），不是 "有记录的最近 7 个日期"
    - 如果某天没有 star，该日不会出现在记录中，但计算时仍以日历日为基准
    - days_back=30 表示获取最近 30 个日历日的数据
    
    Args:
        repo_name: 项目名称（如 "owner/repo"）
        days_back: 获取最近多少天（日历日）
    
    Returns:
        list of dict: star 历史记录 [{"date": "YYYY-MM-DD", "stars": count}, ...]
    """
    headers = {
        "Accept": "application/vnd.github.v3.star+json",
    }
    
    if GITHUB_CONFIG["token"]:
        headers["Authorization"] = f"token {GITHUB_CONFIG['token']}"
    
    # 分页获取所有 stargazers
    all_stargazers = []
    page = 1
    per_page = 100  # 最大每页 100 条
    
    while True:
        url = f"https://api.github.com/repos/{repo_name}/stargazers"
        params = {
            "per_page": per_page,
            "page": page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            stargazers = response.json()
            
            if not stargazers:
                break
            
            all_stargazers.extend(stargazers)
            
            # 检查是否还有更多页
            if len(stargazers) < per_page:
                break
            
            page += 1
            time.sleep(0.5)  # 避免速率限制
            
        except Exception as e:
            print(f"  ✗ 获取 {repo_name} star 历史第 {page} 页失败: {e}")
            break
    
    # 按日期统计
    star_counts = {}
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    for star in all_stargazers:
        starred_at = star.get("starred_at")
        if starred_at:
            date = starred_at[:10]  # YYYY-MM-DD
            star_date = datetime.strptime(date, "%Y-%m-%d")
            if star_date >= cutoff_date:
                star_counts[date] = star_counts.get(date, 0) + 1
    
    # 转换为列表（已过滤并排序）
    history = [
        {"date": date, "stars": count}
        for date, count in sorted(star_counts.items())
    ]
    
    return history


def save_repos_to_json(repos, date_str=None):
    """保存项目到 JSON 文件"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    output_path = DATA_DIR / "github" / "repos" / f"{date_str}.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 项目已保存到: {output_path}")
    return output_path


def save_repos_to_db(repos):
    """保存项目到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    processed = 0
    for repo in repos:
        try:
            cursor.execute("""
                INSERT INTO github_repos 
                (repo, description, language, stars, forks, created_at, updated_at, topics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(repo) DO UPDATE SET
                    description = excluded.description,
                    language = excluded.language,
                    stars = excluded.stars,
                    forks = excluded.forks,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    topics = excluded.topics
            """, (
                repo["repo"],
                repo["description"],
                repo["language"],
                repo["stars"],
                repo["forks"],
                repo["created_at"],
                repo["updated_at"],
                json.dumps(repo["topics"])
            ))
            processed += 1
        except Exception as e:
            print(f"  ✗ 插入/更新项目失败 {repo['repo']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✓ 数据库处理 {processed} 个项目（新增+更新）")
    return processed


def save_star_history_to_db(repo_name, history):
    """保存 star 历史到数据库"""
    if not history:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    processed = 0
    for record in history:
        try:
            cursor.execute("""
                INSERT INTO star_history (repo, date, stars)
                VALUES (?, ?, ?)
                ON CONFLICT(repo, date) DO UPDATE SET stars = excluded.stars
            """, (repo_name, record["date"], record["stars"]))
            processed += 1
        except Exception as e:
            print(f"  ✗ 插入/更新 star 历史失败: {e}")
    
    conn.commit()
    conn.close()
    
    return processed


def fetch_and_store_github(topics=None, max_repos_per_topic=None):
    """按多个技术分支采样 GitHub 项目，并限制搜索 API 请求量。"""
    if topics is None:
        topics = GITHUB_CONFIG["topics"]
    if max_repos_per_topic is None:
        max_repos_per_topic = GITHUB_CONFIG["max_repos_per_topic"]

    max_pages = GITHUB_CONFIG["max_pages_per_topic"]
    search_delay = GITHUB_CONFIG["search_delay_seconds"]
    all_repos = []
    topics = list(topics)

    for index, topic in enumerate(topics):
        repos = fetch_trending_repos(topic=topic, max_pages=max_pages)

        # 限制每个主题的项目数（在 extend 之前截断）
        if len(repos) > max_repos_per_topic:
            repos = repos[:max_repos_per_topic]

        all_repos.extend(repos)
        if index < len(topics) - 1:
            time.sleep(search_delay)
    
    # 去重（同一项目出现在多个 topic 中，保留 stars 最高的记录）
    unique_dict = {}
    for repo in all_repos:
        name = repo["repo"]
        if name not in unique_dict or repo["stars"] > unique_dict[name]["stars"]:
            unique_dict[name] = repo
    unique_repos = list(unique_dict.values())
    
    if unique_repos:
        save_repos_to_json(unique_repos)
        save_repos_to_db(unique_repos)
        
        # 获取前 10 个项目的 star 历史
        print("\n正在获取 star 历史（前 10 个项目）...")
        for repo in unique_repos[:10]:
            history = fetch_star_history(repo["repo"], days_back=30)
            save_star_history_to_db(repo["repo"], history)
            time.sleep(0.5)  # 避免速率限制
    
    return unique_repos


if __name__ == "__main__":
    # 测试运行
    repos = fetch_and_store_github()
    print(f"\n示例项目:")
    if repos:
        sample = repos[0]
        print(f"  名称: {sample['repo']}")
        print(f"  描述: {sample['description']}")
        print(f"  Stars: {sample['stars']}")
        print(f"  语言: {sample['language']}")
