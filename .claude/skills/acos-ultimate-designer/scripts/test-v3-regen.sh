#!/usr/bin/env bash
# test-v3-regen.sh — full-pipeline regeneration test vs v3 reference.
#
# Runs wigum-loop.py end-to-end. Compares output against v3 reference on:
#   - page count (±1)
#   - file size (±30%)
#   - first-page perceptual hash (>80% similarity)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

V3_PDF="/Users/zee/Desktop/Private Credit Capabilities/OKOA Capital - Private Credit Capabilities (v3 — expanded).pdf"
V3_IMAGES="/Users/zee/Desktop/Private Credit Capabilities/v3/images"
SAMPLE_YAML="$SKILL_DIR/examples/v3-input-sample.yaml"
KEEP_SESSION=0; VERBOSE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --keep-session) KEEP_SESSION=1; shift;;
    --verbose)      VERBOSE=1; shift;;
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

SESSION_DIR=".acos/ultimate-designer/sessions/test-v3-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$SESSION_DIR"/{phase1,phase3,visual-audit}

cat > "$SESSION_DIR/manifest.yaml" <<EOF
session_id: "test-v3"
inputs:
  content_path: "$SAMPLE_YAML"
  output_format: pdf
  asset_dir: "$V3_IMAGES"
  iteration_ceiling: 3
EOF

python3 "$SKILL_DIR/scripts/wigum-loop.py" \
  --session-dir "$SESSION_DIR" --format pdf --max-iterations 3 --hard-ceiling 10 \
  || WIGUM_RC=$?

OUTPUT="$SESSION_DIR/output.pdf"
[ ! -f "$OUTPUT" ] && { echo "[v3-regen] FAIL: no output.pdf"; exit 1; }

# Comparisons
{
  echo "| Check | Expected | Actual | Status |"
  echo "|---|---|---|---|"

  if command -v pdfinfo >/dev/null 2>&1; then
    OUT_PAGES=$(pdfinfo "$OUTPUT" | awk '/^Pages:/ {print $2}')
    REF_PAGES=$(pdfinfo "$V3_PDF" 2>/dev/null | awk '/^Pages:/ {print $2}' || echo "?")
    diff=$((OUT_PAGES - REF_PAGES))
    STATUS="pass"; [ ${diff#-} -gt 1 ] && STATUS="fail"
    echo "| page count | $REF_PAGES ±1 | $OUT_PAGES | $STATUS |"
  fi

  OUT_SIZE=$(stat -f%z "$OUTPUT" 2>/dev/null || stat -c%s "$OUTPUT")
  REF_SIZE=$(stat -f%z "$V3_PDF" 2>/dev/null || stat -c%s "$V3_PDF" 2>/dev/null || echo 0)
  if [ "$REF_SIZE" -gt 0 ]; then
    LOWER=$((REF_SIZE * 7 / 10))
    UPPER=$((REF_SIZE * 13 / 10))
    STATUS="pass"; { [ "$OUT_SIZE" -lt "$LOWER" ] || [ "$OUT_SIZE" -gt "$UPPER" ]; } && STATUS="fail"
    echo "| file size | $REF_SIZE ±30% | $OUT_SIZE | $STATUS |"
  fi

  # Perceptual hash (requires imagehash + pdftoppm)
  if command -v pdftoppm >/dev/null 2>&1 && python3 -c "import imagehash" 2>/dev/null; then
    TMPDIR=$(mktemp -d)
    pdftoppm -r 100 -png -f 1 -l 1 "$OUTPUT"  "$TMPDIR/out"
    pdftoppm -r 100 -png -f 1 -l 1 "$V3_PDF"  "$TMPDIR/ref" 2>/dev/null || true
    if [ -f "$TMPDIR/out-1.png" ] && [ -f "$TMPDIR/ref-1.png" ]; then
      SIM=$(python3 -c "from PIL import Image; import imagehash; a=imagehash.phash(Image.open('$TMPDIR/out-1.png')); b=imagehash.phash(Image.open('$TMPDIR/ref-1.png')); print(f'{1 - (a - b) / 64:.3f}')")
      STATUS="pass"; awk "BEGIN {exit !($SIM >= 0.8)}" || STATUS="fail"
      echo "| page-1 pHash similarity | >0.80 | $SIM | $STATUS |"
    fi
    rm -rf "$TMPDIR"
  fi
} | tee "$SESSION_DIR/test-v3-regen.md"

[ "$KEEP_SESSION" -eq 1 ] && echo "[v3-regen] session kept at $SESSION_DIR"
echo "[v3-regen] report: $SESSION_DIR/test-v3-regen.md"
