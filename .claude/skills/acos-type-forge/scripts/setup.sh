#!/usr/bin/env bash
# acos-type-forge — install all dependencies (idempotent).
set -e
echo "=== Python libs (fonttools, shapely, brotli, Pillow) ==="
python3 -m pip install --break-system-packages --quiet fonttools shapely brotli Pillow || \
python3 -m pip install --quiet fonttools shapely brotli Pillow
echo "=== FontForge (outline edits / tracking) ==="
command -v fontforge >/dev/null 2>&1 && echo "  fontforge present" || brew install fontforge
echo "=== potrace (raster edits -> vector glyphs) ==="
command -v potrace   >/dev/null 2>&1 && echo "  potrace present"   || brew install potrace
echo "=== health check ==="
python3 - <<'PY'
import importlib
for m in ("fontTools","shapely","brotli","PIL"):
    importlib.import_module(m); print("  ok:",m)
PY
for b in fontforge potrace; do command -v $b >/dev/null && echo "  ok: $b" || echo "  MISSING: $b"; done
echo "Setup complete."
