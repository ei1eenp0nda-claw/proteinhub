"""
GNN模块验证测试 - 使用真实PPI数据 (阈值>=0.6)

测试内容:
1. PPIGraphBuilder - 从whole.csv构建图
2. PPILightGCN - 图神经网络前向传播
3. 端到端推荐流程
"""

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict
from collections import defaultdict
import sys
sys.path.append('/root/.openclaw/workspace/projects/proteinhub/recommendation')

# 导入要测试的模块
from ppi_gnn_recommender import (
    PPIGraphBuilder, PPILightGCN, MultimodalFusion, QuickReranker
)


def load_ppi_data(threshold: float = 0.6) -> Tuple[List[Tuple], Dict]:
    """
    加载并筛选PPI数据
    
    Returns:
        ppi_pairs: [(蛋白A, 蛋白B, 概率), ...]
        protein_metadata: {蛋白名: {'family': ..., 'organelle': ...}}
    """
    print(f"📚 加载PPI数据 (阈值>={threshold})...")
    
    df = pd.read_csv('/root/.openclaw/workspace/projects/proteinhub/data/whole.tsv', sep='\t')
    
    # 筛选阈值，并排除空值
    df_filtered = df[(df['probability'] >= threshold) & (df['probability'].notna())].copy()
    
    print(f"  原始数据: {len(df)} 对")
    print(f"  筛选后: {len(df_filtered)} 对 (阈值>={threshold})")
    
    # 构建PPI对
    ppi_pairs = []
    for _, row in df_filtered.iterrows():
        p1 = row['LD_protein_symbol'] if pd.notna(row['LD_protein_symbol']) else row['LD_protein']
        p2 = row['organelle_protein_symbol'] if pd.notna(row['organelle_protein_symbol']) else row['organelle_protein']
        score = row['probability']
        
        ppi_pairs.append((p1, p2, score))
    
    # 构建蛋白元数据
    protein_metadata = {}
    all_proteins = set()
    for p1, p2, _ in ppi_pairs:
        all_proteins.add(p1)
        all_proteins.add(p2)
    
    for protein in all_proteins:
        # 找这个蛋白所在的行
        rows = df_filtered[
            (df_filtered['LD_protein_symbol'] == protein) | 
            (df_filtered['LD_protein'] == protein)
        ]
        if len(rows) > 0:
            organelle = rows.iloc[0]['organelle']
        else:
            organelle = 'unknown'
        
        protein_metadata[protein] = {
            'family': 'LD' if protein in df_filtered['LD_protein_symbol'].values else 'organelle',
            'organelle': organelle if pd.notna(organelle) else 'unknown',
            'degree': 0  # 稍后计算
        }
    
    # 计算degree
    for p1, p2, _ in ppi_pairs:
        protein_metadata[p1]['degree'] += 1
        protein_metadata[p2]['degree'] += 1
    
    return ppi_pairs, protein_metadata


def test_graph_builder():
    """测试图构建"""
    print("\n" + "="*60)
    print("测试1: PPIGraphBuilder - 图构建")
    print("="*60)
    
    ppi_pairs, protein_metadata = load_ppi_data(threshold=0.6)
    
    # 构建图
    graph = PPIGraphBuilder()
    graph.build_from_ppi_data(ppi_pairs, protein_metadata)
    
    print(f"✅ 图构建成功")
    print(f"  蛋白数量: {len(graph.protein2id)}")
    print(f"  边数量: {len(graph.edges)}")
    
    # 统计信息
    degrees = [meta['degree'] for meta in protein_metadata.values()]
    print(f"  平均度数: {np.mean(degrees):.2f}")
    print(f"  最大度数: {max(degrees)}")
    
    # 检查图数据
    edge_index, edge_weight = graph.get_graph_data()
    print(f"  Edge index shape: {edge_index.shape}")
    print(f"  Edge weight shape: {edge_weight.shape}")
    
    assert len(graph.protein2id) > 0, "图中没有蛋白"
    assert len(graph.edges) > 0, "图中没有边"
    
    return graph, ppi_pairs, protein_metadata


def test_lightgcn(graph: PPIGraphBuilder):
    """测试LightGCN模型"""
    print("\n" + "="*60)
    print("测试2: PPILightGCN - 图神经网络")
    print("="*60)
    
    num_users = 100  # 模拟用户数
    num_items = len(graph.protein2id)  # 蛋白作为物品
    embedding_dim = 64
    
    print(f"  Users: {num_users}, Items: {num_items}, Dim: {embedding_dim}")
    
    # 初始化模型
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"  使用设备: {device}")
    
    model = PPILightGCN(
        num_users=num_users,
        num_items=num_items,
        embedding_dim=embedding_dim,
        num_layers=3,
        ppi_graph=graph
    ).to(device)
    
    # 准备图数据
    edge_index, edge_weight = graph.get_graph_data()
    edge_index = edge_index.to(device)
    edge_weight = edge_weight.to(device)
    
    # 模拟用户-物品交互
    batch_size = 32
    user_ids = torch.randint(0, num_users, (batch_size,)).to(device)
    item_ids = torch.randint(0, num_items, (batch_size,)).to(device)
    
    # 前向传播
    model.eval()
    with torch.no_grad():
        scores, user_emb, item_emb = model(user_ids, item_ids, edge_index, edge_weight)
    
    print(f"✅ LightGCN前向传播成功")
    print(f"  预测分数 shape: {scores.shape}")
    print(f"  用户embedding shape: {user_emb.shape}")
    print(f"  物品embedding shape: {item_emb.shape}")
    print(f"  分数范围: [{scores.min():.3f}, {scores.max():.3f}]")
    
    assert scores.shape == (batch_size,), f"分数形状错误: {scores.shape}"
    assert not torch.isnan(scores).any(), "分数包含NaN"
    
    # 测试推荐生成
    print(f"\n  测试推荐生成...")
    recommendations = model.get_recommendations(
        user_id=0,
        edge_index=edge_index,
        edge_weight=edge_weight,
        top_k=10
    )
    
    print(f"  为用户0推荐Top-10:")
    for i, (item_idx, score) in enumerate(recommendations[:5]):
        protein_name = graph.id2protein.get(item_idx, f"item_{item_idx}")
        print(f"    {i+1}. {protein_name}: {score:.3f}")
    
    return model, device


def test_multimodal_fusion(device: str):
    """测试多模态融合"""
    print("\n" + "="*60)
    print("测试3: MultimodalFusion - 多模态交叉注意力")
    print("="*60)
    
    dim = 64
    batch_size = 16
    
    fusion = MultimodalFusion(dim=dim).to(device)
    
    # 模拟输入 (seq_feat, graph_feat, text_feat)
    seq_emb = torch.randn(batch_size, dim).to(device)      # 家族/序列特征
    graph_emb = torch.randn(batch_size, dim).to(device)    # GNN图特征
    text_emb = torch.randn(batch_size, dim).to(device)     # 文本特征
    
    # 前向 - 3个参数
    output = fusion(seq_emb, graph_emb, text_emb)
    
    print(f"✅ 多模态融合成功")
    print(f"  输入: seq={seq_emb.shape}, graph={graph_emb.shape}, text={text_emb.shape}")
    print(f"  输出维度: {output.shape}")
    
    assert output.shape == (batch_size, dim), f"输出形状错误"
    
    # 测试无文本特征的情况
    output_no_text = fusion(seq_emb, graph_emb, None)
    print(f"  无文本特征时输出: {output_no_text.shape}")
    
    return fusion


def test_reranker(device: str):
    """测试精排器"""
    print("\n" + "="*60)
    print("测试4: QuickReranker - 轻量精排")
    print("="*60)
    
    feature_dim = 64
    num_fields = 4
    batch_size = 8
    
    reranker = QuickReranker(feature_dim=feature_dim, num_fields=num_fields).to(device)
    
    # 模拟候选物品特征: [batch, num_fields, feature_dim]
    # 4个字段: user, item, family, text
    candidate_features = torch.randn(batch_size, num_fields, feature_dim).to(device)
    
    # 前向
    scores = reranker(candidate_features)
    
    print(f"✅ 精排器成功")
    print(f"  输入: {candidate_features.shape} (batch, num_fields, feature_dim)")
    print(f"  输出分数: {scores.shape}")
    print(f"  分数范围: [{scores.min():.3f}, {scores.max():.3f}]")
    
    # 排序
    sorted_scores, sorted_indices = torch.sort(scores, descending=True)
    print(f"  排序后Top-3: {sorted_scores[:3].tolist()}")
    
    return reranker


def test_end_to_end():
    """端到端流程测试"""
    print("\n" + "="*60)
    print("测试5: 端到端推荐流程")
    print("="*60)
    
    # 1. 加载数据
    ppi_pairs, protein_metadata = load_ppi_data(threshold=0.6)
    
    # 2. 构建图
    graph = PPIGraphBuilder()
    graph.build_from_ppi_data(ppi_pairs, protein_metadata)
    
    # 3. 模拟用户交互数据
    num_users = 50
    num_items = len(graph.protein2id)
    
    # 随机生成一些交互
    interactions = []
    for user_id in range(num_users):
        # 每个用户交互3-10个蛋白
        n_interactions = np.random.randint(3, 11)
        items = np.random.choice(num_items, size=n_interactions, replace=False)
        for item_id in items:
            interactions.append({
                'user_id': user_id,
                'item_id': item_id,
                'rating': np.random.uniform(3, 5)  # 正向交互
            })
    
    import pandas as pd
    df_interactions = pd.DataFrame(interactions)
    
    print(f"  模拟交互数据: {len(df_interactions)} 条")
    
    # 4. 初始化模型
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    edge_index, edge_weight = graph.get_graph_data()
    edge_index = edge_index.to(device)
    edge_weight = edge_weight.to(device)
    
    gnn_model = PPILightGCN(
        num_users=num_users,
        num_items=num_items,
        embedding_dim=32,
        num_layers=2,
        ppi_graph=graph
    ).to(device)
    
    fusion_model = MultimodalFusion(dim=32).to(device)
    reranker = QuickReranker(feature_dim=32).to(device)
    
    # 5. 简单训练 (几个epoch)
    print(f"\n  训练GNN (10 epochs)...")
    optimizer = torch.optim.Adam(gnn_model.parameters(), lr=0.01)
    
    user_ids = torch.tensor(df_interactions['user_id'].values, dtype=torch.long).to(device)
    item_ids = torch.tensor(df_interactions['item_id'].values, dtype=torch.long).to(device)
    ratings = torch.tensor(df_interactions['rating'].values, dtype=torch.float).to(device)
    
    gnn_model.train()
    for epoch in range(10):
        optimizer.zero_grad()
        
        scores, _, _ = gnn_model(user_ids, item_ids, edge_index, edge_weight)
        loss = F.mse_loss(scores, ratings / 5.0)  # 归一化到0-1
        
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 5 == 0:
            print(f"    Epoch {epoch+1}, Loss: {loss.item():.4f}")
    
    # 6. 生成推荐
    print(f"\n  为用户0生成推荐...")
    gnn_model.eval()
    with torch.no_grad():
        candidates = gnn_model.get_recommendations(
            user_id=0,
            edge_index=edge_index,
            edge_weight=edge_weight,
            top_k=10
        )
    
    print(f"✅ 端到端流程成功")
    print(f"  Top-10推荐:")
    for i, (item_idx, score) in enumerate(candidates):
        protein_name = graph.id2protein.get(item_idx, f"item_{item_idx}")
        print(f"    {i+1:2d}. {protein_name:15s} ({score:.3f})")


if __name__ == '__main__':
    print("="*60)
    print("GNN模块验证测试 (使用真实PPI数据)")
    print("="*60)
    
    np.random.seed(42)
    torch.manual_seed(42)
    
    try:
        # 测试1: 图构建
        graph, ppi_pairs, protein_metadata = test_graph_builder()
        
        # 测试2: LightGCN
        model, device = test_lightgcn(graph)
        
        # 测试3: 多模态融合
        fusion = test_multimodal_fusion(device)
        
        # 测试4: 精排器
        reranker = test_reranker(device)
        
        # 测试5: 端到端
        test_end_to_end()
        
        print("\n" + "="*60)
        print("✅ 所有GNN测试通过!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise