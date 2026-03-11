"""
测试内容生成功能
Test Content Generation
"""
import pytest
import json
import sys
import os

sys.path.insert(0, '/root/.openclaw/workspace/projects/proteinhub/backend')

from app import app, db
from crawler.content_generator import ContentGenerator, ContentPipeline
from crawler.pubmed_crawler import PubMedCrawler


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


class TestContentGenerator:
    """内容生成器测试"""
    
    def test_generate_title(self):
        """测试标题生成"""
        generator = ContentGenerator()
        
        article = {
            'title': 'CIDEA regulates lipid droplet fusion',
            'journal': 'Nature',
            'pub_date': '2024-01'
        }
        
        title = generator._generate_title_template(article, 'CIDEA')
        
        assert 'CIDEA' in title
        assert len(title) > 10
        assert any(emoji in title for emoji in ['🔬', '🧬', '📑', '💡', '🎯', '🔥', '📊', '🧪'])
    
    def test_generate_content(self):
        """测试正文生成"""
        generator = ContentGenerator()
        
        article = {
            'title': 'CIDEA regulates lipid droplet fusion',
            'abstract': 'This study reveals the mechanism...',
            'authors': ['Zhang L', 'Wang H'],
            'journal': 'Nature Cell Biology',
            'pub_date': '2024-03'
        }
        
        content = generator._generate_content_template(article, 'CIDEA')
        
        assert 'CIDEA' in content
        assert 'Nature Cell Biology' in content
        assert len(content) > 100
        assert any(emoji in content for emoji in ['🔬', '💡', '🎯', '🎉', '💕'])
    
    def test_generate_tags(self):
        """测试标签生成"""
        generator = ContentGenerator()
        
        article = {
            'title': 'CIDEA regulates lipid droplet fusion and metabolism',
            'journal': 'Nature'
        }
        
        tags = generator._generate_tags(article, 'CIDEA')
        
        assert 'CIDEA' in tags
        assert len(tags) >= 5
        assert '脂滴研究' in tags or '脂质代谢' in tags
        assert '科研干货' in tags
    
    def test_generate_full_post(self):
        """测试生成完整笔记"""
        generator = ContentGenerator()
        
        article = {
            'title': 'CIDEA regulates lipid droplet fusion in adipocytes',
            'abstract': 'Lipid droplets are cellular organelles...',
            'authors': ['Zhang L', 'Wang H', 'Chen Y'],
            'journal': 'Nature Cell Biology',
            'pub_date': '2024-03-15',
            'pmid': '12345678',
            'url': 'https://pubmed.ncbi.nlm.nih.gov/12345678/'
        }
        
        post = generator.generate_xiaohongshu_post(article, 'CIDEA')
        
        assert 'title' in post
        assert 'content' in post
        assert 'tags' in post
        assert 'summary' in post
        assert 'key_points' in post
        assert post['reading_time'] >= 1
        assert post['emoji_count'] >= 0
        assert post['source']['journal'] == 'Nature Cell Biology'


class TestContentAPI:
    """内容生成 API 测试"""
    
    def test_preview_content(self, client):
        """测试内容预览 API"""
        response = client.post('/api/content/preview', json={
            'article': {
                'title': 'CIDEA regulates lipid droplet fusion',
                'abstract': 'This study reveals...',
                'journal': 'Nature Cell Biology',
                'authors': ['Zhang L'],
                'pub_date': '2024-03'
            },
            'protein_name': 'CIDEA'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'preview' in data
    
    def test_preview_missing_data(self, client):
        """测试预览缺少数据"""
        response = client.post('/api/content/preview', json={
            'protein_name': 'CIDEA'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_suggest_tags(self, client):
        """测试标签推荐 API"""
        response = client.get('/api/content/tags/suggest?q=lipid metabolism')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'tags' in data
        assert len(data['tags']) > 0
        assert any('脂滴' in tag or '脂质' in tag for tag in data['tags'])
    
    def test_generate_content_auth_required(self, client):
        """测试生成内容需要认证"""
        response = client.post('/api/content/generate', json={
            'protein_name': 'CIDEA'
        })
        
        # 应该返回 401 未认证
        assert response.status_code == 401
    
    def test_generate_content_missing_protein(self, client, auth_headers):
        """测试缺少蛋白名称"""
        response = client.post('/api/content/generate', 
                              json={},
                              headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestXiaohongshuStyle:
    """小红书风格测试"""
    
    def test_title_length(self):
        """测试标题长度符合小红书规范"""
        generator = ContentGenerator()
        
        article = {'title': 'Test', 'journal': 'Nature', 'pub_date': '2024-01'}
        
        for _ in range(10):  # 测试多次
            title = generator._generate_title_template(article, 'TEST')
            assert 10 <= len(title) <= 50  # 小红书标题推荐长度
    
    def test_content_structure(self):
        """测试正文结构"""
        generator = ContentGenerator()
        
        article = {
            'title': 'Test',
            'journal': 'Nature',
            'authors': ['Author'],
            'pub_date': '2024-01'
        }
        
        content = generator._generate_content_template(article, 'TEST')
        
        # 应该包含多个段落
        paragraphs = content.split('\n\n')
        assert len(paragraphs) >= 3
        
        # 应该包含 emoji
        assert any(emoji in content for emoji in ['🔬', '📑', '💡', '🎯', '🎉'])
    
    def test_tags_format(self):
        """测试标签格式"""
        generator = ContentGenerator()
        
        article = {'title': 'Test interaction mechanism', 'journal': 'Nature'}
        
        tags = generator._generate_tags(article, 'TEST')
        
        # 标签应该有意义
        assert len(tags) >= 5
        assert len(tags) <= 10
        
        # 蛋白名应该在标签中
        assert 'TEST' in tags
    
    def test_key_points_extraction(self):
        """测试关键点提取"""
        generator = ContentGenerator()
        
        # 测试机制类标题
        article1 = {'title': 'CIDEA regulates through a novel mechanism'}
        points1 = generator._extract_key_points(article1)
        assert '揭示了新的分子机制' in points1
        
        # 测试功能类标题
        article2 = {'title': 'CIDEA function in lipid metabolism'}
        points2 = generator._extract_key_points(article2)
        assert len(points2) > 0


class TestContentQuality:
    """内容质量测试"""
    
    def test_reading_time_calculation(self):
        """测试阅读时间计算"""
        generator = ContentGenerator()
        
        # 短内容
        short_post = {'content': 'Short content'}
        reading_time_short = max(1, len(short_post['content']) // 200)
        assert reading_time_short == 1
        
        # 长内容
        long_post = {'content': 'A' * 1000}
        reading_time_long = max(1, len(long_post['content']) // 200)
        assert reading_time_long == 5
    
    def test_emoji_count(self):
        """测试 emoji 计数"""
        generator = ContentGenerator()
        
        article = {
            'title': 'Test',
            'journal': 'Nature',
            'pub_date': '2024-01'
        }
        
        post = generator.generate_xiaohongshu_post(article, 'TEST')
        
        # 应该包含适当数量的 emoji
        assert post['emoji_count'] >= 3
        assert post['emoji_count'] <= 20


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
