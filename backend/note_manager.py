"""
Markdown 笔记管理模块
直接从 data/high_quality_notes/ 读取 md 文件
"""
import os
import glob
import re
from pathlib import Path

def get_notes_dir():
    """获取笔记目录（支持多种运行环境）"""
    # 尝试多种可能的路径
    possible_paths = [
        # 标准项目结构
        Path(__file__).parent.parent.parent / 'data' / 'high_quality_notes',
        # 测试环境（backend 目录下）
        Path(__file__).parent.parent / 'data' / 'high_quality_notes',
        # 当前工作目录
        Path.cwd() / 'data' / 'high_quality_notes',
        Path.cwd().parent / 'data' / 'high_quality_notes',
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # 返回默认路径（即使不存在，让调用者处理）
    return possible_paths[0]

NOTES_DIR = get_notes_dir()

def get_all_notes():
    """获取所有笔记列表（不含内容）"""
    notes = []
    md_files = sorted(NOTES_DIR.glob('*.md'))
    
    for idx, md_file in enumerate(md_files):
        content = md_file.read_text(encoding='utf-8')
        
        # 提取标题
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else md_file.stem
        
        # 提取预览（第一段非标题文字）
        lines = content.split('\n')
        preview = ''
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and len(stripped) > 20:
                preview = stripped[:100] + '...' if len(stripped) > 100 else stripped
                break
        
        notes.append({
            'id': f'note_{idx}',
            'filename': md_file.name,
            'title': title,
            'preview': preview,
            'size': len(content),
            'updated_at': os.path.getmtime(md_file)
        })
    
    return notes

def get_note_content(note_id):
    """根据 ID 获取笔记完整内容"""
    md_files = sorted(NOTES_DIR.glob('*.md'))
    
    # 解析 note_id (note_0, note_1, ...)
    if note_id.startswith('note_'):
        idx = int(note_id.replace('note_', ''))
        if 0 <= idx < len(md_files):
            return md_files[idx].read_text(encoding='utf-8')
    
    # 或者通过文件名匹配
    for md_file in md_files:
        if md_file.stem == note_id or md_file.name == note_id:
            return md_file.read_text(encoding='utf-8')
    
    return None

def search_notes(query):
    """搜索笔记"""
    if not query or not query.strip():
        return []
    
    results = []
    query_lower = query.lower().strip()
    md_files = sorted(get_notes_dir().glob('*.md'))
    
    for idx, md_file in enumerate(md_files):
        content = md_file.read_text(encoding='utf-8').lower()
        if query_lower in content:
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else md_file.stem
            
            results.append({
                'id': f'note_{idx}',
                'filename': md_file.name,
                'title': title
            })
    
    return results