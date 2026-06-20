---
name: academic-paper-ppt-maker
description: Use when Codex needs to create Chinese academic paper presentation slides, journal club PPTX files, or research talk decks from a paper PDF, paper notes, analysis, or extracted paper assets.
---

# Academic Paper PPT Maker

## Role

Act as a Chinese academic paper presentation designer. Build a PPT for classroom reports, group meetings, and paper reading talks. Prefer original paper figures and tables over text-only summaries.

## Mandatory Asset Rule

If the user provides a paper PDF or asks for original paper figures/tables in the PPT, do not create a PPTX directly.

Complete this pipeline first:

1. Use the `paper-pdf-assets-pdftoppm` workflow
2. Render the PDF to high-resolution page images with `pdftoppm`
3. Crop Figure/Table assets
4. Create `outputs/paper_assets/asset_manifest.md`
5. Create and inspect `outputs/paper_assets/crop_qc.md`
6. Inspect crop previews under `outputs/paper_assets/crop_previews/`
7. Design the PPT from `asset_manifest.md`
8. Then generate the final PPTX

If `outputs/paper_assets/asset_manifest.md` does not exist, do not generate PPTX.

If `crop_qc.md` is missing, or if any required asset is visibly truncated or includes unrelated body text, return to `paper-pdf-assets-pdftoppm` and recrop before generating PPTX.

## Required PPT Content

Include when available:

- 原论文方法总览图
- 原论文核心模块图
- **原论文关键公式 (LaTeX 渲染为透明 PNG)** ← 必做, 不可跳过
- 主实验对比表
- 消融实验表
- 可视化结果图
- 数据集或实验设置页
- 优点、局限与讨论页

**公式规则: 每篇论文 PPT 必须包含 >=1 个关键公式**

If the paper lacks a category, explicitly state: “论文中未提供对应图表，因此本页使用文字总结或重绘示意图。”

## PPT Structure

For a 15-minute group meeting, create 12-16 slides by default:

1. 封面
2. 研究背景
3. 问题定义与挑战
4. 相关工作与现有不足
5. 论文动机与贡献
6. 方法整体框架
7. 核心模块一
8. 核心模块二 / 训练策略
9. 损失函数或关键公式
10. 数据集与实验设置
11. 主实验结果
12. 消融实验
13. 可视化结果
14. 优点、局限与讨论
15. 总结与 Q&A

Adjust within 10-20 slides if the user requests a different length.

## Page Planning

Before generating PPTX, prepare a page plan with:

| 页码 | 标题 | 本页目的 | 核心内容 | 使用素材 | 版式建议 | 讲稿提示 |
|---|---|---|---|---|---|---|

Rules:

- Use at most three core points per slide
- Method slides must be figure-led
- Experiment slides must be table/figure-led
- Give ablation experiments their own slide when available
- Explain what the results demonstrate; do not only say the method is better
- If a table is too wide, crop key columns or rebuild a concise table
- Cite original paper assets, for example: `Source: Fig. 2 from paper`

## Asset Usage Rule

Before generating PPTX, read:

```text
outputs/paper_assets/asset_manifest.md
```

Use images primarily from:

```text
outputs/paper_assets/
```

Do not use unrelated web images.

## Failure Check Before PPTX

Before generating PPTX, verify:

- `outputs/paper_assets/asset_manifest.md` exists
- `outputs/paper_assets/crop_qc.md` exists
- Crop preview images exist under `outputs/paper_assets/crop_previews/`
- A method/framework asset exists
- A main results table exists
- An ablation table exists, or the paper has no ablation table and this is documented
- Each experiment slide is bound to a concrete asset
- Every image path exists
- No required asset is marked unresolved in `crop_qc.md`
- No required asset contains unrelated Abstract,正文段落, section headers, or neighboring-column text
- No required table is missing its last row or bottom rule

If any check fails, return to the asset extraction workflow instead of generating PPTX.

## PPT Content Standards (NON-NEGOTIABLE)

### Language & Font

- **PPT content MUST be in Chinese** (key technical terms like YOLO, DETR, PSNR, Transformer may remain in English)
- **Font MUST be Microsoft YaHei** (微软雅黑) for all text
- Section slides may use fewer words; content slides must have substantive Chinese explanations

### Per-Slide-Type Requirements

| Slide Type | Must Include | Don't |
|---|---|---|
| Cover | Full paper title, venue+year, arXiv ID, authors, presenter date | Don't omit venue (e.g., "CVPR 2026") |
| Outline | 4-5 sections with 1-line descriptions | Don't make it a bullet list of just numbers |
| Background/Challenge | 2-3 specific problems with context | Don't say "it's important" without saying WHY |
| Method Overview | Original paper figure + >= 4 bullet points explaining the pipeline | Don't just put the figure and say "here's the method" |
| Core Module | Each module: 1) what it does 2) input/output 3) key innovation | Don't just label boxes in the figure |
| Experiment Setup | Dataset names, metrics, baseline methods | Don't skip metric definitions |
| Main Results | Table/figure + >= 4 bullet points with specific numbers | Don't say "our method is best" without numbers |
| Ablation | Table + analysis of what each component contributes | Don't just show the table without interpretation |
| Visualization | Images + observation text explaining what to look for | Don't let images float alone without commentary |
| Summary | Contributions + limitations + insights for audience's research | Don't just list contributions without reflection |

### Source Citations

Every embedded original-paper figure/table must have a source line:

```
来源: 原论文 Fig.X / Table X
```

For redrawn diagrams:
```
根据论文方法重绘
```

### Final Delivery Checklist

Before declaring the PPT complete, verify ALL of the following:

- [ ] 12-16 slides total
- [ ] All content slides have Chinese text explanations
- [ ] All fonts are Microsoft YaHei
- [ ] All embedded figures/tables have source citations
- [ ] **>= 1 key formula rendered as LaTeX transparent PNG** ← Mandatory
- [ ] No bare images without accompanying text
- [ ] All image aspect ratios preserved
- [ ] No overlapping elements
- [ ] File size 3-15 MB
- [ ] Cover has: title + venue + arXiv ID + authors

- White or light gray background
- Deep blue, gray-black, or dark green as primary colors
- Sparse orange or blue emphasis
- Figure-heavy method pages
- Readable experiment tables
- Clear slide titles
- No flashy animation
- No marketing-style illustration
- No dense paragraphs

## Image Embedding Rules (Critical)

### Aspect Ratio

**NEVER stretch or squash images.** Always compute the display dimensions from the original PNG dimensions:

```javascript
function placeImageFit(slide, filePath, x, y, maxW, maxH) {
  const dims = getPngDimensions(filePath);  // Read IHDR from PNG header
  const imgRatio = dims.w / dims.h;
  const boxRatio = maxW / maxH;
  let displayW, displayH;
  if (imgRatio > boxRatio) {
    displayW = maxW; displayH = maxW / imgRatio;
  } else {
    displayH = maxH; displayW = maxH * imgRatio;
  }
  // Center within available space
  slide.addImage({ path: filePath, x: x+(maxW-displayW)/2, y: y+(maxH-displayH)/2, w: displayW, h: displayH });
}
```

Avoid using `sizing: { type: "contain" }` alone — it may leave unexpected whitespace.

### Overlap Prevention

Track every element's position and check for overlaps before saving:

```javascript
function checkOverlaps(a, b) {
  return a.x < b.x+b.w && a.x+a.w > b.x && a.y < b.y+b.h && a.y+a.h > b.y;
}
```

Common overlap failures:
- Image too large, covering adjacent text box
- Two images placed with overlapping bounding boxes
- Footer text overlapping with large bottom images

### Position Rules

| Rule | Detail |
|---|---|
| Minimum margin from slide edge | 0.3" for images, 0.4" for text |
| Image spacing between elements | At least 0.15" gap |
| Title-to-image gap | At least 0.15" below title underline |
| Full-bleed images | Use 0.1" margins; never go to slide edge (0") |

### Post-Generation Quality Check

After generating the PPTX, verify:
- All image paths resolve to existing files
- No overlap warnings fired (or all flagged overlaps are intentional)
- File size is reasonable (3-15 MB for image-rich PPT)
- Every slide has a distinct title

### Common PPT Failures

| Symptom | Cause | Fix |
|---|---|---|
| Image looks stretched | w/h ratio doesn't match original dims | Compute display size from PNG dimensions |
| Text hidden behind image | Image overlaps text box | Add overlap detection; adjust positions |
| Large whitespace around image | `contain` sizing with mismatched aspect ratio | Compute exact display dimensions |
| Image cut at slide edge | x+w > slide width or y+h > slide height | Add boundary guards |
| PPT file corrupted | Missing image file or invalid path | Pre-verify all image paths exist |
| Formula text looks sloppy | Plain text used instead of LaTeX | Render as transparent PNG, embed as image |
| Formula too large/small | Wrong DPI-to-inches conversion | px / renderDPI = inches (e.g., px / 300 for 300DPI) |
| Formula overlaps text | Formula image placed without position check | Track all element positions; run overlap detection |

## Formula Rendering Rules (Critical)

**NEVER use plain monospace text to simulate math formulas.**

### Rendering Pipeline

1. Write all formulas in LaTeX
2. Render to transparent PNG at 300+ DPI using matplotlib:

```python
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

plt.rcParams.update({"mathtext.fontset": "stix"})  # or "cm" if available
DPI = 300

for fname, latex, fontsize, color in formulas:
    fig, ax = plt.subplots(figsize=(len(latex)*0.05, 0.6), dpi=DPI)
    ax.axis("off"); fig.patch.set_alpha(0)
    ax.text(0.5, 0.5, f"${latex}$", transform=ax.transAxes,
            fontsize=fontsize, color=color, ha="center", va="center")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, transparent=True,
                bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    # Trim excess transparent borders
    img = Image.open(buf); bbox = img.convert("RGBA").getbbox()
    if bbox: img = img.crop(bbox)
    img.save(f"{fname}.png")
```

3. Embed in PPT at correct size:

```javascript
// Formula PNG is at 300 DPI: pixels / 300 = inches
function fImg(slide, filename, x, y) {
  const dims = getPngDims(filename);
  const iw = dims.w / 300;  // inches wide
  const ih = dims.h / 300;  // inches tall
  placeImageFit(slide, filename, x, y, iw + 0.1, ih + 0.1);
}
```

### Key Insight

**The conversion from pixels to inches depends on the render DPI.**

- Rendered at 200 DPI → `px / 200 = inches`
- Rendered at 300 DPI → `px / 300 = inches`
- Using the wrong divisor (e.g., `/ 72`) makes formulas 2.8-4.2x too large → overlap disaster
