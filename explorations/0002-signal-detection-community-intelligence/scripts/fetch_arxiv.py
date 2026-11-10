"""
arXiv 数据采集模块
"""

import arxiv
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config import ARXIV_CONFIG, DATA_DIR, DB_PATH


def fetch_arxiv_papers(days_back=7, max_results_per_category=None):
    """
    按 arXiv 类别独立采样，减少 AI 大类对其他软件技术分支的覆盖挤压。

    Args:
        days_back: 获取最近多少天的论文
        max_results_per_category: 每个类别的最大结果数（None 表示使用配置值）

    Returns:
        list of dict: 去重后的论文列表
    """
    if max_results_per_category is None:
        max_results_per_category = ARXIV_CONFIG["max_results_per_category"]

    cutoff_date = datetime.now() - timedelta(days=days_back)
    print(
        f"正在获取 arXiv 论文（最近 {days_back} 天，"
        f"{len(ARXIV_CONFIG['categories'])} 个类别，每类最多 {max_results_per_category} 篇）..."
    )

    client = arxiv.Client()
    papers_by_id = {}

    for category in ARXIV_CONFIG["categories"]:
        search = arxiv.Search(
            query=f"cat:{category}",
            max_results=max_results_per_category,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        for result in client.results(search):
            published = result.published.replace(tzinfo=None)
            if published < cutoff_date:
                continue

            paper_id = result.entry_id.split("/")[-1]
            if paper_id in papers_by_id:
                merged = set(papers_by_id[paper_id]["categories"])
                merged.update(result.categories)
                papers_by_id[paper_id]["categories"] = sorted(merged)
                continue

            papers_by_id[paper_id] = {
                "id": paper_id,
                "title": result.title,
                "abstract": result.summary,
                "published": result.published.isoformat(),
                "categories": result.categories,
                "authors": [author.name for author in result.authors],
                "references": [],  # arXiv API 不直接提供引用列表，需要额外引用数据源。
                "pdf_url": result.pdf_url,
            }

    papers = sorted(
        papers_by_id.values(),
        key=lambda paper: paper["published"],
        reverse=True,
    )
    print(f"✓ 获取到 {len(papers)} 篇去重论文")
    return papers


def save_papers_to_json(papers, date_str=None):
    """保存论文到 JSON 文件"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    output_path = DATA_DIR / "arxiv" / "papers" / f"{date_str}.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 论文已保存到: {output_path}")
    return output_path


def save_papers_to_db(papers):
    """保存论文到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    for paper in papers:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO papers 
                (id, title, abstract, published, categories, authors, "references")
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                paper["id"],
                paper["title"],
                paper["abstract"],
                paper["published"],
                json.dumps(paper["categories"]),
                json.dumps(paper["authors"]),
                json.dumps(paper["references"])
            ))
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"  ✗ 插入论文失败 {paper['id']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✓ 数据库插入 {inserted} 篇论文")
    return inserted


def fetch_and_store_arxiv(days_back=7):
    """获取并存储 arXiv 论文"""
    papers = fetch_arxiv_papers(days_back)
    
    if papers:
        save_papers_to_json(papers)
        save_papers_to_db(papers)
    
    return papers


if __name__ == "__main__":
    # 测试运行
    papers = fetch_and_store_arxiv(days_back=7)
    print(f"\n示例论文:")
    if papers:
        sample = papers[0]
        print(f"  标题: {sample['title']}")
        print(f"  作者: {', '.join(sample['authors'][:3])}")
        print(f"  类别: {', '.join(sample['categories'])}")
        print(f"  发布日期: {sample['published']}")
