"""
ProteinHub 完整推荐系统 v2

基于真实PPI数据 (whole.tsv) 的推荐流程:
1. 用户行为模拟 (基于细胞器偏好)
2. 双塔模型训练 (用户塔 + PPI增强蛋白塔)
3. 推荐有效性评估 (Recall@K, NDCG@K, MRR)
"""

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict, Optional
from collections import defaultdict
import sys
sys.path.append('/root/.openclaw/workspace/projects/proteinhub/recommendation')

from dual_tower_ppi_fusion import DualTowerWithPPI, PPILightGCNEncoder
from ppi_gnn_recommender import PPIGraphBuilder


class UserBehaviorSimulator:
    """
    用户行为模拟器
    
    模拟真实用户的蛋白偏好:
    - 基于细胞器偏好 (ER, mitochondria, lysosome, peroxisome, Golgi)
    - 基于PPI网络邻近性 (互作蛋白更可能同时被关注)
    - 加入噪声模拟真实行为
    """
    
    def __init__(self, ppi_graph: PPIGraphBuilder, protein_metadata: Dict,
                 random_seed: int = 42):
        self.ppi_graph = ppi_graph
        self.protein_metadata = protein_metadata
        self.rng = np.random.RandomState(random_seed)
        
        # 细胞器偏好配置
        self.organelles = ['ER', 'mitochondria', 'lysosome', 'peroxisome', 'Golgi']
        
    def generate_users(self, n_users: int = 100) -> Dict[int, Dict]:
        """
        生成用户画像
        
        Returns:
            {user_id: {'preferred_organelles': [...], 'interaction_rate': float}}
        """
        users = {}
        
        for user_id in range(n_users):
            # 随机选择1-2个偏好的细胞器
            n_prefs = self.rng.randint(1, 3)
            prefs = self.rng.choice(self.organelles, size=n_prefs, replace=False).tolist()
            
            # 交互率 (有些用户活跃，有些不活跃)
            interaction_rate = self.rng.uniform(0.3, 1.0)
            
            users[user_id] = {
                'preferred_organelles': prefs,
                'interaction_rate': interaction_rate,
                'user_id': user_id
            }
        
        return users
    
    def generate_interactions(self, users: Dict, n_interactions_per_user: int = 20) -> pd.DataFrame:
        """
        生成用户-蛋白交互数据
        
        逻辑:
        1. 用户偏好某细胞器 → 更高概率交互该细胞器的蛋白
        2. 互作蛋白之间存在相关性 (如果喜欢A，也更可能喜欢A的互作蛋白)
        3. 加入随机探索行为
        """
        interactions = []
        
        all_proteins = list(self.ppi_graph.protein2id.keys())
        
        for user_id, user_profile in users.items():
            prefs = user_profile['preferred_organelles']
            rate = user_profile['interaction_rate']
            
            # 为每个用户生成交互
            n_interactions = int(n_interactions_per_user * rate)
            
            # 已交互的蛋白集合 (避免重复)
            interacted = set()
            
            for _ in range(n_interactions):
                # 80%基于偏好，20%随机探索
                if self.rng.random() < 0.8:
                    protein = self._sample_by_preference(prefs, interacted)
                else:
                    protein = self._sample_exploration(interacted, all_proteins)
                
                if protein is None:
                    continue
                
                interacted.add(protein)
                
                # 生成评分 (偏好蛋白更高分)
                base_score = 4.0 if self._is_preferred(protein, prefs) else 3.0
                noise = self.rng.normal(0, 0.5)
                rating = np.clip(base_score + noise, 1, 5)
                
                interactions.append({
                    'user_id': user_id,
                    'protein_id': protein,
                    'rating': rating,
                    'timestamp': self.rng.randint(1000000)
                })
        
        return pd.DataFrame(interactions)
    
    def _sample_by_preference(self, prefs: List[str], excluded: set) -> Optional[str]:
        """基于细胞器偏好采样蛋白"""
        candidates = []
        
        for protein in self.ppi_graph.protein2id.keys():
            if protein in excluded:
                continue
            
            meta = self.protein_metadata.get(protein, {})
            organelle = meta.get('organelle', 'unknown')
            
            if organelle in prefs:
                candidates.append(protein)
        
        if not candidates:
            return None
        
        return self.rng.choice(candidates)
    
    def _sample_exploration(self, excluded: set, all_proteins: List[str]) -> Optional[str]:
        """随机探索 (考虑PPI邻近性)"""
        # 从已交互蛋白的邻居中采样
        if excluded:
            seed_protein = self.rng.choice(list(excluded))
            neighbors = self.ppi_graph.get_neighbors(
                self.ppi_graph.protein2id[seed_protein], top_k=5
            )
            if neighbors:
                neighbor_ids = [n[0] for n in neighbors]
                neighbor_proteins = [
                    self.ppi_graph.id2protein[n] 
                    for n in neighbor_ids 
                    if self.ppi_graph.id2protein[n] not in excluded
                ]
                if neighbor_proteins:
                    return self.rng.choice(neighbor_proteins)
        
        # 否则完全随机
        valid = [p for p in all_proteins if p not in excluded]
        return self.rng.choice(valid) if valid else None
    
    def _is_preferred(self, protein: str, prefs: List[str]) -> bool:
        """检查蛋白是否在用户偏好中"""
        meta = self.protein_metadata.get(protein, {})
        return meta.get('organelle') in prefs


class ProteinHubEvaluator:
    """
    推荐系统评估器
    
    指标:
    - Recall@K: 召回率
    - Precision@K: 精确率
    - NDCG@K: 归一化折损累计增益
    - MRR: 平均倒数排名
    - HitRate@K: 命中率
    """
    
    @staticmethod
    def evaluate(recommender, test_df: pd.DataFrame, top_k: int = 10) -> Dict[str, float]:
        """
        评估推荐效果
        
        Args:
            recommender: 训练好的推荐模型
            test_df: 测试集 [user_id, protein_id, rating]
            top_k: 评估Top-K
        """
        print(f"\n📊 评估推荐效果 (top_k={top_k})...")
        
        metrics = {
            'recalls': [],
            'precisions': [],
            'ndcgs': [],
            'rrs': [],  # Reciprocal Rank
            'hits': []
        }
        
        for user_id in test_df['user_id'].unique():
            user_data = test_df[test_df['user_id'] == user_id]
            
            #  ground truth: 评分≥4的认为是正样本
            ground_truth = set(
                user_data[user_data['rating'] >= 4]['protein_id'].values
            )
            
            if len(ground_truth) == 0:
                continue
            
            # 生成推荐
            try:
                recommendations = recommender.recommend(int(user_id), top_k=top_k)
                recommended_items = [r[0] for r in recommendations]
            except Exception as e:
                continue
            
            # 计算指标
            hits = len(ground_truth & set(recommended_items))
            
            # Recall@K
            recall = hits / len(ground_truth)
            metrics['recalls'].append(recall)
            
            # Precision@K
            precision = hits / top_k
            metrics['precisions'].append(precision)
            
            # NDCG@K
            dcg = 0
            for i, item in enumerate(recommended_items):
                if item in ground_truth:
                    dcg += 1 / np.log2(i + 2)  # i从0开始
            
            ideal_hits = min(len(ground_truth), top_k)
            idcg = sum(1 / np.log2(i + 2) for i in range(ideal_hits))
            ndcg = dcg / idcg if idcg > 0 else 0
            metrics['ndcgs'].append(ndcg)
            
            # MRR
            rr = 0
            for i, item in enumerate(recommended_items):
                if item in ground_truth:
                    rr = 1 / (i + 1)
                    break
            metrics['rrs'].append(rr)
            
            # HitRate
            metrics['hits'].append(1 if hits > 0 else 0)
        
        # 汇总
        results = {
            f'Recall@{top_k}': np.mean(metrics['recalls']),
            f'Precision@{top_k}': np.mean(metrics['precisions']),
            f'NDCG@{top_k}': np.mean(metrics['ndcgs']),
            'MRR': np.mean(metrics['rrs']),
            f'HitRate@{top_k}': np.mean(metrics['hits'])
        }
        
        return results


class CompleteProteinRecommender:
    """
    完整推荐系统
    
    流程:
    1. 加载PPI数据
    2. 模拟用户行为
    3. 训练双塔模型
    4. 评估推荐效果
    """
    
    def __init__(self, embedding_dim: int = 64, device: str = 'cpu'):
        self.embedding_dim = embedding_dim
        self.device = device
        
        self.ppi_graph = None
        self.protein_metadata = None
        self.model = None
        self.simulator = None
        
    def load_data(self, tsv_path: str, threshold: float = 0.6):
        """加载PPI数据"""
        print("📚 加载PPI数据...")
        
        df = pd.read_csv(tsv_path, sep='\t')
        df_filtered = df[(df['probability'] >= threshold) & (df['probability'].notna())].copy()
        
        # 构建PPI对
        ppi_pairs = []
        for _, row in df_filtered.iterrows():
            p1 = row['LD_protein_symbol'] if pd.notna(row['LD_protein_symbol']) else row['LD_protein']
            p2 = row['organelle_protein_symbol'] if pd.notna(row['organelle_protein_symbol']) else row['organelle_protein']
            score = row['probability']
            ppi_pairs.append((p1, p2, score))
        
        # 构建元数据
        self.protein_metadata = {}
        for p1, p2, _ in ppi_pairs:
            for p in [p1, p2]:
                if p not in self.protein_metadata:
                    rows = df_filtered[
                        (df_filtered['LD_protein_symbol'] == p) | 
                        (df_filtered['organelle_protein_symbol'] == p)
                    ]
                    organelle = rows.iloc[0]['organelle'] if len(rows) > 0 else 'unknown'
                    self.protein_metadata[p] = {
                        'organelle': organelle if pd.notna(organelle) else 'unknown',
                        'degree': 0
                    }
                self.protein_metadata[p]['degree'] += 1
        
        # 构建图
        self.ppi_graph = PPIGraphBuilder()
        self.ppi_graph.build_from_ppi_data(ppi_pairs, self.protein_metadata)
        
        print(f"  蛋白数: {len(self.ppi_graph.protein2id)}")
        print(f"  PPI边数: {len(ppi_pairs)}")
        
        return self
    
    def simulate_and_train(self, n_users: int = 100, 
                          interactions_per_user: int = 20,
                          epochs: int = 50):
        """
        模拟用户行为并训练模型
        """
        # 1. 模拟用户
        print(f"\n👥 模拟 {n_users} 个用户...")
        self.simulator = UserBehaviorSimulator(self.ppi_graph, self.protein_metadata)
        users = self.simulator.generate_users(n_users)
        
        # 打印用户分布
        organelle_dist = defaultdict(int)
        for u in users.values():
            for org in u['preferred_organelles']:
                organelle_dist[org] += 1
        print("  细胞器偏好分布:", dict(organelle_dist))
        
        # 2. 生成交互
        print(f"\n🎯 生成交互数据...")
        interactions_df = self.simulator.generate_interactions(users, interactions_per_user)
        print(f"  总交互数: {len(interactions_df)}")
        
        # 3. 划分训练/测试集
        train_df = interactions_df.sample(frac=0.8, random_state=42)
        test_df = interactions_df.drop(train_df.index)
        print(f"  训练集: {len(train_df)}, 测试集: {len(test_df)}")
        
        # 4. 训练双塔模型
        print(f"\n🚀 训练双塔模型...")
        self._train_dual_tower(train_df, epochs)
        
        return train_df, test_df
    
    def _train_dual_tower(self, train_df: pd.DataFrame, epochs: int):
        """训练双塔模型"""
        # 构建映射
        user2id = {u: i for i, u in enumerate(train_df['user_id'].unique())}
        protein2id = self.ppi_graph.protein2id
        
        num_users = len(user2id)
        num_proteins = len(protein2id)
        
        # 初始化模型
        self.model = DualTowerWithPPI(
            num_users=num_users,
            num_proteins=num_proteins,
            embedding_dim=self.embedding_dim,
            fusion='concat'
        ).to(self.device)
        
        # 准备数据
        edge_index, edge_weight = self.ppi_graph.get_graph_data()
        edge_index = edge_index.to(self.device)
        edge_weight = edge_weight.to(self.device)
        
        user_ids = torch.tensor(
            [user2id[u] for u in train_df['user_id']], dtype=torch.long
        ).to(self.device)
        protein_ids = torch.tensor(
            [protein2id.get(p, 0) for p in train_df['protein_id']], dtype=torch.long
        ).to(self.device)
        ratings = torch.tensor(
            train_df['rating'].values / 5.0, dtype=torch.float
        ).to(self.device)
        
        # 训练
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        
        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            
            scores, _, _ = self.model(user_ids, protein_ids, edge_index, edge_weight)
            loss = F.mse_loss(scores, ratings)
            
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 10 == 0:
                print(f"  Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")
        
        # 保存映射
        self.user2id = user2id
        self.id2user = {v: k for k, v in user2id.items()}
        
        print("  ✅ 训练完成")
    
    def recommend(self, user_id: int, top_k: int = 10) -> List[Tuple[str, float]]:
        """生成推荐"""
        if user_id not in self.user2id:
            return []
        
        self.model.eval()
        
        edge_index, edge_weight = self.ppi_graph.get_graph_data()
        edge_index = edge_index.to(self.device)
        edge_weight = edge_weight.to(self.device)
        
        user_idx = self.user2id[user_id]
        num_proteins = len(self.ppi_graph.protein2id)
        
        with torch.no_grad():
            user_tensor = torch.tensor([user_idx] * num_proteins, dtype=torch.long).to(self.device)
            protein_tensor = torch.arange(num_proteins, dtype=torch.long).to(self.device)
            
            scores, _, _ = self.model(user_tensor, protein_tensor, edge_index, edge_weight)
            top_scores, top_indices = torch.topk(scores, top_k)
        
        id2protein = {v: k for k, v in self.ppi_graph.protein2id.items()}
        results = [(id2protein[idx.item()], score.item()) 
                   for idx, score in zip(top_indices, top_scores)]
        
        return results


# ==================== 完整流程测试 ====================

def run_complete_pipeline():
    """运行完整推荐流程"""
    print("="*70)
    print("ProteinHub 完整推荐系统 v2")
    print("="*70)
    
    # 初始化
    recommender = CompleteProteinRecommender(embedding_dim=64, device='cpu')
    
    # 1. 加载PPI数据
    recommender.load_data(
        '/root/.openclaw/workspace/projects/proteinhub/data/whole.tsv',
        threshold=0.6
    )
    
    # 2. 模拟用户行为并训练
    train_df, test_df = recommender.simulate_and_train(
        n_users=50,
        interactions_per_user=15,
        epochs=30
    )
    
    # 3. 评估推荐效果
    print(f"\n📊 推荐效果评估...")
    
    # 为每个测试用户生成推荐并评估
    evaluator = ProteinHubEvaluator()
    results = evaluator.evaluate(recommender, test_df, top_k=10)
    
    print("\n" + "="*70)
    print("评估结果:")
    print("="*70)
    for metric, value in results.items():
        print(f"  {metric:20s}: {value:.4f}")
    
    # 4. 示例推荐
    print(f"\n🎯 示例推荐 (用户0):")
    recommendations = recommender.recommend(user_id=0, top_k=10)
    for i, (protein, score) in enumerate(recommendations, 1):
        organelle = recommender.protein_metadata.get(protein, {}).get('organelle', 'unknown')
        print(f"  {i:2d}. {protein:15s} ({score:.3f}) [{organelle}]")
    
    print("\n✅ 完整流程完成!")
    
    return recommender, results


if __name__ == '__main__':
    run_complete_pipeline()