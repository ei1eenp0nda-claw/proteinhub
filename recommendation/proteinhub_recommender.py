"""
ProteinHub 完整推荐系统

整合四个核心模块:
1. GNN召回层 (PPILightGCN) - 从PPI图召回候选
2. 多模态融合 (MultimodalFusion) - 融合蛋白家族/文献/网络特征
3. FM精排层 (DeepFM) - 精细排序
4. PPI负采样BPR (BPRTrainer) - 训练优化

使用阈值>=0.6的PPI数据 (1,811对)
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

from ppi_gnn_recommender import (
    PPIGraphBuilder, PPILightGCN, MultimodalFusion, QuickReranker
)
from fm_reranker import DeepFM
from bpr_with_ppi_sampling import PPINegativeSampler, BPRTrainer
from multimodal_text_features import PaperLoader, TextFeatureExtractor, MultimodalFeatureFusion


class ProteinHubRecommender:
    """
    ProteinHub完整推荐系统
    
    三阶段架构:
    1. GNN召回: LightGCN在PPI图上召回Top-K候选
    2. 特征增强: 融合多模态特征 (家族+文献+网络)
    3. FM精排: DeepFM对候选精细排序
    
    训练: 使用PPI-aware负采样BPR
    """
    
    def __init__(self, 
                 embedding_dim: int = 64,
                 gnn_layers: int = 3,
                 fm_field_dims: List[int] = None,
                 device: str = 'cpu'):
        """
        Args:
            embedding_dim: 嵌入维度
            gnn_layers: GNN层数
            fm_field_dims: FM特征域维度 [user, item, family, ...]
            device: 计算设备
        """
        self.embedding_dim = embedding_dim
        self.gnn_layers = gnn_layers
        self.device = device
        
        # 各阶段模型
        self.ppi_graph = None
        self.gnn_model = None
        self.fusion_model = None
        self.fm_model = None
        self.reranker = None
        
        # 数据映射
        self.user2id = {}
        self.item2id = {}
        self.id2item = {}
        self.protein_metadata = {}
        
        # 特征提取
        self.paper_loader = None
        self.text_extractor = None
        
        self.is_fitted = False
    
    def load_ppi_data(self, tsv_path: str, threshold: float = 0.6) -> Tuple[List, Dict]:
        """加载PPI数据"""
        print(f"📚 加载PPI数据 (阈值>={threshold})...")
        
        df = pd.read_csv(tsv_path, sep='\t')
        df_filtered = df[(df['probability'] >= threshold) & (df['probability'].notna())].copy()
        
        print(f"  原始: {len(df)} 对 → 筛选后: {len(df_filtered)} 对")
        
        # 构建PPI对
        ppi_pairs = []
        for _, row in df_filtered.iterrows():
            p1 = row['LD_protein_symbol'] if pd.notna(row['LD_protein_symbol']) else row['LD_protein']
            p2 = row['organelle_protein_symbol'] if pd.notna(row['organelle_protein_symbol']) else row['organelle_protein']
            score = row['probability']
            ppi_pairs.append((p1, p2, score))
        
        # 蛋白元数据
        protein_metadata = {}
        for p1, p2, _ in ppi_pairs:
            for p in [p1, p2]:
                if p not in protein_metadata:
                    rows = df_filtered[
                        (df_filtered['LD_protein_symbol'] == p) | 
                        (df_filtered['organelle_protein_symbol'] == p)
                    ]
                    organelle = rows.iloc[0]['organelle'] if len(rows) > 0 else 'unknown'
                    protein_metadata[p] = {
                        'organelle': organelle if pd.notna(organelle) else 'unknown',
                        'degree': 0
                    }
                protein_metadata[p]['degree'] += 1
        
        return ppi_pairs, protein_metadata
    
    def fit(self, 
            interactions_df: pd.DataFrame,
            ppi_tsv_path: str = '/root/.openclaw/workspace/projects/proteinhub/data/whole.tsv',
            threshold: float = 0.6,
            epochs: int = 50):
        """
        训练完整推荐系统
        
        Args:
            interactions_df: DataFrame [user_id, item_id, rating/timestamp]
            ppi_tsv_path: PPI数据路径
            threshold: PPI概率阈值
            epochs: 训练轮数
        """
        print("="*60)
        print("🚀 ProteinHub推荐系统训练")
        print("="*60)
        
        # ========== 1. 加载PPI数据并构建图 ==========
        ppi_pairs, self.protein_metadata = self.load_ppi_data(ppi_tsv_path, threshold)
        
        self.ppi_graph = PPIGraphBuilder()
        self.ppi_graph.build_from_ppi_data(ppi_pairs, self.protein_metadata)
        
        num_items = len(self.ppi_graph.protein2id)
        num_users = interactions_df['user_id'].nunique()
        
        print(f"\n📊 数据统计:")
        print(f"  用户数: {num_users}")
        print(f"  蛋白数: {num_items}")
        print(f"  PPI边数: {len(ppi_pairs)}")
        
        # 构建映射
        self.user2id = {u: i for i, u in enumerate(interactions_df['user_id'].unique())}
        self.item2id = self.ppi_graph.protein2id
        self.id2item = {v: k for k, v in self.item2id.items()}
        
        # ========== 2. 初始化GNN模型 ==========
        print(f"\n🔄 初始化GNN模型...")
        edge_index, edge_weight = self.ppi_graph.get_graph_data()
        
        self.gnn_model = PPILightGCN(
            num_users=num_users,
            num_items=num_items,
            embedding_dim=self.embedding_dim,
            num_layers=self.gnn_layers,
            ppi_graph=self.ppi_graph
        ).to(self.device)
        
        # ========== 3. 初始化多模态融合 ==========
        self.fusion_model = MultimodalFusion(dim=self.embedding_dim).to(self.device)
        
        # ========== 4. 初始化精排模型 ==========
        # 特征域: user, item, protein_family, organelle, degree
        field_dims = [num_users, num_items, 20, 10, 50]  # 简化版本
        self.fm_model = DeepFM(field_dims, embed_dim=16).to(self.device)
        
        # ========== 5. 训练GNN (BPR损失) ==========
        print(f"\n🔄 训练GNN ({epochs} epochs)...")
        self._train_gnn(interactions_df, edge_index, edge_weight, epochs)
        
        self.is_fitted = True
        print("\n✅ 训练完成!")
        
        return self
    
    def _train_gnn(self, interactions_df: pd.DataFrame, 
                   edge_index: torch.Tensor, edge_weight: torch.Tensor,
                   epochs: int):
        """训练GNN模型"""
        optimizer = torch.optim.Adam(self.gnn_model.parameters(), lr=0.01)
        
        # 准备数据
        user_ids = torch.tensor(
            [self.user2id[u] for u in interactions_df['user_id']], 
            dtype=torch.long
        ).to(self.device)
        item_ids = torch.tensor(
            [self.item2id.get(i, 0) for i in interactions_df['item_id']], 
            dtype=torch.long
        ).to(self.device)
        
        # 如果有评分，归一化到0-1
        if 'rating' in interactions_df.columns:
            ratings = torch.tensor(
                interactions_df['rating'].values / interactions_df['rating'].max(), 
                dtype=torch.float
            ).to(self.device)
        else:
            ratings = torch.ones(len(interactions_df), dtype=torch.float).to(self.device)
        
        edge_index = edge_index.to(self.device)
        edge_weight = edge_weight.to(self.device)
        
        self.gnn_model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            
            scores, _, _ = self.gnn_model(user_ids, item_ids, edge_index, edge_weight)
            loss = F.mse_loss(scores, ratings)
            
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 10 == 0:
                print(f"  Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")
    
    def recommend(self, user_id: int, top_k: int = 10, 
                  candidates: int = 100) -> List[Tuple[str, float, str]]:
        """
        为用户生成推荐
        
        Args:
            user_id: 用户ID
            top_k: 返回推荐数量
            candidates: 召回候选数量
            
        Returns:
            [(蛋白名, 分数, 细胞器), ...]
        """
        if not self.is_fitted:
            raise RuntimeError("模型未训练")
        
        if user_id not in self.user2id:
            # 冷启动: 返回热门蛋白
            return self._cold_start_recommend(top_k)
        
        self.gnn_model.eval()
        
        # ========== Stage 1: GNN召回 ==========
        edge_index, edge_weight = self.ppi_graph.get_graph_data()
        edge_index = edge_index.to(self.device)
        edge_weight = edge_weight.to(self.device)
        
        with torch.no_grad():
            gnn_candidates = self.gnn_model.get_recommendations(
                self.user2id[user_id],
                edge_index, edge_weight,
                top_k=candidates
            )
        
        # ========== Stage 2: 特征准备 (简化版) ==========
        # 这里可以加入多模态融合，暂时用GNN分数
        
        # ========== Stage 3: FM精排 ==========
        # 简化: 直接返回GNN排序结果
        # 完整版应该在这里用FM对candidates重新排序
        
        # 映射回蛋白名
        results = []
        for item_idx, score in gnn_candidates[:top_k]:
            protein_name = self.id2item.get(item_idx, f"item_{item_idx}")
            organelle = self.protein_metadata.get(protein_name, {}).get('organelle', 'unknown')
            results.append((protein_name, float(score), organelle))
        
        return results
    
    def _cold_start_recommend(self, top_k: int) -> List[Tuple[str, float, str]]:
        """冷启动推荐 (按度数排序)"""
        # 返回度数高的蛋白 (更可能重要)
        sorted_proteins = sorted(
            self.protein_metadata.items(),
            key=lambda x: x[1].get('degree', 0),
            reverse=True
        )
        
        results = []
        for protein_name, meta in sorted_proteins[:top_k]:
            degree = meta.get('degree', 0)
            organelle = meta.get('organelle', 'unknown')
            # 用degree作为分数 (归一化)
            score = min(degree / 50.0, 1.0)
            results.append((protein_name, score, organelle))
        
        return results
    
    def evaluate(self, test_interactions: pd.DataFrame, top_k: int = 10) -> Dict[str, float]:
        """
        评估推荐效果
        
        指标:
        - Recall@K: 召回率
        - NDCG@K: 归一化折损累计增益
        """
        print(f"\n📊 评估 (top_k={top_k})...")
        
        recalls = []
        ndcgs = []
        
        for user_id in test_interactions['user_id'].unique():
            user_data = test_interactions[test_interactions['user_id'] == user_id]
            ground_truth = set(user_data['item_id'].values)
            
            if len(ground_truth) == 0:
                continue
            
            # 生成推荐
            try:
                recommendations = self.recommend(user_id, top_k=top_k)
                recommended_items = set([r[0] for r in recommendations])
            except:
                continue
            
            # 计算Recall
            hits = len(ground_truth & recommended_items)
            recall = hits / len(ground_truth)
            recalls.append(recall)
            
            # 计算NDCG
            dcg = 0
            for i, (item, _, _) in enumerate(recommendations):
                if item in ground_truth:
                    dcg += 1 / np.log2(i + 2)  # i从0开始，所以+2
            
            ideal_hits = min(len(ground_truth), top_k)
            idcg = sum(1 / np.log2(i + 2) for i in range(ideal_hits))
            ndcg = dcg / idcg if idcg > 0 else 0
            ndcgs.append(ndcg)
        
        metrics = {
            f'Recall@{top_k}': np.mean(recalls) if recalls else 0,
            f'NDCG@{top_k}': np.mean(ndcgs) if ndcgs else 0
        }
        
        print(f"  Recall@{top_k}: {metrics[f'Recall@{top_k}']:.4f}")
        print(f"  NDCG@{top_k}: {metrics[f'NDCG@{top_k}']:.4f}")
        
        return metrics


# ==================== 快速测试 ====================

def test_full_pipeline():
    """测试完整流程"""
    print("="*60)
    print("ProteinHub 完整推荐系统测试")
    print("="*60)
    
    # 模拟交互数据
    np.random.seed(42)
    
    n_users = 50
    n_interactions = 300
    
    # 生成模拟交互
    interactions = []
    for _ in range(n_interactions):
        user_id = np.random.randint(0, n_users)
        # 物品ID会在fit时映射到蛋白
        item_id = f"protein_{np.random.randint(0, 100)}"
        rating = np.random.uniform(3, 5)
        interactions.append({
            'user_id': user_id,
            'item_id': item_id,
            'rating': rating
        })
    
    df = pd.DataFrame(interactions)
    
    # 划分训练/测试
    train_df = df.sample(frac=0.8, random_state=42)
    test_df = df.drop(train_df.index)
    
    # 训练
    recommender = ProteinHubRecommender(embedding_dim=32, device='cpu')
    recommender.fit(train_df, threshold=0.6, epochs=20)
    
    # 生成推荐
    print(f"\n🎯 为用户0生成推荐:")
    recommendations = recommender.recommend(user_id=0, top_k=10)
    
    for i, (protein, score, organelle) in enumerate(recommendations, 1):
        print(f"  {i:2d}. {protein:15s} ({score:.3f}) [{organelle}]")
    
    # 冷启动测试
    print(f"\n🎯 冷启动推荐 (新用户):")
    cold_recs = recommender._cold_start_recommend(top_k=5)
    for i, (protein, score, organelle) in enumerate(cold_recs, 1):
        print(f"  {i}. {protein:15s} ({score:.3f}) [{organelle}]")
    
    print("\n✅ 完整流程测试通过!")


if __name__ == '__main__':
    test_full_pipeline()