"""
负采样改进的BPR训练

核心改进:
1. 从PPI互作网络中采样"硬负例"(互作但不点击)
2. 从同家族采样相似负例
3. 动态调整采样概率
"""

import torch
import torch.nn as nn
import numpy as np
from typing import List, Tuple, Dict, Set
from collections import defaultdict


class PPINegativeSampler:
    """
    PPI-aware负采样器
    
    策略:
    - 基础: 均匀随机采样
    - PPI-hard: 从PPI互作邻居中采样(蛋白相关但用户未互动)
    - Family-hard: 从同家族采样
    - Popularity: 基于热度采样(热门但用户未点)
    """
    
    def __init__(self, n_items: int, ppi_pairs: List[Tuple[int, int, float]] = None,
                 item_family: Dict[int, str] = None, alpha: float = 0.5):
        """
        Args:
            n_items: 物品总数
            ppi_pairs: PPI互作对 [(p1, p2, weight), ...]
            item_family: {item_id: family_name}
            alpha: 混合采样权重
        """
        self.n_items = n_items
        self.alpha = alpha
        
        # 构建PPI邻接表
        self.ppi_neighbors = defaultdict(list)
        if ppi_pairs:
            for p1, p2, weight in ppi_pairs:
                self.ppi_neighbors[p1].append((p2, weight))
                self.ppi_neighbors[p2].append((p1, weight))
        
        # 构建家族映射
        self.family_items = defaultdict(list)
        self.item_family = item_family or {}
        if item_family:
            for item_id, family in item_family.items():
                self.family_items[family].append(item_id)
        
        # 热度分布 (用于popularity采样)
        self.popularity = np.ones(n_items)
    
    def set_popularity(self, popularity: np.ndarray):
        """设置物品热度分布"""
        self.popularity = popularity
    
    def sample_uniform(self, pos_items: Set[int], n_samples: int) -> List[int]:
        """
        均匀随机采样
        
        Args:
            pos_items: 正例集合
            n_samples: 采样数量
            
        Returns:
            负例列表
        """
        negatives = []
        all_items = set(range(self.n_items))
        
        while len(negatives) < n_samples:
            # 从非正例中均匀采样
            candidates = list(all_items - pos_items - set(negatives))
            if not candidates:
                break
            
            neg = np.random.choice(candidates)
            negatives.append(neg)
        
        return negatives
    
    def sample_ppi_hard(self, user_id: int, pos_items: Set[int],
                       n_samples: int) -> List[int]:
        """
        从PPI互作邻居中采样"硬负例"
        
        思路: 与用户已互动蛋白有互作的蛋白，用户可能感兴趣但没点
        """
        negatives = []
        
        # 收集所有正例的PPI邻居
        neighbor_candidates = []
        for pos_item in pos_items:
            for neighbor, weight in self.ppi_neighbors.get(pos_item, []):
                if neighbor not in pos_items and neighbor not in negatives:
                    neighbor_candidates.append((neighbor, weight))
        
        # 按权重排序，优先采样强互作
        neighbor_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 采样
        for neg, _ in neighbor_candidates:
            if len(negatives) >= n_samples:
                break
            negatives.append(neg)
        
        # 如果不够，用均匀采样补充
        if len(negatives) < n_samples:
            negatives.extend(self.sample_uniform(
                pos_items | set(negatives),
                n_samples - len(negatives)
            ))
        
        return negatives[:n_samples]
    
    def sample_family_hard(self, user_id: int, pos_items: Set[int],
                          n_samples: int) -> List[int]:
        """
        从同家族采样"硬负例"
        
        思路: 同家族的蛋白功能相似，用户可能感兴趣但没点
        """
        negatives = []
        
        # 收集正例所在家族
        pos_families = set()
        for pos_item in pos_items:
            if pos_item in self.item_family:
                pos_families.add(self.item_family[pos_item])
        
        # 从这些家族采样
        for family in pos_families:
            family_candidates = [
                item for item in self.family_items[family]
                if item not in pos_items and item not in negatives
            ]
            
            if family_candidates:
                n_from_family = min(
                    n_samples // len(pos_families) + 1,
                    len(family_candidates)
                )
                sampled = np.random.choice(
                    family_candidates,
                    size=n_from_family,
                    replace=False
                ).tolist()
                negatives.extend(sampled)
        
        # 补充
        if len(negatives) < n_samples:
            negatives.extend(self.sample_uniform(
                pos_items | set(negatives),
                n_samples - len(negatives)
            ))
        
        return negatives[:n_samples]
    
    def sample_popularity(self, pos_items: Set[int], n_samples: int) -> List[int]:
        """
        基于热度采样
        
        思路: 热门但用户没点的物品，可能是"隐形负例"
        """
        # 构建概率分布 (排除正例)
        probs = self.popularity.copy()
        for pos in pos_items:
            probs[pos] = 0
        
        # 归一化
        total = probs.sum()
        if total > 0:
            probs = probs / total
        else:
            return self.sample_uniform(pos_items, n_samples)
        
        # 采样
        candidates = list(range(self.n_items))
        negatives = np.random.choice(
            candidates,
            size=min(n_samples, len(candidates) - len(pos_items)),
            replace=False,
            p=probs
        ).tolist()
        
        return negatives
    
    def sample_mixed(self, user_id: int, pos_items: Set[int],
                    n_samples: int, strategy: str = 'ppi') -> List[int]:
        """
        混合采样策略
        
        Args:
            strategy: 'ppi', 'family', 'popularity', 'uniform', 'adaptive'
        """
        if strategy == 'ppi':
            return self.sample_ppi_hard(user_id, pos_items, n_samples)
        elif strategy == 'family':
            return self.sample_family_hard(user_id, pos_items, n_samples)
        elif strategy == 'popularity':
            return self.sample_popularity(pos_items, n_samples)
        elif strategy == 'uniform':
            return self.sample_uniform(pos_items, n_samples)
        elif strategy == 'adaptive':
            # 自适应: 根据正例数量选择策略
            if len(pos_items) > 10 and self.ppi_neighbors:
                return self.sample_ppi_hard(user_id, pos_items, n_samples)
            elif self.family_items:
                return self.sample_family_hard(user_id, pos_items, n_samples)
            else:
                return self.sample_uniform(pos_items, n_samples)
        else:
            return self.sample_uniform(pos_items, n_samples)


class BPRTrainer:
    """
    BPR训练器 (支持多种负采样策略)
    
    BPR损失: -log(sigmoid(score_pos - score_neg))
    """
    
    def __init__(self, model: nn.Module, sampler: PPINegativeSampler,
                 lr: float = 0.001, reg: float = 0.001):
        self.model = model
        self.sampler = sampler
        self.optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        self.reg = reg
    
    def train_epoch(self, interactions: Dict[int, Set[int]],
                    n_negatives: int = 1,
                    strategy: str = 'ppi') -> float:
        """
        训练一个epoch
        
        Args:
            interactions: {user_id: set of pos_items}
            n_negatives: 每个正例配几个负例
            strategy: 采样策略
            
        Returns:
            平均损失
        """
        self.model.train()
        total_loss = 0
        n_batches = 0
        
        for user_id, pos_items in interactions.items():
            if len(pos_items) == 0:
                continue
            
            # 为每个正例采样负例
            for pos_item in pos_items:
                neg_items = self.sampler.sample_mixed(
                    user_id, pos_items, n_negatives, strategy
                )
                
                for neg_item in neg_items:
                    loss = self._train_step(user_id, pos_item, neg_item)
                    total_loss += loss
                    n_batches += 1
        
        return total_loss / max(n_batches, 1)
    
    def _train_step(self, user_id: int, pos_item: int, neg_item: int) -> float:
        """单步训练"""
        self.optimizer.zero_grad()
        
        # 前向
        score_pos = self.model(user_id, pos_item)
        score_neg = self.model(user_id, neg_item)
        
        # BPR损失
        diff = score_pos - score_neg
        loss = -torch.log(torch.sigmoid(diff) + 1e-10)
        
        # L2正则
        if hasattr(self.model, 'get_l2_reg'):
            loss += self.reg * self.model.get_l2_reg()
        
        # 反向
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    def fit(self, interactions: Dict[int, Set[int]], epochs: int = 100,
            n_negatives: int = 1, strategy: str = 'ppi',
            eval_interval: int = 10):
        """
        完整训练流程
        """
        print(f"🔄 BPR训练 (策略: {strategy})...")
        
        for epoch in range(epochs):
            loss = self.train_epoch(interactions, n_negatives, strategy)
            
            if (epoch + 1) % eval_interval == 0:
                print(f"  Epoch {epoch+1}/{epochs}, Loss: {loss:.4f}")
        
        print("✅ BPR训练完成")


# ==================== 单元测试 ====================

def test_ppi_sampler():
    """测试PPI采样器"""
    print("\n" + "="*50)
    print("测试1: PPINegativeSampler")
    print("="*50)
    
    n_items = 100
    
    # 构建PPI对
    ppi_pairs = [
        (0, 10, 0.9), (0, 20, 0.8), (0, 30, 0.7),
        (10, 20, 0.85), (10, 40, 0.6),
        (50, 60, 0.9), (50, 70, 0.8)
    ]
    
    # 家族信息
    item_family = {i: f"F{i//20}" for i in range(n_items)}
    
    sampler = PPINegativeSampler(n_items, ppi_pairs, item_family)
    
    # 测试均匀采样
    pos_items = {0, 50}
    neg_uniform = sampler.sample_uniform(pos_items, 10)
    print(f"  均匀采样: {len(neg_uniform)}个负例")
    assert len(neg_uniform) == 10, "均匀采样数量错误"
    assert not any(n in pos_items for n in neg_uniform), "均匀采样包含正例"
    
    # 测试PPI-hard采样
    neg_ppi = sampler.sample_ppi_hard(0, pos_items, 10)
    print(f"  PPI-hard采样: {len(neg_ppi)}个负例")
    # 应该包含0的邻居
    neighbors_of_0 = {10, 20, 30}
    assert any(n in neighbors_of_0 for n in neg_ppi), "PPI采样未包含邻居"
    
    # 测试Family-hard采样
    neg_family = sampler.sample_family_hard(0, pos_items, 10)
    print(f"  Family-hard采样: {len(neg_family)}个负例")
    
    # 测试混合采样
    neg_mixed = sampler.sample_mixed(0, pos_items, 10, strategy='ppi')
    print(f"  混合采样(ppi): {len(neg_mixed)}个负例")
    
    print("✅ PPI采样器测试通过")
    return True


def test_bpr_trainer():
    """测试BPR训练器"""
    print("\n" + "="*50)
    print("测试2: BPRTrainer")
    print("="*50)
    
    # 简单模型
    class SimpleModel(nn.Module):
        def __init__(self, n_users, n_items, dim=16):
            super().__init__()
            self.user_emb = nn.Embedding(n_users, dim)
            self.item_emb = nn.Embedding(n_items, dim)
            nn.init.xavier_uniform_(self.user_emb.weight)
            nn.init.xavier_uniform_(self.item_emb.weight)
        
        def forward(self, user_id, item_id):
            if not isinstance(user_id, torch.Tensor):
                user_id = torch.tensor([user_id])
                item_id = torch.tensor([item_id])
            u = self.user_emb(user_id)
            i = self.item_emb(item_id)
            return (u * i).sum(dim=1)
    
    n_users = 50
    n_items = 100
    
    model = SimpleModel(n_users, n_items)
    sampler = PPINegativeSampler(n_items)
    trainer = BPRTrainer(model, sampler, lr=0.01)
    
    # 构建交互数据
    interactions = {
        user_id: set(np.random.choice(n_items, size=np.random.randint(3, 10), replace=False))
        for user_id in range(n_users)
    }
    
    # 训练
    trainer.fit(interactions, epochs=30, n_negatives=2, strategy='uniform', eval_interval=10)
    
    print("✅ BPR训练器测试通过")
    return True


def test_sampling_strategies():
    """测试不同采样策略的效果对比"""
    print("\n" + "="*50)
    print("测试3: 采样策略对比")
    print("="*50)
    
    n_items = 200
    ppi_pairs = [(i, (i+10) % n_items, 0.8) for i in range(0, n_items, 5)]
    
    sampler = PPINegativeSampler(n_items, ppi_pairs)
    
    pos_items = {0, 50, 100}
    
    strategies = ['uniform', 'ppi', 'popularity']
    
    for strategy in strategies:
        samples = sampler.sample_mixed(0, pos_items, 20, strategy)
        
        # 统计PPI邻居占比
        if strategy == 'ppi':
            neighbors_0 = {n for n, _ in sampler.ppi_neighbors.get(0, [])}
            overlap = len(set(samples) & neighbors_0)
            print(f"  {strategy:12s}: {overlap}/20 是蛋白0的PPI邻居")
        else:
            print(f"  {strategy:12s}: 采样20个")
    
    print("✅ 采样策略对比测试通过")
    return True


if __name__ == '__main__':
    print("="*60)
    print("负采样改进BPR - 单元测试")
    print("="*60)
    
    np.random.seed(42)
    torch.manual_seed(42)
    
    try:
        test_ppi_sampler()
        test_bpr_trainer()
        test_sampling_strategies()
        
        print("\n" + "="*60)
        print("✅ 所有单元测试通过!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise