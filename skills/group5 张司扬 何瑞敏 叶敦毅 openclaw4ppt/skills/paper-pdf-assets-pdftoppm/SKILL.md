---
name: paper-pdf-assets-pdftoppm
description: Use when Codex needs to extract paper figures, tables, algorithms, ablations, qualitative visualizations, or PPT-ready assets from a research PDF before creating academic slides.
---

# Paper PDF Assets

## Role

Act as an academic PDF asset extraction assistant. Extract original paper assets for PPT use instead of summarizing the paper.

Target assets include:

- 方法总览图、网络结构图、核心模块图、算法流程图
- 主实验对比表、消融实验表、效率对比表
- 可视化结果图、数据集说明图表

## Inputs

Use the user-provided PDF path. If no path is given, look for PDF files under `papers/` and choose the most relevant one.

Use these output directories:

- `outputs/paper_pages/`
- `outputs/paper_assets/`

Use these local tools:

- `tools/render_pdf_pages.sh`
- `tools/make_contact_sheet.py`
- `tools/crop_pdf_assets.py`

## Mandatory Prompt For Asset Extraction

When extracting paper assets, follow this prompt as the operating contract:

```text
请使用 paper-pdf-assets-pdftoppm 工作流抽取图表，但不要只生成一次 crop_plan。

要求：
1. 先渲染 PDF 页面并生成 contact_sheet。
2. 对每个 Figure/Table，必须打开对应 full-resolution page 图，而不是只看 contact_sheet。
3. 双栏论文必须先判断目标在左栏还是右栏，裁剪框不能跨栏。
4. 表格裁剪规则：从 caption 或表格顶线开始，到最后一条表格底线后 10~30px 结束，禁止包含后续正文。
5. Figure 裁剪规则：只裁图形主体和必要标签，禁止包含 Abstract、正文段落或相邻栏内容。
6. 生成 crop_plan.json 后，运行裁剪脚本。
7. 逐张检查裁剪结果；如果有截断、正文混入、跨栏、留白过多，必须修改 crop_plan.json 后重新裁剪。
8. 最终输出 asset_manifest.md、crop_qc.md 和 crop_previews/。
```

## Workflow

1. Render pages at 300 DPI:

```bash
bash tools/render_pdf_pages.sh <PDF_PATH> outputs/paper_pages 300
```

Use 300 DPI by default. If page images are too large, reduce to 220 DPI; do not go below 200 DPI.

2. Create a contact sheet:

```bash
python tools/make_contact_sheet.py \
  --pages_dir outputs/paper_pages \
  --out outputs/paper_pages/contact_sheet.png
```

3. Locate important figures and tables by reading PDF text and page images. Search for:

`Fig.`, `Figure`, `Table`, `Algorithm`, `Overview`, `Framework`, `Architecture`, `Module`, `Ablation`, `Comparison`, `Qualitative`, `Visualization`, `Main Results`.

Produce a figure/table list:

| 类型 | 编号 | 页码 | 内容 | PPT用途 | 优先级 |
|---|---|---:|---|---|---|

Priority meanings:

- A: must include in PPT
- B: recommended
- C: optional

4. Create `outputs/paper_assets/crop_plan.json` with normalized coordinates:

```json
{
  "paper_title": "论文标题",
  "items": [
    {
      "type": "Figure",
      "source": "Fig. 1",
      "page": 2,
      "filename": "fig1_overview.png",
      "description": "方法整体框架图",
      "suggested_slide": 6,
      "box": [0.08, 0.18, 0.92, 0.58]
    }
  ]
}
```

Coordinate rules:

- `box = [x1, y1, x2, y2]`
- All values are normalized from 0 to 1
- Top-left is `[0, 0]`; bottom-right is `[1, 1]`
- Do not cut off captions, axes, legends, table headers, or table borders
- For result tables, preserve headers and key metrics

5. Crop assets:

```bash
python tools/crop_pdf_assets.py \
  --plan outputs/paper_assets/crop_plan.json \
  --pages_dir outputs/paper_pages \
  --assets_dir outputs/paper_assets \
  --padding 20 \
  --enhance \
  --auto-trim \
  --qc \
  --preview
```

This must create cropped PNG files, `outputs/paper_assets/asset_manifest.md`, `outputs/paper_assets/crop_qc.md`, and preview images under `outputs/paper_assets/crop_previews/`.

The crop tool accepts both plan schemas:

- Preferred: `items[].box`
- Compatible: `assets[].box_norm` or `assets[].box_px`

It also accepts page image names like `page-1.png`, `page-001.png`, and `page001.png`.

## Cropping Rules

Use full-resolution page images for coordinates. The contact sheet is only for navigation.

### Mandatory Precision Check (NON-NEGOTIABLE)

**After writing crop coordinates, you MUST verify each crop by:**

1. Scan the page with `page.get_text("blocks")` to get ALL text block positions (x0,y0,x1,y1,text)
2. Scan the page with `page.get_images(full=True)` to get ALL embedded image rects
3. For each figure/table: identify the EXACT y-range of:
   - The figure's containing images (their rects)
   - The caption's text block position
   - The previous/next text blocks (to avoid including them)
4. Crop box rules:
   - **y1** = min(images' y0, first element's y0) - 15px (NOT the page margin!)
   - **y2** = caption's y1 + 15px (for figures) OR last data row's y1 + 15px (for tables)
   - **x1/x2** = column boundaries (L/R/F), checked against each element's x-coordinate

### Common Crop Failures = QC Checklist

| Check | Pass Condition | Common Failure (Dark-ISP/PromptIR lessons) |
|---|---|---|
| y1 too high | Figure's top edge is visible | Fig.5 deraining: y1 was 900 but image starts at y=299 |
| y2 too low | Includes body text below figure/table | Table 1: y2 was 1050 but data ends at y=862 |
| y2 cuts table rows | Last data row visible | Table 4: y2 must include all rows through y=1587 |
| x-range wrong column | No neighboring-column text | Fig.1: x=60-2490 included left-col Abstract |
| Includes body text | Next text block after y2 is a heading or next caption | "Implementation Details" at y=1900 should not be in Table 1 crop |

### Two-column papers:

- Identify column before writing x-coordinates (L: x1~243-1228, R: x1~1321-2306 at 300DPI)
- Never let crop cross into neighbor column unless figure spans both
- Right-column assets: x1 near column boundary, not page margin

For tables:
- Crop from caption top or table top rule
- End at last table bottom rule + small whitespace (10-20px)
- Do NOT include the paragraph after the table, section headers, or the next table
- Verify: the text block at y=y2+30 should NOT be table data

## Quality Check

After cropping, inspect every PNG, every preview image, and `crop_qc.md`. Verify:

- At least one method overview/framework asset exists
- At least one main result table exists
- At least one ablation table exists, or state that the paper has no ablation table
- At least one qualitative/visualization result exists, or state that the paper has none
- Images are clear and tables are readable
- No crop is truncated, too narrow, or dominated by unnecessary whitespace
- No crop includes unrelated Abstract,正文段落, section headers, or neighboring-column content
- Every row marked `CHECK` in `crop_qc.md` has been manually inspected

If an asset fails quality checks, update `crop_plan.json` and crop again.

Never proceed to PPT generation after a single unreviewed crop pass.

## Common Crop Failures

| Symptom | Likely Cause | Fix |
|---|---|---|
| Table includes paragraphs below it | `y2` too low | Move `y2` to the table bottom rule plus small whitespace |
| Table bottom rows are missing | `y2` too high | Increase `y2` until the last row and bottom rule are visible |
| Figure includes Abstract or left-column text | Crop crosses columns | Move `x1`/`x2` to the correct column boundary |
| Asset contains too much blank margin | Box too loose | Tighten coordinates or use `--auto-trim` |
| Preview red box covers the wrong region | Page number or column selection is wrong | Re-open full page image and rewrite the item |

## Naming

Use clear filenames such as:

- `fig1_overview.png`
- `fig2_framework.png`
- `fig3_module.png`
- `table1_main_results.png`
- `table2_ablation.png`
- `table3_efficiency.png`
- `visual_qualitative_results.png`
- `dataset_examples.png`

## Final Response

Report:

1. PDF page rendering result
2. Figure/table list
3. `crop_plan.json` path
4. Cropped image list
5. `asset_manifest.md` path
6. Recommended PPT slide for each asset
7. Any important figures/tables that could not be extracted

## Practical Lessons (from Dark-ISP extraction)

These are hard-won lessons from real extraction iterations.

### The Golden Rule: Check BOTH X and Y

**Never write a crop box from y-coordinates alone.** You MUST check x-coordinates to determine column ownership:

```python
# For each text block, check column:
col = "L" if x1 < 1250 else ("R" if x0 > 1250 else "F")
# Standard two-column: L=243-1228px, R=1321-2306px (at 300DPI on 8.5x11in)
```

### Five Failure Modes and Their Fixes

| Symptom | Root Cause | Fix |
|---|---|---|
| Figure includes Abstract/body text | x-range is full-width but figure is in one column | Narrow x to the figure's column only |
| Figure top/bottom cut off | y1/y2 determined from caption, not from first/last element | Find min y of all image rects and text labels in figure |
| Table includes body paragraphs below | y2 extends past last data row into next section | Set y2 = last data text block y1 + 15-30px |
| Table last rows missing | y2 stops before the last data block | Check all text blocks between caption and next caption/section |
| Auto-trim clips table content | --auto-trim removes thin table borders or edges | Skip --auto-trim for tables; use only --padding |

### Coordinate Discovery

**Use PyMuPDF's get_text('blocks') and get_images(full=True) to get EXACT element positions BEFORE writing any crop box.** Save the full analysis to `page_analysis.json` for reference.

### Two-Column Paper Rules

| Rule | Detail |
|---|---|
| Determine columns first | Left: x=243-1228, Right: x=1321-2306 (Standard IEEE/ICCV 2-col) |
| Never let crop cross columns | Left col x1~0.1 x2~0.48; Right col x1~0.52 x2~0.95 |
| Full-width only for figs that span both columns | Check that image elements/min-text-labels span both columns |
| Right-column assets use x1=0.51 | Not x1=0.02 (which includes left-column text) |

### Table Cropping Precision

- **Top boundary**: table caption's text block y0 minus 15px
- **Bottom boundary**: last data row's block y1 + 15px
- **Verification**: the next text block below y2 must be a different table caption or section header
- If AUTO-TRIM produces a CHECK result for tables, disable it and re-crop

### Figure Cropping Precision

- Find ALL text blocks and image rects within the figure area
- y1 = min(all figure element y0) - 15px
- y2 = max(all figure element y1) + 15px (or caption y1 + 15px if caption is included)
- For grid visualizations (e.g., 7-col thumbnails), x1/x2 from min/max image rect x

### Anti-Patterns

| Don't | Do instead |
|---|---|
| Crop full-width for single-column figure | Check x-coordinates; crop only the correct column |
| Use caption position as figure boundary | Find actual element positions (images + labels) |
| Trust only y-coordinates | Always verify x-coordinates too |
| Use --auto-trim on tables | Use --padding only; auto-trim may delete thin table lines |
| Iterate blindly on coordinates | Save `page_analysis.json` with x,y for every text block first |
