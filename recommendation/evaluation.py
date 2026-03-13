"""
ProteinHub Recommendation System - Evaluation Metrics
评估指标计算：离线指标、在线指标、业务指标
"""
import pandas as pd
import numpy as np
from collections import defaultdict
import json

class RecommendationEvaluator:
    """推荐系统评估器"""
    
    def __init__(self):
        self.metrics = {}
        
    def calculate_offline_metrics(self, recommendations, test_interactions, k_list=[5, 10, 20]):
        """
        计算离线指标
        
        Parameters:
        -----------
        recommendations: dict {user_id: [(item_id, score), ...]}
        test_interactions: dict {user_id: set of item_ids}
        """
        metrics = {}
        
        for k in k_list:
            # Precision@K
            precisions = []
            for user_id, recs in recommendations.items():
                if user_id not in test_interactions:
                    continue
                
                top_k_recs = [item for item, _ in recs[:k]]
                relevant_items = test_interactions[user_id]
                
                n_relevant = len(set(top_k_recs) & relevant_items)
                precision = n_relevant / k if k > 0 else 0
                precisions.append(precision)
            
            metrics[f'Precision@{k}'] = np.mean(precisions) if precisions else 0
            
            # Recall@K
            recalls = []
            for user_id, recs in recommendations.items():
                if user_id not in test_interactions:
                    continue
                
                top_k_recs = [item for item, _ in recs[:k]]
                relevant_items = test_interactions[user_id]
                
                n_relevant = len(set(top_k_recs) & relevant_items)
                recall = n_relevant / len(relevant_items) if relevant_items else 0
                recalls.append(recall)
            
            metrics[f'Recall@{k}'] = np.mean(recalls) if recalls else 0
            
            # F1@K
            p = metrics[f'Precision@{k}']
            r = metrics[f'Recall@{k}']
            metrics[f'F1@{k}'] = 2 * p * r / (p + r) if (p + r) > 0 else 0
            
            # NDCG@K
            ndcgs = []
            for user_id, recs in recommendations.items():
                if user_id not in test_interactions:
                    continue
                
                relevant_items = test_interactions[user_id]
                dcg = 0
                idcg = 0
                
                for i, (item, _) in enumerate(recs[:k]):
                    if item in relevant_items:
                        dcg += 1 / np.log2(i + 2)  # i+2 because log2(1) = 0
                
                # Ideal DCG
                for i in range(min(len(relevant_items), k)):
                    idcg += 1 / np.log2(i + 2)
                
                ndcg = dcg / idcg if idcg > 0 else 0
                ndcgs.append(ndcg)
            
            metrics[f'NDCG@{k}'] = np.mean(ndcgs) if ndcgs else 0
        
        # MAP (Mean Average Precision)
        aps = []
        for user_id, recs in recommendations.items():
            if user_id not in test_interactions:
                continue
            
            relevant_items = test_interactions[user_id]
            if not relevant_items:
                continue
            
            precisions_at_i = []
            n_relevant_so_far = 0
            
            for i, (item, _) in enumerate(recs):
                if item in relevant_items:
                    n_relevant_so_far += 1
                    precisions_at_i.append(n_relevant_so_far / (i + 1))
            
            ap = np.mean(precisions_at_i) if precisions_at_i else 0
            aps.append(ap)
        
        metrics['MAP'] = np.mean(aps) if aps else 0
        
        # Coverage（覆盖率）
        all_recommended_items = set()
        for recs in recommendations.values():
            all_recommended_items.update([item for item, _ in recs])
        
        # 假设总共有164篇笔记
        total_items = 164
        metrics['Coverage'] = len(all_recommended_items) / total_items
        
        # Diversity（多样性）- 基于推荐列表的平均两两差异
        diversities = []
        for user_id, recs in recommendations.items():
            if len(recs) < 2:
                continue
            
            items = [item for item, _ in recs[:10]]  # 取Top 10
            # 简单的多样性：不同item_id的比例（实际应用可以用内容相似度）
            unique_items = len(set(items))
            diversity = unique_items / len(items) if items else 0
            diversities.append(diversity)
        
        metrics['Diversity'] = np.mean(diversities) if diversities else 0
        
        self.metrics['offline'] = metrics
        return metrics
    
    def calculate_online_metrics(self, simulated_logs):
        """
        计算在线指标（基于模拟日志）
        
        Parameters:
        -----------
        simulated_logs: DataFrame with columns [user_id, item_id, action, timestamp]
        """
        metrics = {}
        
        # CTR (Click-Through Rate)
        total_impressions = len(simulated_logs[simulated_logs['action'] == 'impression'])
        total_clicks = len(simulated_logs[simulated_logs['action'] == 'click'])
        metrics['CTR'] = total_clicks / total_impressions if total_impressions > 0 else 0
        
        # 收藏率
        total_collects = len(simulated_logs[simulated_logs['action'] == 'collect'])
        metrics['Collect_Rate'] = total_collects / total_impressions if total_impressions > 0 else 0
        
        # 点赞率
        total_likes = len(simulated_logs[simulated_logs['action'] == 'like'])
        metrics['Like_Rate'] = total_likes / total_impressions if total_impressions > 0 else 0
        
        # 平均阅读时长
        read_logs = simulated_logs[simulated_logs['action'] == 'read']
        if 'duration' in read_logs.columns:
            metrics['Avg_Read_Time'] = read_logs['duration'].mean()
        else:
            metrics['Avg_Read_Time'] = 0
        
        # 用户留存率（模拟：7天内回访的用户比例）
        user_first_visit = simulated_logs.groupby('user_id')['timestamp'].min()
        user_last_visit = simulated_logs.groupby('user_id')['timestamp'].max()
        
        # 假设时间跨度足够
        retention = (user_last_visit > user_first_visit).mean()
        metrics['Retention_Rate'] = retention
        
        self.metrics['online'] = metrics
        return metrics
    
    def calculate_business_metrics(self, recommendations, item_metadata, user_data):
        """
        计算业务指标
        
        Parameters:
        -----------
        recommendations: dict {user_id: [(item_id, score), ...]}
        item_metadata: DataFrame with note metadata
        user_data: DataFrame with user info
        """
        metrics = {}
        
        # 笔记曝光量分布
        exposure_counts = defaultdict(int)
        for recs in recommendations.values():
            for item, _ in recs:
                exposure_counts[item] += 1
        
        exposures = list(exposure_counts.values())
        metrics['Avg_Exposure'] = np.mean(exposures) if exposures else 0
        metrics['Exposure_Std'] = np.std(exposures) if exposures else 0
        
        # 长尾效应：底部80%的笔记获得的曝光占比
        sorted_exposures = sorted(exposure_counts.items(), key=lambda x: x[1], reverse=True)
        total_exposure = sum(exposures)
        
        # Gini系数（衡量分布不均）
        n = len(exposures)
        if n > 0 and total_exposure > 0:
            index = np.arange(1, n + 1)
            exposures_sorted = np.sort(exposures)
            gini = (2 * np.sum(index * exposures_sorted)) / (n * np.sum(exposures_sorted)) - (n + 1) / n
            metrics['Gini_Coefficient'] = gini
        else:
            metrics['Gini_Coefficient'] = 0
        
        # 新用户留存（模拟）
        # 假设新用户是注册时间较近的用户
        if 'register_time' in user_data.columns:
            new_users = user_data[user_data['user_type'] == 'newbie']
            metrics['New_User_Count'] = len(new_users)
        
        # 内容生产者激励：不同作者的笔记被推荐情况
        if 'author_id' in item_metadata.columns:
            author_exposure = defaultdict(int)
            for item_id, count in exposure_counts.items():
                author = item_metadata[item_metadata['note_id'] == item_id]['author_id'].values
                if len(author) > 0:
                    author_exposure[author[0]] += count
            
            metrics['Authors_Covered'] = len(author_exposure)
            metrics['Avg_Exposure_Per_Author'] = np.mean(list(author_exposure.values())) if author_exposure else 0
        
        self.metrics['business'] = metrics
        return metrics
    
    def get_all_metrics(self):
        """获取所有评估指标"""
        return self.metrics
    
    def print_metrics_report(self):
        """打印评估报告"""
        print("\n" + "="*60)
        print("ProteinHub Recommendation System - Evaluation Report")
        print("="*60)
        
        if 'offline' in self.metrics:
            print("\n📊 Offline Metrics:")
            print("-" * 40)
            for metric, value in self.metrics['offline'].items():
                print(f"  {metric:20s}: {value:.4f}")
        
        if 'online' in self.metrics:
            print("\n📈 Online Metrics:")
            print("-" * 40)
            for metric, value in self.metrics['online'].items():
                if isinstance(value, float):
                    print(f"  {metric:20s}: {value:.4f}")
                else:
                    print(f"  {metric:20s}: {value}")
        
        if 'business' in self.metrics:
            print("\n💼 Business Metrics:")
            print("-" * 40)
            for metric, value in self.metrics['business'].items():
                if isinstance(value, float):
                    print(f"  {metric:20s}: {value:.4f}")
                else:
                    print(f"  {metric:20s}: {value}")
        
        print("\n" + "="*60)


def compare_algorithms(results_dict):
    """
    比较多个算法的性能
    
    Parameters:
    -----------
    results_dict: dict {algorithm_name: metrics_dict}
    """
    print("\n" + "="*80)
    print("Algorithm Comparison")
    print("="*80)
    
    # 获取所有指标
    all_metrics = set()
    for metrics in results_dict.values():
        all_metrics.update(metrics.keys())
    
    # 打印对比表格
    metric_list = sorted(all_metrics)
    
    print(f"\n{'Metric':<20}", end="")
    for algo in results_dict.keys():
        print(f"{algo:<15}", end="")
    print()
    print("-" * 80)
    
    for metric in metric_list:
        print(f"{metric:<20}", end="")
        for algo, metrics in results_dict.items():
            value = metrics.get(metric, 0)
            print(f"{value:<15.4f}", end="")
        print()
    
    print("="*80)


if __name__ == '__main__':
    print("Evaluation module loaded successfully")
