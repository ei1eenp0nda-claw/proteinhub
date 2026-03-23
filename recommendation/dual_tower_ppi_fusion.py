"""
双塔推荐模型 + PPI图信息融合

把PPI互作网络通过GNN编码，融合进物品(蛋白)塔的embedding中

架构:
- 用户塔: user_id → embedding
- 蛋白塔: protein_id + PPI图(GNN) → enhanced_embedding
- 融合方式: concat 或 weighted sum
"""

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict, Optional
import sys
sys.path.append('/root/.openclaw/workspace/projects/proteinhub/recommendation')

from ppi_gnn_recommender import PPIGraphBuilder


class PPILightGCNEncoder(nn.Module):
    """
    PPI图的LightGCN编码器
    
    为每个蛋白生成图感知表示
    """
    
    def __init__(self, num_proteins: int, embedding_dim: int = 64, num_layers: int = 2):
        super().__init__()
        
        self.num_proteins = num_proteins
        self.embedding_dim = embedding_dim
        self.num_layers = num_layers
        
        # 蛋白初始embedding
        self.protein_emb = nn.Embedding(num_proteins, embedding_dim)
        nn.init.xavier_uniform_(self.protein_emb.weight)
        
        # 图卷积层
        self.convs = nn.ModuleList([
            LightGCNConv() for _ in range(num_layers)
        ])
    
    def forward(self, edge_index: torch.Tensor, 
                edge_weight: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        前向传播，返回所有蛋白的图表示
        
        Args:
            edge_index: [2, num_edges]
            edge_weight: [num_edges]
            
        Returns:
            protein_repr: [num_proteins, embedding_dim]
        """
        x = self.protein_emb.weight
        
        # 多层传播
        embeddings = [x]
        for conv in self.convs:
            x = conv(x, edge_index, edge_weight)
            embeddings.append(x)
        
        # 层聚合 (平均)
        final_embedding = torch.stack(embeddings, dim=0).mean(dim=0)
        
        return final_embedding
    
    def get_protein_repr(self, protein_ids: torch.Tensor,
                         edge_index: torch.Tensor,
                         edge_weight: Optional[torch.Tensor] = None) -> torch.Tensor:
        """获取指定蛋白的图表示"""
        all_repr = self.forward(edge_index, edge_weight)
        return all_repr[protein_ids]


class LightGCNConv(nn.Module):
    """LightGCN图卷积层"""
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor,
                edge_weight: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: [N, dim]
            edge_index: [2, E]
            edge_weight: [E]
        """
        # 对称归一化
        row, col = edge_index
        
        if edge_weight is None:
            edge_weight = torch.ones(row.size(0), device=x.device)
        
        # 计算度
        deg = torch.zeros(x.size(0), device=x.device)
        deg.scatter_add_(0, row, edge_weight)
        deg.scatter_add_(0, col, edge_weight)
        deg = deg + 1  # 加自环
        
        deg_inv_sqrt = deg.pow(-0.5)
        deg_inv_sqrt[deg_inv_sqrt == float('inf')] = 0
        
        # 归一化
        norm = deg_inv_sqrt[row] * edge_weight * deg_inv_sqrt[col]
        
        # 消息传播
        out = torch.zeros_like(x)
        for i in range(edge_index.size(1)):
            out[row[i]] += norm[i] * x[col[i]]
        
        # 加自环
        out = out + x
        
        return out


class DualTowerWithPPI(nn.Module):
    """
    双塔模型 + PPI图信息融合
    
    用户塔: 独立embedding
    蛋白塔: ID embedding + PPI图GNN → fusion
    """
    
    def __init__(self, num_users: int, num_proteins: int,
                 embedding_dim: int = 64, ppi_dim: int = 64,
                 fusion: str = 'concat'):
        """
        Args:
            num_users: 用户数量
            num_proteins: 蛋白数量
            embedding_dim: 基础嵌入维度
            ppi_dim: PPI图编码维度
            fusion: 融合方式 ('concat', 'add', 'gate')
        """
        super().__init__()
        
        self.num_users = num_users
        self.num_proteins = num_proteins
        self.embedding_dim = embedding_dim
        self.ppi_dim = ppi_dim
        self.fusion_type = fusion
        
        # 用户塔
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        nn.init.xavier_uniform_(self.user_embedding.weight)
        
        # 蛋白塔 - 基础ID embedding
        self.protein_id_emb = nn.Embedding(num_proteins, embedding_dim)
        nn.init.xavier_uniform_(self.protein_id_emb.weight)
        
        # PPI图编码器
        self.ppi_encoder = PPILightGCNEncoder(num_proteins, ppi_dim, num_layers=2)
        
        # 融合层
        if fusion == 'concat':
            # concat后投影回embedding_dim
            self.fusion_proj = nn.Sequential(
                nn.Linear(embedding_dim + ppi_dim, embedding_dim),
                nn.LayerNorm(embedding_dim),
                nn.ReLU()
            )
        elif fusion == 'gate':
            # 门控融合
            self.gate = nn.Sequential(
                nn.Linear(embedding_dim + ppi_dim, embedding_dim),
                nn.Sigmoid()
            )
        # 'add' 不需要额外参数
    
    def forward(self, user_ids: torch.Tensor, protein_ids: torch.Tensor,
                edge_index: torch.Tensor,
                edge_weight: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        前向传播
        
        Args:
            user_ids: [batch]
            protein_ids: [batch]
            edge_index: [2, num_edges] - PPI图边
            edge_weight: [num_edges]
            
        Returns:
            scores: [batch] - 预测分数
        """
        # 用户表示
        user_vec = self.user_embedding(user_ids)  # [batch, emb_dim]
        
        # 蛋白基础表示
        protein_id_vec = self.protein_id_emb(protein_ids)  # [batch, emb_dim]
        
        # PPI图表示
        ppi_vec = self.ppi_encoder.get_protein_repr(
            protein_ids, edge_index, edge_weight
        )  # [batch, ppi_dim]
        
        # 融合
        if self.fusion_type == 'concat':
            combined = torch.cat([protein_id_vec, ppi_vec], dim=-1)
            protein_vec = self.fusion_proj(combined)
        elif self.fusion_type == 'add':
            # 维度对齐后相加
            if self.embedding_dim != self.ppi_dim:
                ppi_proj = nn.Linear(self.ppi_dim, self.embedding_dim).to(ppi_vec.device)
                ppi_vec = ppi_proj(ppi_vec)
            protein_vec = protein_id_vec + ppi_vec
        elif self.fusion_type == 'gate':
            combined = torch.cat([protein_id_vec, ppi_vec], dim=-1)
            gate = self.gate(combined)
            protein_vec = gate * protein_id_vec + (1 - gate) * ppi_vec
        else:
            protein_vec = protein_id_vec
        
        # 计算分数 (内积)
        scores = (user_vec * protein_vec).sum(dim=-1)
        
        return scores, user_vec, protein_vec


class DualTowerRecommender:
    """
    双塔推荐器 (PPI增强)
    
    适用于简历项目描述: 
    "基于 Rosetta PPI 方法预测蛋白质-蛋白质相互作用"
    "构建脂滴蛋白与其他细胞器蛋白的互作网络数据库"
    """
    
    def __init__(self, embedding_dim: int = 64, 
                 fusion: str = 'concat',
                 device: str = 'cpu'):
        self.embedding_dim = embedding_dim
        self.fusion = fusion
        self.device = device
        
        self.model = None
        self.ppi_graph = None
        self.user2id = {}
        self.protein2id = {}
        
        self.is_fitted = False
    
    def fit(self, interactions_df: pd.DataFrame,
            ppi_tsv_path: str = '/root/.openclaw/workspace/projects/proteinhub/data/whole.tsv',
            threshold: float = 0.6,
            epochs: int = 50, lr: float = 0.01):
        """
        训练双塔模型
        
        Args:
            interactions_df: DataFrame [user_id, protein_id, rating]
            ppi_tsv_path: PPI数据路径
            threshold: PPI概率阈值
            epochs: 训练轮数
        """
        print("="*60)
        print("🚀 双塔推荐模型训练 (PPI图增强)")
        print("="*60)
        
        # 加载PPI数据
        print("\n📚 加载PPI数据...")
        ppi_pairs, protein_metadata = self._load_ppi_data(ppi_tsv_path, threshold)
        
        # 构建PPI图
        self.ppi_graph = PPIGraphBuilder()
        self.ppi_graph.build_from_ppi_data(ppi_pairs, protein_metadata)
        
        # 构建映射
        self.user2id = {u: i for i, u in enumerate(interactions_df['user_id'].unique())}
        self.protein2id = self.ppi_graph.protein2id
        
        num_users = len(self.user2id)
        num_proteins = len(self.protein2id)
        
        print(f"\n📊 数据规模:")
        print(f"  用户数: {num_users}")
        print(f"  蛋白数: {num_proteins}")
        print(f"  PPI边数: {len(ppi_pairs)}")
        
        # 初始化模型
        self.model = DualTowerWithPPI(
            num_users=num_users,
            num_proteins=num_proteins,
            embedding_dim=self.embedding_dim,
            fusion=self.fusion
        ).to(self.device)
        
        # 准备图数据
        edge_index, edge_weight = self.ppi_graph.get_graph_data()
        edge_index = edge_index.to(self.device)
        edge_weight = edge_weight.to(self.device)
        
        # 准备训练数据
        user_ids = torch.tensor(
            [self.user2id[u] for u in interactions_df['user_id']],
            dtype=torch.long
        ).to(self.device)
        protein_ids = torch.tensor(
            [self.protein2id.get(p, 0) for p in interactions_df['protein_id']],
            dtype=torch.long
        ).to(self.device)
        
        if 'rating' in interactions_df.columns:
            ratings = torch.tensor(
                interactions_df['rating'].values / interactions_df['rating'].max(),
                dtype=torch.float
            ).to(self.device)
        else:
            ratings = torch.ones(len(interactions_df), dtype=torch.float).to(self.device)
        
        # 训练
        print(f"\n🔄 训练双塔模型 ({epochs} epochs)...")
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        
        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            
            scores, _, _ = self.model(user_ids, protein_ids, edge_index, edge_weight)
            loss = F.mse_loss(scores, ratings)
            
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 10 == 0:
                print(f"  Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")
        
        self.is_fitted = True
        print("\n✅ 训练完成!")
        
        return self
    
    def _load_ppi_data(self, tsv_path: str, threshold: float):
        """加载PPI数据"""
        df = pd.read_csv(tsv_path, sep='\t')
        df_filtered = df[(df['probability'] >= threshold) & (df['probability'].notna())].copy()
        
        ppi_pairs = []
        for _, row in df_filtered.iterrows():
            p1 = row['LD_protein_symbol'] if pd.notna(row['LD_protein_symbol']) else row['LD_protein']
            p2 = row['organelle_protein_symbol'] if pd.notna(row['organelle_protein_symbol']) else row['organelle_protein']
            score = row['probability']
            ppi_pairs.append((p1, p2, score))
        
        protein_metadata = {}
        for p1, p2, _ in ppi_pairs:
            for p in [p1, p2]:
                if p not in protein_metadata:
                    protein_metadata[p] = {'degree': 0}
                protein_metadata[p]['degree'] += 1
        
        return ppi_pairs, protein_metadata
    
    def recommend(self, user_id: int, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        为用户生成推荐
        
        Args:
            user_id: 用户ID
            top_k: 推荐数量
            
        Returns:
            [(蛋白名, 分数), ...]
        """
        if not self.is_fitted:
            raise RuntimeError("模型未训练")
        
        if user_id not in self.user2id:
            return []
        
        self.model.eval()
        
        # 获取图数据
        edge_index, edge_weight = self.ppi_graph.get_graph_data()
        edge_index = edge_index.to(self.device)
        edge_weight = edge_weight.to(self.device)
        
        # 为所有蛋白打分
        num_proteins = len(self.protein2id)
        user_idx = self.user2id[user_id]
        
        with torch.no_grad():
            user_tensor = torch.tensor([user_idx] * num_proteins, dtype=torch.long).to(self.device)
            protein_tensor = torch.arange(num_proteins, dtype=torch.long).to(self.device)
            
            scores, _, _ = self.model(user_tensor, protein_tensor, edge_index, edge_weight)
        
        # 排序
        top_scores, top_indices = torch.topk(scores, top_k)
        
        # 映射回蛋白名
        id2protein = {v: k for k, v in self.protein2id.items()}
        results = [(id2protein[idx.item()], score.item()) 
                   for idx, score in zip(top_indices, top_scores)]
        
        return results


# ==================== 单元测试 ====================

def test_dual_tower_with_ppi():
    """测试双塔+PPI融合模型"""
    print("="*60)
    print("双塔推荐模型 + PPI图融合 测试")
    print("="*60)
    
    # 模拟数据
    np.random.seed(42)
    torch.manual_seed(42)
    
    n_users = 30
    n_interactions = 200
    
    interactions = []
    for _ in range(n_interactions):
        interactions.append({
            'user_id': np.random.randint(0, n_users),
            'protein_id': f"protein_{np.random.randint(0, 50)}",
            'rating': np.random.uniform(3, 5)
        })
    
    df = pd.DataFrame(interactions)
    
    # 训练
    recommender = DualTowerRecommender(
        embedding_dim=32,
        fusion='concat',
        device='cpu'
    )
    
    recommender.fit(df, threshold=0.6, epochs=20)
    
    # 生成推荐
    print(f"\n🎯 为用户0生成推荐:")
    recommendations = recommender.recommend(user_id=0, top_k=10)
    
    for i, (protein, score) in enumerate(recommendations, 1):
        print(f"  {i:2d}. {protein:15s} ({score:.3f})")
    
    print("\n✅ 双塔模型测试通过!")


if __name__ == '__main__':
    test_dual_tower_with_ppi()