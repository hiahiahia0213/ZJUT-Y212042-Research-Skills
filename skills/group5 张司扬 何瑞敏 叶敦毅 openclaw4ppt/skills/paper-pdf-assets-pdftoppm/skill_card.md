# Skill Card: Paper PDF Assets

## 1. Skill 基本信息

| 项目 | 内容 |
|---|---|
| Skill 名称 | paper-pdf-assets-pdftoppm |
| 中文名称 | 论文 PDF 图表素材提取 skill |
| 所属科研场景 | 论文精读、组会 PPT 素材准备、原论文证据整理 |
| 主入口文件 | `SKILL.md` |
| 配套工具 | `tools/render_pdf_pages.sh`、`tools/make_contact_sheet.py`、`tools/crop_pdf_assets.py` |
| 上游输入 | 论文 PDF |
| 下游衔接 | `academic-paper-ppt-maker`、`paper-to-ppt-pipeline` |

## 2. 一句话简介

`paper-pdf-assets-pdftoppm` 用于从研究论文 PDF 中提取适合 PPT 使用的原论文图表素材，包括方法图、网络结构图、主实验表、消融表、算法图和可视化结果，并生成可复查的裁剪计划和质量检查文件。

## 3. 解决的科研问题

制作论文汇报 PPT 时，最容易出问题的环节之一是从 PDF 中截图。人工截图常见问题包括：

- 图表没有裁完整。
- 把 Abstract、正文段落、相邻栏内容一起截进去。
- 双栏论文左右栏判断错误。
- 表格缺少最后一行或底部边界。
- 图表留白过多，放进 PPT 后不清晰。
- 没有记录裁剪坐标，后续无法复查或重现。

本 skill 将 PDF 图表提取拆成渲染、定位、裁剪、预览、QC 和重裁的标准流程，确保素材能作为 PPT 的可靠证据来源。

## 4. 输入与输出

### 输入

| 输入 | 示例 | 说明 |
|---|---|---|
| PDF 路径 | `outputs/PromptIR/PromptIR.pdf` | 必需 |
| 输出页面目录 | `outputs/PromptIR/paper_pages/` | 存放 300DPI 页面图 |
| 输出素材目录 | `outputs/PromptIR/paper_assets/` | 存放裁剪图表和 QC |
| DPI | `300` | 默认 300，不低于 200 |

### 输出

| 输出 | 说明 |
|---|---|
| 页面 PNG | `paper_pages/page001~NNN.png` |
| contact sheet | `paper_pages/contact_sheet.png` |
| 页面元素分析 | `paper_assets/page_analysis.json` |
| 裁剪计划 | `paper_assets/crop_plan.json` |
| 裁剪图表 | `paper_assets/fig*.png`、`table*.png` |
| 素材清单 | `paper_assets/asset_manifest.md` |
| 质量检查报告 | `paper_assets/crop_qc.md` |
| 裁剪预览 | `paper_assets/crop_previews/` |

## 5. 工作流程

1. 使用 `pdftoppm` 将 PDF 渲染为 300DPI 页面图。
2. 使用 `make_contact_sheet.py` 生成页面总览。
3. 阅读论文文本和页面图，定位 Figure、Table、Algorithm、Ablation、Visualization。
4. 对每个候选图表打开 full-resolution 页面图，不能只看 contact sheet。
5. 使用 PDF 文本块和图片坐标判断图表边界。
6. 为每个图表写入 `crop_plan.json`。
7. 使用 `crop_pdf_assets.py` 裁剪图表并生成 preview。
8. 检查 `crop_qc.md` 和 preview。
9. 如果有截断、正文混入、跨栏或留白过多，修改 `crop_plan.json` 后重新裁剪。

## 6. 核心质量规则

| 检查项 | 合格标准 |
|---|---|
| 方法图 | 图形主体完整，必要标签可读，不混入正文 |
| 主实验表 | 表头、所有方法行、关键指标和底部边界完整 |
| 消融表 | 所有组件行完整，不缺最后一行 |
| 可视化结果 | 所有子图、标签、方法名完整 |
| 双栏论文 | 单栏图表不能跨栏，跨栏图表需确认横向范围 |
| 裁剪结果 | 清晰、无明显截断、无无关正文、无过度留白 |

## 7. 与普通截图的区别

| 对比项 | 普通截图 | 本 Skill |
|---|---|---|
| 分辨率 | 依赖屏幕显示 | 使用 300DPI 页面渲染 |
| 坐标记录 | 无 | `crop_plan.json` 可复查 |
| 质量检查 | 人眼临时看一下 | `asset_manifest.md`、`crop_qc.md`、preview |
| 双栏处理 | 容易跨栏 | 强制判断 x/y 坐标和列归属 |
| 失败处理 | 截坏了重新手动试 | 修改 crop plan 后可重复裁剪 |

## 8. Demo

### PromptIR

从 `outputs/PromptIR/PromptIR.pdf` 渲染 18 页页面图，裁剪方法图、架构图、去雾/去雨/去噪可视化结果和多张实验表格。

### Dark-ISP

从 Dark-ISP 论文中裁剪方法总览图、主实验表、消融表、可视化结果，并生成 `asset_manifest.md` 和 `crop_qc.md`。该 demo 暴露并修复了双栏裁剪混入正文、图表截断、表格不完整等问题。

## 9. 验证方式

- 打开每张裁剪图检查是否完整。
- 打开 preview 检查红框是否覆盖正确区域。
- 查看 `crop_qc.md` 中是否存在未解决的 CHECK。
- 对照原 PDF 页确认图表编号和来源。
- 检查是否至少包含方法图、主实验表、消融表或明确说明论文没有对应图表。

## 10. 局限性

- 扫描版 PDF 或图表质量过低时无法保证清晰裁剪。
- 跨页表格、旋转表格、复杂多栏布局需要更多人工调整。
- 自动 QC 可能对大面积白底表格误报，需要人工复查。
- 本 skill 只负责图表素材，不负责最终 PPT 设计。

