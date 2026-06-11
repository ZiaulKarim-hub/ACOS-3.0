#!/usr/bin/env bash
# Type-Forge — launch the whole app on ONE port: home hub + glyph editor +
# spacing editor + specimen viewer, with all save/data endpoints.
#
# Usage:  ./typeforge.sh <base.ttf> <built.ttf> <edits_dir> [port]
#   base.ttf   the base typeface (shown as a ghost in the glyph editor)
#   built.ttf  the current vectorized font (shown in spacing + specimen)
#   edits_dir  where glyph-edits.json / spacing.json live
set -e
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE="${1:?usage: typeforge.sh <base.ttf> <built.ttf> <edits_dir> [port]}"
BUILT="${2:?usage: typeforge.sh <base.ttf> <built.ttf> <edits_dir> [port]}"
EDITS="${3:?usage: typeforge.sh <base.ttf> <built.ttf> <edits_dir> [port]}"
PORT="${4:-8800}"
exec python3 "$SKILL_DIR/scripts/typeforge_serve.py" "$BASE" "$BUILT" "$EDITS" "$SKILL_DIR/assets" "$PORT"
