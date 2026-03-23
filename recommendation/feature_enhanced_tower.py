"""
方案B: 显式特征工程 + 细胞器/PPI信息融合

改进点:
1. 细胞器特征作为side information输入
2. PPI预训练初始化蛋白embedding
3. 特征融合层 (concat + MLP)
4. 对比: 原始LightGCN vs 特征增强版
"""

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple
import sys
sys.path.append('/root/.openclaw/workspace/projects/proteinhub/recommendation')

from ppi_gnn_recommender import PPIGraphBuilder
from complete_recommender_v2 import UserBehaviorSimulator


class ProteinFeatureExtractor:
    """
    蛋白特征提取器
    
    提取以下特征:
    1. 细胞器 (one-hot)
    2. PPI degree (网络中心性)
    3. PPI PageRank (重要性)
    4. 是否脂滴蛋白 (binary)
    """
    
    def __init__(self, protein_metadata: Dict, ppi_graph: PPIGraphBuilder):
        self.metadata = protein_metadata
        self.ppi_graph = ppi_graph
        
        # 细胞器列表
        self.organelles = ['ER', 'mitochondria', 'lysosome', 'peroxisome', 'Golgi', 'unknown']
        self.org2idx = {org: i for i, org in enumerate(self.organelles)}
        
        # 计算PageRank (简化版)
        self.pagerank = self._compute_pagerank()
    
    def _compute_pagerank(self, damping: float = 0.85, iterations: int = 20) -> Dict[str, float]:
        """计算简化PageRank"""
        n = len(self.ppi_graph.protein2id)
        if n == 0:
            return {}
        
        # 初始化
        pr = {p: 1.0 / n for p in self.ppi_graph.protein2id.keys()}
        
        # 构建邻接表
        adj = {p: [] for p in self.ppi_graph.protein2id.keys()}
        for src, dst, weight in self.ppi_graph.edges:
            src_name = self.ppi_graph.id2protein[src]
            dst_name = self.ppi_graph.id2protein[dst]
            adj[src_name].append((dst_name, weight))
        
        # 迭代
        for _ in range(iterations):
            new_pr = {}
            for protein in pr.keys():
                rank = (1 - damping) / n
                
                # 从邻居接收
                for neighbor, weight in adj.get(protein, []):
                    if neighbor in pr:
                        out_degree = len(adj.get(neighbor, []))
                        if out_degree > 0:
                            rank += damping * pr[neighbor] * weight / out_degree
                
                new_pr[protein] = rank
            
            pr = new_pr
        
        # 归一化
        max_pr = max(pr.values()) if pr else 1
        return {p: r / max_pr for p, r in pr.items()}
    
    def get_features(self, protein_id: str) -> torch.Tensor:
        """
        获取蛋白特征向量
        
        Returns:
            features: [6 + 3] = [细胞器one-hot(6), degree, pagerank, is_ld]
        """
        meta = self.metadata.get(protein_id, {})
        
        # 1. 细胞器one-hot
        org = meta.get('organelle', 'unknown')
        org_onehot = [0.0] * len(self.organelles)
        if org in self.org2idx:
            org_onehot[self.org2idx[org]] = 1.0
        
        # 2. PPI degree (log归一化)
        degree = meta.get('degree', 0)
        degree_feat = np.log1p(degree) / 5.0  # 归一化到0-1
        
        # 3. PageRank
        pr = self.pagerank.get(protein_id, 0)
        
        # 4. 是否脂滴蛋白 (从文件名推断，这里简化)
        is_ld = 1.0 if 'LD' in str(protein_id).upper() else 0.0
        
        features = org_onehot + [degree_feat, pr, is_ld]
        return torch.tensor(features, dtype=torch.float)


class FeatureEnhancedDualTower(nn.Module):
    """
    特征增强双塔模型
    
    改进:
    - 蛋白塔: ID embedding + 手工特征 → MLP融合
    - 可选PPI预训练初始化
    """
    
    def __init__(self, num_users: int, num_proteins: int,
                 embedding_dim: int = 64, feature_dim: int = 9,
                 use_features: bool = True,
                 use_ppi_init: bool = False,
                 ppi_graph: PPIGraphBuilder = None):
        super().__init__()
        
        self.num_users = num_users
        self.num_proteins = num_proteins
        self.embedding_dim = embedding_dim
        self.use_features = use_features
        
        # 用户塔
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        nn.init.xavier_uniform_(self.user_embedding.weight)
        
        # 蛋白塔 - 基础ID
        self.protein_id_emb = nn.Embedding(num_proteins, embedding_dim)
        
        # PPI预训练初始化
        if use_ppi_init and ppi_graph is not None:
            self._ppi_init(ppi_graph)
        else:
            nn.init.xavier_uniform_(self.protein_id_emb.weight)
        
        # 特征融合
        if use_features:
            # 特征投影
            self.feature_proj = nn.Sequential(
                nn.Linear(feature_dim, embedding_dim),
                nn.ReLU(),
                nn.Linear(embedding_dim, embedding_dim)
            )
            
            # 融合层: ID + Feature → final
            self.fusion = nn.Sequential(
                nn.Linear(embedding_dim * 2, embedding_dim),
                nn.LayerNorm(embedding_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            )
    
    def _ppi_init(self, ppi_graph: PPIGraphBuilder):
        """用PPI图做预训练初始化 (Node2Vec简化版)"""
        print("  🔧 使用PPI预训练初始化...")
        
        # 简化的PPI感知初始化
        # 基于PPI degree调整embedding scale
        init_emb = torch.randn(self.num_proteins, self.embedding_dim)
        init_emb = F.normalize(init_emb, p=2, dim=1)
        
        # 高degree蛋白获得更大scale
        for protein, idx in ppi_graph.protein2id.items():
            # 从边中统计degree
            degree = sum(1 for s, d, _ in ppi_graph.edges if s == idx or d == idx)
            scale = 1.0 + np.log1p(degree) * 0.1
            init_emb[idx] *= scale
        
        self.protein_id_emb.weight.data = init_emb
    
    def forward(self, user_ids: torch.Tensor, protein_ids: torch.Tensor,
                protein_features: torch.Tensor = None) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Args:
            user_ids: [batch]
            protein_ids: [batch]
            protein_features: [batch, feature_dim] (optional)
        
        Returns:
            scores, user_vec, protein_vec
        """
        # 用户表示
        user_vec = self.user_embedding(user_ids)
        
        # 蛋白基础表示
        protein_id_vec = self.protein_id_emb(protein_ids)
        
        if self.use_features and protein_features is not None:
            # 特征投影
            feature_vec = self.feature_proj(protein_features)
            
            # 融合
            combined = torch.cat([protein_id_vec, feature_vec], dim=-1)
            protein_vec = self.fusion(combined)
        else:
            protein_vec = protein_id_vec
        
        # 内积分数
        scores = (user_vec * protein_vec).sum(dim=-1)
        
        return scores, user_vec, protein_vec


class FeatureEnhancedRecommender:
    """
    特征增强推荐器
    
    对比实验:
    - Baseline: 纯ID embedding
    - +Features: ID + 细胞器/degree/PageRank
    - +PPI Init: PPI预训练初始化 + Features
    """
    
    def __init__(self, device: str = 'cpu'):
        self.device = device
        self.model = None
        self.feature_extractor = None
        self.ppi_graph = None
        self.protein_metadata = None
        
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
        
        # 初始化特征提取器
        self.feature_extractor = ProteinFeatureExtractor(
            self.protein_metadata, self.ppi_graph
        )
        
        print(f"  蛋白数: {len(self.ppi_graph.protein2id)}")
        return self
    
    def train(self, train_df: pd.DataFrame, 
              use_features: bool = True,
              use_ppi_init: bool = False,
              epochs: int = 30, lr: float = 0.01) -> Dict:
        """训练模型"""
        
        # 构建映射
        self.user2id = {u: i for i, u in enumerate(train_df['user_id'].unique())}
        self.protein2id = self.ppi_graph.protein2id
        self.id2protein = {v: k for k, v in self.protein2id.items()}
        
        num_users = len(self.user2id)
        num_proteins = len(self.protein2id)
        
        # 初始化模型
        self.model = FeatureEnhancedDualTower(
            num_users=num_users,
            num_proteins=num_proteins,
            embedding_dim=64,
            feature_dim=9,
            use_features=use_features,
            use_ppi_init=use_ppi_init,
            ppi_graph=self.ppi_graph if use_ppi_init else None
        ).to(self.device)
        
        # 准备数据
        user_ids = torch.tensor(
            [self.user2id[u] for u in train_df['user_id']], dtype=torch.long
        ).to(self.device)
        protein_ids = torch.tensor(
            [self.protein2id.get(p, 0) for p in train_df['protein_id']], dtype=torch.long
        ).to(self.device)
        ratings = torch.tensor(
            train_df['rating'].values / 5.0, dtype=torch.float
        ).to(self.device)
        
        # 准备特征
        if use_features:
            protein_features = torch.stack([
                self.feature_extractor.get_features(p)
                for p in train_df['protein_id']
            ]).to(self.device)
        else:
            protein_features = None
        
        # 训练
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        
        self.model.train()
        losses = []
        for epoch in range(epochs):
            optimizer.zero_grad()
            
            scores, _, _ = self.model(user_ids, protein_ids, protein_features)
            loss = F.mse_loss(scores, ratings)
            
            loss.backward()
            optimizer.step()
            
            losses.append(loss.item())
            if (epoch + 1) % 10 == 0:
                print(f"    Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")
        
        return {'final_loss': losses[-1], 'losses': losses}
    
    def recommend(self, user_id: int, top_k: int = 10) -> List[Tuple[str, float]]:
        """生成推荐"""
        if user_id not in self.user2id:
            return []
        
        self.model.eval()
        
        user_idx = self.user2id[user_id]
        num_proteins = len(self.protein2id)
        
        # 准备所有蛋白的特征
        if self.model.use_features:
            protein_features = torch.stack([
                self.feature_extractor.get_features(self.id2protein[i])
                for i in range(num_proteins)
            ]).to(self.device)
        else:
            protein_features = None
        
        with torch.no_grad():
            user_tensor = torch.tensor([user_idx] * num_proteins, dtype=torch.long).to(self.device)
            protein_tensor = torch.arange(num_proteins, dtype=torch.long).to(self.device)
            
            scores, _, _ = self.model(user_tensor, protein_tensor, protein_features)
            top_scores, top_indices = torch.topk(scores, top_k)
        
        results = [(self.id2protein[idx.item()], score.item()) 
                   for idx, score in zip(top_indices, top_scores)]
        
        return results


def evaluate_model(recommender: FeatureEnhancedRecommender, 
                   test_df: pd.DataFrame, top_k: int = 10) -> Dict[str, float]:
    """评估模型"""
    recalls, precisions, ndcgs, rrs, hits = [], [], [], [], []
    
    for user_id in test_df['user_id'].unique():
        user_data = test_df[test_df['user_id'] == user_id]
        ground_truth = set(user_data[user_data['rating'] >= 4]['protein_id'].values)
        
        if len(ground_truth) == 0:
            continue
        
        try:
            recommendations = recommender.recommend(int(user_id), top_k=top_k)
            recommended = [r[0] for r in recommendations]
        except:
            continue
        
        # 计算指标
        hits_num = len(ground_truth & set(recommended))
        
        recall = hits_num / len(ground_truth)
        precision = hits_num / top_k
        
        # NDCG
        dcg = sum(1 / np.log2(i + 2) for i, item in enumerate(recommended) if item in ground_truth)
        ideal_hits = min(len(ground_truth), top_k)
        idcg = sum(1 / np.log2(i + 2) for i in range(ideal_hits))
        ndcg = dcg / idcg if idcg > 0 else 0
        
        # MRR
        rr = next((1 / (i + 1) for i, item in enumerate(recommended) if item in ground_truth), 0)
        
        recalls.append(recall)
        precisions.append(precision)
        ndcgs.append(ndcg)
        rrs.append(rr)
        hits.append(1 if hits_num > 0 else 0)
    
    return {
        f'Recall@{top_k}': np.mean(recalls),
        f'Precision@{top_k}': np.mean(precisions),
        f'NDCG@{top_k}': np.mean(ndcgs),
        'MRR': np.mean(rrs),
        f'HitRate@{top_k}': np.mean(hits)
    }


def run_feature_comparison():
    """运行特征对比实验"""
    print("="*70)
    print("方案B: 特征增强双塔模型对比")
    print("="*70)
    
    # 加载数据
    recommender = FeatureEnhancedRecommender()
    recommender.load_data('/root/.openclaw/workspace/projects/proteinhub/data/whole.tsv', threshold=0.6)
    
    # 模拟用户
    simulator = UserBehaviorSimulator(recommender.ppi_graph, recommender.protein_metadata)
    users = simulator.generate_users(n_users=50)
    interactions_df = simulator.generate_interactions(users, n_interactions_per_user=15)
    
    train_df = interactions_df.sample(frac=0.8, random_state=42)
    test_df = interactions_df.drop(train_df.index)
    
    print(f"\n  训练集: {len(train_df)}, 测试集: {len(test_df)}")
    
    # 对比实验
    results = {}
    
    # 1. Baseline: 纯ID
    print("\n🔬 Baseline: 纯ID Embedding")
    r1 = FeatureEnhancedRecommender()
    r1.ppi_graph = recommender.ppi_graph
    r1.protein_metadata = recommender.protein_metadata
    r1.feature_extractor = recommender.feature_extractor
    r1.train(train_df, use_features=False, use_ppi_init=False, epochs=30)
    results['纯ID'] = evaluate_model(r1, test_df)
    
    # 2. +细胞器特征
    print("\n🔬 +细胞器/degree/PageRank特征")
    r2 = FeatureEnhancedRecommender()
    r2.ppi_graph = recommender.ppi_graph
    r2.protein_metadata = recommender.protein_metadata
    r2.feature_extractor = recommender.feature_extractor
    r2.train(train_df, use_features=True, use_ppi_init=False, epochs=30)
    results['+Features'] = evaluate_model(r2, test_df)
    
    # 3. +PPI预训练 + 特征
    print("\n🔬 +PPI预训练 + 特征")
    r3 = FeatureEnhancedRecommender()
    r3.ppi_graph = recommender.ppi_graph
    r3.protein_metadata = recommender.protein_metadata
    r3.feature_extractor = recommender.feature_extractor
    r3.train(train_df, use_features=True, use_ppi_init=True, epochs=30)
    results['+PPI_Init+Features'] = evaluate_model(r3, test_df)
    
    # 打印结果
    print("\n" + "="*70)
    print("对比结果")
    print("="*70)
    
    metrics = ['Recall@10', 'Precision@10', 'NDCG@10', 'MRR', 'HitRate@10']
    
    header = f"{'Method':<25}"
    for m in metrics:
        header += f"{m:<12}"
    print(header)
    print("-" * 70)
    
    for method, scores in results.items():
        row = f"{method:<25}"
        for m in metrics:
            val = scores.get(m, 0)
            row += f"{val:<12.4f}"
        print(row)
    
    # 相对提升
    print("\n" + "="*70)
    print("相对提升 (vs 纯ID)")
    print("="*70)
    
    baseline_scores = results['纯ID']
    for method in ['+Features', '+PPI_Init+Features']:
        print(f"\n{method}:")
        for m in metrics:
            base = baseline_scores[m]
            new = results[method][m]
            if base > 0:
                lift = (new - base) / base * 100
                print(f"  {m}: {lift:+.1f}%")
    
    print("\n✅ 实验完成!")
    return results


if __name__ == '__main__':
    run_feature_comparison()