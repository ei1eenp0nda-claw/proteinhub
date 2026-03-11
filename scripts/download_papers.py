#!/usr/bin/env python3
"""
ProteinHub 批量论文下载器
每周运行一次，下载大量真实论文到本地数据库
"""
import json
import os
import time
from datetime import datetime
from typing import List, Dict
import urllib.request
import urllib.parse
import urllib.error

class WeeklyPaperDownloader:
    """每周批量下载真实论文"""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    # 扩展的搜索词列表（覆盖更多蛋白和主题）
    SEARCH_QUERIES = [
        # 核心蛋白
        "CIDEA lipid droplet adipocyte",
        "CIDEB liver hepatic lipid",
        "CIDEC FSP27 CIDE-C lipid droplet",
        "PLIN1 perilipin adipose tissue",
        "PLIN2 ADRP lipid droplet hepatocyte", 
        "PLIN3 TIP47 lipid droplet",
        "PLIN4 S3-12 lipid droplet",
        "PLIN5 LSDP5 OXPAT mitochondria",
        "ATGL PNPLA2 lipolysis triglyceride",
        "HSL hormone-sensitive lipase LIPE",
        "CGI-58 ABHD5 ATGL coactivator",
        "MGL monoglyceride lipase MGLL",
        # 相关主题
        "lipid droplet biogenesis fusion",
        "lipid droplet protein coat PAT",
        "adipose tissue lipolysis fasting",
        "brown adipose thermogenesis UCP1",
        "white adipose beige browning",
        "obesity metabolic syndrome adipocyte",
        "NAFLD non-alcoholic fatty liver",
        "insulin resistance adipocyte lipolysis",
        "metabolic disease lipid storage",
        "diabetes type 2 adipose",
        "triglyceride storage mobilization",
        "fatty acid oxidation adipose",
    ]
    
    FIELDS = "title,authors,year,abstract,fieldsOfStudy,venue,externalIds,citationCount,influentialCitationCount"
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "/root/.openclaw/workspace/projects/proteinhub/data/raw_papers.json"
        self.papers = self._load_papers()
        print(f"当前本地论文库: {len(self.papers)} 篇")
    
    def _load_papers(self) -> List[Dict]:
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            return []
    
    def _save_papers(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.papers, f, ensure_ascii=False, indent=2)
    
    def search(self, query: str, limit: int = 100) -> List[Dict]:
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
                time.sleep(0.3)  # 限速
                return data.get("data", [])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  速率限制，等待 5 秒...")
                time.sleep(5)
                return self.search(query, limit)
            print(f"  错误: {e}")
            return []
        except Exception as e:
            print(f"  错误: {e}")
            return []
    
    def download_batch(self, target_total: int = 5000) -> int:
        """
        批量下载论文到本地库
        目标：每周下载 5000 篇真实论文
        """
        print(f"\n开始批量下载真实论文")
        print(f"目标: {target_total} 篇新论文")
        print(f"当前已有: {len(self.papers)} 篇")
        
        downloaded = 0
        seen_ids = {p.get("paperId") for p in self.papers}
        
        for query in self.SEARCH_QUERIES:
            if downloaded >= target_total:
                break
            
            print(f"\n搜索: {query}")
            papers = self.search(query, limit=100)
            
            new_papers = []
            for p in papers:
                paper_id = p.get("paperId")
                if paper_id and paper_id not in seen_ids:
                    # 确保有基本字段
                    if p.get("title") and p.get("year"):
                        new_papers.append(p)
                        seen_ids.add(paper_id)
            
            print(f"  找到 {len(new_papers)} 篇新论文")
            self.papers.extend(new_papers)
            downloaded += len(new_papers)
            
            # 每 500 篇保存一次
            if len(self.papers) % 500 < 100:
                self._save_papers()
                print(f"  已保存 {len(self.papers)} 篇到本地库")
        
        self._save_papers()
        print(f"\n✅ 批量下载完成！")
        print(f"新增: {downloaded} 篇")
        print(f"总计: {len(self.papers)} 篇")
        return downloaded


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=5000, help="目标下载数量")
    args = parser.parse_args()
    
    print("="*70)
    print("ProteinHub 每周批量论文下载 (Semantic Scholar)")
    print("="*70)
    
    downloader = WeeklyPaperDownloader()
    count = downloader.download_batch(target_total=args.target)
    
    print("="*70)
    print(f"下载完成！新增 {count} 篇真实论文到本地库")
    print("="*70)


if __name__ == "__main__":
    main()
