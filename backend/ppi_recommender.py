# PPI推荐系统实现
# 基于158蛋白超小规模网络，使用邻接表实现O(1)查询

import csv
from collections import defaultdict

class PPIRecommender:
    """基于蛋白互作网络的推荐系统"""
    
    def __init__(self, threshold=0.6):
        self.threshold = threshold
        self.ppi_graph = defaultdict(list)  # 邻接表：蛋白 -> [(邻居, 得分), ...]
        self.protein_to_notes = defaultdict(list)  # 蛋白 -> [笔记ID列表]
        self.all_proteins = set()
        
    def load_ppi_data(self, tsv_file_path):
        """加载PPI TSV数据文件
        
        预期格式（无表头）：
        protein_A  protein_B  score
        CIDEA      FSP27      0.85
        ...
        """
        with open(tsv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if len(row) >= 3:
                    protein_a, protein_b, score = row[0], row[1], float(row[2])
                    
                    # 只保留高于阈值的互作
                    if score >= self.threshold:
                        self.ppi_graph[protein_a].append((protein_b, score))
                        self.ppi_graph[protein_b].append((protein_a, score))
                        self.all_proteins.add(protein_a)
                        self.all_proteins.add(protein_b)
                        
        print(f"PPI网络加载完成：{len(self.all_proteins)}个蛋白，"
              f"{sum(len(v) for v in self.ppi_graph.values())//2}对互作")
        
    def build_protein_note_index(self, notes_data):
        """构建蛋白-笔记倒排索引
        
        Args:
            notes_data: list of dict, 每个dict包含note_id和proteins列表
            例如：[{'note_id': 1, 'proteins': ['CIDEA', 'FSP27']}, ...]
        """
        for note in notes_data:
            note_id = note['note_id']
            for protein in note.get('proteins', []):
                if protein in self.all_proteins:
                    self.protein_to_notes[protein].append(note_id)
                    
        print(f"蛋白-笔记索引构建完成：{len(self.protein_to_notes)}个蛋白有对应笔记")
        
    def get_neighbor_proteins(self, protein, min_score=None):
        """获取某蛋白的PPI邻居（互作伙伴）
        
        Args:
            protein: 蛋白名称
            min_score: 最低得分阈值（默认使用初始化时的threshold）
            
        Returns:
            list of tuples: [(neighbor_protein, score), ...] 按得分降序
        """
        if min_score is None:
            min_score = self.threshold
            
        neighbors = [(p, s) for p, s in self.ppi_graph.get(protein, []) 
                     if s >= min_score]
        return sorted(neighbors, key=lambda x: x[1], reverse=True)
        
    def recommend_by_ppi(self, user_history_note_ids, top_k=10, exclude_seen=True):
        """基于PPI网络推荐笔记
        
        推荐逻辑：
        1. 从用户历史笔记中提取关注的蛋白
        2. 找这些蛋白的PPI邻居（高得分互作伙伴）
        3. 返回邻居蛋白相关的笔记
        
        Args:
            user_history_note_ids: 用户浏览/互动的笔记ID列表
            top_k: 推荐数量
            exclude_seen: 是否排除已看过的笔记
            
        Returns:
            list: 推荐的笔记ID列表，带PPI推荐理由
        """
        # 1. 从用户历史中提取关注的蛋白
        watched_proteins = set()
        for note_id in user_history_note_ids:
            for protein, notes in self.protein_to_notes.items():
                if note_id in notes:
                    watched_proteins.add(protein)
                    
        if not watched_proteins:
            return []
            
        # 2. 找PPI邻居蛋白（带得分）
        candidate_scores = {}  # protein -> max_ppi_score
        for protein in watched_proteins:
            for neighbor, score in self.get_neighbor_proteins(protein):
                if neighbor not in watched_proteins:
                    # 保留最高得分
                    if neighbor not in candidate_scores or score > candidate_scores[neighbor]:
                        candidate_scores[neighbor] = score
                        
        # 3. 获取邻居蛋白的笔记
        recommendations = []
        seen_notes = set(user_history_note_ids) if exclude_seen else set()
        
        # 按PPI得分排序候选蛋白
        sorted_candidates = sorted(candidate_scores.items(), 
                                   key=lambda x: x[1], reverse=True)
        
        for protein, ppi_score in sorted_candidates:
            for note_id in self.protein_to_notes.get(protein, []):
                if note_id not in seen_notes:
                    recommendations.append({
                        'note_id': note_id,
                        'protein': protein,
                        'ppi_score': ppi_score,
                        'reason': f"基于{protein}的PPI互作推荐"
                    })
                    seen_notes.add(note_id)
                    
                    if len(recommendations) >= top_k:
                        return recommendations
                        
        return recommendations
        
    def get_protein_network_stats(self):
        """获取PPI网络统计信息"""
        total_edges = sum(len(v) for v in self.ppi_graph.values()) // 2
        avg_degree = sum(len(v) for v in self.ppi_graph.values()) / len(self.all_proteins) if self.all_proteins else 0
        
        # 找枢纽蛋白（连接数最多的）
        hub_proteins = sorted(self.ppi_graph.items(), 
                             key=lambda x: len(x[1]), reverse=True)[:10]
        
        return {
            'protein_count': len(self.all_proteins),
            'interaction_count': total_edges,
            'avg_degree': round(avg_degree, 2),
            'hub_proteins': [(p, len(n)) for p, n in hub_proteins]
        }


# 使用示例
if __name__ == '__main__':
    # 初始化推荐器
    recommender = PPIRecommender(threshold=0.6)
    
    # 加载PPI数据（假设TSV文件路径）
    # recommender.load_ppi_data('/path/to/whole.tsv')
    
    # 构建蛋白-笔记索引（示例数据）
    sample_notes = [
        {'note_id': 1, 'proteins': ['CIDEA', 'FSP27']},
        {'note_id': 2, 'proteins': ['ATGL', 'HSL']},
        {'note_id': 3, 'proteins': ['Perilipin', 'FSP27']},
    ]
    # recommender.build_protein_note_index(sample_notes)
    
    # 推荐示例
    # user_history = [1]  # 用户看过笔记1
    # recs = recommender.recommend_by_ppi(user_history, top_k=5)
    # print(recs)
