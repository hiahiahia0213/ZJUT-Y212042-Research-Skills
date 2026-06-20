#!/usr/bin/env python3
import argparse
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw


PAGE_RE = re.compile(r"page[-]?(\d+)")


def page_number(path):
    match = PAGE_RE.match(path.stem)
    if match:
        return int(match.group(1))
    return 10**9


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages_dir", default="outputs/paper_pages")
    parser.add_argument("--out", default="outputs/paper_pages/contact_sheet.png")
    parser.add_argument("--thumb_width", type=int, default=320)
    parser.add_argument("--cols", type=int, default=3)
    args = parser.parse_args()

    pages_dir = Path(args.pages_dir)
    files = sorted(list(pages_dir.glob("page-*.png")) + list(pages_dir.glob("page0*.png")), key=page_number)

    if not files:
        raise FileNotFoundError(f"No page-*.png found in {pages_dir}")

    thumbs = []
    for page_path in files:
        img = Image.open(page_path).convert("RGB")
        ratio = args.thumb_width / img.width
        thumb = img.resize((args.thumb_width, int(img.height * ratio)))
        thumbs.append((page_path, thumb))

    pad = 30
    label_h = 30
    cols = args.cols
    rows = math.ceil(len(thumbs) / cols)

    cell_w = args.thumb_width + pad
    cell_h = max(thumb.height for _, thumb in thumbs) + label_h + pad

    sheet = Image.new("RGB", (cols * cell_w + pad, rows * cell_h + pad), "white")
    draw = ImageDraw.Draw(sheet)

    for idx, (page_path, thumb) in enumerate(thumbs):
        row = idx // cols
        col = idx % cols
        x = pad + col * cell_w
        y = pad + row * cell_h
        sheet.paste(thumb, (x, y + label_h))
        draw.text((x, y), f"Page {page_number(page_path)}", fill="black")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"[INFO] Saved contact sheet: {out}")


if __name__ == "__main__":
    main()
