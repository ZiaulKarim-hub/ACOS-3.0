# Phase 3 — Convert (HTML → PDF / PPTX)

## Purpose
Render the filled HTML to the requested output format(s). PDF via Puppeteer with tear-sheet settings; PPTX via loan-doc's `data-to-pptx.py` + post-build cleanup.

## Bash Block

```bash
set -e
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE:-$0}")/.." && pwd)"
SESSION_DIR=".acos/ultimate-designer/sessions/{session_id}"
MANIFEST="$SESSION_DIR/manifest.yaml"
FORMAT="$(python3 -c "import yaml; m=yaml.safe_load(open('$MANIFEST')); print(m['inputs']['output_format'])")"

# PDF path (parallel to PPTX)
if [ "$FORMAT" = "pdf" ] || [ "$FORMAT" = "both" ]; then
  bash "$SKILL_DIR/scripts/render-pdf.sh" \
    --input "$SESSION_DIR/output.html" \
    --output "$SESSION_DIR/output.pdf" &
  PDF_PID=$!
fi

# PPTX path
if [ "$FORMAT" = "pptx" ] || [ "$FORMAT" = "both" ]; then
  python3 "$SKILL_DIR/scripts/emit-pptx-content.py" \
    --page-plan "$SESSION_DIR/page-plan.yaml" \
    --image-log "$SESSION_DIR/image-resolution.log" \
    --output "$SESSION_DIR/phase3/pptx-content.yaml"

  bash "$SKILL_DIR/scripts/render-pptx.sh" \
    --content "$SESSION_DIR/phase3/pptx-content.yaml" \
    --template "$SKILL_DIR/templates/template.pptx" \
    --design-spec "$SKILL_DIR/templates/pptx-design-spec.yaml" \
    --output "$SESSION_DIR/output.pptx" &
  PPTX_PID=$!
fi

# Wait on both
[ -n "${PDF_PID:-}" ]  && wait $PDF_PID
[ -n "${PPTX_PID:-}" ] && wait $PPTX_PID

echo "Phase 3 complete"
```

## render-pdf.sh behavior
- If loan-doc's `html-to-pdf.js` supports the required flags (`--margin 0`, networkidle0, fonts.ready await), wraps it
- Otherwise uses this skill's dedicated `render-pdf.mjs` (mimics v3's render.mjs pattern exactly)
- **Fonts.ready await is non-negotiable** — without it, Cormorant Garamond falls back to Georgia

## render-pptx.sh behavior
- Invokes `data-to-pptx.py` (loan-doc script, reused) with our content + design-spec + template
- On success, runs `pptx-cleanup.py`:
  1. Strip theme shadows (`outerShdw` → effectRef idx=0)
  2. Ensure `fill.solid()` on every text shape (Brad Explicit Background Rule)
  3. Attempt Cormorant Garamond OOXML font embedding; on failure, add advisory note to closing slide

## Outputs
- `{SESSION_DIR}/output.pdf` (if requested)
- `{SESSION_DIR}/output.pptx` (if requested)
