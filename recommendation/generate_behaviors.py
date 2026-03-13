"""
ProteinHub Recommendation System - User Behavior Generator (Optimized)
生成用户行为数据（浏览、点赞、收藏、评论、关注）- 优化版本
"""
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

# 164篇笔记的ID
N_NOTES = 164
NOTE_IDS = [f"note_{i+1:04d}" for i in range(N_NOTES)]

def load_users(path='data/users.csv'):
    """加载用户数据"""
    df = pd.read_csv(path)
    df['research_fields'] = df['research_fields'].apply(json.loads)
    df['reading_preferences'] = df['reading_preferences'].apply(json.loads)
    df['interaction_tendency'] = df['interaction_tendency'].apply(json.loads)
    return df

def generate_note_metadata(n_notes=164):
    """生成笔记元数据（用于行为模拟）"""
    notes = []
    
    for i in range(n_notes):
        note_id = f"note_{i+1:04d}"
        
        # 发布时间
        days_ago = np.random.exponential(scale=300)
        publish_time = datetime.now() - timedelta(days=int(days_ago))
        
        # 内容质量
        quality_score = np.random.beta(3, 2)
        
        # 所属研究领域
        n_fields = np.random.choice([1, 2], p=[0.7, 0.3])
        fields = np.random.choice([
            '蛋白质结构预测', '蛋白质折叠', 'AlphaFold', '分子动力学',
            '蛋白质-配体相互作用', '酶催化', '机器学习', '深度学习'
        ], size=n_fields, replace=False).tolist()
        
        # 内容类型
        content_type = np.random.choice([
            '最新论文', '经典方法', '综述文章', '技术教程',
            '实验技巧', '算法解读', '应用案例'
        ], p=[0.25, 0.15, 0.15, 0.15, 0.10, 0.10, 0.10])
        
        # 热度
        recency_factor = 1 / (1 + days_ago / 30)
        popularity = quality_score * (0.5 + 0.5 * recency_factor)
        
        notes.append({
            'note_id': note_id,
            'publish_time': publish_time,
            'quality_score': quality_score,
            'fields': fields,
            'content_type': content_type,
            'popularity': popularity
        })
    
    return pd.DataFrame(notes)

def generate_behavior_data_fast(users_df, notes_df, output_dir='data'):
    """快速生成用户行为数据 - 优化版本"""
    
    print(f"Generating behaviors for {len(users_df)} users...")
    
    # 向量化操作，避免循环
    all_views = []
    all_likes = []
    all_collects = []
    all_comments = []
    all_follows = []
    
    # 为每种活跃度的用户预定义浏览数量
    activity_views = {
        'low': (50, 200),
        'medium': (200, 800),
        'high': (800, 2000)
    }
    
    # 批量生成
    for _, user in users_df.iterrows():
        user_id = user['user_id']
        activity = user['activity_level']
        interaction_tendency = user['interaction_tendency']
        user_fields = set(user['research_fields'])
        
        # 确定浏览数量
        min_views, max_views = activity_views[activity]
        n_views = np.random.randint(min_views, max_views)
        
        # 批量选择笔记 - 基于匹配度和热度
        note_probs = []
        for _, note in notes_df.iterrows():
            note_fields = set(note['fields'])
            field_match = len(user_fields & note_fields) / max(len(user_fields), 1)
            prob = 0.3 * field_match + 0.4 * note['popularity'] + 0.3 * 0.5
            note_probs.append(prob)
        
        note_probs = np.array(note_probs)
        note_probs = note_probs / note_probs.sum()
        
        # 批量采样
        selected_indices = np.random.choice(
            len(notes_df), 
            size=min(n_views, len(notes_df)), 
            replace=True,
            p=note_probs
        )
        
        # 生成时间戳和浏览记录
        for idx in selected_indices:
            note = notes_df.iloc[idx]
            note_id = note['note_id']
            
            view_time = datetime.now() - timedelta(days=np.random.randint(0, 180), hours=np.random.randint(0, 24))
            read_time = int(60 + np.random.exponential(100))
            
            all_views.append({
                'user_id': user_id,
                'note_id': note_id,
                'timestamp': view_time.strftime('%Y-%m-%d %H:%M:%S'),
                'read_time': read_time
            })
            
            # 根据概率生成其他行为
            if np.random.random() < interaction_tendency['like'] * note['quality_score']:
                all_likes.append({
                    'user_id': user_id,
                    'note_id': note_id,
                    'timestamp': view_time.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            if np.random.random() < interaction_tendency['collect'] * note['quality_score'] * 0.5:
                all_collects.append({
                    'user_id': user_id,
                    'note_id': note_id,
                    'timestamp': view_time.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            if np.random.random() < interaction_tendency['comment'] * note['quality_score'] * 0.2:
                all_comments.append({
                    'user_id': user_id,
                    'note_id': note_id,
                    'timestamp': view_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'content_length': np.random.randint(10, 200)
                })
    
    # 生成关注关系
    print("Generating follow relationships...")
    for _, user in users_df.iterrows():
        user_id = user['user_id']
        n_follow = min(user['following_count'], 50)  # 限制最大关注数
        
        if n_follow > 0:
            # 随机选择关注对象
            follow_targets = users_df.sample(min(n_follow, len(users_df)-1))['user_id'].tolist()
            for target_id in follow_targets:
                if target_id != user_id:
                    all_follows.append({
                        'user_id': user_id,
                        'target_id': target_id,
                        'timestamp': (datetime.now() - timedelta(days=np.random.randint(0, 180))).strftime('%Y-%m-%d %H:%M:%S')
                    })
    
    # 保存数据
    behaviors = {
        'views': all_views,
        'likes': all_likes,
        'collects': all_collects,
        'comments': all_comments,
        'follows': all_follows
    }
    
    for name, data in behaviors.items():
        if data:
            df = pd.DataFrame(data)
            df.to_csv(f"{output_dir}/{name}.csv", index=False, encoding='utf-8')
            print(f"  Generated {len(data)} {name} records")
    
    return behaviors

if __name__ == '__main__':
    import os
    os.makedirs('data', exist_ok=True)
    
    # 生成笔记元数据
    if not os.path.exists('data/notes_metadata.csv'):
        notes = generate_note_metadata()
        notes.to_csv('data/notes_metadata.csv', index=False)
        print(f"Generated {len(notes)} note metadata records")
    else:
        notes = pd.read_csv('data/notes_metadata.csv')
        print(f"Loaded {len(notes)} note metadata records")
    
    # 加载用户
    users = load_users('data/users.csv')
    
    # 生成行为数据
    generate_behavior_data_fast(users, notes)
    
    print("\nBehavior data generation complete!")
