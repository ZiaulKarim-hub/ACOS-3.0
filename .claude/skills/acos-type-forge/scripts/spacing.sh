#!/usr/bin/env bash
# Browser Spacing Editor — set independent left/right cushions per glyph by eye,
# with live preview. Save writes <edits_dir>/spacing.json; then rebuild with
#   vectorize.py --spacing-file <edits_dir>/spacing.json  (plus --space ...)
# to bake the cushions into the real font.
#
# Usage:  ./spacing.sh /path/to/Font.ttf /path/to/edits_dir [port]
set -e
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FONT="${1:?usage: spacing.sh <font.ttf> <edits_dir> [port]}"
EDITS="${2:?usage: spacing.sh <font.ttf> <edits_dir> [port]}"
PORT="${3:-8790}"
exec python3 "$SKILL_DIR/scripts/spacing_serve.py" "$FONT" "$SKILL_DIR/assets" "$EDITS" "$PORT"
