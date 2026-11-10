"""
Layer 2: 社区结构分析模块

从 Layer 1 采集的数据中构建社会网络，识别关键人物、社区结构和跨社区传播路径。

网络构建策略：
1. 论文作者协作网络：节点=作者，边=共同出现在一篇论文中
2. GitHub 项目主题网络：节点=项目，边=共享 topic（二部图投影）
3. HN 讨论网络：节点=用户，边=评论回复关系
4. 跨源融合网络：通过共同主题连接不同来源的实体
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

from config import DB_PATH


class CommunityAnalyzer:
    """社区结构分析器"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.networks = {}  # 存储构建的网络
        self.key_figures = []
        self.communities = []
    
    # ================================================================
    # 网络构建
    # ================================================================
    
    def build_author_collaboration_network(self):
        """
        从论文作者列表构建协作网络
        
        节点：作者
        边：共同出现在一篇论文中（权重 = 共同论文数）
        
        Returns:
            nx.Graph: 协作网络
        """
        print("正在构建论文作者协作网络...")
        
        cursor = self.conn.execute("SELECT authors FROM papers WHERE authors IS NOT NULL")
        rows = cursor.fetchall()
        
        G = nx.Graph()
        paper_count = 0
        
        for row in rows:
            try:
                authors = json.loads(row["authors"])
            except (json.JSONDecodeError, TypeError):
                continue
            
            if not authors or len(authors) < 2:
                # 即使只有一个作者，也添加节点
                if authors:
                    G.add_node(authors[0], source="arxiv")
                continue
            
            paper_count += 1
            
            # 为这篇论文的所有作者对添加边
            for i, author_a in enumerate(authors):
                G.add_node(author_a, source="arxiv")
                for author_b in authors[i + 1:]:
                    if G.has_edge(author_a, author_b):
                        G[author_a][author_b]["weight"] += 1
                    else:
                        G.add_edge(author_a, author_b, weight=1)
        
        print(f"  ✓ 协作网络: {G.number_of_nodes()} 个作者, {G.number_of_edges()} 条边")
        print(f"    基于 {paper_count} 篇多作者论文")
        
        if G.number_of_nodes() > 0:
            # 统计连通分量
            components = list(nx.connected_components(G))
            print(f"    连通分量: {len(components)} 个")
            if components:
                largest = max(components, key=len)
                print(f"    最大连通分量: {len(largest)} 个节点")
        
        self.networks["author_collaboration"] = G
        return G
    
    def build_project_topic_network(self):
        """
        从 GitHub 项目 topics 构建项目关联网络
        
        方法：构建 项目-主题 二部图，然后投影为项目关联网络
        节点：GitHub 项目
        边：共享至少一个 topic（权重 = 共享 topic 数 / Jaccard 相似度）
        
        Returns:
            nx.Graph: 项目关联网络
        """
        print("正在构建 GitHub 项目主题网络...")
        
        cursor = self.conn.execute("""
            SELECT repo, topics, language, stars, forks
            FROM github_repos
            WHERE topics IS NOT NULL AND topics != '[]'
        """)
        rows = cursor.fetchall()
        
        # 构建 项目 -> topics 映射
        repo_topics = {}
        topic_repos = defaultdict(set)
        
        for row in rows:
            repo = row["repo"]
            try:
                topics = json.loads(row["topics"])
            except (json.JSONDecodeError, TypeError):
                continue
            
            if not topics:
                continue
            
            repo_topics[repo] = {
                "topics": set(topics),
                "language": row["language"],
                "stars": row["stars"],
                "forks": row["forks"],
            }
            
            for topic in topics:
                topic_repos[topic].add(repo)
        
        # 构建项目关联网络
        G = nx.Graph()
        
        # 添加节点
        for repo, info in repo_topics.items():
            G.add_node(repo, **info)
        
        # 通过共享 topic 连接项目
        # 为避免 O(n^2) 遍历，通过 topic 中转
        edge_weights = defaultdict(int)
        
        for topic, repos in topic_repos.items():
            repos_list = list(repos)
            # 限制每个 topic 最多连接 50 个项目（避免过于流行的 topic 导致完全图）
            if len(repos_list) > 50:
                # 按 star 数排序，取 top 50
                repos_list.sort(
                    key=lambda r: repo_topics[r].get("stars", 0) if r in repo_topics else 0,
                    reverse=True
                )
                repos_list = repos_list[:50]
            
            for i, repo_a in enumerate(repos_list):
                for repo_b in repos_list[i + 1:]:
                    pair = tuple(sorted([repo_a, repo_b]))
                    edge_weights[pair] += 1
        
        # 添加边
        for (repo_a, repo_b), shared_count in edge_weights.items():
            if shared_count >= 1:
                # 计算 Jaccard 相似度作为权重
                topics_a = repo_topics.get(repo_a, {}).get("topics", set())
                topics_b = repo_topics.get(repo_b, {}).get("topics", set())
                
                if topics_a and topics_b:
                    jaccard = len(topics_a & topics_b) / len(topics_a | topics_b)
                else:
                    jaccard = 0
                
                G.add_edge(repo_a, repo_b, weight=shared_count, jaccard=jaccard)
        
        print(f"  ✓ 项目网络: {G.number_of_nodes()} 个项目, {G.number_of_edges()} 条边")
        print(f"    基于 {len(topic_repos)} 个不同 topic")
        
        if G.number_of_nodes() > 0:
            components = list(nx.connected_components(G))
            print(f"    连通分量: {len(components)} 个")
            if components:
                largest = max(components, key=len)
                print(f"    最大连通分量: {len(largest)} 个节点")
        
        self.networks["project_topic"] = G
        return G
    
    def build_discussion_network(self):
        """
        从 HN 评论构建讨论网络
        
        节点：用户
        边：A 回复了 B 的评论（有向图）
        
        Returns:
            nx.DiGraph: 讨论网络
        """
        print("正在构建 HN 讨论网络...")
        
        # 检查评论数据
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM hn_comments WHERE author IS NOT NULL")
        count = cursor.fetchone()["count"]
        
        if count == 0:
            print("  ⚠ hn_comments 表为空，讨论网络暂不可用")
            print("    需要运行数据采集获取评论数据")
            G = nx.DiGraph()
            self.networks["discussion"] = G
            return G
        
        # 获取评论及其 parent 关系
        query = """
            SELECT c.id, c.author, c.parent, p.author as parent_author
            FROM hn_comments c
            LEFT JOIN hn_comments p ON c.parent = p.id
            WHERE c.author IS NOT NULL AND c.parent IS NOT NULL
        """
        
        cursor = self.conn.execute(query)
        rows = cursor.fetchall()
        
        G = nx.DiGraph()
        
        for row in rows:
            author = row["author"]
            parent_author = row["parent_author"]
            
            if not parent_author or author == parent_author:
                continue
            
            G.add_node(author, platform="hackernews")
            G.add_node(parent_author, platform="hackernews")
            
            if G.has_edge(author, parent_author):
                G[author][parent_author]["weight"] += 1
            else:
                G.add_edge(author, parent_author, weight=1)
        
        print(f"  ✓ 讨论网络: {G.number_of_nodes()} 个用户, {G.number_of_edges()} 条边")
        
        self.networks["discussion"] = G
        return G
    
    def build_language_affinity_network(self):
        """
        从 GitHub 项目语言构建开发者亲和性网络
        
        节点：编程语言
        边：同一项目使用多种语言（共现关系）
        
        这是一个辅助网络，用于理解技术栈之间的关联
        
        Returns:
            nx.Graph: 语言关联网络
        """
        print("正在构建编程语言关联网络...")
        
        cursor = self.conn.execute("""
            SELECT repo, language FROM github_repos
            WHERE language IS NOT NULL AND language != ''
        """)
        rows = cursor.fetchall()
        
        # 按语言统计项目数
        lang_counts = defaultdict(int)
        for row in rows:
            lang_counts[row["language"]] += 1
        
        # 构建语言关联（通过 topic 共现）
        cursor = self.conn.execute("""
            SELECT topics, language FROM github_repos
            WHERE topics IS NOT NULL AND topics != '[]' AND language IS NOT NULL
        """)
        rows = cursor.fetchall()
        
        # 统计 topic 在不同语言中的分布
        topic_langs = defaultdict(lambda: defaultdict(int))
        for row in rows:
            try:
                topics = json.loads(row["topics"])
            except (json.JSONDecodeError, TypeError):
                continue
            lang = row["language"]
            for topic in topics:
                topic_langs[topic][lang] += 1
        
        # 构建语言关联网络
        G = nx.Graph()
        
        for lang, count in lang_counts.items():
            G.add_node(lang, project_count=count)
        
        # 如果两个语言经常出现在同一 topic 下，添加边
        for topic, langs in topic_langs.items():
            lang_list = list(langs.keys())
            for i, lang_a in enumerate(lang_list):
                for lang_b in lang_list[i + 1:]:
                    if G.has_edge(lang_a, lang_b):
                        G[lang_a][lang_b]["weight"] += 1
                    else:
                        G.add_edge(lang_a, lang_b, weight=1, topic=topic)
        
        print(f"  ✓ 语言网络: {G.number_of_nodes()} 种语言, {G.number_of_edges()} 条边")
        
        self.networks["language_affinity"] = G
        return G
    
    # ================================================================
    # 中心性分析
    # ================================================================
    
    def compute_centrality_metrics(self, G, network_name="unknown"):
        """
        计算网络中所有节点的中心性指标
        
        Args:
            G: NetworkX 图
            network_name: 网络名称（用于标识）
        
        Returns:
            dict: {node: {metric: value}} 中心性字典
        """
        if G.number_of_nodes() == 0:
            print(f"  ⚠ {network_name} 网络为空，跳过中心性计算")
            return {}
        
        print(f"正在计算 {network_name} 网络中心性指标...")
        
        metrics = {}
        
        # Degree Centrality
        degree_cent = nx.degree_centrality(G)
        
        # Betweenness Centrality（对于大图使用近似算法）
        if G.number_of_nodes() > 1000:
            print(f"  使用近似 Betweenness 计算（节点数: {G.number_of_nodes()}）")
            betweenness = nx.betweenness_centrality(G, k=min(100, G.number_of_nodes() // 10), weight="weight")
        else:
            betweenness = nx.betweenness_centrality(G, weight="weight")
        
        # Closeness Centrality
        if G.number_of_nodes() > 500:
            print(f"  使用近似 Closeness 计算")
            closeness = nx.closeness_centrality(G, distance="weight")
        else:
            closeness = nx.closeness_centrality(G, distance="weight")
        
        # PageRank（仅适用于连通图或弱连通图）
        try:
            if G.is_directed():
                pagerank = nx.pagerank(G, weight="weight")
            else:
                # 对于无向图，确保是连通的
                if nx.is_connected(G):
                    pagerank = nx.pagerank(G, weight="weight")
                else:
                    # 对每个连通分量分别计算
                    pagerank = {}
                    for component in nx.connected_components(G):
                        subgraph = G.subgraph(component)
                        if subgraph.number_of_nodes() > 1:
                            pr = nx.pagerank(subgraph, weight="weight")
                            pagerank.update(pr)
                        else:
                            for node in subgraph.nodes():
                                pagerank[node] = 1.0 / G.number_of_nodes()
        except Exception as e:
            print(f"  ⚠ PageRank 计算失败: {e}")
            pagerank = {node: 0.0 for node in G.nodes()}
        
        # 汇总
        for node in G.nodes():
            metrics[node] = {
                "degree_centrality": degree_cent.get(node, 0),
                "betweenness_centrality": betweenness.get(node, 0),
                "closeness_centrality": closeness.get(node, 0),
                "pagerank": pagerank.get(node, 0),
                "degree": G.degree(node),
                "network": network_name,
            }
        
        # 统计摘要
        top_pagerank = sorted(metrics.items(), key=lambda x: x[1]["pagerank"], reverse=True)[:5]
        top_betweenness = sorted(metrics.items(), key=lambda x: x[1]["betweenness_centrality"], reverse=True)[:5]
        
        print(f"  ✓ 中心性计算完成")
        print(f"    Top 5 PageRank:")
        for node, m in top_pagerank:
            label = str(node)[:40]
            print(f"      {label}: PR={m['pagerank']:.4f}")
        print(f"    Top 5 Betweenness:")
        for node, m in top_betweenness:
            label = str(node)[:40]
            print(f"      {label}: BC={m['betweenness_centrality']:.4f}")
        
        return metrics
    
    # ================================================================
    # 社区检测
    # ================================================================
    
    def detect_communities(self, G, network_name="unknown"):
        """
        使用 Louvain 算法检测社区结构
        
        Args:
            G: NetworkX 图
            network_name: 网络名称
        
        Returns:
            dict: {community_id: [nodes]} 社区成员字典
        """
        if G.number_of_nodes() == 0:
            print(f"  ⚠ {network_name} 网络为空，跳过社区检测")
            return {}
        
        print(f"正在检测 {network_name} 社区结构...")
        
        try:
            # 使用 Louvain 算法
            communities = nx.community.louvain_communities(G, seed=42)
            
            # 按大小排序
            communities_sorted = sorted(communities, key=len, reverse=True)
            
            print(f"  ✓ 检测到 {len(communities_sorted)} 个社区")
            
            # 输出前 5 个最大社区的摘要
            for i, comm in enumerate(communities_sorted[:5]):
                print(f"    社区 {i}: {len(comm)} 个节点")
                # 显示社区内的示例节点
                examples = list(comm)[:3]
                for ex in examples:
                    print(f"      - {str(ex)[:50]}")
            
            return {i: list(comm) for i, comm in enumerate(communities_sorted)}
            
        except Exception as e:
            print(f"  ⚠ 社区检测失败: {e}")
            return {}
    
    # ================================================================
    # 关键人物识别
    # ================================================================
    
    def identify_key_figures(self, all_metrics, all_communities):
        """
        基于中心性指标和社区结构识别关键人物
        
        分类标准：
        - 意见领袖（Opinion Leader）：高 PageRank + 高度中心性
        - 信息枢纽（Information Bridge）：高 Betweenness 中心性
        - 新兴声音（Emerging Voice）：在较小社区中但中心性较高
        
        Args:
            all_metrics: dict, {network_name: {node: metrics}}
            all_communities: dict, {network_name: {comm_id: [nodes]}}
        
        Returns:
            list of dict: 关键人物列表
        """
        print("=" * 60)
        print("识别关键人物")
        print("=" * 60)
        
        key_figures = []
        
        for network_name, metrics in all_metrics.items():
            if not metrics:
                continue
            
            communities = all_communities.get(network_name, {})
            
            # 计算各指标的全局统计
            pageranks = [m["pagerank"] for m in metrics.values()]
            betweenness_vals = [m["betweenness_centrality"] for m in metrics.values()]
            degree_vals = [m["degree"] for m in metrics.values()]
            
            if not pageranks:
                continue
            
            pr_mean = np.mean(pageranks)
            pr_std = np.std(pageranks) if len(pageranks) > 1 else 0
            bc_mean = np.mean(betweenness_vals)
            bc_std = np.std(betweenness_vals) if len(betweenness_vals) > 1 else 0
            
            # 找到每个节点所属的社区
            node_community = {}
            for comm_id, members in communities.items():
                for node in members:
                    node_community[node] = comm_id
            
            for node, m in metrics.items():
                figure_type = None
                confidence = 0
                
                # 意见领袖：PageRank > mean + 1*std 且 degree > mean
                if pr_std > 0 and m["pagerank"] > pr_mean + pr_std and m["degree"] > np.mean(degree_vals):
                    figure_type = "opinion_leader"
                    confidence = min((m["pagerank"] - pr_mean) / pr_std / 3.0, 1.0) if pr_std > 0 else 0.5
                
                # 信息枢纽：Betweenness > mean + 1*std
                elif bc_std > 0 and m["betweenness_centrality"] > bc_mean + bc_std:
                    figure_type = "information_bridge"
                    confidence = min((m["betweenness_centrality"] - bc_mean) / bc_std / 3.0, 1.0) if bc_std > 0 else 0.5
                
                # 新兴声音：在较小社区中但中心性较高
                elif node in node_community:
                    comm_id = node_community[node]
                    comm_size = len(communities.get(comm_id, []))
                    total_nodes = sum(len(m) for m in communities.values())
                    
                    if total_nodes > 0 and comm_size < total_nodes * 0.1:
                        # 在小社区中但 PageRank 高于平均
                        if m["pagerank"] > pr_mean:
                            figure_type = "emerging_voice"
                            confidence = min(m["pagerank"] / pr_mean - 1, 1.0) if pr_mean > 0 else 0.3
                
                if figure_type:
                    key_figures.append({
                        "id": f"{network_name}:{str(node)[:50]}",
                        "name": str(node),
                        "platform": network_name,
                        "type": figure_type,
                        "degree_centrality": m["degree_centrality"],
                        "betweenness_centrality": m["betweenness_centrality"],
                        "pagerank": m["pagerank"],
                        "degree": m["degree"],
                        "community": node_community.get(node),
                        "confidence": confidence,
                        "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    })
        
        # 按类型和置信度排序
        type_order = {"opinion_leader": 0, "information_bridge": 1, "emerging_voice": 2}
        key_figures.sort(key=lambda x: (type_order.get(x["type"], 3), -x["confidence"]))
        
        # 统计
        type_counts = defaultdict(int)
        for kf in key_figures:
            type_counts[kf["type"]] += 1
        
        print(f"  意见领袖: {type_counts['opinion_leader']}")
        print(f"  信息枢纽: {type_counts['information_bridge']}")
        print(f"  新兴声音: {type_counts['emerging_voice']}")
        print(f"  合计: {len(key_figures)}")
        
        self.key_figures = key_figures
        return key_figures
    
    # ================================================================
    # 跨社区传播路径
    # ================================================================
    
    def analyze_cross_community_paths(self, G, communities, network_name="unknown"):
        """
        分析跨社区的信息传播路径
        
        识别连接不同社区的桥接节点和路径
        
        Args:
            G: NetworkX 图
            communities: dict, {comm_id: [nodes]}
            network_name: 网络名称
        
        Returns:
            list of dict: 跨社区路径信息
        """
        if not communities or G.number_of_nodes() == 0:
            return []
        
        print(f"正在分析 {network_name} 跨社区传播路径...")
        
        # 找到每个节点所属的社区
        node_community = {}
        for comm_id, members in communities.items():
            for node in members:
                node_community[node] = comm_id
        
        # 识别桥接边（连接不同社区的边）
        bridge_edges = []
        for u, v, data in G.edges(data=True):
            comm_u = node_community.get(u)
            comm_v = node_community.get(v)
            
            if comm_u is not None and comm_v is not None and comm_u != comm_v:
                bridge_edges.append({
                    "source": str(u),
                    "target": str(v),
                    "source_community": comm_u,
                    "target_community": comm_v,
                    "weight": data.get("weight", 1),
                })
        
        # 识别桥接节点（连接多个社区的节点）
        bridge_nodes = defaultdict(set)
        for edge in bridge_edges:
            # 源节点连接的社区
            bridge_nodes[edge["source"]].add(edge["target_community"])
            # 目标节点连接的社区
            bridge_nodes[edge["target"]].add(edge["source_community"])
        
        # 筛选真正的桥接节点（连接 2+ 个不同社区）
        real_bridges = []
        for node, connected_comms in bridge_nodes.items():
            own_comm = node_community.get(node)
            external_comms = connected_comms - {own_comm}
            
            if len(external_comms) >= 1:
                real_bridges.append({
                    "node": str(node),
                    "own_community": own_comm,
                    "connected_communities": list(external_comms),
                    "bridge_count": len(external_comms),
                })
        
        real_bridges.sort(key=lambda x: x["bridge_count"], reverse=True)
        
        print(f"  ✓ 桥接边: {len(bridge_edges)}")
        print(f"  ✓ 桥接节点: {len(real_bridges)}")
        
        if real_bridges:
            print(f"  Top 5 桥接节点:")
            for bridge in real_bridges[:5]:
                print(f"    {bridge['node'][:40]}: 连接 {bridge['bridge_count']} 个外部社区")
        
        return {
            "bridge_edges": bridge_edges,
            "bridge_nodes": real_bridges,
            "network": network_name,
        }
    
    # ================================================================
    # 数据持久化
    # ================================================================
    
    def save_key_figures(self):
        """保存关键人物到数据库"""
        if not self.key_figures:
            return 0
        
        cursor = self.conn.cursor()
        saved = 0
        
        for figure in self.key_figures:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO key_figures
                    (id, name, platform, type, degree_centrality, betweenness_centrality, pagerank, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    figure["id"],
                    figure["name"],
                    figure["platform"],
                    figure["type"],
                    figure["degree_centrality"],
                    figure["betweenness_centrality"],
                    figure["pagerank"],
                    figure["last_updated"],
                ))
                if cursor.rowcount > 0:
                    saved += 1
            except Exception as e:
                print(f"  ✗ 保存关键人物失败: {e}")
        
        self.conn.commit()
        print(f"✓ 保存 {saved} 个关键人物到数据库")
        return saved
    
    def save_communities(self, all_communities):
        """保存社区结构到数据库"""
        cursor = self.conn.cursor()
        saved = 0
        
        for network_name, communities in all_communities.items():
            for comm_id, members in communities.items():
                try:
                    name = f"{network_name}_community_{comm_id}"
                    cursor.execute("""
                        INSERT INTO communities (name, members, detected_date)
                        VALUES (?, ?, ?)
                    """, (
                        name,
                        json.dumps([str(m) for m in members[:100]]),  # 限制存储大小
                        datetime.now().strftime("%Y-%m-%d"),
                    ))
                    saved += 1
                except Exception as e:
                    print(f"  ✗ 保存社区失败: {e}")
        
        self.conn.commit()
        print(f"✓ 保存 {saved} 个社区到数据库")
        return saved
    
    # ================================================================
    # 报告生成
    # ================================================================
    
    def generate_report(self, all_metrics, all_communities, cross_community_data):
        """生成社区结构分析报告"""
        print("=" * 60)
        print("生成社区结构分析报告")
        print("=" * 60)
        
        report_lines = []
        report_lines.append("# 社区结构分析报告")
        report_lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report_lines.append("")
        
        # 1. 网络概览
        report_lines.append("## 1. 网络概览")
        report_lines.append("")
        
        for network_name, G in self.networks.items():
            if G.number_of_nodes() == 0:
                continue
            report_lines.append(f"### {network_name}")
            report_lines.append(f"- 节点数: {G.number_of_nodes()}")
            report_lines.append(f"- 边数: {G.number_of_edges()}")
            
            if G.number_of_nodes() > 0:
                density = nx.density(G)
                report_lines.append(f"- 网络密度: {density:.4f}")
                
                if not G.is_directed():
                    components = list(nx.connected_components(G))
                    report_lines.append(f"- 连通分量: {len(components)}")
                    if components:
                        report_lines.append(f"- 最大连通分量: {len(max(components, key=len))} 节点")
            
            report_lines.append("")
        
        # 2. 关键人物
        report_lines.append("## 2. 关键人物")
        report_lines.append("")
        
        for figure_type, type_label in [
            ("opinion_leader", "意见领袖"),
            ("information_bridge", "信息枢纽"),
            ("emerging_voice", "新兴声音"),
        ]:
            figures = [f for f in self.key_figures if f["type"] == figure_type]
            if figures:
                report_lines.append(f"### {type_label} ({len(figures)})")
                report_lines.append("")
                report_lines.append("| 名称 | 平台 | PageRank | Betweenness | 置信度 |")
                report_lines.append("|------|------|----------|-------------|--------|")
                for f in figures[:10]:
                    report_lines.append(
                        f"| {f['name'][:30]} | {f['platform']} | {f['pagerank']:.4f} | "
                        f"{f['betweenness_centrality']:.4f} | {f['confidence']:.2f} |"
                    )
                report_lines.append("")
        
        # 3. 社区结构
        report_lines.append("## 3. 社区结构")
        report_lines.append("")
        
        for network_name, communities in all_communities.items():
            if not communities:
                continue
            report_lines.append(f"### {network_name}")
            report_lines.append(f"共检测到 {len(communities)} 个社区")
            report_lines.append("")
            
            for comm_id, members in sorted(communities.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
                report_lines.append(f"**社区 {comm_id}** ({len(members)} 个节点)")
                examples = [str(m)[:40] for m in members[:5]]
                report_lines.append(f"- 示例: {', '.join(examples)}")
            report_lines.append("")
        
        # 4. 跨社区传播
        report_lines.append("## 4. 跨社区传播路径")
        report_lines.append("")
        
        for data in cross_community_data:
            if not data:
                continue
            network_name = data.get("network", "unknown")
            bridges = data.get("bridge_nodes", [])
            
            if bridges:
                report_lines.append(f"### {network_name}")
                report_lines.append(f"桥接节点: {len(bridges)}")
                report_lines.append("")
                report_lines.append("| 节点 | 所属社区 | 连接外部社区数 |")
                report_lines.append("|------|----------|----------------|")
                for b in bridges[:10]:
                    report_lines.append(
                        f"| {b['node'][:30]} | {b['own_community']} | {b['bridge_count']} |"
                    )
                report_lines.append("")
        
        report_text = "\n".join(report_lines)
        
        # 保存报告
        report_path = Path(self.db_path).parent / "signals" / "community_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_text, encoding="utf-8")
        
        print(f"✓ 报告已保存: {report_path}")
        return report_text
    
    # ================================================================
    # 主运行流程
    # ================================================================
    
    def run_full_analysis(self):
        """运行完整的社区结构分析"""
        print("=" * 60)
        print("Layer 2: 社区结构分析")
        print("=" * 60)
        
        # 1. 构建网络
        print("\n--- 阶段 1: 网络构建 ---\n")
        
        G_author = self.build_author_collaboration_network()
        G_project = self.build_project_topic_network()
        G_discussion = self.build_discussion_network()
        G_language = self.build_language_affinity_network()
        
        # 2. 计算中心性
        print("\n--- 阶段 2: 中心性分析 ---\n")
        
        all_metrics = {}
        if G_author.number_of_nodes() > 0:
            all_metrics["author_collaboration"] = self.compute_centrality_metrics(G_author, "author_collaboration")
        if G_project.number_of_nodes() > 0:
            all_metrics["project_topic"] = self.compute_centrality_metrics(G_project, "project_topic")
        if G_discussion.number_of_nodes() > 0:
            all_metrics["discussion"] = self.compute_centrality_metrics(G_discussion, "discussion")
        
        # 3. 社区检测
        print("\n--- 阶段 3: 社区检测 ---\n")
        
        all_communities = {}
        if G_author.number_of_nodes() > 0:
            all_communities["author_collaboration"] = self.detect_communities(G_author, "author_collaboration")
        if G_project.number_of_nodes() > 0:
            all_communities["project_topic"] = self.detect_communities(G_project, "project_topic")
        
        # 4. 关键人物识别
        print("\n--- 阶段 4: 关键人物识别 ---\n")
        
        key_figures = self.identify_key_figures(all_metrics, all_communities)
        
        # 5. 跨社区传播分析
        print("\n--- 阶段 5: 跨社区传播分析 ---\n")
        
        cross_community_data = []
        if G_project.number_of_nodes() > 0 and "project_topic" in all_communities:
            cc = self.analyze_cross_community_paths(
                G_project, all_communities["project_topic"], "project_topic"
            )
            cross_community_data.append(cc)
        if G_author.number_of_nodes() > 0 and "author_collaboration" in all_communities:
            cc = self.analyze_cross_community_paths(
                G_author, all_communities["author_collaboration"], "author_collaboration"
            )
            cross_community_data.append(cc)
        
        # 6. 持久化
        print("\n--- 阶段 6: 数据持久化 ---\n")
        
        self.save_key_figures()
        self.save_communities(all_communities)
        
        # 7. 生成报告
        print("\n--- 阶段 7: 报告生成 ---\n")
        
        report = self.generate_report(all_metrics, all_communities, cross_community_data)
        
        print("\n" + "=" * 60)
        print("Layer 2 分析完成")
        print("=" * 60)
        
        return {
            "networks": self.networks,
            "metrics": all_metrics,
            "communities": all_communities,
            "key_figures": key_figures,
            "cross_community": cross_community_data,
            "report": report,
        }
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()


if __name__ == "__main__":
    analyzer = CommunityAnalyzer()
    results = analyzer.run_full_analysis()
    
    print(f"\n分析摘要:")
    print(f"  网络数: {len(results['networks'])}")
    print(f"  关键人物: {len(results['key_figures'])}")
    print(f"  社区数: {sum(len(c) for c in results['communities'].values())}")
    
    analyzer.close()
