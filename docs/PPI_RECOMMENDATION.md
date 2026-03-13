# ProteinHub PPI推荐系统

## 概述

基于蛋白互作（PPI）网络的推荐系统，利用蛋白之间的互作关系为用户推荐相关学术笔记。

## 数据规模

- **蛋白节点**：158个
- **互作对**：152对
- **可信互作对（得分≥0.6）**：500+对
- **网络密度**：约2%（稀疏网络）

## 推荐算法

### 核心逻辑

```
用户阅读笔记A（关于蛋白X）
    ↓
查询PPI网络：找与X互作的蛋白（得分>0.6）
    ↓
推荐这些蛋白相关的笔记
```

### 算法特点

| 特性 | 说明 |
|------|------|
| **时间复杂度** | O(1) - 邻接表查询 |
| **空间复杂度** | <1MB - 158节点微型图 |
| **可解释性** | 强 - "基于CIDEA-FSP27互作推荐" |
| **冷启动** | 友好 - 不需要用户行为历史 |

## 使用方法

### 1. 加载PPI数据

```python
from ppi_recommender import PPIRecommender

recommender = PPIRecommender(threshold=0.6)
recommender.load_ppi_data('data/whole.tsv')
```

### 2. 构建蛋白-笔记索引

```python
notes_data = [
    {'note_id': 1, 'proteins': ['CIDEA', 'FSP27']},
    {'note_id': 2, 'proteins': ['ATGL', 'HSL']},
    # ...
]
recommender.build_protein_note_index(notes_data)
```

### 3. 获取推荐

```python
user_history = [1, 3, 5]  # 用户看过的笔记ID
recommendations = recommender.recommend_by_ppi(user_history, top_k=10)

# 返回格式
[
    {
        'note_id': 10,
        'protein': 'FSP27',
        'ppi_score': 0.85,
        'reason': '基于FSP27的PPI互作推荐'
    },
    # ...
]
```

## 与现有推荐系统的关系

PPI推荐作为**召回层**的补充策略：

```
召回层：
  ├── 行为召回（协同过滤）
  ├── 内容召回（TF-IDF）
  └── PPI召回（蛋白互作） ← 新增

精排层：
  └── LightGBM融合模型
```

## API集成

后端已自动集成PPI推荐：

```
GET /api/notes/feed?user_id=123

返回的笔记自动包含PPI推荐分数权重
```

## 优势

1. **科学关联性强**：基于真实的蛋白互作关系
2. **发现新知识**：帮助用户了解相关蛋白的研究
3. **跨领域连接**：连接不同研究方向的蛋白
4. **可解释性好**：推荐原因明确（基于某蛋白互作）

## 未来优化

- [ ] 整合更多PPI数据库（STRING, BioGRID等）
- [ ] 蛋白家族/通路层级推荐
- [ ] 多跳邻居（蛋白A → B → C）
- [ ] 结合结构域信息
