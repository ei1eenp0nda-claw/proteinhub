# ProteinHub 多模态融合推荐系统 (MMF-ProteinHub)

## 问题定义

**三模态数据**：
| 模态 | 数据 | 特征表示 |
|------|------|----------|
| **图模态 (G)** | PPI网络 (158k边, 500+可信对) | 蛋白节点嵌入 (Node2Vec/GNN) |
| **内容模态 (C)** | 164篇笔记 (标题+摘要+比喻) | 文本嵌入 (BERT/TF-IDF) |
| **行为模态 (B)** | 800用户, 118k行为记录 | 用户-物品交互矩阵 |

**目标**：融合三模态信息，生成个性化推荐

---

## 架构设计：Middle Fusion（中期融合）

```
┌─────────────────────────────────────────────────────────────┐
│                    多模态融合推荐架构                         │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   图编码器    │      │   内容编码器  │      │   行为编码器  │
│  Graph Encoder│      │ Content Enc  │      │ Behavior Enc │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       ▼                     ▼                     ▼
  ┌─────────┐          ┌─────────┐          ┌─────────┐
  │ h_graph │          │ h_content│         │ h_behavior│
  │ (64d)   │          │ (128d)  │          │ (64d)   │
  └────┬────┘          └────┬────┘          └────┬────┘
       │                     │                     │
       └────────────┬────────┴────────┬────────────┘
                    ▼                 ▼
            ┌───────────────┐  ┌───────────────┐
            │  模态注意力融合  │  │   门控融合     │
            │  Cross-Attention│  │  Gated Fusion │
            └───────┬───────┘  └───────┬───────┘
                    │                   │
                    └─────────┬─────────┘
                              ▼
                    ┌─────────────────┐
                    │   融合表征 h_fusion │
                    │    (256d)        │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │   预测层 (MLP)   │
                    │  输出: 点击概率   │
                    └─────────────────┘
```

---

## 各模态编码器设计

### 1. 图模态编码 (Graph Modality)

**输入**：PPI网络 (158,152对，稀疏)

**方法A：Node2Vec（轻量级）**
```python
# 只对500+可信对构建子图
from node2vec import Node2Vec

# 构建图
G = nx.Graph()
for protein_a, protein_b, score in ppi_data:
    if score >= 0.6:  # 只保留可信对
        G.add_edge(protein_a, protein_b, weight=score)

# Node2Vec嵌入
node2vec = Node2Vec(G, dimensions=64, walk_length=30, num_walks=200)
model = node2vec.fit(window=10, min_count=1)

# 蛋白嵌入: {protein_id: 64d向量}
protein_embeddings = {node: model.wv[node] for node in G.nodes()}
```

**方法B：GraphSAGE（GNN，效果更好）**
```python
import torch
from torch_geometric.nn import SAGEConv

class GraphEncoder(torch.nn.Module):
    def __init__(self, in_channels=1, hidden_channels=64, out_channels=64):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, out_channels)
        
    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index)
        return x  # [num_proteins, 64]
```

**笔记的图表征**：
```python
def get_note_graph_embedding(note_id):
    """笔记中所有蛋白的嵌入聚合"""
    proteins = get_note_proteins(note_id)  # ['CIDEA', 'FSP27', ...]
    embeddings = [protein_embeddings[p] for p in proteins if p in protein_embeddings]
    if embeddings:
        return np.mean(embeddings, axis=0)  # 平均池化
    return np.zeros(64)
```

---

### 2. 内容模态编码 (Content Modality)

**输入**：笔记内容（标题+核心发现+学术比喻）

**方法A：BERT嵌入**
```python
from transformers import BertTokenizer, BertModel

# 使用PubMedBERT（生物医学领域预训练）
tokenizer = BertTokenizer.from_pretrained('microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract')
model = BertModel.from_pretrained('microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract')

def encode_note_content(text):
    """BERT编码笔记内容"""
    inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
    outputs = model(**inputs)
    # 取[CLS]token的嵌入
    cls_embedding = outputs.last_hidden_state[:, 0, :].detach().numpy()
    return cls_embedding[0]  # 768d
```

**方法B：TF-IDF + SVD（轻量级）**
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

# TF-IDF
tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1,2))
tfidf_matrix = tfidf.fit_transform(note_contents)  # [164, 5000]

# SVD降维
svd = TruncatedSVD(n_components=128)
content_embeddings = svd.fit_transform(tfidf_matrix)  # [164, 128]
```

---

### 3. 行为模态编码 (Behavior Modality)

**输入**：用户-笔记交互矩阵 (800用户 × 164笔记)

**方法：矩阵分解 (SVD/ALS)**
```python
from sklearn.decomposition import NMF

# 构建交互矩阵
interaction_matrix = build_user_note_matrix()  # [800, 164]

# 非负矩阵分解
nmf = NMF(n_components=64, init='random', random_state=42)
user_embeddings = nmf.fit_transform(interaction_matrix)  # [800, 64]
note_embeddings_behavior = nmf.components_.T  # [164, 64]
```

**双塔模型（在线推理快）**
```python
class TwoTowerModel(torch.nn.Module):
    def __init__(self, user_dim=800, note_dim=164, embed_dim=64):
        super().__init__()
        self.user_embedding = torch.nn.Embedding(user_dim, embed_dim)
        self.note_embedding = torch.nn.Embedding(note_dim, embed_dim)
        
    def forward(self, user_ids, note_ids):
        user_vec = self.user_embedding(user_ids)  # [batch, 64]
        note_vec = self.note_embedding(note_ids)  # [batch, 64]
        score = (user_vec * note_vec).sum(dim=1)  # 内积
        return score
```

---

## 模态融合策略

### 策略1：注意力融合 (Attention Fusion) ⭐推荐

```python
class MultimodalFusion(torch.nn.Module):
    def __init__(self, graph_dim=64, content_dim=128, behavior_dim=64, fusion_dim=256):
        super().__init__()
        self.fusion_dim = fusion_dim
        
        # 投影到统一维度
        self.graph_proj = torch.nn.Linear(graph_dim, fusion_dim)
        self.content_proj = torch.nn.Linear(content_dim, fusion_dim)
        self.behavior_proj = torch.nn.Linear(behavior_dim, fusion_dim)
        
        # 跨模态注意力
        self.cross_attention = torch.nn.MultiheadAttention(fusion_dim, num_heads=8)
        
        # 自注意力 (学习模态间关系)
        self.self_attention = torch.nn.MultiheadAttention(fusion_dim, num_heads=8)
        
    def forward(self, h_graph, h_content, h_behavior):
        """
        h_graph: [batch, 64]
        h_content: [batch, 128]
        h_behavior: [batch, 64]
        """
        # 投影
        g = self.graph_proj(h_graph)       # [batch, 256]
        c = self.content_proj(h_content)   # [batch, 256]
        b = self.behavior_proj(h_behavior) # [batch, 256]
        
        # 堆叠: [3, batch, 256]
        multimodal_input = torch.stack([g, c, b], dim=0)
        
        # 自注意力 (模态间交互)
        attended, attention_weights = self.self_attention(
            multimodal_input, multimodal_input, multimodal_input
        )
        
        # 平均池化融合
        fused = attended.mean(dim=0)  # [batch, 256]
        
        return fused, attention_weights
```

**注意力权重解释**：
```
注意力矩阵 (3×3):
          Graph  Content  Behavior
Graph      0.4     0.3       0.3
Content    0.2     0.6       0.2
Behavior   0.3     0.2       0.5

含义: Content模态最重要(自注意力0.6)，因为文本信息丰富
```

---

### 策略2：门控融合 (Gated Fusion)

```python
class GatedFusion(torch.nn.Module):
    def __init__(self, graph_dim=64, content_dim=128, behavior_dim=64, output_dim=256):
        super().__init__()
        total_dim = graph_dim + content_dim + behavior_dim
        
        # 门控网络 (学习各模态权重)
        self.gate = torch.nn.Sequential(
            torch.nn.Linear(total_dim, 3),  # 3个模态的权重
            torch.nn.Softmax(dim=1)
        )
        
        # 融合层
        self.fusion = torch.nn.Linear(total_dim, output_dim)
        
    def forward(self, h_graph, h_content, h_behavior):
        # 拼接
        concatenated = torch.cat([h_graph, h_content, h_behavior], dim=1)
        
        # 计算门控权重
        gates = self.gate(concatenated)  # [batch, 3]
        
        # 加权融合
        weighted = torch.cat([
            h_graph * gates[:, 0:1],
            h_content * gates[:, 1:2],
            h_behavior * gates[:, 2:3]
        ], dim=1)
        
        fused = self.fusion(weighted)
        return fused, gates
```

---

## 完整训练流程

```python
class MMFProteinHub(torch.nn.Module):
    """多模态融合推荐模型"""
    
    def __init__(self):
        super().__init__()
        # 各模态编码器
        self.graph_encoder = GraphEncoder()
        self.content_encoder = BERTEncoder()  # 或TF-IDF
        self.behavior_encoder = TwoTowerModel()
        
        # 融合层
        self.fusion = MultimodalFusion(fusion_dim=256)
        
        # 预测层
        self.predictor = torch.nn.Sequential(
            torch.nn.Linear(256, 128),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.3),
            torch.nn.Linear(128, 1),
            torch.nn.Sigmoid()
        )
        
    def forward(self, user_id, note_id, protein_ids, note_text):
        # 各模态特征
        h_graph = self.graph_encoder(protein_ids)      # [batch, 64]
        h_content = self.content_encoder(note_text)    # [batch, 128]
        h_behavior = self.behavior_encoder(user_id, note_id)  # [batch, 64]
        
        # 融合
        h_fusion, attention_weights = self.fusion(
            h_graph, h_content, h_behavior
        )  # [batch, 256]
        
        # 预测点击概率
        click_prob = self.predictor(h_fusion)  # [batch, 1]
        
        return click_prob, attention_weights

# 损失函数
criterion = torch.nn.BCELoss()  # 二分类交叉熵
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
```

---

## 推理阶段 (在线推荐)

```python
def recommend_multimodal(user_id, top_k=10):
    """多模态融合推荐"""
    
    # 1. 获取候选集 (粗排)
    candidates = get_candidate_notes(user_id, n=100)  # CF + 热门
    
    # 2. 多模态特征提取
    user_history = get_user_history(user_id)
    history_proteins = get_proteins_from_notes(user_history)
    
    scores = []
    for note_id in candidates:
        note_proteins = get_note_proteins(note_id)
        note_text = get_note_text(note_id)
        
        # 各模态得分
        graph_score = compute_graph_similarity(history_proteins, note_proteins)
        content_score = compute_content_similarity(user_id, note_id)
        behavior_score = compute_behavior_score(user_id, note_id)
        
        # 融合预测
        with torch.no_grad():
            prob, weights = model.predict(
                graph_score, content_score, behavior_score
            )
        
        scores.append({
            'note_id': note_id,
            'score': prob.item(),
            'graph_score': graph_score,
            'content_score': content_score,
            'behavior_score': behavior_score,
            'modality_weights': weights.numpy()
        })
    
    # 3. 精排返回TopK
    scores.sort(key=lambda x: x['score'], reverse=True)
    return scores[:top_k]
```

---

## 实验设计 (A/B Test)

| 组 | 模型 | 评估指标 |
|----|------|----------|
| 对照组 | 纯行为CF | CTR, 收藏率, 阅读时长 |
| 实验组A | 行为+内容 | CTR, 收藏率, 阅读时长 |
| 实验组B | 行为+内容+PPI(我们的) | CTR, 收藏率, 阅读时长, 新蛋白发现率 |

**关键指标**：
- **新蛋白发现率**：用户通过推荐了解到的新蛋白比例
- **跨通路点击率**：用户点击非熟悉通路笔记的比例

---

## 部署架构

```
离线训练 (每日):
  - 重新训练GNN嵌入
  - 更新内容编码器
  - 重训练融合模型

在线服务 (实时):
  - 用户请求 → 召回(CF+热门) → 100候选
  - 多模态特征提取 (缓存)
  - 融合模型精排 → Top10
  - 返回推荐结果 (20ms内)
```

---

## 总结

| 特性 | 方案 |
|------|------|
| **图模态** | Node2Vec/GNN (64d) |
| **内容模态** | PubMedBERT/TF-IDF (128d) |
| **行为模态** | 双塔模型/矩阵分解 (64d) |
| **融合策略** | 注意力融合 (Attentive Fusion) |
| **预测** | MLP输出点击概率 |
| **特色** | 可解释性强 (注意力权重) |

**优势**：
1. **科学发现导向**：PPI网络引导跨蛋白/通路推荐
2. **可解释**：注意力权重显示各模态贡献
3. **冷启动友好**：图模态不依赖用户行为
4. **实时性**：轻量级架构，推理<20ms

需要我实现这个多模态融合模型吗？