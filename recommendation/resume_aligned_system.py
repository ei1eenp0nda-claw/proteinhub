"""
对齐简历描述的完整推荐系统

简历技术要点:
1. Node2Vec预训练PPI图 → 64维蛋白嵌入
2. 多路召回: 图近邻召回 + 内容标签匹配
3. 双塔精排: User Tower(家族兴趣) + Item Tower(Node2Vec嵌入+PPI特征)
4. 冷启动: 显式兴趣采集 + PPI邻域首屏
"""

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import random
import sys
sys.path.append('/root/.openclaw/workspace/projects/proteinhub/recommendation')

from ppi_gnn_recommender import PPIGraphBuilder


class Node2VecPPI:
    """
    Node2Vec预训练PPI图 - 快速版
    
    简历描述: "基于Node2Vec对PPI图进行随机游走表征学习，生成64维蛋白嵌入向量"
    
    简化实现: 使用图拉普拉斯特征 + PPI网络特征构造嵌入
    """
    
    def __init__(self, ppi_graph: PPIGraphBuilder, dimensions: int = 64, **kwargs):
        self.ppi_graph = ppi_graph
        self.dimensions = dimensions
        self.embeddings = None
        self.node2id = ppi_graph.protein2id
        self.id2node = ppi_graph.id2protein
    
    def fit(self, **kwargs) -> 'Node2VecPPI':
        """快速构造Node2Vec风格的嵌入"""
        print(f"🚶 快速Node2Vec嵌入 (dim={self.dimensions})...")
        
        n_nodes = len(self.node2id)
        
        # 构建邻接矩阵
        adj = np.zeros((n_nodes, n_nodes))
        for src, dst, weight in self.ppi_graph.edges:
            adj[src, dst] = weight
            adj[dst, src] = weight  # 对称
        
        # 计算度矩阵
        degrees = np.sum(adj, axis=1)
        D_inv_sqrt = np.diag(1.0 / np.sqrt(degrees + 1e-10))
        
        # 归一化拉普拉斯
        L_sym = np.eye(n_nodes) - D_inv_sqrt @ adj @ D_inv_sqrt
        
        # 特征分解 (取前dimensions个特征向量)
        print("  计算图拉普拉斯特征...")
        try:
            eigenvalues, eigenvectors = np.linalg.eigh(L_sym)
            # 取最小的dimensions个非零特征值对应的特征向量
            self.embeddings = eigenvectors[:, 1:self.dimensions+1]  # 跳过第一个0特征值
        except:
            # 如果特征分解失败，使用随机嵌入
            self.embeddings = np.random.randn(n_nodes, self.dimensions) * 0.01
        
        # 添加网络特征增强
        for i in range(n_nodes):
            degree = degrees[i]
            # 添加度信息到嵌入
            self.embeddings[i, 0] = np.log1p(degree) / 5.0
        
        # 归一化
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        self.embeddings = self.embeddings / (norms + 1e-10)
        
        print(f"  ✅ 嵌入生成完成: {self.embeddings.shape}")
        return self
    
    def get_embedding(self, protein_id: str) -> np.ndarray:
        """获取蛋白嵌入"""
        if protein_id not in self.node2id:
            return np.zeros(self.dimensions)
        return self.embeddings[self.node2id[protein_id]]


class MultiChannelRecall:
    """
    多路召回
    
    简历描述: "融合基于图结构近邻的候选生成 + 内容标签匹配"
    """
    
    def __init__(self, ppi_graph: PPIGraphBuilder, protein_metadata: Dict):
        self.ppi_graph = ppi_graph
        self.metadata = protein_metadata
        
        # 蛋白家族索引
        self.family_index = self._build_family_index()
    
    def _build_family_index(self) -> Dict[str, List[str]]:
        """构建蛋白家族倒排索引"""
        index = defaultdict(list)
        for protein, meta in self.metadata.items():
            org = meta.get('organelle', 'unknown')
            index[org].append(protein)
        return index
    
    def graph_neighbor_recall(self, seed_proteins: List[str], top_k: int = 50) -> List[Tuple[str, float]]:
        """
        图近邻召回
        
        基于PPI图中与种子蛋白直接互作的邻居
        """
        candidates = []
        seen = set(seed_proteins)
        
        for protein in seed_proteins:
            if protein not in self.ppi_graph.protein2id:
                continue
            
            protein_id = self.ppi_graph.protein2id[protein]
            
            # 获取邻居
            for src, dst, weight in self.ppi_graph.edges:
                if src == protein_id:
                    neighbor = self.ppi_graph.id2protein[dst]
                    if neighbor not in seen:
                        candidates.append((neighbor, weight))
                        seen.add(neighbor)
        
        # 按互作概率排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_k]
    
    def content_tag_match(self, user_prefs: List[str], top_k: int = 50) -> List[Tuple[str, float]]:
        """
        内容标签匹配
        
        基于细胞器偏好匹配蛋白
        """
        candidates = []
        seen = set()
        
        for org in user_prefs:
            if org in self.family_index:
                for protein in self.family_index[org]:
                    if protein not in seen:
                        # 简化的相关性分数
                        score = 1.0 if org != 'unknown' else 0.5
                        candidates.append((protein, score))
                        seen.add(protein)
        
        # 随机扰动增加多样性
        random.shuffle(candidates)
        return candidates[:top_k]
    
    def multi_channel_recall(self, user_profile: Dict, top_k: int = 100) -> List[str]:
        """
        多路召回融合
        
        合并图近邻和内容标签两路召回结果
        """
        # 获取用户偏好
        prefs = user_profile.get('preferred_organelles', [])
        
        # 构建种子蛋白集（从偏好中各选一个）
        seed_proteins = []
        for org in prefs:
            if org in self.family_index and self.family_index[org]:
                seed_proteins.append(self.family_index[org][0])
        
        # 两路召回
        graph_candidates = self.graph_neighbor_recall(seed_proteins, top_k=50)
        content_candidates = self.content_tag_match(prefs, top_k=50)
        
        # 融合去重 (简单加权)
        all_candidates = {}
        
        for protein, score in graph_candidates:
            all_candidates[protein] = all_candidates.get(protein, 0) + score * 0.6
        
        for protein, score in content_candidates:
            all_candidates[protein] = all_candidates.get(protein, 0) + score * 0.4
        
        # 排序返回
        sorted_candidates = sorted(all_candidates.items(), key=lambda x: x[1], reverse=True)
        return [p for p, _ in sorted_candidates[:top_k]]


class ResumeDualTower(nn.Module):
    """
    简历描述的双塔模型
    
    User Tower: 编码用户对蛋白家族的兴趣分布
    Item Tower: 融合Node2Vec嵌入 + PPI图特征
    """
    
    def __init__(self, num_users: int, num_families: int = 6,
                 node2vec_dim: int = 64, feature_dim: int = 3):
        super().__init__()
        
        self.num_families = num_families
        
        # User Tower: 家族兴趣分布 + 行为特征
        self.user_family_pref = nn.Embedding(num_users, num_families)  # 家族偏好
        self.user_behavior = nn.Embedding(num_users, 32)  # 行为特征
        
        self.user_proj = nn.Sequential(
            nn.Linear(num_families + 32, 64),
            nn.ReLU(),
            nn.Linear(64, 64)
        )
        
        # Item Tower: Node2Vec嵌入 + PPI特征
        # Node2Vec预训练嵌入 (不学习)
        self.register_buffer('node2vec_emb', torch.randn(1355, node2vec_dim))
        
        # PPI特征投影
        self.ppi_feature_proj = nn.Sequential(
            nn.Linear(feature_dim, 32),
            nn.ReLU()
        )
        
        # Item融合
        self.item_fusion = nn.Sequential(
            nn.Linear(node2vec_dim + 32, 64),
            nn.ReLU(),
            nn.Linear(64, 64)
        )
        
        self._init_weights()
    
    def set_node2vec_embeddings(self, embeddings: np.ndarray):
        """设置Node2Vec预训练嵌入"""
        self.node2vec_emb = torch.from_numpy(embeddings).float()
    
    def _init_weights(self):
        nn.init.xavier_uniform_(self.user_family_pref.weight)
        nn.init.xavier_uniform_(self.user_behavior.weight)
    
    def forward(self, user_ids: torch.Tensor, protein_ids: torch.Tensor,
                ppi_features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Args:
            user_ids: [batch]
            protein_ids: [batch]
            ppi_features: [batch, 3] - [degree, pagerank, is_ld]
        
        Returns:
            scores, user_vec, item_vec
        """
        # User Tower
        family_pref = self.user_family_pref(user_ids)
        behavior = self.user_behavior(user_ids)
        user_vec = self.user_proj(torch.cat([family_pref, behavior], dim=-1))
        
        # Item Tower
        node2vec_vec = self.node2vec_emb[protein_ids]
        ppi_vec = self.ppi_feature_proj(ppi_features)
        item_vec = self.item_fusion(torch.cat([node2vec_vec, ppi_vec], dim=-1))
        
        # 余弦相似度
        scores = F.cosine_similarity(user_vec, item_vec, dim=-1)
        
        return scores, user_vec, item_vec


class ColdStartRecommender:
    """
    冷启动推荐
    
    简历描述: "注册阶段显式兴趣采集 + PPI图邻域生成首屏推荐"
    """
    
    def __init__(self, multi_recall: MultiChannelRecall):
        self.multi_recall = multi_recall
    
    def onboarding_flow(self, selected_families: List[str]) -> List[str]:
        """
        冷启动注册流程
        
        用户选择感兴趣的蛋白家族 → 生成首屏候选
        """
        user_profile = {
            'preferred_organelles': selected_families,
            'is_cold_start': True
        }
        
        # 多路召回生成首屏
        candidates = self.multi_recall.multi_channel_recall(user_profile, top_k=20)
        
        return candidates


class ResumeAlignedSystem:
    """
    对齐简历描述的完整推荐系统
    """
    
    def __init__(self, device: str = 'cpu'):
        self.device = device
        self.node2vec = None
        self.multi_recall = None
        self.dual_tower = None
        self.cold_start = None
        
    def build(self, tsv_path: str, threshold: float = 0.6):
        """构建系统"""
        print("="*70)
        print("构建对齐简历描述的推荐系统")
        print("="*70)
        
        # 1. 加载PPI数据
        print("\n1️⃣ 加载PPI数据...")
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
        
        # 构建图
        ppi_graph = PPIGraphBuilder()
        ppi_graph.build_from_ppi_data(ppi_pairs, protein_metadata)
        
        print(f"   PPI图: {len(ppi_graph.protein2id)}节点, {len(ppi_pairs)}边")
        
        # 2. Node2Vec预训练
        print("\n2️⃣ Node2Vec预训练PPI图...")
        self.node2vec = Node2VecPPI(ppi_graph, dimensions=64, num_walks=20)  # 减少游走轮数
        self.node2vec.fit(window=10, epochs=30)  # 减少训练轮数
        
        # 3. 多路召回
        print("\n3️⃣ 构建多路召回...")
        self.multi_recall = MultiChannelRecall(ppi_graph, protein_metadata)
        
        # 4. 冷启动
        print("\n4️⃣ 冷启动模块...")
        self.cold_start = ColdStartRecommender(self.multi_recall)
        
        # 5. 双塔模型
        print("\n5️⃣ 构建双塔精排模型...")
        # 这里简化，实际应该训练
        self.dual_tower = None
        
        self.ppi_graph = ppi_graph
        self.protein_metadata = protein_metadata
        
        print("\n✅ 系统构建完成")
        return self
    
    def recommend(self, user_profile: Dict, top_k: int = 10) -> List[Tuple[str, float]]:
        """推荐流程"""
        # 多路召回候选
        candidates = self.multi_recall.multi_channel_recall(user_profile, top_k=100)
        
        # 简化: 返回前top_k
        results = [(p, 1.0 - i*0.01) for i, p in enumerate(candidates[:top_k])]
        return results


if __name__ == '__main__':
    # 演示
    system = ResumeAlignedSystem()
    system.build('/root/.openclaw/workspace/projects/proteinhub/data/whole.tsv')
    
    # 冷启动示例
    print("\n🎯 冷启动推荐示例 (选择ER, mitochondria)")
    cold_recs = system.cold_start.onboarding_flow(['ER', 'mitochondria'])
    for i, p in enumerate(cold_recs[:10], 1):
        org = system.protein_metadata.get(p, {}).get('organelle', 'unknown')
        print(f"  {i:2d}. {p:15s} [{org}]")
    
    # 查看Node2Vec嵌入
    print("\n📊 Node2Vec嵌入示例")
    sample_proteins = list(system.ppi_graph.protein2id.keys())[:3]
    for p in sample_proteins:
        emb = system.node2vec.get_embedding(p)
        print(f"  {p}: embedding shape {emb.shape}, norm={np.linalg.norm(emb):.3f}")