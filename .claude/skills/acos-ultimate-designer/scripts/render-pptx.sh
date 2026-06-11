#!/usr/bin/env bash
# render-pptx.sh — generate editable PPTX via loan-doc's data-to-pptx.py + cleanup.
#
# Usage: render-pptx.sh --content <yaml> --template <pptx> --design-spec <yaml> --output <pptx> [--skip-cleanup]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Locate ACOS 3.0 root
ACOS_ROOT="$SKILL_DIR"
while [ "$ACOS_ROOT" != "/" ] && [ ! -f "$ACOS_ROOT/.claude/scripts/data-to-pptx.py" ]; do
  ACOS_ROOT="$(dirname "$ACOS_ROOT")"
done

if [ ! -f "$ACOS_ROOT/.claude/scripts/data-to-pptx.py" ]; then
  echo "render-pptx.sh: ERROR — data-to-pptx.py not found (searched up from $SKILL_DIR)" >&2
  exit 1
fi

CONTENT=""; TEMPLATE=""; DESIGN_SPEC=""; OUTPUT=""; SKIP_CLEANUP=0
while [ $# -gt 0 ]; do
  case "$1" in
    --content)      CONTENT="$2"; shift 2;;
    --template)     TEMPLATE="$2"; shift 2;;
    --design-spec)  DESIGN_SPEC="$2"; shift 2;;
    --output)       OUTPUT="$2"; shift 2;;
    --skip-cleanup) SKIP_CLEANUP=1; shift;;
    -h|--help)
      echo "Usage: $0 --content <yaml> --template <pptx> --design-spec <yaml> --output <pptx> [--skip-cleanup]"
      exit 0;;
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

[ -z "$CONTENT" ] || [ -z "$OUTPUT" ] && { echo "ERROR: --content + --output required" >&2; exit 1; }

# Ensure template exists; if not, build it
if [ -n "$TEMPLATE" ] && [ ! -f "$TEMPLATE" ]; then
  echo "render-pptx.sh: template.pptx missing — running build-template-pptx.py" >&2
  python3 "$SCRIPT_DIR/build-template-pptx.py" --output "$TEMPLATE"
fi

# Invoke data-to-pptx.py (loan-doc script, reused).
# Verified CLI: data-to-pptx.py <data_yaml> <design_spec_yaml> [--template T] [-o OUTPUT]
#   positional 1 = content/data YAML, positional 2 = REQUIRED design-spec YAML.
# --design-spec is required by this script; --template is optional (guarded below).
[ -z "$DESIGN_SPEC" ] && { echo "ERROR: --design-spec required for data-to-pptx.py" >&2; exit 1; }

DTP_ARGS=("$CONTENT" "$DESIGN_SPEC")
[ -n "$TEMPLATE" ] && DTP_ARGS+=(--template "$TEMPLATE")
DTP_ARGS+=(-o "$OUTPUT")

echo "render-pptx.sh: invoking $ACOS_ROOT/.claude/scripts/data-to-pptx.py" >&2
if ! python3 "$ACOS_ROOT/.claude/scripts/data-to-pptx.py" "${DTP_ARGS[@]}" 2>&1; then
  echo "render-pptx.sh: WARN — data-to-pptx.py rejected our schema. Falling back to inline generator." >&2
  python3 "$SCRIPT_DIR/pptx-cleanup.py" --inline-generate --content "$CONTENT" --design-spec "$DESIGN_SPEC" --template "$TEMPLATE" --output "$OUTPUT"
fi

# Post-build cleanup
if [ "$SKIP_CLEANUP" -eq 0 ]; then
  python3 "$SCRIPT_DIR/pptx-cleanup.py" --pptx "$OUTPUT" --design-spec "$DESIGN_SPEC"
fi

echo "render-pptx.sh: wrote $OUTPUT" >&2
