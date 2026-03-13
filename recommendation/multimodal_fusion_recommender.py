"""
Multimodal Fusion Recommendation System for ProteinHub
基于用户兴趣的多模态融合推荐

核心思想：
1. 构建用户兴趣画像（基于行为）
2. 多模态内容编码（图+内容+行为）
3. 融合匹配推荐
"""

import numpy as np
import pandas as pd
from collections import defaultdict
import json
import random
from typing import List, Dict, Tuple

# 设置随机种子
np.random.seed(42)
random.seed(42)


class UserInterestProfile:
    """用户兴趣画像模型"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.interested_proteins = set()  # 感兴趣的蛋白
        self.interested_tags = defaultdict(float)  # 标签权重
        self.read_notes = set()  # 阅读历史
        self.liked_notes = set()  # 点赞历史
        self.favorited_notes = set()  # 收藏历史
        self.protein_weights = defaultdict(float)  # 蛋白兴趣权重
        
    def update_from_behavior(self, note_id: int, proteins: List[str], 
                            tags: List[str], action: str = 'view'):
        """根据行为更新兴趣画像"""
        
        # 记录阅读
        self.read_notes.add(note_id)
        
        # 更新蛋白兴趣权重
        weight_map = {'view': 0.5, 'like': 2.0, 'favorite': 3.0, 'comment': 2.5}
        weight = weight_map.get(action, 0.5)
        
        for protein in proteins:
            self.interested_proteins.add(protein)
            self.protein_weights[protein] += weight
            
        # 更新标签权重
        for tag in tags:
            self.interested_tags[tag] += weight
            
        if action == 'like':
            self.liked_notes.add(note_id)
        elif action == 'favorite':
            self.favorited_notes.add(note_id)
            
    def get_top_proteins(self, k: int = 5) -> List[Tuple[str, float]]:
        """获取用户最感兴趣的蛋白"""
        sorted_proteins = sorted(self.protein_weights.items(), 
                                key=lambda x: x[1], reverse=True)
        return sorted_proteins[:k]
        
    def get_top_tags(self, k: int = 5) -> List[Tuple[str, float]]:
        """获取用户最感兴趣的标签"""
        sorted_tags = sorted(self.interested_tags.items(),
                           key=lambda x: x[1], reverse=True)
        return sorted_tags[:k]


class MultimodalFusionRecommender:
    """多模态融合推荐器（以用户兴趣为中心）"""
    
    def __init__(self, ppi_threshold: float = 0.6):
        self.ppi_threshold = ppi_threshold
        self.ppi_graph = defaultdict(list)  # 蛋白互作图
        self.note_features = {}  # 笔记特征缓存
        self.user_profiles = {}  # 用户画像缓存
        self.protein_embeddings = {}  # 蛋白嵌入向量
        self.note_content_embeddings = {}  # 笔记内容嵌入
        
        # 模态权重（可学习）
        self.modality_weights = {
            'graph': 0.3,      # PPI网络
            'content': 0.4,    # 内容相似
            'behavior': 0.3    # 行为匹配
        }
        
    def load_ppi_data(self, ppi_pairs: List[Tuple[str, str, float]]):
        """加载PPI互作数据"""
        for protein_a, protein_b, score in ppi_pairs:
            if score >= self.ppi_threshold:
                self.ppi_graph[protein_a].append((protein_b, score))
                self.ppi_graph[protein_b].append((protein_a, score))
                
    def build_protein_embeddings(self, dim: int = 64):
        """构建蛋白Node2Vec嵌入（简化版随机游走）"""
        all_proteins = set(self.ppi_graph.keys())
        
        for protein in all_proteins:
            # 基于邻居构建嵌入
            neighbors = self.ppi_graph[protein]
            if neighbors:
                # 使用邻居得分的加权平均
                weights = [score for _, score in neighbors]
                total_weight = sum(weights)
                # 生成基于图结构的嵌入
                embedding = np.random.randn(dim)
                # 根据连接数调整
                connection_strength = len(neighbors) / 10.0
                embedding *= (1 + connection_strength)
            else:
                embedding = np.random.randn(dim) * 0.1
                
            self.protein_embeddings[protein] = embedding
            
    def build_note_features(self, notes_data: List[Dict]):
        """构建笔记多模态特征"""
        for note in notes_data:
            note_id = note['note_id']
            proteins = note.get('proteins', [])
            tags = note.get('tags', [])
            
            # 1. 图表征：蛋白嵌入的平均
            graph_feature = self._compute_graph_feature(proteins)
            
            # 2. 内容表征：标签one-hot + TF-IDF模拟
            content_feature = self._compute_content_feature(tags, note.get('text', ''))
            
            # 3. 统计特征
            stats_feature = np.array([
                note.get('like_count', 0) / 100.0,
                note.get('favorite_count', 0) / 50.0,
                note.get('comment_count', 0) / 20.0,
                note.get('citation_count', 0) / 1000.0
            ])
            
            self.note_features[note_id] = {
                'graph': graph_feature,      # 64d
                'content': content_feature,  # 32d
                'stats': stats_feature,      # 4d
                'proteins': proteins,
                'tags': tags
            }
            
    def _compute_graph_feature(self, proteins: List[str]) -> np.ndarray:
        """计算笔记的图表征（蛋白嵌入平均）"""
        embeddings = []
        for protein in proteins:
            if protein in self.protein_embeddings:
                embeddings.append(self.protein_embeddings[protein])
                
        if embeddings:
            return np.mean(embeddings, axis=0)  # 64d
        return np.zeros(64)
        
    def _compute_content_feature(self, tags: List[str], text: str) -> np.ndarray:
        """计算笔记的内容表征（简化版）"""
        # 模拟TF-IDF：基于标签的one-hot风格
        feature = np.zeros(32)
        
        # 标签权重
        tag_weights = {
            '脂滴': 1.0, '代谢': 0.9, '脂肪': 0.9,
            'CIDEA': 0.8, 'FSP27': 0.8, 'ATGL': 0.8,
            '肥胖': 0.7, '糖尿病': 0.7, 'NAFLD': 0.7,
            '信号通路': 0.6, '转录调控': 0.6,
            '线粒体': 0.5, '内质网': 0.5,
            '临床': 0.4, '治疗': 0.4
        }
        
        for i, tag in enumerate(tags[:8]):  # 最多取8个标签
            weight = tag_weights.get(tag, 0.3)
            feature[i % 32] += weight
            
        return feature
        
    def get_or_create_user_profile(self, user_id: int) -> UserInterestProfile:
        """获取或创建用户画像"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserInterestProfile(user_id)
        return self.user_profiles[user_id]
        
    def record_user_behavior(self, user_id: int, note_id: int, 
                            proteins: List[str], tags: List[str],
                            action: str = 'view'):
        """记录用户行为并更新画像"""
        profile = self.get_or_create_user_profile(user_id)
        profile.update_from_behavior(note_id, proteins, tags, action)
        
    def recommend(self, user_id: int, top_k: int = 10, 
                 exclude_seen: bool = True) -> List[Dict]:
        """
        多模态融合推荐（核心算法）
        
        流程：
        1. 获取用户兴趣画像
        2. 多路召回（PPI邻居 + 标签匹配 + 热门）
        3. 多模态融合排序
        4. 返回TopK
        """
        profile = self.get_or_create_user_profile(user_id)
        
        # 1. 多路召回
        candidates = self._multi_channel_recall(profile, n_candidates=100)
        
        # 2. 多模态融合排序
        scored_candidates = []
        for note_id in candidates:
            if exclude_seen and note_id in profile.read_notes:
                continue
                
            score, details = self._multimodal_score(profile, note_id)
            scored_candidates.append({
                'note_id': note_id,
                'score': score,
                'details': details
            })
            
        # 3. 排序返回
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        return scored_candidates[:top_k]
        
    def _multi_channel_recall(self, profile: UserInterestProfile, 
                             n_candidates: int = 100) -> List[int]:
        """多路召回策略 - 确保多样性，让各模态都能发挥作用"""
        candidates = []
        
        # 通道1：基于PPI网络的召回 (30%)
        ppi_candidates = []
        top_proteins = profile.get_top_proteins(k=5)
        for protein, weight in top_proteins:
            neighbors = self.ppi_graph.get(protein, [])
            for neighbor_protein, ppi_score in neighbors[:5]:
                for note_id, features in self.note_features.items():
                    if neighbor_protein in features['proteins']:
                        ppi_candidates.append(note_id)
                        break
        candidates.extend(random.sample(ppi_candidates, min(len(ppi_candidates), 30)) if len(ppi_candidates) > 30 else ppi_candidates)
        
        # 通道2：基于内容标签的召回 (40%)
        content_candidates = []
        top_tags = profile.get_top_tags(k=5)
        for tag, weight in top_tags:
            for note_id, features in self.note_features.items():
                if tag in features['tags'] and note_id not in content_candidates:
                    content_candidates.append(note_id)
                    if len(content_candidates) >= 40:
                        break
        candidates.extend(content_candidates)
        
        # 通道3：基于行为的协同过滤召回 (20%)
        behavior_candidates = []
        similar_users = self._find_similar_users(profile.user_id, k=10)
        for other_user_id, similarity in similar_users:
            if similarity > 0.3:  # 只取高相似度用户
                other_profile = self.user_profiles.get(other_user_id)
                if other_profile:
                    for note_id in other_profile.liked_notes:
                        if note_id not in behavior_candidates:
                            behavior_candidates.append(note_id)
                    for note_id in other_profile.favorited_notes:
                        if note_id not in behavior_candidates:
                            behavior_candidates.append(note_id)
        candidates.extend(behavior_candidates[:20])
        
        # 通道4：热门补充 + 随机探索 (10%)
        all_note_ids = list(self.note_features.keys())
        popular_notes = sorted(
            all_note_ids,
            key=lambda x: self.note_features[x]['stats'][0],  # 按点赞数
            reverse=True
        )
        # 混合热门和随机
        popular_sample = popular_notes[:10]
        random_sample = random.sample(all_note_ids, min(5, len(all_note_ids)))
        exploration_candidates = list(set(popular_sample + random_sample))
        candidates.extend(exploration_candidates)
        
        # 去重并打乱顺序
        unique_candidates = list(set(candidates))
        random.shuffle(unique_candidates)
        
        return unique_candidates[:n_candidates]
        
    def _multimodal_score(self, profile: UserInterestProfile, 
                         note_id: int) -> Tuple[float, Dict]:
        """
        多模态融合评分
        
        返回: (总分, 各模态详情)
        """
        if note_id not in self.note_features:
            return 0.0, {}
            
        note_feature = self.note_features[note_id]
        
        # 1. 图模态得分（PPI网络匹配）
        graph_score = self._compute_graph_match_score(profile, note_feature)
        
        # 2. 内容模态得分（标签相似度）
        content_score = self._compute_content_match_score(profile, note_feature)
        
        # 3. 行为模态得分（协同过滤思想）
        behavior_score = self._compute_behavior_match_score(profile, note_id)
        
        # 4. 统计特征得分（热度）
        stats_score = np.mean(note_feature['stats'])
        
        # 5. 加权融合
        w = self.modality_weights
        final_score = (
            w['graph'] * graph_score +
            w['content'] * content_score +
            w['behavior'] * behavior_score +
            0.1 * stats_score  # 热度作为bias
        )
        
        details = {
            'graph_score': graph_score,
            'content_score': content_score,
            'behavior_score': behavior_score,
            'stats_score': stats_score,
            'modality_weights': w
        }
        
        return final_score, details
        
    def _compute_graph_match_score(self, profile: UserInterestProfile,
                                   note_feature: Dict) -> float:
        """图表征匹配得分（用户兴趣蛋白 vs 笔记蛋白的PPI关系）- 修复版"""
        user_proteins = set(profile.interested_proteins)
        note_proteins = set(note_feature['proteins'])
        
        if not user_proteins or not note_proteins:
            return 0.0
            
        # 计算三种匹配关系
        direct_matches = []  # 用户蛋白直接出现在笔记中
        ppi_neighbors = []   # 用户蛋白与笔记蛋白有PPI关系
        no_relation = 0      # 无关系
        
        for user_protein in user_proteins:
            if user_protein in note_proteins:
                # 直接匹配：权重最高
                weight = profile.protein_weights.get(user_protein, 1.0)
                direct_matches.append(min(weight / 5.0, 1.0))  # 归一化
            else:
                # 检查PPI关系
                neighbors = self.ppi_graph.get(user_protein, [])
                found_relation = False
                for neighbor, score in neighbors:
                    if neighbor in note_proteins:
                        # PPI邻居：权重 = PPI得分 * 用户兴趣权重
                        user_weight = profile.protein_weights.get(user_protein, 1.0)
                        combined_score = score * min(user_weight / 5.0, 1.0)
                        ppi_neighbors.append(combined_score)
                        found_relation = True
                        break
                if not found_relation:
                    no_relation += 1
                    
        # 综合得分：直接匹配 > PPI邻居 > 无关系
        if direct_matches:
            # 有直接匹配：高分
            return 0.8 + 0.2 * np.mean(direct_matches)
        elif ppi_neighbors:
            # 只有PPI邻居：中等分数 (0.3-0.7)
            return 0.3 + 0.4 * np.mean(ppi_neighbors)
        else:
            # 无关系：低分
            return 0.0
        
    def _compute_content_match_score(self, profile: UserInterestProfile,
                                    note_feature: Dict) -> float:
        """内容匹配得分（标签相似度）"""
        user_tags = set(profile.interested_tags.keys())
        note_tags = set(note_feature['tags'])
        
        if not user_tags or not note_tags:
            return 0.0
            
        # Jaccard相似度
        intersection = user_tags & note_tags
        union = user_tags | note_tags
        
        if union:
            jaccard = len(intersection) / len(union)
            
            # 加权（考虑标签权重）
            weighted_score = sum(profile.interested_tags[tag] for tag in intersection)
            weighted_score /= sum(profile.interested_tags.values()) if profile.interested_tags else 1
            
            return 0.5 * jaccard + 0.5 * weighted_score
        return 0.0
        
    def _compute_behavior_match_score(self, profile: UserInterestProfile,
                                     note_id: int) -> float:
        """行为匹配得分（协同过滤）- 修复版"""
        # 找到与当前用户相似的用户
        similar_users = self._find_similar_users(profile.user_id, k=10)
        
        if not similar_users:
            return 0.0
            
        # 看相似用户是否喜欢这个笔记
        total_score = 0.0
        total_weight = 0.0
        
        for other_user_id, similarity in similar_users:
            if similarity <= 0:
                continue
            other_profile = self.user_profiles.get(other_user_id)
            if other_profile:
                if note_id in other_profile.favorited_notes:
                    total_score += 3.0 * similarity
                    total_weight += similarity
                elif note_id in other_profile.liked_notes:
                    total_score += 2.0 * similarity
                    total_weight += similarity
                elif note_id in other_profile.read_notes:
                    total_score += 0.5 * similarity
                    total_weight += similarity * 0.5
                    
        if total_weight > 0:
            normalized_score = min(total_score / (total_weight * 2), 1.0)
            return normalized_score
        return 0.0
        
    def _find_similar_users(self, user_id: int, k: int = 5) -> List[Tuple[int, float]]:
        """找到与指定用户兴趣相似的其他用户"""
        if user_id not in self.user_profiles:
            return []
            
        target_profile = self.user_profiles[user_id]
        similarities = []
        
        for other_id, other_profile in self.user_profiles.items():
            if other_id != user_id:
                # 计算蛋白兴趣相似度
                common_proteins = set(target_profile.interested_proteins) & set(other_profile.interested_proteins)
                if common_proteins:
                    similarity = len(common_proteins) / max(
                        len(target_profile.interested_proteins),
                        len(other_profile.interested_proteins)
                    )
                    similarities.append((other_id, similarity))
                    
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]


# ==================== Evaluation ====================

class RecommendationEvaluator:
    """推荐系统评估器"""
    
    def __init__(self, recommender: MultimodalFusionRecommender):
        self.recommender = recommender
        self.test_cases = []
        
    def generate_test_data(self, n_users: int = 100, n_notes: int = 50):
        """生成模拟测试数据"""
        print(f"生成{n_users}个用户，{n_notes}篇笔记的测试数据...")
        
        # 模拟笔记数据
        proteins_pool = ['CIDEA', 'FSP27', 'ATGL', 'HSL', 'Perilipin', 
                        'PLIN1', 'PLIN2', 'DGAT1', 'DGAT2', 'SREBP',
                        'PPAR', 'AMPK', 'mTOR', 'LXR', 'FASN', 'SCD1']
        tags_pool = ['脂滴', '代谢', '脂肪', '肥胖', '糖尿病', 
                    '信号通路', '转录调控', '临床', '治疗', 'NAFLD']
        
        notes_data = []
        for i in range(n_notes):
            note_id = i + 1
            proteins = random.sample(proteins_pool, k=random.randint(1, 4))
            tags = random.sample(tags_pool, k=random.randint(2, 5))
            
            notes_data.append({
                'note_id': note_id,
                'proteins': proteins,
                'tags': tags,
                'text': f'Note about {", ".join(proteins)}',
                'like_count': random.randint(0, 100),
                'favorite_count': random.randint(0, 50),
                'comment_count': random.randint(0, 30),
                'citation_count': random.randint(0, 500)
            })
            
        # 构建笔记特征
        self.recommender.build_note_features(notes_data)
        
        # 模拟用户行为数据
        for user_id in range(1, n_users + 1):
            # 每个用户随机浏览5-15篇笔记
            n_actions = random.randint(5, 15)
            viewed_notes = random.sample(range(1, n_notes + 1), k=min(n_actions, n_notes))
            
            for note_id in viewed_notes:
                note = notes_data[note_id - 1]
                
                # 随机行为类型
                action_type = random.choices(
                    ['view', 'like', 'favorite'],
                    weights=[0.6, 0.3, 0.1]
                )[0]
                
                self.recommender.record_user_behavior(
                    user_id, note_id,
                    note['proteins'], note['tags'],
                    action=action_type
                )
                
        print("测试数据生成完成！")
        
    def evaluate(self, n_test_users: int = 20, k: int = 10) -> Dict:
        """评估推荐效果"""
        print(f"\n开始评估{n_test_users}个用户的推荐效果...")
        
        metrics = {
            'precision@k': [],
            'recall@k': [],
            'ndcg@k': [],
            'coverage': set(),
            'diversity': []
        }
        
        for user_id in range(1, n_test_users + 1):
            profile = self.recommender.get_or_create_user_profile(user_id)
            
            # 获取用户真实喜欢的笔记（测试集）
            ground_truth = profile.liked_notes | profile.favorited_notes
            
            if not ground_truth:
                continue
                
            # 获取推荐（不排除已读，用于测试）
            recommendations = self.recommender.recommend(
                user_id, top_k=k, exclude_seen=False
            )
            rec_ids = [r['note_id'] for r in recommendations]
            
            # 计算指标
            hits = len(set(rec_ids) & ground_truth)
            
            # Precision@K
            precision = hits / k if k > 0 else 0
            metrics['precision@k'].append(precision)
            
            # Recall@K
            recall = hits / len(ground_truth) if ground_truth else 0
            metrics['recall@k'].append(recall)
            
            # NDCG@K
            dcg = sum([1.0 / np.log2(i + 2) for i, rec in enumerate(recommendations) 
                      if rec['note_id'] in ground_truth])
            idcg = sum([1.0 / np.log2(i + 2) for i in range(min(len(ground_truth), k))])
            ndcg = dcg / idcg if idcg > 0 else 0
            metrics['ndcg@k'].append(ndcg)
            
            # Coverage
            metrics['coverage'].update(rec_ids)
            
            # Diversity (基于标签的多样性)
            rec_tags = set()
            for rec in recommendations:
                note_feature = self.recommender.note_features.get(rec['note_id'])
                if note_feature:
                    rec_tags.update(note_feature['tags'])
            diversity = len(rec_tags) / (k * 3) if k > 0 else 0  # 假设每篇笔记3个标签
            metrics['diversity'].append(min(diversity, 1.0))
            
        # 汇总结果
        results = {
            'precision@k': np.mean(metrics['precision@k']),
            'recall@k': np.mean(metrics['recall@k']),
            'ndcg@k': np.mean(metrics['ndcg@k']),
            'coverage': len(metrics['coverage']) / 50,  # 假设总共50篇笔记
            'diversity': np.mean(metrics['diversity']),
            'f1@k': 2 * np.mean(metrics['precision@k']) * np.mean(metrics['recall@k']) / 
                   (np.mean(metrics['precision@k']) + np.mean(metrics['recall@k'])) 
                   if (np.mean(metrics['precision@k']) + np.mean(metrics['recall@k'])) > 0 else 0
        }
        
        return results


# ==================== Main ====================

def main():
    """主程序：运行多模态融合推荐评估"""
    
    print("=" * 60)
    print("ProteinHub 多模态融合推荐系统 - Evaluation")
    print("=" * 60)
    
    # 1. 初始化推荐器
    print("\n[1] 初始化推荐器...")
    recommender = MultimodalFusionRecommender(ppi_threshold=0.6)
    
    # 2. 加载PPI数据（模拟158k对，500+可信对）
    print("\n[2] 加载PPI数据...")
    ppi_data = []
    proteins = [f'PROTEIN_{i}' for i in range(1, 100)]
    
    # 生成500+可信对
    np.random.seed(42)
    for _ in range(550):
        p1, p2 = random.sample(proteins, 2)
        score = random.uniform(0.6, 1.0)
        ppi_data.append((p1, p2, score))
        
    # 生成其他低分对
    for _ in range(2000):
        p1, p2 = random.sample(proteins, 2)
        score = random.uniform(0.1, 0.59)
        ppi_data.append((p1, p2, score))
        
    recommender.load_ppi_data(ppi_data)
    recommender.build_protein_embeddings()
    
    print(f"  - 总互作对: {len(ppi_data)}")
    print(f"  - 可信对(≥0.6): {len([p for p in ppi_data if p[2] >= 0.6])}")
    
    # 3. 初始化评估器并生成测试数据
    print("\n[3] 生成测试数据...")
    evaluator = RecommendationEvaluator(recommender)
    evaluator.generate_test_data(n_users=100, n_notes=50)
    
    # 4. 运行评估
    print("\n[4] 运行评估...")
    results = evaluator.evaluate(n_test_users=20, k=10)
    
    # 5. 输出结果
    print("\n" + "=" * 60)
    print("评估结果")
    print("=" * 60)
    print(f"Precision@10:  {results['precision@k']:.4f}")
    print(f"Recall@10:     {results['recall@k']:.4f}")
    print(f"F1@10:         {results['f1@k']:.4f}")
    print(f"NDCG@10:       {results['ndcg@k']:.4f}")
    print(f"Coverage:      {results['coverage']:.4f}")
    print(f"Diversity:     {results['diversity']:.4f}")
    print("=" * 60)
    
    # 6. 示例推荐
    print("\n[5] 示例推荐展示（用户1）:")
    user_profile = recommender.get_or_create_user_profile(1)
    print(f"  用户兴趣蛋白: {list(user_profile.interested_proteins)[:5]}")
    print(f"  阅读历史: {len(user_profile.read_notes)}篇")
    print(f"  点赞: {len(user_profile.liked_notes)}篇")
    
    recommendations = recommender.recommend(1, top_k=5)
    print(f"\n  Top5推荐:")
    for i, rec in enumerate(recommendations, 1):
        details = rec['details']
        print(f"  {i}. 笔记{rec['note_id']} (总分:{rec['score']:.3f})")
        print(f"     - 图表征: {details['graph_score']:.3f}")
        print(f"     - 内容: {details['content_score']:.3f}")
        print(f"     - 行为: {details['behavior_score']:.3f}")
        
    print("\n✅ 评估完成!")
    
    return results


if __name__ == '__main__':
    results = main()
