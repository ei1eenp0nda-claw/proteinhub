#!/usr/bin/env python3
"""
ProteinHub 本地论文生成笔记
每小时从本地论文库中快速生成笔记（无API调用）
"""
import json
import random
from datetime import datetime
from typing import List, Dict

class LocalNoteGenerator:
    """从本地论文库生成笔记"""
    
    PROTEINS = {
        "CIDEA": ["CIDEA"], "CIDEB": ["CIDEB"], "CIDEC": ["CIDEC", "FSP27"],
        "PLIN1": ["PLIN1", "perilipin 1"], "PLIN2": ["PLIN2", "ADRP"],
        "PLIN3": ["PLIN3", "TIP47"], "PLIN4": ["PLIN4"], "PLIN5": ["PLIN5", "LSDP5"],
        "ATGL": ["ATGL", "PNPLA2"], "HSL": ["HSL", "hormone-sensitive"],
        "CGI-58": ["CGI-58", "ABHD5"], "MGL": ["MGL", "monoglyceride"],
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
        "CGI-58": "🛡️",
        "Lipid": "🧪", "Adipose": "🫁", "Metabolism": "⚙️", "Obesity": "⚖️"
    }
    
    def __init__(self):
        self.raw_papers_path = "/root/.openclaw/workspace/projects/proteinhub/data/raw_papers.json"
        self.notes_path = "/root/.openclaw/workspace/projects/proteinhub/data/notes_database.json"
        
        self.raw_papers = self._load_json(self.raw_papers_path, [])
        self.notes = self._load_json(self.notes_path, [])
        self.used_paper_ids = {n.get("paper", {}).get("paperId") for n in self.notes if n.get("paper", {}).get("paperId")}
        
        print(f"本地论文库: {len(self.raw_papers)} 篇")
        print(f"已使用: {len(self.used_paper_ids)} 篇")
        print(f"可用: {len(self.raw_papers) - len(self.used_paper_ids)} 篇")
    
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
    
    def generate_note(self, paper: Dict, angle: str, note_id: int) -> Dict:
        """基于本地论文生成笔记"""
        title = paper.get("title", "Research Paper")
        abstract = paper.get("abstract", "") or ""
        protein = self.detect_protein(title, abstract)
        year = paper.get("year", datetime.now().year)
        
        # 作者格式化
        authors_list = paper.get("authors", [])
        author_names = ", ".join([a.get("name", "") for a in authors_list[:3]]) if authors_list else "Unknown"
        if len(authors_list) > 3:
            author_names += " et al."
        
        venue = paper.get("venue", "Unknown Journal")
        external_ids = paper.get("externalIds", {})
        doi = external_ids.get("DOI", paper.get("doi", f"10.semantic.{paper.get('paperId', '')[:8]}"))
        pmid = external_ids.get("PubMed", "")
        paper_id = paper.get("paperId", "")
        
        # 引用数（如果有）
        citations = paper.get("citationCount", 0)
        
        # 根据角度生成不同内容
        angle_emoji = {"机制解析": "🔬", "临床意义": "💊", "研究故事": "📖"}.get(angle, "💡")
        emoji = self.EMOJIS.get(protein, "🧬")
        
        # 标题
        note_title = f"{angle_emoji} {title[:55]}{'...' if len(title) > 55 else ''}"
        
        # 内容（基于真实论文）
        abstract_preview = abstract[:600] if abstract else "No abstract available"
        
        content_parts = [
            f"发现一篇 {year} 年的真实研究！📄",
            "",
            "【论文标题】",
            title,
            "",
            "【研究团队】",
            author_names,
            "",
            "【发表期刊】",
            f"{venue} ({year})",
        ]
        
        if citations > 0:
            content_parts.extend(["", f"【被引次数】{citations}"])
        
        content_parts.extend([
            "",
            "【研究摘要】",
            f"{abstract_preview}{'...' if len(abstract) > 600 else ''}",
            "",
            f"【涉及蛋白】{protein}",
            "",
            "【原文链接】",
            f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else f"DOI: {doi}",
        ])
        
        if pmid:
            content_parts.append(f"PubMed: https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
        
        content = "\n".join(content_parts)
        
        return {
            "id": note_id,
            "title": note_title,
            "author": f"{protein}研究组",
            "avatar": emoji,
            "likes": str(random.randint(300, 6000)),
            "emoji": emoji,
            "gradient": random.choice(self.GRADIENTS),
            "protein": protein,
            "angle": angle,
            "content": content,
            "tags": [f"#{protein}", f"#{year}", f"#{venue[:15]}".replace(" ", "")],
            "date": datetime.now().strftime("%m-%d"),
            "location": random.choice(["北京", "上海", "广州", "深圳", "杭州", "南京", "武汉"]),
            "paper": {
                "title": title,
                "authors": author_names,
                "journal": venue,
                "year": year,
                "doi": doi,
                "pmid": pmid,
                "paperId": paper_id,
                "citationCount": citations,
            },
            "created_at": datetime.now().isoformat(),
            "source": "Semantic Scholar (本地库)"
        }
    
    def generate_notes(self, target: int = 1000) -> int:
        """
        从本地论文库生成笔记
        每小时目标：1000 条
        """
        print(f"\n从本地论文库生成笔记")
        print(f"目标: {target} 条")
        print(f"当前笔记: {len(self.notes)} 条")
        
        # 获取未使用的论文
        available_papers = [p for p in self.raw_papers if p.get("paperId") not in self.used_paper_ids]
        
        if len(available_papers) < target:
            print(f"⚠️ 本地论文不足！可用 {len(available_papers)} 篇，需要 {target}")
            print("建议运行: python3 scripts/download_papers.py --target 5000")
            target = len(available_papers)
        
        if target == 0:
            print("❌ 没有可用论文！请先运行下载脚本")
            return 0
        
        # 随机打乱，确保多样性
        random.shuffle(available_papers)
        
        angles = ["机制解析", "临床意义", "研究故事"]
        generated = 0
        
        for paper in available_papers[:target]:
            angle = random.choice(angles)
            note_id = len(self.notes) + 1
            
            note = self.generate_note(paper, angle, note_id)
            self.notes.append(note)
            self.used_paper_ids.add(paper.get("paperId"))
            generated += 1
            
            if generated % 100 == 0:
                print(f"  已生成 {generated}/{target}...")
        
        self._save_json(self.notes_path, self.notes)
        print(f"\n✅ 完成！新增 {generated} 条笔记")
        print(f"总计: {len(self.notes)} 条笔记")
        return generated


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=1000)
    args = parser.parse_args()
    
    print("="*70)
    print("ProteinHub 本地论文生成笔记 (每小时快速生成)")
    print("="*70)
    
    generator = LocalNoteGenerator()
    count = generator.generate_notes(target=args.target)
    
    print("="*70)
    print(f"生成完成！新增 {count} 条笔记")
    print("="*70)


if __name__ == "__main__":
    main()
