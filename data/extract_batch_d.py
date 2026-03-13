#!/usr/bin/env python3
"""Extract papers 91-120 from raw_papers.json sorted by citation count"""
import json

# Read the full file
with open('/root/.openclaw/workspace/projects/proteinhub/data/raw_papers.json', 'r') as f:
    papers = json.load(f)

# Sort by citation count (descending)
papers_sorted = sorted(papers, key=lambda x: x.get('citationCount', 0), reverse=True)

# Get papers 91-120 (0-indexed: 90-119)
target_papers = papers_sorted[90:120]

# Print info
print(f"Total papers: {len(papers)}")
print(f"Target papers (91-120): {len(target_papers)}")
print("\n--- Papers 91-120 ---\n")

for i, paper in enumerate(target_papers, 91):
    print(f"#{i}: {paper.get('title', 'N/A')[:80]}...")
    print(f"    Citations: {paper.get('citationCount', 0)}")
    print(f"    Year: {paper.get('year', 'N/A')}")
    print(f"    DOI: {paper.get('externalIds', {}).get('DOI', 'N/A')}")
    print()

# Save target papers
with open('/root/.openclaw/workspace/projects/proteinhub/data/v2_batch_d_target_papers.json', 'w') as f:
    json.dump(target_papers, f, indent=2)

print(f"\nSaved {len(target_papers)} papers to v2_batch_d_target_papers.json")
