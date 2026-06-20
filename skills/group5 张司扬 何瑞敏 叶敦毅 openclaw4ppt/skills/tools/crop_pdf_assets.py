#!/usr/bin/env python3
"""
crop_pdf_assets.py — Crop paper figures/tables from rendered page images.

Usage:
    python tools/crop_pdf_assets.py \\
      --plan outputs/paper_assets/crop_plan.json \\
      --pages_dir outputs/paper_pages \\
      --assets_dir outputs/paper_assets \\
      --padding 20 \\
      --enhance \\
      --auto-trim \\
      --qc \\
      --preview
"""
import argparse, json, os, sys
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# QUALITY CHECK
# ============================================================
def check_quality(img: Image.Image, asset_type: str) -> list:
    """Return list of QC issues."""
    issues = []
    w, h = img.size

    # 1. Minimum size
    if w < 300 or h < 150:
        issues.append(f"Small dimensions ({w}x{h})")

    # 2. Detail ratio (for tables vs figures)
    gray = img.convert("L")
    hist = gray.histogram()
    total = max(sum(hist), 1)
    detail = sum(hist[30:230]) / total
    if asset_type == "table" and detail < 0.01:
        issues.append(f"Low detail ({detail:.4f})—may be blank or white-dominant")
    if asset_type in ("figure", "visualization") and detail < 0.02:
        issues.append(f"Low detail ({detail:.4f})—check for blank crop")

    # 3. Edge continuity (checks if border is all pure white = likely clipped content)
    top_edge = [gray.getpixel((x, 0)) for x in range(0, w, max(1, w // 10))]
    bot_edge = [gray.getpixel((x, h - 1)) for x in range(0, w, max(1, w // 10))]
    left_edge = [gray.getpixel((0, y)) for y in range(0, h, max(1, h // 10))]
    right_edge = [gray.getpixel((w - 1, y)) for y in range(0, h, max(1, h // 10))]

    if all(p < 240 for p in top_edge):
        issues.append("Top edge has content—crop may be too tight (clipping)")
    if all(p < 240 for p in bot_edge):
        issues.append("Bottom edge has content—check for clipped rows")

    # 4. White margin ratio
    white_px = sum(1 for p in list(gray.getdata())[:10000] if p > 245) / min(10000, w * h)
    if white_px > 0.92:
        issues.append(f"High white ratio ({white_px:.2f})—too much blank margin")

    return issues


# ============================================================
# AUTO-TRIM
# ============================================================
def auto_trim(img: Image.Image, padding: int) -> Image.Image:
    """Trim excess whitespace from edges of image."""
    gray = img.convert("L")
    w, h = img.size

    # Find non-white rows/columns
    def is_content_x(x):
        col = [gray.getpixel((x, y)) for y in range(0, h, 2)]
        return any(p < 240 for p in col)

    def is_content_y(y):
        row = [gray.getpixel((x, y)) for x in range(0, w, 2)]
        return any(p < 240 for p in row)

    left = next((x for x in range(w) if is_content_x(x)), 0)
    right = next((x for x in range(w - 1, -1, -1) if is_content_x(x)), w - 1)
    top = next((y for y in range(h) if is_content_y(y)), 0)
    bottom = next((y for y in range(h - 1, -1, -1) if is_content_y(y)), h - 1)

    # Apply padding
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(w, right + padding)
    bottom = min(h, bottom + padding)

    return img.crop((left, top, right, bottom))


# ============================================================
# PREVIEW GENERATION
# ============================================================
def create_preview(page_img: Image.Image, box_px: list, page_num: int,
                   out_path: str):
    """Draw a red rectangle on the page image showing the crop region."""
    preview = page_img.copy().convert("RGBA")
    overlay = Image.new("RGBA", preview.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    x1, y1, x2, y2 = box_px
    # Semi-transparent red fill
    draw.rectangle([x1, y1, x2, y2], fill=(255, 0, 0, 40), outline=(255, 0, 0, 255), width=4)
    # Label
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    draw.text((x1 + 10, y1 + 10), f"Page {page_num}", fill=(255, 0, 0, 255), font=font)

    preview = Image.alpha_composite(preview, overlay)
    preview.convert("RGB").save(out_path)
    return out_path


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Crop figures and tables from rendered PDF pages")
    parser.add_argument("--plan", required=True, help="Path to crop_plan.json")
    parser.add_argument("--pages_dir", required=True, help="Directory with rendered page PNGs")
    parser.add_argument("--assets_dir", required=True, help="Output directory for cropped assets")
    parser.add_argument("--padding", type=int, default=0, help="Extra padding around crop (px)")
    parser.add_argument("--enhance", action="store_true", help="Apply contrast sharpening")
    parser.add_argument("--auto-trim", action="store_true", help="Trim excess whitespace after cropping")
    parser.add_argument("--qc", action="store_true", help="Run quality checks and generate crop_qc.md")
    parser.add_argument("--preview", action="store_true", help="Generate preview images with crop box overlay")
    args = parser.parse_args()

    # Load plan
    with open(args.plan, encoding="utf-8") as f:
        plan = json.load(f)

    # Determine schema
    if "items" in plan:
        assets = plan["items"]
        key_box = "box"
    elif "assets" in plan:
        assets = plan["assets"]
        key_box = "box_norm" if "box_norm" in assets[0] else "box_px"
    else:
        print("Error: plan must have 'items' or 'assets' key")
        sys.exit(1)

    os.makedirs(args.assets_dir, exist_ok=True)
    preview_dir = os.path.join(args.assets_dir, "crop_previews")
    if args.preview:
        os.makedirs(preview_dir, exist_ok=True)

    # Determine DPI and page size
    dpi = plan.get("dpi", 300)
    if "page_size_px" in plan:
        PW, PH = plan["page_size_px"]
    else:
        PW, PH = 2550, 3300  # Assume 8.5x11 at 300DPI

    # Find page image files
    def find_page(pn):
        """Find page image with various naming patterns."""
        for fmt in [f"page{pn:03d}.png", f"page{pn:02d}.png", f"page-{pn}.png",
                     f"page-{pn:03d}.png", f"page-{pn:02d}.png", f"page{pn}.png"]:
            path = os.path.join(args.pages_dir, fmt)
            if os.path.exists(path):
                return path
        return None

    # Crop each asset
    results = []
    qc_issues = []

    print(f"Cropping {len(assets)} assets @ {dpi}DPI")
    print(f"pages_dir: {args.pages_dir}")
    print(f"assets_dir: {args.assets_dir}")
    if args.padding: print(f"padding: {args.padding}px")
    if args.auto_trim: print(f"auto-trim: on")
    if args.enhance: print(f"enhance: on")
    print()

    for i, item in enumerate(assets, 1):
        page_num = item.get("page", 1)
        name = item.get("name", item.get("filename", f"asset_{i}"))
        asset_type = item.get("type", "unknown")

        # Resolve box: normalize to pixels
        if key_box == "box":
            # Normalized coordinates -> convert to pixels
            b = item["box"]
            box_px = [int(b[0] * PW), int(b[1] * PH), int(b[2] * PW), int(b[3] * PH)]
        elif key_box == "box_norm":
            b = item.get("box_norm", item.get("box"))
            if isinstance(b, list) and len(b) == 4:
                box_px = [int(b[0] * PW), int(b[1] * PH), int(b[2] * PW), int(b[3] * PH)]
            else:
                print(f"  [{i}] {name}: invalid norm box")
                continue
        elif key_box in item:
            # Pixel coordinates
            box_px = item.get(key_box)
        else:
            print(f"  [{i}] {name}: no box found (tried {key_box})")
            continue

        # Apply padding
        box_px = [box_px[0] - args.padding, box_px[1] - args.padding,
                   box_px[2] + args.padding, box_px[3] + args.padding]
        box_px = [max(0, b) for b in box_px]
        box_px[2] = min(PW, box_px[2])
        box_px[3] = min(PH, box_px[3])

        # Load page image
        page_path = find_page(page_num)
        if not page_path:
            print(f"  [{i}] {name}: page {page_num} not found")
            qc_issues.append({"name": name, "issue": "PAGE MISSING"})
            continue

        page_img = Image.open(page_path)

        # Crop
        crop_box = tuple(box_px)
        cropped = page_img.crop(crop_box)

        # Auto-trim
        if args.auto_trim:
            cropped = auto_trim(cropped, padding=max(10, args.padding))

        # Enhance
        if args.enhance:
            from PIL import ImageEnhance
            cropped = ImageEnhance.Sharpness(cropped).enhance(1.2)
            cropped = ImageEnhance.Contrast(cropped).enhance(1.05)

        # Save
        out_path = os.path.join(args.assets_dir, f"{name}.png")
        cropped.save(out_path)
        w, h = cropped.size
        kb = os.path.getsize(out_path) // 1024
        status = "OK"

        # QC
        if args.qc:
            qc_list = check_quality(cropped, asset_type)
            if qc_list:
                status = "CHECK"
                qc_issues.append({"name": name, "issues": qc_list})

        # Preview
        if args.preview:
            prev_path = os.path.join(preview_dir, f"{name}_preview.png")
            create_preview(page_img, box_px, page_num, prev_path)

        print(f"  [{i:2d}] {status:6s} {name:30s} | page={page_num} | {w}x{h} | {kb}KB | box=({box_px[0]},{box_px[1]})-({box_px[2]},{box_px[3]})")
        results.append({"name": name, "size": f"{w}x{h}", "kb": kb, "status": status,
                        "page": page_num, "type": asset_type})

    # ============================================================
    # OUTPUTS
    # ============================================================

    # asset_manifest.md
    manifest_path = os.path.join(args.assets_dir, "asset_manifest.md")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("# Asset Manifest\n\n")
        f.write(f"| # | File | Page | Size | Type | Status |\n")
        f.write(f"|---|------|------|------|------|--------|\n")
        for i, r in enumerate(results, 1):
            f.write(f"| {i} | {r['name']}.png | {r['page']} | {r['size']} ({r['kb']}KB) | {r['type']} | {r['status']} |\n")

    # crop_qc.md
    qc_path = os.path.join(args.assets_dir, "crop_qc.md")
    with open(qc_path, "w", encoding="utf-8") as f:
        f.write("# Crop Quality Check Report\n\n")
        f.write(f"Total assets: {len(results)}\n")
        f.write(f"QC issues: {len(qc_issues)}\n\n")
        if qc_issues:
            for qc in qc_issues:
                f.write(f"## {qc['name']}\n")
                f.write(f"Status: CHECK\n")
                for iss in qc["issues"]:
                    f.write(f"- {iss}\n")
                f.write("\n")
        else:
            f.write("All assets passed initial QC.\n")

    # Summary
    ok_count = sum(1 for r in results if r["status"] == "OK")
    chk_count = sum(1 for r in results if r["status"] == "CHECK")

    print(f"\n{'='*60}")
    print(f"RESULT: {ok_count}/{len(results)} OK  |  {chk_count} CHECK")
    print(f"Assets: {args.assets_dir}")
    print(f"Manifest: {manifest_path}")
    print(f"QC Report: {qc_path}")
    if args.preview:
        print(f"Previews: {preview_dir}")

    if chk_count > 0:
        print(f"\n!! {chk_count} assets need manual review. Inspect crop_qc.md and previews.")
        for qc in qc_issues:
            print(f"  - {qc['name']}: {'; '.join(qc['issues'])}")


if __name__ == "__main__":
    main()
