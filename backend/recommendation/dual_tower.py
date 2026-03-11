"""
ProteinHub Recommendation Engine
双塔召回推荐算法实现

架构：
- 用户塔 (User Tower): 编码用户兴趣
- 物品塔 (Item Tower): 编码蛋白/帖子特征
- 召回层: 向量相似度检索
- 精排层: 浅层模型重排序
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import json
import os


class DualTowerRecommender:
    """
    双塔推荐模型
    
    用户塔输入：用户ID、关注的蛋白、互动历史
    物品塔输入：蛋白ID、名称、描述、家族
    输出：个性化推荐列表
    """
    
    def __init__(self, embedding_dim=64):
        """
        初始化双塔模型
        
        Args:
            embedding_dim: 向量维度
        """
        self.embedding_dim = embedding_dim
        
        # 用户塔参数（简化为嵌入表）
        self.user_embeddings = {}  # user_id -> vector
        
        # 物品塔参数
        self.item_embeddings = {}  # protein_id -> vector
        self.item_text_vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        
        # 特征维度
        self.n_families = 0  # 蛋白家族数量
        self.family_to_idx = {}
        
        # 模型状态
        self.is_fitted = False
        
    def _build_family_mapping(self, proteins):
        """构建蛋白家族到索引的映射"""
        families = set(p.family for p in proteins if p.family)
        self.family_to_idx = {f: i for i, f in enumerate(sorted(families))}
        self.n_families = len(families)
        
    def _item_tower(self, protein, text_features=None):
        """
        物品塔：将蛋白编码为向量
        
        Args:
            protein: Protein对象
            text_features: 预计算的文本特征
            
        Returns:
            np.ndarray: 蛋白嵌入向量
        """
        features = []
        
        # 1. 家族独热编码
        family_vec = np.zeros(self.n_families)
        if protein.family and protein.family in self.family_to_idx:
            family_vec[self.family_to_idx[protein.family]] = 1
        features.extend(family_vec)
        
        # 2. 名称TF-IDF特征（简化为字符n-gram统计）
        if text_features is not None:
            features.extend(text_features)
        else:
            # 简单的字符特征
            name = protein.name.lower() if protein.name else ''
            char_features = self._extract_char_features(name)
            features.extend(char_features)
        
        # 3. 描述长度（归一化）
        desc_len = len(protein.description) if protein.description else 0
        features.append(min(desc_len / 1000, 1.0))  # 归一化到0-1
        
        # 4. 填充到指定维度
        while len(features) < self.embedding_dim:
            features.append(0.0)
        
        # 截断或填充到embedding_dim
        vector = np.array(features[:self.embedding_dim])
        
        # L2归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector
    
    def _extract_char_features(self, text, max_len=50):
        """提取字符级特征"""
        features = []
        # 字母频率
        for char in 'abcdefghijklmnopqrstuvwxyz':
            features.append(text.count(char) / max(len(text), 1))
        # 数字频率
        digit_count = sum(c.isdigit() for c in text)
        features.append(digit_count / max(len(text), 1))
        # 长度特征
        features.append(min(len(text) / max_len, 1.0))
        return features
    
    def _user_tower(self, user, user_interactions, user_follows):
        """
        用户塔：将用户编码为向量
        
        Args:
            user: User对象
            user_interactions: 用户互动历史
            user_follows: 用户关注的蛋白列表
            
        Returns:
            np.ndarray: 用户嵌入向量
        """
        features = []
        
        # 1. 关注的蛋白家族分布
        family_vec = np.zeros(self.n_families)
        for protein in user_follows:
            if protein.family and protein.family in self.family_to_idx:
                family_vec[self.family_to_idx[protein.family]] += 1
        
        # 归一化
        if np.sum(family_vec) > 0:
            family_vec = family_vec / np.sum(family_vec)
        features.extend(family_vec)
        
        # 2. 互动历史特征（简化）
        n_interactions = len(user_interactions) if user_interactions else 0
        features.append(min(n_interactions / 100, 1.0))  # 活跃度
        
        # 3. 注册时间特征
        from datetime import datetime
        if user.created_at:
            days_since_reg = (datetime.utcnow() - user.created_at).days
            features.append(min(days_since_reg / 365, 1.0))  # 账户年龄（年）
        else:
            features.append(0.0)
        
        # 4. 填充到指定维度
        while len(features) < self.embedding_dim:
            features.append(0.0)
        
        vector = np.array(features[:self.embedding_dim])
        
        # L2归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector
    
    def fit(self, proteins, users_data=None):
        """
        训练/初始化模型
        
        Args:
            proteins: 蛋白列表
            users_data: 用户数据（可选，用于冷启动）
        """
        print(f"🔄 初始化双塔模型...")
        
        # 构建家族映射
        self._build_family_mapping(proteins)
        print(f"   蛋白家族数量: {self.n_families}")
        
        # 预计算所有蛋白的嵌入
        self.item_embeddings = {}
        for protein in proteins:
            self.item_embeddings[protein.id] = self._item_tower(protein)
        
        print(f"   预计算蛋白嵌入: {len(self.item_embeddings)} 个")
        
        self.is_fitted = True
        print("✅ 双塔模型初始化完成")
        
    def get_user_embedding(self, user, user_follows):
        """
        获取用户嵌入向量
        
        Args:
            user: User对象
            user_follows: 关注的蛋白列表
            
        Returns:
            np.ndarray: 用户嵌入向量
        """
        if user.id in self.user_embeddings:
            return self.user_embeddings[user.id]
        
        # 冷启动用户：基于关注计算
        vector = self._user_tower(user, [], user_follows)
        self.user_embeddings[user.id] = vector
        return vector
    
    def recommend(self, user, user_follows, top_k=20, exclude_ids=None):
        """
        为用户推荐蛋白/内容
        
        Args:
            user: User对象
            user_follows: 用户关注的蛋白
            top_k: 推荐数量
            exclude_ids: 需要排除的蛋白ID
            
        Returns:
            list: [(protein_id, score), ...] 推荐列表
        """
        if not self.is_fitted:
            raise RuntimeError("模型未初始化，请先调用 fit()")
        
        exclude_ids = set(exclude_ids or [])
        exclude_ids.update(p.id for p in user_follows)  # 排除已关注的
        
        # 获取用户向量
        user_vec = self.get_user_embedding(user, user_follows)
        
        # 计算与所有物品的相似度
        scores = []
        for protein_id, item_vec in self.item_embeddings.items():
            if protein_id in exclude_ids:
                continue
            
            # 余弦相似度
            similarity = np.dot(user_vec, item_vec)
            scores.append((protein_id, similarity))
        
        # 按相似度排序，返回top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def recommend_for_new_user(self, selected_families, top_k=20):
        """
        为新用户推荐（冷启动）
        
        基于用户选择的感兴趣的家族推荐
        
        Args:
            selected_families: 用户选择的感兴趣的家族列表
            top_k: 推荐数量
            
        Returns:
            list: [(protein_id, score), ...]
        """
        if not self.is_fitted:
            raise RuntimeError("模型未初始化")
        
        # 构建临时用户向量
        family_vec = np.zeros(self.n_families)
        for family in selected_families:
            if family in self.family_to_idx:
                family_vec[self.family_to_idx[family]] = 1.0
        
        # 填充到完整维度
        temp_user_vec = np.zeros(self.embedding_dim)
        temp_user_vec[:len(family_vec)] = family_vec
        
        # L2归一化
        norm = np.linalg.norm(temp_user_vec)
        if norm > 0:
            temp_user_vec = temp_user_vec / norm
        
        # 计算相似度
        scores = []
        for protein_id, item_vec in self.item_embeddings.items():
            similarity = np.dot(temp_user_vec, item_vec)
            scores.append((protein_id, similarity))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def save(self, filepath):
        """保存模型"""
        data = {
            'embedding_dim': self.embedding_dim,
            'n_families': self.n_families,
            'family_to_idx': self.family_to_idx,
            'item_embeddings': {k: v.tolist() for k, v in self.item_embeddings.items()},
            'user_embeddings': {k: v.tolist() for k, v in self.user_embeddings.items()},
            'is_fitted': self.is_fitted
        }
        with open(filepath, 'w') as f:
            json.dump(data, f)
    
    @classmethod
    def load(cls, filepath):
        """加载模型"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        model = cls(embedding_dim=data['embedding_dim'])
        model.n_families = data['n_families']
        model.family_to_idx = data['family_to_idx']
        model.item_embeddings = {int(k): np.array(v) for k, v in data['item_embeddings'].items()}
        model.user_embeddings = {int(k): np.array(v) for k, v in data['user_embeddings'].items()}
        model.is_fitted = data['is_fitted']
        
        return model


class SimpleRecommender:
    """
    简化版推荐器（用于MVP）
    
    基于规则的推荐：
    1. 同家族推荐
    2. 热门推荐
    3. 随机探索
    """
    
    @staticmethod
    def recommend_by_family(protein_id, proteins, top_k=5):
        """基于同家族推荐"""
        target = next((p for p in proteins if p.id == protein_id), None)
        if not target or not target.family:
            return []
        
        same_family = [p for p in proteins 
                      if p.family == target.family and p.id != protein_id]
        
        # 随机选择top_k个
        import random
        if len(same_family) > top_k:
            same_family = random.sample(same_family, top_k)
        
        return [(p.id, 1.0) for p in same_family]
    
    @staticmethod
    def recommend_popular(proteins, top_k=10):
        """热门推荐（MVP：随机）"""
        import random
        selected = random.sample(proteins, min(top_k, len(proteins)))
        return [(p.id, 1.0) for p in selected]
    
    @staticmethod
    def recommend_explore(proteins, top_k=5):
        """探索推荐（不同家族）"""
        import random
        families = set(p.family for p in proteins if p.family)
        
        results = []
        for family in random.sample(list(families), min(top_k, len(families))):
            family_proteins = [p for p in proteins if p.family == family]
            if family_proteins:
                results.append((random.choice(family_proteins).id, 0.8))
        
        return results
