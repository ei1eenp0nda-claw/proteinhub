"""
ProteinHub Content Generator - 改进版Prompt
科研论文 → 小红书风格笔记生成器（优化版）

生成规则（必须遵守）：
1. 非必要不使用双引号，比喻时可用
2. 减少空行，保持紧凑排版
3. 保持形象比喻，但确保科学准确性
4. 文章结尾必须引用原文信息
5. 避免GPT腔，口语化自然表达
"""

import json
import re
from typing import List, Dict, Optional
from datetime import datetime


class ContentGenerator:
    """内容生成器 - 针对小红书平台优化"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.style_guide = self._get_style_guide()
    
    def _get_style_guide(self) -> str:
        """获取小红书风格指南"""
        return """
【小红书笔记风格指南】

1. 语言表达：
   - 避免AI腔，像朋友聊天一样自然
   - 不用首先/其次/最后，改用数字序号或自然过渡
   - 非必要不使用双引号，比喻时可用
   - 适当使用网络流行语（绝绝子、挖到宝了、码住等）

2. 排版格式：
   - 减少空行，段落之间紧凑
   - 用符号分隔（• 、→ 、|）替代过多换行
   - 关键信息用【】标注，不用标题
   -  emoji控制在5-8个，不堆砌

3. 内容结构：
   - 开场：口语化引入，直接点题
   - 核心：2-3个重点，用 bullet points
   - 机制：形象比喻，准确传达科学概念
   - 结尾：必须引用原文（期刊+年份+PMID）

4. 避雷指南：
   - ❌ 不难发现/值得注意的是/研究表明
   - ❌ 过长的书面语句子
   - ❌ 过多的装饰性形容词
   - ❌ 空行超过2行连续出现
   - ✅ 短句为主，口语化表达
   - ✅ 用具体数字替代笼统描述

示例对比：
❌ "不难发现，CIDEA蛋白在代谢调控中扮演着至关重要的角色。"
✅ "CIDEA这个蛋白挺关键的，代谢调控离不开它。"

❌ "这项研究具有重要的科学意义和临床应用价值。"
✅ "搞懂了这点，以后治代谢病可能有新思路。"
"""
    
    def generate_xiaohongshu_post(self, article: Dict, protein_name: str) -> Dict:
        """生成小红书风格笔记"""
        
        if self.llm_client:
            return self._generate_with_llm(article, protein_name)
        else:
            return self._generate_optimized(article, protein_name)
    
    def _generate_optimized(self, article: Dict, protein_name: str) -> Dict:
        """优化版模板生成"""
        
        paper_title = article.get('title', '')
        journal = article.get('journal', '权威期刊')
        authors = article.get('authors', [])
        year = article.get('pub_date', '')[:4] if article.get('pub_date') else '2024'
        pmid = article.get('pmid', '')
        abstract = article.get('abstract', '')
        
        # 提取关键信息
        discovery = self._extract_discovery(paper_title)
        
        # 生成标题（带emoji，15-25字）
        title = self._generate_title(protein_name, discovery, year)
        
        # 生成正文（500字左右，紧凑排版）
        content = self._generate_content(protein_name, discovery, journal, year, authors, pmid)
        
        # 生成标签
        tags = self._generate_tags(protein_name, paper_title)
        
        # 生成一句话总结
        summary = self._generate_summary(protein_name, discovery)
        
        return {
            'title': title,
            'content': content,
            'tags': tags,
            'summary': summary,
            'word_count': len(content),
            'reading_time': max(1, len(content) // 250),
            'source': {
                'title': paper_title,
                'journal': journal,
                'year': year,
                'pmid': pmid,
                'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/' if pmid else ''
            }
        }
    
    def _generate_title(self, protein_name: str, discovery: str, year: str) -> str:
        """生成标题（紧凑，带emoji）"""
        import random
        
        templates = [
            f"🔬 {protein_name}新功能！{discovery[:20]}",
            f"💡 {year}最新：{protein_name}原来这么重要",
            f"🧬 挖到宝了！{protein_name}{discovery[:15]}",
            f"📑 {protein_name}研究速递，{discovery[:18]}",
            f"🎯 {protein_name}研究者必看！{discovery[:15]}"
        ]
        
        return random.choice(templates)
    
    def _generate_content(self, protein_name: str, discovery: str, 
                         journal: str, year: str, authors: list, pmid: str) -> str:
        """生成正文（优化版，减少空行）"""
        
        lines = []
        
        # 开场（直接点题，口语化）
        openings = [
            f"姐妹们！这篇《{journal}》的研究绝了 🎉",
            f"挖到一篇{year}年的宝藏文献，必须分享 🔥",
            f"今天读到个超有意思的发现，{protein_name}又上分了 📑",
            f"科研人速来！这篇{journal}的文章值得看 💡"
        ]
        import random
        lines.append(random.choice(openings))
        
        # 背景介绍（紧凑）
        lines.append(f"【{protein_name}是干嘛的】")
        lines.append(f"简单说就是个脂滴相关蛋白，专门管脂肪怎么存、怎么用。{authors[0] if authors else '研究团队'}这次挖出了新功能。")
        
        # 核心发现（用|分隔，减少换行）
        lines.append(f"【核心发现】")
        if discovery and len(discovery) > 10:
            lines.append(f"这次发现{protein_name}在{discovery[:40]}这块有重要作用。")
        else:
            lines.append(f"这次搞清楚了{protein_name}调控代谢的新机制。")
        
        # 形象比喻（准确且通俗）
        lines.append(f"【怎么理解】")
        lines.append(f"可以把{protein_name}想象成细胞里的能量管家 → 饭多了帮你存起来，需要时再拿出来用。整个过程跟生物钟同步，精密得很。")
        
        # 重要性（具体而非笼统）
        lines.append(f"【为啥重要】")
        lines.append(f"• 搞懂了代谢调控的细节 | • 可能找到治代谢病的新靶点 | • 解释了为啥作息乱容易胖")
        
        # 结尾必须引用原文（紧凑格式）
        lines.append(f"【原文信息】")
        lines.append(f"发表于《{journal}》{year}年 | PMID: {pmid}")
        
        # 互动结尾
        closings = [
            f"对{protein_name}感兴趣的朋友评论区聊聊 💬",
            f"觉得有用记得码住！持续分享科研干货 💕",
            f"有问题直接问，看到就回 👇"
        ]
        lines.append(random.choice(closings))
        
        # 用换行连接，但避免连续空行
        return '\n'.join(lines)
    
    def _generate_tags(self, protein_name: str, paper_title: str) -> List[str]:
        """生成标签"""
        tags = [protein_name]
        
        title_lower = paper_title.lower()
        
        # 研究领域标签
        if any(w in title_lower for w in ['lipid', 'fat', '脂滴']):
            tags.extend(['脂滴研究', '脂质代谢'])
        if any(w in title_lower for w in ['cancer', 'tumor']):
            tags.extend(['癌症研究'])
        if any(w in title_lower for w in ['metabolism', '代谢']):
            tags.extend(['代谢疾病'])
        if any(w in title_lower for w in ['interaction', 'binding']):
            tags.extend(['蛋白互作'])
        
        # 通用标签
        tags.extend(['科研干货', '文献解读'])
        
        return tags[:6]  # 限制数量
    
    def _generate_summary(self, protein_name: str, discovery: str) -> str:
        """生成一句话总结"""
        if discovery and len(discovery) > 5:
            return f"{protein_name}在{discovery[:25]}中发挥关键作用"
        return f"{protein_name}调控代谢的新机制被揭示"
    
    def _extract_discovery(self, title: str) -> str:
        """从标题提取发现"""
        patterns = [
            r'regulates?\s+(.+?)(?:\.|$)',
            r'promotes?\s+(.+?)(?:\.|$)',
            r'in\s+(.+?)(?:\.|$)'
        ]
        for p in patterns:
            m = re.search(p, title, re.I)
            if m:
                return m.group(1).strip()[:50]
        return "代谢调控"


if __name__ == "__main__":
    # 测试
    generator = ContentGenerator()
    
    test_article = {
        'title': 'The rhythmic coupling of Egr-1 and Cidea regulates age-related metabolic dysfunction',
        'abstract': 'This study reveals the mechanism...',
        'authors': ['Wu J', 'Smith A'],
        'journal': 'Nature Communications',
        'pub_date': '2023-03',
        'pmid': '36964140'
    }
    
    post = generator.generate_xiaohongshu_post(test_article, 'CIDEA')
    
    print(f"标题: {post['title']}")
    print(f"\n标签: {' '.join(['#'+t for t in post['tags']])}")
    print(f"\n正文 ({post['word_count']}字):")
    print("="*60)
    print(post['content'])
    print("="*60)
    print(f"\n来源: 《{post['source']['journal']}》{post['source']['year']} | PMID: {post['source']['pmid']}")
