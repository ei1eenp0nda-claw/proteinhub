"""
PPI推荐系统 - NumPy轻量版 (无需PyTorch)
快速评估用，可以立即运行获取指标
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from collections import defaultdict


class SimplePPIGNN:
    """
    简化版PPI-GNN推荐 (纯NumPy实现)
    
    核心算法:
    1. 在PPI图上进行图卷积传播
    2. 用户-蛋白嵌入内积评分
    """
    
    def __init__(self, embedding_dim: int = 32, n_layers: int = 2):
        self.embedding_dim = embedding_dim
        self.n_layers = n_layers
        self.user_emb = None
        self.item_emb = None
        self.ppi_adj = None
        self.is_fitted = False
    
    def build_ppi_graph(self, ppi_pairs: List[Tuple], n_proteins: int):
        """
        构建PPI邻接矩阵
        
        Args:
            ppi_pairs: [(p1_id, p2_id, weight), ...]
            n_proteins: 蛋白数量
        """
        # 构建对称归一化邻接矩阵
        adj = np.zeros((n_proteins, n_proteins))
        
        for p1, p2, weight in ppi_pairs:
            if p1 < n_proteins and p2 < n_proteins:
                adj[p1, p2] = weight
                adj[p2, p1] = weight
        
        # 添加自环
        adj = adj + np.eye(n_proteins)
        
        # 对称归一化: D^(-1/2) A D^(-1/2)
        degree = np.sum(adj, axis=1)
        degree_inv_sqrt = np.power(degree, -0.5)
        degree_inv_sqrt[np.isinf(degree_inv_sqrt)] = 0
        
        D_inv_sqrt = np.diag(degree_inv_sqrt)
        self.ppi_adj = D_inv_sqrt @ adj @ D_inv_sqrt
        
        print(f"  PPI图构建完成: {n_proteins}节点, {len(ppi_pairs)}边")
    
    def fit(self, interactions: pd.DataFrame, ppi_pairs: List[Tuple] = None):
        """
        训练模型
        
        Args:
            interactions: DataFrame [user_id, item_id, rating]
            ppi_pairs: PPI互作对 (可选)
        """
        print("🔄 训练Simple-PPI-GNN...")
        
        # 构建映射
        self.user2id = {u: i for i, u in enumerate(interactions['user_id'].unique())}
        self.item2id = {i: j for j, i in enumerate(interactions['item_id'].unique())}
        self.id2item = {j: i for i, j in self.item2id.items()}
        
        n_users = len(self.user2id)
        n_items = len(self.item2id)
        
        # 初始化嵌入
        np.random.seed(42)
        self.user_emb = np.random.normal(0, 0.1, (n_users, self.embedding_dim))
        self.item_emb = np.random.normal(0, 0.1, (n_items, self.embedding_dim))
        
        # 构建PPI图
        if ppi_pairs:
            ppi_ids = []
            for p1, p2, w in ppi_pairs:
                if p1 in self.item2id and p2 in self.item2id:
                    ppi_ids.append((self.item2id[p1], self.item2id[p2], w))
            self.build_ppi_graph(ppi_ids, n_items)
        
        # 构建交互矩阵
        interaction_matrix = np.zeros((n_users, n_items))
        for _, row in interactions.iterrows():
            u = self.user2id[row['user_id']]
            i = self.item2id.get(row['item_id'], None)
            if i is not None:
                interaction_matrix[u, i] = row['rating']
        
        # 训练 (简化版BPR)
        lr = 0.01
        reg = 0.001
        
        for epoch in range(100):
            # 采样正样本和负样本
            for u in range(n_users):
                pos_items = np.where(interaction_matrix[u] > 0)[0]
                if len(pos_items) == 0:
                    continue
                
                for i in pos_items:
                    # 采样负样本
                    neg_items = np.where(interaction_matrix[u] == 0)[0]
                    if len(neg_items) == 0:
                        continue
                    j = np.random.choice(neg_items)
                    
                    # BPR损失梯度
                    diff = self.user_emb[u] @ (self.item_emb[i] - self.item_emb[j])
                    sigmoid = 1 / (1 + np.exp(-diff))
                    
                    # 更新
                    grad_u = (1 - sigmoid) * (self.item_emb[i] - self.item_emb[j]) + reg * self.user_emb[u]
                    grad_i = (1 - sigmoid) * self.user_emb[u] + reg * self.item_emb[i]
                    grad_j = -(1 - sigmoid) * self.user_emb[u] + reg * self.item_emb[j]
                    
                    self.user_emb[u] += lr * grad_u
                    self.item_emb[i] += lr * grad_i
                    self.item_emb[j] += lr * grad_j
            
            if (epoch + 1) % 30 == 0:
                # 计算损失
                loss = 0
                for u in range(n_users):
                    pos_items = np.where(interaction_matrix[u] > 0)[0]
                    for i in pos_items:
                        neg_items = np.where(interaction_matrix[u] == 0)[0]
                        if len(neg_items) > 0:
                            j = np.random.choice(neg_items)
                            diff = self.user_emb[u] @ (self.item_emb[i] - self.item_emb[j])
                            loss += -np.log(1 / (1 + np.exp(-diff)))
                print(f"  Epoch {epoch+1}/100, Loss: {loss:.2f}")
        
        # 图卷积传播 (LightGCN风格)
        if self.ppi_adj is not None:
            print("  应用图卷积传播...")
            embeddings = [self.item_emb]
            
            for _ in range(self.n_layers):
                self.item_emb = self.ppi_adj @ self.item_emb
                embeddings.append(self.item_emb)
            
            # 平均各层
            self.item_emb = np.mean(embeddings, axis=0)
        
        self.is_fitted = True
        print("✅ 训练完成")
    
    def recommend(self, user_id: int, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        为用户生成推荐
        
        Returns:
            [(item_id, score), ...]
        """
        if not self.is_fitted:
            raise RuntimeError("模型未训练")
        
        if user_id not in self.user2id:
            # 冷启动: 返回热门
            scores = np.random.random(len(self.item2id))
        else:
            u = self.user2id[user_id]
            scores = self.user_emb[u] @ self.item_emb.T
        
        # Top-K
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        return [(self.id2item[idx], scores[idx]) for idx in top_indices]


class UserSimulator:
    """用户模拟器 (简化版)"""
    
    def __init__(self, user_id: int, user_type: str):
        self.user_id = user_id
        self.user_type = user_type
        
        # 兴趣向量 (20维家族偏好)
        if user_type == 'expert':
            self.interest = np.random.dirichlet(np.ones(20) * 2)
            self.click_bias = 0.12
            self.collect_prob = 0.30
        elif user_type == 'regular':
            self.interest = np.random.dirichlet(np.ones(20))
            self.click_bias = 0.20
            self.collect_prob = 0.15
        else:  # newbie
            self.interest = np.random.dirichlet(np.ones(20) * 0.5)
            self.click_bias = 0.35
            self.collect_prob = 0.05
    
    def respond(self, recs: List[Dict]) -> List[Dict]:
        """模拟用户对推荐的响应"""
        interactions = []
        
        for pos, item in enumerate(recs):
            position_bias = 1.0 / (1 + 0.15 * pos)
            relevance = np.dot(self.interest, item['features'])
            
            click_prob = self.click_bias * position_bias * (0.4 + 0.6 * relevance) * (0.5 + 0.5 * item['quality'])
            
            if np.random.random() < click_prob:
                read_prob = relevance * (0.3 + 0.7 * item['quality'])
                
                if np.random.random() < read_prob:
                    read_time = min(np.random.exponential(120) * (0.5 + relevance), 600)
                    interactions.append({
                        'user_id': self.user_id,
                        'item_id': item['id'],
                        'position': pos,
                        'action': 'deep_read',
                        'read_time': read_time,
                        'liked': np.random.random() < self.click_bias * relevance * item['quality'],
                        'collected': np.random.random() < self.collect_prob * relevance * item['quality'],
                        'relevance': relevance
                    })
                else:
                    interactions.append({
                        'user_id': self.user_id,
                        'item_id': item['id'],
                        'position': pos,
                        'action': 'shallow_read',
                        'read_time': np.random.exponential(20),
                        'liked': False,
                        'collected': False,
                        'relevance': relevance
                    })
            else:
                interactions.append({
                    'user_id': self.user_id,
                    'item_id': item['id'],
                    'position': pos,
                    'action': 'impression',
                    'read_time': 0,
                    'liked': False,
                    'collected': False,
                    'relevance': relevance
                })
        
        return interactions


def run_quick_evaluation():
    """快速评估完整流程"""
    print("="*60)
    print("ProteinHub PPI-GNN 快速评估 (NumPy版)")
    print("="*60)
    
    np.random.seed(42)
    
    # 1. 生成模拟数据
    print("\n📦 生成模拟数据...")
    
    n_proteins = 300
    n_users = 200
    n_ppi = 2000
    
    # 蛋白家族
    families = ['CIDE', 'PLIN', 'ADRP', 'LSDP', 'FITM', 'SEIPIN', 'LIPA', 'DGAT']
    proteins = [f"{f}_{i:03d}" for f in families for i in range(n_proteins // len(families))]
    
    # PPI对
    ppi_pairs = []
    for _ in range(n_ppi):
        if np.random.random() < 0.6:
            family = np.random.choice(families)
            p1 = f"{family}_{np.random.randint(0, n_proteins // len(families)):03d}"
            p2 = f"{family}_{np.random.randint(0, n_proteins // len(families)):03d}"
        else:
            p1, p2 = np.random.choice(proteins, 2, replace=False)
        
        if p1 != p2:
            ppi_pairs.append((p1, p2, np.random.beta(3, 2)))
    
    # 交互数据
    interactions = []
    for u in range(n_users):
        user_type = np.random.choice(['newbie', 'regular', 'expert'], p=[0.3, 0.5, 0.2])
        n_interactions = {'newbie': 10, 'regular': 30, 'expert': 60}[user_type]
        n_interactions = np.random.poisson(n_interactions)
        
        pref_families = np.random.choice(families, size=np.random.randint(1, 4), replace=False)
        
        for _ in range(n_interactions):
            if np.random.random() < 0.7:
                p = f"{np.random.choice(pref_families)}_{np.random.randint(0, 50):03d}"
            else:
                p = np.random.choice(proteins)
            
            interactions.append({
                'user_id': u,
                'item_id': p,
                'rating': np.random.choice([1, 2, 3, 4, 5], p=[0.1, 0.15, 0.3, 0.3, 0.15])
            })
    
    interactions_df = pd.DataFrame(interactions)
    
    print(f"  蛋白数: {len(proteins)}, PPI对: {len(ppi_pairs)}, 交互数: {len(interactions_df)}")
    
    # 2. 训练PPI-GNN
    print("\n🚀 训练PPI-GNN模型...")
    model = SimplePPIGNN(embedding_dim=32, n_layers=2)
    model.fit(interactions_df, ppi_pairs)
    
    # 3. 生成物品特征 (用于模拟) - 使用训练集中的物品
    items = {}
    trained_proteins = list(model.item2id.keys())  # 使用训练集中的蛋白
    for p in trained_proteins:
        items[p] = {
            'id': p,
            'features': np.random.dirichlet(np.ones(20)),
            'quality': np.random.beta(3, 2)
        }
    
    # 4. 创建模拟用户
    print("\n🎲 创建模拟用户...")
    users = []
    for u in range(100):
        utype = np.random.choice(['newbie', 'regular', 'expert'], p=[0.3, 0.5, 0.2])
        users.append(UserSimulator(u, utype))
    
    print(f"  新手: {sum(1 for u in users if u.user_type=='newbie')}, "
          f"普通: {sum(1 for u in users if u.user_type=='regular')}, "
          f"专家: {sum(1 for u in users if u.user_type=='expert')}")
    
    # 5. 运行模拟
    print("\n🧪 运行模拟实验 (5天)...")
    all_logs = []
    
    for day in range(5):
        for user in users:
            n_sessions = np.random.poisson({'newbie': 3, 'regular': 8, 'expert': 12}[user.user_type])
            
            for _ in range(n_sessions):
                recs = model.recommend(user.user_id, top_k=10)
                rec_details = [items[item_id] for item_id, _ in recs]
                
                interactions = user.respond(rec_details)
                for inter in interactions:
                    inter['day'] = day
                    inter['user_type'] = user.user_type
                
                all_logs.extend(interactions)
        
        # 计算当日指标
        day_logs = [l for l in all_logs if l['day'] == day]
        df = pd.DataFrame(day_logs)
        
        ctr = len(df[df['action'] != 'impression']) / len(df) if len(df) > 0 else 0
        collect = df['collected'].mean()
        deep = len(df[df['action'] == 'deep_read']) / len(df[df['action'] != 'impression']) if len(df[df['action'] != 'impression']) > 0 else 0
        
        print(f"  Day {day+1}: CTR={ctr:.3f}, Collect={collect:.3f}, DeepRead={deep:.3f}")
    
    # 6. 计算完整指标
    print("\n📊 计算评估指标...")
    df = pd.DataFrame(all_logs)
    
    # 整体指标
    total = len(df)
    clicks = len(df[df['action'] != 'impression'])
    deep_reads = len(df[df['action'] == 'deep_read'])
    
    metrics = {
        'CTR': clicks / total,
        'Deep_Read_Rate': deep_reads / clicks if clicks > 0 else 0,
        'Like_Rate': df['liked'].mean(),
        'Collect_Rate': df['collected'].mean(),
        'Avg_Read_Time': df[df['read_time'] > 0]['read_time'].mean()
    }
    
    # 分群指标
    segments = {}
    for utype in ['newbie', 'regular', 'expert']:
        tdf = df[df['user_type'] == utype]
        if len(tdf) > 0:
            t_clicks = len(tdf[tdf['action'] != 'impression'])
            segments[utype] = {
                'CTR': t_clicks / len(tdf),
                'Collect_Rate': tdf['collected'].mean(),
                'Deep_Read_Rate': len(tdf[tdf['action'] == 'deep_read']) / t_clicks if t_clicks > 0 else 0
            }
    
    # 打印报告
    print("\n" + "="*60)
    print("评估报告")
    print("="*60)
    
    print("\n📈 在线指标:")
    print(f"  CTR (整体):     {metrics['CTR']:.3f} ({metrics['CTR']*100:.1f}%)")
    print(f"  深度阅读率:     {metrics['Deep_Read_Rate']:.3f}")
    print(f"  点赞率:         {metrics['Like_Rate']:.3f}")
    print(f"  收藏率:         {metrics['Collect_Rate']:.3f}")
    print(f"  平均阅读时长:   {metrics['Avg_Read_Time']:.1f}s")
    
    print("\n👥 用户分群表现:")
    print(f"{'类型':<12} {'CTR':>8} {'收藏率':>8} {'深度阅读':>8}")
    print("-" * 40)
    for utype, m in segments.items():
        print(f"{utype:<12} {m['CTR']:>8.3f} {m['Collect_Rate']:>8.3f} {m['Deep_Read_Rate']:>8.3f}")
    
    # 位置偏置分析
    print("\n📍 位置偏置分析:")
    for pos in [0, 2, 5, 9]:
        pdf = df[df['position'] == pos]
        if len(pdf) > 0:
            ctr = len(pdf[pdf['action'] != 'impression']) / len(pdf)
            print(f"  位置 {pos+1}: CTR={ctr:.3f}")
    
    print("\n" + "="*60)
    
    return metrics


if __name__ == '__main__':
    run_quick_evaluation()