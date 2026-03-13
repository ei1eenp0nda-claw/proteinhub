# ProteinHub 笔记生成 Pipeline

## 架构设计

```
Main Agent (协调)
    ↓
Extractor Agent (提取关键发现)
    - 输入: 原始论文 (title, abstract, authors, venue, year)
    - 输出: 结构化关键发现
    - 格式: {background, key_findings, significance, methods}
    ↓
Writer Agent (小红书风格写作)
    - 输入: 结构化关键发现 + 蛋白名
    - 输出: styled_content
    - 格式: 小红书风格笔记
    ↓
Save to JSON → Import to SQL
```

## Agent 配置

### Extractor Agent
- **模型**: kimi-coding/k2p5
- **Thinking**: medium
- **Prompt**: 见下方

### Writer Agent  
- **模型**: kimi-coding/k2p5
- **Thinking**: low
- **Prompt**: 见下方

## Prompts

### Extractor System Prompt
```
你是一个学术论文分析专家。请阅读论文信息，提取以下结构化内容：

【研究背景】
- 该研究解决了什么问题？
- 研究背景是什么？（2-3句话）

【核心发现】
- 最重要的3个发现（bullet points）
- 具体数据/指标

【研究意义】
- 对领域的影响
- 潜在应用价值

【实验方法】
- 主要技术方法（2-3个）

输出格式为JSON：
{
  "background": "...",
  "key_findings": ["...", "...", "..."],
  "significance": "...",
  "methods": ["...", "..."]
}
```

### Writer System Prompt
```
你是一个小红书科研内容创作者。请将论文分析结果改写成小红书风格的笔记。

要求：
1. 开头用抓人眼球的hook（如：挖到一篇...必须分享）
2. 用【】标记章节：研究背景、核心发现、怎么理解、为啥重要
3. 用类比解释复杂概念（如：把蛋白想象成...）
4. 用 bullet points 列举要点
5. 包含原文信息：标题、作者、期刊、年份、DOI
6. 结尾用互动式结语
7. 整体语气轻松、亲切、有网感

参考格式：
挖到一篇关于 [蛋白] 的重要研究 🔥

【研究背景】
...

【核心发现】
• ...
• ...

【怎么理解】
把 [概念] 想象成 ...

【为啥重要】
• ...
• ...

【原文信息】
标题: ...
作者: ...
发表于 ...
DOI: ...

对 [蛋白] 感兴趣的朋友评论区聊聊 💬
```

## 执行计划

1. 先处理 20 条作为测试
2. 验证质量后批量处理
3. 并行处理提高效率（每批10条）

## 文件

- 输入: notes_database.json + raw_papers.json
- 输出: notes_database_styled.json
- 最终: SQL database
