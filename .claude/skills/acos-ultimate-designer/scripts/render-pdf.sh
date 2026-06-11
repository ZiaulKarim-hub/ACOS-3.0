#!/usr/bin/env bash
# render-pdf.sh — wraps render-pdf.mjs with node_modules resolution.
#
# Tries to reuse Puppeteer from loan-doc skill's node_modules (which installs
# puppeteer in the ACOS 3.0 source tree). Falls back to whatever is globally
# resolvable.
#
# Usage: render-pdf.sh --input <html> --output <pdf> [--timeout 120]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Locate ACOS 3.0 root (contains .claude/scripts)
ACOS_ROOT="$SKILL_DIR"
while [ "$ACOS_ROOT" != "/" ] && [ ! -d "$ACOS_ROOT/.claude/scripts" ]; do
  ACOS_ROOT="$(dirname "$ACOS_ROOT")"
done

# Prefer loan-doc skill's node_modules (has Puppeteer installed)
LOAN_DOC_TMPL="$ACOS_ROOT/.claude/skills/acos-loan-doc-generator-with-visual-verification/templates"
LOAN_DOC_TMPL_ALT="$ACOS_ROOT/.claude/skills/acos-loan-doc-generator/templates"
NODE_MODULES=""
for dir in "$LOAN_DOC_TMPL" "$LOAN_DOC_TMPL_ALT" "$ACOS_ROOT/.claude/scripts" "$ACOS_ROOT"; do
  if [ -d "$dir/node_modules/puppeteer" ]; then
    NODE_MODULES="$dir/node_modules"
    break
  fi
done

if [ -n "$NODE_MODULES" ]; then
  export NODE_PATH="$NODE_MODULES"
  echo "render-pdf.sh: using Puppeteer at $NODE_MODULES" >&2
else
  echo "render-pdf.sh: WARN — no bundled Puppeteer found; relying on global resolution" >&2
fi

exec node "$SCRIPT_DIR/render-pdf.mjs" "$@"
