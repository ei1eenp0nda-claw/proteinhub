#!/usr/bin/env python3
"""
ProteinHub 功能检查工具
Functionality Check Tool
"""

import sys
from pathlib import Path
from typing import List, Dict


class FunctionalityChecker:
    """功能检查器"""
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir)
        self.checks = []
        self.results = []
    
    def check_file_exists(self, path: str, description: str) -> bool:
        """检查文件是否存在"""
        full_path = self.project_dir / path
        exists = full_path.exists()
        self.results.append({
            'check': description,
            'status': '✅' if exists else '❌',
            'path': path
        })
        return exists
    
    def check_backend_structure(self):
        """检查后端结构"""
        print("\n📦 后端结构检查")
        print("-" * 40)
        
        files = [
            ('backend/app.py', '主应用'),
            ('backend/config.py', '配置文件'),
            ('backend/database.py', '数据库'),
            ('backend/auth.py', '认证模块'),
            ('backend/requirements.txt', '依赖列表'),
            ('backend/routes/auth.py', '认证路由'),
            ('backend/routes/search.py', '搜索路由'),
            ('backend/services/protein_service.py', '蛋白服务'),
            ('backend/services/search_service.py', '搜索服务'),
            ('backend/recommendation/dual_tower.py', '推荐算法'),
            ('backend/crawler/pubmed_crawler.py', 'PubMed爬虫'),
        ]
        
        for path, desc in files:
            self.check_file_exists(path, desc)
    
    def check_frontend_structure(self):
        """检查前端结构"""
        print("\n🎨 前端结构检查")
        print("-" * 40)
        
        files = [
            ('frontend/package.json', '包配置'),
            ('frontend/src/App.vue', '主组件'),
            ('frontend/src/router/index.js', '路由'),
            ('frontend/src/views/Feed.vue', 'Feed页面'),
            ('frontend/src/views/Search.vue', '搜索页面'),
            ('frontend/src/components/LoginForm.vue', '登录组件'),
        ]
        
        for path, desc in files:
            self.check_file_exists(path, desc)
    
    def check_devops(self):
        """检查 DevOps 配置"""
        print("\n🚀 DevOps 检查")
        print("-" * 40)
        
        files = [
            ('docker-compose.yml', 'Docker编排'),
            ('setup.sh', '环境设置'),
            ('deploy.sh', '部署脚本'),
            ('.github/workflows/ci.yml', 'CI/CD'),
            ('README.md', '项目文档'),
            ('DEPLOY.md', '部署文档'),
        ]
        
        for path, desc in files:
            self.check_file_exists(path, desc)
    
    def check_tests(self):
        """检查测试"""
        print("\n🧪 测试检查")
        print("-" * 40)
        
        files = [
            ('backend/tests/test_api.py', 'API测试'),
            ('test_api.py', '集成测试'),
        ]
        
        for path, desc in files:
            self.check_file_exists(path, desc)
    
    def count_code_lines(self):
        """统计代码行数"""
        print("\n📊 代码统计")
        print("-" * 40)
        
        extensions = {
            'Python': '*.py',
            'Vue': '*.vue',
            'JavaScript': '*.js',
        }
        
        total = 0
        for lang, pattern in extensions.items():
            files = list(self.project_dir.rglob(pattern))
            lines = 0
            for f in files:
                try:
                    lines += len(f.read_text().split('\n'))
                except:
                    pass
            print(f"   {lang}: {lines} 行 ({len(files)} 文件)")
            total += lines
        
        print(f"\n   总计: {total} 行")
        return total
    
    def run_all_checks(self):
        """运行所有检查"""
        print("🧬 ProteinHub 功能检查")
        print("=" * 50)
        
        self.check_backend_structure()
        self.check_frontend_structure()
        self.check_devops()
        self.check_tests()
        total_lines = self.count_code_lines()
        
        # 汇总
        print("\n" + "=" * 50)
        print("📋 检查结果汇总")
        print("=" * 50)
        
        passed = sum(1 for r in self.results if r['status'] == '✅')
        failed = sum(1 for r in self.results if r['status'] == '❌')
        
        print(f"   通过: {passed}")
        print(f"   失败: {failed}")
        print(f"   总计: {len(self.results)}")
        print(f"   代码: {total_lines} 行")
        
        if failed > 0:
            print("\n❌ 缺失项:")
            for r in self.results:
                if r['status'] == '❌':
                    print(f"   - {r['check']}: {r['path']}")
        
        print(f"\n✅ 项目完成度: {passed}/{len(self.results)} ({passed/len(self.results)*100:.1f}%)")
        
        return failed == 0


if __name__ == "__main__":
    checker = FunctionalityChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)
