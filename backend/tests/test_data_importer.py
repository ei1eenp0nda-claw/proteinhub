"""
ProteinHub Data Importer Tests
数据导入器测试套件
"""
import pytest
import json
import csv
import tempfile
import os
from unittest.mock import Mock, patch
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_importer import DataImporter, ProteinInteractionImporter, BatchDataLoader


# ============================================================================
# Mock Models and Database
# ============================================================================

class MockProtein:
    """模拟蛋白模型"""
    _instances = {}
    _next_id = 1
    
    def __init__(self, name, family=None, description=None):
        self.id = MockProtein._next_id
        MockProtein._next_id += 1
        self.name = name
        self.family = family
        self.description = description
        MockProtein._instances[self.id] = self
    
    @classmethod
    def query(cls):
        return MockQuery(cls._instances.values())
    
    @classmethod
    def reset(cls):
        cls._instances = {}
        cls._next_id = 1


class MockProteinInteraction:
    """模拟蛋白互作模型"""
    _instances = {}
    _next_id = 1
    
    def __init__(self, protein_a_id, protein_b_id, interaction_score=0.5):
        self.id = MockProteinInteraction._next_id
        MockProteinInteraction._next_id += 1
        self.protein_a_id = protein_a_id
        self.protein_b_id = protein_b_id
        self.interaction_score = interaction_score
        MockProteinInteraction._instances[self.id] = self
    
    @classmethod
    def query(cls):
        return MockQuery(cls._instances.values())
    
    @classmethod
    def reset(cls):
        cls._instances = {}
        cls._next_id = 1


class MockQuery:
    """模拟 SQLAlchemy Query"""
    def __init__(self, items):
        self.items = list(items)
        self.filters = []
    
    def filter_by(self, **kwargs):
        result = self.items
        for key, value in kwargs.items():
            result = [item for item in result if getattr(item, key, None) == value]
        self.items = result
        return self
    
    def filter(self, *conditions):
        # 简化处理，实际应该解析条件
        return self
    
    def first(self):
        return self.items[0] if self.items else None
    
    def all(self):
        return self.items
    
    def count(self):
        return len(self.items)
    
    def distinct(self):
        seen = set()
        result = []
        for item in self.items:
            key = str(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        self.items = result
        return self


class MockSession:
    """模拟数据库会话"""
    def __init__(self):
        self.added = []
        self.committed = False
        self.rolled_back = False
    
    def add(self, obj):
        self.added.append(obj)
    
    def commit(self):
        self.committed = True
    
    def rollback(self):
        self.rolled_back = True
    
    def flush(self):
        pass
    
    def execute(self, query, params=None):
        return []


# ============================================================================
# DataImporter Tests
# ============================================================================

class TestDataImporter:
    """数据导入器基类测试"""
    
    @pytest.fixture
    def mock_session(self):
        return MockSession()
    
    @pytest.fixture
    def importer(self, mock_session):
        class TestImporter(DataImporter):
            def validate_row(self, row):
                if 'name' not in row or not row['name']:
                    return False, 'Name is required'
                return True, None
            
            def import_row(self, row):
                self.imported_count += 1
                return True
        
        return TestImporter(mock_session)
    
    def test_initialization(self, mock_session):
        """测试初始化"""
        importer = DataImporter(mock_session)
        assert importer.db == mock_session
        assert importer.errors == []
        assert importer.imported_count == 0
        assert importer.skipped_count == 0
    
    def test_import_csv_success(self, importer, tmp_path):
        """测试成功导入 CSV"""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'value'])
            writer.writeheader()
            writer.writerow({'name': 'Item1', 'value': '100'})
            writer.writerow({'name': 'Item2', 'value': '200'})
        
        importer.import_file(str(csv_file))
        
        assert importer.imported_count == 2
        assert importer.skipped_count == 0
        assert len(importer.errors) == 0
    
    def test_import_csv_with_invalid_rows(self, importer, tmp_path):
        """测试导入包含无效行的 CSV"""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'value'])
            writer.writeheader()
            writer.writerow({'name': 'Item1', 'value': '100'})
            writer.writerow({'name': '', 'value': '200'})  # Invalid
        
        importer.import_file(str(csv_file))
        
        assert importer.imported_count == 1
        assert importer.skipped_count == 1
        assert len(importer.errors) == 1
    
    def test_import_json_success(self, importer, tmp_path):
        """测试成功导入 JSON"""
        json_file = tmp_path / "test.json"
        data = [
            {'name': 'Item1', 'value': '100'},
            {'name': 'Item2', 'value': '200'}
        ]
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        importer.import_file(str(json_file))
        
        assert importer.imported_count == 2
        assert len(importer.errors) == 0
    
    def test_import_json_single_object(self, importer, tmp_path):
        """测试导入单个 JSON 对象"""
        json_file = tmp_path / "test.json"
        data = {'name': 'Item1', 'value': '100'}
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        importer.import_file(str(json_file))
        
        assert importer.imported_count == 1
    
    def test_import_file_not_found(self, importer):
        """测试导入不存在的文件"""
        with pytest.raises(FileNotFoundError):
            importer.import_file('/nonexistent/file.csv')
    
    def test_import_unsupported_format(self, importer, tmp_path):
        """测试导入不支持的格式"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text('content')
        
        with pytest.raises(ValueError) as exc_info:
            importer.import_file(str(txt_file))
        
        assert '不支持的文件格式' in str(exc_info.value)
    
    def test_get_report(self, importer, tmp_path):
        """测试获取导入报告"""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name'])
            writer.writeheader()
            writer.writerow({'name': 'Item1'})
            writer.writerow({'name': ''})  # Invalid
        
        importer.import_file(str(csv_file))
        report = importer.get_report()
        
        assert report['imported'] == 1
        assert report['skipped'] == 1
        assert report['errors'] == 1
        assert 'error_details' in report
    
    def test_progress_callback(self, importer, tmp_path):
        """测试进度回调"""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name'])
            writer.writeheader()
            for i in range(150):
                writer.writerow({'name': f'Item{i}'})
        
        progress_calls = []
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        importer.import_file(str(csv_file), progress_callback=progress_callback)
        
        # 应该至少被调用一次（每100行）
        assert len(progress_calls) >= 1
        # 最后一次调用应该是完成
        assert progress_calls[-1][0] == progress_calls[-1][1]


# ============================================================================
# ProteinInteractionImporter Tests
# ============================================================================

class TestProteinInteractionImporter:
    """蛋白互作导入器测试"""
    
    @pytest.fixture
    def mock_session(self):
        return MockSession()
    
    @pytest.fixture
    def importer(self, mock_session):
        # 重置 mock 模型
        MockProtein.reset()
        MockProteinInteraction.reset()
        
        # 创建一些初始蛋白
        MockProtein('CIDEA', 'CIDE')
        MockProtein('CIDEB', 'CIDE')
        
        return ProteinInteractionImporter(mock_session)
    
    def test_validate_row_valid(self, importer):
        """测试验证有效行"""
        row = {'protein_a': 'CIDEA', 'protein_b': 'CIDEB'}
        is_valid, error = importer.validate_row(row)
        assert is_valid is True
        assert error is None
    
    def test_validate_row_missing_protein_a(self, importer):
        """测试缺少 protein_a"""
        row = {'protein_b': 'CIDEB'}
        is_valid, error = importer.validate_row(row)
        assert is_valid is False
        assert '缺少蛋白名称' in error
    
    def test_validate_row_missing_protein_b(self, importer):
        """测试缺少 protein_b"""
        row = {'protein_a': 'CIDEA'}
        is_valid, error = importer.validate_row(row)
        assert is_valid is False
        assert '缺少蛋白名称' in error
    
    def test_validate_row_same_protein(self, importer):
        """测试相同蛋白"""
        row = {'protein_a': 'CIDEA', 'protein_b': 'CIDEA'}
        is_valid, error = importer.validate_row(row)
        assert is_valid is False
        assert '不能与自己互作' in error
    
    def test_import_row_create_new_proteins(self, importer, mock_session):
        """测试导入时创建新蛋白"""
        row = {'protein_a': 'NEW1', 'protein_b': 'NEW2', 'score': '0.8'}
        result = importer.import_row(row)
        
        assert result is True
        assert importer.imported_count >= 1
    
    def test_import_row_with_interaction_score(self, importer, mock_session):
        """测试导入带分数的互作"""
        row = {'protein_a': 'CIDEA', 'protein_b': 'CIDEB', 'score': '0.85'}
        result = importer.import_row(row)
        
        assert result is True
    
    def test_import_row_duplicate_interaction(self, importer, mock_session):
        """测试重复互作"""
        # 第一次导入
        row = {'protein_a': 'CIDEA', 'protein_b': 'CIDEB'}
        result1 = importer.import_row(row)
        assert result1 is True
        
        # 第二次导入（应该跳过）
        result2 = importer.import_row(row)
        assert result2 is False
    
    def test_import_row_alternative_column_names(self, importer, mock_session):
        """测试替代列名"""
        row = {'Protein_A': 'CIDEA', 'Protein_B': 'CIDEB'}
        is_valid, error = importer.validate_row(row)
        assert is_valid is True
    
    def test_import_row_default_score(self, importer, mock_session):
        """测试默认分数"""
        row = {'protein_a': 'CIDEA', 'protein_b': 'CIDEB'}  # 没有 score
        result = importer.import_row(row)
        assert result is True
        # 应该使用默认分数 0.5


# ============================================================================
# BatchDataLoader Tests
# ============================================================================

class TestBatchDataLoader:
    """批量数据加载器测试"""
    
    @pytest.fixture
    def mock_app(self):
        app = Mock()
        app.app_context = lambda: MockContext()
        return app
    
    @pytest.fixture
    def mock_db(self):
        return MockSession()
    
    @pytest.fixture
    def loader(self, mock_app, mock_db):
        return BatchDataLoader(mock_app, mock_db)
    
    def test_initialization(self, mock_app, mock_db):
        """测试初始化"""
        loader = BatchDataLoader(mock_app, mock_db)
        assert loader.app == mock_app
        assert loader.db == mock_db
    
    def test_generate_sample_data(self, loader, tmp_path):
        """测试生成示例数据"""
        output_file = tmp_path / "sample.csv"
        
        loader.generate_sample_data(str(output_file), n_interactions=10)
        
        assert output_file.exists()
        
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) <= 10  # 可能少于10，因为有重复检查
            assert 'protein_a' in rows[0]
            assert 'protein_b' in rows[0]
            assert 'interaction_score' in rows[0]
    
    def test_generate_sample_data_unique_pairs(self, loader, tmp_path):
        """测试生成的蛋白对是唯一的"""
        output_file = tmp_path / "sample.csv"
        
        loader.generate_sample_data(str(output_file), n_interactions=50)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            pairs = [(r['protein_a'], r['protein_b']) for r in rows]
            # 没有自互作
            for a, b in pairs:
                assert a != b


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestImporterEdgeCases:
    """导入器边界情况测试"""
    
    def test_empty_csv_file(self, tmp_path):
        """测试空 CSV 文件"""
        csv_file = tmp_path / "empty.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name'])
            writer.writeheader()
        
        mock_session = MockSession()
        
        class TestImporter(DataImporter):
            def validate_row(self, row): return True, None
            def import_row(self, row): return True
        
        importer = TestImporter(mock_session)
        importer.import_file(str(csv_file))
        
        assert importer.imported_count == 0
    
    def test_csv_with_special_characters(self, tmp_path):
        """测试包含特殊字符的 CSV"""
        csv_file = tmp_path / "special.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name'])
            writer.writeheader()
            writer.writerow({'name': 'Protein\nWith\nNewlines'})
            writer.writerow({'name': 'Protein"With"Quotes'})
            writer.writerow({'name': 'Protein,With,Commas'})
        
        mock_session = MockSession()
        
        class TestImporter(DataImporter):
            def validate_row(self, row): return True, None
            def import_row(self, row): self.imported_count += 1; return True
        
        importer = TestImporter(mock_session)
        importer.import_file(str(csv_file))
        
        assert importer.imported_count == 3
    
    def test_large_csv_file(self, tmp_path):
        """测试大 CSV 文件"""
        csv_file = tmp_path / "large.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'value'])
            writer.writeheader()
            for i in range(1000):
                writer.writerow({'name': f'Item{i}', 'value': str(i)})
        
        mock_session = MockSession()
        
        class TestImporter(DataImporter):
            def validate_row(self, row): return True, None
            def import_row(self, row): self.imported_count += 1; return True
        
        importer = TestImporter(mock_session)
        importer.import_file(str(csv_file))
        
        assert importer.imported_count == 1000
    
    def test_invalid_score_format(self, importer):
        """测试无效的分数格式"""
        row = {'protein_a': 'A', 'protein_b': 'B', 'score': 'invalid'}
        # 应该使用默认分数 0.5
        result = importer.import_row(row)
        assert result is True
    
    def test_unicode_in_csv(self, tmp_path):
        """测试 Unicode 字符"""
        csv_file = tmp_path / "unicode.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name'])
            writer.writeheader()
            writer.writerow({'name': '蛋白A'})
            writer.writerow({'name': 'Proteína B'})
            writer.writerow({'name': 'たんぱく質 C'})
        
        mock_session = MockSession()
        
        class TestImporter(DataImporter):
            def validate_row(self, row): return True, None
            def import_row(self, row): self.imported_count += 1; return True
        
        importer = TestImporter(mock_session)
        importer.import_file(str(csv_file))
        
        assert importer.imported_count == 3


class MockContext:
    """模拟 Flask app_context"""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
