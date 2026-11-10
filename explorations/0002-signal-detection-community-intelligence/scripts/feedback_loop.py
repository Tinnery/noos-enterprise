"""
Layer 4: 反馈循环模块

追踪预测准确性、测量信息时滞、评估决策质量、迭代优化方法论
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import statistics

from config import DB_PATH, DATA_DIR


class FeedbackLoop:
    """反馈循环管理器"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.data_dir = DATA_DIR
        self.feedback_dir = self.data_dir / "feedback"
        self.feedback_dir.mkdir(exist_ok=True)
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def track_signal_outcomes(self, lookback_days: int = 180) -> Dict:
        """
        追踪信号结果
        
        检查历史信号是否最终成为趋势（通过后续数据验证）
        
        Args:
            lookback_days: 回溯多少天
        
        Returns:
            信号结果统计
        """
        print("\n🔍 追踪信号结果...")
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        
        # 获取所有历史信号
        cursor.execute("""
            SELECT 
                id,
                signal_type,
                source,
                description,
                detected_date,
                confidence,
                status,
                outcome,
                validated_date
            FROM signals
            WHERE detected_date >= ?
            ORDER BY detected_date DESC
        """, (cutoff_date,))
        
        signals = cursor.fetchall()
        conn.close()
        
        print(f"  找到 {len(signals)} 个信号（最近 {lookback_days} 天）")
        
        # 分类统计
        outcomes = {
            "validated": [],      # 已验证（成为趋势）
            "invalidated": [],    # 已否定（未成为趋势）
            "pending": [],        # 待验证
            "uncertain": [],      # 不确定
        }
        
        for signal in signals:
            signal_dict = dict(signal)
            status = signal_dict.get("status", "detected")
            
            if status == "validated":
                outcomes["validated"].append(signal_dict)
            elif status == "invalidated":
                outcomes["invalidated"].append(signal_dict)
            elif status == "uncertain":
                outcomes["uncertain"].append(signal_dict)
            else:
                outcomes["pending"].append(signal_dict)
        
        # 输出统计
        print(f"  ✓ 已验证: {len(outcomes['validated'])}")
        print(f"  ✗ 已否定: {len(outcomes['invalidated'])}")
        print(f"  ⏳ 待验证: {len(outcomes['pending'])}")
        print(f"  ? 不确定: {len(outcomes['uncertain'])}")
        
        return outcomes
    
    def calculate_prediction_accuracy(self, outcomes: Dict) -> Dict:
        """
        计算预测准确性
        
        Args:
            outcomes: 信号结果字典
        
        Returns:
            准确性指标
        """
        print("\n📊 计算预测准确性...")
        
        validated = outcomes["validated"]
        invalidated = outcomes["invalidated"]
        total_decided = len(validated) + len(invalidated)
        
        if total_decided == 0:
            print("  ⚠ 没有已决策的信号，无法计算准确性")
            return {
                "accuracy": 0.0,
                "total_decided": 0,
                "validated": 0,
                "invalidated": 0,
                "precision": 0.0,
                "recall": 0.0,
            }
        
        # 基础准确性
        accuracy = len(validated) / total_decided if total_decided > 0 else 0.0
        
        # 按信号类型统计
        type_stats = defaultdict(lambda: {"validated": 0, "invalidated": 0})
        
        for signal in validated:
            type_stats[signal["signal_type"]]["validated"] += 1
        for signal in invalidated:
            type_stats[signal["signal_type"]]["invalidated"] += 1
        
        # 计算每种类型的准确性
        type_accuracy = {}
        for sig_type, stats in type_stats.items():
            total = stats["validated"] + stats["invalidated"]
            if total > 0:
                type_accuracy[sig_type] = {
                    "accuracy": stats["validated"] / total,
                    "validated": stats["validated"],
                    "invalidated": stats["invalidated"],
                    "total": total,
                }
        
        # 按置信度分组分析
        confidence_groups = {
            "high": {"range": (0.7, 1.0), "validated": 0, "invalidated": 0},
            "medium": {"range": (0.4, 0.7), "validated": 0, "invalidated": 0},
            "low": {"range": (0.0, 0.4), "validated": 0, "invalidated": 0},
        }
        
        for signal in validated + invalidated:
            confidence = signal.get("confidence", 0.5)
            is_validated = signal in validated
            
            for group_name, group_data in confidence_groups.items():
                if group_data["range"][0] <= confidence < group_data["range"][1]:
                    if is_validated:
                        group_data["validated"] += 1
                    else:
                        group_data["invalidated"] += 1
                    break
        
        # 计算每组的准确性
        confidence_accuracy = {}
        for group_name, group_data in confidence_groups.items():
            total = group_data["validated"] + group_data["invalidated"]
            if total > 0:
                confidence_accuracy[group_name] = {
                    "accuracy": group_data["validated"] / total,
                    "validated": group_data["validated"],
                    "invalidated": group_data["invalidated"],
                    "total": total,
                }
        
        metrics = {
            "accuracy": accuracy,
            "total_decided": total_decided,
            "validated": len(validated),
            "invalidated": len(invalidated),
            "type_accuracy": type_accuracy,
            "confidence_accuracy": confidence_accuracy,
        }
        
        print(f"  总体准确性: {accuracy:.1%} ({len(validated)}/{total_decided})")
        
        if type_accuracy:
            print(f"  按类型:")
            for sig_type, acc_data in type_accuracy.items():
                print(f"    - {sig_type}: {acc_data['accuracy']:.1%} ({acc_data['total']} 个)")
        
        return metrics
    
    def measure_information_lag(self, lookback_days: int = 180) -> Dict:
        """
        测量信息时滞
        
        从信号检测到被验证（或被主流媒体关注）的时间差
        
        Args:
            lookback_days: 回溯多少天
        
        Returns:
            时滞指标
        """
        print("\n⏱️  测量信息时滞...")
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        
        # 获取已验证的信号（有 validated_date）
        cursor.execute("""
            SELECT 
                detected_date,
                validated_date,
                signal_type,
                confidence
            FROM signals
            WHERE status = 'validated'
              AND validated_date IS NOT NULL
              AND detected_date >= ?
        """, (cutoff_date,))
        
        validated_signals = cursor.fetchall()
        conn.close()
        
        if not validated_signals:
            print("  ⚠ 没有已验证的信号，无法测量时滞")
            return {
                "average_lag_days": None,
                "median_lag_days": None,
                "min_lag_days": None,
                "max_lag_days": None,
                "sample_size": 0,
            }
        
        # 计算时滞
        lags = []
        for signal in validated_signals:
            detected = datetime.strptime(signal["detected_date"], "%Y-%m-%d")
            validated = datetime.strptime(signal["validated_date"], "%Y-%m-%d")
            lag_days = (validated - detected).days
            
            if lag_days >= 0:  # 忽略负值（数据错误）
                lags.append(lag_days)
        
        if not lags:
            return {
                "average_lag_days": None,
                "median_lag_days": None,
                "min_lag_days": None,
                "max_lag_days": None,
                "sample_size": 0,
            }
        
        metrics = {
            "average_lag_days": statistics.mean(lags),
            "median_lag_days": statistics.median(lags),
            "min_lag_days": min(lags),
            "max_lag_days": max(lags),
            "sample_size": len(lags),
            "lags": lags,  # 保留原始数据用于分析
        }
        
        print(f"  平均时滞: {metrics['average_lag_days']:.1f} 天")
        print(f"  中位数: {metrics['median_lag_days']:.1f} 天")
        print(f"  范围: {metrics['min_lag_days']} - {metrics['max_lag_days']} 天")
        print(f"  样本量: {len(lags)}")
        
        # 目标对比
        target_lag = 7  # README 中的目标
        if metrics["median_lag_days"] <= target_lag:
            print(f"  ✓ 达到目标（< {target_lag} 天）")
        else:
            print(f"  ⚠ 未达到目标（目标 < {target_lag} 天）")
        
        return metrics
    
    def evaluate_decision_quality(self, outcomes: Dict, accuracy_metrics: Dict) -> Dict:
        """
        评估决策质量
        
        基于信号做出的方向判断，最终被验证正确的比例
        
        Args:
            outcomes: 信号结果
            accuracy_metrics: 准确性指标
        
        Returns:
            决策质量评估
        """
        print("\n🎯 评估决策质量...")
        
        validated = outcomes["validated"]
        invalidated = outcomes["invalidated"]
        pending = outcomes["pending"]
        
        total_signals = len(validated) + len(invalidated) + len(pending)
        total_decided = len(validated) + len(invalidated)
        
        # 决策质量分数
        quality_score = accuracy_metrics["accuracy"] * 100 if total_decided > 0 else 0
        
        # 决策成熟度
        if total_decided == 0:
            maturity = "未开始"
            maturity_score = 0
        elif total_decided < 10:
            maturity = "早期"
            maturity_score = 1
        elif total_decided < 30:
            maturity = "发展中"
            maturity_score = 2
        elif total_decided < 50:
            maturity = "成熟"
            maturity_score = 3
        else:
            maturity = "充分"
            maturity_score = 4
        
        # 决策分布
        decision_distribution = {
            "validated_pct": len(validated) / total_decided * 100 if total_decided > 0 else 0,
            "invalidated_pct": len(invalidated) / total_decided * 100 if total_decided > 0 else 0,
            "pending_pct": len(pending) / total_signals * 100 if total_signals > 0 else 0,
        }
        
        # 按来源分析
        source_stats = defaultdict(lambda: {"validated": 0, "invalidated": 0})
        for signal in validated:
            source_stats[signal["source"]]["validated"] += 1
        for signal in invalidated:
            source_stats[signal["source"]]["invalidated"] += 1
        
        source_quality = {}
        for source, stats in source_stats.items():
            total = stats["validated"] + stats["invalidated"]
            if total > 0:
                source_quality[source] = {
                    "accuracy": stats["validated"] / total,
                    "total": total,
                }
        
        evaluation = {
            "quality_score": quality_score,
            "maturity": maturity,
            "maturity_score": maturity_score,
            "total_signals": total_signals,
            "total_decided": total_decided,
            "decision_distribution": decision_distribution,
            "source_quality": source_quality,
            "target_score": 70,  # README 中的目标
        }
        
        print(f"  决策质量分数: {quality_score:.1f}/100")
        print(f"  决策成熟度: {maturity}")
        print(f"  已决策信号: {total_decided}/{total_signals}")
        
        if source_quality:
            print(f"  按来源:")
            for source, quality in source_quality.items():
                print(f"    - {source}: {quality['accuracy']:.1%} ({quality['total']} 个)")
        
        # 目标对比
        if quality_score >= evaluation["target_score"]:
            print(f"  ✓ 达到目标（≥ {evaluation['target_score']} 分）")
        else:
            print(f"  ⚠ 未达到目标（目标 ≥ {evaluation['target_score']} 分）")
        
        return evaluation
    
    def validate_pending_signals(
        self,
        lookback_days: int = 90,
        auto_validate: bool = False
    ) -> int:
        """
        验证待验证信号
        
        通过检查后续数据来判断信号是否成为趋势
        
        Args:
            lookback_days: 检查最近多少天的数据
            auto_validate: 是否自动验证（False 则只标记候选）
        
        Returns:
            验证的信号数量
        """
        print("\n🔬 验证待验证信号...")
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        
        # 获取待验证信号
        cursor.execute("""
            SELECT id, signal_type, source, description, detected_date, confidence
            FROM signals
            WHERE status = 'detected'
              AND detected_date >= ?
        """, (cutoff_date,))
        
        pending_signals = cursor.fetchall()
        
        if not pending_signals:
            print("  没有待验证的信号")
            conn.close()
            return 0
        
        print(f"  找到 {len(pending_signals)} 个待验证信号")
        
        validated_count = 0
        
        for signal in pending_signals:
            signal_id = signal["id"]
            signal_type = signal["signal_type"]
            description = signal["description"]
            
            # 简单的验证逻辑（实际应该更复杂）
            # 这里只是示例，需要根据实际情况调整
            
            validation_result = self._validate_signal_by_type(
                signal_type, description, signal["detected_date"]
            )
            
            if validation_result == "validated":
                if auto_validate:
                    cursor.execute("""
                        UPDATE signals
                        SET status = 'validated',
                            validated_date = ?
                        WHERE id = ?
                    """, (datetime.now().strftime("%Y-%m-%d"), signal_id))
                    validated_count += 1
                else:
                    print(f"    候选验证: {description[:50]}...")
            
            elif validation_result == "invalidated":
                if auto_validate:
                    cursor.execute("""
                        UPDATE signals
                        SET status = 'invalidated',
                            validated_date = ?
                        WHERE id = ?
                    """, (datetime.now().strftime("%Y-%m-%d"), signal_id))
        
        if auto_validate:
            conn.commit()
            print(f"  ✓ 自动验证了 {validated_count} 个信号")
        else:
            print(f"  发现 {validated_count} 个候选验证信号（未自动更新）")
        
        conn.close()
        
        return validated_count
    
    def _validate_signal_by_type(
        self,
        signal_type: str,
        description: str,
        detected_date: str
    ) -> str:
        """
        根据信号类型验证
        
        这是一个简化的验证逻辑，实际应该更复杂
        
        Returns:
            "validated", "invalidated", 或 "pending"
        """
        # 这里只是占位逻辑，实际验证应该基于后续数据
        
        # 示例：检查 GitHub trending 信号
        if signal_type == "github_trending":
            # 应该检查该项目后续是否持续增长
            # 这里返回 "pending" 表示需要手动验证
            return "pending"
        
        # 示例：检查引用网络异常
        elif signal_type == "citation_anomaly":
            # 应该检查论文后续引用是否持续增长
            return "pending"
        
        # 默认返回 pending
        return "pending"
    
    def generate_methodology_recommendations(
        self,
        accuracy_metrics: Dict,
        lag_metrics: Dict,
        quality_metrics: Dict
    ) -> List[Dict]:
        """
        生成方法论优化建议
        
        Args:
            accuracy_metrics: 准确性指标
            lag_metrics: 时滞指标
            quality_metrics: 质量指标
        
        Returns:
            优化建议列表
        """
        print("\n💡 生成方法论优化建议...")
        
        recommendations = []
        
        # 1. 基于准确性的建议
        if accuracy_metrics["total_decided"] > 0:
            accuracy = accuracy_metrics["accuracy"]
            
            if accuracy < 0.5:
                recommendations.append({
                    "priority": "high",
                    "category": "准确性",
                    "issue": f"预测准确性较低（{accuracy:.1%}）",
                    "suggestion": "提高信号检测阈值，减少误报",
                    "action": "调整 SIGNAL_THRESHOLDS 配置，增加最小提及次数和置信度要求"
                })
            elif accuracy > 0.8:
                recommendations.append({
                    "priority": "medium",
                    "category": "准确性",
                    "issue": f"预测准确性很高（{accuracy:.1%}）",
                    "suggestion": "可能过于保守，漏掉了弱信号",
                    "action": "适当降低检测阈值，捕获更多早期信号"
                })
            
            # 按类型分析
            type_accuracy = accuracy_metrics.get("type_accuracy", {})
            weak_types = [
                (t, data) for t, data in type_accuracy.items()
                if data["accuracy"] < 0.4 and data["total"] >= 3
            ]
            
            if weak_types:
                recommendations.append({
                    "priority": "medium",
                    "category": "信号类型",
                    "issue": f"{len(weak_types)} 种信号类型准确性较低",
                    "suggestion": "针对这些类型优化检测算法",
                    "action": f"重点改进: {', '.join(t[0] for t in weak_types)}"
                })
        
        # 2. 基于时滞的建议
        if lag_metrics["median_lag_days"] is not None:
            median_lag = lag_metrics["median_lag_days"]
            
            if median_lag > 14:
                recommendations.append({
                    "priority": "high",
                    "category": "时滞",
                    "issue": f"信息时滞较长（中位数 {median_lag:.0f} 天）",
                    "suggestion": "提高数据采集频率",
                    "action": "将采集频率从每日改为每 12 小时，或增加实时数据源"
                })
            elif median_lag < 3:
                recommendations.append({
                    "priority": "low",
                    "category": "时滞",
                    "issue": f"信息时滞很短（中位数 {median_lag:.0f} 天）",
                    "suggestion": "表现优秀，保持当前策略",
                    "action": "继续监控，确保可持续性"
                })
        
        # 3. 基于决策质量的建议
        if quality_metrics["maturity_score"] < 2:
            recommendations.append({
                "priority": "high",
                "category": "成熟度",
                "issue": f"决策成熟度较低（{quality_metrics['maturity']}）",
                "suggestion": "积累更多验证数据",
                "action": "定期运行验证流程，建立信号结果追踪机制"
            })
        
        # 4. 基于来源的建议
        source_quality = quality_metrics.get("source_quality", {})
        weak_sources = [
            (s, data) for s, data in source_quality.items()
            if data["accuracy"] < 0.4 and data["total"] >= 3
        ]
        
        if weak_sources:
            recommendations.append({
                "priority": "medium",
                "category": "数据源",
                "issue": f"{len(weak_sources)} 个数据源质量较低",
                "suggestion": "优化这些来源的信号检测",
                "action": f"重点改进: {', '.join(s[0] for s in weak_sources)}"
            })
        
        # 限制建议数量
        recommendations = recommendations[:5]
        
        print(f"  生成 {len(recommendations)} 条建议")
        
        return recommendations
    
    def generate_report(
        self,
        outcomes: Dict,
        accuracy_metrics: Dict,
        lag_metrics: Dict,
        quality_metrics: Dict,
        recommendations: List[Dict]
    ) -> str:
        """
        生成反馈循环报告
        
        Args:
            outcomes: 信号结果
            accuracy_metrics: 准确性指标
            lag_metrics: 时滞指标
            quality_metrics: 质量指标
            recommendations: 优化建议
        
        Returns:
            Markdown 格式的报告
        """
        print("\n📝 生成反馈循环报告...")
        
        report_lines = []
        report_lines.append("# 反馈循环报告")
        report_lines.append("")
        report_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report_lines.append("")
        
        # 1. 预测准确性
        report_lines.append("## 1. 预测准确性")
        report_lines.append("")
        
        if accuracy_metrics["total_decided"] > 0:
            report_lines.append(f"- **总体准确性**: {accuracy_metrics['accuracy']:.1%} ({accuracy_metrics['validated']}/{accuracy_metrics['total_decided']})")
            report_lines.append(f"- **已验证**: {accuracy_metrics['validated']} 个信号")
            report_lines.append(f"- **已否定**: {accuracy_metrics['invalidated']} 个信号")
            report_lines.append("")
            
            # 按类型
            if accuracy_metrics.get("type_accuracy"):
                report_lines.append("### 按信号类型")
                report_lines.append("")
                report_lines.append("| 类型 | 准确性 | 已验证 | 已否定 | 总数 |")
                report_lines.append("|------|--------|--------|--------|------|")
                for sig_type, data in accuracy_metrics["type_accuracy"].items():
                    report_lines.append(
                        f"| {sig_type} | {data['accuracy']:.1%} | "
                        f"{data['validated']} | {data['invalidated']} | {data['total']} |"
                    )
                report_lines.append("")
            
            # 按置信度
            if accuracy_metrics.get("confidence_accuracy"):
                report_lines.append("### 按置信度分组")
                report_lines.append("")
                report_lines.append("| 置信度 | 准确性 | 已验证 | 已否定 | 总数 |")
                report_lines.append("|--------|--------|--------|--------|------|")
                for group, data in accuracy_metrics["confidence_accuracy"].items():
                    report_lines.append(
                        f"| {group} | {data['accuracy']:.1%} | "
                        f"{data['validated']} | {data['invalidated']} | {data['total']} |"
                    )
                report_lines.append("")
        else:
            report_lines.append("*暂无已决策的信号*")
            report_lines.append("")
        
        # 2. 信息时滞
        report_lines.append("## 2. 信息时滞")
        report_lines.append("")
        
        if lag_metrics["median_lag_days"] is not None:
            report_lines.append(f"- **平均时滞**: {lag_metrics['average_lag_days']:.1f} 天")
            report_lines.append(f"- **中位数**: {lag_metrics['median_lag_days']:.1f} 天")
            report_lines.append(f"- **范围**: {lag_metrics['min_lag_days']} - {lag_metrics['max_lag_days']} 天")
            report_lines.append(f"- **样本量**: {lag_metrics['sample_size']}")
            report_lines.append("")
            
            # 目标对比
            target = 7
            if lag_metrics["median_lag_days"] <= target:
                report_lines.append(f"✓ **达到目标**（< {target} 天）")
            else:
                report_lines.append(f"⚠ **未达到目标**（目标 < {target} 天）")
            report_lines.append("")
        else:
            report_lines.append("*暂无已验证信号的时滞数据*")
            report_lines.append("")
        
        # 3. 决策质量
        report_lines.append("## 3. 决策质量")
        report_lines.append("")
        report_lines.append(f"- **质量分数**: {quality_metrics['quality_score']:.1f}/100")
        report_lines.append(f"- **决策成熟度**: {quality_metrics['maturity']}")
        report_lines.append(f"- **总信号数**: {quality_metrics['total_signals']}")
        report_lines.append(f"- **已决策**: {quality_metrics['total_decided']}")
        report_lines.append("")
        
        # 决策分布
        dist = quality_metrics["decision_distribution"]
        report_lines.append("### 决策分布")
        report_lines.append("")
        report_lines.append(f"- 已验证: {dist['validated_pct']:.1f}%")
        report_lines.append(f"- 已否定: {dist['invalidated_pct']:.1f}%")
        report_lines.append(f"- 待验证: {dist['pending_pct']:.1f}%")
        report_lines.append("")
        
        # 按来源
        if quality_metrics.get("source_quality"):
            report_lines.append("### 按数据源")
            report_lines.append("")
            report_lines.append("| 来源 | 准确性 | 总数 |")
            report_lines.append("|------|--------|------|")
            for source, data in quality_metrics["source_quality"].items():
                report_lines.append(f"| {source} | {data['accuracy']:.1%} | {data['total']} |")
            report_lines.append("")
        
        # 目标对比
        target_score = quality_metrics["target_score"]
        if quality_metrics["quality_score"] >= target_score:
            report_lines.append(f"✓ **达到目标**（≥ {target_score} 分）")
        else:
            report_lines.append(f"⚠ **未达到目标**（目标 ≥ {target_score} 分）")
        report_lines.append("")
        
        # 4. 方法论优化建议
        report_lines.append("## 4. 方法论优化建议")
        report_lines.append("")
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec["priority"], "⚪")
                report_lines.append(f"### {i}. {rec['suggestion']} {priority_emoji}")
                report_lines.append("")
                report_lines.append(f"- **类别**: {rec['category']}")
                report_lines.append(f"- **问题**: {rec['issue']}")
                report_lines.append(f"- **行动**: {rec['action']}")
                report_lines.append("")
        else:
            report_lines.append("*暂无优化建议*")
            report_lines.append("")
        
        # 5. 成功标准追踪
        report_lines.append("## 5. 成功标准追踪")
        report_lines.append("")
        report_lines.append("根据 README 定义的成功标准：")
        report_lines.append("")
        
        # 短期目标
        report_lines.append("### 短期目标（3 个月）")
        report_lines.append("")
        
        accuracy = accuracy_metrics["accuracy"] if accuracy_metrics["total_decided"] > 0 else 0
        lag = lag_metrics["median_lag_days"] if lag_metrics["median_lag_days"] is not None else 999
        
        report_lines.append(f"- [{'x' if accuracy >= 0.5 else ' '}] 预测准确性达到 50%（当前: {accuracy:.1%}）")
        report_lines.append(f"- [{'x' if lag <= 14 else ' '}] 信息时滞 < 14 天（当前: {lag:.0f} 天）")
        report_lines.append("")
        
        # 长期目标
        report_lines.append("### 长期目标（12 个月）")
        report_lines.append("")
        report_lines.append(f"- [{'x' if accuracy >= 0.7 else ' '}] 预测准确性达到 70%（当前: {accuracy:.1%}）")
        report_lines.append(f"- [{'x' if lag <= 7 else ' '}] 信息时滞 < 7 天（当前: {lag:.0f} 天）")
        report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        # 保存报告
        report_path = self.data_dir / "signals" / "feedback_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print(f"  ✓ 报告已保存: {report_path}")
        
        return report_content
    
    def run_full_analysis(self, lookback_days: int = 180) -> str:
        """
        运行完整的反馈循环分析
        
        Args:
            lookback_days: 回溯多少天
        
        Returns:
            报告内容
        """
        print("\n" + "=" * 60)
        print("Layer 4: 反馈循环")
        print("=" * 60)
        
        # 1. 追踪信号结果
        outcomes = self.track_signal_outcomes(lookback_days)
        
        # 2. 计算预测准确性
        accuracy_metrics = self.calculate_prediction_accuracy(outcomes)
        
        # 3. 测量信息时滞
        lag_metrics = self.measure_information_lag(lookback_days)
        
        # 4. 评估决策质量
        quality_metrics = self.evaluate_decision_quality(outcomes, accuracy_metrics)
        
        # 5. 生成优化建议
        recommendations = self.generate_methodology_recommendations(
            accuracy_metrics, lag_metrics, quality_metrics
        )
        
        # 6. 生成报告
        report = self.generate_report(
            outcomes, accuracy_metrics, lag_metrics, quality_metrics, recommendations
        )
        
        print("\n✓ Layer 4 分析完成")
        
        return report


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="反馈循环分析")
    parser.add_argument("--lookback-days", type=int, default=180, help="回溯多少天（默认: 180）")
    parser.add_argument("--validate", action="store_true", help="尝试验证待验证信号")
    
    args = parser.parse_args()
    
    feedback = FeedbackLoop()
    feedback.run_full_analysis(lookback_days=args.lookback_days)


if __name__ == "__main__":
    main()
