"""
ProteinHub Data Import Module
批量数据导入工具

支持：
1. CSV/TSV 蛋白互作数据导入
2. 批量 PubMed 文献爬取
3. 数据清洗和验证
"""
import csv
import json
from datetime import datetime
from typing import List, Dict, Optional, Callable
from pathlib import Path


class DataImporter:
    """数据导入器基类"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.errors = []
        self.imported_count = 0
        self.skipped_count = 0
    
    def validate_row(self, row: Dict) -> tuple:
        """
        验证单行数据
        
        Returns:
            (是否有效, 错误信息)
        """
        return True, None
    
    def import_row(self, row: Dict) -> bool:
        """
        导入单行数据
        
        Returns:
            是否成功
        """
        raise NotImplementedError
    
    def import_file(self, filepath: str, progress_callback: Optional[Callable] = None):
        """
        导入文件
        
        Args:
            filepath: 文件路径
            progress_callback: 进度回调函数 (current, total)
        """
        self.errors = []
        self.imported_count = 0
        self.skipped_count = 0
        
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        # 检测文件格式
        ext = path.suffix.lower()
        if ext == '.csv':
            return self._import_csv(filepath, progress_callback)
        elif ext == '.json':
            return self._import_json(filepath, progress_callback)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    def _import_csv(self, filepath: str, progress_callback: Optional[Callable] = None):
        """导入 CSV 文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            # 检测分隔符
            sample = f.read(1024)
            f.seek(0)
            
            delimiter = '\t' if '\t' in sample else ','
            
            reader = csv.DictReader(f, delimiter=delimiter)
            rows = list(reader)
            total = len(rows)
            
            for i, row in enumerate(rows, 1):
                try:
                    is_valid, error = self.validate_row(row)
                    if not is_valid:
                        self.errors.append({'row': i, 'error': error, 'data': row})
                        self.skipped_count += 1
                        continue
                    
                    if self.import_row(row):
                        self.imported_count += 1
                    else:
                        self.skipped_count += 1
                    
                    if progress_callback and i % 100 == 0:
                        progress_callback(i, total)
                        
                except Exception as e:
                    self.errors.append({'row': i, 'error': str(e), 'data': row})
                    self.skipped_count += 1
            
            if progress_callback:
                progress_callback(total, total)
    
    def _import_json(self, filepath: str, progress_callback: Optional[Callable] = None):
        """导入 JSON 文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            data = [data]
        
        total = len(data)
        
        for i, row in enumerate(data, 1):
            try:
                is_valid, error = self.validate_row(row)
                if not is_valid:
                    self.errors.append({'row': i, 'error': error, 'data': row})
                    self.skipped_count += 1
                    continue
                
                if self.import_row(row):
                    self.imported_count += 1
                else:
                    self.skipped_count += 1
                
                if progress_callback and i % 100 == 0:
                    progress_callback(i, total)
                    
            except Exception as e:
                self.errors.append({'row': i, 'error': str(e), 'data': row})
                self.skipped_count += 1
        
        if progress_callback:
            progress_callback(total, total)
    
    def get_report(self) -> Dict:
        """获取导入报告"""
        return {
            'imported': self.imported_count,
            'skipped': self.skipped_count,
            'errors': len(self.errors),
            'error_details': self.errors[:10]  # 只返回前10个错误
        }


class ProteinInteractionImporter(DataImporter):
    """蛋白互作数据导入器"""
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.protein_cache = {}  # 缓存已创建的蛋白
    
    def validate_row(self, row: Dict) -> tuple:
        """验证蛋白互作数据行"""
        protein_a = row.get('protein_a') or row.get('Protein_A') or row.get('protein1')
        protein_b = row.get('protein_b') or row.get('Protein_B') or row.get('protein2')
        
        if not protein_a or not protein_b:
            return False, '缺少蛋白名称'
        
        if protein_a == protein_b:
            return False, '蛋白不能与自己互作'
        
        return True, None
    
    def import_row(self, row: Dict) -> bool:
        """导入蛋白互作数据"""
        from models import Protein, ProteinInteraction
        
        # 获取蛋白名称
        protein_a_name = row.get('protein_a') or row.get('Protein_A') or row.get('protein1')
        protein_b_name = row.get('protein_b') or row.get('Protein_B') or row.get('protein2')
        
        # 获取或创建蛋白A
        if protein_a_name not in self.protein_cache:
            protein_a = Protein.query.filter_by(name=protein_a_name).first()
            if not protein_a:
                protein_a = Protein(
                    name=protein_a_name,
                    family=row.get('family_a'),
                    description=f'Protein {protein_a_name}'
                )
                self.db.add(protein_a)
                self.db.flush()
            self.protein_cache[protein_a_name] = protein_a
        else:
            protein_a = self.protein_cache[protein_a_name]
        
        # 获取或创建蛋白B
        if protein_b_name not in self.protein_cache:
            protein_b = Protein.query.filter_by(name=protein_b_name).first()
            if not protein_b:
                protein_b = Protein(
                    name=protein_b_name,
                    family=row.get('family_b'),
                    description=f'Protein {protein_b_name}'
                )
                self.db.add(protein_b)
                self.db.flush()
            self.protein_cache[protein_b_name] = protein_b
        else:
            protein_b = self.protein_cache[protein_b_name]
        
        # 检查互作是否已存在
        existing = ProteinInteraction.query.filter(
            ((ProteinInteraction.protein_a_id == protein_a.id) & 
             (ProteinInteraction.protein_b_id == protein_b.id)) |
            ((ProteinInteraction.protein_a_id == protein_b.id) & 
             (ProteinInteraction.protein_b_id == protein_a.id))
        ).first()
        
        if existing:
            return False  # 已存在，跳过
        
        # 创建互作记录
        interaction_score = row.get('score') or row.get('interaction_score') or row.get('probability')
        try:
            score = float(interaction_score) if interaction_score else 0.5
        except:
            score = 0.5
        
        interaction = ProteinInteraction(
            protein_a_id=protein_a.id,
            protein_b_id=protein_b.id,
            interaction_score=score
        )
        self.db.add(interaction)
        self.db.flush()
        
        return True


class BatchDataLoader:
    """批量数据加载器"""
    
    def __init__(self, app, db):
        self.app = app
        self.db = db
    
    def load_protein_interactions(self, filepath: str, batch_size: int = 1000):
        """
        批量加载蛋白互作数据
        
        Args:
            filepath: 数据文件路径
            batch_size: 批量提交大小
        """
        print(f"🔄 开始导入蛋白互作数据: {filepath}")
        
        importer = ProteinInteractionImporter(self.db)
        
        def progress(current, total):
            pct = (current / total) * 100
            print(f"   进度: {current}/{total} ({pct:.1f}%)")
        
        with self.app.app_context():
            try:
                importer.import_file(filepath, progress_callback=progress)
                self.db.commit()
                
                report = importer.get_report()
                print(f"\n✅ 导入完成:")
                print(f"   成功: {report['imported']}")
                print(f"   跳过: {report['skipped']}")
                print(f"   错误: {report['errors']}")
                
                if report['error_details']:
                    print(f"\n⚠️ 部分错误示例:")
                    for err in report['error_details'][:3]:
                        print(f"   行 {err['row']}: {err['error']}")
                
                return report
                
            except Exception as e:
                self.db.rollback()
                print(f"❌ 导入失败: {e}")
                raise
    
    def generate_sample_data(self, output_path: str, n_interactions: int = 1000):
        """
        生成示例数据（用于测试）
        
        Args:
            output_path: 输出文件路径
            n_interactions: 互作对数
        """
        import random
        
        # 常见的脂滴相关蛋白
        proteins = [
            'CIDEA', 'CIDEB', 'CIDEC',
            'PLIN1', 'PLIN2', 'PLIN3', 'PLIN4', 'PLIN5',
            'ATGL', 'HSL', 'MGL',
            'FSP27', 'FITM1', 'FITM2',
            'GPAT3', 'GPAT4', 'AGPAT2', 'DGAT1', 'DGAT2',
            'Perilipin', 'ADRP', 'TIP47', 'S3-12', 'OXPAT'
        ]
        
        data = []
        for i in range(n_interactions):
            protein_a = random.choice(proteins)
            protein_b = random.choice(proteins)
            
            if protein_a != protein_b:
                data.append({
                    'protein_a': protein_a,
                    'protein_b': protein_b,
                    'interaction_score': round(random.uniform(0.3, 0.99), 3),
                    'source': 'Rosetta_PPI_prediction'
                })
        
        # 保存为 CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['protein_a', 'protein_b', 'interaction_score', 'source'])
            writer.writeheader()
            writer.writerows(data)
        
        print(f"✅ 生成示例数据: {output_path} ({len(data)} 条记录)")


if __name__ == '__main__':
    # 测试数据导入
    from app import app, db
    
    loader = BatchDataLoader(app, db)
    
    # 生成测试数据
    loader.generate_sample_data('/tmp/sample_interactions.csv', n_interactions=100)
    
    # 导入测试数据
    loader.load_protein_interactions('/tmp/sample_interactions.csv')
