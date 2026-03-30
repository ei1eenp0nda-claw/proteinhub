#!/usr/bin/env python3
"""
ProteinHub 实际开发进度统计工具
不编造，真实检查代码文件
"""

import os
from pathlib import Path
from datetime import datetime

def count_project_stats(project_path):
    """统计项目真实代码数据"""
    stats = {
        'total_files': 0,
        'total_lines': 0,
        'python_files': [],
        'vue_files': [],
        'js_files': [],
        'by_dir': {}
    }
    
    project = Path(project_path)
    
    for root, dirs, files in os.walk(project):
        # 跳过 node_modules 和 venv
        dirs[:] = [d for d in dirs if d not in ['node_modules', 'venv', '__pycache__', '.git']]
        
        rel_root = os.path.relpath(root, project_path)
        if rel_root not in stats['by_dir']:
            stats['by_dir'][rel_root] = {'files': 0, 'lines': 0}
        
        for file in files:
            if file.endswith(('.py', '.vue', '.js', '.ts', '.json', '.sql', '.md')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                    
                    stats['total_files'] += 1
                    stats['total_lines'] += lines
                    stats['by_dir'][rel_root]['files'] += 1
                    stats['by_dir'][rel_root]['lines'] += lines
                    
                    if file.endswith('.py'):
                        stats['python_files'].append((filepath, lines))
                    elif file.endswith('.vue'):
                        stats['vue_files'].append((filepath, lines))
                    elif file.endswith('.js'):
                        stats['js_files'].append((filepath, lines))
                        
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return stats

def main():
    project_path = "/root/.openclaw/workspace/projects/proteinhub"
    
    print("=" * 60)
    print("ProteinHub 项目真实进度检查")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    stats = count_project_stats(project_path)
    
    print(f"\n【实际代码统计】")
    print(f"总文件数: {stats['total_files']}")
    print(f"总代码行数: {stats['total_lines']}")
    
    print(f"\n【按目录分布】")
    for dir_name, dir_stats in sorted(stats['by_dir'].items()):
        print(f"  {dir_name}: {dir_stats['files']} 文件, {dir_stats['lines']} 行")
    
    print(f"\n【Python 文件详情】")
    for filepath, lines in sorted(stats['python_files'], key=lambda x: -x[1]):
        rel_path = os.path.relpath(filepath, project_path)
        print(f"  {rel_path}: {lines} 行")
    
    print(f"\n【Vue 文件详情】")
    for filepath, lines in sorted(stats['vue_files'], key=lambda x: -x[1]):
        rel_path = os.path.relpath(filepath, project_path)
        print(f"  {rel_path}: {lines} 行")
    
    print(f"\n【JS 文件详情】")
    for filepath, lines in sorted(stats['js_files'], key=lambda x: -x[1]):
        rel_path = os.path.relpath(filepath, project_path)
        print(f"  {rel_path}: {lines} 行")
    
    # 实际进度评估
    estimated_progress = min(100, int(stats['total_lines'] / 1000 * 5))  # 粗略估算：1000行 = 5%
    print(f"\n【进度估算】")
    print(f"基于代码行数粗略估算: ~{estimated_progress}%")
    print("(注: 真实进度需要结合功能完成度评估)")
    
    print("\n" + "=" * 60)
    print("报告生成完毕 - 所有数据基于实际文件统计，无编造")
    print("=" * 60)

if __name__ == "__main__":
    main()
