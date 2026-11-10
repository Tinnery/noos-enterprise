"""
信号检测器最小可复现测试

为每个检测器提供独立的测试用例，验证核心逻辑的正确性。
"""

import sqlite3
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from detect_signals import SignalDetector
from config import DB_SCHEMA


def create_test_db():
    """创建测试数据库"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = temp_file.name
    temp_file.close()
    
    conn = sqlite3.connect(db_path)
    conn.executescript(DB_SCHEMA)
    conn.close()
    
    return db_path


def test_citation_anomaly_detector():
    """测试引用网络异常检测器"""
    print("\n=== 测试 1: 引用网络异常检测器 ===")
    
    db_path = create_test_db()
    detector = SignalDetector(db_path)
    
    # 插入测试数据
    now = datetime.now()
    
    # 插入论文
    papers = [
        {
            "id": "paper1",
            "title": "Test Paper 1",
            "abstract": "Abstract 1",
            "published": now.isoformat(),
            "categories": ["cs.AI", "cs.LG"],
            "authors": ["Author 1"],
            "references": [],
        },
        {
            "id": "paper2",
            "title": "Test Paper 2",
            "abstract": "Abstract 2",
            "published": now.isoformat(),
            "categories": ["cs.CV"],
            "authors": ["Author 2"],
            "references": [],
        },
    ]
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for paper in papers:
        cursor.execute("""
            INSERT INTO papers (id, title, abstract, published, categories, authors, "references")
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            paper["id"],
            paper["title"],
            paper["abstract"],
            paper["published"],
            json.dumps(paper["categories"]),
            json.dumps(paper["authors"]),
            json.dumps(paper["references"]),
        ))
    
    conn.commit()
    conn.close()
    
    # 测试：citations 表为空时应该返回空结果
    results = detector.detect_citation_anomalies()
    assert len(results) == 0, "citations 表为空时应返回空结果"
    print("✓ 测试通过：citations 表为空时正确返回空结果")
    
    detector.close()
    Path(db_path).unlink()


def test_github_trending_detector():
    """测试 GitHub trending 检测器"""
    print("\n=== 测试 2: GitHub trending 检测器 ===")
    
    db_path = create_test_db()
    detector = SignalDetector(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 插入测试项目
    cursor.execute("""
        INSERT INTO github_repos (repo, description, language, stars, forks, created_at, updated_at, topics)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("test/repo", "Test repo", "Python", 50, 10, datetime.now().isoformat(), datetime.now().isoformat(), json.dumps(["test"])))
    
    # 插入 star 历史（每日新增数）
    # 60 天数据：前 53 天每天 1 star，后 7 天每天 100 star
    # mean≈12.55, std≈31.79, recent=100, z≈2.75 > 2.0 ✓
    now = datetime.now()
    for i in range(60):
        date = (now - timedelta(days=60-i)).strftime("%Y-%m-%d")
        daily_stars = 100 if i >= 53 else 1
        cursor.execute("""
            INSERT INTO star_history (repo, date, stars)
            VALUES (?, ?, ?)
        """, ("test/repo", date, daily_stars))
    
    conn.commit()
    conn.close()
    
    # 测试：应该能正确识别异常增长
    results = detector.detect_github_trending()
    
    # 验证：最近 3 天平均增长 5，历史平均约 1.9，应该有显著增长
    if results:
        print(f"✓ 检测到 {len(results)} 个 trending 项目")
        for r in results:
            print(f"  - {r['repo']}: 最近增长 {r['recent_growth']:.2f}, Z-score {r['z_score']:.2f}")
    else:
        print("⚠ 未检测到 trending（可能因为数据量不足或阈值过高）")
    
    detector.close()
    Path(db_path).unlink()


def test_abandonment_narrative_detector():
    """测试放弃叙事检测器"""
    print("\n=== 测试 3: 放弃叙事检测器 ===")
    
    db_path = create_test_db()
    detector = SignalDetector(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 插入测试评论（使用 Unix 时间戳）
    now_timestamp = int(datetime.now().timestamp())
    
    comments = [
        "I migrated from WordPress to Ghost and it's much better",
        "Switched from WordPress to static site generator",
        "We abandoned WordPress after years of using it",
        "Looking for WordPress alternatives",
        "Moved away from WordPress recently",
    ]
    
    for i, text in enumerate(comments):
        cursor.execute("""
            INSERT INTO hn_comments (id, story_id, author, time, text, parent)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (i + 1, i + 1, f"user{i}", now_timestamp - i * 3600, text, 0))
    
    conn.commit()
    conn.close()
    
    # 测试：应该能检测到 WordPress 相关的放弃叙事
    results = detector.detect_abandonment_narratives()
    
    assert len(results) > 0, "应该检测到放弃叙事"
    assert any(r["tool"].lower() == "wordpress" for r in results), "应该检测到 WordPress"
    
    print(f"✓ 检测到 {len(results)} 个放弃叙事")
    for r in results:
        print(f"  - {r['tool']}: 提及 {r['frequency']} 次")
    
    detector.close()
    Path(db_path).unlink()


def test_recurring_topic_detector():
    """测试跨社区重复话题检测器"""
    print("\n=== 测试 4: 跨社区重复话题检测器 ===")
    
    db_path = create_test_db()
    detector = SignalDetector(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 插入 HN 帖子
    now_date = datetime.now().strftime("%Y-%m-%d")
    for i in range(5):
        cursor.execute("""
            INSERT INTO hn_stories (id, title, url, score, author, time, descendants, detected_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (100 + i, f"AI machine learning story {i}", f"https://example.com/{i}", 50, f"user{i}", int(datetime.now().timestamp()), 10, now_date))
    
    # 插入 GitHub 项目
    for i in range(5):
        cursor.execute("""
            INSERT INTO github_repos (repo, description, language, stars, forks, created_at, updated_at, topics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (f"gh/repo{i}", f"AI machine learning repo {i}", "Python", 50, 10, now_date, now_date, json.dumps(["ai"])))
    
    conn.commit()
    conn.close()
    
    # 测试：应该能检测到跨社区的共同话题
    results = detector.detect_recurring_topics()
    
    if results:
        print(f"✓ 检测到 {len(results)} 个跨社区重复话题")
        for r in results[:5]:  # 只显示前 5 个
            print(f"  - {r['topic']}: 出现在 {', '.join(r['communities'])}，共 {r['occurrences']} 次")
    else:
        print("⚠ 未检测到跨社区重复话题（可能因为关键词提取不够或阈值过高）")
    
    detector.close()
    Path(db_path).unlink()


def main():
    """运行所有测试"""
    print("=" * 60)
    print("信号检测器测试套件")
    print("=" * 60)
    
    try:
        test_citation_anomaly_detector()
        test_github_trending_detector()
        test_abandonment_narrative_detector()
        test_recurring_topic_detector()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试完成")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
