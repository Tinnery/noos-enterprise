"""
数据库初始化脚本
"""

import sqlite3
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from config import DB_PATH, DB_SCHEMA


def init_database():
    """初始化数据库"""
    print(f"正在初始化数据库: {DB_PATH}")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 执行 Schema
    cursor.executescript(DB_SCHEMA)
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print("✓ 数据库初始化完成")
    print(f"  位置: {DB_PATH}")
    print("  表结构:")
    print("    - papers (论文)")
    print("    - citations (引用关系)")
    print("    - github_repos (GitHub 项目)")
    print("    - star_history (Star 历史)")
    print("    - hn_stories (HN 帖子)")
    print("    - hn_comments (HN 评论)")
    print("    - signals (信号)")
    print("    - key_figures (关键人物)")
    print("    - communities (社区)")


if __name__ == "__main__":
    init_database()
