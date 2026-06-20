---
name: paper-search-download
description: 搜索指定领域的顶会/顶刊论文，输出标题、年份、出处、链接、方法关键词、建议精读。
---

# Paper Search

## When to Use

- 用户说"帮我搜《X》方向的论文"
- 文献调研时快速收集相关论文
- 需要了解某个方向的最新顶会工作

## Usage

```bash
python tools/search_papers.py "few-shot object detection" --max 10 --years 2024,2025,2026
```

## Search Sources

| Source | Coverage | Priority |
|--------|----------|----------|
| arXiv API | 全量预印本 (journal-ref 标注场馆) | 广泛覆盖 |
| Semantic Scholar | 已发表论文 (venue 字段) | 精筛场馆 |

## Priority Venues

CVPR > ICCV > AAAI > NeurIPS > ICML > TPAMI > IJCV > TIP > ECCV > WACV

## Output Format

对每篇论文输出：

```
[序号] [年份] [出处] 论文标题
       建议精读: ⭐/✓/? | arXiv: XXXX.XXXXX | 链接
       方法关键词: xxx, xxx, xxx
       简介: 一句话概括
```

## 精读建议

| 标记 | 条件 |
|------|------|
| ⭐ 建议精读 | CVPR, ICCV, AAAI, NeurIPS, ICML, TPAMI |
| ✓ 可读 | 其他正式发表 (ECCV, WACV, IJCV, TIP) |
| ? 预印本 | 仅 arXiv，未确认被接收 |
