"""
Baseline对比实验

对比方法:
1. Random: 完全随机推荐
2. Popularity: 热门度排序
3. LightGCN (无PPI): 标准双塔，蛋白只用ID embedding
4. LightGCN + PPI (我们的模型): 蛋白塔用PPI图增强

评估指标:
- Recall@K, Precision@K, NDCG@K, MRR, HitRate@K
"""

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import sys
sys.path.append('/root/.openclaw/workspace/projects/proteinhub/recommendation')

from complete_recommender_v2 import (
    CompleteProteinRecommender, ProteinHubEvaluator, 
    UserBehaviorSimulator
)
from ppi_gnn_recommender import PPIGraphBuilder


class BaselineRecommenders:
    """Baseline推荐模型"""
    
    @staticmethod
    def random_recommend(protein_list: list, top_k: int = 10) -> list:
        """随机推荐"""
        candidates = np.random.choice(protein_list, 
                                     size=min(top_k, len(protein_list)), 
                                     replace=False)
        # 随机分数
        scores = np.random.uniform(0, 1, len(candidates))
        return [(p, s) for p, s in zip(candidates, scores)]
    
    @staticmethod
    def popularity_recommend(protein_popularity: dict, top_k: int = 10) -> list:
        """热门度推荐 (按PPI degree排序)"""
        sorted_proteins = sorted(protein_popularity.items(), 
                                key=lambda x: x[1], 
                                reverse=True)
        return [(p, s/50.0) for p, s in sorted_proteins[:top_k]]  # 归一化分数
    
    @staticmethod
    def org_preference_recommend(user_prefs: list, 
                                  protein_metadata: dict,
                                  protein_list: list,
                                  top_k: int = 10) -> list:
        """基于细胞器偏好的简单推荐"""
        candidates = []
        for protein in protein_list:
            meta = protein_metadata.get(protein, {})
            if meta.get('organelle') in user_prefs:
                candidates.append(protein)
        
        # 随机选择偏好的蛋白
        if len(candidates) >= top_k:
            selected = np.random.choice(candidates, size=top_k, replace=False)
        else:
            # 补充随机
            others = [p for p in protein_list if p not in candidates]
            if others:
                n_more = min(top_k - len(candidates), len(others))
                selected = list(candidates) + list(np.random.choice(others, size=n_more, replace=False))
            else:
                selected = candidates
        
        scores = np.random.uniform(0.5, 1.0, len(selected))
        return [(p, s) for p, s in zip(selected, scores)]


class LightGCNBaseline(nn.Module):
    """
    标准LightGCN (无PPI增强)
    
    对比: 看PPI信息带来的提升
    """
    
    def __init__(self, num_users: int, num_items: int, embedding_dim: int = 64):
        super().__init__()
        
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.item_embedding = nn.Embedding(num_items, embedding_dim)
        
        nn.init.xavier_uniform_(self.user_embedding.weight)
        nn.init.xavier_uniform_(self.item_embedding.weight)
    
    def forward(self, user_ids: torch.Tensor, item_ids: torch.Tensor):
        """简单内积"""
        user_vec = self.user_embedding(user_ids)
        item_vec = self.item_embedding(item_ids)
        scores = (user_vec * item_vec).sum(dim=-1)
        return scores, user_vec, item_vec


class BaselineEvaluator:
    """Baseline评估器"""
    
    def __init__(self, protein_list: list, protein_metadata: dict, 
                 protein_popularity: dict):
        self.protein_list = protein_list
        self.protein_metadata = protein_metadata
        self.protein_popularity = protein_popularity
        self.baselines = BaselineRecommenders()
    
    def evaluate_random(self, test_df: pd.DataFrame, top_k: int = 10) -> dict:
        """评估随机推荐"""
        print("\n  评估 Random Baseline...")
        
        recalls, precisions, ndcgs, rrs, hits = [], [], [], [], []
        
        for user_id in test_df['user_id'].unique():
            user_data = test_df[test_df['user_id'] == user_id]
            ground_truth = set(user_data[user_data['rating'] >= 4]['protein_id'].values)
            
            if len(ground_truth) == 0:
                continue
            
            recs = self.baselines.random_recommend(self.protein_list, top_k)
            recommended = [r[0] for r in recs]
            
            metrics = self._calc_metrics(ground_truth, recommended, top_k)
            recalls.append(metrics['recall'])
            precisions.append(metrics['precision'])
            ndcgs.append(metrics['ndcg'])
            rrs.append(metrics['rr'])
            hits.append(metrics['hit'])
        
        return {
            f'Recall@{top_k}': np.mean(recalls),
            f'Precision@{top_k}': np.mean(precisions),
            f'NDCG@{top_k}': np.mean(ndcgs),
            'MRR': np.mean(rrs),
            f'HitRate@{top_k}': np.mean(hits)
        }
    
    def evaluate_popularity(self, test_df: pd.DataFrame, top_k: int = 10) -> dict:
        """评估热门度推荐"""
        print("  评估 Popularity Baseline...")
        
        recalls, precisions, ndcgs, rrs, hits = [], [], [], [], []
        
        for user_id in test_df['user_id'].unique():
            user_data = test_df[test_df['user_id'] == user_id]
            ground_truth = set(user_data[user_data['rating'] >= 4]['protein_id'].values)
            
            if len(ground_truth) == 0:
                continue
            
            recs = self.baselines.popularity_recommend(self.protein_popularity, top_k)
            recommended = [r[0] for r in recs]
            
            metrics = self._calc_metrics(ground_truth, recommended, top_k)
            recalls.append(metrics['recall'])
            precisions.append(metrics['precision'])
            ndcgs.append(metrics['ndcg'])
            rrs.append(metrics['rr'])
            hits.append(metrics['hit'])
        
        return {
            f'Recall@{top_k}': np.mean(recalls),
            f'Precision@{top_k}': np.mean(precisions),
            f'NDCG@{top_k}': np.mean(ndcgs),
            'MRR': np.mean(rrs),
            f'HitRate@{top_k}': np.mean(hits)
        }
    
    def evaluate_org_preference(self, users: dict, test_df: pd.DataFrame, 
                                 top_k: int = 10) -> dict:
        """评估基于细胞器偏好的推荐"""
        print("  评估 Org-Preference Baseline...")
        
        recalls, precisions, ndcgs, rrs, hits = [], [], [], [], []
        
        for user_id in test_df['user_id'].unique():
            user_data = test_df[test_df['user_id'] == user_id]
            ground_truth = set(user_data[user_data['rating'] >= 4]['protein_id'].values)
            
            if len(ground_truth) == 0:
                continue
            
            user_profile = users.get(user_id, {})
            prefs = user_profile.get('preferred_organelles', [])
            
            recs = self.baselines.org_preference_recommend(
                prefs, self.protein_metadata, self.protein_list, top_k
            )
            recommended = [r[0] for r in recs]
            
            metrics = self._calc_metrics(ground_truth, recommended, top_k)
            recalls.append(metrics['recall'])
            precisions.append(metrics['precision'])
            ndcgs.append(metrics['ndcg'])
            rrs.append(metrics['rr'])
            hits.append(metrics['hit'])
        
        return {
            f'Recall@{top_k}': np.mean(recalls),
            f'Precision@{top_k}': np.mean(precisions),
            f'NDCG@{top_k}': np.mean(ndcgs),
            'MRR': np.mean(rrs),
            f'HitRate@{top_k}': np.mean(hits)
        }
    
    def evaluate_standard_lightgcn(self, train_df: pd.DataFrame, test_df: pd.DataFrame,
                                   top_k: int = 10, epochs: int = 30) -> dict:
        """评估标准LightGCN (无PPI)"""
        print("  评估 Standard LightGCN (无PPI)...")
        
        # 构建映射
        user2id = {u: i for i, u in enumerate(train_df['user_id'].unique())}
        protein2id = {p: i for i, p in enumerate(sorted(train_df['protein_id'].unique()))}
        id2protein = {v: k for k, v in protein2id.items()}
        
        num_users = len(user2id)
        num_items = len(protein2id)
        
        # 训练
        model = LightGCNBaseline(num_users, num_items, embedding_dim=64)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        
        user_ids = torch.tensor([user2id[u] for u in train_df['user_id']], dtype=torch.long)
        item_ids = torch.tensor([protein2id.get(p, 0) for p in train_df['protein_id']], dtype=torch.long)
        ratings = torch.tensor(train_df['rating'].values / 5.0, dtype=torch.float)
        
        model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            scores, _, _ = model(user_ids, item_ids)
            loss = nn.functional.mse_loss(scores, ratings)
            loss.backward()
            optimizer.step()
        
        # 评估
        model.eval()
        recalls, precisions, ndcgs, rrs, hits = [], [], [], [], []
        
        with torch.no_grad():
            for user_id in test_df['user_id'].unique():
                user_data = test_df[test_df['user_id'] == user_id]
                ground_truth = set(user_data[user_data['rating'] >= 4]['protein_id'].values)
                
                if len(ground_truth) == 0:
                    continue
                
                if user_id not in user2id:
                    continue
                
                user_idx = user2id[user_id]
                user_tensor = torch.tensor([user_idx] * num_items, dtype=torch.long)
                item_tensor = torch.arange(num_items, dtype=torch.long)
                
                scores, _, _ = model(user_tensor, item_tensor)
                top_scores, top_indices = torch.topk(scores, top_k)
                
                recommended = [id2protein[idx.item()] for idx in top_indices]
                
                metrics = self._calc_metrics(ground_truth, recommended, top_k)
                recalls.append(metrics['recall'])
                precisions.append(metrics['precision'])
                ndcgs.append(metrics['ndcg'])
                rrs.append(metrics['rr'])
                hits.append(metrics['hit'])
        
        return {
            f'Recall@{top_k}': np.mean(recalls),
            f'Precision@{top_k}': np.mean(precisions),
            f'NDCG@{top_k}': np.mean(ndcgs),
            'MRR': np.mean(rrs),
            f'HitRate@{top_k}': np.mean(hits)
        }
    
    def _calc_metrics(self, ground_truth: set, recommended: list, top_k: int) -> dict:
        """计算指标"""
        hits = len(ground_truth & set(recommended))
        
        recall = hits / len(ground_truth)
        precision = hits / top_k
        
        # NDCG
        dcg = 0
        for i, item in enumerate(recommended):
            if item in ground_truth:
                dcg += 1 / np.log2(i + 2)
        
        ideal_hits = min(len(ground_truth), top_k)
        idcg = sum(1 / np.log2(i + 2) for i in range(ideal_hits))
        ndcg = dcg / idcg if idcg > 0 else 0
        
        # MRR
        rr = 0
        for i, item in enumerate(recommended):
            if item in ground_truth:
                rr = 1 / (i + 1)
                break
        
        hit = 1 if hits > 0 else 0
        
        return {
            'recall': recall,
            'precision': precision,
            'ndcg': ndcg,
            'rr': rr,
            'hit': hit
        }


def run_comparison():
    """运行对比实验"""
    print("="*70)
    print("ProteinHub Baseline 对比实验")
    print("="*70)
    
    # 1. 加载PPI数据
    print("\n📚 加载PPI数据...")
    recommender = CompleteProteinRecommender(embedding_dim=64, device='cpu')
    recommender.load_data('/root/.openclaw/workspace/projects/proteinhub/data/whole.tsv', threshold=0.6)
    
    # 2. 模拟用户行为
    print("\n👥 模拟用户行为...")
    simulator = UserBehaviorSimulator(recommender.ppi_graph, recommender.protein_metadata)
    users = simulator.generate_users(n_users=50)
    interactions_df = simulator.generate_interactions(users, n_interactions_per_user=15)
    
    train_df = interactions_df.sample(frac=0.8, random_state=42)
    test_df = interactions_df.drop(train_df.index)
    
    print(f"  训练集: {len(train_df)}, 测试集: {len(test_df)}")
    
    # 准备baseline数据
    protein_list = list(recommender.ppi_graph.protein2id.keys())
    protein_popularity = {p: m['degree'] for p, m in recommender.protein_metadata.items()}
    
    # 3. 评估所有方法
    print("\n📊 评估各方法...")
    baseline_eval = BaselineEvaluator(protein_list, recommender.protein_metadata, protein_popularity)
    
    results = {}
    
    # Baseline 1: Random
    results['Random'] = baseline_eval.evaluate_random(test_df, top_k=10)
    
    # Baseline 2: Popularity
    results['Popularity'] = baseline_eval.evaluate_popularity(test_df, top_k=10)
    
    # Baseline 3: Org-Preference
    results['Org-Preference'] = baseline_eval.evaluate_org_preference(users, test_df, top_k=10)
    
    # Baseline 4: Standard LightGCN (无PPI)
    results['LightGCN (无PPI)'] = baseline_eval.evaluate_standard_lightgcn(
        train_df, test_df, top_k=10, epochs=30
    )
    
    # Our Method: LightGCN + PPI
    print("  评估 LightGCN + PPI (我们的方法)...")
    recommender.simulate_and_train(n_users=50, interactions_per_user=15, epochs=30)
    
    evaluator = ProteinHubEvaluator()
    results['LightGCN + PPI (Ours)'] = evaluator.evaluate(recommender, test_df, top_k=10)
    
    # 4. 打印对比结果
    print("\n" + "="*70)
    print("对比结果 (Top-10)")
    print("="*70)
    
    metrics = ['Recall@10', 'Precision@10', 'NDCG@10', 'MRR', 'HitRate@10']
    
    # 表头
    header = f"{'Method':<25}"
    for m in metrics:
        header += f"{m:<12}"
    print(header)
    print("-" * 70)
    
    # 各方法结果
    for method, scores in results.items():
        row = f"{method:<25}"
        for m in metrics:
            val = scores.get(m, 0)
            row += f"{val:<12.4f}"
        print(row)
    
    # 5. 提升分析
    print("\n" + "="*70)
    print("相对提升 (vs Random)")
    print("="*70)
    
    random_scores = results['Random']
    our_scores = results['LightGCN + PPI (Ours)']
    
    for m in metrics:
        base = random_scores[m]
        ours = our_scores[m]
        if base > 0:
            lift = (ours - base) / base * 100
            print(f"  {m}: {lift:+.1f}%")
        else:
            print(f"  {m}: N/A")
    
    print("\n✅ 对比实验完成!")
    
    return results


if __name__ == '__main__':
    run_comparison()