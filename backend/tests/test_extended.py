"""
ProteinHub Extended Tests
扩展测试套件

测试覆盖：
- Services (ProteinService, FeedService, SearchService)
- Utils (Cache, Performance)
- Routes (Admin, Follow, Recommendation)
- Models (User, Protein)
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 导入被测模块
import sys
sys.path.insert(0, '/root/.openclaw/workspace/projects/proteinhub/backend')

from app import app, db, Protein, User, Post, ProteinInteraction


@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def auth_headers(client):
    """获取认证头"""
    # 注册用户
    client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # 登录
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    data = json.loads(response.data)
    return {'Authorization': f'Bearer {data["access_token"]}'}


@pytest.fixture
def sample_proteins(client):
    """创建测试蛋白数据"""
    proteins = [
        Protein(name='CIDEA', family='CIDE', description='Test protein A'),
        Protein(name='PLIN1', family='PLIN', description='Test protein B'),
        Protein(name='ATGL', family='ATGL', description='Test protein C'),
    ]
    for p in proteins:
        db.session.add(p)
    db.session.commit()
    return proteins


# ============ Service 测试 ============

class TestProteinService:
    """ProteinService 测试"""
    
    def test_get_proteins_pagination(self, client, sample_proteins):
        """测试蛋白分页"""
        from services.protein_service import ProteinService
        
        result = ProteinService.get_proteins(page=1, per_page=2)
        
        assert len(result['items']) == 2
        assert result['total'] == 3
        assert result['pages'] == 2
    
    def test_get_proteins_by_family(self, client, sample_proteins):
        """测试按家族筛选"""
        from services.protein_service import ProteinService
        
        result = ProteinService.get_proteins(family='CIDE')
        
        assert len(result['items']) == 1
        assert result['items'][0]['name'] == 'CIDEA'
    
    def test_get_proteins_search(self, client, sample_proteins):
        """测试蛋白搜索"""
        from services.protein_service import ProteinService
        
        result = ProteinService.get_proteins(search='CIDE')
        
        assert len(result['items']) >= 1
        assert any('CIDE' in p['name'] or 'CIDE' in p['family'] for p in result['items'])
    
    def test_get_protein_profile(self, client, sample_proteins):
        """测试获取蛋白主页"""
        from services.protein_service import ProteinService
        
        profile = ProteinService.get_protein_profile(sample_proteins[0].id)
        
        assert profile is not None
        assert profile['protein']['name'] == 'CIDEA'
        assert 'biography' in profile
        assert 'interactions' in profile


class TestFeedService:
    """FeedService 测试"""
    
    def test_get_recent_feed(self, client, sample_proteins):
        """测试最新 Feed"""
        from services.feed_service import FeedService
        from models import Post
        
        # 创建测试帖子
        post = Post(
            protein_id=sample_proteins[0].id,
            title='Test Post',
            summary='Test summary'
        )
        db.session.add(post)
        db.session.commit()
        
        result = FeedService.get_feed(strategy='recent')
        
        assert len(result['items']) == 1
        assert result['items'][0]['title'] == 'Test Post'
    
    def test_get_random_feed(self, client, sample_proteins):
        """测试随机 Feed"""
        from services.feed_service import FeedService
        from models import Post
        
        # 创建多个帖子
        for i in range(5):
            post = Post(
                protein_id=sample_proteins[i % 3].id,
                title=f'Test Post {i}',
                summary=f'Summary {i}'
            )
            db.session.add(post)
        db.session.commit()
        
        result = FeedService.get_feed(strategy='random', per_page=3)
        
        assert len(result['items']) == 3
        assert result['strategy'] == 'random'


class TestSearchService:
    """SearchService 测试"""
    
    def test_search_proteins(self, client, sample_proteins):
        """测试蛋白搜索"""
        from services.search_service import SearchEngine
        
        engine = SearchEngine(db.session)
        result = engine.search_proteins('CIDEA', page=1, per_page=10)
        
        assert len(result['items']) >= 1
        assert result['query'] == 'CIDEA'
    
    def test_autocomplete(self, client, sample_proteins):
        """测试自动补全"""
        from services.search_service import SearchEngine
        
        engine = SearchEngine(db.session)
        result = engine.autocomplete('CID', limit=5)
        
        assert 'suggestions' in result
        assert len(result['suggestions']) >= 1


# ============ Route 测试 ============

class TestAdminRoutes:
    """管理后台路由测试"""
    
    def test_get_system_stats(self, client, sample_proteins):
        """测试获取系统统计"""
        # 创建管理员用户
        from auth import hash_password
        admin = User(
            username='admin',
            email='admin@test.com',
            password_hash=hash_password('admin123')
        )
        db.session.add(admin)
        db.session.commit()
        
        # 登录获取 token
        response = client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'admin123'
        })
        data = json.loads(response.data)
        headers = {'Authorization': f'Bearer {data["access_token"]}'}
        
        response = client.get('/api/admin/stats', headers=headers)
        
        assert response.status_code == 200
        stats = json.loads(response.data)
        assert 'users' in stats
        assert 'proteins' in stats


class TestFollowRoutes:
    """关注功能路由测试"""
    
    def test_follow_protein(self, client, sample_proteins, auth_headers):
        """测试关注蛋白"""
        protein_id = sample_proteins[0].id
        
        response = client.post(
            f'/api/proteins/{protein_id}/follow',
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == '关注成功'
    
    def test_follow_already_followed(self, client, sample_proteins, auth_headers):
        """测试重复关注"""
        protein_id = sample_proteins[0].id
        
        # 第一次关注
        client.post(f'/api/proteins/{protein_id}/follow', headers=auth_headers)
        
        # 第二次关注
        response = client.post(
            f'/api/proteins/{protein_id}/follow',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '已经关注' in data['message']
    
    def test_unfollow_protein(self, client, sample_proteins, auth_headers):
        """测试取消关注"""
        protein_id = sample_proteins[0].id
        
        # 先关注
        client.post(f'/api/proteins/{protein_id}/follow', headers=auth_headers)
        
        # 再取消关注
        response = client.delete(
            f'/api/proteins/{protein_id}/unfollow',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '取消关注成功' in data['message']
    
    def test_get_followed_proteins(self, client, sample_proteins, auth_headers):
        """测试获取关注列表"""
        # 关注两个蛋白
        client.post(f'/api/proteins/{sample_proteins[0].id}/follow', headers=auth_headers)
        client.post(f'/api/proteins/{sample_proteins[1].id}/follow', headers=auth_headers)
        
        response = client.get('/api/user/followed-proteins', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] == 2


class TestRecommendationRoutes:
    """推荐功能路由测试"""
    
    def test_cold_start_recommendation(self, client, sample_proteins):
        """测试冷启动推荐"""
        response = client.post('/api/recommend/cold-start', json={
            'selected_families': ['CIDE'],
            'top_k': 5
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendations' in data
    
    def test_explore_recommendation(self, client, sample_proteins):
        """测试探索推荐"""
        response = client.get('/api/recommend/explore?top_k=5')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendations' in data
    
    def test_personalized_recommendation(self, client, sample_proteins, auth_headers):
        """测试个性化推荐"""
        response = client.get(
            '/api/recommend/personalized?top_k=5',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendations' in data


# ============ Utils 测试 ============

class TestCache:
    """缓存工具测试"""
    
    def test_memory_cache_get_set(self):
        """测试内存缓存读写"""
        from utils.cache import MemoryCache
        
        cache = MemoryCache()
        cache.set('test_key', 'test_value', expire=60)
        
        value = cache.get('test_key')
        assert value == 'test_value'
    
    def test_memory_cache_expiration(self):
        """测试缓存过期"""
        from utils.cache import MemoryCache
        
        cache = MemoryCache()
        cache.set('test_key', 'test_value', expire=0)  # 立即过期
        
        value = cache.get('test_key')
        assert value is None
    
    def test_cache_make_key(self):
        """测试缓存键生成"""
        from utils.cache import Cache
        
        cache = Cache()
        key1 = cache._make_key('test', 'arg1', kwarg1='val1')
        key2 = cache._make_key('test', 'arg1', kwarg1='val1')
        
        assert key1 == key2


class TestPerformanceMonitor:
    """性能监控测试"""
    
    def test_record_request(self):
        """测试记录请求"""
        from utils.performance import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        monitor.record_request('/api/test', 0.1, 200)
        
        stats = monitor.get_stats()
        assert stats['total_requests'] == 1
    
    def test_record_slow_query(self):
        """测试记录慢查询"""
        from utils.performance import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        monitor.record_request('/api/slow', 1.0, 200)  # 超过 0.5s 阈值
        
        stats = monitor.get_stats()
        assert stats['slow_queries'] == 1


# ============ 模型测试 ============

class TestUserModel:
    """用户模型测试"""
    
    def test_user_creation(self, client):
        """测试用户创建"""
        from auth import hash_password
        
        user = User(
            username='newuser',
            email='new@test.com',
            password_hash=hash_password('password123')
        )
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.username == 'newuser'
    
    def test_user_to_dict(self, client):
        """测试用户序列化"""
        from auth import hash_password
        
        user = User(
            username='testuser',
            email='test@test.com',
            password_hash=hash_password('password123')
        )
        db.session.add(user)
        db.session.commit()
        
        user_dict = user.to_dict()
        assert user_dict['username'] == 'testuser'
        assert 'email' not in user_dict  # 默认不包含邮箱


class TestProteinModel:
    """蛋白模型测试"""
    
    def test_protein_creation(self, client):
        """测试蛋白创建"""
        protein = Protein(
            name='TEST1',
            family='TEST',
            description='Test description'
        )
        db.session.add(protein)
        db.session.commit()
        
        assert protein.id is not None
        assert protein.name == 'TEST1'
    
    def test_protein_to_dict(self, client, sample_proteins):
        """测试蛋白序列化"""
        protein_dict = sample_proteins[0].to_dict()
        
        assert protein_dict['name'] == 'CIDEA'
        assert protein_dict['family'] == 'CIDE'


# ============ 集成测试 ============

class TestIntegration:
    """集成测试"""
    
    def test_full_user_flow(self, client, sample_proteins):
        """测试完整用户流程"""
        # 1. 注册
        response = client.post('/api/auth/register', json={
            'username': 'flowuser',
            'email': 'flow@test.com',
            'password': 'password123'
        })
        assert response.status_code == 201
        
        # 2. 登录
        response = client.post('/api/auth/login', json={
            'email': 'flow@test.com',
            'password': 'password123'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        headers = {'Authorization': f'Bearer {data["access_token"]}'}
        
        # 3. 获取蛋白列表
        response = client.get('/api/proteins')
        assert response.status_code == 200
        
        # 4. 关注蛋白
        protein_id = sample_proteins[0].id
        response = client.post(f'/api/proteins/{protein_id}/follow', headers=headers)
        assert response.status_code == 201
        
        # 5. 获取关注列表
        response = client.get('/api/user/followed-proteins', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] == 1
        
        # 6. 获取推荐
        response = client.get('/api/recommend/explore?top_k=3')
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
