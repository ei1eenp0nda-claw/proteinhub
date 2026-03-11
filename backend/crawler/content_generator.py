"""
ProteinHub Content Generator
科研论文 → 小红书风格笔记生成器

使用 LLM 接口：
- 概括改写论文摘要
- 生成小红书风格标题和内容
- 自动打标签
"""

import json
import re
from typing import List, Dict, Optional
from datetime import datetime


class ContentGenerator:
    """
    内容生成器 - 将科研论文转化为小红书风格笔记
    
    输入: PubMed 文献信息 (标题、摘要、作者、期刊)
    输出: 小红书风格笔记 (标题、正文、标签、emoji)
    """
    
    # 小红书风格模板
    TEMPLATES = {
        'title_patterns': [
            "🔬 {protein}研究新发现！{discovery}",
            "🧬 必读！{protein}与{topic}的秘密",
            "📑 Nature子刊揭秘：{protein}{discovery}",
            "💡 {year}最新研究：{protein}原来这么重要",
            "🎯 {protein}研究者必看！{discovery}",
            "🔥 热点追踪：{protein}{discovery}",
            "📊 数据说话：{protein}{discovery}",
            "🧪 实验揭秘：{protein}{discovery}"
        ],
        'opening_lines': [
            "姐妹们，今天分享一个超重要的研究发现！",
            "科研人必看！这个发现太有意思了",
            "挖到一篇宝藏文献，赶紧来分享",
            "最新研究速递，建议收藏",
            "这个蛋白的研究有新进展了！",
            "今天读到一篇很有意思的paper"
        ],
        'closing_lines': [
            "觉得有用的话记得点赞收藏哦～",
            "对这个研究感兴趣的朋友可以讨论",
            "持续分享蛋白研究新进展，欢迎关注",
            "科研路上一起加油！",
            "有问题欢迎留言讨论"
        ]
    }
    
    def __init__(self, llm_client=None):
        """
        初始化内容生成器
        
        Args:
            llm_client: LLM 客户端 (如果为 None 则使用模拟生成)
        """
        self.llm_client = llm_client
    
    def generate_xiaohongshu_post(self, article: Dict, protein_name: str) -> Dict:
        """
        生成小红书风格笔记
        
        Args:
            article: {
                'title': 论文标题,
                'abstract': 论文摘要,
                'authors': 作者列表,
                'journal': 期刊名,
                'pub_date': 发表日期,
                'pmid': PubMed ID,
                'url': 原文链接
            }
            protein_name: 蛋白名称
            
        Returns:
            {
                'title': 小红书标题,
                'content': 正文内容,
                'tags': 标签列表,
                'summary': 一句话总结,
                'key_points': 关键点列表,
                'emoji_count': emoji数量统计,
                'reading_time': 预计阅读时间,
                'source': 原文信息
            }
        """
        # 使用 LLM 或模板生成
        if self.llm_client:
            return self._generate_with_llm(article, protein_name)
        else:
            return self._generate_with_template(article, protein_name)
    
    def _generate_with_llm(self, article: Dict, protein_name: str) -> Dict:
        """使用 LLM 生成内容"""
        
        # 构建 prompt
        prompt = self._build_prompt(article, protein_name)
        
        # 调用 LLM (这里模拟，实际使用时接入真实 API)
        response = self._call_llm(prompt)
        
        # 解析 LLM 输出
        return self._parse_llm_response(response, article, protein_name)
    
    def _build_prompt(self, article: Dict, protein_name: str) -> str:
        """构建 LLM prompt"""
        
        paper_title = article.get('title', '')
        abstract = article.get('abstract', '')
        journal = article.get('journal', '')
        year = article.get('pub_date', '')[:4] if article.get('pub_date') else '2024'
        
        prompt = f"""请将以下科研论文改写为小红书风格的科普笔记。

【论文信息】
- 标题: {paper_title}
- 期刊: {journal}
- 年份: {year}
- 蛋白名称: {protein_name}
- 摘要: {abstract[:500] if abstract else '暂无摘要'}

【输出要求】
请以 JSON 格式输出：
{{
    "title": "小红书风格标题（15-25字，带emoji，吸引眼球）",
    "content": "正文（200-400字，口语化，分段清晰，带emoji，适合非专业读者理解）",
    "tags": ["标签1", "标签2", "标签3", "标签4", "标签5"],
    "summary": "一句话核心发现（30字以内）",
    "key_points": ["关键点1", "关键点2", "关键点3"],
    "why_it_matters": "为什么这个研究重要（50字以内）"
}}

【风格要求】
1. 标题党风格，要有吸引力
2. 正文口语化，避免过多专业术语
3. 适当使用emoji增加可读性
4. 每段不要太长，适合手机阅读
5. 最后要有互动引导（提问或邀请评论）
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        调用 LLM
        
        这里使用模拟输出，实际使用时替换为真实 API 调用
        """
        # TODO: 接入真实 LLM API
        # return self.llm_client.complete(prompt)
        
        # 模拟 LLM 响应 (实际使用时删除)
        return self._simulate_llm_response(prompt)
    
    def _simulate_llm_response(self, prompt: str) -> str:
        """模拟 LLM 响应（用于测试）"""
        # 从 prompt 中提取信息
        protein_match = re.search(r'蛋白名称: (\w+)', prompt)
        protein = protein_match.group(1) if protein_match else 'Protein'
        
        journal_match = re.search(r'期刊: ([^\n]+)', prompt)
        journal = journal_match.group(1) if journal_match else 'Nature'
        
        year_match = re.search(r'年份: (\d{4})', prompt)
        year = year_match.group(1) if year_match else '2024'
        
        response = f"""{{
    "title": "🔬 {protein}研究新突破！科学家发现新机制",
    "content": "姐妹们，今天读到一篇超有意思的研究！📑\\n\\n{protein}一直是脂滴研究的热点蛋白。这篇发表在《{journal}》的最新研究发现，{protein}在脂质代谢调控中扮演了关键角色！🧬\\n\\n研究团队通过一系列精妙实验，揭示了{protein}调控脂滴形成的新机制。简单来说，这个蛋白就像一个"分子开关"，控制着脂肪细胞的能量存储和释放。💡\\n\\n这个发现不仅对理解肥胖和代谢疾病有重要意义，还可能为未来的治疗提供新靶点！🔍\\n\\n大家对这个研究有什么看法？欢迎在评论区讨论～",
    "tags": ["{protein}", "脂滴研究", "代谢疾病", "科研干货", "文献解读"],
    "summary": "{protein}调控脂滴形成的新机制被发现",
    "key_points": [
        "{protein}是脂滴形成的关键调控因子",
        "发现新的分子调控机制",
        "对代谢疾病研究有重要意义"
    ],
    "why_it_matters": "为肥胖和代谢疾病治疗提供潜在新靶点"
}}"""
        return response
    
    def _parse_llm_response(self, response: str, article: Dict, protein_name: str) -> Dict:
        """解析 LLM 输出"""
        try:
            # 提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {}
        except json.JSONDecodeError:
            data = {}
        
        # 补充计算字段
        content = data.get('content', '')
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', content))
        
        return {
            'title': data.get('title', self._generate_title_template(article, protein_name)),
            'content': content or self._generate_content_template(article, protein_name),
            'tags': data.get('tags', self._generate_tags(article, protein_name)),
            'summary': data.get('summary', ''),
            'key_points': data.get('key_points', []),
            'why_it_matters': data.get('why_it_matters', ''),
            'emoji_count': emoji_count,
            'reading_time': max(1, len(content) // 200) if content else 1,
            'source': {
                'title': article.get('title', ''),
                'journal': article.get('journal', ''),
                'pub_date': article.get('pub_date', ''),
                'pmid': article.get('pmid', ''),
                'url': article.get('url', '')
            }
        }
    
    def _generate_with_template(self, article: Dict, protein_name: str) -> Dict:
        """使用模板生成内容（LLM不可用时）"""
        return {
            'title': self._generate_title_template(article, protein_name),
            'content': self._generate_content_template(article, protein_name),
            'tags': self._generate_tags(article, protein_name),
            'summary': self._generate_summary(article, protein_name),
            'key_points': self._extract_key_points(article),
            'why_it_matters': '该研究对理解蛋白功能机制有重要意义',
            'emoji_count': 8,
            'reading_time': 2,
            'source': {
                'title': article.get('title', ''),
                'journal': article.get('journal', ''),
                'pub_date': article.get('pub_date', ''),
                'pmid': article.get('pmid', ''),
                'url': article.get('url', '')
            }
        }
    
    def _generate_title_template(self, article: Dict, protein_name: str) -> str:
        """生成小红书风格标题"""
        import random
        
        paper_title = article.get('title', '')
        year = article.get('pub_date', '')[:4] if article.get('pub_date') else '2024'
        
        # 提取发现关键词
        discovery = self._extract_discovery(paper_title)
        topic = self._extract_topic(paper_title)
        
        # 随机选择模板
        template = random.choice(self.TEMPLATES['title_patterns'])
        
        return template.format(
            protein=protein_name,
            discovery=discovery[:30],
            topic=topic[:20],
            year=year
        )
    
    def _generate_content_template(self, article: Dict, protein_name: str) -> str:
        """生成小红书风格正文"""
        import random
        
        paper_title = article.get('title', '')
        journal = article.get('journal', '权威期刊')
        authors = article.get('authors', [])
        year = article.get('pub_date', '')[:4] if article.get('pub_date') else '2024'
        
        opening = random.choice(self.TEMPLATES['opening_lines'])
        closing = random.choice(self.TEMPLATES['closing_lines'])
        
        # 提取关键信息
        discovery = self._extract_discovery(paper_title)
        mechanism = self._extract_mechanism(paper_title)
        
        content = f"""{opening} 🎉

📑 今天分享的是发表在《{journal}》的一篇研究，研究团队来自{authors[0] if authors else '国际知名实验室'}。

🔬 研究背景
{protein_name}一直是蛋白研究领域的明星分子。这篇{year}年的最新研究，揭示了它在{discovery[:40]}方面的新机制！

💡 核心发现
研究团队发现，{protein_name}{mechanism[:60]}。简单来说，这个蛋白就像一个精密的"分子开关"，调控着细胞的正常功能。

🎯 为什么重要？
这个发现不仅帮助我们更好地理解{protein_name}的功能，还可能为相关疾病的治疗提供新思路！

{closing} 💕"""
        
        return content
    
    def _generate_tags(self, article: Dict, protein_name: str) -> List[str]:
        """生成小红书标签"""
        tags = [protein_name]
        
        # 根据标题提取主题标签
        paper_title = article.get('title', '').lower()
        
        # 研究领域标签
        if any(word in paper_title for word in ['lipid', 'fat', 'adipose', '脂滴']):
            tags.extend(['脂滴研究', '脂质代谢'])
        if any(word in paper_title for word in ['cancer', 'tumor', '癌']):
            tags.extend(['癌症研究', '肿瘤学'])
        if any(word in paper_title for word in ['interaction', 'binding', 'complex', '互作']):
            tags.extend(['蛋白互作', '分子机制'])
        if any(word in paper_title for word in ['metabolism', 'metabolic', '代谢']):
            tags.extend(['代谢研究', '代谢疾病'])
        
        # 方法学标签
        if any(word in paper_title for word in ['crystal', 'structure', '结构']):
            tags.append('结构生物学')
        if any(word in paper_title for word in ['single cell', 'scRNA', '单细胞']):
            tags.append('单细胞测序')
        
        # 通用标签
        tags.extend(['科研干货', '文献解读', '生物医学', '学术分享'])
        
        # 去重并限制数量
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen and len(unique_tags) < 8:
                seen.add(tag)
                unique_tags.append(tag)
        
        return unique_tags
    
    def _generate_summary(self, article: Dict, protein_name: str) -> str:
        """生成一句话总结"""
        paper_title = article.get('title', '')
        discovery = self._extract_discovery(paper_title)
        return f"{protein_name}{discovery[:30]}" if discovery else f"{protein_name}最新研究进展"
    
    def _extract_key_points(self, article: Dict) -> List[str]:
        """提取关键点"""
        paper_title = article.get('title', '')
        points = []
        
        # 根据标题提取关键发现
        if 'mechanism' in paper_title.lower() or '机制' in paper_title:
            points.append('揭示了新的分子机制')
        if 'function' in paper_title.lower() or '功能' in paper_title:
            points.append('发现了新的生物学功能')
        if 'interaction' in paper_title.lower() or '互作' in paper_title:
            points.append('鉴定了新的蛋白互作伙伴')
        if 'structure' in paper_title.lower() or '结构' in paper_title:
            points.append('解析了高分辨率结构')
        
        if not points:
            points = ['提供了新的研究视角', '推进了该领域的认知', '具有重要的临床意义']
        
        return points[:3]
    
    def _extract_discovery(self, title: str) -> str:
        """从标题中提取发现"""
        patterns = [
            r'(?:reveals?|shows?|demonstrates?)\s+(.+?)(?:\. |$)',
            r'(?:novel\s+)?(?:role|function|mechanism)\s+of\s+(.+?)(?:\. |$)',
            r'(?:regulates?|mediates?|controls?)\s+(.+?)(?:\. |$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "的新功能"
    
    def _extract_topic(self, title: str) -> str:
        """提取研究主题"""
        if 'lipid' in title.lower():
            return "脂质代谢"
        if 'cancer' in title.lower() or 'tumor' in title.lower():
            return "癌症"
        if 'metabolism' in title.lower():
            return "代谢"
        return "细胞功能"
    
    def _extract_mechanism(self, title: str) -> str:
        """提取机制描述"""
        patterns = [
            r'(?:through|via|by)\s+(.+?)(?:\. |$)',
            r'(?:involves?|mediates?)\s+(.+?)(?:\. |$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "调控细胞功能"


class ContentPipeline:
    """
    内容生成流水线
    
    整合 PubMed 爬虫 + LLM 内容生成
    """
    
    def __init__(self, crawler, content_generator):
        self.crawler = crawler
        self.generator = content_generator
    
    def generate_post_for_protein(self, protein_name: str) -> Optional[Dict]:
        """
        为蛋白生成小红书笔记
        
        Args:
            protein_name: 蛋白名称
            
        Returns:
            生成的笔记内容
        """
        print(f"🔍 搜索 {protein_name} 相关文献...")
        
        # 1. 搜索文献
        articles = self.crawler.search_protein_interactions(
            protein_name,
            max_results=1
        )
        
        if not articles:
            print(f"⚠️ 未找到 {protein_name} 相关文献")
            return None
        
        # 2. 获取第一篇文献的完整摘要
        article = articles[0]
        print(f"   📑 {article['title'][:60]}...")
        
        abstract = self.crawler.fetch_abstract(article['pmid'])
        if abstract:
            article['abstract'] = abstract
            print(f"   ✅ 获取摘要 ({len(abstract)} 字符)")
        
        # 3. 生成小红书风格内容
        print(f"   ✨ 生成小红书风格笔记...")
        post = self.generator.generate_xiaohongshu_post(article, protein_name)
        
        return post
    
    def batch_generate(self, protein_names: List[str]) -> List[Dict]:
        """批量生成笔记"""
        posts = []
        
        for i, protein_name in enumerate(protein_names, 1):
            print(f"\n[{i}/{len(protein_names)}] 处理 {protein_name}...")
            post = self.generate_post_for_protein(protein_name)
            if post:
                posts.append(post)
        
        return posts


# ============ 测试代码 ============

if __name__ == "__main__":
    print("🧪 测试内容生成器")
    print("=" * 50)
    
    # 测试数据
    test_article = {
        'title': 'CIDEA regulates lipid droplet fusion and energy storage in adipocytes',
        'abstract': 'Lipid droplets (LDs) are cellular organelles that store neutral lipids. CIDEA is a lipid droplet-associated protein that promotes lipid storage. Here we show that CIDEA regulates LD fusion through direct interaction with FSP27.',
        'authors': ['Zhang L', 'Wang H', 'Chen Y'],
        'journal': 'Nature Cell Biology',
        'pub_date': '2024-03',
        'pmid': '12345678',
        'url': 'https://pubmed.ncbi.nlm.nih.gov/12345678/'
    }
    
    # 创建生成器
    generator = ContentGenerator()
    
    # 生成笔记
    post = generator.generate_xiaohongshu_post(test_article, 'CIDEA')
    
    print("\n📱 生成的笔记：")
    print("-" * 50)
    print(f"标题: {post['title']}")
    print(f"\n正文:\n{post['content']}")
    print(f"\n标签: {' '.join(['#' + tag for tag in post['tags']])}")
    print(f"\n总结: {post['summary']}")
    print(f"\n关键点:")
    for point in post['key_points']:
        print(f"  • {point}")
    print(f"\n阅读时间: {post['reading_time']} 分钟")
    print(f"Emoji 数量: {post['emoji_count']}")
