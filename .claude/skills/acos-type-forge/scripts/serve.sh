#!/usr/bin/env bash
# Serve the glyph editor with a chosen base font.
# Web fonts can't load over file:// in Chrome, so we serve over localhost.
#
# Usage:  ./serve.sh /path/to/BaseFont.ttf [port]
set -e
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FONT="${1:?usage: serve.sh <base-font.ttf|.otf|.woff2> [port]}"
PORT="${2:-8787}"
ASSETS="$SKILL_DIR/assets"

echo "=== converting base font -> assets/base.woff2 ==="
python3 - "$FONT" "$ASSETS/base.woff2" <<'PY'
import sys
from fontTools.ttLib import TTFont
f = TTFont(sys.argv[1]); f.flavor = "woff2"; f.save(sys.argv[2])
print("  base.woff2 written")
PY

echo "=== serving editor (with disk Save) at http://127.0.0.1:$PORT/editor.html ==="
exec python3 "$SKILL_DIR/scripts/serve.py" "$ASSETS" "$SKILL_DIR/edits" "$PORT"
