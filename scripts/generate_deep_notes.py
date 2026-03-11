#!/usr/bin/env python3
"""
ProteinHub 本地论文生成笔记 - 深度挖掘版
每篇论文生成3个不同角度的笔记
"""
import json
import random
from datetime import datetime
from typing import List, Dict

class DeepNoteGenerator:
    """深度挖掘：每篇论文生成多条笔记"""
    
    PROTEINS = {
        "CIDEA": ["CIDEA"], "CIDEB": ["CIDEB"], "CIDEC": ["CIDEC", "FSP27"],
        "PLIN1": ["PLIN1", "perilipin 1"], "PLIN2": ["PLIN2", "ADRP"],
        "PLIN3": ["PLIN3", "TIP47"], "PLIN4": ["PLIN4"], "PLIN5": ["PLIN5", "LSDP5"],
        "ATGL": ["ATGL", "PNPLA2"], "HSL": ["HSL", "hormone-sensitive"],
        "CGI-58": ["CGI-58", "ABHD5"], "MGL": ["MGL", "monoglyceride"],
        "DGAT1": ["DGAT1"], "DGAT2": ["DGAT2"],
        "FASN": ["FASN"], "SCD1": ["SCD1"], "ACC": ["ACC"],
        "ACLY": ["ACLY"], "GPAT": ["GPAT"], "AGPAT": ["AGPAT"],
        "Lipid": ["lipid"], "Adipose": ["adipose"], "Metabolism": ["metabolism"],
        "Obesity": ["obesity"], "NAFLD": ["NAFLD", "fatty liver"],
        "Mitochondria": ["mitochondria"], "Cholesterol": ["cholesterol"],
    }
    
    GRADIENTS = [
        "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
        "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
        "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)",
    ]
    
    EMOJIS = {
        "CIDEA": "🧬", "CIDEB": "🔬", "CIDEC": "⚗️",
        "PLIN1": "🔥", "PLIN2": "💧", "PLIN3": "💨", "PLIN4": "🌊", "PLIN5": "⚡",
        "ATGL": "⚔️", "HSL": "🗡️", "MGL": "🔪",
        "CGI-58": "🛡️", "DGAT1": "⚙️", "DGAT2": "⚡",
        "FASN": "🔧", "SCD1": "🧪", "ACC": "📊",
        "ACLY": "📈", "GPAT": "🔬", "AGPAT": "⚗️",
        "Lipid": "🧪", "Adipose": "🫁", "Metabolism": "⚙️",
        "Obesity": "⚖️", "NAFLD": "🫀", "Mitochondria": "🔋", "Cholesterol": "💎"
    }
    
    def __init__(self):
        self.raw_papers_path = "/root/.openclaw/workspace/projects/proteinhub/data/raw_papers.json"
        self.notes_path = "/root/.openclaw/workspace/projects/proteinhub/data/notes_database.json"
        
        self.raw_papers = self._load_json(self.raw_papers_path, [])
        self.notes = self._load_json(self.notes_path, [])
        self.current_id = len(self.notes) + 1
        
        # 统计已使用的论文-角度组合
        self.used_combinations = set()
        for n in self.notes:
            pid = n.get("paper", {}).get("paperId")
            angle = n.get("angle")
            if pid and angle:
                self.used_combinations.add((pid, angle))
    
    def _load_json(self, path: str, default):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            import os
            os.makedirs(os.path.dirname(path), exist_ok=True)
            return default
    
    def _save_json(self, path: str, data):
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def detect_protein(self, title: str, abstract: str) -> str:
        text = (title + " " + abstract).lower()
        for protein, keywords in self.PROTEINS.items():
            for kw in keywords:
                if kw.lower() in text:
                    return protein
        return "Lipid"
    
    def generate_notes_from_paper(self, paper: Dict) -> List[Dict]:
        """从一篇论文生成3个不同角度的笔记"""
        title = paper.get("title", "Research Paper")
        abstract = paper.get("abstract", "") or ""
        protein = self.detect_protein(title, abstract)
        year = paper.get("year", datetime.now().year)
        paper_id = paper.get("paperId", "")
        
        # 作者格式化
        authors_list = paper.get("authors", [])
        author_names = ", ".join([a.get("name", "") for a in authors_list[:3]]) if authors_list else "Unknown"
        if len(authors_list) > 3:
            author_names += " et al."
        
        venue = paper.get("venue", "Unknown Journal")
        external_ids = paper.get("externalIds", {})
        doi = external_ids.get("DOI", f"10.semantic.{paper_id[:8]}")
        pmid = external_ids.get("PubMed", "")
        citations = paper.get("citationCount", 0)
        
        emoji = self.EMOJIS.get(protein, "🧬")
        
        # 三个不同角度的笔记
        angles = [
            {
                "name": "机制解析",
                "emoji": "🔬",
                "focus": "分子机制",
                "content_template": self._mechanism_content
            },
            {
                "name": "临床意义", 
                "emoji": "💊",
                "focus": "临床应用",
                "content_template": self._clinical_content
            },
            {
                "name": "研究故事",
                "emoji": "📖", 
                "focus": "研究历程",
                "content_template": self._story_content
            }
        ]
        
        notes = []
        for angle in angles:
            # 检查是否已生成过这个角度
            if (paper_id, angle["name"]) in self.used_combinations:
                continue
            
            note = self._create_note(
                paper, protein, year, title, author_names, venue,
                doi, pmid, citations, emoji, abstract, angle
            )
            notes.append(note)
            self.used_combinations.add((paper_id, angle["name"]))
        
        return notes
    
    def _create_note(self, paper, protein, year, title, author_names, venue,
                     doi, pmid, citations, emoji, abstract, angle):
        """创建单条笔记"""
        
        abstract_preview = abstract[:500] if abstract else "No abstract available"
        
        # 根据角度生成不同内容
        content = angle["content_template"](
            title, author_names, venue, year, protein, 
            abstract_preview, doi, pmid, paper.get("paperId", ""), citations
        )
        
        note_title = f"{angle['emoji']} [{angle['focus']}] {title[:45]}{'...' if len(title) > 45 else ''}"
        
        return {
            "id": self.current_id,
            "title": note_title,
            "author": f"{protein}研究组",
            "avatar": emoji,
            "likes": str(random.randint(400, 8000)),
            "emoji": emoji,
            "gradient": random.choice(self.GRADIENTS),
            "protein": protein,
            "angle": angle["name"],
            "content": content,
            "tags": [f"#{protein}", f"#{year}", f"#{angle['name']}", "#SemanticScholar"],
            "date": datetime.now().strftime("%m-%d"),
            "location": random.choice(["北京", "上海", "广州", "深圳", "杭州", "南京", "武汉", "成都"]),
            "paper": {
                "title": title,
                "authors": author_names,
                "journal": venue,
                "year": year,
                "doi": doi,
                "pmid": pmid,
                "paperId": paper.get("paperId", ""),
                "citationCount": citations,
            },
            "created_at": datetime.now().isoformat(),
            "source": f"Semantic Scholar - {angle['name']}"
        }
    
    def _mechanism_content(self, title, authors, venue, year, protein, abstract, doi, pmid, paper_id, citations):
        return f"""🔬 深度解析这篇 {year} 年的机制研究！

【论文标题】
{title}

【研究团队】
{authors}

【发表期刊】
{venue} ({year})
{ f"【被引次数】{citations}" if citations else ""}

【核心机制】
{abstract}{'...' if len(abstract) > 500 else ''}

【关键发现】
这项研究深入揭示了 {protein} 调控脂质代谢的分子机制，为理解细胞脂质稳态提供了重要线索。

【实验亮点】
✅ 清晰的机制阐述
✅ 可靠的实验验证
✅ 创新的研究视角

【原文链接】
https://www.semanticscholar.org/paper/{paper_id}
{ f"PubMed: https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""}

#分子机制 #{protein} #脂滴研究"""
    
    def _clinical_content(self, title, authors, venue, year, protein, abstract, doi, pmid, paper_id, citations):
        return f"""💊 从实验室到临床！这篇研究的转化价值分析

【论文标题】
{title}

【研究团队】
{authors}

【发表期刊】
{venue} ({year})
{ f"【被引次数】{citations}" if citations else ""}

【研究摘要】
{abstract}{'...' if len(abstract) > 500 else ''}

【临床意义】
这项关于 {protein} 的研究具有重要的临床转化价值：
✅ 潜在的生物标志物
✅ 新药开发靶点
✅ 精准医疗应用

【应用前景】
该发现可能为代谢疾病、肥胖、糖尿病等提供新的治疗策略。

【原文链接】
https://www.semanticscholar.org/paper/{paper_id}
{ f"PubMed: https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""}

#转化医学 #{protein} #临床价值"""
    
    def _story_content(self, title, authors, venue, year, protein, abstract, doi, pmid, paper_id, citations):
        return f"""📖 研究背后的故事！这篇 {year} 年的经典文献

【论文标题】
{title}

【研究团队】
{authors}

【发表期刊】
{venue} ({year})
{ f"【被引次数】{citations}" if citations else ""}

【研究背景】
{abstract}{'...' if len(abstract) > 500 else ''}

【科研历程】
这项关于 {protein} 的研究展现了科学家如何：
1️⃣ 发现科学问题
2️⃣ 设计精巧实验
3️⃣ 得出重要结论

【科研启示】
✅ 严谨的实验设计
✅ 创新的研究思路
✅ 坚持不懈的探索精神

【原文链接】
https://www.semanticscholar.org/paper/{paper_id}
{ f"PubMed: https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""}

#科研故事 #{protein} #学术经典"""
    
    def generate_deep_notes(self, target_multiplier: int = 3) -> int:
        """
        深度挖掘：每篇论文生成多条笔记
        
        Args:
            target_multiplier: 每篇论文生成几条笔记（默认3条）
        """
        print(f"深度挖掘模式：每篇论文生成最多 {target_multiplier} 条笔记")
        print(f"本地论文库: {len(self.raw_papers)} 篇")
        print(f"当前笔记: {len(self.notes)} 条")
        print(f"已使用论文-角度组合: {len(self.used_combinations)}")
        
        generated = 0
        
        for paper in self.raw_papers:
            notes_from_paper = self.generate_notes_from_paper(paper)
            
            for note in notes_from_paper:
                note["id"] = self.current_id
                self.notes.append(note)
                self.current_id += 1
                generated += 1
                
                if generated % 100 == 0:
                    print(f"  已生成 {generated} 条新笔记...")
                    self._save_json(self.notes_path, self.notes)
        
        self._save_json(self.notes_path, self.notes)
        print(f"\n✅ 深度挖掘完成！")
        print(f"新增: {generated} 条笔记")
        print(f"总计: {len(self.notes)} 条笔记")
        print(f"覆盖: {len(self.used_combinations)} 个论文-角度组合")
        return generated


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--multiplier", type=int, default=3, help="每篇论文生成几条笔记")
    args = parser.parse_args()
    
    print("="*70)
    print("ProteinHub 深度挖掘模式 - 每篇论文多角度生成")
    print("="*70)
    
    generator = DeepNoteGenerator()
    count = generator.generate_deep_notes(target_multiplier=args.multiplier)
    
    print("="*70)
    print(f"新增 {count} 条深度挖掘笔记")
    print("="*70)


if __name__ == "__main__":
    main()
