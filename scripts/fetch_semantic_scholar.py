#!/usr/bin/env python3
"""
ProteinHub Semantic Scholar 论文获取器
使用 Semantic Scholar API (免费、快速、覆盖生物医学)
API文档: https://api.semanticscholar.org/api-docs/
"""
import json
import random
import urllib.request
import urllib.parse
import urllib.error
import time  # 添加延迟
from datetime import datetime
from typing import List, Dict

class SemanticScholarFetcher:
    """Semantic Scholar API 封装"""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    # 蛋白研究相关查询
    QUERIES = [
        "CIDEA lipid droplet",
        "CIDEB liver lipid",
        "CIDEC FSP27 lipid droplet",
        "PLIN1 perilipin adipose",
        "PLIN2 ADRP lipid droplet",
        "PLIN3 TIP47",
        "PLIN5 LSDP5 mitochondria",
        "ATGL PNPLA2 lipolysis",
        "hormone-sensitive lipase HSL",
        "CGI-58 ABHD5 ATGL",
        "lipid droplet fusion biogenesis",
        "adipose tissue lipolysis",
        "brown adipose thermogenesis UCP1",
        "obesity lipid metabolism",
        "NAFLD fatty liver",
        "insulin resistance adipocyte",
    ]
    
    FIELDS = "title,authors,year,abstract,fieldsOfStudy,publicationTypes,venue,externalIds"
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索论文"""
        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "fields": self.FIELDS,
            "limit": limit,
            "offset": 0
        }
        
        try:
            query_str = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_str}"
            
            req = urllib.request.Request(
                full_url,
                headers={"User-Agent": "ProteinHub/1.0 (research@proteinhub.org)"}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read())
                # 添加延迟避免 429
                time.sleep(0.5)
                return data.get("data", [])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("  遇到速率限制，等待 3 秒...")
                time.sleep(3)
                return self.search(query, limit)  # 重试
            print(f"  搜索失败: {e}")
            return []
        except Exception as e:
            print(f"  搜索失败: {e}")
            return []
    
    def get_paper_details(self, paper_id: str) -> Dict:
        """获取单篇论文详情"""
        url = f"{self.BASE_URL}/paper/{paper_id}"
        params = {"fields": self.FIELDS}
        
        try:
            query_str = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_str}"
            
            req = urllib.request.Request(full_url)
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read())
        except:
            return {}


class ProteinNoteExpander:
    """基于 Semantic Scholar 的笔记扩展器"""
    
    PROTEINS = {
        "CIDEA": ["CIDEA", "cell death-inducing DFFA-like effector A"],
        "CIDEB": ["CIDEB", "CIDE-B"],
        "CIDEC": ["CIDEC", "FSP27"],
        "PLIN1": ["PLIN1", "perilipin 1"],
        "PLIN2": ["PLIN2", "ADRP"],
        "PLIN3": ["PLIN3", "TIP47"],
        "PLIN5": ["PLIN5", "LSDP5", "OXPAT"],
        "ATGL": ["ATGL", "PNPLA2", "desnutrin"],
        "HSL": ["HSL", "hormone-sensitive lipase", "LIPE"],
        "CGI-58": ["CGI-58", "ABHD5"],
    }
    
    GRADIENTS = [
        "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
        "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    ]
    
    EMOJIS = {
        "CIDEA": "🧬", "CIDEB": "🔬", "CIDEC": "⚗️",
        "PLIN1": "🔥", "PLIN2": "💧", "PLIN3": "💨", "PLIN5": "⚡",
        "ATGL": "⚔️", "HSL": "🗡️", "CGI-58": "🛡️",
        "Lipid": "🧪", "Adipose": "🫁", "Metabolism": "⚙️"
    }
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "/root/.openclaw/workspace/projects/proteinhub/data/notes_database.json"
        self.fetcher = SemanticScholarFetcher()
        self.notes = self._load_notes()
        self.current_id = len(self.notes) + 1
    
    def _load_notes(self):
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            import os
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            return []
    
    def _save_notes(self):
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)
    
    def detect_protein(self, title: str, abstract: str) -> str:
        title = title or ""
        abstract = abstract or ""
        text = (title + " " + abstract).lower()
        for protein, keywords in self.PROTEINS.items():
            for kw in keywords:
                if kw.lower() in text:
                    return protein
        return "Lipid"
    
    def generate_note(self, paper: Dict, angle: str) -> Dict:
        protein = self.detect_protein(paper.get("title", ""), paper.get("abstract", ""))
        year = paper.get("year", datetime.now().year)
        
        # 作者格式化
        authors = paper.get("authors", [])
        author_names = ", ".join([a.get("name", "") for a in authors[:3]])
        if len(authors) > 3:
            author_names += " et al."
        
        # 期刊/会议
        venue = paper.get("venue", "Unknown")
        
        # DOI
        external_ids = paper.get("externalIds", {})
        doi = external_ids.get("DOI", f"10.semantic.{paper.get('paperId', '')[:8]}")
        pmid = external_ids.get("PubMed", "")
        
        # URL
        url = f"https://www.semanticscholar.org/paper/{paper.get('paperId', '')}"
        
        # 内容
        abstract = paper.get("abstract", "") or "No abstract available"
        abstract_preview = abstract[:500]
        
        content = f"""发现一篇 {year} 年的真实生物医学研究！📄

【论文标题】
{paper.get('title', 'No title')}

【研究团队】
{author_names or 'Unknown'}

【发表期刊/会议】
{venue} ({year})

【研究摘要】
{abstract_preview}{'...' if len(abstract) > 500 else ''}

【涉及蛋白】
{protein}

【研究领域】
{', '.join((paper.get('fieldsOfStudy') or [])[:3]) or 'Lipid Metabolism'}

【原文链接】
{url}
{ f"PubMed: https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""}

【为什么值得关注】
这篇发表在 {venue} 的研究为理解 {protein} 在脂质代谢中的作用提供了重要证据。"""
        
        emoji = self.EMOJIS.get(protein, "🧬")
        
        note = {
            "id": self.current_id,
            "title": f"{emoji} {paper.get('title', 'Research')[:55]}{'...' if len(paper.get('title', '')) > 55 else ''}",
            "author": f"{protein}研究组",
            "avatar": emoji,
            "likes": str(random.randint(400, 6000)),
            "emoji": emoji,
            "gradient": random.choice(self.GRADIENTS),
            "protein": protein,
            "angle": angle,
            "content": content,
            "tags": [f"#{protein}", f"#{year}", "#SemanticScholar", f"#{venue[:15]}".replace(" ", "")],
            "date": datetime.now().strftime("%m-%d"),
            "location": random.choice(["北京", "上海", "广州", "深圳", "杭州", "南京"]),
            "paper": {
                "title": paper.get("title", ""),
                "authors": author_names,
                "journal": venue,
                "year": year,
                "doi": doi,
                "pmid": pmid,
                "paperId": paper.get("paperId", ""),
                "url": url
            },
            "created_at": datetime.now().isoformat(),
            "source": "Semantic Scholar API"
        }
        
        self.current_id += 1
        return note
    
    def expand(self, target: int = 100) -> int:
        print(f"使用 Semantic Scholar API 获取真实学术论文")
        print(f"目标: {target} 条，当前: {len(self.notes)} 条")
        
        expanded = 0
        angles = ["机制解析", "临床意义", "研究故事"]
        
        for query in self.fetcher.QUERIES:
            if expanded >= target:
                break
            
            print(f"\n搜索: {query}")
            papers = self.fetcher.search(query, limit=20)
            
            if not papers:
                continue
            
            print(f"  找到 {len(papers)} 篇")
            
            for paper in papers:
                if expanded >= target:
                    break
                
                # 过滤：必须有标题和年份
                if not paper.get("title") or not paper.get("year"):
                    continue
                
                angle = random.choice(angles)
                note = self.generate_note(paper, angle)
                self.notes.append(note)
                expanded += 1
                
                venue = paper.get("venue", "Unknown")
                print(f"  [{expanded}/{target}] {paper['title'][:40]}... ({venue})")
        
        self._save_notes()
        print(f"\n✅ 完成！新增 {expanded} 条真实学术论文笔记")
        return expanded


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--db-path", type=str)
    args = parser.parse_args()
    
    print("="*70)
    print("ProteinHub Semantic Scholar 真实学术论文扩展")
    print("="*70)
    
    expander = ProteinNoteExpander(db_path=args.db_path)
    count = expander.expand(target=args.target)
    
    print("="*70)
    print(f"新增 {count} 条笔记")
    print("="*70)


if __name__ == "__main__":
    main()
