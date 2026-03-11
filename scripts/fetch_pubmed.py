#!/usr/bin/env python3
"""
ProteinHub PubMed 论文获取器
使用 PubMed E-utilities API 获取真实生物医学论文
"""
import json
import random
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict
import time

class PubMedFetcher:
    """PubMed E-utilities API 封装"""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # 蛋白研究相关搜索词（生物学/医学）
    SEARCH_TERMS = [
        "CIDEA[Title/Abstract] AND (lipid droplet OR adipocyte)",
        "CIDEB[Title/Abstract] AND (liver OR hepatic)",
        "CIDEC[Title/Abstract] OR FSP27[Title/Abstract]",
        "PLIN1[Title/Abstract] AND (lipid droplet OR adipose)",
        "PLIN2[Title/Abstract] OR ADRP[Title/Abstract]",
        "PLIN3[Title/Abstract] OR TIP47[Title/Abstract]",
        "ATGL[Title/Abstract] OR PNPLA2[Title/Abstract]",
        "HSL[Title/Abstract] OR hormone-sensitive lipase",
        "CGI-58[Title/Abstract] OR ABHD5[Title/Abstract]",
        "lipid droplet[Title/Abstract] AND (fusion OR biogenesis)",
        "lipolysis[Title/Abstract] AND (adipose OR fat)",
        "obesity[Title/Abstract] AND (lipid metabolism OR lipolysis)",
        "NAFLD[Title/Abstract] OR fatty liver[Title/Abstract]",
        "brown adipose[Title/Abstract] AND thermogenesis",
        "perilipin[Title/Abstract] AND lipid droplet",
        "adipocyte[Title/Abstract] AND lipolysis",
        "metabolic syndrome[Title/Abstract] AND lipid",
        "insulin resistance[Title/Abstract] AND adipose",
    ]
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.email = "proteinhub@research.org"  # NCBI 要求提供 email
        self.request_count = 0
        
    def _make_request(self, url: str, params: dict) -> bytes:
        """发送请求（带限速）"""
        # NCBI 限制：无 API key 时每秒不超过 3 次请求
        if self.request_count > 0 and not self.api_key:
            time.sleep(0.4)
        
        query = urllib.parse.urlencode(params)
        full_url = f"{url}?{query}"
        
        req = urllib.request.Request(
            full_url,
            headers={
                "User-Agent": f"ProteinHub/1.0 ({self.email})"
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                self.request_count += 1
                return response.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("  达到速率限制，等待 1 秒...")
                time.sleep(1)
                return self._make_request(url, params)
            raise
    
    def search(self, term: str, max_results: int = 20) -> List[str]:
        """搜索论文，返回 PMID 列表"""
        url = f"{self.BASE_URL}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": term,
            "retmax": max_results,
            "retmode": "json",
            "sort": "date"
        }
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            data = json.loads(self._make_request(url, params))
            return data.get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            print(f"  搜索失败: {e}")
            return []
    
    def fetch_details(self, pmids: List[str]) -> List[Dict]:
        """获取论文详细信息"""
        if not pmids:
            return []
        
        url = f"{self.BASE_URL}/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            xml_data = self._make_request(url, params)
            return self._parse_xml(xml_data)
        except Exception as e:
            print(f"  获取详情失败: {e}")
            return []
    
    def _parse_xml(self, xml_data: bytes) -> List[Dict]:
        """解析 PubMed XML"""
        papers = []
        
        try:
            root = ET.fromstring(xml_data)
            
            for article in root.findall(".//PubmedArticle"):
                paper = {}
                
                # PMID
                pmid_elem = article.find(".//PMID")
                paper["pmid"] = pmid_elem.text if pmid_elem is not None else ""
                
                # 标题
                title_elem = article.find(".//ArticleTitle")
                paper["title"] = title_elem.text if title_elem is not None else "No title"
                
                # 作者
                authors = []
                for author in article.findall(".//Author"):
                    last = author.find("LastName")
                    first = author.find("ForeName")
                    if last is not None:
                        name = last.text
                        if first is not None:
                            name = f"{first.text} {name}"
                        authors.append(name)
                paper["authors"] = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "") if authors else "Unknown"
                
                # 期刊
                journal_elem = article.find(".//Journal/Title")
                paper["journal"] = journal_elem.text if journal_elem is not None else "Unknown"
                
                # 年份
                year = None
                year_elem = article.find(".//PubDate/Year")
                if year_elem is not None:
                    year = int(year_elem.text)
                else:
                    medline = article.find(".//PubDate/MedlineDate")
                    if medline is not None:
                        try:
                            year = int(medline.text[:4])
                        except:
                            pass
                paper["year"] = year if year else datetime.now().year
                
                # DOI
                doi_elem = article.find(".//ArticleId[@IdType='doi']")
                paper["doi"] = doi_elem.text if doi_elem is not None else f"10.pubmed.{paper['pmid']}"
                
                # 摘要
                abstract_elem = article.find(".//Abstract/AbstractText")
                paper["abstract"] = abstract_elem.text[:600] if abstract_elem is not None else ""
                
                # URL
                paper["url"] = f"https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/" if paper['pmid'] else ""
                
                papers.append(paper)
                
        except Exception as e:
            print(f"  解析 XML 失败: {e}")
        
        return papers


class PubMedNoteExpander:
    """基于 PubMed 真实论文的笔记扩展器"""
    
    PROTEIN_KEYWORDS = {
        "CIDEA": ["CIDEA", "CIDE-A", "cell death-inducing DFFA-like effector A"],
        "CIDEB": ["CIDEB", "CIDE-B"],
        "CIDEC": ["CIDEC", "CIDE-C", "FSP27", "FSP-27"],
        "PLIN1": ["PLIN1", "PLIN-1", "perilipin 1", "perilipin-1", "perilipin A"],
        "PLIN2": ["PLIN2", "PLIN-2", "ADRP", "adipophilin", "adipose differentiation-related protein"],
        "PLIN3": ["PLIN3", "PLIN-3", "TIP47", "tail-interacting protein 47"],
        "PLIN4": ["PLIN4", "PLIN-4", "S3-12"],
        "PLIN5": ["PLIN5", "PLIN-5", "LSDP5", "OXPAT"],
        "ATGL": ["ATGL", "PNPLA2", "desnutrin", "adipose triglyceride lipase", "calcium-independent phospholipase A2"],
        "HSL": ["HSL", "hormone-sensitive lipase", "hormone sensitive lipase", "LIPE"],
        "CGI-58": ["CGI-58", "CGI58", "ABHD5", "abhydrolase domain-containing protein 5"],
        "MGL": ["MGL", "monoglyceride lipase", "MGLL"],
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
        "Lipid Droplet": "🧪", "Lipolysis": "🔥", "Adipose": "🫁", 
        "Metabolism": "⚙️", "Obesity": "⚖️", "NAFLD": "🫀"
    }
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = "/root/.openclaw/workspace/projects/proteinhub/data/notes_database.json"
        else:
            self.db_path = db_path
        
        self.fetcher = PubMedFetcher()
        self.notes = self._load_notes()
        self.current_id = len(self.notes) + 1
    
    def _load_notes(self) -> List[Dict]:
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            import os
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            return []
    
    def _save_notes(self):
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)
    
    def detect_protein(self, title: str, abstract: str) -> str:
        """检测论文涉及的蛋白"""
        text = (title + " " + abstract).lower()
        
        for protein, keywords in self.PROTEIN_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    return protein
        
        # 根据内容推测
        text_upper = text.upper()
        if "LIPID DROPLET" in text_upper:
            return "Lipid Droplet"
        elif "LIPOLYSIS" in text_upper:
            return "Lipolysis"
        elif "ADIPOSE" in text_upper:
            return "Adipose"
        elif "OBESITY" in text_upper:
            return "Obesity"
        elif "NAFLD" in text_upper or "FATTY LIVER" in text_upper:
            return "NAFLD"
        else:
            return "Metabolism"
    
    def generate_note(self, paper: Dict, angle: str) -> Dict:
        """基于真实论文生成笔记"""
        protein = self.detect_protein(paper["title"], paper.get("abstract", ""))
        year = paper["year"]
        
        # 标题模板
        emojis_map = {"机制解析": "🔬", "临床意义": "💊", "研究故事": "📖"}
        emoji = emojis_map.get(angle, "💡")
        
        title = f"{emoji} {paper['title'][:50]}{'...' if len(paper['title']) > 50 else ''}"
        
        # 内容
        abstract_preview = paper.get("abstract", "")[:400]
        
        content = f"""发现一篇 {year} 年的真实研究！📄

【论文标题】
{paper['title']}

【研究团队】
{paper['authors']}

【发表期刊】
{paper['journal']} ({year})

【研究摘要】
{abstract_preview}{'...' if len(paper.get('abstract', '')) > 400 else ''}

【涉及蛋白/主题】
{protein}

【原文链接】
{paper.get('url', f"https://pubmed.ncbi.nlm.nih.gov/{paper.get('pmid', '')}/")}

【为什么值得关注】
这篇发表在 {paper['journal']} 的研究深入探讨了 {protein} 相关的分子机制，是理解脂质代谢的重要文献。"""
        
        note = {
            "id": self.current_id,
            "title": title,
            "author": f"{protein}研究组",
            "avatar": self.EMOJIS.get(protein, "🧬"),
            "likes": str(random.randint(300, 5000)),
            "emoji": self.EMOJIS.get(protein, "🧬"),
            "gradient": random.choice(self.GRADIENTS),
            "protein": protein,
            "angle": angle,
            "content": content,
            "tags": [f"#{protein}", f"#{year}", "#PubMed", f"#{paper['journal'][:20]}".replace(" ", "")],
            "date": datetime.now().strftime("%m-%d"),
            "location": random.choice(["北京", "上海", "广州", "深圳", "杭州", "南京", "武汉", "成都"]),
            "paper": {
                "title": paper["title"],
                "authors": paper["authors"],
                "journal": paper["journal"],
                "year": paper["year"],
                "doi": paper["doi"],
                "pmid": paper.get("pmid", ""),
                "url": paper.get("url", "")
            },
            "created_at": datetime.now().isoformat(),
            "source": "PubMed API (NCBI)"
        }
        
        self.current_id += 1
        return note
    
    def expand(self, target_count: int = 50) -> int:
        """扩展笔记库（使用真实 PubMed 论文）"""
        print(f"使用 PubMed API 获取真实生物医学论文")
        print(f"目标: {target_count} 条，当前: {len(self.notes)} 条")
        print("注意: PubMed API 有速率限制，可能需要较长时间")
        
        expanded = 0
        angles = ["机制解析", "临床意义", "研究故事"]
        
        for search_term in self.fetcher.SEARCH_TERMS:
            if expanded >= target_count:
                break
            
            print(f"\n搜索: {search_term}")
            pmids = self.fetcher.search(search_term, max_results=10)
            
            if not pmids:
                continue
            
            print(f"  找到 {len(pmids)} 篇")
            
            # 分批获取详情（避免请求过大）
            papers = self.fetcher.fetch_details(pmids[:10])
            
            for paper in papers:
                if expanded >= target_count:
                    break
                
                # 过滤：确保摘要不为空
                if not paper.get("abstract"):
                    continue
                
                angle = random.choice(angles)
                note = self.generate_note(paper, angle)
                self.notes.append(note)
                expanded += 1
                
                print(f"  [{expanded}/{target_count}] {paper['title'][:45]}... ({paper['journal']})")
        
        self._save_notes()
        print(f"\n✅ 完成！新增 {expanded} 条 PubMed 真实论文笔记")
        return expanded


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="ProteinHub PubMed 真实论文扩展")
    parser.add_argument("--target", type=int, default=50, help="目标数量（建议50-100，受API限制）")
    parser.add_argument("--db-path", type=str, help="数据库路径")
    
    args = parser.parse_args()
    
    print("="*70)
    print("ProteinHub PubMed 真实论文扩展（生物医学数据库）")
    print("="*70)
    
    expander = PubMedNoteExpander(db_path=args.db_path)
    count = expander.expand(target_count=args.target)
    
    print("="*70)
    print(f"新增 {count} 条基于 PubMed 真实论文的笔记")
    print("="*70)


if __name__ == "__main__":
    main()
