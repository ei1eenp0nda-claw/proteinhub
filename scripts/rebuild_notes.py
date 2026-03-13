#!/usr/bin/env python3
"""
ProteinHub 笔记内容重写脚本
- 读取 notes_database.json
- 为每条笔记生成 styled_content（小红书风格）
- 保存到新的 JSON 文件
- 导入到 SQL 数据库
"""

import json
import sys
import os
from datetime import datetime

# 添加 backend 路径
sys.path.insert(0, '/root/.openclaw/workspace/projects/proteinhub/backend')

def load_papers():
    """加载真实论文数据"""
    with open('/root/.openclaw/workspace/projects/proteinhub/data/raw_papers.json', 'r') as f:
        papers = json.load(f)
    return papers

def get_author_names(authors):
    """提取作者名字"""
    if not authors:
        return "Unknown"
    if isinstance(authors[0], dict):
        names = [a.get('name', '') for a in authors[:3]]
    else:
        names = authors[:3]
    return ', '.join(names)

def find_related_paper(papers, protein_name):
    """根据蛋白名找相关论文"""
    protein_keywords = {
        'CIDEA': ['CIDEA'],
        'CIDEB': ['CIDEB'],
        'CIDEC': ['CIDEC', 'FSP27'],
        'PLIN1': ['PLIN1', 'PERILIPIN 1'],
        'PLIN2': ['PLIN2', 'PERILIPIN 2', 'ADFP'],
        'PLIN3': ['PLIN3', 'PERILIPIN 3', 'TIP47'],
        'PLIN4': ['PLIN4', 'PERILIPIN 4'],
        'PLIN5': ['PLIN5', 'PERILIPIN 5', 'OXPAT'],
        'ATGL': ['ATGL', 'PNPLA2'],
        'CGI-58': ['CGI-58', 'ABHD5'],
    }
    
    keywords = protein_keywords.get(protein_name, [protein_name])
    
    for paper in papers:
        title = (paper.get('title') or '').upper()
        abstract = (paper.get('abstract') or '').upper()
        
        for kw in keywords:
            if kw.upper() in title or kw.upper() in abstract:
                return paper
    
    return None

def generate_styled_content(note, paper):
    """生成小红书风格的 styled_content"""
    protein = note.get('protein', 'Unknown')
    original_title = note.get('title', '')
    
    if paper:
        # 有真实论文数据
        title = paper.get('title', original_title)
        authors = get_author_names(paper.get('authors'))
        year = paper.get('year', 'N/A')
        venue = paper.get('venue', 'N/A')
        citations = paper.get('citationCount', 'N/A')
        doi = paper.get('externalIds', {}).get('DOI', 'N/A')
        pmid = paper.get('externalIds', {}).get('PubMed', 'N/A')
        abstract = paper.get('abstract', '')[:300] if paper.get('abstract') else 'No abstract available'
        
        styled = f"""挖到一篇关于 {protein} 的重要研究，必须分享 🔥

【研究背景】
{abstract[:150]}...

【核心发现】
{title[:100]}...
• 研究团队: {authors}
• 发表期刊: {venue} ({year})
• 被引次数: {citations}次

【为什么重要】
• 揭示了{protein}在代谢调控中的新功能
• 为理解脂滴生物学提供重要线索
• 可能为代谢疾病治疗提供新靶点

【原文信息】
标题: {title}
作者: {authors}
发表于 {venue} ({year})
引用: {citations}次
DOI: {doi}
PubMed: {pmid}

对 {protein} 感兴趣的朋友评论区聊聊 💬"""
    else:
        # 没有真实论文数据，用模板
        styled = f"""分享一篇关于 {protein} 的研究发现 🧬

【{protein}是干嘛的】
{protein} 是脂滴相关蛋白，在脂质代谢中发挥重要作用。

【核心发现】
{original_title}

【研究意义】
• 深入理解 {protein} 的功能机制
• 为代谢疾病研究提供新视角
• 有助于开发新的治疗策略

【值得关注】
关注 {protein} 的最新研究进展，了解更多脂滴生物学知识！

对 {protein} 感兴趣的朋友评论区交流 💬"""
    
    return styled

def process_notes():
    """处理所有笔记"""
    print("=" * 60)
    print("ProteinHub 笔记内容重写")
    print("=" * 60)
    
    # 加载数据
    print("\n[1/4] 加载笔记数据...")
    with open('/root/.openclaw/workspace/projects/proteinhub/data/notes_database.json', 'r') as f:
        notes = json.load(f)
    print(f"   共 {len(notes)} 条笔记")
    
    print("\n[2/4] 加载论文数据...")
    papers = load_papers()
    print(f"   共 {len(papers)} 篇论文")
    
    # 创建论文索引（按蛋白名）
    paper_cache = {}
    
    print("\n[3/4] 生成 styled_content...")
    processed = 0
    has_paper = 0
    
    for i, note in enumerate(notes):
        protein = note.get('protein', 'Unknown')
        
        # 查找相关论文
        if protein not in paper_cache:
            paper_cache[protein] = find_related_paper(papers, protein)
        
        paper = paper_cache[protein]
        if paper:
            has_paper += 1
        
        # 生成 styled_content
        styled = generate_styled_content(note, paper)
        note['styled_content'] = styled
        
        processed += 1
        if (i + 1) % 1000 == 0:
            print(f"   已处理 {i + 1}/{len(notes)} 条...")
    
    print(f"   完成！{processed} 条笔记，其中 {has_paper} 条有真实论文数据")
    
    # 保存新的 JSON
    print("\n[4/4] 保存到新的 JSON 文件...")
    output_path = '/root/.openclaw/workspace/projects/proteinhub/data/notes_database_styled.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)
    print(f"   已保存: {output_path}")
    
    # 导入到 SQL
    print("\n[5/5] 导入到 SQL 数据库...")
    from app import app, db, Post, Protein
    
    with app.app_context():
        # 清空现有 posts
        Post.query.delete()
        db.session.commit()
        print("   已清空现有 posts")
        
        # 批量导入
        batch_size = 500
        for i in range(0, len(notes), batch_size):
            batch = notes[i:i+batch_size]
            for note in batch:
                protein_name = note.get('protein', 'Unknown')
                
                # 获取或创建蛋白
                protein = Protein.query.filter_by(name=protein_name).first()
                if not protein:
                    protein = Protein(
                        name=protein_name,
                        family='Unknown',
                        description=f'{protein_name} protein'
                    )
                    db.session.add(protein)
                    db.session.flush()
                
                # 创建 post
                post = Post(
                    protein_id=protein.id,
                    title=note.get('title', ''),
                    summary=note.get('styled_content', note.get('content', '')),
                    source_url='https://pubmed.ncbi.nlm.nih.gov/'
                )
                db.session.add(post)
            
            db.session.commit()
            print(f"   已导入 {min(i + batch_size, len(notes))}/{len(notes)} 条...")
        
        total = Post.query.count()
        print(f"   数据库中共有 {total} 条笔记")
    
    print("\n" + "=" * 60)
    print("✅ 全部完成！")
    print("=" * 60)

if __name__ == '__main__':
    process_notes()
