"""
ProteinHub PPI-GNN Recommender
基于图神经网络的蛋白互作推荐系统

核心架构:
1. GNN召回层 - LightGCN + PPI网络
2. 多模态融合 - 家族/文献/网络特征交叉注意力
3. 轻量精排 - 特征交叉 + 残差连接
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
import random


class PPIGraphBuilder:
    """
    构建PPI图结构
    从15万对蛋白互作数据构建图
    """
    
    def __init__(self):
        self.protein2id = {}
        self.id2protein = {}
        self.edges = []  # (src, dst, weight)
        self.adj_matrix = None
        self.protein_features = {}
    
    def build_from_ppi_data(self, ppi_pairs: List[Tuple[str, str, float]], 
                           protein_metadata: Dict):
        """
        从PPI对构建图
        
        Args:
            ppi_pairs: [(蛋白A, 蛋白B, 互作概率), ...]
            protein_metadata: {蛋白名: {'family': ..., 'function': ...}}
        """
        # 构建蛋白ID映射
        all_proteins = set()
        for p1, p2, _ in ppi_pairs:
            all_proteins.add(p1)
            all_proteins.add(p2)
        
        self.protein2id = {p: i for i, p in enumerate(sorted(all_proteins))}
        self.id2protein = {i: p for p, i in self.protein2id.items()}
        
        # 构建边列表
        self.edges = []
        for p1, p2, score in ppi_pairs:
            src = self.protein2id[p1]
            dst = self.protein2id[p2]
            self.edges.append((src, dst, score))
            self.edges.append((dst, src, score))  # 无向图
        
        # 构建特征
        self._build_features(protein_metadata)
        
        print(f"✅ PPI图构建完成: {len(self.protein2id)} 节点, {len(ppi_pairs)} 边")
        return self
    
    def _build_features(self, protein_metadata: Dict):
        """构建蛋白特征向量"""
        for protein, meta in protein_metadata.items():
            if protein not in self.protein2id:
                continue
            
            features = []
            
            # 家族特征 (one-hot or embedding index)
            family = meta.get('family', 'unknown')
            features.append(family)
            
            # 功能类别
            functions = meta.get('functions', [])
            features.extend(functions)
            
            # 亚细胞定位
            location = meta.get('location', 'unknown')
            features.append(location)
            
            # 网络特征 (后续计算)
            features.append(meta.get('degree', 0))
            features.append(meta.get('centrality', 0.0))
            
            self.protein_features[self.protein2id[protein]] = features
    
    def get_neighbors(self, protein_id: int, top_k: int = 10) -> List[Tuple[int, float]]:
        """获取蛋白的邻居节点"""
        neighbors = [(dst, weight) for src, dst, weight in self.edges if src == protein_id]
        neighbors.sort(key=lambda x: x[1], reverse=True)
        return neighbors[:top_k]
    
    def get_graph_data(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        获取PyG格式的图数据
        
        Returns:
            edge_index: [2, num_edges]
            edge_weight: [num_edges]
        """
        edge_index = torch.tensor([[e[0], e[1]] for e in self.edges]).t()
        edge_weight = torch.tensor([e[2] for e in self.edges], dtype=torch.float)
        return edge_index, edge_weight


class LightGCNConv(nn.Module):
    """
    LightGCN图卷积层
    简化版GCN，去除特征变换和非线性激活，更适合推荐场景
    """
    
    def __init__(self):
        super().__init__()
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, 
                edge_weight: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: [num_nodes, feature_dim]
            edge_index: [2, num_edges]
            edge_weight: [num_edges]
        """
        num_nodes = x.size(0)
        
        # 计算归一化邻接矩阵
        row, col = edge_index
        
        # 计算度
        deg = torch.zeros(num_nodes, device=x.device)
        deg.index_add_(0, row, torch.ones_like(row, dtype=torch.float))
        
        # 归一化
        deg_inv_sqrt = deg.pow(-0.5)
        deg_inv_sqrt[deg_inv_sqrt == float('inf')] = 0
        
        # 消息传递
        if edge_weight is None:
            edge_weight = torch.ones(edge_index.size(1), device=x.device)
        
        # 归一化边权重
        norm = deg_inv_sqrt[row] * edge_weight * deg_inv_sqrt[col]
        
        # 聚合邻居信息
        out = torch.zeros_like(x)
        for i in range(edge_index.size(1)):
            src, dst = edge_index[0, i], edge_index[1, i]
            out[dst] += norm[i] * x[src]
        
        return out


class PPILightGCN(nn.Module):
    """
    PPI-aware LightGCN推荐模型
    
    核心思想:
    - 使用LightGCN在PPI图上传播用户和物品嵌入
    - 利用蛋白互作网络增强蛋白表示
    """
    
    def __init__(self, num_users: int, num_items: int, 
                 embedding_dim: int = 64, num_layers: int = 3,
                 ppi_graph: Optional[PPIGraphBuilder] = None):
        super().__init__()
        
        self.num_users = num_users
        self.num_items = num_items
        self.embedding_dim = embedding_dim
        self.num_layers = num_layers
        self.ppi_graph = ppi_graph
        
        # 用户和物品嵌入
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.item_embedding = nn.Embedding(num_items, embedding_dim)
        
        # LightGCN层
        self.convs = nn.ModuleList([LightGCNConv() for _ in range(num_layers)])
        
        # 初始化
        self._init_weights()
    
    def _init_weights(self):
        """Xavier初始化"""
        nn.init.xavier_uniform_(self.user_embedding.weight)
        nn.init.xavier_uniform_(self.item_embedding.weight)
    
    def forward(self, user_ids: torch.Tensor, item_ids: torch.Tensor,
                edge_index: torch.Tensor, edge_weight: Optional[torch.Tensor] = None):
        """
        前向传播
        
        Args:
            user_ids: [batch_size]
            item_ids: [batch_size]
            edge_index: [2, num_edges]
            edge_weight: [num_edges]
        """
        # 初始嵌入
        x_users = self.user_embedding.weight
        x_items = self.item_embedding.weight
        x = torch.cat([x_users, x_items], dim=0)
        
        # 多层传播
        embeddings = [x]
        for conv in self.convs:
            x = conv(x, edge_index, edge_weight)
            embeddings.append(x)
        
        # 层聚合 (平均)
        final_embedding = torch.stack(embeddings, dim=0).mean(dim=0)
        
        # 分离用户和物品嵌入
        user_emb = final_embedding[:self.num_users]
        item_emb = final_embedding[self.num_users:]
        
        # 获取batch嵌入
        u_emb = user_emb[user_ids]
        i_emb = item_emb[item_ids]
        
        # 计算分数
        scores = (u_emb * i_emb).sum(dim=1)
        
        return scores, u_emb, i_emb
    
    def get_recommendations(self, user_id: int, edge_index: torch.Tensor,
                           edge_weight: Optional[torch.Tensor] = None,
                           top_k: int = 10) -> List[Tuple[int, float]]:
        """
        为指定用户生成推荐
        
        Returns:
            [(item_id, score), ...]
        """
        self.eval()
        with torch.no_grad():
            # 计算所有嵌入
            x_users = self.user_embedding.weight
            x_items = self.item_embedding.weight
            x = torch.cat([x_users, x_items], dim=0)
            
            embeddings = [x]
            for conv in self.convs:
                x = conv(x, edge_index, edge_weight)
                embeddings.append(x)
            
            final_embedding = torch.stack(embeddings, dim=0).mean(dim=0)
            user_emb = final_embedding[user_id]
            item_emb = final_embedding[self.num_users:]
            
            # 计算所有物品分数
            scores = torch.matmul(user_emb, item_emb.t())
            
            # Top-K
            top_scores, top_indices = torch.topk(scores, top_k)
            
            return [(idx.item(), score.item()) for idx, score in zip(top_indices, top_scores)]


class CrossModalAttention(nn.Module):
    """
    跨模态交叉注意力融合
    
    参考: MR-CSAF (Multimodal Recommendation with Cross Self-Attention Fusion)
    用于融合蛋白的多种特征:
    - 序列特征 (家族/功能)
    - 网络特征 (PPI图嵌入)
    - 文献特征 (PubMed文本)
    """
    
    def __init__(self, dim: int, num_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.scale = self.head_dim ** -0.5
        
        self.q_proj = nn.Linear(dim, dim)
        self.k_proj = nn.Linear(dim, dim)
        self.v_proj = nn.Linear(dim, dim)
        self.out_proj = nn.Linear(dim, dim)
        
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(dim)
    
    def forward(self, query: torch.Tensor, key: torch.Tensor, 
                value: torch.Tensor, mask: Optional[torch.Tensor] = None):
        """
        Args:
            query: [batch, seq_len_q, dim]
            key: [batch, seq_len_k, dim]
            value: [batch, seq_len_v, dim]
            mask: [batch, seq_len_q, seq_len_k]
        """
        batch_size = query.size(0)
        
        # 投影
        Q = self.q_proj(query).view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        K = self.k_proj(key).view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        V = self.v_proj(value).view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 注意力
        scores = torch.matmul(Q, K.transpose(-2, -1)) * self.scale
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attn = F.softmax(scores, dim=-1)
        attn = self.dropout(attn)
        
        out = torch.matmul(attn, V)
        out = out.transpose(1, 2).contiguous().view(batch_size, -1, self.num_heads * self.head_dim)
        
        out = self.out_proj(out)
        out = self.dropout(out)
        
        # 残差连接
        out = self.layer_norm(query + out)
        
        return out, attn


class MultimodalFusion(nn.Module):
    """
    多模态融合模块
    
    融合三种模态:
    1. 序列模态: 蛋白家族、功能分类
    2. 图模态: PPI网络嵌入 (来自LightGCN)
    3. 文本模态: 文献摘要嵌入 (预训练模型)
    """
    
    def __init__(self, dim: int = 64, num_heads: int = 4):
        super().__init__()
        
        self.dim = dim
        
        # 模态投影
        self.seq_proj = nn.Linear(dim, dim)
        self.graph_proj = nn.Linear(dim, dim)
        self.text_proj = nn.Linear(dim, dim)
        
        # 交叉注意力
        self.cross_attn_seq_graph = CrossModalAttention(dim, num_heads)
        self.cross_attn_seq_text = CrossModalAttention(dim, num_heads)
        self.cross_attn_graph_text = CrossModalAttention(dim, num_heads)
        
        # 融合门控
        self.gate = nn.Sequential(
            nn.Linear(dim * 3, dim),
            nn.Sigmoid()
        )
        
        # 输出投影
        self.output_proj = nn.Sequential(
            nn.Linear(dim * 3, dim),
            nn.LayerNorm(dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
    
    def forward(self, seq_feat: torch.Tensor, graph_feat: torch.Tensor,
                text_feat: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            seq_feat: [batch, dim] - 序列特征
            graph_feat: [batch, dim] - 图特征
            text_feat: [batch, dim] or None - 文本特征
        """
        # 投影
        seq = self.seq_proj(seq_feat).unsqueeze(1)  # [batch, 1, dim]
        graph = self.graph_proj(graph_feat).unsqueeze(1)
        
        # seq <-> graph 交叉
        seq_enhanced, _ = self.cross_attn_seq_graph(seq, graph, graph)
        graph_enhanced, _ = self.cross_attn_seq_graph(graph, seq, seq)
        
        # 如果有文本特征
        if text_feat is not None:
            text = self.text_proj(text_feat).unsqueeze(1)
            
            # 与文本交叉
            seq_enhanced, _ = self.cross_attn_seq_text(seq_enhanced, text, text)
            graph_enhanced, _ = self.cross_attn_graph_text(graph_enhanced, text, text)
            
            # 拼接所有模态
            fused = torch.cat([
                seq_enhanced.squeeze(1),
                graph_enhanced.squeeze(1),
                text.squeeze(1)
            ], dim=-1)
        else:
            # 拼接两种模态
            fused = torch.cat([
                seq_enhanced.squeeze(1),
                graph_enhanced.squeeze(1),
                torch.zeros_like(seq.squeeze(1))  # 占位
            ], dim=-1)
        
        # 门控融合
        gate_weights = self.gate(fused)
        
        # 最终输出
        output = self.output_proj(fused)
        
        return output * gate_weights


class QuickReranker(nn.Module):
    """
    轻量级精排模型
    
    基于特征交叉 + 残差连接
    参考DeepFM的FM部分，但更加轻量
    """
    
    def __init__(self, feature_dim: int = 64, num_fields: int = 4,
                 mlp_dims: List[int] = [128, 64]):
        super().__init__()
        
        # FM部分: 二阶交叉
        self.fm_linear = nn.Linear(feature_dim * num_fields, 1)
        self.fm_v = nn.Parameter(torch.randn(feature_dim, num_fields))
        
        # Deep部分: MLP
        input_dim = feature_dim * num_fields
        layers = []
        for dim in mlp_dims:
            layers.extend([
                nn.Linear(input_dim, dim),
                nn.LayerNorm(dim),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            input_dim = dim
        layers.append(nn.Linear(input_dim, 1))
        self.mlp = nn.Sequential(*layers)
    
    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """
        Args:
            features: [batch, num_fields, feature_dim]
        """
        batch_size = features.size(0)
        flat_features = features.view(batch_size, -1)
        
        # FM线性部分
        fm_linear = self.fm_linear(flat_features)
        
        # FM二阶交叉: sum_square - square_sum
        # features: [batch, num_fields, feature_dim]
        # fm_v: [feature_dim, num_fields] -> 转置为 [num_fields, feature_dim]
        fm_v = self.fm_v.t()  # [num_fields, feature_dim]
        square_of_sum = torch.sum(features * fm_v.unsqueeze(0), dim=1) ** 2
        sum_of_square = torch.sum((features * fm_v.unsqueeze(0)) ** 2, dim=1)
        fm_interaction = 0.5 * torch.sum(square_of_sum - sum_of_square, dim=1, keepdim=True)
        
        # Deep部分
        deep_out = self.mlp(flat_features)
        
        # 组合
        output = torch.sigmoid(fm_linear + fm_interaction + deep_out)
        
        return output.squeeze(-1)


class PPIEnhancedRecommender:
    """
    PPI增强的推荐系统 (完整流程)
    
    三步架构:
    1. GNN召回: LightGCN在PPI图上召回候选
    2. 多模态融合: 交叉注意力融合蛋白特征
    3. 轻量精排: FM + Deep特征交叉重排序
    """
    
    def __init__(self, embedding_dim: int = 64, device: str = 'cpu'):
        self.embedding_dim = embedding_dim
        self.device = device
        
        self.ppi_graph = None
        self.gnn_model = None
        self.fusion_model = None
        self.reranker = None
        self.is_fitted = False
    
    def fit(self, interactions: pd.DataFrame, ppi_pairs: List[Tuple],
            protein_features: Dict, user_features: Optional[Dict] = None):
        """
        训练推荐模型
        
        Args:
            interactions: DataFrame [user_id, item_id, rating]
            ppi_pairs: [(蛋白A, 蛋白B, 概率), ...]
            protein_features: {蛋白名: {特征字典}}
            user_features: {用户ID: {特征字典}}
        """
        print("🔄 训练PPI增强推荐模型...")
        
        # 1. 构建PPI图
        self.ppi_graph = PPIGraphBuilder()
        self.ppi_graph.build_from_ppi_data(ppi_pairs, protein_features)
        
        # 2. 准备数据
        self.num_users = interactions['user_id'].nunique()
        self.num_items = interactions['item_id'].nunique()
        
        self.user2id = {u: i for i, u in enumerate(interactions['user_id'].unique())}
        self.item2id = {i: j for j, i in enumerate(interactions['item_id'].unique())}
        
        # 3. 初始化模型
        edge_index, edge_weight = self.ppi_graph.get_graph_data()
        edge_index = edge_index.to(self.device)
        edge_weight = edge_weight.to(self.device)
        
        self.gnn_model = PPILightGCN(
            num_users=self.num_users,
            num_items=self.num_items,
            embedding_dim=self.embedding_dim,
            num_layers=3,
            ppi_graph=self.ppi_graph
        ).to(self.device)
        
        self.fusion_model = MultimodalFusion(dim=self.embedding_dim).to(self.device)
        self.reranker = QuickReranker(feature_dim=self.embedding_dim).to(self.device)
        
        # 4. 简单训练 (这里用随机梯度下降示例)
        self._train_gnn(interactions, edge_index, edge_weight)
        
        self.is_fitted = True
        print("✅ 模型训练完成")
        
        return self
    
    def _train_gnn(self, interactions: pd.DataFrame, edge_index: torch.Tensor,
                   edge_weight: torch.Tensor, epochs: int = 100):
        """训练GNN模型"""
        optimizer = torch.optim.Adam(self.gnn_model.parameters(), lr=0.01)
        
        user_ids = torch.tensor([self.user2id[u] for u in interactions['user_id']], dtype=torch.long)
        item_ids = torch.tensor([self.item2id[i] for i in interactions['item_id']], dtype=torch.long)
        ratings = torch.tensor(interactions['rating'].values, dtype=torch.float)
        
        for epoch in range(epochs):
            self.gnn_model.train()
            optimizer.zero_grad()
            
            scores, _, _ = self.gnn_model(user_ids, item_ids, edge_index, edge_weight)
            
            # BPR损失 (简化版)
            loss = F.mse_loss(scores, ratings)
            
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 20 == 0:
                print(f"  Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")
    
    def recommend(self, user_id: int, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        为用户生成推荐
        
        Args:
            user_id: 用户ID
            top_k: 推荐数量
            
        Returns:
            [(item_id, score), ...]
        """
        if not self.is_fitted:
            raise RuntimeError("模型未训练")
        
        # Step 1: GNN召回 (扩大候选集)
        edge_index, edge_weight = self.ppi_graph.get_graph_data()
        edge_index = edge_index.to(self.device)
        edge_weight = edge_weight.to(self.device)
        
        candidates = self.gnn_model.get_recommendations(
            self.user2id.get(user_id, 0),
            edge_index, edge_weight,
            top_k=top_k * 3  # 召回更多供精排
        )
        
        # Step 2: 多模态融合 (增强物品表示)
        # Step 3: 精排
        # (简化实现：直接返回GNN结果)
        
        # 映射回原始ID
        id2item = {v: k for k, v in self.item2id.items()}
        results = [(id2item.get(idx, idx), score) for idx, score in candidates[:top_k]]
        
        return results


# ==================== 快速使用接口 ====================

def build_ppi_recommender(ppi_data_path: str, 
                         interaction_data_path: str,
                         embedding_dim: int = 64) -> PPIEnhancedRecommender:
    """
    快速构建PPI增强推荐系统
    
    Args:
        ppi_data_path: PPI数据CSV路径 (protein_a, protein_b, score)
        interaction_data_path: 交互数据CSV路径 (user_id, item_id, rating)
        embedding_dim: 嵌入维度
    
    Returns:
        训练好的推荐模型
    """
    # 加载数据
    ppi_df = pd.read_csv(ppi_data_path)
    interactions = pd.read_csv(interaction_data_path)
    
    # 构建PPI对
    ppi_pairs = [
        (row['protein_a'], row['protein_b'], row['score'])
        for _, row in ppi_df.iterrows()
    ]
    
    # 构建蛋白特征 (简化版)
    all_proteins = set(ppi_df['protein_a']) | set(ppi_df['protein_b'])
    protein_features = {
        p: {
            'family': p.split('_')[0] if '_' in p else 'unknown',
            'functions': [],
            'degree': ppi_df[ppi_df['protein_a'] == p].shape[0] + 
                     ppi_df[ppi_df['protein_b'] == p].shape[0]
        }
        for p in all_proteins
    }
    
    # 训练模型
    recommender = PPIEnhancedRecommender(embedding_dim=embedding_dim)
    recommender.fit(interactions, ppi_pairs, protein_features)
    
    return recommender


if __name__ == '__main__':
    print("PPI-GNN Recommender Module")
    print("="*50)
    print("核心组件:")
    print("  1. PPIGraphBuilder - 构建PPI图")
    print("  2. PPILightGCN - 轻量级图神经网络")
    print("  3. MultimodalFusion - 多模态交叉注意力融合")
    print("  4. QuickReranker - 轻量精排")
    print("="*50)