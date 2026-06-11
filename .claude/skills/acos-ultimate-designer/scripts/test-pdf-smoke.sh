#!/usr/bin/env bash
# test-pdf-smoke.sh — end-to-end PDF smoke test.
#
# Runs decompose → emit → fill → render → compares output to v3 reference.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

V3_HTML="/Users/zee/Desktop/Private Credit Capabilities/v3/tearsheet-v3.html"
V3_PDF="/Users/zee/Desktop/Private Credit Capabilities/OKOA Capital - Private Credit Capabilities (v3 — expanded).pdf"
V3_IMAGES="/Users/zee/Desktop/Private Credit Capabilities/v3/images"
SAMPLE_YAML="$SKILL_DIR/examples/v3-input-sample.yaml"
SESSION_DIR="/tmp/acos-ultimate-designer-smoke-$$"
mkdir -p "$SESSION_DIR"/{phase1,phase3,visual-audit}

cat > "$SESSION_DIR/manifest.yaml" <<EOF
session_id: "smoke-$(date +%Y%m%d-%H%M%S)"
inputs:
  content_path: "$SAMPLE_YAML"
  output_format: pdf
  asset_dir: "$V3_IMAGES"
  iteration_ceiling: 1
EOF

echo "[smoke] running pipeline for $SAMPLE_YAML"
python3 "$SKILL_DIR/scripts/decompose-content.py" "$SAMPLE_YAML" "$SESSION_DIR/page-plan.yaml"
python3 "$SKILL_DIR/scripts/html-emit.py" "$SESSION_DIR/page-plan.yaml" "$SESSION_DIR/output.html" \
  --tokens "$SKILL_DIR/templates/tokens.css" --templates "$SKILL_DIR/templates/page-templates"

if [ -d "$V3_IMAGES" ]; then
  python3 "$SKILL_DIR/scripts/bootstrap-manifest.py" --asset-dir "$V3_IMAGES" || true
  python3 "$SKILL_DIR/scripts/fill-photo-slots.py" \
    --html "$SESSION_DIR/output.html" --session-dir "$SESSION_DIR" \
    --output "$SESSION_DIR/output.html" \
    --manifest "$V3_IMAGES/.acos-ultimate-designer-manifest.yaml" || true
fi

bash "$SKILL_DIR/scripts/render-pdf.sh" --input "$SESSION_DIR/output.html" --output "$SESSION_DIR/output.pdf" || {
  echo "[smoke] render failed"
  exit 1
}

# Comparisons
if [ -f "$V3_PDF" ]; then
  OUT_SIZE=$(stat -f%z "$SESSION_DIR/output.pdf" 2>/dev/null || stat -c%s "$SESSION_DIR/output.pdf")
  REF_SIZE=$(stat -f%z "$V3_PDF" 2>/dev/null || stat -c%s "$V3_PDF")
  echo "[smoke] out: $OUT_SIZE bytes  ref: $REF_SIZE bytes"

  if command -v pdfinfo >/dev/null 2>&1; then
    OUT_PAGES=$(pdfinfo "$SESSION_DIR/output.pdf" | awk '/^Pages:/ {print $2}')
    REF_PAGES=$(pdfinfo "$V3_PDF" | awk '/^Pages:/ {print $2}')
    echo "[smoke] out pages: $OUT_PAGES  ref pages: $REF_PAGES"
  fi
fi

echo "[smoke] output: $SESSION_DIR/output.pdf"
