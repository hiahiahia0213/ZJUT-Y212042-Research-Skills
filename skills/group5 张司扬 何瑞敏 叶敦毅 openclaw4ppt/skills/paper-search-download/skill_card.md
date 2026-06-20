# Skill Card: Paper Search

## 1. Skill 基本信息

| 项目 | 内容 |
|---|---|
| Skill 名称 | paper-search-download |
| 当前定位 | 论文查找与结构化推荐 |
| 中文名称 | 顶会/顶刊论文查找 skill |
| 所属科研场景 | 文献调研、确定精读论文、生成论文候选清单 |
| 主入口文件 | `SKILL.md` |
| 配套脚本 | `tools/search_papers.py` |
| 下游衔接 | 可将候选论文交给 `paper-to-ppt-pipeline` 继续生成 PPT |

## 2. 一句话简介

`paper-search-download` 用于按研究主题查找相关领域论文，优先从 CVPR、ICCV、AAAI、NeurIPS、ICML、TPAMI、IJCV、TIP 等会议和期刊中选择，并输出标题、年份、出处、链接、方法关键词、简介和精读建议。

## 3. 解决的科研问题

在开始做论文汇报或课题调研前，用户往往还没有确定具体论文，只知道一个方向。此时需要一个轻量但结构化的检索 skill，帮助用户快速回答：

- 这个方向近期有哪些论文？
- 哪些论文可能来自顶会/顶刊？
- 哪些论文更值得精读？
- 每篇论文大概用了什么方法关键词？
- 后续如果要做 PPT，应该优先选择哪篇？

本 skill 的重点是“找论文和推荐论文”，不是直接制作 PPT。

## 4. 输入与输出

### 输入

| 输入 | 示例 |
|---|---|
| 研究主题 | `few-shot object detection` |
| 年份范围 | `2024,2025,2026` |
| 最大结果数 | `10` |
| 优先 venue | CVPR、ICCV、AAAI、NeurIPS、ICML、TPAMI、IJCV、TIP |

### 输出

固定输出每篇论文的：

- 论文标题
- 年份
- 出处或 arXiv 信息
- 链接
- 方法关键词
- 一句话简介
- 是否建议精读

## 5. 工作流程

1. 将用户主题改写为适合论文检索的英文关键词。
2. 搜索 arXiv 和 Semantic Scholar。
3. 对候选论文按标题去重。
4. 根据 venue 优先级排序。
5. 根据标题、摘要和主题相关性筛选。
6. 提取方法关键词。
7. 输出结构化论文候选列表。
8. 给出精读优先级建议。

## 6. 精读建议规则

| 标记 | 条件 | 建议 |
|---|---|---|
| 星标建议精读 | 顶会/顶刊，且与主题高度相关 | 优先下载 PDF 并进入 PPT pipeline |
| 可读 | 正式发表或与主题中度相关 | 可作为补充材料 |
| 预印本 | 仅 arXiv，尚未确认发表 | 需要人工判断创新性和可靠性 |
| 不建议 | 主题偏离或任务不匹配 | 不作为主讲论文 |

## 7. 与 `paper-search` 的关系

本目录当前版本更偏向“查找与推荐论文”，而 `paper-search` 目录中的版本还强调 PDF 下载和 JSON 输出。实际使用时可按任务选择：

- 只需要论文候选清单：使用本 skill。
- 需要下载 PDF 并进入完整流水线：使用 `paper-search` 或直接调用 `tools/search_papers.py --download`。

## 8. 验证方式

- 检查论文是否确实属于用户主题。
- 检查 venue 是否属于优先列表，或是否只是 arXiv 预印本。
- 检查链接是否可打开。
- 检查方法关键词是否来自标题/摘要，而不是凭空生成。
- 检查推荐精读的论文是否具备较高相关性和汇报价值。

## 9. Demo

### Demo 输入

```bash
python tools/search_papers.py "few-shot object detection" --max 10 --years 2024,2025,2026
```

### Demo 输出摘要

输出“小样本目标检测”方向论文候选，包含论文标题、年份、出处、链接、方法关键词和是否建议精读。用户可从中选择一篇，继续调用 `paper-to-ppt-pipeline`。

## 10. 局限性

- 搜索质量依赖英文关键词设计。
- arXiv 和 Semantic Scholar 可能限流。
- venue 自动识别可能不完整，需要人工复查。
- 本 skill 不负责最终 PPT 生成，PPT 生成应交给 `paper-to-ppt-pipeline`。

