#!/usr/bin/env python3
"""
ProteinHub arXiv 论文获取器
使用 arXiv API 获取真实论文数据（更快更稳定）
"""
import json
import random
import urllib.request
import urllib.parse
from datetime import datetime
from typing import List, Dict
import xml.etree.ElementTree as ET

class ArxivFetcher:
    """arXiv 论文获取器"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    # 蛋白/代谢相关搜索词
    SEARCH_QUERIES = [
        "lipid droplet protein",
        "adipose tissue metabolism",
        "lipid metabolism obesity",
        "fatty liver NAFLD",
        "brown adipose thermogenesis",
        "lipolysis hormone sensitive",
        "triglyceride lipase ATGL",
        "perilipin lipid droplet",
        "CIDEA CIDEB lipid",
        "cellular lipid storage",
    ]
    
    def __init__(self):
        self.timeout = 30
    
    def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        """搜索 arXiv 论文"""
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        try:
            query_str = urllib.parse.urlencode(params)
            url = f"{self.BASE_URL}?{query_str}"
            
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "ProteinHub/1.0"}
            )
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                xml_data = response.read()
                return self._parse_arxiv_xml(xml_data)
                
        except Exception as e:
            print(f"搜索失败 {query}: {e}")
            return []
    
    def _parse_arxiv_xml(self, xml_data: bytes) -> List[Dict]:
        """解析 arXiv Atom XML"""
        papers = []
        
        try:
            # 注册命名空间
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            root = ET.fromstring(xml_data)
            
            for entry in root.findall('atom:entry', ns):
                paper = {}
                
                # 标题
                title_elem = entry.find('atom:title', ns)
                paper["title"] = title_elem.text.strip() if title_elem is not None else "Unknown"
                
                # 作者
                authors = []
                for author in entry.findall('atom:author', ns):
                    name_elem = author.find('atom:name', ns)
                    if name_elem is not None:
                        authors.append(name_elem.text)
                paper["authors"] = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "") if authors else "Unknown"
                
                # 发表日期
                published = entry.find('atom:published', ns)
                if published is not None:
                    date_str = published.text[:4]
                    paper["year"] = int(date_str)
                else:
                    paper["year"] = datetime.now().year
                
                # arXiv ID / DOI 替代
                id_elem = entry.find('atom:id', ns)
                if id_elem is not None:
                    arxiv_id = id_elem.text.split('/')[-1]
                    paper["doi"] = f"10.arxiv.{arxiv_id}"
                    paper["arxiv_id"] = arxiv_id
                else:
                    paper["doi"] = f"10.arxiv.{random.randint(10000,99999)}"
                    paper["arxiv_id"] = ""
                
                # 期刊（arXiv 是预印本）
                paper["journal"] = "arXiv"
                
                # 摘要
                summary = entry.find('atom:summary', ns)
                paper["abstract"] = summary.text.strip()[:500] if summary is not None else ""
                
                # 链接
                paper["url"] = f"https://arxiv.org/abs/{paper['arxiv_id']}" if paper['arxiv_id'] else ""
                
                papers.append(paper)
                
        except Exception as e:
            print(f"解析XML失败: {e}")
            
        return papers


class ArxivNoteExpander:
    """基于 arXiv 论文的笔记扩展器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = "/root/.openclaw/workspace/projects/proteinhub/data/notes_database.json"
        else:
            self.db_path = db_path
        
        self.fetcher = ArxivFetcher()
        self.notes = self._load_notes()
        self.current_id = len(self.notes) + 1
        
        # 蛋白检测关键词
        self.protein_keywords = {
            "CIDEA": ["CIDEA", "CIDE-A", "cell death-inducing DFFA-like effector a"],
            "CIDEB": ["CIDEB", "CIDE-B"],
            "CIDEC": ["CIDEC", "CIDE-C", "FSP27", "FSP-27"],
            "PLIN1": ["PLIN1", "PLIN-1", "perilipin 1", "perilipin-1"],
            "PLIN2": ["PLIN2", "PLIN-2", "ADRP", "adipophilin"],
            "PLIN3": ["PLIN3", "PLIN-3", "TIP47", "TIP-47"],
            "PLIN5": ["PLIN5", "PLIN-5", "LSDP5", "OXPAT"],
            "ATGL": ["ATGL", "PNPLA2", "desnutrin", "adipose triglyceride lipase"],
            "HSL": ["HSL", "hormone-sensitive lipase", "hormone sensitive lipase", "LIPE"],
            "CGI-58": ["CGI-58", "CGI58", "ABHD5"],
        }
    
    def _load_notes(self) -> List[Dict]:
        """加载现有笔记"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            import os
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            return []
    
    def _save_notes(self):
        """保存笔记"""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)
    
    def detect_protein(self, title: str, abstract: str) -> str:
        """检测论文涉及的蛋白"""
        text = (title + " " + abstract).lower()
        
        for protein, keywords in self.protein_keywords.items():
            for kw in keywords:
                if kw.lower() in text:
                    return protein
        
        # 默认根据内容推测
        if "lipid droplet" in text:
            return "Lipid Droplet"
        elif "lipolysis" in text:
            return "Lipolysis"
        elif "adipose" in text:
            return "Adipose"
        else:
            return "Metabolism"
    
    def generate_note(self, paper: Dict, angle: str) -> Dict:
        """生成笔记"""
        protein = self.detect_protein(paper["title"], paper.get("abstract", ""))
        
        # 样式
        gradients = [
            "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
            "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
            "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        ]
        
        emojis = {
            "CIDEA": "🧬", "CIDEB": "🔬", "CIDEC": "⚗️",
            "PLIN1": "🔥", "PLIN2": "💧", "PLIN3": "💨",
            "PLIN5": "⚡", "ATGL": "⚔️", "HSL": "🗡️",
            "CGI-58": "🛡️", "Lipid Droplet": "🧪",
            "Lipolysis": "🔥", "Adipose": "🫁", "Metabolism": "⚙️"
        }
        
        # 标题
        year = paper["year"]
        title_emoji = {"机制解析": "🔬", "临床意义": "💊", "研究故事": "📖"}.get(angle, "💡")
        
        titles = {
            "机制解析": f"{title_emoji} {protein}新机制：{paper['title'][:35]}...",
            "临床意义": f"{title_emoji} {protein}应用：{paper['title'][:30]}...",
            "研究故事": f"{title_emoji} {year}年{protein}研究：{paper['title'][:30]}...",
        }
        
        title = titles.get(angle, f"💡 {protein}：{paper['title'][:40]}")
        
        # 内容
        abstract_preview = paper.get("abstract", "")[:300]
        
        content = f"""发现一篇{year}年的真实研究！📄

【论文标题】
{paper['title']}

【作者团队】
{paper['authors']}

【发表平台】
arXiv preprint ({year})

【研究摘要】
{abstract_preview}...

【涉及蛋白/主题】
{protein}

【原文链接】
{paper.get('url', f"https://arxiv.org/abs/{paper.get('arxiv_id', '')}")}

【为什么值得关注】
这篇预印本论文提供了{protein}相关研究的最新进展，值得关注其后续发表情况。"""
        
        note = {
            "id": self.current_id,
            "title": title,
            "author": f"{protein}研究组",
            "avatar": emojis.get(protein, "🧬"),
            "likes": str(random.randint(300, 4000)),
            "emoji": emojis.get(protein, "🧬"),
            "gradient": random.choice(gradients),
            "protein": protein,
            "angle": angle,
            "content": content,
            "tags": [f"#{protein}", f"#{year}", "#arXiv", "#预印本"],
            "date": datetime.now().strftime("%m-%d"),
            "location": random.choice(["北京", "上海", "广州", "深圳", "杭州", "南京", "武汉"]),
            "paper": {
                "title": paper["title"],
                "authors": paper["authors"],
                "journal": "arXiv",
                "year": paper["year"],
                "doi": paper["doi"],
                "arxiv_id": paper.get("arxiv_id", ""),
                "url": paper.get("url", "")
            },
            "created_at": datetime.now().isoformat(),
            "source": "arXiv API"
        }
        
        self.current_id += 1
        return note
    
    def expand(self, target_count: int = 100) -> int:
        """扩展笔记库"""
        print(f"使用 arXiv API 获取真实论文")
        print(f"目标: {target_count} 条，当前: {len(self.notes)} 条")
        
        expanded = 0
        angles = ["机制解析", "临床意义", "研究故事"]
        
        for query in self.fetcher.SEARCH_QUERIES:
            if expanded >= target_count:
                break
            
            print(f"\n搜索: {query}")
            papers = self.fetcher.search_papers(query, max_results=20)
            
            if not papers:
                continue
            
            print(f"  找到 {len(papers)} 篇")
            
            for paper in papers:
                if expanded >= target_count:
                    break
                
                angle = random.choice(angles)
                note = self.generate_note(paper, angle)
                self.notes.append(note)
                expanded += 1
                
                print(f"  [{expanded}/{target_count}] {paper['title'][:40]}...")
        
        self._save_notes()
        print(f"\n✅ 完成！新增 {expanded} 条真实论文笔记")
        return expanded


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--db-path", type=str)
    args = parser.parse_args()
    
    print("="*60)
    print("ProteinHub arXiv 真实论文扩展")
    print("="*60)
    
    expander = ArxivNoteExpander(db_path=args.db_path)
    count = expander.expand(target_count=args.target)
    
    print("="*60)
    print(f"新增 {count} 条笔记")
    print("="*60)


if __name__ == "__main__":
    main()
