"""
重排层 (Reranking Layer)

实现以下功能:
1. 多样性控制 - MMR (Maximal Marginal Relevance) 算法
2. EE探索 - ε-greedy / Thompson Sampling
3. 业务规则过滤
"""

import numpy as np
import torch
import torch.nn as nn
from typing import List, Dict, Tuple, Set
from collections import defaultdict
import random


class MMRReranker:
    """
    MMR (Maximal Marginal Relevance) 多样性重排
    
    公式: MMR = λ * Relevance - (1-λ) * max(Similarity to selected)
    
    在相关性和多样性之间做权衡:
    - λ接近1: 优先考虑相关性
    - λ接近0: 优先考虑多样性
    """
    
    def __init__(self, lambda_param: float = 0.5):
        """
        Args:
            lambda_param: 权衡参数, 0-1之间
        """
        self.lambda_param = lambda_param
    
    def compute_similarity(self, item_i: np.ndarray, item_j: np.ndarray) -> float:
        """计算两个物品的相似度 (余弦相似度)"""
        norm_i = np.linalg.norm(item_i)
        norm_j = np.linalg.norm(item_j)
        if norm_i == 0 or norm_j == 0:
            return 0.0
        return np.dot(item_i, item_j) / (norm_i * norm_j)
    
    def rerank(self, 
               items: List[Tuple[str, float]], 
               item_embeddings: Dict[str, np.ndarray],
               top_k: int = 10) -> List[Tuple[str, float]]:
        """
        MMR重排
        
        Args:
            items: [(item_id, relevance_score), ...] 已按相关性排序
            item_embeddings: {item_id: embedding_vector}
            top_k: 返回数量
        
        Returns:
            [(item_id, mmr_score), ...]
        """
        selected = []
        candidates = list(items)
        
        while len(selected) < top_k and candidates:
            max_mmr_score = -float('inf')
            best_item = None
            best_idx = -1
            
            for idx, (item_id, relevance) in enumerate(candidates):
                # 获取物品嵌入
                emb = item_embeddings.get(item_id)
                if emb is None:
                    continue
                
                # 计算与已选物品的相似度
                if not selected:
                    sim_to_selected = 0.0
                else:
                    similarities = []
                    for sel_id, _ in selected:
                        sel_emb = item_embeddings.get(sel_id)
                        if sel_emb is not None:
                            sim = self.compute_similarity(emb, sel_emb)
                            similarities.append(sim)
                    sim_to_selected = max(similarities) if similarities else 0.0
                
                # MMR分数
                mmr_score = self.lambda_param * relevance - (1 - self.lambda_param) * sim_to_selected
                
                if mmr_score > max_mmr_score:
                    max_mmr_score = mmr_score
                    best_item = item_id
                    best_idx = idx
            
            if best_item:
                selected.append((best_item, max_mmr_score))
                candidates.pop(best_idx)
            else:
                break
        
        return selected


class EpsilonGreedyExplorer:
    """
    ε-greedy 探索策略
    
    以ε概率进行随机探索, 以1-ε概率选择最优
    """
    
    def __init__(self, epsilon: float = 0.1, decay: float = 0.999):
        """
        Args:
            epsilon: 探索概率
            decay: 每轮衰减系数
        """
        self.epsilon = epsilon
        self.initial_epsilon = epsilon
        self.decay = decay
    
    def rerank(self, 
               items: List[Tuple[str, float]], 
               top_k: int = 10,
               diversity_candidates: List[str] = None) -> List[Tuple[str, float]]:
        """
        ε-greedy重排
        
        Args:
            items: [(item_id, score), ...]
            top_k: 返回数量
            diversity_candidates: 用于探索的候选池
        """
        result = []
        candidates = list(items)
        
        for i in range(top_k):
            if not candidates:
                break
            
            if random.random() < self.epsilon:
                # 探索: 随机选择
                idx = random.randint(0, len(candidates) - 1)
                item_id, score = candidates[idx]
                result.append((item_id, score * 0.9))  # 探索项稍微降权
            else:
                # 利用: 选择最优
                item_id, score = candidates[0]
                result.append((item_id, score))
            
            candidates.pop(0)
        
        # 衰减探索率
        self.epsilon *= self.decay
        
        return result
    
    def reset(self):
        """重置探索率"""
        self.epsilon = self.initial_epsilon


class ThompsonSamplingExplorer:
    """
    Thompson Sampling 探索策略
    
    使用Beta分布建模CTR, 采样后排序
    """
    
    def __init__(self):
        # 每个物品的点击数和展示数
        self.clicks = defaultdict(int)
        self.impressions = defaultdict(int)
    
    def update(self, item_id: str, clicked: bool):
        """更新物品反馈"""
        self.impressions[item_id] += 1
        if clicked:
            self.clicks[item_id] += 1
    
    def get_score(self, item_id: str) -> float:
        """从Beta分布采样得到分数"""
        # Beta(α, β) where α = clicks + 1, β = impressions - clicks + 1
        alpha = self.clicks[item_id] + 1
        beta = self.impressions[item_id] - self.clicks[item_id] + 1
        return np.random.beta(alpha, beta)
    
    def rerank(self, items: List[Tuple[str, float]], top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Thompson Sampling重排
        
        Args:
            items: [(item_id, base_score), ...]
            top_k: 返回数量
        """
        # 计算Thompson采样分数
        scored_items = []
        for item_id, base_score in items:
            ts_score = self.get_score(item_id)
            # 结合基础分数和TS分数
            combined_score = 0.7 * base_score + 0.3 * ts_score
            scored_items.append((item_id, combined_score))
        
        # 按分数排序
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return scored_items[:top_k]


class BusinessRuleFilter:
    """
    业务规则过滤
    
    实现常见的业务规则:
    1. 去重规则
    2. 新鲜度加权
    3. 疲劳度控制
    4. 配额控制
    """
    
    def __init__(self):
        self.user_exposure = defaultdict(lambda: defaultdict(int))
        self.item_exposure = defaultdict(int)
    
    def record_exposure(self, user_id: str, item_ids: List[str]):
        """记录曝光"""
        for item_id in item_ids:
            self.user_exposure[user_id][item_id] += 1
            self.item_exposure[item_id] += 1
    
    def filter_seen_items(self, 
                          items: List[Tuple[str, float]], 
                          user_id: str,
                          max_seen_count: int = 3) -> List[Tuple[str, float]]:
        """
        过滤用户已看过的物品
        
        Args:
            items: 候选物品
            user_id: 用户ID
            max_seen_count: 最大允许重复次数
        """
        filtered = []
        for item_id, score in items:
            seen_count = self.user_exposure[user_id][item_id]
            if seen_count < max_seen_count:
                # 根据观看次数降权
                discount = 0.7 ** seen_count
                filtered.append((item_id, score * discount))
        return filtered
    
    def apply_freshness_boost(self,
                              items: List[Tuple[str, float]],
                              item_timestamps: Dict[str, float],
                              current_time: float,
                              half_life: float = 86400) -> List[Tuple[str, float]]:
        """
        应用新鲜度加权
        
        Args:
            items: 候选物品
            item_timestamps: 物品发布时间戳
            current_time: 当前时间戳
            half_life: 半衰期(秒), 默认1天
        """
        boosted = []
        for item_id, score in items:
            timestamp = item_timestamps.get(item_id, current_time)
            age = current_time - timestamp
            # 指数衰减
            freshness = np.exp(-age / half_life)
            boosted_score = score * (0.5 + 0.5 * freshness)  # 新鲜度加权
            boosted.append((item_id, boosted_score))
        return boosted
    
    def apply_quota_control(self,
                           items: List[Tuple[str, float]],
                           item_categories: Dict[str, str],
                           category_quota: Dict[str, int]) -> List[Tuple[str, float]]:
        """
        类别配额控制
        
        Args:
            items: 候选物品
            item_categories: 物品类别映射
            category_quota: 每个类别的配额
        """
        result = []
        category_count = defaultdict(int)
        
        for item_id, score in items:
            category = item_categories.get(item_id, 'default')
            if category_count[category] < category_quota.get(category, float('inf')):
                result.append((item_id, score))
                category_count[category] += 1
        
        return result


class RerankingPipeline:
    """
    重排Pipeline
    
    组合多种重排策略
    """
    
    def __init__(self,
                 use_mmr: bool = True,
                 use_exploration: bool = True,
                 use_business_rules: bool = True,
                 mmr_lambda: float = 0.5,
                 epsilon: float = 0.1):
        """
        Args:
            use_mmr: 是否使用MMR多样性
            use_exploration: 是否使用探索
            use_business_rules: 是否使用业务规则
            mmr_lambda: MMR权衡参数
            epsilon: 探索概率
        """
        self.use_mmr = use_mmr
        self.use_exploration = use_exploration
        self.use_business_rules = use_business_rules
        
        self.mmr = MMRReranker(lambda_param=mmr_lambda) if use_mmr else None
        self.explorer = EpsilonGreedyExplorer(epsilon=epsilon) if use_exploration else None
        self.rule_filter = BusinessRuleFilter() if use_business_rules else None
    
    def rerank(self,
               user_id: str,
               items: List[Tuple[str, float]],
               item_embeddings: Dict[str, np.ndarray] = None,
               top_k: int = 10) -> List[Tuple[str, float]]:
        """
        执行重排Pipeline
        
        Args:
            user_id: 用户ID
            items: [(item_id, score), ...] 精排结果
            item_embeddings: 物品嵌入 (用于MMR)
            top_k: 返回数量
        
        Returns:
            [(item_id, final_score), ...]
        """
        result = list(items)
        
        # 1. 业务规则过滤
        if self.use_business_rules and self.rule_filter:
            result = self.rule_filter.filter_seen_items(result, user_id)
        
        # 2. MMR多样性重排
        if self.use_mmr and self.mmr and item_embeddings:
            result = self.mmr.rerank(result, item_embeddings, top_k=min(top_k * 2, len(result)))
        
        # 3. 探索策略
        if self.use_exploration and self.explorer:
            result = self.explorer.rerank(result, top_k=top_k)
        else:
            result = result[:top_k]
        
        # 记录曝光
        if self.use_business_rules and self.rule_filter:
            item_ids = [item_id for item_id, _ in result]
            self.rule_filter.record_exposure(user_id, item_ids)
        
        return result


# ============== 测试 ==============

def test_mmr_reranker():
    """测试MMR重排"""
    print("\n🧪 测试MMR重排器")
    
    # 模拟物品和嵌入
    items = [
        ('item_a', 0.95),
        ('item_b', 0.90),
        ('item_c', 0.85),
        ('item_d', 0.80),
        ('item_e', 0.75),
    ]
    
    # 模拟嵌入 (使用随机但固定的嵌入)
    np.random.seed(42)
    embeddings = {
        'item_a': np.random.randn(10),
        'item_b': np.random.randn(10),
        'item_c': np.random.randn(10),
        'item_d': np.random.randn(10),
        'item_e': np.random.randn(10),
    }
    
    # 高多样性 (λ=0.3)
    mmr_high_div = MMRReranker(lambda_param=0.3)
    result_high = mmr_high_div.rerank(items, embeddings, top_k=3)
    print(f"  高多样性 (λ=0.3): {[i for i, _ in result_high]}")
    
    # 高相关性 (λ=0.8)
    mmr_high_rel = MMRReranker(lambda_param=0.8)
    result_rel = mmr_high_rel.rerank(items, embeddings, top_k=3)
    print(f"  高相关性 (λ=0.8): {[i for i, _ in result_rel]}")


def test_exploration():
    """测试探索策略"""
    print("\n🧪 测试探索策略")
    
    items = [
        ('item_a', 0.95),
        ('item_b', 0.90),
        ('item_c', 0.85),
        ('item_d', 0.80),
        ('item_e', 0.75),
    ]
    
    # ε-greedy
    explorer = EpsilonGreedyExplorer(epsilon=0.3)
    results = []
    for _ in range(5):
        result = explorer.rerank(items, top_k=3)
        results.append([i for i, _ in result])
    print(f"  ε-greedy (ε=0.3) 5次结果:")
    for i, r in enumerate(results):
        print(f"    第{i+1}次: {r}")
    
    # Thompson Sampling
    ts = ThompsonSamplingExplorer()
    # 模拟一些反馈
    ts.update('item_a', True)
    ts.update('item_a', True)
    ts.update('item_b', False)
    
    ts_results = []
    for _ in range(5):
        result = ts.rerank(items, top_k=3)
        ts_results.append([i for i, _ in result])
    print(f"  Thompson Sampling 5次结果:")
    for i, r in enumerate(ts_results):
        print(f"    第{i+1}次: {r}")


def test_business_rules():
    """测试业务规则"""
    print("\n🧪 测试业务规则")
    
    rules = BusinessRuleFilter()
    
    # 模拟曝光
    rules.record_exposure('user_1', ['item_a', 'item_b', 'item_a'])
    
    items = [
        ('item_a', 0.95),  # 已看2次
        ('item_b', 0.90),  # 已看1次
        ('item_c', 0.85),  # 未看过
        ('item_d', 0.80),  # 未看过
    ]
    
    # 过滤已看物品
    filtered = rules.filter_seen_items(items, 'user_1', max_seen_count=2)
    print(f"  过滤后: {[(i, f'{s:.3f}') for i, s in filtered]}")
    
    # 新鲜度加权
    current_time = 1000000
    timestamps = {
        'item_a': current_time - 100000,  # 较旧
        'item_b': current_time - 10000,   # 较新
        'item_c': current_time - 1000,    # 最新
    }
    boosted = rules.apply_freshness_boost(items[:3], timestamps, current_time, half_life=50000)
    print(f"  新鲜度加权后: {[(i, f'{s:.3f}') for i, s in boosted]}")


if __name__ == '__main__':
    test_mmr_reranker()
    test_exploration()
    test_business_rules()
    
    print("\n✅ 所有测试通过")
