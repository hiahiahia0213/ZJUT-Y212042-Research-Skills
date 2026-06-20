---
name: paper-to-ppt-pipeline
description: 总流程编排器：给定论文 arXiv ID，调度 paper-pdf-assets-pdftoppm（下载+渲染+裁剪）和 academic-paper-ppt-maker（公式+PPT生成）完成全流程。不包含具体实现，只做编排和质量把关。
---

# Paper-to-PPT Pipeline（编排器）

## 职责

**只做编排和质检，不包含具体实现。**

当用户说"帮我做这篇论文的 PPT"时，按照以下顺序调度两个子 skill：

```
用户指定 arXiv ID
    │
    ▼
┌─────────────────────────────────────────────┐
│  paper-pdf-assets-pdftoppm                  │
│  负责: 下载 PDF → 渲染页面 → 定位图表       │
│        → crop_plan.json → 裁剪图表          │
│  产出: paper_pages/ + paper_assets/         │
│        asset_manifest.md + crop_qc.md       │
└─────────────────────────────────────────────┘
    │ 质检: 图表完整、无截断、无混入正文
    ▼
┌─────────────────────────────────────────────┐
│  academic-paper-ppt-maker                   │
│  负责: 读 asset_manifest.md → 设计幻灯片     │
│        → 渲染 LaTeX 公式 → 生成 PPTX         │
│  产出: 论文名_组会汇报.pptx                  │
└─────────────────────────────────────────────┘
    │ 质检: 无重叠、比例正确、素材齐全
    ▼
  最终 PPT
```

## 执行流程

### Phase 1: 初始化

```bash
python tools/init_paper.py {论文名} --arxiv {arxiv_id}
```

在 `outputs/{论文名}/` 下创建标准目录结构。

### Phase 2: 调用 paper-pdf-assets-pdftoppm

将以下工作交给该 skill 完成：

| 步骤 | 对应 skill 章节 |
|------|----------------|
| 下载 PDF | paper-pdf-assets-pdftoppm 的 Step 1 |
| 渲染 300DPI 页面 | paper-pdf-assets-pdftoppm 的 Step 1 |
| 生成 contact sheet | paper-pdf-assets-pdftoppm 的 Step 2 |
| 页面元素定位 (x,y 坐标) | paper-pdf-assets-pdftoppm 的 Step 3-4 |
| 生成 crop_plan.json | paper-pdf-assets-pdftoppm 的 Step 5 |
| 裁剪图表 | paper-pdf-assets-pdftoppm 的 Step 6 |
| 质检 + 重裁 | paper-pdf-assets-pdftoppm 的 Step 7-8 |

### Phase 3: 质检关口（不可跳过 — 来自 Dark-ISP/PromptIR 实战教训）

必须逐项检查 paper-pdf-assets-pdftoppm 的产出：

- [ ] `asset_manifest.md` 存在
- [ ] `crop_qc.md` 存在且无未解决的 CHECK
- [ ] **每个裁剪资产已人工验证: 检查 y1 是否太高(截断图像顶部)、y2 是否太低(混入正文)、x 是否在正确列**
- [ ] 方法总览图存在且完整 (检查: 图像顶部未被切, 下半部分未被截)
- [ ] 主实验表存在且包含所有数据行 (检查: y2 是否在最后一行之后, 而非提前截断)
- [ ] 消融表存在（或确认论文无消融表）
- [ ] 可视化图存在且完整 (检查: 包含所有子图和标签行)

**任何一项不通过 → 回到 Phase 2, 用 page.get_text("blocks") 重新定位, 修改 crop_plan.json, 重新裁剪。**

### Phase 4: 调用 academic-paper-ppt-maker

将以下工作交给该 skill 完成：

| 步骤 | 对应 skill 章节 |
|------|----------------|
| 论文分析 (如有需要) | academic-paper-ppt-maker 的 Step 1 |
| 幻灯片设计 (逐页大纲) | academic-paper-ppt-maker 的 Step 2-4 |
| LaTeX 公式渲染 | academic-paper-ppt-maker 的 Formula Rendering Rules |
| PPTX 生成 | academic-paper-ppt-maker 的 Step 5-6 |
| 嵌入质检 (重叠/比例) | academic-paper-ppt-maker 的 Post-Generation QC |

### Phase 5: 最终质检（引用 academic-paper-ppt-maker 的 Final Delivery Checklist）

- [ ] PPTX 文件存在且大小 3-15 MB
- [ ] 0 个真实重叠（非包容关系）
- [ ] 所有嵌入图片路径有效
- [ ] **中文讲解 + Microsoft YaHei 字体 + >= 1 个关键公式以 LaTeX PNG 嵌入**
- [ ] **每页内容幻灯片都有 >= 3 行讲解文字，每张嵌入图表有来源标注**
- [ ] 每页有明确标题
- [ ] 封面包含论文标题 + 出处
- [ ] 符合 `academic-paper-ppt-maker` 中 PPT Content Standards 的全部 9 条规则

**如果任何内容页只有图没有文字 → 回到 Phase 4, 补文字后重新生成。**

## 目录结构（由 init_paper.py 创建）

```
outputs/{论文名}/
├── README.md                 # 进度追踪
├── {论文名}.pdf              # [paper-pdf-assets] 下载
├── paper_pages/              # [paper-pdf-assets] 渲染
│   ├── page001~NNN.png
│   └── contact_sheet.png
├── paper_assets/             # [paper-pdf-assets] 裁剪
│   ├── page_analysis.json
│   ├── crop_plan.json
│   ├── asset_manifest.md
│   ├── crop_qc.md
│   ├── crop_previews/
│   ├── fig*.png
│   ├── table*.png
│   └── f_*.png              # [academic-ppt-maker] 公式
└── {论文名}_组会汇报.pptx    # [academic-ppt-maker] 最终产出
```

## 调度规则

| 规则 | 说明 |
|------|------|
| 不越权 | pipeline 不自己写 crop 坐标、不自己调 pptxgenjs |
| 先质检再传递 | Phase 2 产出必须经过 Phase 3 质检才能进入 Phase 4 |
| 失败即停 | 任何一步质检不通过，修复后重新执行该步骤 |
| 技能引用 | 通过 skill 名称调用: `paper-pdf-assets-pdftoppm` → `academic-paper-ppt-maker` |

## 快速备忘

```bash
# 全程由 pipeline 编排:
arxiv_id="2603.28182"
paper_name="FSOD-CrossDomain"

# Step 1: 初始化
python tools/init_paper.py $paper_name --arxiv $arxiv_id

# Step 2-3: 调用 paper-pdf-assets-pdftoppm
#   (下载 PDF, 渲染页面, 定位图表, 裁剪, 质检)

# Step 4: 调用 academic-paper-ppt-maker  
#   (渲染公式, 生成 PPTX, 嵌入质检)

# 每个 phase 完成后检查对应目录下的产出文件
```
