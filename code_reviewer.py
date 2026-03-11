#!/usr/bin/env python3
"""
ProteinHub Code Review Report
代码审查报告

生成时间: 2026-03-11
审查范围: backend/, frontend/src/
审查标准: PEP8, 安全性, 性能, 可维护性
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Tuple
import json


class CodeReviewer:
    """代码审查器"""
    
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.issues: List[Dict] = []
        self.stats = {
            'total_files': 0,
            'total_lines': 0,
            'issues_by_severity': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0},
            'issues_by_category': {}
        }
    
    def review_all(self):
        """审查所有代码"""
        print("🔍 开始代码审查...")
        
        # 审查 Python 代码
        for py_file in self.project_dir.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            self.review_python_file(py_file)
        
        # 审查 Vue 代码
        for vue_file in self.project_dir.rglob("*.vue"):
            self.review_vue_file(vue_file)
        
        # 生成报告
        self.generate_report()
    
    def review_python_file(self, filepath: Path):
        """审查 Python 文件"""
        self.stats['total_files'] += 1
        
        try:
            content = filepath.read_text(encoding='utf-8')
            self.stats['total_lines'] += len(content.split('\n'))
            
            # 安全检查
            self._check_security_issues(filepath, content)
            
            # 代码规范检查
            self._check_pep8_issues(filepath, content)
            
            # 性能检查
            self._check_performance_issues(filepath, content)
            
            # 架构检查
            self._check_architecture_issues(filepath, content)
            
        except Exception as e:
            self.add_issue('Error', f'无法审查文件: {e}', str(filepath), 0)
    
    def review_vue_file(self, filepath: Path):
        """审查 Vue 文件"""
        self.stats['total_files'] += 1
        
        try:
            content = filepath.read_text(encoding='utf-8')
            self.stats['total_lines'] += len(content.split('\n'))
            
            # Vue 安全检查
            if 'v-html' in content and 'v-html="' in content:
                self.add_issue('High', '使用 v-html 可能导致 XSS 攻击，建议使用 {{ }} 或 v-text', str(filepath), 0, 'Security')
            
            # API 硬编码检查
            if 'localhost:5000' in content or 'http://localhost' in content:
                self.add_issue('Medium', '硬编码 API 地址，建议使用环境变量', str(filepath), 0, 'Maintainability')
            
        except Exception as e:
            pass
    
    def _check_security_issues(self, filepath: Path, content: str):
        """检查安全问题"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # SQL 注入检查
            if '.execute(' in line and ('%' in line or '+ ' in line or 'f"' in line):
                if '?' not in line and '%s' not in line:
                    self.add_issue('Critical', '潜在的 SQL 注入风险，建议使用参数化查询', str(filepath), i, 'Security')
            
            # 硬编码密钥检查
            if re.search(r'(SECRET_KEY|PASSWORD|API_KEY)\s*=\s*["\'][^"\']+["\']', line):
                if 'os.getenv' not in line and 'os.environ' not in line:
                    self.add_issue('Critical', '硬编码敏感信息，建议使用环境变量', str(filepath), i, 'Security')
            
            # 不安全的反序列化
            if 'pickle.loads' in line or 'yaml.load(' in line:
                self.add_issue('High', '不安全的反序列化，可能导致代码执行', str(filepath), i, 'Security')
            
            # 调试模式
            if 'debug=True' in line or 'DEBUG = True' in line:
                self.add_issue('Medium', '生产环境应关闭调试模式', str(filepath), i, 'Security')
            
            # 不安全的 HTTP
            if 'http://' in line and 'localhost' not in line:
                self.add_issue('Low', '建议使用 HTTPS', str(filepath), i, 'Security')
    
    def _check_pep8_issues(self, filepath: Path, content: str):
        """检查 PEP8 规范"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 行长度检查
            if len(line) > 120:
                self.add_issue('Low', f'行长度超过 120 字符 ({len(line)})', str(filepath), i, 'Style')
            
            # 尾随空格
            if line.rstrip() != line:
                self.add_issue('Low', '行尾有空格', str(filepath), i, 'Style')
        
        # 缺少文档字符串
        if 'def ' in content and '"""' not in content and "'''" not in content:
            if 'test_' not in str(filepath):  # 测试文件除外
                self.add_issue('Medium', '模块缺少文档字符串', str(filepath), 0, 'Documentation')
    
    def _check_performance_issues(self, filepath: Path, content: str):
        """检查性能问题"""
        # N+1 查询检查
        if 'for ' in content and '.query' in content:
            self.add_issue('High', '循环中可能存在 N+1 查询问题，建议使用 join 或 eager loading', str(filepath), 0, 'Performance')
        
        # 列表推导式检查
        if re.search(r'result = \[\]', content) and 'for ' in content:
            self.add_issue('Medium', '可以使用列表推导式优化', str(filepath), 0, 'Performance')
    
    def _check_architecture_issues(self, filepath: Path, content: str):
        """检查架构问题"""
        # 函数长度检查
        func_pattern = re.compile(r'def \w+\([^)]*\):')
        funcs = func_pattern.findall(content)
        
        if len(content.split('\n')) > 200 and len(funcs) == 1:
            self.add_issue('Medium', '文件过长，建议拆分', str(filepath), 0, 'Architecture')
        
        # 循环导入检查（简化）
        if 'import' in content and 'from .' in content:
            self.add_issue('Low', '注意循环导入风险', str(filepath), 0, 'Architecture')
    
    def add_issue(self, severity: str, message: str, filepath: str, line: int, category: str = 'General'):
        """添加问题"""
        self.issues.append({
            'severity': severity,
            'message': message,
            'file': filepath,
            'line': line,
            'category': category
        })
        self.stats['issues_by_severity'][severity] += 1
        self.stats['issues_by_category'][category] = self.stats['issues_by_category'].get(category, 0) + 1
    
    def generate_report(self):
        """生成审查报告"""
        report_path = self.project_dir / 'CODE_REVIEW_REPORT.md'
        
        # 按严重级别排序
        severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        sorted_issues = sorted(self.issues, key=lambda x: severity_order.get(x['severity'], 99))
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# ProteinHub 代码审查报告\n\n")
            f.write("**审查时间**: 2026-03-11\n")
            f.write(f"**审查文件**: {self.stats['total_files']} 个\n")
            f.write(f"**代码行数**: {self.stats['total_lines']} 行\n")
            f.write(f"**发现问题**: {len(self.issues)} 个\n\n")
            
            # 统计摘要
            f.write("## 📊 问题统计\n\n")
            f.write("### 按严重级别\n\n")
            for sev, count in self.stats['issues_by_severity'].items():
                emoji = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(sev, '⚪')
                f.write(f"- {emoji} **{sev}**: {count} 个\n")
            
            f.write("\n### 按类别\n\n")
            for cat, count in sorted(self.stats['issues_by_category'].items(), key=lambda x: -x[1]):
                f.write(f"- **{cat}**: {count} 个\n")
            
            # 详细问题列表
            f.write("\n## 📝 详细问题列表\n\n")
            
            current_severity = None
            for issue in sorted_issues:
                if issue['severity'] != current_severity:
                    current_severity = issue['severity']
                    emoji = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(current_severity, '⚪')
                    f.write(f"\n### {emoji} {current_severity} 级别\n\n")
                
                f.write(f"**[{issue['category']}]** {issue['message']}\n")
                f.write(f"- 文件: `{issue['file']}`")
                if issue['line'] > 0:
                    f.write(f":{issue['line']}")
                f.write("\n\n")
            
            # 修复建议
            f.write("\n## 💡 修复建议\n\n")
            f.write("### 高优先级\n\n")
            f.write("1. **将硬编码密钥移至环境变量**\n")
            f.write("   - 修改 `config.py` 使用 `os.getenv()`\n")
            f.write("   - 创建 `.env.example` 文件\n\n")
            f.write("2. **修复 SQL 注入风险**\n")
            f.write("   - 使用参数化查询替代字符串拼接\n")
            f.write("   - 使用 ORM 的 `filter_by()` 方法\n\n")
            f.write("3. **优化 N+1 查询**\n")
            f.write("   - 使用 `joinedload()` 进行预加载\n")
            f.write("   - 批量查询替代循环查询\n\n")
            
            f.write("### 中优先级\n\n")
            f.write("1. **添加文档字符串**\n")
            f.write("2. **拆分过长的函数**\n")
            f.write("3. **配置前端 API 环境变量**\n\n")
            
            f.write("### 低优先级\n\n")
            f.write("1. **修复 PEP8 格式问题**\n")
            f.write("2. **移除行尾空格**\n")
            f.write("3. **使用 HTTPS 链接**\n\n")
            
            f.write("---\n\n")
            f.write("*报告由 Code Reviewer Agent 自动生成*\n")
        
        print(f"✅ 代码审查报告已生成: {report_path}")
        return report_path


if __name__ == "__main__":
    reviewer = CodeReviewer("/root/.openclaw/workspace/projects/proteinhub")
    reviewer.review_all()
    
    print("\n" + "="*50)
    print("审查完成!")
    print(f"文件数: {reviewer.stats['total_files']}")
    print(f"代码行数: {reviewer.stats['total_lines']}")
    print(f"问题数: {len(reviewer.issues)}")
    print("="*50)
