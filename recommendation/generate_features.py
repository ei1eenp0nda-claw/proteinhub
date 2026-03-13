"""
ProteinHub Recommendation System - Content Feature Generator
生成内容特征数据（TF-IDF、主题标签、引用热度、质量评分）
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import json
import random

np.random.seed(42)
random.seed(42)

# 模拟学术关键词池
ACADEMIC_KEYWORDS = {
    '蛋白质结构预测': ['AlphaFold', '结构预测', '深度学习', '神经网络', '蛋白质折叠'],
    '蛋白质折叠': ['折叠机制', '热力学', '动力学', '中间体', '错误折叠'],
    'AlphaFold': ['AlphaFold2', 'AlphaFold3', '结构预测', '神经网络', '端到端'],
    '分子动力学': ['MD模拟', 'GROMACS', 'AMBER', '力场', '模拟时间'],
    '机器学习': ['深度学习', '神经网络', '特征工程', '模型训练', '预测精度'],
    '深度学习': ['神经网络', 'CNN', 'Transformer', '注意力机制', '表征学习'],
    '图神经网络': ['GNN', '图卷积', '分子图', '消息传递', '图注意力'],
    '扩散模型': ['扩散过程', '去噪', '生成模型', '采样', '分数匹配'],
    '分子对接': ['对接打分', '结合位点', '虚拟筛选', '配体设计', '亲和力'],
    '药物设计': ['先导化合物', 'ADMET', '成药性', '靶点', '优化'],
    '酶催化': ['催化机制', '活性位点', '底物结合', '催化效率', '酶工程'],
    '膜蛋白': ['跨膜结构', 'GPCR', '离子通道', '膜环境', '去垢剂'],
    '抗体设计': ['抗体工程', '人源化', '亲和力成熟', 'CDR', '免疫原性'],
    '冷冻电镜': ['Cryo-EM', '单颗粒分析', '三维重构', '分辨率', '样本制备'],
    '蛋白质组学': ['质谱分析', '定量蛋白质组', 'PTM', '生物标志物', '样本处理']
}

# 生成模拟的笔记文本内容
def generate_note_text(note_id, fields, content_type):
    """为笔记生成模拟的文本内容"""
    text_parts = []
    
    # 基于领域和类型生成关键词
    for field in fields:
        if field in ACADEMIC_KEYWORDS:
            keywords = ACADEMIC_KEYWORDS[field]
            text_parts.extend(keywords)
    
    # 基于内容类型添加特征词
    type_keywords = {
        '最新论文': ['最新研究', '发表', '期刊', '影响因子', '创新'],
        '经典方法': ['经典', '方法学', 'protocol', '标准化', '验证'],
        '综述文章': ['综述', '进展', '展望', '挑战', '机遇'],
        '技术教程': ['教程', '步骤', '操作', '软件', '工具'],
        '实验技巧': ['技巧', '经验', '优化', ' troubleshooting', 'protocol'],
        '算法解读': ['算法', '原理', '实现', '代码', '性能'],
        '应用案例': ['应用', '实例', '成功', '案例研究', '临床']
    }
    
    if content_type in type_keywords:
        text_parts.extend(type_keywords[content_type])
    
    # 生成多段文本
    n_paragraphs = random.randint(3, 8)
    paragraphs = []
    for _ in range(n_paragraphs):
        n_sentences = random.randint(3, 6)
        paragraph_words = []
        for _ in range(n_sentences * 10):  # 每句约10个词
            word = random.choice(text_parts) if text_parts else "蛋白质"
            paragraph_words.append(word)
        paragraphs.append(" ".join(paragraph_words))
    
    return "\n".join(paragraphs)

def generate_content_features(notes_metadata_path='data/notes_metadata.csv', output_dir='data'):
    """生成内容特征"""
    
    # 加载笔记元数据
    notes_df = pd.read_csv(notes_metadata_path)
    
    # 为每篇笔记生成文本内容
    note_texts = []
    for _, note in notes_df.iterrows():
        fields = json.loads(note['fields'].replace("'", '"')) if isinstance(note['fields'], str) else note['fields']
        text = generate_note_text(note['note_id'], fields, note['content_type'])
        note_texts.append(text)
    
    # 1. TF-IDF特征向量
    print("Generating TF-IDF features...")
    vectorizer = TfidfVectorizer(
        max_features=100,
        min_df=2,
        max_df=0.8,
        ngram_range=(1, 2)
    )
    tfidf_matrix = vectorizer.fit_transform(note_texts)
    tfidf_features = tfidf_matrix.toarray()
    
    # 保存TF-IDF特征
    feature_names = vectorizer.get_feature_names_out()
    tfidf_df = pd.DataFrame(
        tfidf_features,
        columns=[f'tfidf_{name}' for name in feature_names],
        index=notes_df['note_id']
    )
    tfidf_df.to_csv(f'{output_dir}/note_tfidf_features.csv')
    print(f"Generated TF-IDF features: {tfidf_features.shape}")
    
    # 2. 主题标签（多标签分类）
    print("Generating topic labels...")
    
    # 定义主题类别
    topics = [
        '结构预测', '分子模拟', '机器学习', '实验技术',
        '药物设计', '疾病研究', '方法学', '应用案例'
    ]
    
    topic_labels = []
    for i, note in notes_df.iterrows():
        fields = json.loads(note['fields'].replace("'", '"')) if isinstance(note['fields'], str) else note['fields']
        
        # 基于领域映射到主题
        note_topics = []
        
        field_topic_map = {
            '蛋白质结构预测': '结构预测',
            'AlphaFold': '结构预测',
            '蛋白质折叠': '结构预测',
            '分子动力学': '分子模拟',
            '机器学习': '机器学习',
            '深度学习': '机器学习',
            '图神经网络': '机器学习',
            '扩散模型': '机器学习',
            '冷冻电镜': '实验技术',
            'X射线晶体学': '实验技术',
            'NMR': '实验技术',
            '质谱分析': '实验技术',
            '分子对接': '药物设计',
            '虚拟筛选': '药物设计',
            '药物设计': '药物设计',
            '癌症生物学': '疾病研究',
            '神经退行性疾病': '疾病研究',
            '罕见病研究': '疾病研究'
        }
        
        for field in fields:
            if field in field_topic_map:
                note_topics.append(field_topic_map[field])
        
        # 基于内容类型添加主题
        content_type_topic_map = {
            '经典方法': '方法学',
            '技术教程': '方法学',
            '实验技巧': '方法学',
            '应用案例': '应用案例',
            '最新论文': '应用案例'
        }
        
        if note['content_type'] in content_type_topic_map:
            note_topics.append(content_type_topic_map[note['content_type']])
        
        # 去重
        note_topics = list(set(note_topics))
        
        # 如果没有匹配到主题，随机分配一个
        if not note_topics:
            note_topics = [random.choice(topics)]
        
        topic_labels.append({
            'note_id': note['note_id'],
            'topics': json.dumps(note_topics, ensure_ascii=False),
            'topic_vector': json.dumps([1 if t in note_topics else 0 for t in topics])
        })
    
    topics_df = pd.DataFrame(topic_labels)
    topics_df.to_csv(f'{output_dir}/note_topic_labels.csv', index=False)
    print(f"Generated topic labels for {len(topics_df)} notes")
    
    # 3. 引用热度（模拟）
    print("Generating citation popularity...")
    
    citation_data = []
    for _, note in notes_df.iterrows():
        # 基于质量分数和发布时间计算引用热度
        base_citations = int(note['popularity'] * 100)
        
        # 添加一些随机性
        citations = max(0, int(base_citations + np.random.normal(0, 20)))
        
        # 近期热度（最近30天的浏览量）
        recent_views = int(citations * np.random.uniform(0.1, 0.3))
        
        citation_data.append({
            'note_id': note['note_id'],
            'total_citations': citations,
            'recent_views_30d': recent_views,
            'trend_score': recent_views / max(citations, 1)  # 上升趋势指标
        })
    
    citation_df = pd.DataFrame(citation_data)
    citation_df.to_csv(f'{output_dir}/note_citation_stats.csv', index=False)
    print(f"Generated citation stats")
    
    # 4. 内容质量评分
    print("Generating quality scores...")
    
    quality_data = []
    for _, note in notes_df.iterrows():
        # 基础质量分数
        base_quality = note['quality_score']
        
        # 基于互动数据调整（这里使用模拟）
        engagement_score = np.random.beta(2, 2)
        
        # 专业度评分
        professionalism = np.random.beta(3, 2)
        
        # 完整性评分
        completeness = np.random.beta(2.5, 2)
        
        # 综合质量分
        overall_quality = 0.4 * base_quality + 0.3 * engagement_score + \
                         0.15 * professionalism + 0.15 * completeness
        
        quality_data.append({
            'note_id': note['note_id'],
            'overall_quality': round(overall_quality, 3),
            'engagement_score': round(engagement_score, 3),
            'professionalism': round(professionalism, 3),
            'completeness': round(completeness, 3)
        })
    
    quality_df = pd.DataFrame(quality_data)
    quality_df.to_csv(f'{output_dir}/note_quality_scores.csv', index=False)
    print(f"Generated quality scores")
    
    # 5. 合并所有特征
    print("Merging all features...")
    
    # 合并数据
    features_df = notes_df.merge(topics_df, on='note_id')
    features_df = features_df.merge(citation_df, on='note_id')
    features_df = features_df.merge(quality_df, on='note_id')
    
    # 保存完整的特征数据
    features_df.to_csv(f'{output_dir}/note_features_complete.csv', index=False)
    print(f"Saved complete features to {output_dir}/note_features_complete.csv")
    
    return features_df, tfidf_df

if __name__ == '__main__':
    import os
    os.makedirs('data', exist_ok=True)
    
    generate_content_features()
