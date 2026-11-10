"""
Layer 3: 实践参与追踪模块

追踪社区参与机会、记录参与历史、计算融入度指标
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import requests

from config import DB_PATH, DATA_DIR


class ParticipationTracker:
    """实践参与追踪器"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.data_dir = DATA_DIR
        self.participation_dir = self.data_dir / "participation"
        self.participation_dir.mkdir(exist_ok=True)
        
        # 参与类型定义
        self.participation_types = {
            "pull_request": "提交 PR（修复 bug、添加功能、改进文档）",
            "issue_comment": "在 Issue 中评论",
            "discussion": "参与 GitHub Discussions",
            "blog_post": "撰写技术博客",
            "stack_overflow": "回答 Stack Overflow 问题",
            "hn_comment": "在 Hacker News 参与讨论",
            "open_source": "开源自己的工具",
            "community_event": "参与社区活动（线上/线下）",
        }
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def find_participation_opportunities(
        self,
        github_token: Optional[str] = None,
        max_issues_per_repo: int = 5
    ) -> List[Dict]:
        """
        查找参与机会
        
        从已采集的 GitHub 项目中查找：
        1. good first issues
        2. help wanted issues
        3. 需要文档改进的 issues
        
        Args:
            github_token: GitHub API token（可选）
            max_issues_per_repo: 每个项目最多返回几个 issue
        
        Returns:
            参与机会列表
        """
        print("\n🔍 查找参与机会...")
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # 获取已采集的项目
        cursor.execute("""
            SELECT repo, stars, language, topics, description
            FROM github_repos
            WHERE stars > 0
            ORDER BY stars DESC
            LIMIT 50
        """)
        
        repos = cursor.fetchall()
        print(f"  从 {len(repos)} 个项目中查找...")
        
        opportunities = []
        
        for repo_row in repos:
            repo = repo_row["repo"]
            
            # 查找 good first issues
            try:
                # 使用 GitHub API 查找 issues
                url = f"https://api.github.com/repos/{repo}/issues"
                headers = {"Accept": "application/vnd.github.v3+json"}
                if github_token:
                    headers["Authorization"] = f"token {github_token}"
                
                params = {
                    "labels": "good first issue,help wanted",
                    "state": "open",
                    "per_page": max_issues_per_repo,
                    "sort": "created",
                    "direction": "desc"
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    issues = response.json()
                    
                    for issue in issues[:max_issues_per_repo]:
                        # 跳过 PR
                        if "pull_request" in issue:
                            continue
                        
                        opportunity = {
                            "repo": repo,
                            "issue_number": issue["number"],
                            "title": issue["title"],
                            "url": issue["html_url"],
                            "labels": [l["name"] for l in issue.get("labels", [])],
                            "created_at": issue["created_at"],
                            "body_preview": (issue.get("body") or "")[:200],
                            "difficulty": self._estimate_difficulty(issue),
                            "opportunity_type": self._classify_opportunity(issue),
                        }
                        opportunities.append(opportunity)
                
                # 速率限制
                import time
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ⚠ 获取 {repo} issues 失败: {e}")
                continue
        
        conn.close()
        
        # 按难度和机会类型排序
        opportunities.sort(key=lambda x: (
            {"easy": 0, "medium": 1, "hard": 2}.get(x["difficulty"], 1),
            {"good_first_issue": 0, "help_wanted": 1, "documentation": 2}.get(x["opportunity_type"], 3)
        ))
        
        print(f"  ✓ 找到 {len(opportunities)} 个参与机会")
        
        # 保存机会
        self._save_opportunities(opportunities)
        
        return opportunities
    
    def _estimate_difficulty(self, issue: Dict) -> str:
        """估算 issue 难度"""
        labels = [l["name"].lower() for l in issue.get("labels", [])]
        body = (issue.get("body") or "").lower()
        
        # 简单指标
        if any(x in labels for x in ["good first issue", "beginner", "easy"]):
            return "easy"
        elif any(x in labels for x in ["help wanted", "intermediate"]):
            return "medium"
        elif any(x in body for x in ["simple", "easy", "beginner", "straightforward"]):
            return "easy"
        elif any(x in body for x in ["complex", "difficult", "advanced"]):
            return "hard"
        else:
            return "medium"
    
    def _classify_opportunity(self, issue: Dict) -> str:
        """分类机会类型"""
        labels = [l["name"].lower() for l in issue.get("labels", [])]
        
        if "good first issue" in labels:
            return "good_first_issue"
        elif "help wanted" in labels:
            return "help_wanted"
        elif any(x in labels for x in ["documentation", "docs"]):
            return "documentation"
        elif any(x in labels for x in ["bug", "bugfix"]):
            return "bug_fix"
        else:
            return "general"
    
    def _save_opportunities(self, opportunities: List[Dict]):
        """保存参与机会"""
        output_file = self.participation_dir / "opportunities.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "discovered_at": datetime.now().isoformat(),
                "count": len(opportunities),
                "opportunities": opportunities
            }, f, ensure_ascii=False, indent=2)
    
    def record_participation(
        self,
        participation_type: str,
        target: str,
        url: str,
        description: str,
        date: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        记录一次参与
        
        Args:
            participation_type: 参与类型（pull_request, blog_post 等）
            target: 目标（项目名、博客标题等）
            url: 链接
            description: 描述
            date: 日期（默认今天）
            metadata: 额外元数据
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # 创建参与记录表（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participation_type TEXT,
                target TEXT,
                url TEXT,
                description TEXT,
                participation_date DATE,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        date = date or datetime.now().strftime("%Y-%m-%d")
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO participation_history
            (participation_type, target, url, description, participation_date, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (participation_type, target, url, description, date, metadata_json))
        
        conn.commit()
        conn.close()
        
        print(f"✓ 记录参与: {participation_type} - {target}")
    
    def get_participation_history(self, days: int = 90) -> List[Dict]:
        """
        获取参与历史
        
        Args:
            days: 查询最近多少天
        
        Returns:
            参与记录列表
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # 确保表存在
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participation_type TEXT,
                target TEXT,
                url TEXT,
                description TEXT,
                participation_date DATE,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cursor.execute("""
            SELECT * FROM participation_history
            WHERE participation_date >= ?
            ORDER BY participation_date DESC
        """, (cutoff_date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def calculate_engagement_score(self) -> Dict:
        """
        计算社区融入度指标
        
        Returns:
            融入度指标字典
        """
        print("\n📊 计算社区融入度...")
        
        history = self.get_participation_history(days=90)
        
        # 按类型统计
        type_counts = defaultdict(int)
        for record in history:
            type_counts[record["participation_type"]] += 1
        
        # 计算总分（加权）
        weights = {
            "pull_request": 10,      # PR 权重最高
            "blog_post": 8,
            "open_source": 8,
            "stack_overflow": 5,
            "discussion": 3,
            "issue_comment": 2,
            "hn_comment": 2,
            "community_event": 5,
        }
        
        total_score = sum(
            type_counts.get(p_type, 0) * weight
            for p_type, weight in weights.items()
        )
        
        # 计算各维度得分
        max_score_per_type = {p_type: 5 * weight for p_type, weight in weights.items()}
        
        dimension_scores = {}
        for p_type, weight in weights.items():
            count = type_counts.get(p_type, 0)
            max_score = max_score_per_type[p_type]
            score = min(count * weight, max_score)
            dimension_scores[p_type] = {
                "count": count,
                "score": score,
                "max_score": max_score,
                "percentage": (score / max_score * 100) if max_score > 0 else 0
            }
        
        # 总体评级
        max_total = sum(max_score_per_type.values())
        overall_percentage = (total_score / max_total * 100) if max_total > 0 else 0
        
        if overall_percentage >= 80:
            grade = "A"
            level = "核心贡献者"
        elif overall_percentage >= 60:
            grade = "B"
            level = "活跃成员"
        elif overall_percentage >= 40:
            grade = "C"
            level = "定期参与者"
        elif overall_percentage >= 20:
            grade = "D"
            level = "偶尔参与"
        else:
            grade = "E"
            level = "观察者"
        
        metrics = {
            "total_score": total_score,
            "max_score": max_total,
            "percentage": overall_percentage,
            "grade": grade,
            "level": level,
            "dimensions": dimension_scores,
            "total_participations": len(history),
            "period_days": 90,
        }
        
        print(f"  总得分: {total_score}/{max_total} ({overall_percentage:.1f}%)")
        print(f"  评级: {grade} - {level}")
        print(f"  参与次数: {len(history)}")
        
        return metrics
    
    def generate_strategy_recommendations(
        self,
        engagement_metrics: Dict,
        opportunities: List[Dict]
    ) -> List[Dict]:
        """
        生成参与策略建议
        
        Args:
            engagement_metrics: 融入度指标
            opportunities: 参与机会列表
        
        Returns:
            策略建议列表
        """
        print("\n💡 生成参与策略建议...")
        
        recommendations = []
        
        dimensions = engagement_metrics["dimensions"]
        current_level = engagement_metrics["level"]
        
        # 1. 根据当前水平建议
        if current_level == "观察者":
            recommendations.append({
                "priority": "high",
                "category": "入门",
                "action": "从 good first issue 开始",
                "reason": "当前参与度较低，建议从简单的 issue 开始建立存在感",
                "target_count": 3,
                "timeline": "2 周内"
            })
            recommendations.append({
                "priority": "medium",
                "category": "学习",
                "action": "在感兴趣的项目中评论 issue",
                "reason": "通过评论展示理解和兴趣，建立初步联系",
                "target_count": 5,
                "timeline": "1 个月内"
            })
        
        elif current_level == "偶尔参与":
            recommendations.append({
                "priority": "high",
                "category": "提升",
                "action": "提交第一个 PR",
                "reason": "已有基础参与，应尝试实质性贡献",
                "target_count": 1,
                "timeline": "1 个月内"
            })
            recommendations.append({
                "priority": "medium",
                "category": "扩展",
                "action": "撰写技术博客分享经验",
                "reason": "通过写作展示专业能力",
                "target_count": 1,
                "timeline": "2 个月内"
            })
        
        elif current_level == "定期参与者":
            recommendations.append({
                "priority": "high",
                "category": "深化",
                "action": "在 1 个核心项目建立持续贡献",
                "reason": "从广泛参与转向深度贡献",
                "target_count": 1,
                "timeline": "3 个月内"
            })
        
        # 2. 根据机会推荐具体目标
        easy_opportunities = [o for o in opportunities if o["difficulty"] == "easy"]
        if easy_opportunities:
            top_3 = easy_opportunities[:3]
            recommendations.append({
                "priority": "high",
                "category": "具体目标",
                "action": "推荐参与的 good first issues",
                "reason": f"找到 {len(easy_opportunities)} 个适合入门的 issue",
                "targets": [
                    {"repo": o["repo"], "title": o["title"], "url": o["url"]}
                    for o in top_3
                ]
            })
        
        # 3. 根据薄弱维度建议
        if dimensions.get("pull_request", {}).get("count", 0) == 0:
            recommendations.append({
                "priority": "high",
                "category": "补强",
                "action": "尝试提交 PR",
                "reason": "PR 是展示技术能力的重要方式，当前尚未有 PR 记录",
            })
        
        if dimensions.get("blog_post", {}).get("count", 0) == 0:
            recommendations.append({
                "priority": "medium",
                "category": "补强",
                "action": "撰写技术博客",
                "reason": "技术博客可以展示思考深度，建立专业形象",
            })
        
        # 限制建议数量
        recommendations = recommendations[:5]
        
        print(f"  生成 {len(recommendations)} 条建议")
        
        return recommendations
    
    def generate_report(
        self,
        opportunities: List[Dict],
        engagement_metrics: Dict,
        recommendations: List[Dict]
    ) -> str:
        """
        生成实践参与报告
        
        Args:
            opportunities: 参与机会
            engagement_metrics: 融入度指标
            recommendations: 策略建议
        
        Returns:
            Markdown 格式的报告
        """
        print("\n📝 生成实践参与报告...")
        
        report_lines = []
        report_lines.append("# 实践参与报告")
        report_lines.append("")
        report_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report_lines.append("")
        
        # 1. 融入度概览
        report_lines.append("## 1. 社区融入度")
        report_lines.append("")
        report_lines.append(f"- **总得分**: {engagement_metrics['total_score']}/{engagement_metrics['max_score']} ({engagement_metrics['percentage']:.1f}%)")
        report_lines.append(f"- **评级**: {engagement_metrics['grade']} - {engagement_metrics['level']}")
        report_lines.append(f"- **参与次数**: {engagement_metrics['total_participations']}（最近 90 天）")
        report_lines.append("")
        
        # 各维度得分
        report_lines.append("### 各维度得分")
        report_lines.append("")
        report_lines.append("| 维度 | 次数 | 得分 | 满分 | 占比 |")
        report_lines.append("|------|------|------|------|------|")
        for dim_name, dim_data in engagement_metrics["dimensions"].items():
            report_lines.append(
                f"| {dim_name} | {dim_data['count']} | {dim_data['score']:.0f} | "
                f"{dim_data['max_score']:.0f} | {dim_data['percentage']:.0f}% |"
            )
        report_lines.append("")
        
        # 2. 参与机会
        report_lines.append("## 2. 参与机会")
        report_lines.append("")
        report_lines.append(f"发现 **{len(opportunities)}** 个参与机会：")
        report_lines.append("")
        
        if opportunities:
            # 按难度分组
            by_difficulty = defaultdict(list)
            for opp in opportunities:
                by_difficulty[opp["difficulty"]].append(opp)
            
            for difficulty in ["easy", "medium", "hard"]:
                opps = by_difficulty.get(difficulty, [])
                if opps:
                    report_lines.append(f"### {difficulty.capitalize()} 难度（{len(opps)} 个）")
                    report_lines.append("")
                    for opp in opps[:5]:  # 每个难度最多显示 5 个
                        report_lines.append(f"- **{opp['repo']}** #{opp['issue_number']}: {opp['title']}")
                        report_lines.append(f"  - 链接: {opp['url']}")
                        report_lines.append(f"  - 标签: {', '.join(opp['labels'])}")
                    report_lines.append("")
        
        # 3. 策略建议
        report_lines.append("## 3. 策略建议")
        report_lines.append("")
        
        for i, rec in enumerate(recommendations, 1):
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec["priority"], "⚪")
            report_lines.append(f"### {i}. {rec['action']} {priority_emoji}")
            report_lines.append("")
            report_lines.append(f"- **类别**: {rec['category']}")
            report_lines.append(f"- **原因**: {rec['reason']}")
            if "target_count" in rec:
                report_lines.append(f"- **目标**: {rec['target_count']} 次")
            if "timeline" in rec:
                report_lines.append(f"- **时间线**: {rec['timeline']}")
            if "targets" in rec:
                report_lines.append(f"- **推荐目标**:")
                for t in rec["targets"]:
                    report_lines.append(f"  - [{t['repo']}] {t['title']}")
            report_lines.append("")
        
        # 4. 成功标准追踪
        report_lines.append("## 4. 成功标准追踪")
        report_lines.append("")
        report_lines.append("根据 README 定义的成功标准：")
        report_lines.append("")
        
        pr_count = engagement_metrics["dimensions"].get("pull_request", {}).get("count", 0)
        blog_count = engagement_metrics["dimensions"].get("blog_post", {}).get("count", 0)
        
        report_lines.append(f"- [ ] 在 3 个核心社区建立可见度（当前评级: {engagement_metrics['level']}）")
        report_lines.append(f"- [{'x' if pr_count >= 1 else ' '}] 至少 1 个 PR 被合并到目标项目（当前: {pr_count}）")
        report_lines.append(f"- [{'x' if blog_count >= 1 else ' '}] 至少 1 篇技术博客获得社区反馈（当前: {blog_count}）")
        report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        # 保存报告
        report_path = self.data_dir / "signals" / "participation_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print(f"  ✓ 报告已保存: {report_path}")
        
        return report_content
    
    def run_full_analysis(self, github_token: Optional[str] = None) -> str:
        """
        运行完整的实践参与分析
        
        Args:
            github_token: GitHub API token（可选）
        
        Returns:
            报告内容
        """
        print("\n" + "=" * 60)
        print("Layer 3: 实践参与追踪")
        print("=" * 60)
        
        # 1. 查找参与机会
        opportunities = self.find_participation_opportunities(github_token=github_token)
        
        # 2. 计算融入度
        engagement_metrics = self.calculate_engagement_score()
        
        # 3. 生成策略建议
        recommendations = self.generate_strategy_recommendations(
            engagement_metrics, opportunities
        )
        
        # 4. 生成报告
        report = self.generate_report(opportunities, engagement_metrics, recommendations)
        
        print("\n✓ Layer 3 分析完成")
        
        return report


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="实践参与追踪")
    parser.add_argument("--github-token", type=str, help="GitHub API token")
    
    args = parser.parse_args()
    
    tracker = ParticipationTracker()
    tracker.run_full_analysis(github_token=args.github_token)


if __name__ == "__main__":
    main()
