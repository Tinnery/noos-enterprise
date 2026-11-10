"""
信号检测算法模块
"""

import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import networkx as nx
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config import DB_PATH, SIGNAL_THRESHOLDS


class SignalDetector:
    """信号检测器"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def detect_citation_anomalies(self, days_back=7):
        """
        检测引用网络异常
        
        识别在短时间内被多个不相关领域引用的论文
        
        Args:
            days_back: 检测最近多少天
        
        Returns:
            list of dict: 异常信号列表
        """
        print("正在检测引用网络异常...")
        
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        # 获取最近的引用关系
        query = """
            SELECT c.paper_id, c.cited_paper_id, p.categories, p.title
            FROM citations c
            JOIN papers p ON c.paper_id = p.id
            WHERE p.published >= ?
        """
        
        cursor = self.conn.execute(query, (cutoff_date,))
        citations = cursor.fetchall()
        
        # 构建引用图
        G = nx.DiGraph()
        paper_categories = {}
        paper_titles = {}
        
        for citation in citations:
            paper_id = citation["paper_id"]
            cited_id = citation["cited_paper_id"]
            categories = json.loads(citation["categories"]) if citation["categories"] else []
            title = citation["title"]
            
            G.add_edge(paper_id, cited_id)
            paper_categories[paper_id] = categories
            paper_titles[paper_id] = title
        
        # 检测异常
        anomalies = []
        threshold = SIGNAL_THRESHOLDS["citation_anomaly"]
        
        for node in G.nodes():
            # 获取引用该节点的论文
            citing_papers = list(G.predecessors(node))
            
            if len(citing_papers) < threshold["min_citations"]:
                continue
            
            # 计算引用来源的类别多样性
            citing_categories = set()
            for citing_paper in citing_papers:
                if citing_paper in paper_categories:
                    citing_categories.update(paper_categories[citing_paper])
            
            # 如果引用来自多个不同类别，可能是跨领域影响
            if len(citing_categories) >= threshold["min_categories"]:
                anomaly_score = len(citing_papers) * len(citing_categories)
                
                if anomaly_score >= threshold["anomaly_score_threshold"]:
                    anomalies.append({
                        "paper_id": node,
                        "title": paper_titles.get(node, "Unknown"),
                        "citation_count": len(citing_papers),
                        "category_diversity": len(citing_categories),
                        "categories": list(citing_categories),
                        "anomaly_score": anomaly_score,
                        "signal_type": "citation_anomaly",
                        "confidence": min(anomaly_score / 20.0, 1.0),
                    })
        
        # 按异常分数排序
        anomalies.sort(key=lambda x: x["anomaly_score"], reverse=True)
        
        print(f"✓ 检测到 {len(anomalies)} 个引用网络异常")
        return anomalies
    
    def detect_github_trending(self):
        """
        检测 GitHub 项目异常增长
        
        识别 10-100 星项目中 star 增长异常的项目
        
        Returns:
            list of dict: trending 信号列表
        """
        print("正在检测 GitHub trending 项目...")
        
        threshold = SIGNAL_THRESHOLDS["github_trending"]
        
        # 获取所有项目的 star 历史
        query = """
            SELECT r.repo, r.stars, r.description, r.language,
                   GROUP_CONCAT(sh.date || ':' || sh.stars, ',') as history
            FROM github_repos r
            LEFT JOIN star_history sh ON r.repo = sh.repo
            WHERE r.stars BETWEEN ? AND ?
            GROUP BY r.repo
        """
        
        cursor = self.conn.execute(
            query,
            (threshold["min_stars"], threshold["max_stars"])
        )
        repos = cursor.fetchall()
        
        trends = []
        
        for repo in repos:
            repo_name = repo["repo"]
            current_stars = repo["stars"]
            description = repo["description"]
            language = repo["language"]
            
            # 解析 star 历史
            if not repo["history"]:
                continue
            
            history = []
            for item in repo["history"].split(","):
                if ":" in item:
                    date, stars = item.split(":")
                    history.append({"date": date, "stars": int(stars)})
            
            if len(history) < 7:
                continue
            
            # 按日期排序
            history.sort(key=lambda x: x["date"])
            
            # 计算每日增长
            daily_growths = []
            for i in range(1, len(history)):
                growth = history[i]["stars"] - history[i-1]["stars"]
                daily_growths.append(growth)
            
            if not daily_growths:
                continue
            
            # 计算最近 7 天的平均增长
            recent_growth = np.mean(daily_growths[-7:])
            
            # 计算历史平均增长和标准差
            historical_mean = np.mean(daily_growths)
            historical_std = np.std(daily_growths)
            
            if historical_std == 0:
                continue
            
            # 计算 Z-score
            z_score = (recent_growth - historical_mean) / historical_std
            
            if z_score > threshold["z_score_threshold"] and recent_growth >= threshold["min_daily_growth"]:
                trends.append({
                    "repo": repo_name,
                    "description": description,
                    "language": language,
                    "current_stars": current_stars,
                    "recent_growth": recent_growth,
                    "z_score": z_score,
                    "signal_type": "github_trending",
                    "confidence": min(z_score / 5.0, 1.0),
                })
        
        # 按 Z-score 排序
        trends.sort(key=lambda x: x["z_score"], reverse=True)
        
        print(f"✓ 检测到 {len(trends)} 个 GitHub trending 项目")
        return trends
    
    def detect_abandonment_narratives(self, texts=None, days_back=7):
        """
        检测"放弃叙事"
        
        识别"放弃 X 工具"类内容
        
        Args:
            texts: 文本列表（如果为 None，从数据库获取）
            days_back: 检测最近多少天
        
        Returns:
            list of dict: 放弃叙事信号列表
        """
        print("正在检测放弃叙事...")
        
        if texts is None:
            # 从 HN 评论和帖子获取文本
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            query = """
                SELECT text FROM hn_comments
                WHERE time >= ?
                UNION
                SELECT title as text FROM hn_stories
                WHERE detected_date >= ?
            """
            
            cursor = self.conn.execute(query, (cutoff_date, cutoff_date))
            texts = [row["text"] for row in cursor.fetchall() if row["text"]]
        
        if not texts:
            print("  没有足够的文本数据")
            return []
        
        # 关键词模式
        import re
        keywords = [
            r"migrat(?:e|ing|ion) from (\w+)",
            r"switch(?:ed|ing) from (\w+)",
            r"abandon(?:ing)? (\w+)",
            r"replace(?:d|ing)? (\w+)",
            r"(\w+) alternative",
            r"better than (\w+)",
            r"moved away from (\w+)",
            r"stopped using (\w+)",
        ]
        
        # 提取工具名称
        tool_mentions = defaultdict(list)
        
        for text in texts:
            for pattern in keywords:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    tool_name = match.group(1)
                    tool_mentions[tool_name].append(text)
        
        # 识别高频工具提及
        threshold = SIGNAL_THRESHOLDS["abandonment_narrative"]
        narratives = []
        
        for tool, mentions in tool_mentions.items():
            if len(mentions) >= threshold["min_mentions"]:
                narratives.append({
                    "tool": tool,
                    "frequency": len(mentions),
                    "examples": mentions[:3],
                    "signal_type": "abandonment_narrative",
                    "confidence": min(len(mentions) / 10.0, 1.0),
                })
        
        # 按频率排序
        narratives.sort(key=lambda x: x["frequency"], reverse=True)
        
        print(f"✓ 检测到 {len(narratives)} 个放弃叙事")
        return narratives
    
    def detect_recurring_topics(self, days_back=7):
        """
        检测跨社区重复话题
        
        识别在多个社区中重复出现的主题
        
        Args:
            days_back: 检测最近多少天
        
        Returns:
            list of dict: 重复话题信号列表
        """
        print("正在检测跨社区重复话题...")
        
        threshold = SIGNAL_THRESHOLDS["recurring_topic"]
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        # 从不同来源获取数据
        sources = {
            "hackernews": [],
            "github": [],
        }
        
        # HN 帖子
        query = """
            SELECT title, score FROM hn_stories
            WHERE detected_date >= ?
        """
        cursor = self.conn.execute(query, (cutoff_date,))
        for row in cursor.fetchall():
            sources["hackernews"].append(row["title"])
        
        # GitHub 项目描述
        query = """
            SELECT description FROM github_repos
            WHERE updated_at >= ?
        """
        cursor = self.conn.execute(query, (cutoff_date,))
        for row in cursor.fetchall():
            if row["description"]:
                sources["github"].append(row["description"])
        
        # 简单的关键词提取（实际应用中应该用更复杂的方法）
        def extract_keywords(texts, top_n=20):
            """提取关键词"""
            from collections import Counter
            import re
            
            # 停用词
            stop_words = {
                "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
                "for", "of", "with", "by", "is", "are", "was", "were", "be",
                "been", "being", "have", "has", "had", "do", "does", "did",
                "will", "would", "could", "should", "may", "might", "can",
                "this", "that", "these", "those", "it", "its", "my", "your",
            }
            
            words = []
            for text in texts:
                # 提取单词
                text_words = re.findall(r"\b[a-z]{3,}\b", text.lower())
                words.extend([w for w in text_words if w not in stop_words])
            
            # 返回最常见的词
            return [word for word, count in Counter(words).most_common(top_n)]
        
        # 提取每个来源的关键词
        source_keywords = {}
        for source, texts in sources.items():
            if texts:
                source_keywords[source] = set(extract_keywords(texts))
        
        # 找出跨来源的共同关键词
        all_keywords = defaultdict(lambda: {"sources": set(), "count": 0})
        
        for source, keywords in source_keywords.items():
            for keyword in keywords:
                all_keywords[keyword]["sources"].add(source)
                all_keywords[keyword]["count"] += 1
        
        # 筛选符合条件的关键词
        recurring = []
        for keyword, data in all_keywords.items():
            if len(data["sources"]) >= threshold["min_communities"] and data["count"] >= threshold["min_occurrences"]:
                recurring.append({
                    "topic": keyword,
                    "communities": list(data["sources"]),
                    "occurrences": data["count"],
                    "signal_type": "recurring_topic",
                    "confidence": min(data["count"] / 10.0, 1.0),
                })
        
        # 按出现次数排序
        recurring.sort(key=lambda x: x["occurrences"], reverse=True)
        
        print(f"✓ 检测到 {len(recurring)} 个跨社区重复话题")
        return recurring
    
    def save_signals(self, signals):
        """保存信号到数据库"""
        if not signals:
            return 0
        
        cursor = self.conn.cursor()
        inserted = 0
        
        for signal in signals:
            try:
                cursor.execute("""
                    INSERT INTO signals 
                    (signal_type, source, description, detected_date, confidence, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal["signal_type"],
                    signal.get("source", ""),
                    signal.get("description", signal.get("title", signal.get("tool", signal.get("topic", "")))),
                    datetime.now().isoformat(),
                    signal.get("confidence", 0.5),
                    "detected",
                    json.dumps(signal)
                ))
                if cursor.rowcount > 0:
                    inserted += 1
            except Exception as e:
                print(f"  ✗ 插入信号失败: {e}")
        
        self.conn.commit()
        print(f"✓ 保存 {inserted} 个信号到数据库")
        return inserted
    
    def run_all_detections(self):
        """运行所有检测算法"""
        print("=" * 60)
        print("开始信号检测")
        print("=" * 60)
        
        all_signals = []
        
        # 1. 引用网络异常
        citation_anomalies = self.detect_citation_anomalies()
        all_signals.extend(citation_anomalies)
        
        # 2. GitHub trending
        github_trends = self.detect_github_trending()
        all_signals.extend(github_trends)
        
        # 3. 放弃叙事
        abandonment_narratives = self.detect_abandonment_narratives()
        all_signals.extend(abandonment_narratives)
        
        # 4. 跨社区重复话题
        recurring_topics = self.detect_recurring_topics()
        all_signals.extend(recurring_topics)
        
        # 保存所有信号
        if all_signals:
            self.save_signals(all_signals)
        
        print("=" * 60)
        print(f"检测完成，共发现 {len(all_signals)} 个信号")
        print("=" * 60)
        
        return all_signals
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()


if __name__ == "__main__":
    # 测试运行
    detector = SignalDetector()
    signals = detector.run_all_detections()
    
    print("\n信号摘要:")
    for signal in signals[:10]:
        print(f"  - [{signal['signal_type']}] {signal.get('title', signal.get('tool', signal.get('topic', 'Unknown')))}")
        print(f"    置信度: {signal.get('confidence', 0):.2f}")
    
    detector.close()
