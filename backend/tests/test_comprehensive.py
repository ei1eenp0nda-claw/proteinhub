"""
ProteinHub Backend Tests - Comprehensive Test Suite
综合测试套件
"""
import pytest
import json
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, Protein, User, Post, ProteinInteraction
from auth import (
    validate_email, validate_password, create_access_token, 
    create_refresh_token, decode_token, AuthError
)
from services.protein_service import ProteinService
from services.search_service import SearchEngine, SearchService
from utils.cache import MemoryCache, Cache
from utils.performance import PerformanceMonitor


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def sample_proteins(client):
    """创建测试蛋白数据"""
    proteins = [
        Protein(name='CIDEA', family='CIDE', description='Cell Death-Inducing DFF45-like Effector A'),
        Protein(name='CIDEB', family='CIDE', description='Cell Death-Inducing DFF45-like Effector B'),
        Protein(name='PLIN1', family='PLIN', description='Perilipin 1'),
        Protein(name='PLIN2', family='PLIN', description='Perilipin 2'),
    ]
    for p in proteins:
        db.session.add(p)
    db.session.commit()
    return proteins


@pytest.fixture
def sample_user(client):
    """创建测试用户"""
    user = User(username='testuser', email='test@example.com', password='password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def auth_headers(sample_user):
    """创建认证请求头"""
    token = create_access_token(sample_user.id)
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def sample_posts(client, sample_proteins):
    """创建测试帖子数据"""
    posts = [
        Post(protein_id=sample_proteins[0].id, title='Post 1', summary='Summary 1'),
        Post(protein_id=sample_proteins[1].id, title='Post 2', summary='Summary 2'),
        Post(protein_id=sample_proteins[0].id, title='Post 3', summary='Summary 3'),
    ]
    for p in posts:
        db.session.add(p)
    db.session.commit()
    return posts


# ============================================================================
# Health Check Tests
# ============================================================================

class TestHealth:
    """健康检查测试"""
    
    def test_health_check_success(self, client):
        """测试健康检查端点正常响应"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'service' in data
        assert 'version' in data


# ============================================================================
# Authentication Tests
# ============================================================================

class TestAuthValidation:
    """认证验证函数测试"""
    
    def test_validate_email_valid(self):
        """测试有效邮箱验证"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            '123@example.com'
        ]
        for email in valid_emails:
            assert validate_email(email) is True, f"{email} should be valid"
    
    def test_validate_email_invalid(self):
        """测试无效邮箱验证"""
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'test@',
            'test@.com',
            '',
            None,
            'test@@example.com'
        ]
        for email in invalid_emails:
            result = validate_email(email) if email is not None else False
            if email is not None:
                assert validate_email(email) is False, f"{email} should be invalid"
    
    def test_validate_password_valid(self):
        """测试有效密码验证"""
        valid_passwords = [
            'password123',
            'SecurePass1',
            'MyP@ssw0rd',
            'a' * 8 + '1'
        ]
        for pwd in valid_passwords:
            is_valid, error = validate_password(pwd)
            assert is_valid is True, f"{pwd} should be valid: {error}"
    
    def test_validate_password_invalid(self):
        """测试无效密码验证"""
        test_cases = [
            ('short1', '密码长度至少为8位'),
            ('password', '密码必须包含至少一个数字'),
            ('12345678', '密码必须包含至少一个字母'),
            ('', '密码长度至少为8位'),
        ]
        for pwd, expected_error in test_cases:
            is_valid, error = validate_password(pwd)
            assert is_valid is False
            assert expected_error in error


class TestTokenManagement:
    """令牌管理测试"""
    
    def test_create_access_token(self, sample_user):
        """测试创建访问令牌"""
        token = create_access_token(sample_user.id)
        assert token is not None
        assert isinstance(token, str)
        
        # 验证令牌内容
        payload = jwt.decode(token, 'proteinhub-secret-key', algorithms=['HS256'])
        assert payload['user_id'] == sample_user.id
        assert payload['token_type'] == 'access'
        assert 'exp' in payload
    
    def test_create_refresh_token(self, sample_user):
        """测试创建刷新令牌"""
        token = create_refresh_token(sample_user.id)
        assert token is not None
        
        payload = jwt.decode(token, 'proteinhub-secret-key', algorithms=['HS256'])
        assert payload['user_id'] == sample_user.id
        assert payload['token_type'] == 'refresh'
    
    def test_decode_token_valid(self, sample_user):
        """测试解码有效令牌"""
        token = create_access_token(sample_user.id)
        payload = decode_token(token, token_type='access')
        assert payload['user_id'] == sample_user.id
    
    def test_decode_token_invalid_type(self, sample_user):
        """测试令牌类型不匹配"""
        access_token = create_access_token(sample_user.id)
        with pytest.raises(AuthError) as exc_info:
            decode_token(access_token, token_type='refresh')
        assert exc_info.value.status_code == 401


class TestAuthRoutes:
    """认证路由测试"""
    
    def test_register_success(self, client):
        """测试成功注册"""
        response = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'user_id' in data
        assert data['message'] == '注册成功'
    
    def test_register_duplicate_username(self, client, sample_user):
        """测试重复用户名注册"""
        response = client.post('/api/auth/register', json={
            'username': sample_user.username,
            'email': 'different@example.com',
            'password': 'password123'
        })
        assert response.status_code == 409
        data = json.loads(response.data)
        assert '用户名已被使用' in data['error']
    
    def test_register_duplicate_email(self, client, sample_user):
        """测试重复邮箱注册"""
        response = client.post('/api/auth/register', json={
            'username': 'different',
            'email': sample_user.email,
            'password': 'password123'
        })
        assert response.status_code == 409
        data = json.loads(response.data)
        assert '邮箱已被注册' in data['error']
    
    def test_register_missing_fields(self, client):
        """测试缺少字段的注册"""
        # 缺少用户名
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        assert response.status_code == 400
        
        # 空请求体
        response = client.post('/api/auth/register', json={})
        assert response.status_code == 400
    
    def test_login_success(self, client, sample_user):
        """测试成功登录"""
        response = client.post('/api/auth/login', json={
            'email': sample_user.email,
            'password': 'password123'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['email'] == sample_user.email
    
    def test_login_invalid_credentials(self, client, sample_user):
        """测试无效凭证登录"""
        response = client.post('/api/auth/login', json={
            'email': sample_user.email,
            'password': 'wrongpassword'
        })
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """测试不存在的用户登录"""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })
        assert response.status_code == 401
    
    def test_get_current_user(self, client, sample_user, auth_headers):
        """测试获取当前用户信息"""
        response = client.get('/api/auth/me', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == sample_user.id
        assert data['username'] == sample_user.username
    
    def test_get_current_user_no_token(self, client):
        """测试无令牌获取用户信息"""
        response = client.get('/api/auth/me')
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client):
        """测试无效令牌"""
        headers = {'Authorization': 'Bearer invalid_token'}
        response = client.get('/api/auth/me', headers=headers)
        assert response.status_code == 401


# ============================================================================
# Protein API Tests
# ============================================================================

class TestProteinRoutes:
    """蛋白API路由测试"""
    
    def test_get_proteins_list(self, client, sample_proteins):
        """测试获取蛋白列表"""
        response = client.get('/api/proteins')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == len(sample_proteins)
    
    def test_get_proteins_with_family_filter(self, client, sample_proteins):
        """测试按家族筛选蛋白"""
        response = client.get('/api/proteins?family=CIDE')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        for p in data:
            assert p['family'] == 'CIDE'
    
    def test_get_protein_detail(self, client, sample_proteins):
        """测试获取单个蛋白详情"""
        protein = sample_proteins[0]
        response = client.get(f'/api/proteins/{protein.id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == protein.name
        assert data['family'] == protein.family
    
    def test_get_protein_not_found(self, client):
        """测试获取不存在的蛋白"""
        response = client.get('/api/proteins/99999')
        assert response.status_code == 404
    
    def test_get_protein_profile(self, client, sample_proteins, sample_posts):
        """测试获取蛋白主页"""
        protein = sample_proteins[0]
        response = client.get(f'/api/proteins/{protein.id}/profile')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'protein' in data
        assert 'biography' in data
        assert 'posts' in data
        assert data['protein']['name'] == protein.name


# ============================================================================
# Feed API Tests
# ============================================================================

class TestFeedRoutes:
    """Feed API路由测试"""
    
    def test_get_feed(self, client, sample_posts):
        """测试获取Feed"""
        response = client.get('/api/feed')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_create_post_unauthorized(self, client):
        """测试未授权创建帖子"""
        response = client.post('/api/posts', json={
            'protein_id': 1,
            'title': 'Test Post'
        })
        assert response.status_code == 401
    
    def test_create_post_authorized(self, client, sample_user, sample_proteins, auth_headers):
        """测试授权创建帖子"""
        response = client.post('/api/posts', 
            json={
                'protein_id': sample_proteins[0].id,
                'title': 'New Post',
                'summary': 'Post summary'
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['title'] == 'New Post'


# ============================================================================
# Follow API Tests
# ============================================================================

class TestFollowRoutes:
    """关注功能测试"""
    
    def test_follow_protein(self, client, sample_user, sample_proteins, auth_headers):
        """测试关注蛋白"""
        protein = sample_proteins[0]
        response = client.post(
            f'/api/proteins/{protein.id}/follow',
            headers=auth_headers
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == '关注成功'
    
    def test_follow_nonexistent_protein(self, client, sample_user, auth_headers):
        """测试关注不存在的蛋白"""
        response = client.post('/api/proteins/99999/follow', headers=auth_headers)
        assert response.status_code == 404
    
    def test_follow_already_following(self, client, sample_user, sample_proteins, auth_headers):
        """测试重复关注"""
        protein = sample_proteins[0]
        # 第一次关注
        client.post(f'/api/proteins/{protein.id}/follow', headers=auth_headers)
        # 第二次关注
        response = client.post(f'/api/proteins/{protein.id}/follow', headers=auth_headers)
        # 应该返回200，表示已经关注
        assert response.status_code == 200
    
    def test_unfollow_protein(self, client, sample_user, sample_proteins, auth_headers):
        """测试取消关注"""
        protein = sample_proteins[0]
        # 先关注
        client.post(f'/api/proteins/{protein.id}/follow', headers=auth_headers)
        # 再取消关注
        response = client.delete(f'/api/proteins/{protein.id}/unfollow', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '取消关注成功' in data['message']
    
    def test_get_followed_proteins(self, client, sample_user, sample_proteins, auth_headers):
        """测试获取关注列表"""
        # 关注几个蛋白
        for protein in sample_proteins[:2]:
            client.post(f'/api/proteins/{protein.id}/follow', headers=auth_headers)
        
        response = client.get('/api/user/followed-proteins', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] == 2
    
    def test_check_follow_status(self, client, sample_user, sample_proteins, auth_headers):
        """测试检查关注状态"""
        protein = sample_proteins[0]
        response = client.get(f'/api/proteins/{protein.id}/is-followed', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['is_followed'] is False
        assert data['protein_id'] == protein.id


# ============================================================================
# Search API Tests
# ============================================================================

class TestSearchRoutes:
    """搜索API测试"""
    
    def test_search_suggestions(self, client, sample_proteins):
        """测试搜索建议"""
        response = client.get('/api/search/suggestions?q=CID&limit=5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'suggestions' in data
    
    def test_global_search(self, client, sample_proteins):
        """测试全局搜索"""
        response = client.get('/api/search?q=CIDEA')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'proteins' in data
        assert 'posts' in data
    
    def test_search_proteins(self, client, sample_proteins):
        """测试蛋白搜索"""
        response = client.get('/api/search/proteins?q=CIDEA')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'items' in data
    
    def test_search_empty_query(self, client):
        """测试空搜索查询"""
        response = client.get('/api/search?q=')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['proteins']['total'] == 0


# ============================================================================
# Recommendation API Tests
# ============================================================================

class TestRecommendationRoutes:
    """推荐API测试"""
    
    def test_cold_start_recommendation(self, client, sample_proteins):
        """测试冷启动推荐"""
        response = client.post('/api/recommend/cold-start', json={
            'selected_families': ['CIDE'],
            'top_k': 5
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendations' in data
        assert 'strategy' in data
    
    def test_explore_recommendation(self, client, sample_proteins):
        """测试探索推荐"""
        response = client.get('/api/recommend/explore?top_k=5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendations' in data
    
    def test_similar_proteins_recommendation(self, client, sample_proteins):
        """测试相似蛋白推荐"""
        protein = sample_proteins[0]
        response = client.get(f'/api/recommend/by-protein/{protein.id}?top_k=5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendations' in data
    
    def test_get_model_status(self, client):
        """测试获取模型状态"""
        response = client.get('/api/recommend/model/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'model_type' in data


# ============================================================================
# Service Layer Tests
# ============================================================================

class TestProteinService:
    """蛋白服务层测试"""
    
    def test_get_proteins_pagination(self, client, sample_proteins):
        """测试蛋白分页"""
        with app.app_context():
            result = ProteinService.get_proteins(page=1, per_page=2)
            assert len(result['items']) == 2
            assert result['total'] == 4
            assert result['pages'] == 2
    
    def test_get_protein_by_id(self, client, sample_proteins):
        """测试根据ID获取蛋白"""
        with app.app_context():
            protein = ProteinService.get_protein_by_id(sample_proteins[0].id)
            assert protein is not None
            assert protein.name == 'CIDEA'
    
    def test_get_protein_by_id_not_found(self, client):
        """测试获取不存在的蛋白"""
        with app.app_context():
            protein = ProteinService.get_protein_by_id(99999)
            assert protein is None
    
    def test_get_protein_profile(self, client, sample_proteins):
        """测试获取蛋白主页"""
        with app.app_context():
            profile = ProteinService.get_protein_profile(sample_proteins[0].id)
            assert profile is not None
            assert 'protein' in profile
            assert 'biography' in profile
            assert 'posts' in profile
            assert 'interactions' in profile
    
    def test_create_protein(self, client):
        """测试创建蛋白"""
        with app.app_context():
            protein, error = ProteinService.create_protein(
                name='NEWPROTEIN',
                family='NEWFAMILY',
                description='Test description'
            )
            assert protein is not None
            assert error is None
            assert protein.name == 'NEWPROTEIN'
    
    def test_create_duplicate_protein(self, client, sample_proteins):
        """测试创建重复蛋白"""
        with app.app_context():
            protein, error = ProteinService.create_protein(name='CIDEA')
            assert protein is None
            assert error is not None


# ============================================================================
# Utility Tests
# ============================================================================

class TestCache:
    """缓存工具测试"""
    
    def test_memory_cache_basic(self):
        """测试内存缓存基本操作"""
        cache = MemoryCache()
        
        # 设置值
        cache.set('key1', 'value1', expire=300)
        
        # 获取值
        value = cache.get('key1')
        assert value == 'value1'
    
    def test_memory_cache_expiration(self):
        """测试缓存过期"""
        cache = MemoryCache()
        cache.set('key1', 'value1', expire=0)  # 立即过期
        
        value = cache.get('key1')
        assert value is None
    
    def test_memory_cache_delete(self):
        """测试缓存删除"""
        cache = MemoryCache()
        cache.set('key1', 'value1')
        cache.delete('key1')
        
        value = cache.get('key1')
        assert value is None
    
    def test_memory_cache_clear(self):
        """测试清空缓存"""
        cache = MemoryCache()
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.clear()
        
        assert cache.get('key1') is None
        assert cache.get('key2') is None


class TestPerformanceMonitor:
    """性能监控工具测试"""
    
    def test_record_request(self):
        """测试记录请求"""
        monitor = PerformanceMonitor()
        monitor.record_request('/api/test', 0.1, 200)
        
        assert monitor.request_count == 1
        assert len(monitor.metrics['requests']) == 1
    
    def test_record_slow_request(self):
        """测试记录慢请求"""
        monitor = PerformanceMonitor()
        monitor.record_request('/api/slow', 0.6, 200)  # 超过500ms
        
        assert len(monitor.slow_queries) == 1
    
    def test_get_stats(self):
        """测试获取统计信息"""
        monitor = PerformanceMonitor()
        monitor.record_request('/api/test', 0.1, 200)
        monitor.record_request('/api/test', 0.2, 500)
        
        stats = monitor.get_stats()
        assert stats['total_requests'] == 2
        assert stats['error_count'] == 1
        assert 'avg_response_time' in stats
    
    def test_get_slow_queries(self):
        """测试获取慢查询"""
        monitor = PerformanceMonitor()
        monitor.record_request('/api/slow1', 0.6, 200)
        monitor.record_request('/api/slow2', 0.8, 200)
        
        slow_queries = monitor.get_slow_queries(limit=10)
        assert len(slow_queries) == 2
        # 应该按耗时排序
        assert slow_queries[0]['duration'] >= slow_queries[1]['duration']


# ============================================================================
# Admin API Tests
# ============================================================================

class TestAdminRoutes:
    """管理后台API测试"""
    
    def test_admin_stats_unauthorized(self, client):
        """测试未授权访问统计数据"""
        response = client.get('/api/admin/stats')
        assert response.status_code == 401
    
    def test_admin_stats_authorized(self, client):
        """测试授权访问统计数据"""
        # 创建管理员用户
        admin = User(username='admin', email='admin@example.com', password='admin123')
        db.session.add(admin)
        db.session.commit()
        
        token = create_access_token(admin.id)
        headers = {'Authorization': f'Bearer {token}'}
        
        response = client.get('/api/admin/stats', headers=headers)
        # 管理员权限检查（当前实现简单检查id=1或username=admin）
        if admin.id == 1 or admin.username == 'admin':
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'users' in data
            assert 'proteins' in data


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """错误处理测试"""
    
    def test_404_error(self, client):
        """测试404错误处理"""
        response = client.get('/api/nonexistent-endpoint')
        assert response.status_code == 404
    
    def test_invalid_json_body(self, client):
        """测试无效JSON请求体"""
        response = client.post('/api/auth/login',
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_method_not_allowed(self, client):
        """测试不允许的方法"""
        response = client.delete('/api/health')
        assert response.status_code == 405


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================

class TestEdgeCases:
    """边界情况和异常测试"""
    
    def test_very_long_search_query(self, client):
        """测试超长搜索查询"""
        long_query = 'a' * 1000
        response = client.get(f'/api/search?q={long_query}')
        # 应该正常处理，不崩溃
        assert response.status_code in [200, 400]
    
    def test_special_characters_in_search(self, client):
        """测试搜索中的特殊字符"""
        special_queries = ['test%20query', 'test<script>', 'test"quote"', 'test\\backslash']
        for query in special_queries:
            response = client.get(f'/api/search?q={query}')
            assert response.status_code in [200, 400]
    
    def test_negative_pagination(self, client):
        """测试负分页参数"""
        response = client.get('/api/feed?page=-1')
        # 应该返回第一页或400错误
        assert response.status_code in [200, 400]
    
    def test_zero_per_page(self, client):
        """测试每页0条记录"""
        response = client.get('/api/feed?per_page=0')
        # 应该返回默认分页或400错误
        assert response.status_code in [200, 400]
    
    def test_very_large_per_page(self, client):
        """测试非常大的每页数量"""
        response = client.get('/api/feed?per_page=10000')
        # 应该限制最大数量或返回400
        assert response.status_code in [200, 400]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
