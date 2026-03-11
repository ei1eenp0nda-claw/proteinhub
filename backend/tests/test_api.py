"""
ProteinHub Tests
测试套件
"""
import pytest
import json
from app import app, db, Protein, User, Post


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
def sample_proteins(client):
    """创建测试蛋白数据"""
    proteins = [
        Protein(name='CIDEA', family='CIDE', description='Test protein A'),
        Protein(name='PLIN1', family='PLIN', description='Test protein B'),
    ]
    for p in proteins:
        db.session.add(p)
    db.session.commit()
    return proteins


class TestHealth:
    """健康检查测试"""
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'


class TestAuth:
    """认证测试"""
    
    def test_register_success(self, client):
        """测试成功注册"""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'user_id' in data
        assert data['message'] == '注册成功'
    
    def test_register_duplicate_email(self, client):
        """测试重复邮箱注册"""
        # 先注册一个用户
        client.post('/api/auth/register', json={
            'username': 'user1',
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # 再用相同邮箱注册
        response = client.post('/api/auth/register', json={
            'username': 'user2',
            'email': 'test@example.com',
            'password': 'password123'
        })
        assert response.status_code == 409
        data = json.loads(response.data)
        assert '邮箱已被注册' in data['error']
    
    def test_register_invalid_email(self, client):
        """测试无效邮箱格式"""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'password123'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert '邮箱格式无效' in data['error']
    
    def test_register_weak_password(self, client):
        """测试弱密码"""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123'  # 太短的密码
        })
        assert response.status_code == 400
    
    def test_login_success(self, client):
        """测试成功登录"""
        # 先注册
        client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # 再登录
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    def test_login_wrong_password(self, client):
        """测试错误密码"""
        # 先注册
        client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # 用错误密码登录
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401


class TestProtein:
    """蛋白API测试"""
    
    def test_get_proteins(self, client, sample_proteins):
        """测试获取蛋白列表"""
        response = client.get('/api/proteins')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
    
    def test_get_protein_by_id(self, client, sample_proteins):
        """测试获取单个蛋白"""
        response = client.get('/api/proteins/1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'CIDEA'
    
    def test_get_protein_not_found(self, client):
        """测试获取不存在的蛋白"""
        response = client.get('/api/proteins/999')
        assert response.status_code == 404


class TestFeed:
    """Feed API测试"""
    
    def test_get_feed_empty(self, client):
        """测试空Feed"""
        response = client.get('/api/feed')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 0
    
    def test_get_feed_with_posts(self, client, sample_proteins):
        """测试有帖子的Feed"""
        # 创建一个帖子
        post = Post(
            protein_id=sample_proteins[0].id,
            title='Test Post',
            summary='Test summary'
        )
        db.session.add(post)
        db.session.commit()
        
        response = client.get('/api/feed')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1


class TestRecommendation:
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
    
    def test_explore_recommendation(self, client, sample_proteins):
        """测试探索推荐"""
        response = client.get('/api/recommend/explore?top_k=5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendations' in data
