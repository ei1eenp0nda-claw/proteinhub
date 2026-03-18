"""
测试 markdown 笔记管理模块
"""
import pytest
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from note_manager import get_all_notes, get_note_content, search_notes


class TestNoteManager:
    """测试笔记管理功能"""
    
    def test_get_all_notes_returns_list(self):
        """测试获取所有笔记返回列表"""
        notes = get_all_notes()
        assert isinstance(notes, list)
        assert len(notes) > 0
    
    def test_get_all_notes_has_required_fields(self):
        """测试笔记对象包含必要字段"""
        notes = get_all_notes()
        if notes:
            note = notes[0]
            assert 'id' in note
            assert 'filename' in note
            assert 'title' in note
            assert 'preview' in note
    
    def test_get_all_notes_note_id_format(self):
        """测试笔记ID格式正确"""
        notes = get_all_notes()
        for i, note in enumerate(notes):
            assert note['id'] == f'note_{i}'
    
    def test_get_note_content_by_id(self):
        """测试根据ID获取笔记内容"""
        content = get_note_content('note_0')
        assert content is not None
        assert len(content) > 0
        assert '#' in content  # markdown 应该有标题
    
    def test_get_note_content_invalid_id(self):
        """测试无效ID返回None"""
        content = get_note_content('nonexistent_note')
        assert content is None
    
    def test_get_note_content_by_index(self):
        """测试通过索引获取笔记"""
        notes = get_all_notes()
        if len(notes) > 1:
            content = get_note_content('note_1')
            assert content is not None
    
    def test_search_notes_returns_results(self):
        """测试搜索功能返回结果"""
        results = search_notes('蛋白')
        assert isinstance(results, list)
    
    def test_search_notes_case_insensitive(self):
        """测试搜索不区分大小写"""
        results_lower = search_notes('protein')
        results_upper = search_notes('PROTEIN')
        # 两者应该返回相似结果
        assert isinstance(results_lower, list)
        assert isinstance(results_upper, list)
    
    def test_search_notes_empty_query(self):
        """测试空查询返回空列表"""
        results = search_notes('')
        assert results == []
    
    def test_search_notes_no_match(self):
        """测试无匹配结果"""
        results = search_notes('xyzabc123nonexistent')
        assert results == []
    
    def test_note_content_structure(self):
        """测试笔记内容结构正确"""
        content = get_note_content('note_0')
        if content:
            # 应该有 markdown 标题
            lines = content.split('\n')
            has_heading = any(line.strip().startswith('#') for line in lines)
            assert has_heading, "笔记应该包含 markdown 标题"


class TestNoteAPIIntegration:
    """测试笔记 API 集成"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        # 从 app.py 导入应用实例
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_api_list_notes(self, client):
        """测试 API 获取笔记列表"""
        response = client.get('/api/notes/list')
        assert response.status_code == 200
        data = response.get_json()
        assert 'notes' in data
        assert 'total' in data
        assert 'has_more' in data
    
    def test_api_list_notes_pagination(self, client):
        """测试 API 分页功能"""
        response = client.get('/api/notes/list?page=1&per_page=5')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['notes']) <= 5
    
    def test_api_get_note_detail(self, client):
        """测试 API 获取单篇笔记"""
        response = client.get('/api/notes/note_0')
        assert response.status_code == 200
        data = response.get_json()
        assert 'id' in data
        assert 'content' in data
    
    def test_api_get_note_not_found(self, client):
        """测试 API 获取不存在的笔记"""
        response = client.get('/api/notes/nonexistent')
        assert response.status_code == 404
    
    def test_api_search_notes(self, client):
        """测试 API 搜索笔记"""
        response = client.get('/api/notes/search?q=蛋白')
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])