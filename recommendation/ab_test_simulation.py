"""
ProteinHub Recommendation System - A/B Testing Simulation
A/B测试模拟框架
"""
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from collections import defaultdict
import random

from recommendation_engine import CollaborativeFiltering, ContentBasedRecommender, HybridRecommender
from evaluation import RecommendationEvaluator

np.random.seed(42)
random.seed(42)

class ABTestSimulator:
    """A/B测试模拟器"""
    
    def __init__(self, user_data, item_data, interaction_data):
        self.users = user_data
        self.items = item_data
        self.interactions = interaction_data
        self.test_results = {}
        
    def split_users(self, split_ratio=0.5, strategy='random'):
        """
        将用户分为对照组和实验组
        
        Parameters:
        -----------
        split_ratio: 实验组占比（如0.5表示50/50分组）
        strategy: 分组策略 ('random', 'stratified')
        """
        user_ids = self.users['user_id'].tolist()
        n_users = len(user_ids)
        n_treatment = int(n_users * split_ratio)
        
        if strategy == 'random':
            # 随机分组
            np.random.shuffle(user_ids)
            treatment_group = set(user_ids[:n_treatment])
            control_group = set(user_ids[n_treatment:])
        
        elif strategy == 'stratified':
            # 按用户类型分层分组，保证各组用户类型分布一致
            treatment_group = set()
            control_group = set()
            
            for user_type in self.users['user_type'].unique():
                type_users = self.users[self.users['user_type'] == user_type]['user_id'].tolist()
                np.random.shuffle(type_users)
                n_type_treatment = int(len(type_users) * split_ratio)
                
                treatment_group.update(type_users[:n_type_treatment])
                control_group.update(type_users[n_type_treatment:])
        
        self.groups = {
            'control': control_group,
            'treatment': treatment_group
        }
        
        print(f"User split complete:")
        print(f"  Control group: {len(control_group)} users")
        print(f"  Treatment group: {len(treatment_group)} users")
        
        return self.groups
    
    def setup_recommenders(self):
        """设置各组的推荐算法"""
        
        # 准备训练数据
        train_data = self.interactions.copy()
        
        # 对照组使用简单策略
        self.control_strategy = 'popularity'  # 或 'random', 'time_based'
        
        # 训练实验组模型
        print("\nTraining recommendation models...")
        
        # 协同过滤模型
        self.cf_model = CollaborativeFiltering(n_factors=50)
        self.cf_model.fit(train_data)
        print("  - Collaborative Filtering trained")
        
        # 内容推荐模型
        self.cb_model = ContentBasedRecommender()
        # 准备特征数据
        feature_cols = [c for c in self.items.columns if c not in ['note_id', 'publish_time', 'fields', 'content_type']]
        self.cb_model.fit(self.items, feature_cols=feature_cols)
        print("  - Content-Based model trained")
        
        # 混合推荐模型
        self.hybrid_model = HybridRecommender(cf_weight=0.6, cb_weight=0.4)
        self.hybrid_model.fit(train_data, self.items)
        print("  - Hybrid model trained")
    
    def generate_control_recommendations(self, user_id, n=10):
        """
        对照组推荐策略
        
        Strategies:
        - 'random': 随机推荐
        - 'popularity': 热度排序
        - 'time_based': 时间倒序
        """
        if self.control_strategy == 'random':
            return [(item, 0) for item in np.random.choice(self.items['note_id'].tolist(), n, replace=False)]
        
        elif self.control_strategy == 'popularity':
            # 按热度排序
            sorted_items = self.items.sort_values('popularity', ascending=False)
            return [(row['note_id'], row['popularity']) for _, row in sorted_items.head(n).iterrows()]
        
        elif self.control_strategy == 'time_based':
            # 按时间倒序
            sorted_items = self.items.sort_values('publish_time', ascending=False)
            return [(row['note_id'], 0.5) for _, row in sorted_items.head(n).iterrows()]
    
    def simulate_experiment(self, experiment_duration_days=14, n_recommendations=10):
        """
        模拟A/B测试实验
        
        Parameters:
        -----------
        experiment_duration_days: 实验持续天数
        n_recommendations: 每次推荐的物品数量
        """
        print(f"\nSimulating A/B test for {experiment_duration_days} days...")
        
        # 为每个用户生成推荐
        control_recommendations = {}
        treatment_cf_recommendations = {}
        treatment_cb_recommendations = {}
        treatment_hybrid_recommendations = {}
        
        for user_id in self.groups['control']:
            control_recommendations[user_id] = self.generate_control_recommendations(user_id, n_recommendations)
        
        for user_id in self.groups['treatment']:
            # 获取用户历史
            user_history = self.interactions[self.interactions['user_id'] == user_id]['note_id'].tolist()
            
            # 协同过滤
            treatment_cf_recommendations[user_id] = self.cf_model.recommend(user_id, n_recommendations)
            
            # 内容推荐
            treatment_cb_recommendations[user_id] = self.cb_model.recommend(user_history, n_recommendations)
            
            # 混合推荐
            treatment_hybrid_recommendations[user_id] = self.hybrid_model.recommend(
                user_id, user_history, n_recommendations
            )
        
        # 模拟用户反馈
        print("  Simulating user feedback...")
        
        control_feedback = self._simulate_feedback(control_recommendations)
        cf_feedback = self._simulate_feedback(treatment_cf_recommendations)
        cb_feedback = self._simulate_feedback(treatment_cb_recommendations)
        hybrid_feedback = self._simulate_feedback(treatment_hybrid_recommendations)
        
        self.test_results = {
            'control': {
                'recommendations': control_recommendations,
                'feedback': control_feedback
            },
            'cf': {
                'recommendations': treatment_cf_recommendations,
                'feedback': cf_feedback
            },
            'cb': {
                'recommendations': treatment_cb_recommendations,
                'feedback': cb_feedback
            },
            'hybrid': {
                'recommendations': treatment_hybrid_recommendations,
                'feedback': hybrid_feedback
            }
        }
        
        return self.test_results
    
    def _simulate_feedback(self, recommendations):
        """模拟用户对推荐的反馈"""
        feedback = []
        
        for user_id, recs in recommendations.items():
            user_info = self.users[self.users['user_id'] == user_id].iloc[0]
            interaction_tendency = json.loads(user_info['interaction_tendency'])
            
            for item_id, score in recs:
                item_info = self.items[self.items['note_id'] == item_id].iloc[0]
                
                # 模拟曝光
                feedback.append({
                    'user_id': user_id,
                    'note_id': item_id,
                    'action': 'impression'
                })
                
                # 模拟点击（基于推荐分数和用户倾向）
                click_prob = 0.3 * score + 0.3 * item_info['quality_score'] + 0.1
                if np.random.random() < click_prob:
                    feedback.append({
                        'user_id': user_id,
                        'note_id': item_id,
                        'action': 'click'
                    })
                    
                    # 模拟阅读时长
                    read_time = np.random.exponential(60) * (1 + item_info['quality_score'])
                    feedback.append({
                        'user_id': user_id,
                        'note_id': item_id,
                        'action': 'read',
                        'duration': min(read_time, 600)
                    })
                    
                    # 模拟点赞
                    if np.random.random() < interaction_tendency['like'] * item_info['quality_score']:
                        feedback.append({
                            'user_id': user_id,
                            'note_id': item_id,
                            'action': 'like'
                        })
                    
                    # 模拟收藏
                    if np.random.random() < interaction_tendency['collect'] * item_info['quality_score'] * 0.5:
                        feedback.append({
                            'user_id': user_id,
                            'note_id': item_id,
                            'action': 'collect'
                        })
        
        return pd.DataFrame(feedback)
    
    def analyze_results(self):
        """分析A/B测试结果"""
        print("\n" + "="*70)
        print("A/B Test Results Analysis")
        print("="*70)
        
        results = {}
        
        for group_name, data in self.test_results.items():
            feedback = data['feedback']
            
            # 计算在线指标
            metrics = {}
            
            # CTR
            impressions = len(feedback[feedback['action'] == 'impression'])
            clicks = len(feedback[feedback['action'] == 'click'])
            metrics['CTR'] = clicks / impressions if impressions > 0 else 0
            
            # 点赞率
            likes = len(feedback[feedback['action'] == 'like'])
            metrics['Like_Rate'] = likes / impressions if impressions > 0 else 0
            
            # 收藏率
            collects = len(feedback[feedback['action'] == 'collect'])
            metrics['Collect_Rate'] = collects / impressions if impressions > 0 else 0
            
            # 平均阅读时长
            read_data = feedback[feedback['action'] == 'read']
            metrics['Avg_Read_Time'] = read_data['duration'].mean() if len(read_data) > 0 else 0
            
            results[group_name] = metrics
        
        # 打印结果对比
        print(f"\n{'Metric':<20} {'Control':<15} {'CF':<15} {'CB':<15} {'Hybrid':<15}")
        print("-" * 70)
        
        for metric in ['CTR', 'Like_Rate', 'Collect_Rate', 'Avg_Read_Time']:
            print(f"{metric:<20}", end="")
            for group in ['control', 'cf', 'cb', 'hybrid']:
                value = results[group].get(metric, 0)
                print(f"{value:<15.4f}", end="")
            print()
        
        # 计算提升率
        print("\n" + "-" * 70)
        print("Lift vs Control (%)")
        print("-" * 70)
        
        for metric in ['CTR', 'Like_Rate', 'Collect_Rate', 'Avg_Read_Time']:
            print(f"{metric:<20}", end="")
            control_value = results['control'].get(metric, 0)
            for group in ['cf', 'cb', 'hybrid']:
                value = results[group].get(metric, 0)
                if control_value > 0:
                    lift = (value - control_value) / control_value * 100
                    print(f"{lift:+14.1f}%", end="")
                else:
                    print(f"{'N/A':<15}", end="")
            print()
        
        print("="*70)
        
        return results


def run_ab_test_simulation():
    """运行完整的A/B测试模拟"""
    print("="*70)
    print("ProteinHub A/B Testing Simulation")
    print("="*70)
    
    # 加载数据
    print("\nLoading data...")
    users = pd.read_csv('data/users.csv')
    items = pd.read_csv('data/notes_metadata.csv')
    
    # 合并特征数据
    features = pd.read_csv('data/note_features_complete.csv')
    items = items.merge(features[['note_id', 'overall_quality', 'popularity']], on='note_id', how='left')
    
    # 确保popularity列存在
    if 'popularity' not in items.columns or items['popularity'].isna().all():
        # 如果没有popularity，使用quality_score作为替代
        items['popularity'] = items.get('quality_score', 0.5)
    
    # 加载交互数据并合并
    views = pd.read_csv('data/views.csv')
    likes = pd.read_csv('data/likes.csv')
    collects = pd.read_csv('data/collects.csv')
    
    # 合并所有交互
    interactions = views[['user_id', 'note_id']].copy()
    interactions['rating'] = 1  # 浏览=1
    
    likes_filtered = likes[['user_id', 'note_id']].copy()
    likes_filtered['rating'] = 2  # 点赞=2
    
    collects_filtered = collects[['user_id', 'note_id']].copy()
    collects_filtered['rating'] = 3  # 收藏=3
    
    all_interactions = pd.concat([interactions, likes_filtered, collects_filtered], ignore_index=True)
    
    # 初始化模拟器
    simulator = ABTestSimulator(users, items, all_interactions)
    
    # 分组（50/50）
    simulator.split_users(split_ratio=0.5, strategy='stratified')
    
    # 设置推荐算法
    simulator.setup_recommenders()
    
    # 模拟实验
    simulator.simulate_experiment(experiment_duration_days=14, n_recommendations=10)
    
    # 分析结果
    results = simulator.analyze_results()
    
    return simulator, results


if __name__ == '__main__':
    simulator, results = run_ab_test_simulation()
