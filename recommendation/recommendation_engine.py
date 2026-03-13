"""
ProteinHub Recommendation System - Recommendation Engine
推荐算法实现：协同过滤、内容推荐、混合推荐
"""
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
import json
import warnings
warnings.filterwarnings('ignore')

class CollaborativeFiltering:
    """协同过滤推荐"""
    
    def __init__(self, n_factors=50):
        self.n_factors = n_factors
        self.user_item_matrix = None
        self.user_factors = None
        self.item_factors = None
        self.user_id_map = {}
        self.item_id_map = {}
        self.reverse_user_map = {}
        self.reverse_item_map = {}
        
    def fit(self, interactions_df, user_col='user_id', item_col='note_id', rating_col='rating'):
        """训练协同过滤模型"""
        
        # 创建ID映射
        unique_users = interactions_df[user_col].unique()
        unique_items = interactions_df[item_col].unique()
        
        self.user_id_map = {uid: i for i, uid in enumerate(unique_users)}
        self.item_id_map = {iid: i for i, iid in enumerate(unique_items)}
        self.reverse_user_map = {i: uid for uid, i in self.user_id_map.items()}
        self.reverse_item_map = {i: iid for iid, i in self.item_id_map.items()}
        
        # 创建用户-物品矩阵
        rows = interactions_df[user_col].map(self.user_id_map)
        cols = interactions_df[item_col].map(self.item_id_map)
        
        # 使用隐式反馈（浏览=1，点赞=2，收藏=3）
        if rating_col not in interactions_df.columns:
            ratings = np.ones(len(interactions_df))
        else:
            ratings = interactions_df[rating_col].values
        
        self.user_item_matrix = csr_matrix(
            (ratings, (rows, cols)),
            shape=(len(unique_users), len(unique_items))
        )
        
        # 矩阵分解 (SVD)
        self._fit_svd()
        
        return self
    
    def _fit_svd(self):
        """使用SVD进行矩阵分解"""
        # 使用随机SVD以提高效率
        svd = TruncatedSVD(n_components=self.n_factors, random_state=42)
        self.user_factors = svd.fit_transform(self.user_item_matrix)
        self.item_factors = svd.components_.T
        self.svd_explained_variance = svd.explained_variance_ratio_.sum()
        
    def recommend(self, user_id, n_recommendations=10, exclude_seen=True):
        """为用户生成推荐"""
        
        if user_id not in self.user_id_map:
            return []
        
        user_idx = self.user_id_map[user_id]
        
        # 计算用户对所有物品的预测评分
        scores = np.dot(self.user_factors[user_idx], self.item_factors.T)
        
        # 排除已交互的物品
        if exclude_seen:
            seen_items = self.user_item_matrix[user_idx].nonzero()[1]
            scores[seen_items] = -np.inf
        
        # 获取Top-K推荐
        top_indices = np.argsort(scores)[::-1][:n_recommendations]
        recommendations = [
            (self.reverse_item_map[idx], scores[idx])
            for idx in top_indices if scores[idx] > -np.inf
        ]
        
        return recommendations
    
    def get_similar_items(self, item_id, n_similar=10):
        """获取相似物品"""
        
        if item_id not in self.item_id_map:
            return []
        
        item_idx = self.item_id_map[item_id]
        item_vector = self.item_factors[item_idx].reshape(1, -1)
        
        # 计算余弦相似度
        similarities = cosine_similarity(item_vector, self.item_factors)[0]
        
        # 排除自身
        similarities[item_idx] = -1
        
        # 获取最相似的物品
        similar_indices = np.argsort(similarities)[::-1][:n_similar]
        similar_items = [
            (self.reverse_item_map[idx], similarities[idx])
            for idx in similar_indices
        ]
        
        return similar_items


class ContentBasedRecommender:
    """基于内容的推荐"""
    
    def __init__(self):
        self.item_features = None
        self.item_ids = None
        self.similarity_matrix = None
        
    def fit(self, features_df, item_col='note_id', feature_cols=None):
        """训练内容推荐模型"""
        
        self.item_ids = features_df[item_col].values
        
        if feature_cols is None:
            # 自动选择数值特征列
            feature_cols = features_df.select_dtypes(include=[np.number]).columns.tolist()
            feature_cols = [c for c in feature_cols if c != item_col]
        
        # 提取特征
        self.item_features = features_df[feature_cols].values
        
        # 归一化
        norms = np.linalg.norm(self.item_features, axis=1, keepdims=True)
        norms[norms == 0] = 1
        self.item_features = self.item_features / norms
        
        # 预计算相似度矩阵
        self.similarity_matrix = cosine_similarity(self.item_features)
        
        # 创建ID到索引的映射
        self.item_id_to_idx = {item_id: i for i, item_id in enumerate(self.item_ids)}
        
        return self
    
    def recommend(self, user_history, n_recommendations=10):
        """基于用户历史推荐"""
        
        if not user_history:
            return []
        
        # 计算用户画像（基于历史物品的平均特征）
        user_profile = np.zeros(self.item_features.shape[1])
        valid_items = 0
        
        for item_id in user_history:
            if item_id in self.item_id_to_idx:
                idx = self.item_id_to_idx[item_id]
                user_profile += self.item_features[idx]
                valid_items += 1
        
        if valid_items == 0:
            return []
        
        user_profile /= valid_items
        
        # 计算用户画像与所有物品的相似度
        scores = cosine_similarity(user_profile.reshape(1, -1), self.item_features)[0]
        
        # 排除已浏览的物品
        for item_id in user_history:
            if item_id in self.item_id_to_idx:
                scores[self.item_id_to_idx[item_id]] = -1
        
        # 获取Top-K推荐
        top_indices = np.argsort(scores)[::-1][:n_recommendations]
        recommendations = [
            (self.item_ids[idx], scores[idx])
            for idx in top_indices if scores[idx] > -1
        ]
        
        return recommendations
    
    def get_similar_items(self, item_id, n_similar=10):
        """获取相似物品"""
        
        if item_id not in self.item_id_to_idx:
            return []
        
        idx = self.item_id_to_idx[item_id]
        similarities = self.similarity_matrix[idx].copy()
        similarities[idx] = -1  # 排除自身
        
        similar_indices = np.argsort(similarities)[::-1][:n_similar]
        similar_items = [
            (self.item_ids[i], similarities[i])
            for i in similar_indices
        ]
        
        return similar_items


class HybridRecommender:
    """混合推荐系统"""
    
    def __init__(self, cf_weight=0.5, cb_weight=0.5, exploration_rate=0.1):
        self.cf_weight = cf_weight
        self.cb_weight = cb_weight
        self.exploration_rate = exploration_rate
        self.cf_model = None
        self.cb_model = None
        self.popularity_ranking = None
        
    def fit(self, interactions_df, features_df, user_col='user_id', item_col='note_id'):
        """训练混合推荐模型"""
        
        # 训练协同过滤模型
        self.cf_model = CollaborativeFiltering(n_factors=50)
        self.cf_model.fit(interactions_df, user_col, item_col)
        
        # 训练内容推荐模型
        self.cb_model = ContentBasedRecommender()
        self.cb_model.fit(features_df, item_col)
        
        # 计算热门度排名（用于冷启动和探索）
        item_counts = interactions_df[item_col].value_counts()
        self.popularity_ranking = item_counts.index.tolist()
        
        return self
    
    def recommend(self, user_id, user_history=None, n_recommendations=10, 
                  cold_start=False, diversity_boost=True):
        """生成混合推荐"""
        
        # 冷启动处理
        if cold_start or user_id not in self.cf_model.user_id_map:
            return self._cold_start_recommend(n_recommendations)
        
        # 获取协同过滤推荐
        cf_recs = self.cf_model.recommend(user_id, n_recommendations * 2, exclude_seen=True)
        cf_dict = {item_id: score for item_id, score in cf_recs}
        
        # 获取内容推荐
        if user_history is None:
            # 从CF模型获取用户历史
            user_idx = self.cf_model.user_id_map[user_id]
            seen_indices = self.cf_model.user_item_matrix[user_idx].nonzero()[1]
            user_history = [self.cf_model.reverse_item_map[idx] for idx in seen_indices]
        
        cb_recs = self.cb_model.recommend(user_history, n_recommendations * 2)
        cb_dict = {item_id: score for item_id, score in cb_recs}
        
        # 加权融合
        all_items = set(cf_dict.keys()) | set(cb_dict.keys())
        fused_scores = {}
        
        for item_id in all_items:
            cf_score = cf_dict.get(item_id, 0)
            cb_score = cb_dict.get(item_id, 0)
            
            # 加权融合
            fused_score = self.cf_weight * cf_score + self.cb_weight * cb_score
            
            # 多样性增强：降低与历史物品相似的物品的分数
            if diversity_boost and user_history:
                max_sim = 0
                for hist_item in user_history[:10]:  # 只考虑最近10个
                    sim_items = self.cb_model.get_similar_items(hist_item, 5)
                    if any(s[0] == item_id for s in sim_items):
                        max_sim = max(max_sim, next(s[1] for s in sim_items if s[0] == item_id))
                
                # 惩罚高度相似的物品
                fused_score *= (1 - 0.3 * max_sim)
            
            fused_scores[item_id] = fused_score
        
        # 添加探索（随机推荐热门物品）
        n_explore = int(n_recommendations * self.exploration_rate)
        n_exploit = n_recommendations - n_explore
        
        # 按分数排序
        sorted_items = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 选择exploit推荐
        exploit_recs = sorted_items[:n_exploit]
        
        # 随机选择explore推荐
        explore_candidates = [item for item in self.popularity_ranking 
                             if item not in dict(exploit_recs)]
        explore_recs = [(item, 0.5) for item in 
                       np.random.choice(explore_candidates, min(n_explore, len(explore_candidates)), replace=False)]
        
        return exploit_recs + explore_recs
    
    def _cold_start_recommend(self, n_recommendations):
        """冷启动推荐：返回热门物品"""
        return [(item, 0.5) for item in self.popularity_ranking[:n_recommendations]]


class MultiArmedBandit:
    """多臂老虎机推荐（用于探索-利用平衡）"""
    
    def __init__(self, n_items, epsilon=0.1):
        self.n_items = n_items
        self.epsilon = epsilon
        self.counts = np.zeros(n_items)
        self.values = np.zeros(n_items)
        
    def select(self, n_selections=10):
        """选择物品"""
        selections = []
        
        for _ in range(n_selections):
            if np.random.random() < self.epsilon:
                # 探索：随机选择
                choice = np.random.randint(0, self.n_items)
            else:
                # 利用：选择价值最高的
                choice = np.argmax(self.values)
            
            selections.append(choice)
        
        return selections
    
    def update(self, item_idx, reward):
        """更新物品价值估计"""
        self.counts[item_idx] += 1
        n = self.counts[item_idx]
        value = self.values[item_idx]
        
        # 增量更新平均值
        self.values[item_idx] = ((n - 1) / n) * value + (1 / n) * reward


if __name__ == '__main__':
    print("Recommendation Engine loaded successfully")
    print("Available algorithms:")
    print("- CollaborativeFiltering: 协同过滤")
    print("- ContentBasedRecommender: 内容推荐")
    print("- HybridRecommender: 混合推荐")
    print("- MultiArmedBandit: 多臂老虎机")
