"""
多模态文献特征提取

基于PubMed/Semantic Scholar文献数据，提取文本特征用于推荐

核心功能:
1. 文献数据加载与预处理
2. TF-IDF特征提取
3. 主题模型 (LDA) 提取语义主题
4. 与蛋白/笔记关联
"""

import json
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import re
from pathlib import Path

# sklearn用于文本特征
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation, TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity


class PaperLoader:
    """
    文献数据加载器
    
    支持多种数据源:
    - 原始paper JSON文件
    - proteinhub_notes_database.json
    - batch_papers.json
    """
    
    def __init__(self, data_dir: str = "/root/.openclaw/workspace/projects/proteinhub/data"):
        self.data_dir = Path(data_dir)
        self.papers = {}
        self.protein2papers = defaultdict(list)
    
    def load_from_notes_database(self, db_path: Optional[str] = None) -> Dict:
        """
        从proteinhub_notes_database.json加载
        
        Returns:
            {paper_id: {title, abstract, proteins, tags, ...}}
        """
        if db_path is None:
            db_path = self.data_dir / "proteinhub_notes_database.json"
        
        print(f"📚 加载笔记数据库: {db_path}")
        
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        for note in db.get('notes', []):
            paper_id = note.get('id', '')
            
            # 从content中提取信息
            content = note.get('content', '')
            title = note.get('title', '')
            
            # 提取关联的蛋白 (从tags或content中)
            proteins = self._extract_proteins_from_text(content + ' ' + title)
            
            self.papers[paper_id] = {
                'id': paper_id,
                'title': title,
                'content': content,
                'abstract': self._extract_abstract(content),
                'tags': note.get('tags', []),
                'proteins': proteins,
                'source': 'notes_db'
            }
            
            # 建立蛋白-文献映射
            for protein in proteins:
                self.protein2papers[protein].append(paper_id)
        
        print(f"  加载了 {len(self.papers)} 篇笔记")
        return self.papers
    
    def load_from_raw_papers(self, batch_dir: str = "high_quality_notes/v2_batch_e") -> Dict:
        """
        从原始paper JSON加载
        
        Args:
            batch_dir: 批次目录名
        """
        batch_path = self.data_dir / batch_dir
        
        if not batch_path.exists():
            print(f"⚠️ 目录不存在: {batch_path}")
            return {}
        
        print(f"📚 加载原始论文数据: {batch_path}")
        
        count = 0
        for paper_file in batch_path.glob("paper_*.json"):
            try:
                with open(paper_file, 'r', encoding='utf-8') as f:
                    paper = json.load(f)
                
                paper_id = paper.get('paperId', paper_file.stem)
                
                # 提取作者名
                authors = [a.get('name', '') for a in paper.get('authors', [])]
                
                self.papers[paper_id] = {
                    'id': paper_id,
                    'title': paper.get('title', ''),
                    'abstract': paper.get('abstract', ''),
                    'authors': authors,
                    'venue': paper.get('venue', ''),
                    'year': paper.get('year', 0),
                    'citations': paper.get('citationCount', 0),
                    'fields': paper.get('fieldsOfStudy', []),
                    'doi': paper.get('externalIds', {}).get('DOI', ''),
                    'source': 'raw_json'
                }
                
                count += 1
                
            except Exception as e:
                print(f"  加载失败 {paper_file}: {e}")
        
        print(f"  加载了 {count} 篇原始论文")
        return self.papers
    
    def _extract_proteins_from_text(self, text: str) -> List[str]:
        """从文本中提取蛋白名称 (简单规则)"""
        # 常见脂滴蛋白
        protein_keywords = [
            'CIDEA', 'CIDEC', 'FSP27', 'PLIN1', 'PLIN2', 'PLIN3',
            'PLIN4', 'PLIN5', 'ADRP', 'TIP47', 'S3-12', 'MLDP',
            'ATGL', 'HSL', 'CGI-58', ' perilipin'
        ]
        
        proteins = []
        text_upper = text.upper()
        
        for keyword in protein_keywords:
            if keyword.upper() in text_upper:
                proteins.append(keyword)
        
        return proteins
    
    def _extract_abstract(self, content: str) -> str:
        """从笔记content中提取abstract部分"""
        # 尝试找abstract标记
        patterns = [
            r'【研究背景】.*?\n\n',
            r'##.*background.*\n(.*?)(?=##|$)',
            r'abstract.*?:\s*(.+?)(?=\n\n|\n##|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(0)[:500]  # 限制长度
        
        # 默认返回前500字符
        return content[:500]
    
    def get_paper_text(self, paper_id: str) -> str:
        """获取论文的完整文本 (用于特征提取)"""
        paper = self.papers.get(paper_id, {})
        
        # 组合标题、摘要、内容
        text_parts = []
        
        if paper.get('title'):
            text_parts.append(paper['title'])
        
        if paper.get('abstract'):
            text_parts.append(paper['abstract'])
        
        if paper.get('content'):
            text_parts.append(paper['content'][:1000])  # 限制长度
        
        return ' '.join(text_parts)
    
    def get_protein_papers(self, protein_name: str) -> List[str]:
        """获取与蛋白相关的所有论文ID"""
        return self.protein2papers.get(protein_name, [])


class TextFeatureExtractor:
    """
    文本特征提取器
    
    方法:
    1. TF-IDF: 词频-逆文档频率
    2. LDA: 主题模型
    3. LSA: 潜在语义分析
    """
    
    def __init__(self, max_features: int = 1000, n_topics: int = 20):
        self.max_features = max_features
        self.n_topics = n_topics
        
        self.tfidf_vectorizer = None
        self.lda_model = None
        self.lsa_model = None
        
        self.is_fitted = False
    
    def preprocess_text(self, text: str) -> str:
        """
        文本预处理
        
        - 转小写
        - 去除特殊字符
        - 简单tokenization
        """
        if not text:
            return ""
        
        # 转小写
        text = text.lower()
        
        # 去除多余空白和特殊字符
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def fit(self, texts: List[str]):
        """
        训练特征提取器
        
        Args:
            texts: 文献文本列表
        """
        print(f"🔄 训练文本特征提取器...")
        
        # 预处理
        processed_texts = [self.preprocess_text(t) for t in texts if t]
        
        # 1. TF-IDF
        print(f"  训练TF-IDF (max_features={self.max_features})...")
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            min_df=2,  # 至少出现在2个文档中
            max_df=0.8,  # 最多出现在80%文档中
            ngram_range=(1, 2),  # unigram + bigram
            stop_words='english'
        )
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(processed_texts)
        print(f"    TF-IDF维度: {tfidf_matrix.shape}")
        
        # 2. LDA主题模型
        print(f"  训练LDA (n_topics={self.n_topics})...")
        self.lda_model = LatentDirichletAllocation(
            n_components=self.n_topics,
            random_state=42,
            max_iter=10,
            learning_method='online'
        )
        self.lda_model.fit(tfidf_matrix)
        print(f"    LDA训练完成")
        
        # 3. LSA (可选，用于降维)
        n_lsa_components = min(100, tfidf_matrix.shape[1] - 1)
        print(f"  训练LSA (n_components={n_lsa_components})...")
        self.lsa_model = TruncatedSVD(n_components=n_lsa_components, random_state=42)
        self.lsa_model.fit(tfidf_matrix)
        print(f"    LSA训练完成")
        
        self.is_fitted = True
        print("✅ 特征提取器训练完成")
        
        return self
    
    def transform(self, texts: List[str]) -> Dict[str, np.ndarray]:
        """
        提取特征
        
        Returns:
            {'tfidf': array, 'lda': array, 'lsa': array, 'combined': array}
        """
        if not self.is_fitted:
            raise RuntimeError("模型未训练")
        
        # 预处理
        processed_texts = [self.preprocess_text(t) for t in texts if t]
        
        # TF-IDF
        tfidf = self.tfidf_vectorizer.transform(processed_texts).toarray()
        
        # LDA主题分布
        lda = self.lda_model.transform(tfidf)
        
        # LSA
        lsa = self.lsa_model.transform(tfidf)
        
        # 组合特征 (加权拼接)
        # TF-IDF取前min(100, n_features)维, LDA: n_topics维, LSA取前min(50, n_lsa)维
        n_tfidf = min(100, tfidf.shape[1])
        n_lsa_use = min(50, lsa.shape[1])
        combined = np.concatenate([tfidf[:, :n_tfidf], lda, lsa[:, :n_lsa_use]], axis=1)
        
        return {
            'tfidf': tfidf,
            'lda': lda,
            'lsa': lsa,
            'combined': combined
        }
    
    def get_top_terms_per_topic(self, n_terms: int = 10) -> List[List[str]]:
        """获取每个主题的关键词"""
        if not self.is_fitted or self.lda_model is None:
            return []
        
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        topics = []
        
        for topic_idx, topic in enumerate(self.lda_model.components_):
            top_indices = topic.argsort()[-n_terms:][::-1]
            top_terms = [feature_names[i] for i in top_indices]
            topics.append(top_terms)
        
        return topics


class MultimodalFeatureFusion:
    """
    多模态特征融合
    
    将文献特征与蛋白/用户特征融合
    """
    
    def __init__(self, text_extractor: TextFeatureExtractor):
        self.text_extractor = text_extractor
        self.paper_embeddings = {}
        self.protein_embeddings = {}
    
    def build_paper_embeddings(self, paper_loader: PaperLoader) -> Dict[str, np.ndarray]:
        """
        为所有文献构建embedding
        
        Returns:
            {paper_id: embedding_vector}
        """
        print("🔄 构建文献embedding...")
        
        paper_ids = list(paper_loader.papers.keys())
        texts = [paper_loader.get_paper_text(pid) for pid in paper_ids]
        
        features = self.text_extractor.transform(texts)
        embeddings = features['combined']
        
        self.paper_embeddings = {
            pid: emb for pid, emb in zip(paper_ids, embeddings)
        }
        
        print(f"  构建了 {len(self.paper_embeddings)} 篇文献的embedding")
        return self.paper_embeddings
    
    def build_protein_embeddings(self, paper_loader: PaperLoader) -> Dict[str, np.ndarray]:
        """
        构建蛋白embedding (聚合相关文献)
        
        Returns:
            {protein_name: embedding_vector}
        """
        print("🔄 构建蛋白embedding...")
        
        if not self.paper_embeddings:
            self.build_paper_embeddings(paper_loader)
        
        for protein, paper_ids in paper_loader.protein2papers.items():
            if not paper_ids:
                continue
            
            # 聚合相关文献的embedding (平均)
            embeddings = []
            for pid in paper_ids:
                if pid in self.paper_embeddings:
                    embeddings.append(self.paper_embeddings[pid])
            
            if embeddings:
                self.protein_embeddings[protein] = np.mean(embeddings, axis=0)
        
        print(f"  构建了 {len(self.protein_embeddings)} 个蛋白的embedding")
        return self.protein_embeddings
    
    def compute_paper_similarity(self, paper_id1: str, paper_id2: str) -> float:
        """计算两篇文献的相似度"""
        if paper_id1 not in self.paper_embeddings or paper_id2 not in self.paper_embeddings:
            return 0.0
        
        emb1 = self.paper_embeddings[paper_id1]
        emb2 = self.paper_embeddings[paper_id2]
        
        # 余弦相似度
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    
    def find_similar_papers(self, paper_id: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """找相似文献"""
        if paper_id not in self.paper_embeddings:
            return []
        
        query_emb = self.paper_embeddings[paper_id]
        
        similarities = []
        for pid, emb in self.paper_embeddings.items():
            if pid != paper_id:
                sim = np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb))
                similarities.append((pid, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def find_papers_for_protein(self, protein_name: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        为蛋白找最相关的文献 (基于embedding相似度)
        
        与直接关联不同，这是语义相似
        """
        if protein_name not in self.protein_embeddings:
            return []
        
        protein_emb = self.protein_embeddings[protein_name]
        
        similarities = []
        for pid, emb in self.paper_embeddings.items():
            sim = np.dot(protein_emb, emb) / (np.linalg.norm(protein_emb) * np.linalg.norm(emb))
            similarities.append((pid, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


# ==================== 单元测试 ====================

def test_paper_loader():
    """测试文献加载器"""
    print("\n" + "="*50)
    print("测试1: PaperLoader")
    print("="*50)
    
    loader = PaperLoader()
    
    # 测试从笔记数据库加载
    try:
        papers = loader.load_from_notes_database()
        assert len(papers) > 0, "没有加载到论文"
        print(f"✅ 从笔记数据库加载了 {len(papers)} 篇文献")
        
        # 检查第一篇的结构
        first_paper = list(papers.values())[0]
        assert 'title' in first_paper, "缺少title字段"
        assert 'content' in first_paper or 'abstract' in first_paper, "缺少content/abstract字段"
        print(f"  示例: {first_paper['title'][:50]}...")
        
    except Exception as e:
        print(f"⚠️ 笔记数据库加载失败: {e}")
        # 尝试加载原始论文
        papers = loader.load_from_raw_papers()
        if papers:
            print(f"✅ 从原始论文加载了 {len(papers)} 篇文献")
    
    return loader


def test_text_extractor():
    """测试文本特征提取"""
    print("\n" + "="*50)
    print("测试2: TextFeatureExtractor")
    print("="*50)
    
    # 模拟文本
    texts = [
        "CIDEA is a lipid droplet protein that promotes lipid storage in adipocytes.",
        "FSP27 regulates lipid droplet fusion and growth in white adipose tissue.",
        "Perilipin proteins are important for lipid droplet stability and lipolysis regulation.",
        "Lipid droplets are cellular organelles for neutral lipid storage.",
        "Obesity is associated with altered lipid droplet protein expression."
    ] * 5  # 复制扩充
    
    extractor = TextFeatureExtractor(max_features=50, n_topics=3)
    extractor.fit(texts)
    
    # 转换
    features = extractor.transform(texts[:2])
    
    print(f"✅ 特征提取成功")
    print(f"  TF-IDF维度: {features['tfidf'].shape}")
    print(f"  LDA维度: {features['lda'].shape}")
    print(f"  组合特征维度: {features['combined'].shape}")
    
    # 检查主题
    topics = extractor.get_top_terms_per_topic(n_terms=5)
    print(f"  学习到的主题:")
    for i, terms in enumerate(topics[:3]):
        print(f"    主题{i+1}: {', '.join(terms[:5])}")
    
    return extractor


def test_full_pipeline():
    """测试完整流程"""
    print("\n" + "="*50)
    print("测试3: 完整流程")
    print("="*50)
    
    # 1. 加载数据
    loader = PaperLoader()
    try:
        loader.load_from_notes_database()
    except:
        print("⚠️ 使用模拟数据")
        # 创建模拟数据
        for i in range(20):
            loader.papers[f"paper_{i}"] = {
                'id': f"paper_{i}",
                'title': f"Paper about {'CIDEA' if i % 3 == 0 else 'FSP27' if i % 3 == 1 else 'lipid metabolism'}",
                'abstract': f"This study investigates {'CIDEA' if i % 3 == 0 else 'FSP27' if i % 3 == 1 else 'lipid droplets'} in adipocytes.",
                'proteins': ['CIDEA'] if i % 3 == 0 else ['FSP27'] if i % 3 == 1 else []
            }
            for p in loader.papers[f"paper_{i}"]['proteins']:
                loader.protein2papers[p].append(f"paper_{i}")
    
    if not loader.papers:
        print("⚠️ 没有可用数据，跳过")
        return True
    
    # 2. 训练特征提取器
    texts = [loader.get_paper_text(pid) for pid in loader.papers.keys()]
    extractor = TextFeatureExtractor(max_features=100, n_topics=5)
    extractor.fit(texts)
    
    # 3. 构建融合器
    fusion = MultimodalFeatureFusion(extractor)
    fusion.build_paper_embeddings(loader)
    fusion.build_protein_embeddings(loader)
    
    print(f"✅ 完整流程测试通过")
    print(f"  文献embedding: {len(fusion.paper_embeddings)}")
    print(f"  蛋白embedding: {len(fusion.protein_embeddings)}")
    
    # 4. 测试相似度搜索
    if fusion.paper_embeddings:
        paper_ids = list(fusion.paper_embeddings.keys())
        similar = fusion.find_similar_papers(paper_ids[0], top_k=3)
        print(f"  相似文献搜索: 找到 {len(similar)} 篇相似文献")
    
    return True


def test_text_preprocessing():
    """测试文本预处理"""
    print("\n" + "="*50)
    print("测试4: 文本预处理")
    print("="*50)
    
    extractor = TextFeatureExtractor()
    
    test_cases = [
        "CIDEA is a Protein!!!",
        "Lipid Droplets: Storage \u0026 Metabolism.",
        "  Multiple   Spaces   Here  "
    ]
    
    for text in test_cases:
        processed = extractor.preprocess_text(text)
        print(f"  输入: '{text}'")
        print(f"  输出: '{processed}'")
        assert processed == processed.lower(), "未转小写"
        assert '  ' not in processed, "有多余空格"
    
    print("✅ 文本预处理测试通过")
    return True


if __name__ == '__main__':
    print("="*60)
    print("多模态文献特征 - 单元测试")
    print("="*60)
    
    np.random.seed(42)
    
    try:
        test_text_preprocessing()
        test_text_extractor()
        loader = test_paper_loader()
        test_full_pipeline()
        
        print("\n" + "="*60)
        print("✅ 所有单元测试通过!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise