#!/usr/bin/env python3
"""
PPI-GNN推荐系统快速测试
一键运行，获取量化指标
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
import torch
from typing import List, Tuple

from ppi_gnn_recommender import (
    PPIGraphBuilder, PPILightGCN, MultimodalFusion, 
    QuickReranker, PPIEnhancedRecommender
)
from quick_evaluate import QuickEvaluator


def create_sample_ppi_data(n_proteins: int = 500, n_interactions: int = 5000):
    """
    创建示例PPI数据
    
    模拟15万对蛋白互作的一部分
    """
    print(f"📦 生成示例PPI数据 ({n_proteins}蛋白, {n_interactions}互作对)...")
    
    # 生成蛋白名称
    families = ['CIDE', 'PLIN', 'ADRP', 'LSDP', 'FITM', 'SEIPIN', 'LIPA', 'DGAT']
    proteins = []
    for family in families:
        for i in range(n_proteins // len(families)):
            proteins.append(f"{family}_{i:03d}")
    
    # 生成PPI对 (优先同家族互作)
    ppi_pairs = []
    for _ in range(n_interactions):
        if np.random.random() < 0.6:
            # 同家族互作
            family = np.random.choice(families)
            p1 = f"{family}_{np.random.randint(0, n_proteins // len(families)):03d}"
            p2 = f"{family}_{np.random.randint(0, n_proteins // len(families)):03d}"
        else:
            # 跨家族互作
            p1 = np.random.choice(proteins)
            p2 = np.random.choice(proteins)
        
        if p1 != p2:
            score = np.random.beta(3, 2)  # 大部分中高置信度
            ppi_pairs.append((p1, p2, score))
    
    # 蛋白元数据
    protein_metadata = {}
    for p in proteins:
        family = p.split('_')[0]
        protein_metadata[p] = {
            'family': family,
            'functions': [f'function_{i}' for i in range(np.random.randint(1, 4))],
            'degree': sum(1 for pp in ppi_pairs if p in [pp[0], pp[1]]),
            'centrality': np.random.random()
        }
    
    return ppi_pairs, protein_metadata, proteins


def create_sample_interactions(n_users: int = 200, proteins: List[str] = None):
    """创建示例用户-蛋白交互数据"""
    print(f"📦 生成示例交互数据 ({n_users}用户)...")
    
    interactions = []
    
    for user_id in range(n_users):
        # 用户类型决定行为模式
        user_type = np.random.choice(['newbie', 'regular', 'expert'], p=[0.3, 0.5, 0.2])
        
        if user_type == 'newbie':
            n_interactions = np.random.poisson(10)
        elif user_type == 'regular':
            n_interactions = np.random.poisson(30)
        else:
            n_interactions = np.random.poisson(60)
        
        # 用户偏好某些家族
        preferred_families = np.random.choice(
            ['CIDE', 'PLIN', 'ADRP', 'LSDP', 'FITM'], 
            size=np.random.randint(1, 4),
            replace=False
        )
        
        for _ in range(n_interactions):
            # 优先选择偏好家族的蛋白
            if np.random.random() < 0.7:
                family = np.random.choice(preferred_families)
                protein = f"{family}_{np.random.randint(0, 50):03d}"
            else:
                protein = np.random.choice(proteins)
            
            # 评分 (1-5)
            rating = np.random.choice([1, 2, 3, 4, 5], p=[0.1, 0.15, 0.3, 0.3, 0.15])
            
            interactions.append({
                'user_id': user_id,
                'item_id': protein,
                'rating': rating
            })
    
    return pd.DataFrame(interactions)


def test_ppi_graph_builder():
    """测试PPI图构建"""
    print("\n" + "="*60)
    print("测试1: PPI图构建")
    print("="*60)
    
    ppi_pairs, protein_metadata, proteins = create_sample_ppi_data(
        n_proteins=200, n_interactions=1000
    )
    
    graph = PPIGraphBuilder()
    graph.build_from_ppi_data(ppi_pairs, protein_metadata)
    
    # 测试邻居查询
    test_protein = proteins[0]
    test_id = graph.protein2id[test_protein]
    neighbors = graph.get_neighbors(test_id, top_k=5)
    
    print(f"✅ PPI图构建成功")
    print(f"  节点数: {len(graph.protein2id)}")
    print(f"  边数: {len(graph.edges) // 2} (无向图)")  # 除以2因为无向图存了两条边
    print(f"  示例查询: {test_protein} 的Top-5邻居:")
    for nid, score in neighbors[:3]:
        print(f"    - {graph.id2protein[nid]}: {score:.3f}")
    
    return graph


def test_light_gcn(graph: PPIGraphBuilder):
    """测试LightGCN模型"""
    print("\n" + "="*60)
    print("测试2: LightGCN模型")
    print("="*60)
    
    # 创建模拟数据
    num_users = 100
    num_items = len(graph.protein2id)
    
    # 初始化模型
    model = PPILightGCN(
        num_users=num_users,
        num_items=num_items,
        embedding_dim=32,
        num_layers=2,
        ppi_graph=graph
    )
    
    print(f"✅ LightGCN模型初始化成功")
    print(f"  用户数: {num_users}, 物品数: {num_items}")
    print(f"  嵌入维度: 32, 层数: 2")
    
    # 模拟前向
    edge_index, edge_weight = graph.get_graph_data()
    
    user_ids = torch.tensor([0, 1, 2])
    item_ids = torch.tensor([10, 20, 30])
    
    scores, u_emb, i_emb = model(user_ids, item_ids, edge_index, edge_weight)
    
    print(f"  前向测试: scores shape={scores.shape}, mean={scores.mean():.3f}")
    
    # 推荐测试
    recs = model.get_recommendations(user_id=0, edge_index=edge_index, 
                                      edge_weight=edge_weight, top_k=5)
    print(f"  推荐测试: User 0 的Top-5推荐:")
    for idx, score in recs[:3]:
        print(f"    - Item {idx}: {score:.3f}")
    
    return model


def test_multimodal_fusion():
    """测试多模态融合"""
    print("\n" + "="*60)
    print("测试3: 多模态融合")
    print("="*60)
    
    fusion = MultimodalFusion(dim=32, num_heads=4)
    
    # 模拟输入
    batch_size = 4
    seq_feat = torch.randn(batch_size, 32)   # 序列特征
    graph_feat = torch.randn(batch_size, 32)  # 图特征
    text_feat = torch.randn(batch_size, 32)   # 文本特征
    
    output = fusion(seq_feat, graph_feat, text_feat)
    
    print(f"✅ 多模态融合测试成功")
    print(f"  输入: seq={seq_feat.shape}, graph={graph_feat.shape}, text={text_feat.shape}")
    print(f"  输出: {output.shape}")
    print(f"  输出范围: [{output.min():.3f}, {output.max():.3f}]")
    
    return fusion


def test_full_pipeline():
    """测试完整流程 + 模拟评估"""
    print("\n" + "="*60)
    print("测试4: 完整推荐流程 + 模拟评估")
    print("="*60)
    
    # 1. 生成数据
    ppi_pairs, protein_metadata, proteins = create_sample_ppi_data(
        n_proteins=300, n_interactions=2000
    )
    interactions = create_sample_interactions(n_users=100, proteins=proteins)
    
    print(f"\n数据规模:")
    print(f"  PPI对: {len(ppi_pairs)}")
    print(f"  蛋白数: {len(proteins)}")
    print(f"  用户数: {interactions['user_id'].nunique()}")
    print(f"  交互数: {len(interactions)}")
    
    # 2. 训练模型
    print(f"\n🚀 训练PPI-GNN推荐模型...")
    
    # 简化版：直接使用LightGCN
    graph = PPIGraphBuilder()
    graph.build_from_ppi_data(ppi_pairs, protein_metadata)
    
    # 构建user/item映射
    user2id = {u: i for i, u in enumerate(interactions['user_id'].unique())}
    item2id = {item: i for i, item in enumerate(proteins)}
    id2item = {i: item for item, i in item2id.items()}
    
    num_users = len(user2id)
    num_items = len(item2id)
    
    model = PPILightGCN(
        num_users=num_users,
        num_items=num_items,
        embedding_dim=32,
        num_layers=2,
        ppi_graph=graph
    )
    
    # 简单训练
    edge_index, edge_weight = graph.get_graph_data()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    
    user_ids = torch.tensor([user2id[u] for u in interactions['user_id']], dtype=torch.long)
    item_ids = torch.tensor([item2id.get(i, 0) for i in interactions['item_id']], dtype=torch.long)
    ratings = torch.tensor(interactions['rating'].values, dtype=torch.float)
    
    for epoch in range(50):
        model.train()
        optimizer.zero_grad()
        
        scores, _, _ = model(user_ids, item_ids, edge_index, edge_weight)
        loss = torch.nn.functional.mse_loss(scores, ratings)
        
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 20 == 0:
            print(f"  Epoch {epoch+1}/50, Loss: {loss.item():.4f}")
    
    # 3. 创建推荐函数
    def ppi_recommender(user_id: int, top_k: int = 10) -> List[Tuple[int, float]]:
        """包装好的推荐函数"""
        if user_id not in user2id:
            # 冷启动：随机推荐
            items = np.random.choice(num_items, size=top_k, replace=False)
            return [(int(i), 0.5) for i in items]
        
        uid = user2id[user_id]
        recs = model.get_recommendations(uid, edge_index, edge_weight, top_k)
        
        # 映射回蛋白名称
        return [(id2item.get(idx, f"item_{idx}"), score) for idx, score in recs]
    
    # 4. 模拟评估
    print(f"\n🧪 运行模拟评估...")
    
    evaluator = QuickEvaluator(num_users=100, num_items=num_items)
    evaluator.setup_simulation()
    
    # 使用训练好的模型进行推荐
    evaluator.run_simulation(ppi_recommender, days=5)
    
    # 计算指标
    metrics = evaluator.calculate_metrics()
    evaluator.print_report(metrics)
    
    return metrics


def compare_baselines():
    """对比不同基线算法"""
    print("\n" + "="*60)
    print("测试5: 基线算法对比")
    print("="*60)
    
    # 定义基线算法
    def random_baseline(user_id: int, top_k: int = 10):
        """随机推荐"""
        items = np.random.choice(500, size=top_k, replace=False)
        return [(int(i), np.random.random()) for i in items]
    
    def popularity_baseline(user_id: int, top_k: int = 10):
        """热度推荐"""
        # 模拟热度分布
        popular_items = np.argsort(np.random.beta(2, 5, 500))[-top_k:][::-1]
        return [(int(i), 0.5 + 0.5 * (top_k - idx) / top_k) 
                for idx, i in enumerate(popular_items)]
    
    # 运行对比
    evaluator = QuickEvaluator(num_users=200, num_items=500)
    evaluator.setup_simulation()
    
    print("\n>>> 随机推荐")
    evaluator.run_simulation(random_baseline, days=3)
    random_metrics = evaluator.calculate_metrics()
    
    print("\n>>> 热度推荐")
    evaluator.setup_simulation()  # 重置
    evaluator.run_simulation(popularity_baseline, days=3)
    pop_metrics = evaluator.calculate_metrics()
    
    # 对比表格
    print("\n" + "="*60)
    print("对比结果")
    print("="*60)
    print(f"{'指标':<20} {'随机':<15} {'热度':<15}")
    print("-" * 60)
    
    for metric in ['CTR', 'Collect_Rate', 'Deep_Read_Rate', 'Like_Rate']:
        r_val = random_metrics['online'][metric]
        p_val = pop_metrics['online'][metric]
        print(f"{metric:<20} {r_val:<15.3f} {p_val:<15.3f}")
    
    print("="*60)


if __name__ == '__main__':
    print("="*60)
    print("ProteinHub PPI-GNN 推荐系统快速测试")
    print("="*60)
    
    # 设置随机种子
    np.random.seed(42)
    torch.manual_seed(42)
    
    # 运行测试
    try:
        # 测试1: PPI图构建
        graph = test_ppi_graph_builder()
        
        # 测试2: LightGCN
        model = test_light_gcn(graph)
        
        # 测试3: 多模态融合
        fusion = test_multimodal_fusion()
        
        # 测试4: 完整流程 + 评估
        metrics = test_full_pipeline()
        
        # 测试5: 基线对比
        compare_baselines()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()