import json
import os
from models import app, db, User, Note

with app.app_context():
    # 查找JSON数据文件
    json_paths = [
        '../data/proteinhub_notes_database.json',
        'data/proteinhub_notes_database.json',
        '/root/.openclaw/workspace/projects/proteinhub/data/proteinhub_notes_database.json'
    ]
    
    data_file = None
    for path in json_paths:
        if os.path.exists(path):
            data_file = path
            break
    
    if not data_file:
        print("未找到JSON数据文件，创建示例笔记...")
        # 创建一些示例笔记
        user = User.query.first()
        if not user:
            print("请先创建用户")
            exit(1)
        
        sample_notes = [
            {
                'title': 'CRISPR-Cas9技术在基因编辑中的最新进展',
                'content': 'CRISPR-Cas9技术是一种革命性的基因编辑工具，本研究总结了2024年的最新进展...',
                'paper_title': 'CRISPR-Cas9: A Revolutionary Tool for Genome Editing',
                'paper_venue': 'Nature Reviews Molecular Cell Biology',
                'paper_year': 2024,
                'paper_doi': '10.1038/s41580-024-00123-4',
                'paper_pmid': '36964140',
                'tags': ['CRISPR', '基因编辑', '生物技术']
            },
            {
                'title': 'AlphaFold2预测蛋白质结构的突破性研究',
                'content': 'AlphaFold2在蛋白质结构预测方面取得了重大突破，准确率达到90%以上...',
                'paper_title': 'Highly accurate protein structure prediction with AlphaFold',
                'paper_venue': 'Nature',
                'paper_year': 2021,
                'paper_doi': '10.1038/s41586-021-03819-2',
                'paper_pmid': '34265844',
                'tags': ['AlphaFold', '蛋白质结构', '人工智能']
            },
            {
                'title': 'mRNA疫苗技术原理与临床应用综述',
                'content': 'mRNA疫苗技术在COVID-19疫情期间展示了巨大的应用潜力...',
                'paper_title': 'mRNA vaccines — a new era in vaccinology',
                'paper_venue': 'Nature Reviews Drug Discovery',
                'paper_year': 2018,
                'paper_doi': '10.1038/nrd.2017.243',
                'paper_pmid': '29326426',
                'tags': ['mRNA疫苗', '免疫学', '临床转化']
            },
            {
                'title': '单细胞测序技术在肿瘤研究中的应用',
                'content': '单细胞测序技术揭示了肿瘤异质性和微环境的复杂性...',
                'paper_title': 'Single-cell RNA sequencing technologies and bioinformatics pipelines',
                'paper_venue': 'Experimental & Molecular Medicine',
                'paper_year': 2018,
                'paper_doi': '10.1038/s12276-018-0071-8',
                'paper_pmid': '29632359',
                'tags': ['单细胞测序', '肿瘤学', '生物信息学']
            },
            {
                'title': 'CAR-T细胞疗法治疗血液肿瘤的临床进展',
                'content': 'CAR-T细胞疗法在血液肿瘤治疗中取得了显著疗效...',
                'paper_title': 'Chimeric antigen receptor T cell therapy for B cell malignancies',
                'paper_venue': 'Blood',
                'paper_year': 2023,
                'paper_doi': '10.1182/blood.2022018692',
                'paper_pmid': '37018047',
                'tags': ['CAR-T', '免疫治疗', '血液肿瘤']
            }
        ]
        
        for note_data in sample_notes:
            note = Note(
                title=note_data['title'],
                content=note_data['content'],
                author_id=user.id,
                paper_title=note_data.get('paper_title', ''),
                paper_journal=note_data.get('paper_venue', ''),
                paper_pub_date=str(note_data.get('paper_year', '')),
                paper_doi=note_data.get('paper_doi', ''),
                paper_pmid=note_data.get('paper_pmid', ''),
                media_urls='[]'
            )
            db.session.add(note)
        
        db.session.commit()
        print(f"成功创建 {len(sample_notes)} 篇示例笔记！")
        exit(0)
    
    print(f"使用数据文件: {data_file}")
    
    with open(data_file) as f:
        data = json.load(f)
    
    user = User.query.first()
    if not user:
        print("请先创建用户")
        exit(1)
    
    notes_data = data.get('notes', []) if isinstance(data, dict) else data
    count = 0
    max_notes = min(50, len(notes_data))
    
    for note_data in notes_data[:max_notes]:
        try:
            paper_info = note_data.get('paper_info', {}) if isinstance(note_data.get('paper_info'), dict) else {}
            note = Note(
                title=note_data.get('title', 'Untitled')[:200],
                content=note_data.get('content', ''),
                author_id=user.id,
                paper_title=paper_info.get('title', '')[:500],
                paper_journal=paper_info.get('venue', '')[:200],
                paper_pub_date=str(paper_info.get('year', '')) if paper_info.get('year') else None,
                paper_doi=paper_info.get('doi', '')[:100],
                paper_pmid=str(paper_info.get('pmid', ''))[:20] if paper_info.get('pmid') else None,
                media_urls='[]'
            )
            db.session.add(note)
            count += 1
        except Exception as e:
            print(f"跳过一条笔记: {e}")
            continue
    
    db.session.commit()
    print(f"成功导入 {count} 篇笔记！")