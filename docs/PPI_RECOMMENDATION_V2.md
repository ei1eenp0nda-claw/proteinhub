# ProteinHub PPI推荐系统 v2 - 中规模网络优化

## 数据规模（修正）

| 指标 | 数值 | 说明 |
|------|------|------|
| **总互作对** | **158,152对** | 原始预测结果 |
| **可信对 (>0.6)** | **~500对** | 占比0.3%，极度稀疏 |
| **网络密度** | ~0.003% | 超稀疏图 |

## 关键洞察

**稀疏性分析**：
- 500对可信互作 / 158,152总对 = **0.3%**
- 这意味着：平均每蛋白只有 **3-5个** 可信互作伙伴
- **冷启动问题严重**：大多数蛋白没有高质量互作

## 推荐策略调整

### 方案1：可信网络+基于内容的Fallback

```
if 蛋白A有可信互作伙伴:
    推荐伙伴蛋白相关的笔记（PPI召回）
else:
    推荐与蛋白A功能相似/同通路的笔记（内容召回）
```

**优势**：
- 避免推荐质量低的互作
- 保证覆盖率

### 方案2：加权多跳（Multi-hop）

对于只有1-2个可信互作的蛋白，扩展搜索：

```
蛋白A ←[0.85]→ 蛋白B ←[0.75]→ 蛋白C

蛋白A到蛋白C的间接推荐得分 = 0.85 * 0.75 = 0.64
```

**实现**：
- BFS搜索2跳邻居
- 路径得分相乘
- 只保留>0.5的路径

### 方案3：通路/家族层面推荐

当具体互作不足时，上升到通路层面：

```
蛋白A（脂滴代谢通路）
    ↓
推荐同通路其他蛋白的笔记
    ↓
CIDEA, FSP27, Perilipin, ATGL...
```

## 技术实现（数据库优化）

由于158k对数据，改用**数据库存储**：

### 数据库表设计

```sql
-- PPI互作表
CREATE TABLE ppi_interactions (
    id SERIAL PRIMARY KEY,
    protein_a VARCHAR(50) NOT NULL,
    protein_b VARCHAR(50) NOT NULL,
    score DECIMAL(4,3) NOT NULL,  -- 0.000-1.000
    is_high_confidence BOOLEAN DEFAULT FALSE,  -- score >= 0.6
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_ppi_protein_a ON ppi_interactions(protein_a);
CREATE INDEX idx_ppi_protein_b ON ppi_interactions(protein_b);
CREATE INDEX idx_ppi_high_confidence ON ppi_interactions(protein_a, is_high_confidence) WHERE is_high_confidence = TRUE;
CREATE INDEX idx_ppi_score ON ppi_interactions(score) WHERE score >= 0.6;
```

### 推荐查询（SQL实现）

```sql
-- 查询蛋白A的所有可信互作伙伴
SELECT protein_b, score 
FROM ppi_interactions 
WHERE protein_a = 'CIDEA' 
  AND is_high_confidence = TRUE 
ORDER BY score DESC;

-- 查询与蛋白A相关的笔记（通过互作伙伴）
SELECT DISTINCT n.id, n.title, ppi.score as ppi_score
FROM notes n
JOIN note_proteins np ON n.id = np.note_id
JOIN ppi_interactions ppi ON np.protein = ppi.protein_b
WHERE ppi.protein_a = 'CIDEA'
  AND ppi.is_high_confidence = TRUE
ORDER BY ppi.score DESC
LIMIT 20;
```

## 推荐算法伪代码

```python
def recommend_by_ppi_v2(protein, top_k=10):
    """
    改进版PPI推荐：处理稀疏网络
    """
    recommendations = []
    
    # Step 1: 直接可信互作（1跳）
    direct_neighbors = db.query(
        "SELECT protein_b, score FROM ppi_interactions "
        "WHERE protein_a = ? AND is_high_confidence = TRUE "
        "ORDER BY score DESC",
        (protein,)
    ).fetchall()
    
    for neighbor, score in direct_neighbors:
        notes = get_notes_by_protein(neighbor)
        for note in notes:
            recommendations.append({
                'note_id': note.id,
                'protein': neighbor,
                'ppi_score': score,
                'hop': 1,  # 1跳
                'reason': f'{protein}-{neighbor}互作(得分{score})'
            })
    
    # Step 2: 如果直接互作不足，搜索2跳
    if len(recommendations) < top_k:
        for neighbor, score1 in direct_neighbors:
            second_hop = db.query(
                "SELECT protein_b, score FROM ppi_interactions "
                "WHERE protein_a = ? AND is_high_confidence = TRUE",
                (neighbor,)
            ).fetchall()
            
            for second_neighbor, score2 in second_hop:
                if second_neighbor != protein:  # 避免回到起点
                    combined_score = score1 * score2
                    if combined_score >= 0.5:  # 阈值
                        notes = get_notes_by_protein(second_neighbor)
                        for note in notes:
                            recommendations.append({
                                'note_id': note.id,
                                'protein': second_neighbor,
                                'ppi_score': combined_score,
                                'hop': 2,
                                'reason': f'{protein}-{neighbor}-{second_neighbor}(间接,得分{combined_score:.2f})'
                            })
    
    # Step 3: 去重并排序
    seen_notes = set()
    final_recommendations = []
    for rec in sorted(recommendations, key=lambda x: (-x['hop'], -x['ppi_score'])):
        if rec['note_id'] not in seen_notes:
            final_recommendations.append(rec)
            seen_notes.add(rec['note_id'])
            if len(final_recommendations) >= top_k:
                break
    
    return final_recommendations
```

## 与现有推荐系统的融合

```python
def get_personalized_feed_v2(user_id):
    """融合PPI推荐的个性化Feed"""
    
    # 1. 获取用户历史
    history = get_user_history(user_id)
    
    # 2. 提取历史笔记中的蛋白
    proteins = extract_proteins_from_notes(history)
    
    # 3. 多路召回
    candidates = []
    
    # 3.1 行为召回（CF）
    cf_recs = collaborative_filtering_recall(user_id)
    candidates.extend(cf_recs)
    
    # 3.2 内容召回（Tag匹配）
    content_recs = content_based_recall(user_id)
    candidates.extend(content_recs)
    
    # 3.3 PPI召回（新增）
    for protein in proteins[:5]:  # 取前5个蛋白
        ppi_recs = recommend_by_ppi_v2(protein, top_k=5)
        for rec in ppi_recs:
            candidates.append({
                'note_id': rec['note_id'],
                'source': 'ppi',
                'ppi_score': rec['ppi_score'],
                'reason': rec['reason']
            })
    
    # 4. 精排（融合分数）
    ranked = rank_candidates(candidates, user_id)
    
    return ranked
```

## 预期效果

| 场景 | 效果 |
|------|------|
| 用户看CIDEA笔记 | 推荐FSP27笔记（直接互作，高可信度） |
| 用户看ATGL笔记 | 推荐HSL笔记（同脂解通路） |
| 冷启动新用户 | 推荐高可信度PPI对的热门笔记 |

## 下一步实现

1. **数据导入**：将TSV导入PostgreSQL ppi_interactions表
2. **建立索引**：protein_a + protein_b + is_high_confidence
3. **修改推荐API**：融合PPI召回
4. **A/B测试**：对比含PPI vs 不含PPI的推荐效果
