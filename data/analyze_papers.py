import json
import os
import re

# 读取JSON文件
with open('/root/.openclaw/workspace/projects/proteinhub/data/raw_papers.json', 'r') as f:
    papers = json.load(f)

# 按引用数排序（降序）
papers_sorted = sorted(papers, key=lambda x: x.get('citationCount', 0), reverse=True)

# 获取第31-60篇论文（索引30-59）
target_papers = papers_sorted[30:60]

print(f"Total papers in file: {len(papers)}")
print(f"Selected papers: {len(target_papers)}")
print("\nTop 10 of selected papers:")
for i, p in enumerate(target_papers[:10], 31):
    print(f"{i}. {p.get('title', 'N/A')[:60]}... (Citations: {p.get('citationCount', 0)})")
