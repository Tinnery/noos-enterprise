"""
信号检测系统主运行脚本
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from init_db import init_database
from fetch_arxiv import fetch_and_store_arxiv
from fetch_github import fetch_and_store_github
from fetch_hackernews import fetch_and_store_hackernews
from detect_signals import SignalDetector


def run_data_collection(days_back=7, skip_github=False, skip_hackernews=False):
    """
    运行数据采集
    
    Args:
        days_back: 获取最近多少天的数据
        skip_github: 是否跳过 GitHub 数据采集
        skip_hackernews: 是否跳过 Hacker News 数据采集
    """
    print("\n" + "=" * 60)
    print("阶段 1: 数据采集")
    print("=" * 60)
    
    # 1. 初始化数据库
    init_database()
    
    # 2. 获取 arXiv 论文
    print("\n--- arXiv 论文 ---")
    arxiv_papers = fetch_and_store_arxiv(days_back)
    
    # 3. 获取 GitHub 项目
    if not skip_github:
        print("\n--- GitHub 项目 ---")
        github_repos = fetch_and_store_github()
    else:
        print("\n跳过 GitHub 数据采集")
    
    # 4. 获取 Hacker News 数据
    if not skip_hackernews:
        print("\n--- Hacker News 数据 ---")
        hn_stories = fetch_and_store_hackernews(fetch_comments_for_top=10)
    else:
        print("\n跳过 Hacker News 数据采集")
    
    print("\n✓ 数据采集完成")


def run_signal_detection():
    """运行信号检测"""
    print("\n" + "=" * 60)
    print("阶段 2: 信号检测")
    print("=" * 60)
    
    detector = SignalDetector()
    
    try:
        signals = detector.run_all_detections()
        
        if signals:
            print("\n" + "=" * 60)
            print("检测到的信号（按类型分组）:")
            print("=" * 60)
            
            # 按类型分组
            signals_by_type = {}
            for signal in signals:
                signal_type = signal["signal_type"]
                if signal_type not in signals_by_type:
                    signals_by_type[signal_type] = []
                signals_by_type[signal_type].append(signal)
            
            # 打印每个类型的信号
            for signal_type, type_signals in signals_by_type.items():
                print(f"\n【{signal_type}】({len(type_signals)} 个)")
                
                for i, signal in enumerate(type_signals[:5], 1):  # 只显示前 5 个
                    if signal_type == "citation_anomaly":
                        print(f"  {i}. {signal['title']}")
                        print(f"     引用数: {signal['citation_count']}, 类别多样性: {signal['category_diversity']}")
                        print(f"     置信度: {signal['confidence']:.2f}")
                    
                    elif signal_type == "github_trending":
                        print(f"  {i}. {signal['repo']}")
                        print(f"     {signal['description'][:80]}...")
                        print(f"     Stars: {signal['current_stars']}, 增长: {signal['recent_growth']:.1f}/天")
                        print(f"     Z-score: {signal['z_score']:.2f}, 置信度: {signal['confidence']:.2f}")
                    
                    elif signal_type == "abandonment_narrative":
                        print(f"  {i}. 工具: {signal['tool']}")
                        print(f"     提及次数: {signal['frequency']}")
                        print(f"     置信度: {signal['confidence']:.2f}")
                    
                    elif signal_type == "recurring_topic":
                        print(f"  {i}. 话题: {signal['topic']}")
                        print(f"     涉及社区: {', '.join(signal['communities'])}")
                        print(f"     出现次数: {signal['occurrences']}")
                        print(f"     置信度: {signal['confidence']:.2f}")
                
                if len(type_signals) > 5:
                    print(f"  ... 还有 {len(type_signals) - 5} 个信号")
        
        return signals
        
    finally:
        detector.close()


def generate_report(signals, output_path=None):
    """
    生成信号检测报告
    
    Args:
        signals: 信号列表
        output_path: 输出文件路径（None 则使用默认路径）
    """
    if output_path is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = Path(__file__).parent.parent / "data" / "signals" / f"report_{date_str}.md"
    
    print(f"\n生成报告: {output_path}")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# 信号检测报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**检测到的信号总数**: {len(signals)}\n\n")
        
        f.write("---\n\n")
        
        # 按类型分组
        signals_by_type = {}
        for signal in signals:
            signal_type = signal["signal_type"]
            if signal_type not in signals_by_type:
                signals_by_type[signal_type] = []
            signals_by_type[signal_type].append(signal)
        
        # 1. 引用网络异常
        if "citation_anomaly" in signals_by_type:
            f.write("## 1. 引用网络异常\n\n")
            f.write("这些论文在短时间内被多个不相关领域的研究引用，可能代表跨领域影响。\n\n")
            
            for signal in signals_by_type["citation_anomaly"][:10]:
                f.write(f"### {signal['title']}\n\n")
                f.write(f"- **引用数**: {signal['citation_count']}\n")
                f.write(f"- **类别多样性**: {signal['category_diversity']}\n")
                f.write(f"- **涉及类别**: {', '.join(signal['categories'][:5])}\n")
                f.write(f"- **异常分数**: {signal['anomaly_score']}\n")
                f.write(f"- **置信度**: {signal['confidence']:.2f}\n\n")
        
        # 2. GitHub Trending
        if "github_trending" in signals_by_type:
            f.write("## 2. GitHub Trending 项目\n\n")
            f.write("这些项目在 10-100 星范围内出现异常增长，可能代表新兴技术。\n\n")
            
            for signal in signals_by_type["github_trending"][:10]:
                f.write(f"### {signal['repo']}\n\n")
                f.write(f"- **描述**: {signal['description']}\n")
                f.write(f"- **语言**: {signal['language']}\n")
                f.write(f"- **当前 Stars**: {signal['current_stars']}\n")
                f.write(f"- **日均增长**: {signal['recent_growth']:.1f}\n")
                f.write(f"- **Z-score**: {signal['z_score']:.2f}\n")
                f.write(f"- **置信度**: {signal['confidence']:.2f}\n\n")
        
        # 3. 放弃叙事
        if "abandonment_narrative" in signals_by_type:
            f.write("## 3. 放弃叙事\n\n")
            f.write('这些工具被多次提及"放弃"或"迁移"，可能代表技术衰退信号。\n\n')
            
            for signal in signals_by_type["abandonment_narrative"][:10]:
                f.write(f"### {signal['tool']}\n\n")
                f.write(f"- **提及次数**: {signal['frequency']}\n")
                f.write(f"- **置信度**: {signal['confidence']:.2f}\n")
                f.write(f"- **示例**:\n")
                for example in signal['examples'][:2]:
                    f.write(f"  > {example[:200]}...\n\n")
        
        # 4. 跨社区重复话题
        if "recurring_topic" in signals_by_type:
            f.write("## 4. 跨社区重复话题\n\n")
            f.write("这些话题在多个社区中重复出现，可能代表行业关注焦点。\n\n")
            
            for signal in signals_by_type["recurring_topic"][:10]:
                f.write(f"### {signal['topic']}\n\n")
                f.write(f"- **涉及社区**: {', '.join(signal['communities'])}\n")
                f.write(f"- **出现次数**: {signal['occurrences']}\n")
                f.write(f"- **置信度**: {signal['confidence']:.2f}\n\n")
        
        # 总结
        f.write("---\n\n")
        f.write("## 总结\n\n")
        f.write(f"本次检测共发现 **{len(signals)}** 个信号，分布在 {len(signals_by_type)} 个类别中。\n\n")
        
        f.write("### 信号分布\n\n")
        for signal_type, type_signals in signals_by_type.items():
            f.write(f"- **{signal_type}**: {len(type_signals)} 个\n")
        
        f.write("\n### 高置信度信号（> 0.7）\n\n")
        high_confidence = [s for s in signals if s.get('confidence', 0) > 0.7]
        if high_confidence:
            for signal in high_confidence[:10]:
                title = signal.get('title', signal.get('tool', signal.get('topic', 'Unknown')))
                f.write(f"- {title} (置信度: {signal['confidence']:.2f})\n")
        else:
            f.write("无\n")
    
    print(f"✓ 报告已生成: {output_path}")
    return output_path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="信号检测系统")
    parser.add_argument("--days", type=int, default=7, help="获取最近多少天的数据（默认: 7）")
    parser.add_argument("--skip-github", action="store_true", help="跳过 GitHub 数据采集")
    parser.add_argument("--skip-hackernews", action="store_true", help="跳过 Hacker News 数据采集")
    parser.add_argument("--collection-only", action="store_true", help="仅运行数据采集，不检测信号")
    parser.add_argument("--detection-only", action="store_true", help="仅运行信号检测，不采集数据")
    parser.add_argument("--no-report", action="store_true", help="不生成报告")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("信号检测系统")
    print("=" * 60)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"参数: {args}")
    
    # 1. 数据采集
    if not args.detection_only:
        run_data_collection(
            days_back=args.days,
            skip_github=args.skip_github,
            skip_hackernews=args.skip_hackernews
        )
    
    # 2. 信号检测
    if not args.collection_only:
        signals = run_signal_detection()
        
        # 3. 生成报告
        if signals and not args.no_report:
            report_path = generate_report(signals)
            print(f"\n✓ 完整流程完成")
            print(f"  报告位置: {report_path}")
    else:
        print("\n✓ 数据采集完成（跳过信号检测）")


if __name__ == "__main__":
    main()
