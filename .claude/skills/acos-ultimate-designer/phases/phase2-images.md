# Phase 2 — Image Sourcing

## Purpose
Bootstrap the brand-asset manifest (if asset dir provided and stale), fill every `data-photo-slot` in the HTML with an actual image (brand-asset or Unsplash/Pexels fallback), write attribution.

## Scripts Invoked
- `scripts/validate-image.py` — magic-byte + Pillow decode check; rejects HTML error pages saved as `.jpg`, truncated downloads, zero-byte files
- `scripts/bootstrap-manifest.py` — scans asset dir, makes parallel Anthropic vision API calls if `ANTHROPIC_API_KEY` is set, else writes filename-derived placeholder tags; writes manifest.yaml
- `scripts/match-image.py` — semantic match per slot
- `scripts/fetch-image-fallback.py` — Unsplash → Pexels
- `scripts/fill-photo-slots.py` — substitutes placeholders in HTML, writes ATTRIBUTION.md

## Why validation runs first

Downloaders that ignore HTTP status codes (including `curl` without `--fail` and
some WebFetch flows) will happily save a server's HTML 404 page under an image
filename. Sending such a file to the Anthropic vision API returns
`400 Could not process image`, and because attached image bytes persist in
conversation history, the failure is **sticky** — every subsequent turn in that
session replays the bad image and gets the same 400. The only recovery is
`/clear`, losing the session. Therefore: validate every image the moment it
enters the pipeline, before any tool or API call touches it.

## Bash Block

```bash
set -e
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE:-$0}")/.." && pwd)"
SESSION_DIR=".acos/ultimate-designer/sessions/{session_id}"
MANIFEST="$SESSION_DIR/manifest.yaml"

ASSET_DIR="$(python3 -c "import yaml; m=yaml.safe_load(open('$MANIFEST')); print(m['inputs'].get('asset_dir') or '')")"

# Sweep any pre-populated photo pool (populated outside the skill, e.g. by
# the main conversation using WebFetch/curl). Quarantine non-images to
# photo-pool/_quarantine/ so they can never be Read() as images downstream.
# Uses `find` instead of shell globs — portable across bash/zsh regardless
# of nullglob/nomatch defaults.
POOL="$SESSION_DIR/photo-pool"
if [ -d "$POOL" ]; then
  mkdir -p "$POOL/_quarantine"
  find "$POOL" -maxdepth 1 -type f \
    \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.gif' \) \
    -print0 | while IFS= read -r -d '' f; do
      if ! python3 "$SKILL_DIR/scripts/validate-image.py" --quiet "$f" 2>> "$SESSION_DIR/validate-image.log"; then
        mv "$f" "$POOL/_quarantine/" 2>/dev/null || true
      fi
    done
fi

# Bootstrap manifest if asset dir is provided
if [ -n "$ASSET_DIR" ] && [ -d "$ASSET_DIR" ]; then
  python3 "$SKILL_DIR/scripts/bootstrap-manifest.py" \
    --asset-dir "$ASSET_DIR" \
    --manifest "$ASSET_DIR/.acos-ultimate-designer-manifest.yaml"
fi

# Fill photo slots in HTML
BRAND_MANIFEST_ARG=""
[ -n "$ASSET_DIR" ] && BRAND_MANIFEST_ARG="--manifest $ASSET_DIR/.acos-ultimate-designer-manifest.yaml"

python3 "$SKILL_DIR/scripts/fill-photo-slots.py" \
  --html "$SESSION_DIR/output.html" \
  --session-dir "$SESSION_DIR" \
  --output "$SESSION_DIR/output.html" \
  $BRAND_MANIFEST_ARG

echo "Phase 2 complete — image log at $SESSION_DIR/image-resolution.log, attributions at $SESSION_DIR/ATTRIBUTION.md"
```

## API Key Behavior
- `UNSPLASH_ACCESS_KEY` + `PEXELS_API_KEY` are optional env vars
- Unset → warning to stderr, continue in brand-only mode, unmatched slots render as "IMAGE MISSING" placeholders (visual gate flags these in Phase 4)

## Outputs
- `{ASSET_DIR}/.acos-ultimate-designer-manifest.yaml` — persistent brand manifest (idempotent)
- `{SESSION_DIR}/images/` — downloaded fallback images
- `{SESSION_DIR}/output.html` — HTML with all slots filled
- `{SESSION_DIR}/image-resolution.log` — per-slot resolution decisions (`{page, slot_id, file_hash_or_url, source, score}`)
- `{SESSION_DIR}/ATTRIBUTION.md` — markdown table matching v3 reference format
- `{SESSION_DIR}/photo-pool/_quarantine/` — any pre-populated photo-pool files that failed image validation (HTML saved as `.jpg`, truncated downloads, zero-byte files). Inspect this directory when a slot resolves to an unexpected image; the underlying URL probably 404'd.
- `{SESSION_DIR}/validate-image.log` — stderr output from the photo-pool sweep
