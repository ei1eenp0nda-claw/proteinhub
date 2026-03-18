"""
Markdown 笔记管理模块
直接从 data/high_quality_notes/ 读取 md 文件
"""
import os
import glob
import re
from pathlib import Path

NOTES_DIR = Path(__file__).parent.parent.parent / 'data' / 'high_quality_notes'

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
    results = []
    query_lower = query.lower()
    md_files = sorted(NOTES_DIR.glob('*.md'))
    
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