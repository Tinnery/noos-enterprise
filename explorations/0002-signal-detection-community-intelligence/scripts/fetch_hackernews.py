"""
Hacker News 数据采集模块
"""

import requests
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).parent))

from config import HACKERNEWS_CONFIG, DATA_DIR, DB_PATH


def fetch_top_stories(count=None):
    """
    获取热门帖子
    
    Args:
        count: 获取数量（None 表示使用配置值）
    
    Returns:
        list of dict: 帖子列表
    """
    if count is None:
        count = HACKERNEWS_CONFIG["top_stories_count"]
    
    print(f"正在获取 HN 热门帖子（前 {count} 个）...")
    
    # 获取热门帖子 ID
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        story_ids = response.json()[:count]
    except Exception as e:
        print(f"  ✗ 获取热门帖子 ID 失败: {e}")
        return []
    
    # 获取每个帖子的详情
    stories = []
    for i, story_id in enumerate(story_ids):
        story = fetch_story_detail(story_id)
        if story:
            stories.append(story)
        
        # 进度提示
        if (i + 1) % 20 == 0:
            print(f"  已获取 {i + 1}/{len(story_ids)}")
        
        # 避免请求过快
        time.sleep(0.1)
    
    print(f"✓ 获取到 {len(stories)} 个帖子")
    return stories


def fetch_new_stories(count=None):
    """
    获取最新帖子
    
    Args:
        count: 获取数量
    
    Returns:
        list of dict: 帖子列表
    """
    if count is None:
        count = HACKERNEWS_CONFIG["new_stories_count"]
    
    print(f"正在获取 HN 最新帖子（前 {count} 个）...")
    
    # 获取最新帖子 ID
    url = "https://hacker-news.firebaseio.com/v0/newstories.json"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        story_ids = response.json()[:count]
    except Exception as e:
        print(f"  ✗ 获取最新帖子 ID 失败: {e}")
        return []
    
    # 获取每个帖子的详情
    stories = []
    for i, story_id in enumerate(story_ids):
        story = fetch_story_detail(story_id)
        if story:
            stories.append(story)
        
        # 进度提示
        if (i + 1) % 20 == 0:
            print(f"  已获取 {i + 1}/{len(story_ids)}")
        
        time.sleep(0.1)
    
    print(f"✓ 获取到 {len(stories)} 个帖子")
    return stories


def fetch_story_detail(story_id):
    """
    获取帖子详情
    
    Args:
        story_id: 帖子 ID
    
    Returns:
        dict: 帖子详情
    """
    url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data is None:
            return None
        
        story = {
            "id": data.get("id"),
            "title": data.get("title", ""),
            "url": data.get("url", ""),
            "score": data.get("score", 0),
            "descendants": data.get("descendants", 0),
            "author": data.get("by", ""),
            "time": data.get("time", 0),
            "type": data.get("type", "story"),
            "detected_date": datetime.now().isoformat(),
        }
        
        return story
        
    except Exception as e:
        print(f"  ✗ 获取帖子 {story_id} 失败: {e}")
        return None


def fetch_comments(story_id, max_comments=100):
    """
    获取帖子的评论
    
    Args:
        story_id: 帖子 ID
        max_comments: 最大评论数
    
    Returns:
        list of dict: 评论列表
    """
    url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data is None or "kids" not in data:
            return []
        
        comment_ids = data["kids"][:max_comments]
        comments = []
        
        for comment_id in comment_ids:
            comment = fetch_comment_detail(comment_id, story_id)
            if comment:
                comments.append(comment)
            
            time.sleep(0.1)
        
        return comments
        
    except Exception as e:
        print(f"  ✗ 获取帖子 {story_id} 评论失败: {e}")
        return []


def fetch_comment_detail(comment_id, story_id):
    """
    获取评论详情
    
    Args:
        comment_id: 评论 ID
        story_id: 所属帖子 ID
    
    Returns:
        dict: 评论详情
    """
    url = f"https://hacker-news.firebaseio.com/v0/item/{comment_id}.json"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data is None:
            return None
        
        comment = {
            "id": data.get("id"),
            "story_id": story_id,
            "author": data.get("by", ""),
            "text": data.get("text", ""),
            "time": data.get("time", 0),
            "parent": data.get("parent"),
        }
        
        return comment
        
    except Exception as e:
        return None


def save_stories_to_json(stories, date_str=None, story_type="stories"):
    """保存帖子到 JSON 文件"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    output_path = DATA_DIR / "hackernews" / "stories" / f"{story_type}_{date_str}.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 帖子已保存到: {output_path}")
    return output_path


def save_stories_to_db(stories):
    """保存帖子到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    for story in stories:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO hn_stories 
                (id, title, url, score, descendants, author, time, detected_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                story["id"],
                story["title"],
                story["url"],
                story["score"],
                story["descendants"],
                story["author"],
                story["time"],
                story["detected_date"]
            ))
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"  ✗ 插入帖子失败 {story['id']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✓ 数据库插入 {inserted} 个帖子")
    return inserted


def save_comments_to_db(comments):
    """保存评论到数据库"""
    if not comments:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    for comment in comments:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO hn_comments 
                (id, story_id, author, text, time, parent)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                comment["id"],
                comment["story_id"],
                comment["author"],
                comment["text"],
                comment["time"],
                comment["parent"]
            ))
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"  ✗ 插入评论失败 {comment['id']}: {e}")
    
    conn.commit()
    conn.close()
    
    return inserted


def fetch_and_store_hackernews(fetch_comments_for_top=10):
    """获取并存储 Hacker News 数据"""
    # 获取热门帖子
    top_stories = fetch_top_stories()
    
    if top_stories:
        save_stories_to_json(top_stories, story_type="top")
        save_stories_to_db(top_stories)
        
        # 获取前 N 个帖子的评论
        if fetch_comments_for_top > 0:
            print(f"\n正在获取评论（前 {fetch_comments_for_top} 个帖子）...")
            all_comments = []
            
            for i, story in enumerate(top_stories[:fetch_comments_for_top]):
                comments = fetch_comments(story["id"])
                all_comments.extend(comments)
                
                if (i + 1) % 5 == 0:
                    print(f"  已获取 {i + 1}/{fetch_comments_for_top} 个帖子的评论")
            
            if all_comments:
                save_comments_to_db(all_comments)
                print(f"✓ 获取并保存 {len(all_comments)} 条评论")
    
    return top_stories


if __name__ == "__main__":
    # 测试运行
    stories = fetch_and_store_hackernews(fetch_comments_for_top=5)
    print(f"\n示例帖子:")
    if stories:
        sample = stories[0]
        print(f"  标题: {sample['title']}")
        print(f"  分数: {sample['score']}")
        print(f"  评论数: {sample['descendants']}")
        print(f"  作者: {sample['author']}")
