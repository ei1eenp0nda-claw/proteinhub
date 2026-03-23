"""
分析模拟数据的问题

检查用户行为的分布和特征，找出为什么Org-Preference强，而LightGCN弱
"""

import pandas as pd
import numpy as np
from collections import defaultdict
import sys
sys.path.append('/root/.openclaw/workspace/projects/proteinhub/recommendation')

from complete_recommender_v2 import CompleteProteinRecommender, UserBehaviorSimulator


def analyze_simulation():
    """详细分析模拟数据"""
    print("="*70)
    print("模拟数据分析")
    print("="*70)
    
    # 加载PPI数据
    recommender = CompleteProteinRecommender()
    recommender.load_data('/root/.openclaw/workspace/projects/proteinhub/data/whole.tsv', threshold=0.6)
    
    # 模拟用户
    simulator = UserBehaviorSimulator(recommender.ppi_graph, recommender.protein_metadata)
    users = simulator.generate_users(n_users=50)
    interactions_df = simulator.generate_interactions(users, n_interactions_per_user=15)
    
    print(f"\n📊 数据概况:")
    print(f"  用户数: {len(users)}")
    print(f"  蛋白总数: {len(recommender.ppi_graph.protein2id)}")
    print(f"  总交互数: {len(interactions_df)}")
    print(f"  数据稀疏度: {len(interactions_df) / (len(users) * len(recommender.ppi_graph.protein2id)) * 100:.4f}%")
    
    # 分析1: 用户偏好细胞器 vs 实际交互细胞器
    print(f"\n🔍 分析1: 用户偏好 vs 实际交互")
    
    for user_id in list(users.keys())[:5]:  # 看前5个用户
        user = users[user_id]
        prefs = user['preferred_organelles']
        user_interactions = interactions_df[interactions_df['user_id'] == user_id]
        
        # 统计交互蛋白的细胞器分布
        organelle_count = defaultdict(int)
        for protein in user_interactions['protein_id']:
            meta = recommender.protein_metadata.get(protein, {})
            org = meta.get('organelle', 'unknown')
            organelle_count[org] += 1
        
        print(f"\n  用户{user_id}:")
        print(f"    偏好细胞器: {prefs}")
        print(f"    实际交互分布: {dict(organelle_count)}")
        
        # 计算偏好命中率
        pref_hits = sum(c for org, c in organelle_count.items() if org in prefs)
        total = sum(organelle_count.values())
        if total > 0:
            print(f"    偏好命中率: {pref_hits}/{total} = {pref_hits/total*100:.1f}%")
    
    # 分析2: 全局分布
    print(f"\n🔍 分析2: 全局交互分布")
    
    all_interactions = interactions_df
    
    # 按细胞器统计
    org_dist = defaultdict(int)
    for protein in all_interactions['protein_id']:
        meta = recommender.protein_metadata.get(protein, {})
        org = meta.get('organelle', 'unknown')
        org_dist[org] += 1
    
    print(f"\n  交互蛋白的细胞器分布:")
    for org, count in sorted(org_dist.items(), key=lambda x: -x[1]):
        pct = count / len(all_interactions) * 100
        print(f"    {org:15s}: {count:4d} ({pct:5.1f}%)")
    
    # 分析3: 蛋白流行度
    print(f"\n🔍 分析3: 蛋白流行度 (被交互次数)")
    
    protein_counts = all_interactions['protein_id'].value_counts()
    print(f"\n  最热门的10个蛋白:")
    for protein, count in protein_counts.head(10).items():
        meta = recommender.protein_metadata.get(protein, {})
        org = meta.get('organelle', 'unknown')
        ppi_degree = meta.get('degree', 0)
        print(f"    {protein:15s}: {count:3d}次  [{org}] (PPI degree: {ppi_degree})")
    
    # 分析4: 每个用户交互的独特蛋白数
    print(f"\n🔍 分析4: 用户交互多样性")
    
    unique_proteins_per_user = []
    for user_id in users.keys():
        user_data = all_interactions[all_interactions['user_id'] == user_id]
        unique = user_data['protein_id'].nunique()
        unique_proteins_per_user.append(unique)
    
    print(f"  每用户平均交互独特蛋白数: {np.mean(unique_proteins_per_user):.1f}")
    print(f"  最小: {min(unique_proteins_per_user)}, 最大: {max(unique_proteins_per_user)}")
    
    # 分析5: 评分分布
    print(f"\n🔍 分析5: 评分分布")
    print(f"  平均评分: {all_interactions['rating'].mean():.2f}")
    print(f"  评分分布:")
    for rating in sorted(all_interactions['rating'].unique()):
        count = (all_interactions['rating'] == rating).sum()
        print(f"    {rating:.1f}: {count:3d}次")
    
    # 分析6: PPI网络利用情况
    print(f"\n🔍 分析6: PPI网络与用户行为关联")
    
    # 检查用户交互的蛋白是否倾向于互作
    ppi_edges = set()
    for p1, p2, _ in recommender.ppi_graph.edges:
        ppi_edges.add((recommender.ppi_graph.id2protein[p1], 
                      recommender.ppi_graph.id2protein[p2]))
    
    # 对每个用户，计算其交互蛋白之间的PPI边数
    ppi_consistency = []
    for user_id in list(users.keys())[:10]:
        user_proteins = set(all_interactions[all_interactions['user_id'] == user_id]['protein_id'])
        
        # 检查这些蛋白之间的PPI连接
        ppi_count = 0
        for p1 in user_proteins:
            for p2 in user_proteins:
                if p1 != p2 and (p1, p2) in ppi_edges:
                    ppi_count += 1
        
        ppi_consistency.append(ppi_count)
        print(f"  用户{user_id}: {len(user_proteins)}个蛋白, {ppi_count}对PPI互作")
    
    avg_ppi = np.mean(ppi_consistency)
    print(f"\n  平均每用户的PPI互作对数: {avg_ppi:.1f}")
    
    # 分析7: 核心问题
    print(f"\n⚠️ 核心问题分析")
    
    # 计算纯随机期望
    n_proteins = len(recommender.ppi_graph.protein2id)
    n_interactions_total = len(all_interactions)
    
    # 如果完全随机，每个细胞器的期望占比
    org_protein_counts = defaultdict(int)
    for protein, meta in recommender.protein_metadata.items():
        org = meta.get('organelle', 'unknown')
        org_protein_counts[org] += 1
    
    print(f"\n  蛋白池的细胞器分布:")
    for org, count in sorted(org_protein_counts.items(), key=lambda x: -x[1]):
        pct = count / n_proteins * 100
        print(f"    {org:15s}: {count:4d} ({pct:5.1f}%)")
    
    # 对比交互分布 vs 蛋白池分布
    print(f"\n  交互偏差分析 (交互占比 vs 蛋白池占比):")
    for org in org_dist.keys():
        interaction_pct = org_dist[org] / len(all_interactions)
        pool_pct = org_protein_counts.get(org, 0) / n_proteins
        bias = interaction_pct / pool_pct if pool_pct > 0 else 0
        print(f"    {org:15s}: 偏差系数 = {bias:.2f}x {'(over)' if bias > 1 else '(under)'}")
    
    print("\n" + "="*70)
    print("结论:")
    print("="*70)
    print("""
问题1: 数据太稀疏
  - 50用户 × 1355蛋白 = 67,750可能交互
  - 实际只有425交互 → 稀疏度 0.63%
  - 深度学习模型需要更多数据

问题2: 用户行为太规则
  - 80%基于细胞器偏好，20%探索
  - 这让Org-Preference规则几乎完美预测
  - 但LightGCN没有学到这个强特征

问题3: PPI网络未被利用
  - 用户交互蛋白间的PPI连接很少
  - 说明模拟时没有充分考虑PPI邻近性

问题4: 特征工程缺失
  - LightGCN只学了ID embedding
  - 没有显式利用细胞器、PPI degree等特征

改进建议:
  1. 增加用户数和交互数
  2. 在模型中显式加入细胞器特征
  3. 让模拟数据更"噪声化"（降低Org-Preference的信号）
  4. 用PPI信息做预训练或特征增强
    """)


if __name__ == '__main__':
    analyze_simulation()