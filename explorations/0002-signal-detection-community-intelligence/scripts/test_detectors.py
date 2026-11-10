"""
信号检测器测试套件

为每个检测器提供正向（应检测到）、负向（不应误报）和边界条件测试。
运行: python test_detectors.py
"""

import sqlite3
import json
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from detect_signals import SignalDetector
from config import ARXIV_CONFIG, GITHUB_CONFIG, DB_SCHEMA


# ── 工具函数 ─────────────────────────────────────────────────────────

def create_test_db():
    """创建临时测试数据库"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = temp_file.name
    temp_file.close()

    conn = sqlite3.connect(db_path)
    conn.executescript(DB_SCHEMA)
    conn.close()

    return db_path


def cleanup_db(db_path):
    """安全清理测试数据库"""
    try:
        Path(db_path).unlink()
    except OSError:
        pass


# ── 引用网络异常检测器 ────────────────────────────────────────────────

class TestCitationAnomaly:
    """
    检测逻辑：
    - 获取最近 7 天的引用关系
    - 对被引用论文，统计引用来源的类别多样性
    - 阈值：min_citations=3, min_categories=3, anomaly_score>=10
    - anomaly_score = citing_count × category_count
    """

    def test_positive(self):
        """正向：被 4 个不同领域引用 → 应检测到"""
        db_path = create_test_db()
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            now = datetime.now()

            # 被引用论文（不需要满足日期条件，但必须在 papers 表中存在）
            c.execute(
                "INSERT INTO papers VALUES (?,?,?,?,?,?,?)",
                ("target", "Cross-Domain Survey", "Abstract",
                 (now - timedelta(days=30)).isoformat(),
                 json.dumps(["cs.AI"]), json.dumps(["Author"]), json.dumps([])))

            # 4 篇引用论文，分别来自 4 个不同领域（均在 7 天内）
            citing_papers = [
                ("c1", "cs.LG", "ML paper"),
                ("c2", "cs.CV", "Vision paper"),
                ("c3", "cs.CL", "NLP paper"),
                ("c4", "cs.RO", "Robotics paper"),
            ]
            for pid, cat, title in citing_papers:
                c.execute(
                    "INSERT INTO papers VALUES (?,?,?,?,?,?,?)",
                    (pid, title, "Abstract", now.isoformat(),
                     json.dumps([cat]), json.dumps(["Author"]), json.dumps([])))
                c.execute(
                    "INSERT INTO citations VALUES (?,?)",
                    (pid, "target"))

            conn.commit()
            conn.close()

            detector = SignalDetector(db_path)
            results = detector.detect_citation_anomalies()
            detector.close()

            assert len(results) == 1, f"应检测到 1 个异常，实际 {len(results)}"
            assert results[0]["paper_id"] == "target"
            assert results[0]["citation_count"] >= 4
            # score = 4 papers × 4 categories = 16
            assert results[0]["anomaly_score"] >= 10
            assert 0 <= results[0]["confidence"] <= 1
            print("  ✓ 正向测试通过：跨领域引用被正确检测")
        finally:
            cleanup_db(db_path)

    def test_negative(self):
        """负向：仅被 2 个领域引用 → 不应检测到"""
        db_path = create_test_db()
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            now = datetime.now()

            c.execute(
                "INSERT INTO papers VALUES (?,?,?,?,?,?,?)",
                ("target2", "Narrow Paper", "Abstract",
                 now.isoformat(), json.dumps(["cs.AI"]),
                 json.dumps(["Author"]), json.dumps([])))

            # 4 篇引用论文，但只来自 2 个领域
            for pid, cat in [("c1", "cs.AI"), ("c2", "cs.AI"),
                             ("c3", "cs.LG"), ("c4", "cs.LG")]:
                c.execute(
                    "INSERT INTO papers VALUES (?,?,?,?,?,?,?)",
                    (pid, f"Paper {pid}", "Abstract", now.isoformat(),
                     json.dumps([cat]), json.dumps(["Author"]), json.dumps([])))
                c.execute(
                    "INSERT INTO citations VALUES (?,?)",
                    (pid, "target2"))

            conn.commit()
            conn.close()

            detector = SignalDetector(db_path)
            results = detector.detect_citation_anomalies()
            detector.close()

            # categories={cs.AI, cs.LG} → len=2 < min_categories(3) → 不检测
            assert len(results) == 0, f"不应检测到异常，实际 {len(results)}"
            print("  ✓ 负向测试通过：同类别引用未误报")
        finally:
            cleanup_db(db_path)

    def test_empty_citations(self):
        """边界：citations 表为空 → 返回空"""
        db_path = create_test_db()
        try:
            detector = SignalDetector(db_path)
            results = detector.detect_citation_anomalies()
            detector.close()

            assert len(results) == 0
            print("  ✓ 边界测试通过：空 citations 表正确返回空")
        finally:
            cleanup_db(db_path)


# ── GitHub Trending 检测器 ────────────────────────────────────────────

class TestGitHubTrending:
    """
    检测逻辑：
    - 筛选 stars 在 [10, 100] 范围的 repo
    - 需要 ≥14 天 star 历史（7 天近期 + 7 天历史基准）
    - 历史基准排除最近 7 天，避免异常值污染
    - Z-score = (recent_mean - historical_mean) / historical_std
    - 阈值：z_score > 2.0 且 recent_growth >= 5
    """

    def test_positive(self):
        """正向：最近 7 天异常增长（历史 mean≈2, recent=100）"""
        db_path = create_test_db()
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            now = datetime.now()

            c.execute(
                "INSERT INTO github_repos VALUES (?,?,?,?,?,?,?,?)",
                ("test/hot", "Hot repo", "Python", 50, 10,
                 now.isoformat(), now.isoformat(), json.dumps(["test"])))

            # 60 天数据：前 53 天 daily 1-3（有波动），后 7 天 daily 100
            for i in range(60):
                date = (now - timedelta(days=60 - i)).strftime("%Y-%m-%d")
                daily = 100 if i >= 53 else (i % 3) + 1
                c.execute(
                    "INSERT INTO star_history VALUES (?,?,?)",
                    ("test/hot", date, daily))

            conn.commit()
            conn.close()

            detector = SignalDetector(db_path)
            results = detector.detect_github_trending()
            detector.close()

            assert len(results) >= 1, "应检测到异常增长"
            repo = next(r for r in results if r["repo"] == "test/hot")
            assert repo["z_score"] > 2.0, f"Z-score 应 > 2.0，实际 {repo['z_score']:.2f}"
            assert repo["recent_growth"] >= 5
            print(f"  ✓ 正向测试通过：Z-score={repo['z_score']:.2f}")
        finally:
            cleanup_db(db_path)

    def test_negative(self):
        """负向：稳定增长（历史 mean≈2, recent≈2）→ 不应检测到"""
        db_path = create_test_db()
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            now = datetime.now()

            c.execute(
                "INSERT INTO github_repos VALUES (?,?,?,?,?,?,?,?)",
                ("test/stable", "Stable repo", "Python", 50, 10,
                 now.isoformat(), now.isoformat(), json.dumps(["test"])))

            # 60 天稳定增长：1, 3, 1, 3... → mean≈2 全程一致
            for i in range(60):
                date = (now - timedelta(days=60 - i)).strftime("%Y-%m-%d")
                daily = 1 if i % 2 == 0 else 3
                c.execute(
                    "INSERT INTO star_history VALUES (?,?,?)",
                    ("test/stable", date, daily))

            conn.commit()
            conn.close()

            detector = SignalDetector(db_path)
            results = detector.detect_github_trending()
            detector.close()

            # recent_mean ≈ historical_mean → z_score ≈ 0 < 2.0
            assert not any(r["repo"] == "test/stable" for r in results), \
                "稳定增长不应被检测为 trending"
            print("  ✓ 负向测试通过：稳定增长未误报")
        finally:
            cleanup_db(db_path)

    def test_boundary_enough_history(self):
        """边界：恰好 14 天历史（7 天基准 + 7 天近期）→ 应正常检测"""
        db_path = create_test_db()
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            now = datetime.now()

            c.execute(
                "INSERT INTO github_repos VALUES (?,?,?,?,?,?,?,?)",
                ("test/boundary14", "Boundary", "Python", 50, 10,
                 now.isoformat(), now.isoformat(), json.dumps(["test"])))

            # 恰好 14 天：前 7 天 daily 1-2，后 7 天 daily 50
            for i in range(14):
                date = (now - timedelta(days=14 - i)).strftime("%Y-%m-%d")
                daily = 50 if i >= 7 else (i % 2) + 1
                c.execute(
                    "INSERT INTO star_history VALUES (?,?,?)",
                    ("test/boundary14", date, daily))

            conn.commit()
            conn.close()

            detector = SignalDetector(db_path)
            results = detector.detect_github_trending()
            detector.close()

            assert any(r["repo"] == "test/boundary14" for r in results), \
                "14 天数据应能正常检测"
            print("  ✓ 边界测试通过：14 天数据正常检测")
        finally:
            cleanup_db(db_path)

    def test_boundary_insufficient_history(self):
        """边界：仅 13 天历史（6 天基准）→ 应跳过"""
        db_path = create_test_db()
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            now = datetime.now()

            c.execute(
                "INSERT INTO github_repos VALUES (?,?,?,?,?,?,?,?)",
                ("test/short", "Short history", "Python", 50, 10,
                 now.isoformat(), now.isoformat(), json.dumps(["test"])))

            # 仅 13 天：historical_data = 13-7 = 6 天 < 7 天最低要求
            for i in range(13):
                date = (now - timedelta(days=13 - i)).strftime("%Y-%m-%d")
                daily = 50 if i >= 6 else (i % 2) + 1
                c.execute(
                    "INSERT INTO star_history VALUES (?,?,?)",
                    ("test/short", date, daily))

            conn.commit()
            conn.close()

            detector = SignalDetector(db_path)
            results = detector.detect_github_trending()
            detector.close()

            assert not any(r["repo"] == "test/short" for r in results), \
                "历史不足 7 天应被跳过"
            print("  ✓ 边界测试通过：历史不足 7 天正确跳过")
        finally:
            cleanup_db(db_path)


# ── 放弃叙事检测器 ────────────────────────────────────────────────────

class TestAbandonmentNarrative:
    """
    检测逻辑：
    - 正则匹配"放弃/迁移/替代"类模式，提取工具名
    - 阈值：min_mentions=3
    - 支持直接传入 texts 或从 DB 查询
    """

    def test_positive(self):
        """正向：5 条文本提到放弃 WordPress → 应检测到"""
        db_path = create_test_db()
        try:
            detector = SignalDetector(db_path)

            texts = [
                "I migrate from WordPress to Ghost",
                "Switched from WordPress to static site",
                "We abandon WordPress after years",
                "Looking for WordPress alternative",
                "Moved away from WordPress recently",
            ]
            results = detector.detect_abandonment_narratives(texts=texts)
            detector.close()

            assert len(results) > 0, "应检测到放弃叙事"
            wp = next((r for r in results if r["tool"].lower() == "wordpress"), None)
            assert wp is not None, f"应检测到 WordPress，实际检测到: {[r['tool'] for r in results]}"
            assert wp["frequency"] >= 5
            assert 0 <= wp["confidence"] <= 1
            print(f"  ✓ 正向测试通过：WordPress frequency={wp['frequency']}")
        finally:
            cleanup_db(db_path)

    def test_negative(self):
        """负向：中性技术讨论 → 不应误报"""
        db_path = create_test_db()
        try:
            detector = SignalDetector(db_path)

            texts = [
                "Python is great for data science",
                "Rust has excellent memory safety",
                "Go is perfect for microservices",
                "TypeScript improves JavaScript development",
            ]
            results = detector.detect_abandonment_narratives(texts=texts)
            detector.close()

            assert len(results) == 0, f"中性文本不应触发检测，实际: {results}"
            print("  ✓ 负向测试通过：中性文本未误报")
        finally:
            cleanup_db(db_path)

    def test_boundary_below_threshold(self):
        """边界：仅 2 次提及（阈值 3）→ 不应检测到"""
        db_path = create_test_db()
        try:
            detector = SignalDetector(db_path)

            texts = [
                "I migrated from Emacs to Vim",
                "Switched from Emacs to Neovim",
                "Rust is great for systems programming",
                "Python has excellent libraries",
            ]
            results = detector.detect_abandonment_narratives(texts=texts)
            detector.close()

            emacs = next((r for r in results if r["tool"].lower() == "emacs"), None)
            assert emacs is None, \
                f"Emacs 仅 2 次提及（< min_mentions 3），不应检测到，实际 frequency={emacs['frequency'] if emacs else 'N/A'}"
            print("  ✓ 边界测试通过：低于阈值未触发")
        finally:
            cleanup_db(db_path)


# ── 跨社区重复话题检测器 ──────────────────────────────────────────────

class TestRecurringTopic:
    """
    检测逻辑：
    - 从 HN stories 和 GitHub repos 提取关键词（≥3 字母，非停用词）
    - 阈值：min_communities=2（出现在两个来源）, min_occurrences=5
    """

    def test_positive(self):
        """正向：相同关键词出现在两个社区，总频次 ≥5 → 应检测到"""
        db_path = create_test_db()
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            now_date = datetime.now().strftime("%Y-%m-%d")
            now_dt = datetime.now().isoformat()

            # HN 帖子：5 条都含 "machine" 和 "learning"
            for i in range(5):
                c.execute(
                    "INSERT INTO hn_stories VALUES (?,?,?,?,?,?,?,?)",
                    (200 + i, f"machine learning advances {i}",
                     f"https://example.com/{i}", 50, f"user{i}",
                     int(datetime.now().timestamp()), 10, now_date))

            # GitHub 项目：5 条都含 "machine" 和 "learning"
            for i in range(5):
                c.execute(
                    "INSERT INTO github_repos VALUES (?,?,?,?,?,?,?,?)",
                    (f"ml/repo{i}", f"machine learning framework {i}",
                     "Python", 50, 10, now_dt, now_dt, json.dumps(["ml"])))

            conn.commit()
            conn.close()

            detector = SignalDetector(db_path)
            results = detector.detect_recurring_topics()
            detector.close()

            assert len(results) > 0, "应检测到跨社区重复话题"
            topics = {r["topic"] for r in results}
            assert "machine" in topics, f"'machine' 应在检测结果中，实际: {topics}"
            assert "learning" in topics, f"'learning' 应在检测结果中，实际: {topics}"

            ml_topic = next(r for r in results if r["topic"] == "machine")
            assert len(ml_topic["communities"]) >= 2
            assert ml_topic["occurrences"] >= 5
            print(f"  ✓ 正向测试通过：检测到 {len(results)} 个共同话题")
        finally:
            cleanup_db(db_path)

    def test_negative(self):
        """负向：数据库为空 → 不应检测到"""
        db_path = create_test_db()
        try:
            detector = SignalDetector(db_path)
            results = detector.detect_recurring_topics()
            detector.close()

            assert len(results) == 0, "空数据库应返回空结果"
            print("  ✓ 负向测试通过：空数据库正确返回空")
        finally:
            cleanup_db(db_path)

    def test_boundary_below_threshold(self):
        """边界：关键词出现在两个社区但总频次 <5 → 不应检测到"""
        db_path = create_test_db()
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            now_date = datetime.now().strftime("%Y-%m-%d")
            now_dt = datetime.now().isoformat()

            # HN：2 条含 "neural" 和 "network"
            for i in range(2):
                c.execute(
                    "INSERT INTO hn_stories VALUES (?,?,?,?,?,?,?,?)",
                    (300 + i, f"neural network research {i}",
                     f"https://example.com/{i}", 50, f"user{i}",
                     int(datetime.now().timestamp()), 10, now_date))

            # GitHub：2 条含 "neural" 和 "network"
            for i in range(2):
                c.execute(
                    "INSERT INTO github_repos VALUES (?,?,?,?,?,?,?,?)",
                    (f"nn/repo{i}", f"neural network library {i}",
                     "Python", 50, 10, now_dt, now_dt, json.dumps(["ml"])))

            conn.commit()
            conn.close()

            detector = SignalDetector(db_path)
            results = detector.detect_recurring_topics()
            detector.close()

            # "neural" 总频次 = 2(HN) + 2(GitHub) = 4 < min_occurrences(5)
            nn_topics = [r for r in results
                         if r["topic"] in ("neural", "network")]
            assert len(nn_topics) == 0, \
                f"频次不足不应被检测，实际: {[r['topic'] for r in nn_topics]}"
            print("  ✓ 边界测试通过：频次不足未触发")
        finally:
            cleanup_db(db_path)


class TestResearchCoverageConfiguration:
    """配置层覆盖 AI 与相邻软件工程分支，避免采集范围退化为少数 AI 热门标签。"""

    def test_arxiv_categories_cover_ai_and_core_software_fields(self):
        required = {
            "cs.AI", "cs.LG", "cs.CL", "cs.CV",
            "cs.CR", "cs.SE", "cs.DB", "cs.DC", "cs.PL", "cs.IR",
        }
        configured = set(ARXIV_CONFIG["categories"])
        assert required.issubset(configured), (
            f"arXiv 类别覆盖缺失: {sorted(required - configured)}"
        )
        assert len(ARXIV_CONFIG["categories"]) == len(configured), \
            "arXiv 类别不应重复"
        assert ARXIV_CONFIG["max_results_per_category"] > 0

    def test_github_topics_cover_ai_security_and_engineering(self):
        required = {
            "artificial-intelligence", "ai-agents", "inference", "rag",
            "llm-evaluation", "cybersecurity", "software-supply-chain",
            "developer-tools", "data-engineering", "observability",
        }
        configured = set(GITHUB_CONFIG["topics"])
        assert required.issubset(configured), (
            f"GitHub Topic 覆盖缺失: {sorted(required - configured)}"
        )
        assert len(GITHUB_CONFIG["topics"]) == len(configured), \
            "GitHub Topic 不应重复"
        assert GITHUB_CONFIG["max_pages_per_topic"] == 1
        assert GITHUB_CONFIG["max_repos_per_topic"] > 0
        assert GITHUB_CONFIG["search_delay_seconds"] > 0




# ── 主入口 ────────────────────────────────────────────────────────────

def main():
    """运行所有测试"""
    print("=" * 60)
    print("信号检测器测试套件")
    print("=" * 60)

    test_classes = [
        ("引用网络异常检测器", TestCitationAnomaly),
        ("GitHub Trending 检测器", TestGitHubTrending),
        ("放弃叙事检测器", TestAbandonmentNarrative),
        ("跨社区重复话题检测器", TestRecurringTopic),
        ("研究领域采集配置", TestResearchCoverageConfiguration),
    ]

    passed = 0
    failed = 0

    for name, cls in test_classes:
        print(f"\n{'─' * 50}")
        print(f"  {name}")
        print(f"{'─' * 50}")
        instance = cls()
        for method_name in sorted(dir(instance)):
            if not method_name.startswith("test_"):
                continue
            method = getattr(instance, method_name)
            label = method_name.replace("test_", "")
            try:
                method()
                passed += 1
            except AssertionError as e:
                print(f"  ✗ {label}: {e}")
                failed += 1
            except Exception as e:
                print(f"  ✗ {label}: 异常 - {e}")
                import traceback
                traceback.print_exc()
                failed += 1

    print(f"\n{'=' * 60}")
    print(f"测试结果: {passed} 通过, {failed} 失败, 共 {passed + failed} 个")
    print(f"{'=' * 60}")

    if failed > 0:
        sys.exit(1)
    print("✓ 所有测试通过")


if __name__ == "__main__":
    main()
