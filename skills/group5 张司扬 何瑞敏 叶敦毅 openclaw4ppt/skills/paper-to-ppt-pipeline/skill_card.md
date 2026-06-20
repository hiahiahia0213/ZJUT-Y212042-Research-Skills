# Skill Card: Paper-to-PPT Pipeline

## 1. Skill 基本信息

| 项目 | 内容 |
|---|---|
| Skill 名称 | paper-to-ppt-pipeline |
| 中文名称 | 论文检索与论文讲解 PPT 自动生成编排器 |
| 所属科研场景 | 文献调研、论文精读、组会汇报、课程论文展示 |
| 目标用户 | 需要快速完成论文检索、论文分析和中文组会 PPT 的研究生或科研初学者 |
| 主入口文件 | `SKILL.md` |
| 依赖子 skill | `paper-search` / `paper-search-download`、`paper-pdf-assets-pdftoppm`、`academic-paper-ppt-maker` |
| 配套工具脚本 | `tools/search_papers.py`、`tools/init_paper.py`、`tools/render_pdf_pages.sh`、`tools/make_contact_sheet.py`、`tools/crop_pdf_assets.py` |

## 2. 一句话简介

`paper-to-ppt-pipeline` 是一个面向科研论文汇报的 OpenClaw Research Skill：用户给定研究主题、论文标题、arXiv ID 或 PDF 后，它按固定流程组织论文检索、PDF 下载、论文分析、原论文图表裁剪、关键公式重渲染和中文 PPT 制作，并在每个阶段设置质量检查。

## 3. 解决的科研问题

研究生在准备组会或课程论文汇报时，经常要完成一串重复但容易出错的工作：

- 从某个研究主题中筛选值得精读的论文。
- 下载论文 PDF 并阅读方法、实验、公式和结论。
- 从双栏论文 PDF 中裁剪方法图、实验表格、消融表和可视化结果。
- 将关键公式重新写成适合 PPT 展示的形式。
- 设计 10-20 页中文汇报 PPT，既要逻辑清晰，也要能直接讲。
- 检查 PPT 中是否存在图片变形、图表截断、文字重叠、纯图无讲解、字体不统一等问题。

本 skill 将这些高频任务标准化为可复用流程，使一次论文汇报准备不再依赖临时问答和人工经验。

## 4. 输入与输出

### 输入

| 输入类型 | 示例 | 是否必需 |
|---|---|---|
| 研究主题 | `小样本目标检测`、`恶劣天气目标检测` | 主题检索时必需 |
| 论文标题 | `PromptIR: Prompting for All-in-One Blind Image Restoration` | 指定论文时可用 |
| arXiv ID | `2306.13090` | 自动下载 PDF 时推荐 |
| PDF 文件 | `papers/paper.pdf` | 网络不可用或非 arXiv 论文时可用 |
| PPT 要求 | 15 分钟、中文、包含方法图/实验表/公式 | 推荐提供 |

### 输出

| 输出 | 说明 |
|---|---|
| 论文检索列表 | 标题、年份、出处、链接、方法关键词、是否建议精读 |
| 独立论文目录 | `outputs/{论文名}/` |
| 论文 PDF | `{论文名}.pdf` |
| 页面渲染图 | `paper_pages/page001~NNN.png`、`contact_sheet.png` |
| 图表裁剪素材 | `paper_assets/fig*.png`、`table*.png` |
| 裁剪检查文件 | `crop_plan.json`、`asset_manifest.md`、`crop_qc.md`、`crop_previews/` |
| 公式图片 | `paper_assets/f_*.png`，由 LaTeX 渲染为透明 PNG |
| 最终 PPT | `{论文名}_组会汇报.pptx` |

## 5. 工作流程

1. 识别用户任务：判断用户是在找论文，还是已经指定论文要生成 PPT。
2. 论文检索：调用 `paper-search` 或 `paper-search-download`，优先筛选 CVPR、ICCV、AAAI、NeurIPS、ICML、TPAMI、IJCV、TIP 等论文。
3. 初始化目录：调用 `tools/init_paper.py` 创建 `outputs/{论文名}/`。
4. PDF 获取：根据 arXiv ID 自动下载，或使用用户提供的 PDF。
5. 图表资产处理：调用 `paper-pdf-assets-pdftoppm` 完成页面渲染、图表定位、裁剪和 crop QC。
6. 论文内容组织：调用 `academic-paper-ppt-maker` 完成论文分析、逐页大纲、关键公式选择和 LaTeX 公式渲染。
7. PPT 生成：生成中文、微软雅黑、带来源标注、包含讲解文字的组会 PPT。
8. 最终质检：检查图片比例、文字重叠、公式数量、图表来源、每页讲解文字、PPT 页数和文件大小。
9. 失败回退：任一质检项不通过，回到对应阶段重新裁剪、重排或重生成。

## 6. 与普通 ChatGPT 问答的区别

| 对比项 | 普通 ChatGPT 问答 | 本 Skill |
|---|---|---|
| 任务目标 | 临时回答论文相关问题 | 固化论文检索到 PPT 生成的完整科研流程 |
| 输入材料 | 用户随意描述 | 明确要求主题、论文标题、arXiv ID 或 PDF |
| 中间产物 | 通常没有 | PDF、页面图、裁剪图、公式 PNG、QC 文件、PPT |
| 流程稳定性 | 每次回答可能不同 | 按 Phase 1-5 固定执行 |
| 可验证性 | 多依赖文本可信度 | 图表可追溯到 PDF，裁剪有 preview 和 QC |
| 失败处理 | 容易跳过问题直接输出 | 质检失败必须回退修复 |
| 可复用性 | 依赖用户每次重新描述要求 | 规则写入 SKILL.md，可被其他同学复用 |

## 7. 质量检查机制

### 图表裁剪检查

- 必须使用 300DPI full-resolution 页面图。
- 不能只看 contact sheet 来写裁剪坐标。
- 双栏论文必须判断目标图表属于左栏、右栏还是跨栏。
- Figure 不得混入 Abstract、正文段落或相邻栏内容。
- Table 必须包含表头、所有数据行和底部边界。
- 生成 `asset_manifest.md` 和 `crop_qc.md` 后必须人工查看 preview。

### PPT 生成检查

- PPT 内容必须用中文讲解，关键术语可保留英文。
- 全文默认字体为 Microsoft YaHei / 微软雅黑。
- 每页内容幻灯片必须有实质讲解文字，不能只有图。
- 每张原论文图表必须标注来源，如 `来源：原论文 Fig. 2`。
- 至少包含一个关键公式，公式必须由 LaTeX 渲染为透明 PNG。
- 图片嵌入时必须保持原始长宽比。
- 保存前检查真实重叠、页面留白、图片路径和文件大小。

## 8. Demo

### Demo 1: PromptIR

| 项目 | 内容 |
|---|---|
| 输入 | arXiv: `2306.13090` |
| 论文 | PromptIR: Prompting for All-in-One Blind Image Restoration |
| 主要输出 | `outputs/PromptIR/PromptIR.pdf`、`paper_pages/page001~page018.png`、`paper_assets/*.png`、`PromptIR_v5.pptx` |
| 验证重点 | PDF 下载、18 页页面渲染、方法图/实验表/可视化图裁剪、公式加入、中文讲解 PPT |

### Demo 2: Dark-ISP

| 项目 | 内容 |
|---|---|
| 输入 | Dark-ISP: Enhancing RAW Image Processing for Low-Light Object Detection |
| 主要输出 | `outputs/Dark-ISP/paper_assets/asset_manifest.md`、`crop_qc.md`、`slides/Dark-ISP_v5_组会汇报.pptx` |
| 验证重点 | 双栏论文精确裁剪、主实验表、消融表、可视化结果、LaTeX 公式、图片比例与重叠检查 |

## 9. 典型使用方式

### 查找某方向论文

```bash
python tools/search_papers.py "few-shot object detection" --max 10 --years 2024,2025,2026
```

### 初始化单篇论文项目

```bash
python tools/init_paper.py PromptIR --arxiv 2306.13090
```

### 后续执行

按照 `paper-to-ppt-pipeline/SKILL.md`：

1. 调用 `paper-pdf-assets-pdftoppm` 完成 PDF 渲染和图表裁剪。
2. 通过 Phase 3 质检后，调用 `academic-paper-ppt-maker` 生成 PPT。
3. 通过 Phase 5 最终质检后交付 PPTX。

## 10. 适用范围

适合：

- 计算机视觉、机器学习、图像处理、目标检测、图像恢复等论文汇报。
- 需要保留原论文图表证据的组会 PPT。
- 需要快速构建论文精读材料和汇报材料的课程项目。

不适合：

- 没有 PDF、没有 arXiv ID 且无法联网的论文。
- 扫描质量很差、图表无法辨认的 PDF。
- 需要完全自动审稿判断或实验复现的任务。
- 只需要一句话论文摘要的轻量问答场景。

## 11. 局限性

- arXiv 和 Semantic Scholar 可能出现限流、SSL 超时或下载失败。
- venue 信息依赖外部数据库，可能需要人工确认。
- 图表裁剪仍需要人工查看 preview，不能完全依赖自动 QC。
- 对跨页表格、复杂多栏版式、扫描版 PDF 的支持仍有限。
- 公式选择和论文贡献解释仍需要模型理解与人工抽查。

## 12. 后续改进方向

- 增加网络失败后的镜像源、缓存和重试策略。
- 增加自动截图检查 PPT 页面是否存在重叠和空白过多。
- 增加 PDF 结构解析，自动识别 Figure/Table/Equation 编号。
- 将 PromptIR、Dark-ISP 等 demo 整理成更小的 examples/input 和 examples/output。
- 增加测试脚本，检查输出目录是否包含 PDF、页面图、图表素材、公式 PNG 和 PPTX。

