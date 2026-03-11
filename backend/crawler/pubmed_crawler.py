"""
ProteinHub PubMed Crawler
PubMed 文献爬虫和摘要生成

功能：
1. 根据蛋白名称搜索 PubMed 文献
2. 获取文献摘要
3. 生成蛋白互作相关的帖子内容
"""
import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class PubMedCrawler:
    """
    PubMed 文献爬虫
    
    使用 NCBI E-utilities API
    https://www.ncbi.nlm.nih.gov/books/NBK25501/
    """
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, api_key: Optional[str] = None, delay: float = 0.34):
        """
        初始化爬虫
        
        Args:
            api_key: NCBI API key (可选，可提高请求频率)
            delay: 请求间隔（秒），无API key时建议0.34s
        """
        self.api_key = api_key
        self.delay = delay
        self.last_request_time = 0
    
    def _rate_limit(self):
        """请求频率限制"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict) -> requests.Response:
        """
        发送请求到 NCBI API
        
        Args:
            endpoint: API 端点
            params: 请求参数
            
        Returns:
            Response 对象
        """
        self._rate_limit()
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        return response
    
    def search_articles(
        self, 
        query: str, 
        max_results: int = 10,
        sort: str = 'relevance',
        date_range: Optional[tuple] = None
    ) -> List[Dict]:
        """
        搜索 PubMed 文献
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数
            sort: 排序方式 ('relevance', 'date')
            date_range: 日期范围 (start_date, end_date) 格式 'YYYY/MM/DD'
            
        Returns:
            文献ID列表
        """
        # Step 1: ESearch - 获取文献ID
        search_params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'sort': sort,
            'retmode': 'json'
        }
        
        if date_range:
            start, end = date_range
            search_params['mindate'] = start.replace('/', '-')
            search_params['maxdate'] = end.replace('/', '-')
        
        try:
            response = self._make_request('esearch.fcgi', search_params)
            data = response.json()
            
            id_list = data.get('esearchresult', {}).get('idlist', [])
            total_count = data.get('esearchresult', {}).get('count', 0)
            
            print(f"   找到 {total_count} 篇文献，获取前 {len(id_list)} 篇")
            
            if not id_list:
                return []
            
            # Step 2: ESummary - 获取文献摘要信息
            return self._fetch_article_summaries(id_list)
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []
    
    def _fetch_article_summaries(self, pmids: List[str]) -> List[Dict]:
        """
        获取文献摘要信息
        
        Args:
            pmids: PubMed ID 列表
            
        Returns:
            文献摘要列表
        """
        if not pmids:
            return []
        
        summary_params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'json'
        }
        
        try:
            response = self._make_request('esummary.fcgi', summary_params)
            data = response.json()
            
            articles = []
            for pmid in pmids:
                doc = data.get('result', {}).get(pmid, {})
                if doc:
                    article = {
                        'pmid': pmid,
                        'title': doc.get('title', ''),
                        'authors': [a.get('name', '') for a in doc.get('authors', [])[:5]],
                        'journal': doc.get('fulljournalname', ''),
                        'pub_date': doc.get('pubdate', ''),
                        'doi': doc.get('elocationid', '').replace('doi: ', '') if doc.get('elocationid') else None,
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    }
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            print(f"❌ 获取摘要失败: {e}")
            return []
    
    def fetch_abstract(self, pmid: str) -> Optional[str]:
        """
        获取单篇文献的完整摘要
        
        Args:
            pmid: PubMed ID
            
        Returns:
            摘要文本
        """
        fetch_params = {
            'db': 'pubmed',
            'id': pmid,
            'retmode': 'xml',
            'rettype': 'abstract'
        }
        
        try:
            response = self._make_request('efetch.fcgi', fetch_params)
            root = ET.fromstring(response.content)
            
            # 解析 XML 获取摘要
            abstract_text = []
            for abstract in root.findall('.//AbstractText'):
                if abstract.text:
                    abstract_text.append(abstract.text)
            
            return ' '.join(abstract_text) if abstract_text else None
            
        except Exception as e:
            print(f"❌ 获取摘要失败 (PMID:{pmid}): {e}")
            return None
    
    def search_protein_interactions(
        self, 
        protein_a: str, 
        protein_b: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict]:
        """
        搜索蛋白互作相关文献
        
        Args:
            protein_a: 第一个蛋白名称
            protein_b: 第二个蛋白名称（可选）
            max_results: 最大结果数
            
        Returns:
            相关文献列表
        """
        # 构建搜索查询
        if protein_b:
            # 搜索两个蛋白的互作
            query = f'({protein_a}[Title/Abstract] AND {protein_b}[Title/Abstract]) AND (interaction OR binding OR complex)'
        else:
            # 搜索单个蛋白的相关文献
            query = f'{protein_a}[Title/Abstract] AND (protein OR lipid droplet)'
        
        print(f"🔍 搜索: {query}")
        
        # 限制到近5年
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5*365)
        date_range = (
            start_date.strftime('%Y/%m/%d'),
            end_date.strftime('%Y/%m/%d')
        )
        
        return self.search_articles(query, max_results=max_results, date_range=date_range)
    
    def generate_post_content(self, article: Dict, protein_name: str) -> Dict:
        """
        从文献生成帖子内容
        
        Args:
            article: 文献信息字典
            protein_name: 蛋白名称
            
        Returns:
            帖子内容字典
        """
        title = article.get('title', '')
        authors = article.get('authors', [])
        journal = article.get('journal', '')
        pub_date = article.get('pub_date', '')
        
        # 生成帖子标题（吸引眼球的标题党风格）
        post_title = self._generate_title(title, protein_name)
        
        # 生成摘要
        summary = self._generate_summary(article, protein_name)
        
        return {
            'title': post_title,
            'summary': summary,
            'source_title': title,
            'source_url': article.get('url', ''),
            'source_journal': journal,
            'source_authors': authors,
            'source_date': pub_date,
            'pmid': article.get('pmid', '')
        }
    
    def _generate_title(self, paper_title: str, protein_name: str) -> str:
        """
        从论文标题生成吸引眼球的帖子标题
        
        Args:
            paper_title: 原论文标题
            protein_name: 蛋白名称
            
        Returns:
            帖子标题
        """
        # 简单规则：提取关键信息，添加emoji
        import re
        
        # 提取发现/机制/功能相关的短语
        patterns = [
            r'(?:reveals?|shows?|demonstrates?)\s+(.+?)(?:\.|$)',
            r'(?:regulates?|mediates?|controls?)\s+(.+?)(?:\.|$)',
            r'(?:novel\s+)?(?:role|function|mechanism)\s+of\s+(.+?)(?:\.|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, paper_title, re.IGNORECASE)
            if match:
                key_point = match.group(1).strip()
                return f"🧬 {protein_name} 新发现：{key_point}"
        
        # 默认标题
        return f"📑 {protein_name} 研究速递"
    
    def _generate_summary(self, article: Dict, protein_name: str) -> str:
        """
        生成文献摘要
        
        Args:
            article: 文献信息
            protein_name: 蛋白名称
            
        Returns:
            摘要文本
        """
        authors = article.get('authors', [])
        journal = article.get('journal', '')
        pub_date = article.get('pub_date', '')
        
        author_text = f"{authors[0]} 等" if len(authors) > 1 else (authors[0] if authors else 'Unknown')
        
        summary = f"**研究来源**: {author_text} | {journal} | {pub_date}\n\n"
        summary += f"**研究背景**: 该研究探索了 {protein_name} 的功能和机制。"
        
        return summary


class BatchPubMedCrawler:
    """批量爬虫，用于初始化数据"""
    
    def __init__(self, crawler: PubMedCrawler):
        self.crawler = crawler
    
    def crawl_proteins(self, protein_names: List[str], articles_per_protein: int = 3) -> Dict[str, List[Dict]]:
        """
        批量爬取多个蛋白的文献
        
        Args:
            protein_names: 蛋白名称列表
            articles_per_protein: 每个蛋白爬取的文献数
            
        Returns:
            {蛋白名: 文献列表}
        """
        results = {}
        
        for i, protein_name in enumerate(protein_names, 1):
            print(f"\n[{i}/{len(protein_names)}] 爬取 {protein_name} 相关文献...")
            
            articles = self.crawler.search_protein_interactions(
                protein_name,
                max_results=articles_per_protein
            )
            
            results[protein_name] = articles
            
            # 为每篇文献生成帖子内容
            posts = []
            for article in articles:
                post = self.crawler.generate_post_content(article, protein_name)
                posts.append(post)
                print(f"   ✅ {post['title'][:60]}...")
            
            results[protein_name] = posts
        
        return results
