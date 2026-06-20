#!/usr/bin/env bash
set -euo pipefail

PDF_PATH="${1:-}"
OUT_DIR="${2:-outputs/paper_pages}"
DPI="${3:-300}"

if [ -z "$PDF_PATH" ]; then
  echo "Usage: bash tools/render_pdf_pages.sh <paper.pdf> [out_dir] [dpi]"
  exit 1
fi

if [ ! -f "$PDF_PATH" ]; then
  echo "PDF not found: $PDF_PATH"
  exit 1
fi

if ! command -v pdftoppm >/dev/null 2>&1; then
  echo "pdftoppm not found. Install Poppler, for example: sudo apt install poppler-utils" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

echo "[INFO] Rendering PDF pages..."
echo "[INFO] PDF: $PDF_PATH"
echo "[INFO] OUT: $OUT_DIR"
echo "[INFO] DPI: $DPI"

pdftoppm -png -r "$DPI" "$PDF_PATH" "$OUT_DIR/page"

echo "[INFO] Done."
echo "[INFO] Generated files:"
find "$OUT_DIR" -maxdepth 1 -type f -name 'page-*.png' | sort | head
