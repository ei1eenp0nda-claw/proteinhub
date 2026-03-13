"""
ProteinHub Recommendation System - User Profile Generator
生成用户画像数据
"""
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import random

# 配置参数
np.random.seed(42)
random.seed(42)

# 研究领域标签
RESEARCH_FIELDS = [
    '蛋白质结构预测', '蛋白质折叠', 'AlphaFold', '分子动力学',
    '蛋白质-配体相互作用', '酶催化', '膜蛋白', '抗体设计',
    '蛋白质工程', '结构生物学', '冷冻电镜', 'X射线晶体学',
    'NMR', '蛋白质组学', '质谱分析', '生物信息学',
    '机器学习', '深度学习', '图神经网络', '扩散模型',
    '分子对接', '虚拟筛选', '药物设计', '罕见病研究',
    '癌症生物学', '神经退行性疾病', '免疫学', '代谢工程'
]

# 活跃时段分布
ACTIVE_HOURS_DIST = {
    'morning': 0.15,      # 6-12点
    'afternoon': 0.25,    # 12-18点
    'evening': 0.40,      # 18-24点
    'night': 0.20         # 0-6点
}

# 阅读偏好类型
READING_PREFERENCES = [
    '最新论文', '经典方法', '综述文章', '技术教程',
    '实验技巧', '算法解读', '应用案例', '新闻动态'
]

# 互动倾向
INTERACTION_TYPES = ['like', 'collect', 'comment', 'share', 'follow']

def generate_user_profiles(n_users=800, output_path='data/users.csv'):
    """生成用户画像数据"""
    
    users = []
    base_date = datetime(2023, 1, 1)
    
    for i in range(n_users):
        user_id = f"user_{i+1:04d}"
        
        # 注册时间 - 模拟不同注册时间
        days_ago = np.random.exponential(scale=200)
        register_time = base_date + timedelta(days=int(days_ago))
        register_time = min(register_time, datetime.now())
        
        # 研究领域标签（多标签，1-3个）
        n_fields = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
        fields = np.random.choice(RESEARCH_FIELDS, size=n_fields, replace=False).tolist()
        
        # 活跃时段
        active_period = np.random.choice(
            list(ACTIVE_HOURS_DIST.keys()),
            p=list(ACTIVE_HOURS_DIST.values())
        )
        
        # 阅读偏好（1-2个主要偏好）
        n_prefs = np.random.choice([1, 2], p=[0.6, 0.4])
        reading_prefs = np.random.choice(READING_PREFERENCES, size=n_prefs, replace=False).tolist()
        
        # 互动倾向评分（0-1之间）
        interaction_tendency = {
            'like': np.random.beta(3, 2),      # 点赞倾向较高
            'collect': np.random.beta(2, 3),   # 收藏倾向中等
            'comment': np.random.beta(1.5, 4), # 评论倾向较低
            'share': np.random.beta(1, 5),     # 分享倾向低
            'follow': np.random.beta(2, 2)     # 关注倾向中等
        }
        
        # 社交属性
        follower_count = int(np.random.lognormal(3, 1.5))  # 粉丝数
        following_count = int(np.random.lognormal(2.5, 1.2))  # 关注数
        
        # 用户活跃度（影响行为数据生成）
        activity_level = np.random.choice(['low', 'medium', 'high'], p=[0.3, 0.5, 0.2])
        
        # 用户类型（用于模拟不同行为模式）
        user_type = np.random.choice(
            ['researcher', 'student', 'industry', 'newbie'],
            p=[0.35, 0.35, 0.20, 0.10]
        )
        
        user = {
            'user_id': user_id,
            'register_time': register_time.strftime('%Y-%m-%d %H:%M:%S'),
            'research_fields': json.dumps(fields, ensure_ascii=False),
            'active_period': active_period,
            'reading_preferences': json.dumps(reading_prefs, ensure_ascii=False),
            'interaction_tendency': json.dumps(interaction_tendency),
            'follower_count': follower_count,
            'following_count': following_count,
            'activity_level': activity_level,
            'user_type': user_type
        }
        users.append(user)
    
    df = pd.DataFrame(users)
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"Generated {n_users} user profiles -> {output_path}")
    
    return df

if __name__ == '__main__':
    import os
    os.makedirs('data', exist_ok=True)
    generate_user_profiles(800)
