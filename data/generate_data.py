#!/usr/bin/env python3
"""
ProteinHub 数据导入工具
Data Import Utility for ProteinHub

功能:
- 导入蛋白数据
- 导入蛋白互作数据
- 导入文献数据
- 生成测试数据
"""

import json
import csv
import random
from pathlib import Path
from datetime import datetime


class DataImporter:
    """数据导入器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.log = []
    
    def generate_sample_proteins(self, count: int = 100) -> list:
        """生成示例蛋白数据"""
        families = ['CIDE', 'PLIN', 'ATGL', 'HSL', 'FSP27', 'Rab', 'SNARE', 'Perilipin']
        proteins = []
        
        for i in range(count):
            family = random.choice(families)
            proteins.append({
                'name': f'PROTEIN_{i+1}',
                'family': family,
                'uniprot_id': f'P{random.randint(10000, 99999)}',
                'description': f'{family} family protein {i+1} involved in lipid metabolism',
                'sequence': self._generate_sequence()
            })
        
        return proteins
    
    def generate_interactions(self, proteins: list, count: int = 500) -> list:
        """生成蛋白互作数据"""
        interactions = []
        
        for _ in range(count):
            p1, p2 = random.sample(proteins, 2)
            interactions.append({
                'protein_a': p1['name'],
                'protein_b': p2['name'],
                'interaction_score': round(random.uniform(0.5, 1.0), 3),
                'interaction_type': random.choice(['binding', 'catalysis', 'regulation']),
                'confidence': random.choice(['high', 'medium', 'low'])
            })
        
        return interactions
    
    def generate_posts(self, proteins: list, count: int = 50) -> list:
        """生成示例帖子数据"""
        posts = []
        titles = [
            "最新研究揭示{}在脂滴代谢中的关键作用",
            "{}与{}的相互作用机制解析",
            "{}作为新型药物靶点的潜力评估",
            "基于{}的癌症诊断标志物研究",
            "{}在脂肪细胞分化中的调控功能"
        ]
        
        for i in range(count):
            protein = random.choice(proteins)
            title_template = random.choice(titles)
            
            if '{}' in title_template:
                title = title_template.format(protein['name'])
            else:
                title = title_template
            
            posts.append({
                'title': title,
                'summary': f'本研究探讨了{protein["name"]}在细胞代谢中的重要功能...',
                'protein_name': protein['name'],
                'author': f'Researcher_{random.randint(1, 20)}',
                'likes': random.randint(0, 500),
                'views': random.randint(100, 5000),
                'tags': [protein['family'], 'research', 'lipid']
            })
        
        return posts
    
    def _generate_sequence(self, length: int = 100) -> str:
        """生成随机蛋白序列"""
        amino_acids = 'ACDEFGHIKLMNPQRSTVWY'
        return ''.join(random.choices(amino_acids, k=length))
    
    def export_to_json(self, data: list, filename: str):
        """导出为 JSON"""
        filepath = self.data_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        self.log.append(f"✅ 导出 {filename}: {len(data)} 条记录")
        return filepath
    
    def export_to_csv(self, data: list, filename: str):
        """导出为 CSV"""
        if not data:
            return None
        
        filepath = self.data_dir / filename
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        self.log.append(f"✅ 导出 {filename}: {len(data)} 条记录")
        return filepath
    
    def generate_all(self):
        """生成所有示例数据"""
        print("🧬 生成 ProteinHub 示例数据")
        print("=" * 50)
        
        # 生成蛋白
        print("\n1️⃣ 生成蛋白数据...")
        proteins = self.generate_sample_proteins(200)
        self.export_to_json(proteins, 'proteins.json')
        self.export_to_csv(proteins, 'proteins.csv')
        
        # 生成互作
        print("\n2️⃣ 生成蛋白互作数据...")
        interactions = self.generate_interactions(proteins, 1000)
        self.export_to_json(interactions, 'interactions.json')
        self.export_to_csv(interactions, 'interactions.csv')
        
        # 生成帖子
        print("\n3️⃣ 生成帖子数据...")
        posts = self.generate_posts(proteins, 100)
        self.export_to_json(posts, 'posts.json')
        self.export_to_csv(posts, 'posts.csv')
        
        # 输出日志
        print("\n" + "=" * 50)
        print("📊 数据生成完成:")
        for msg in self.log:
            print(f"   {msg}")
        
        print(f"\n📁 数据目录: {self.data_dir.absolute()}")


def import_to_database(data_file: str, db_uri: str = None):
    """导入数据到数据库（示例函数）"""
    print(f"\n📥 导入 {data_file} 到数据库")
    print("   注意: 需要运行中的数据库服务")
    print("   使用: docker-compose up -d db")


if __name__ == "__main__":
    importer = DataImporter()
    importer.generate_all()
