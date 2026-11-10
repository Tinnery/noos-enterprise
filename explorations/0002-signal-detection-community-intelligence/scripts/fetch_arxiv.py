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


def fetch_arxiv_papers(days_back=7, max_results=None):
    """
    获取 arXiv 论文
    
    Args:
        days_back: 获取最近多少天的论文
        max_results: 最大结果数（None 表示使用配置值）
    
    Returns:
        list of dict: 论文列表
    """
    if max_results is None:
        max_results = ARXIV_CONFIG["max_results"]
    
    # 构建查询
    categories = " OR ".join([f"cat:{cat}" for cat in ARXIV_CONFIG["categories"]])
    
    # 搜索论文
    search = arxiv.Search(
        query=categories,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    papers = []
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    print(f"正在获取 arXiv 论文（最近 {days_back} 天）...")
    
    # arxiv 4.x API: 使用 Client 执行搜索
    client = arxiv.Client()
    for result in client.results(search):
        # 检查日期
        if result.published.replace(tzinfo=None) < cutoff_date:
            continue
        
        paper = {
            "id": result.entry_id.split("/")[-1],
            "title": result.title,
            "abstract": result.summary,
            "published": result.published.isoformat(),
            "categories": result.categories,
            "authors": [author.name for author in result.authors],
            "references": [],  # arXiv API 不直接提供引用列表，需要额外数据源（如 Semantic Scholar API）
            "pdf_url": result.pdf_url,
        }
        papers.append(paper)
    
    print(f"✓ 获取到 {len(papers)} 篇论文")
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
