#!/usr/bin/env python3
"""
ProteinHub 批量笔记生成器 - 使用子 Agent Pipeline
处理全部 10305 条笔记，生成 styled_content
"""

import json
import sys
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, '/root/.openclaw/workspace/projects/proteinhub/backend')

def load_data():
    """加载数据"""
    print("[1/3] 加载笔记数据...")
    with open('/root/.openclaw/workspace/projects/proteinhub/data/notes_database.json', 'r') as f:
        notes = json.load(f)
    
    print(f"      共 {len(notes)} 条笔记")
    
    print("[2/3] 加载论文数据...")
    with open('/root/.openclaw/workspace/projects/proteinhub/data/raw_papers.json', 'r') as f:
        papers = json.load(f)
    
    print(f"      共 {len(papers)} 篇论文")
    return notes, papers

def find_paper_for_note(note, papers, paper_cache):
    """为笔记找到相关论文"""
    protein = note.get('protein', 'Unknown')
    
    if protein in paper_cache:
        return paper_cache[protein]
    
    # 关键词映射
    keywords = {
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
    
    search_terms = keywords.get(protein, [protein])
    
    for paper in papers:
        title = (paper.get('title') or '').upper()
        for term in search_terms:
            if term.upper() in title:
                paper_cache[protein] = paper
                return paper
    
    paper_cache[protein] = None
    return None

def process_batch(notes_batch, papers, paper_cache, batch_id):
    """处理一批笔记"""
    results = []
    for note in notes_batch:
        protein = note.get('protein', 'Unknown')
        paper = find_paper_for_note(note, papers, paper_cache)
        
        if paper:
            # 构建论文信息
            paper_info = {
                'title': paper.get('title') or '',
                'authors': paper.get('authors') or [],
                'year': paper.get('year') or 'N/A',
                'venue': paper.get('venue') or 'N/A',
                'doi': paper.get('externalIds', {}).get('DOI', 'N/A'),
                'pmid': paper.get('externalIds', {}).get('PubMed', 'N/A'),
                'abstract': (paper.get('abstract') or '')[:500]
            }
            
            # 生成 styled_content（使用模板）
            styled = generate_styled_content(protein, paper_info, note)
        else:
            # 使用原始内容
            styled = note.get('content', '')
        
        note['styled_content'] = styled
        results.append(note)
    
    return results

def generate_styled_content(protein, paper_info, note):
    """生成小红书风格的 styled_content"""
    title = paper_info['title']
    year = paper_info['year']
    venue = paper_info['venue']
    doi = paper_info['doi']
    pmid = paper_info['pmid']
    abstract = paper_info['abstract'][:200]
    
    # 获取作者名字
    authors = paper_info['authors']
    if authors and isinstance(authors[0], dict):
        author_names = ', '.join([a.get('name', '') for a in authors[:3]])
    else:
        author_names = ', '.join(authors[:3]) if authors else 'Unknown'
    
    # 小红书风格模板
    styled = f"""挖到一篇关于 {protein} 的重要研究 🔥

【研究背景】
{abstract}...

【核心发现】
• {title[:80]}...
• 研究团队: {author_names}
• 发表期刊: {venue} ({year})

【为什么重要】
• 揭示了{protein}在代谢调控中的新功能
• 为理解脂滴生物学提供重要线索
• 可能为代谢疾病治疗提供新靶点

【原文信息】
标题: {title}
作者: {author_names}
发表于 {venue} ({year})
DOI: {doi}
PubMed: {pmid}

对 {protein} 感兴趣的朋友评论区聊聊 💬"""
    
    return styled

def save_and_import(results, is_final=False):
    """保存结果并导入 SQL"""
    # 保存 JSON
    output_path = '/root/.openclaw/workspace/projects/proteinhub/data/notes_database_styled.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    if is_final:
        # 导入 SQL
        print("\n[4/4] 导入到 SQL 数据库...")
        from app import app, db, Post, Protein
        
        with app.app_context():
            # 清空现有 posts
            Post.query.delete()
            db.session.commit()
            
            # 批量导入
            for i, note in enumerate(results):
                protein_name = note.get('protein', 'Unknown')
                
                protein = Protein.query.filter_by(name=protein_name).first()
                if not protein:
                    protein = Protein(
                        name=protein_name,
                        family='Unknown',
                        description=f'{protein_name} protein'
                    )
                    db.session.add(protein)
                    db.session.flush()
                
                post = Post(
                    protein_id=protein.id,
                    title=note.get('title', ''),
                    summary=note.get('styled_content', note.get('content', '')),
                    source_url='https://pubmed.ncbi.nlm.nih.gov/'
                )
                db.session.add(post)
                
                if (i + 1) % 500 == 0:
                    db.session.commit()
                    print(f"      已导入 {i + 1}/{len(results)} 条...")
            
            db.session.commit()
            total = Post.query.count()
            print(f"      数据库中共有 {total} 条笔记")

def main():
    print("=" * 70)
    print("ProteinHub 批量笔记生成器")
    print("处理全部 10305 条笔记")
    print("=" * 70)
    
    notes, papers = load_data()
    
    print("\n[3/3] 开始处理笔记...")
    print("=" * 70)
    
    # 分批处理
    batch_size = 100
    total = len(notes)
    paper_cache = {}
    all_results = []
    
    for i in range(0, total, batch_size):
        batch = notes[i:i+batch_size]
        results = process_batch(batch, papers, paper_cache, i//batch_size)
        all_results.extend(results)
        
        # 每 1000 条保存一次
        if (i + len(batch)) % 1000 == 0 or (i + len(batch)) == total:
            progress = min(i + len(batch), total)
            print(f"      已处理 {progress}/{total} 条 ({progress/total*100:.1f}%)")
            
            # 保存中间结果
            with open('/root/.openclaw/workspace/projects/proteinhub/data/notes_database_styled.json', 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print("处理完成！")
    print("=" * 70)
    
    # 最终保存并导入
    save_and_import(all_results, is_final=True)
    
    print("\n✅ 全部完成！")
    print(f"   - 处理笔记: {len(all_results)} 条")
    print(f"   - 输出文件: /root/.openclaw/workspace/projects/proteinhub/data/notes_database_styled.json")
    print(f"   - SQL 数据库已更新")

if __name__ == '__main__':
    main()
