"""
ProteinHub Recommendation System Tests
推荐系统测试套件
"""
import pytest
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recommendation.dual_tower import DualTowerRecommender, SimpleRecommender


# ============================================================================
# Mock Models
# ============================================================================

class MockProtein:
    """模拟蛋白模型"""
    def __init__(self, id, name, family=None, description=None):
        self.id = id
        self.name = name
        self.family = family
        self.description = description or f"Description of {name}"


class MockUser:
    """模拟用户模型"""
    def __init__(self, id, username, created_at=None):
        self.id = id
        self.username = username
        self.created_at = created_at or datetime.utcnow()


# ============================================================================
# Dual Tower Recommender Tests
# ============================================================================

class TestDualTowerRecommender:
    """双塔推荐模型测试"""
    
    @pytest.fixture
    def sample_proteins(self):
        """创建测试蛋白数据"""
        return [
            MockProtein(1, 'CIDEA', 'CIDE', 'Cell Death-Inducing DFF45-like Effector A'),
            MockProtein(2, 'CIDEB', 'CIDE', 'Cell Death-Inducing DFF45-like Effector B'),
            MockProtein(3, 'CIDEC', 'CIDE', 'Cell Death-Inducing DFF45-like Effector C'),
            MockProtein(4, 'PLIN1', 'PLIN', 'Perilipin 1'),
            MockProtein(5, 'PLIN2', 'PLIN', 'Perilipin 2'),
            MockProtein(6, 'PLIN3', 'PLIN', 'Perilipin 3'),
        ]
    
    @pytest.fixture
    def sample_user(self):
        """创建测试用户"""
        return MockUser(1, 'testuser')
    
    @pytest.fixture
    def fitted_model(self, sample_proteins):
        """创建并训练好的模型"""
        model = DualTowerRecommender(embedding_dim=32)
        model.fit(sample_proteins)
        return model
    
    def test_initialization(self):
        """测试模型初始化"""
        model = DualTowerRecommender(embedding_dim=64)
        assert model.embedding_dim == 64
        assert model.is_fitted is False
        assert len(model.item_embeddings) == 0
        assert len(model.user_embeddings) == 0
    
    def test_fit(self, sample_proteins):
        """测试模型训练"""
        model = DualTowerRecommender(embedding_dim=32)
        model.fit(sample_proteins)
        
        assert model.is_fitted is True
        assert len(model.item_embeddings) == len(sample_proteins)
        assert model.n_families > 0
        assert len(model.family_to_idx) > 0
        
        # 检查嵌入向量维度
        for protein_id, embedding in model.item_embeddings.items():
            assert len(embedding) == 32
            # 检查归一化
            norm = np.linalg.norm(embedding)
            assert abs(norm - 1.0) < 1e-6 or norm == 0.0
    
    def test_item_tower_output(self, fitted_model, sample_proteins):
        """测试物品塔输出"""
        protein = sample_proteins[0]
        embedding = fitted_model._item_tower(protein)
        
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == fitted_model.embedding_dim
    
    def test_user_tower_output(self, fitted_model, sample_user):
        """测试用户塔输出"""
        embedding = fitted_model._user_tower(sample_user, [], [])
        
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == fitted_model.embedding_dim
    
    def test_get_user_embedding_new_user(self, fitted_model, sample_user):
        """测试获取新用户嵌入"""
        embedding = fitted_model.get_user_embedding(sample_user, [])
        
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == fitted_model.embedding_dim
        assert sample_user.id in fitted_model.user_embeddings
    
    def test_get_user_embedding_existing_user(self, fitted_model, sample_user):
        """测试获取已有用户嵌入"""
        # 第一次获取
        embedding1 = fitted_model.get_user_embedding(sample_user, [])
        # 第二次获取（应该从缓存读取）
        embedding2 = fitted_model.get_user_embedding(sample_user, [])
        
        np.testing.assert_array_equal(embedding1, embedding2)
    
    def test_recommend(self, fitted_model, sample_user, sample_proteins):
        """测试推荐功能"""
        # 用户关注部分蛋白
        followed = sample_proteins[:2]
        recommendations = fitted_model.recommend(sample_user, followed, top_k=3)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 3
        
        # 检查推荐格式
        for item_id, score in recommendations:
            assert isinstance(item_id, int)
            assert isinstance(score, (int, float))
            # 已关注的蛋白不应出现在推荐中
            assert item_id not in [p.id for p in followed]
    
    def test_recommend_not_fitted(self, sample_user):
        """测试未训练模型推荐"""
        model = DualTowerRecommender(embedding_dim=32)
        
        with pytest.raises(RuntimeError) as exc_info:
            model.recommend(sample_user, [], top_k=5)
        
        assert '未初始化' in str(exc_info.value) or 'fit' in str(exc_info.value).lower()
    
    def test_recommend_for_new_user(self, fitted_model):
        """测试冷启动推荐"""
        selected_families = ['CIDE']
        recommendations = fitted_model.recommend_for_new_user(selected_families, top_k=5)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 5
        
        # 推荐应该包含同家族的蛋白
        for item_id, score in recommendations:
            assert isinstance(item_id, int)
            assert score >= 0
    
    def test_save_and_load(self, fitted_model, tmp_path):
        """测试模型保存和加载"""
        filepath = tmp_path / "model.json"
        
        # 保存模型
        fitted_model.save(str(filepath))
        assert filepath.exists()
        
        # 加载模型
        loaded_model = DualTowerRecommender.load(str(filepath))
        
        assert loaded_model.embedding_dim == fitted_model.embedding_dim
        assert loaded_model.is_fitted == fitted_model.is_fitted
        assert len(loaded_model.item_embeddings) == len(fitted_model.item_embeddings)
        assert loaded_model.n_families == fitted_model.n_families
    
    def test_recommend_with_exclude_ids(self, fitted_model, sample_user, sample_proteins):
        """测试带排除列表的推荐"""
        exclude_ids = [4, 5, 6]  # 排除所有 PLIN 蛋白
        recommendations = fitted_model.recommend(
            sample_user, [], top_k=10, exclude_ids=exclude_ids
        )
        
        for item_id, _ in recommendations:
            assert item_id not in exclude_ids
    
    def test_recommend_top_k_limit(self, fitted_model, sample_user, sample_proteins):
        """测试推荐数量限制"""
        for top_k in [1, 3, 5]:
            recommendations = fitted_model.recommend(sample_user, [], top_k=top_k)
            assert len(recommendations) <= top_k


# ============================================================================
# Simple Recommender Tests
# ============================================================================

class TestSimpleRecommender:
    """简单推荐器测试"""
    
    @pytest.fixture
    def sample_proteins(self):
        """创建测试蛋白数据"""
        return [
            MockProtein(1, 'CIDEA', 'CIDE'),
            MockProtein(2, 'CIDEB', 'CIDE'),
            MockProtein(3, 'CIDEC', 'CIDE'),
            MockProtein(4, 'PLIN1', 'PLIN'),
            MockProtein(5, 'PLIN2', 'PLIN'),
            MockProtein(6, 'PLIN3', 'PLIN'),
            MockProtein(7, 'ATGL', 'Lipase'),
        ]
    
    def test_recommend_by_family(self, sample_proteins):
        """测试同家族推荐"""
        recommendations = SimpleRecommender.recommend_by_family(
            1, sample_proteins, top_k=5
        )
        
        assert isinstance(recommendations, list)
        # 应该推荐同家族的其他蛋白
        for item_id, score in recommendations:
            assert item_id != 1  # 不包含查询蛋白本身
            protein = next(p for p in sample_proteins if p.id == item_id)
            assert protein.family == 'CIDE'
    
    def test_recommend_by_family_not_found(self, sample_proteins):
        """测试不存在的蛋白推荐"""
        recommendations = SimpleRecommender.recommend_by_family(
            999, sample_proteins, top_k=5
        )
        assert recommendations == []
    
    def test_recommend_by_family_no_family(self, sample_proteins):
        """测试无家族蛋白的推荐"""
        # 创建一个无家族的蛋白
        protein_no_family = MockProtein(8, 'UNKNOWN', None)
        all_proteins = sample_proteins + [protein_no_family]
        
        recommendations = SimpleRecommender.recommend_by_family(
            8, all_proteins, top_k=5
        )
        assert recommendations == []
    
    def test_recommend_popular(self, sample_proteins):
        """测试热门推荐"""
        recommendations = SimpleRecommender.recommend_popular(
            sample_proteins, top_k=5
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 5
        assert len(recommendations) <= len(sample_proteins)
        
        # 检查格式
        for item_id, score in recommendations:
            assert isinstance(item_id, int)
            assert score == 1.0  # 热门推荐固定分数为1.0
    
    def test_recommend_popular_empty_list(self):
        """测试空列表热门推荐"""
        recommendations = SimpleRecommender.recommend_popular([], top_k=5)
        assert recommendations == []
    
    def test_recommend_explore(self, sample_proteins):
        """测试探索推荐"""
        recommendations = SimpleRecommender.recommend_explore(
            sample_proteins, top_k=5
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 5
        
        # 推荐应该来自不同家族
        families = set()
        for item_id, score in recommendations:
            protein = next(p for p in sample_proteins if p.id == item_id)
            families.add(protein.family)
        
        # 探索推荐应该有多样性
        assert len(families) >= 1
    
    def test_recommend_explore_empty_list(self):
        """测试空列表探索推荐"""
        recommendations = SimpleRecommender.recommend_explore([], top_k=5)
        assert recommendations == []


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestRecommendationEdgeCases:
    """推荐系统边界情况测试"""
    
    def test_recommend_with_empty_proteins(self):
        """测试空蛋白列表"""
        model = DualTowerRecommender(embedding_dim=32)
        
        with pytest.raises(Exception):
            model.fit([])
    
    def test_recommend_single_protein(self):
        """测试只有一个蛋白的情况"""
        proteins = [MockProtein(1, 'CIDEA', 'CIDE')]
        model = DualTowerRecommender(embedding_dim=32)
        
        # 可以训练
        model.fit(proteins)
        assert model.is_fitted
        
        # 但不能推荐（没有其他蛋白）
        user = MockUser(1, 'test')
        recommendations = model.recommend(user, [], top_k=5)
        assert recommendations == []
    
    def test_recommend_more_than_available(self):
        """测试请求数量超过可用蛋白数"""
        proteins = [MockProtein(i, f'PROTEIN{i}', 'FAMILY') for i in range(1, 4)]
        model = DualTowerRecommender(embedding_dim=32)
        model.fit(proteins)
        
        user = MockUser(1, 'test')
        recommendations = model.recommend(user, [], top_k=10)
        
        # 应该返回所有可用蛋白
        assert len(recommendations) <= len(proteins)
    
    def test_similarity_score_range(self):
        """测试相似度分数范围"""
        proteins = [
            MockProtein(1, 'CIDEA', 'CIDE'),
            MockProtein(2, 'CIDEB', 'CIDE'),
        ]
        model = DualTowerRecommender(embedding_dim=32)
        model.fit(proteins)
        
        user = MockUser(1, 'test')
        recommendations = model.recommend(user, [], top_k=5)
        
        # 分数应该在 [-1, 1] 范围内（余弦相似度）
        for _, score in recommendations:
            assert -1.0 <= score <= 1.0
    
    def test_embedding_normalization(self):
        """测试嵌入向量归一化"""
        proteins = [MockProtein(i, f'P{i}', f'F{i%3}') for i in range(10)]
        model = DualTowerRecommender(embedding_dim=32)
        model.fit(proteins)
        
        # 所有嵌入向量应该归一化
        for protein_id, embedding in model.item_embeddings.items():
            norm = np.linalg.norm(embedding)
            # 允许小的数值误差
            assert abs(norm - 1.0) < 1e-5 or norm == 0.0


# ============================================================================
# Performance Tests
# ============================================================================

class TestRecommendationPerformance:
    """推荐系统性能测试"""
    
    def test_fit_performance(self):
        """测试模型训练性能"""
        import time
        
        proteins = [MockProtein(i, f'PROTEIN{i}', f'FAMILY{i%10}') for i in range(100)]
        model = DualTowerRecommender(embedding_dim=64)
        
        start = time.time()
        model.fit(proteins)
        elapsed = time.time() - start
        
        # 100个蛋白应该在1秒内完成训练
        assert elapsed < 1.0
    
    def test_recommend_performance(self):
        """测试推荐性能"""
        import time
        
        proteins = [MockProtein(i, f'PROTEIN{i}', f'FAMILY{i%10}') for i in range(100)]
        model = DualTowerRecommender(embedding_dim=64)
        model.fit(proteins)
        
        user = MockUser(1, 'test')
        
        start = time.time()
        for _ in range(100):
            model.recommend(user, [], top_k=10)
        elapsed = time.time() - start
        
        # 100次推荐应该在1秒内完成
        assert elapsed < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
