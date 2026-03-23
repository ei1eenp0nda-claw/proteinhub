"""
PPI推荐系统快速评估与模拟

无需真实用户，通过模拟用户行为获取量化指标
"""

import numpy as np
import pandas as pd
import torch
from typing import List, Dict, Tuple
from collections import defaultdict
import json


class SimulatedUser:
    """
    模拟用户
    
    基于真实用户行为分布建模:
    - 新手用户 (30%): 探索性强，点击率高但转化低
    - 普通用户 (50%): 稳定兴趣，中等活跃度  
    - 专家用户 (20%): 深耕领域，高质量互动
    """
    
    def __init__(self, user_id: int, user_type: str, interest_vector: np.ndarray):
        self.user_id = user_id
        self.user_type = user_type
        self.interest_vector = interest_vector
        
        # 根据类型设置行为参数
        if user_type == 'newbie':
            self.click_bias = 0.35      # 容易点击
            self.quality_threshold = 0.3  # 低质量门槛
            self.collect_prob = 0.05    # 低收藏率
            self.daily_sessions = np.random.poisson(3)
            
        elif user_type == 'regular':
            self.click_bias = 0.20
            self.quality_threshold = 0.5
            self.collect_prob = 0.15
            self.daily_sessions = np.random.poisson(8)
            
        else:  # expert
            self.click_bias = 0.12
            self.quality_threshold = 0.7
            self.collect_prob = 0.30
            self.daily_sessions = np.random.poisson(12)
        
        self.history = []
        self.satisfaction = 0.5
    
    def respond_to_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """
        模拟用户对推荐列表的响应
        
        Args:
            recommendations: [{item_id, features, quality_score}, ...]
            
        Returns:
            互动记录列表
        """
        interactions = []
        
        for pos, item in enumerate(recommendations):
            # 位置偏置 (越靠前越容易点击)
            position_bias = 1.0 / (1 + 0.15 * pos)
            
            # 计算相关性
            relevance = np.dot(self.interest_vector, item['features'])
            
            # 点击概率 (position-aware)
            click_prob = (
                self.click_bias *
                position_bias *
                (0.4 + 0.6 * relevance) *
                (0.5 + 0.5 * item['quality_score'])
            )
            
            if np.random.random() < click_prob:
                # 点击了
                read_prob = relevance * (0.3 + 0.7 * item['quality_score'])
                
                if np.random.random() < read_prob:
                    # 深度阅读
                    read_time = np.random.exponential(120) * (0.5 + relevance + item['quality_score'])
                    is_deep = read_time > 60
                    
                    # 互动决策
                    like_prob = self.click_bias * relevance * item['quality_score']
                    collect_prob = self.collect_prob * relevance * item['quality_score']
                    
                    interactions.append({
                        'user_id': self.user_id,
                        'item_id': item['item_id'],
                        'position': pos,
                        'action': 'deep_read',
                        'read_time': min(read_time, 600),
                        'liked': np.random.random() < like_prob,
                        'collected': np.random.random() < collect_prob,
                        'relevance': relevance,
                        'quality': item['quality_score']
                    })
                    
                    # 更新满意度
                    self.satisfaction = 0.9 * self.satisfaction + 0.1 * relevance
                else:
                    # 浅度浏览
                    interactions.append({
                        'user_id': self.user_id,
                        'item_id': item['item_id'],
                        'position': pos,
                        'action': 'shallow_read',
                        'read_time': np.random.exponential(20),
                        'liked': False,
                        'collected': False,
                        'relevance': relevance,
                        'quality': item['quality_score']
                    })
            else:
                # 曝光未点击
                interactions.append({
                    'user_id': self.user_id,
                    'item_id': item['item_id'],
                    'position': pos,
                    'action': 'impression',
                    'read_time': 0,
                    'liked': False,
                    'collected': False,
                    'relevance': relevance,
                    'quality': item['quality_score']
                })
        
        self.history.extend(interactions)
        return interactions


class QuickEvaluator:
    """
    快速评估器
    
    生成模拟用户并与推荐系统交互，输出量化指标
    """
    
    def __init__(self, num_users: int = 500, num_items: int = 1000):
        self.num_users = num_users
        self.num_items = num_items
        self.users = []
        self.items = []
        self.logs = []
        
    def setup_simulation(self, item_metadata: Optional[Dict] = None):
        """
        设置模拟环境
        
        Args:
            item_metadata: 物品元数据 {item_id: {features, quality}}
        """
        print(f"🎲 设置模拟环境: {self.num_users}用户 × {self.num_items}物品")
        
        # 生成物品
        if item_metadata is None:
            self.items = self._generate_synthetic_items()
        else:
            self.items = item_metadata
        
        # 生成模拟用户
        self.users = self._generate_users()
        
        print(f"  用户分布: 新手{sum(1 for u in self.users if u.user_type=='newbie')} / "
              f"普通{sum(1 for u in self.users if u.user_type=='regular')} / "
              f"专家{sum(1 for u in self.users if u.user_type=='expert')}")
    
    def _generate_synthetic_items(self) -> Dict:
        """生成合成物品数据"""
        items = {}
        
        for i in range(self.num_items):
            item_id = f"protein_{i:04d}"
            
            # 随机特征向量 (模拟蛋白家族分布)
            features = np.random.dirichlet(np.ones(20))
            
            # 质量分数 (beta分布，大部分中等质量)
            quality = np.random.beta(3, 2)
            
            # 热度 (基于质量+随机)
            popularity = quality * (0.5 + 0.5 * np.random.random())
            
            items[item_id] = {
                'item_id': item_id,
                'features': features,
                'quality_score': quality,
                'popularity': popularity,
                'family': f"FAMILY_{i % 20}"
            }
        
        return items
    
    def _generate_users(self) -> List[SimulatedUser]:
        """生成模拟用户"""
        users = []
        
        for i in range(self.num_users):
            # 用户类型分布
            user_type = np.random.choice(
                ['newbie', 'regular', 'expert'],
                p=[0.3, 0.5, 0.2]
            )
            
            # 兴趣向量 (模拟对20个蛋白家族的偏好)
            if user_type == 'expert':
                # 专家兴趣集中
                interest = np.random.dirichlet(np.ones(20) * 2)
            elif user_type == 'regular':
                # 普通用户兴趣适中
                interest = np.random.dirichlet(np.ones(20))
            else:
                # 新手兴趣分散
                interest = np.random.dirichlet(np.ones(20) * 0.5)
            
            users.append(SimulatedUser(i, user_type, interest))
        
        return users
    
    def run_simulation(self, recommender_fn, days: int = 7) -> pd.DataFrame:
        """
        运行模拟实验
        
        Args:
            recommender_fn: 推荐函数 fn(user_id, top_k) -> [(item_id, score), ...]
            days: 模拟天数
            
        Returns:
            交互日志DataFrame
        """
        print(f"🚀 运行模拟实验 ({days}天)...")
        
        all_logs = []
        item_list = list(self.items.values())
        
        for day in range(days):
            day_logs = []
            
            for user in self.users:
                # 每日会话数
                n_sessions = np.random.poisson(user.daily_sessions)
                
                for _ in range(n_sessions):
                    # 获取推荐
                    recs = recommender_fn(user.user_id, top_k=10)
                    
                    # 组装推荐详情
                    rec_details = []
                    for item_id, score in recs:
                        if item_id in self.items:
                            item = self.items[item_id].copy()
                            item['rec_score'] = score
                            rec_details.append(item)
                        elif isinstance(item_id, int) and item_id < len(item_list):
                            item = item_list[item_id].copy()
                            item['rec_score'] = score
                            rec_details.append(item)
                    
                    if not rec_details:
                        # 随机推荐作为fallback
                        rec_details = np.random.choice(item_list, size=10, replace=False).tolist()
                    
                    # 模拟用户响应
                    interactions = user.respond_to_recommendations(rec_details)
                    
                    for inter in interactions:
                        inter['day'] = day
                    
                    day_logs.extend(interactions)
            
            all_logs.extend(day_logs)
            
            if (day + 1) % 2 == 0 or day == 0:
                metrics = self._calculate_daily_metrics(day_logs)
                print(f"  Day {day+1}: CTR={metrics['ctr']:.3f}, "
                      f"Collect={metrics['collect_rate']:.3f}, "
                      f"DeepRead={metrics['deep_read_rate']:.3f}")
        
        self.logs = pd.DataFrame(all_logs)
        print(f"✅ 模拟完成: 共{len(self.logs)}条交互记录")
        
        return self.logs
    
    def _calculate_daily_metrics(self, logs: List[Dict]) -> Dict:
        """计算单日指标"""
        if not logs:
            return {'ctr': 0, 'collect_rate': 0, 'deep_read_rate': 0}
        
        df = pd.DataFrame(logs)
        
        total = len(df)
        clicks = len(df[df['action'] != 'impression'])
        deep_reads = len(df[df['action'] == 'deep_read'])
        collects = df['collected'].sum()
        
        return {
            'ctr': clicks / total if total > 0 else 0,
            'collect_rate': collects / total if total > 0 else 0,
            'deep_read_rate': deep_reads / clicks if clicks > 0 else 0,
            'avg_read_time': df[df['read_time'] > 0]['read_time'].mean() if len(df[df['read_time'] > 0]) > 0 else 0
        }
    
    def calculate_metrics(self) -> Dict:
        """
        计算完整评估指标
        
        Returns:
            指标字典
        """
        if self.logs is None or len(self.logs) == 0:
            raise ValueError("没有日志数据，请先运行模拟")
        
        df = self.logs
        
        metrics = {
            # ========== 在线指标 ==========
            'online': {
                'CTR': self._safe_div(len(df[df['action'] != 'impression']), len(df)),
                'Deep_Read_Rate': self._safe_div(
                    len(df[df['action'] == 'deep_read']),
                    len(df[df['action'] != 'impression'])
                ),
                'Like_Rate': df['liked'].mean(),
                'Collect_Rate': df['collected'].mean(),
                'Avg_Read_Time': df[df['read_time'] > 0]['read_time'].mean(),
                
                # 位置偏置分析
                'CTR_Top3': self._calculate_ctr_at_position(df, 3),
                'CTR_Top5': self._calculate_ctr_at_position(df, 5),
                'CTR_Top10': self._calculate_ctr_at_position(df, 10),
            },
            
            # ========== 用户分群指标 ==========
            'user_segments': self._calculate_segment_metrics(df),
            
            # ========== 物品覆盖指标 ==========
            'coverage': {
                'Item_Coverage': df['item_id'].nunique() / self.num_items,
                'Gini_Coefficient': self._calculate_gini(df),
            }
        }
        
        return metrics
    
    def _safe_div(self, a, b):
        """安全除法"""
        return a / b if b > 0 else 0
    
    def _calculate_ctr_at_position(self, df: pd.DataFrame, k: int) -> float:
        """计算Top-K位置的CTR"""
        top_k = df[df['position'] < k]
        if len(top_k) == 0:
            return 0
        return len(top_k[top_k['action'] != 'impression']) / len(top_k)
    
    def _calculate_segment_metrics(self, df: pd.DataFrame) -> Dict:
        """计算分群指标"""
        # 需要用户信息
        user_types = {}
        for user in self.users:
            user_types[user.user_id] = user.user_type
        
        df['user_type'] = df['user_id'].map(user_types)
        
        segments = {}
        for utype in ['newbie', 'regular', 'expert']:
            type_df = df[df['user_type'] == utype]
            if len(type_df) > 0:
                segments[utype] = {
                    'CTR': self._safe_div(
                        len(type_df[type_df['action'] != 'impression']),
                        len(type_df)
                    ),
                    'Collect_Rate': type_df['collected'].mean(),
                    'Deep_Read_Rate': self._safe_div(
                        len(type_df[type_df['action'] == 'deep_read']),
                        len(type_df[type_df['action'] != 'impression'])
                    ),
                    'Avg_Read_Time': type_df[type_df['read_time'] > 0]['read_time'].mean()
                }
        
        return segments
    
    def _calculate_gini(self, df: pd.DataFrame) -> float:
        """计算Gini系数 (衡量曝光分布不均)"""
        exposure_counts = df['item_id'].value_counts().values
        n = len(exposure_counts)
        if n == 0:
            return 0
        
        index = np.arange(1, n + 1)
        exposures_sorted = np.sort(exposure_counts)
        
        gini = (2 * np.sum(index * exposures_sorted)) / (n * np.sum(exposures_sorted)) - (n + 1) / n
        return gini
    
    def print_report(self, metrics: Dict):
        """打印评估报告"""
        print("\n" + "="*60)
        print("ProteinHub 推荐系统评估报告 (模拟)")
        print("="*60)
        
        # 在线指标
        print("\n📊 在线指标:")
        print("-" * 40)
        online = metrics['online']
        print(f"  CTR (整体):          {online['CTR']:.3f} ({online['CTR']*100:.1f}%)")
        print(f"  CTR (Top 3):         {online['CTR_Top3']:.3f}")
        print(f"  CTR (Top 5):         {online['CTR_Top5']:.3f}")
        print(f"  深度阅读率:          {online['Deep_Read_Rate']:.3f}")
        print(f"  点赞率:              {online['Like_Rate']:.3f}")
        print(f"  收藏率:              {online['Collect_Rate']:.3f}")
        print(f"  平均阅读时长:        {online['Avg_Read_Time']:.1f}s")
        
        # 分群指标
        print("\n👥 用户分群表现:")
        print("-" * 40)
        print(f"{'类型':<12} {'CTR':>8} {'收藏率':>8} {'深度阅读':>8}")
        print("-" * 40)
        for utype, m in metrics['user_segments'].items():
            print(f"{utype:<12} {m['CTR']:>8.3f} {m['Collect_Rate']:>8.3f} {m['Deep_Read_Rate']:>8.3f}")
        
        # 覆盖指标
        print("\n📈 覆盖指标:")
        print("-" * 40)
        coverage = metrics['coverage']
        print(f"  物品覆盖率:          {coverage['Item_Coverage']:.1%}")
        print(f"  Gini系数:            {coverage['Gini_Coefficient']:.3f}")
        print(f"    (0=完全均匀, 1=极度不均)")
        
        print("\n" + "="*60)


# ==================== 快速测试接口 ====================

def quick_evaluate_recommender(recommender_fn, 
                                num_users: int = 500,
                                num_items: int = 1000,
                                simulation_days: int = 7) -> Dict:
    """
    快速评估推荐算法
    
    Args:
        recommender_fn: 推荐函数 (user_id, top_k) -> [(item_id, score), ...]
        num_users: 模拟用户数量
        num_items: 物品数量
        simulation_days: 模拟天数
        
    Returns:
        完整指标字典
    """
    evaluator = QuickEvaluator(num_users, num_items)
    evaluator.setup_simulation()
    evaluator.run_simulation(recommender_fn, days=simulation_days)
    metrics = evaluator.calculate_metrics()
    evaluator.print_report(metrics)
    
    return metrics


def compare_recommenders(recommender_dict: Dict[str, callable],
                         num_users: int = 500,
                         simulation_days: int = 7):
    """
    对比多个推荐算法
    
    Args:
        recommender_dict: {算法名: 推荐函数}
    """
    print("\n" + "="*70)
    print("推荐算法对比实验")
    print("="*70)
    
    results = {}
    
    for name, fn in recommender_dict.items():
        print(f"\n>>> 测试算法: {name}")
        evaluator = QuickEvaluator(num_users, num_items=1000)
        evaluator.setup_simulation()
        evaluator.run_simulation(fn, days=simulation_days)
        metrics = evaluator.calculate_metrics()
        results[name] = metrics
    
    # 对比表格
    print("\n" + "="*70)
    print("对比结果")
    print("="*70)
    
    print(f"\n{'指标':<20}", end="")
    for name in recommender_dict.keys():
        print(f"{name:<15}", end="")
    print()
    print("-" * 70)
    
    metrics_to_show = ['CTR', 'Collect_Rate', 'Deep_Read_Rate', 'Like_Rate']
    for metric in metrics_to_show:
        print(f"{metric:<20}", end="")
        for name in recommender_dict.keys():
            value = results[name]['online'].get(metric, 0)
            print(f"{value:<15.3f}", end="")
        print()
    
    print("="*70)
    
    return results


# 示例推荐算法 (用于测试)

def random_recommender(user_id: int, top_k: int = 10) -> List[Tuple[int, float]]:
    """随机推荐 (基线)"""
    items = np.random.choice(1000, size=top_k, replace=False)
    return [(int(i), np.random.random()) for i in items]


def popularity_recommender(user_id: int, top_k: int = 10) -> List[Tuple[int, float]]:
    """热度推荐 (基线)"""
    # 模拟热度排序
    popular_items = np.argsort(np.random.beta(2, 5, 1000))[-top_k:][::-1]
    return [(int(i), 0.5 + 0.5 * (top_k - idx) / top_k) 
            for idx, i in enumerate(popular_items)]


def simple_ppi_recommender(ppi_graph, user_interests: Dict):
    """
    简单的PPI-aware推荐
    
    基于用户兴趣，在PPI图上进行传播
    """
    def recommend(user_id: int, top_k: int = 10):
        # 获取用户兴趣
        interest = user_interests.get(user_id, np.random.dirichlet(np.ones(20)))
        
        # 基于兴趣选择种子蛋白
        seed_proteins = np.argsort(interest)[-3:]
        
        # 在PPI图上扩散 (简化版：随机选择邻居)
        candidates = set()
        for seed in seed_proteins:
            candidates.add(seed)
            # 添加邻居
            if ppi_graph is not None:
                neighbors = ppi_graph.get_neighbors(seed, top_k=5)
                candidates.update([n[0] for n in neighbors])
        
        # 评分并排序
        scores = []
        for item in candidates:
            # 相关性评分
            item_vec = np.random.dirichlet(np.ones(20))  # 模拟物品特征
            score = np.dot(interest, item_vec)
            scores.append((item, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    return recommend


if __name__ == '__main__':
    print("PPI推荐系统快速评估模块")
    print("="*50)
    
    # 快速测试
    print("\n>>> 测试随机推荐 (基线)")
    metrics = quick_evaluate_recommender(
        random_recommender,
        num_users=200,
        simulation_days=3
    )
    
    print("\n>>> 测试热度推荐 (基线)")
    metrics = quick_evaluate_recommender(
        popularity_recommender,
        num_users=200,
        simulation_days=3
    )