#!/usr/bin/env bash
# render-and-verify.sh — render output to 200 DPI PNGs + spawn opus-pinned visual reviewer.
#
# The visual reviewer is HARD-PINNED to model='opus'. Do NOT replace with a session
# config lookup — subtle coffee-table defects require opus acuity (per STORY-005).
#
# Usage: render-and-verify.sh --session-dir <dir> --iteration <N> --format pdf|pptx [--checklist <path>]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Locate ACOS 3.0 root
ACOS_ROOT="$SKILL_DIR"
while [ "$ACOS_ROOT" != "/" ] && [ ! -f "$ACOS_ROOT/.claude/scripts/render-doc-audit.py" ]; do
  ACOS_ROOT="$(dirname "$ACOS_ROOT")"
done

SESSION_DIR=""; ITERATION=1; FORMAT="pdf"; CHECKLIST=""
while [ $# -gt 0 ]; do
  case "$1" in
    --session-dir) SESSION_DIR="$2"; shift 2;;
    --iteration)   ITERATION="$2"; shift 2;;
    --format)      FORMAT="$2"; shift 2;;
    --checklist)   CHECKLIST="$2"; shift 2;;
    -h|--help) echo "Usage: $0 --session-dir <dir> --iteration <N> --format pdf|pptx [--checklist <path>]"; exit 0;;
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

[ -z "$SESSION_DIR" ] && { echo "ERROR: --session-dir required" >&2; exit 1; }
[ -z "$CHECKLIST" ] && CHECKLIST="$SKILL_DIR/templates/visual-checklist.yaml"

case "$FORMAT" in
  pdf)  OUTPUT_FILE="$SESSION_DIR/output.pdf";;
  pptx) OUTPUT_FILE="$SESSION_DIR/output.pptx";;
  *) echo "ERROR: --format must be pdf or pptx" >&2; exit 1;;
esac

[ ! -f "$OUTPUT_FILE" ] && { echo "ERROR: output not found: $OUTPUT_FILE" >&2; exit 1; }

AUDIT_DIR="$SESSION_DIR/visual-audit/iteration-$(printf '%02d' $ITERATION)"
mkdir -p "$AUDIT_DIR"

# Step 1 — render output to PNGs via render-doc-audit.py (loan-doc script, reused)
# DPI = 150: US Letter -> 1275x1650 px, safely under the Anthropic API 2000 px
# many-image cap. Higher DPI silently locks the conversation when the reviewer
# tries to Read multiple page PNGs in one turn.
if [ -f "$ACOS_ROOT/.claude/scripts/render-doc-audit.py" ]; then
  python3 "$ACOS_ROOT/.claude/scripts/render-doc-audit.py" \
    "$OUTPUT_FILE" --output-dir "$AUDIT_DIR" --dpi 150 2>&1 | tee "$AUDIT_DIR/render.log" || true
fi

# Fallback: use pdftoppm / macOS sips if render-doc-audit.py didn't produce PNGs
if ! ls "$AUDIT_DIR"/*.png >/dev/null 2>&1; then
  if [ "$FORMAT" = "pdf" ] && command -v pdftoppm >/dev/null 2>&1; then
    pdftoppm -r 150 -png "$OUTPUT_FILE" "$AUDIT_DIR/page" || true
  fi
fi

# Safety net: enforce a hard 1800 px ceiling on any PNG that slipped through
# (e.g., tabloid / A3 input where even 150 DPI exceeds 2000 px). The Anthropic
# API rejects many-image requests where ANY image exceeds 2000 px on either
# edge; once tripped, the conversation is locked until manual /compact.
if command -v sips >/dev/null 2>&1; then
  sips -Z 1800 "$AUDIT_DIR"/*.png >/dev/null 2>&1 || true
fi

PNG_COUNT=$(ls "$AUDIT_DIR"/*.png 2>/dev/null | wc -l | tr -d ' ')
echo "render-and-verify.sh: rendered $PNG_COUNT PNGs to $AUDIT_DIR" >&2

if [ "$PNG_COUNT" -eq 0 ]; then
  echo "render-and-verify.sh: ERROR — no PNGs produced; cannot verify visually" >&2
  exit 1
fi

# Step 2 — spawn opus-pinned visual reviewer agent
# The agent prompt is written to a file; the skill's protocol triggers the Task()
# with model='opus' HARDCODED when dispatching this phase. For a local-scripted
# invocation (e.g., CI), we write the prompt + defects file skeleton so the
# orchestration agent (wigum-loop.py's caller) can pick them up.
#
# Agent model: opus (HARDCODED — do not change)
AGENT_PROMPT_FILE="$AUDIT_DIR/agent-prompt.md"
DEFECTS_FILE="$AUDIT_DIR/visual-defects.yaml"

cat > "$AGENT_PROMPT_FILE" <<EOF
# Visual Reviewer — Iteration $ITERATION

**MODEL: opus (hard-pinned, non-negotiable).**

You are reviewing a rendered OKOA coffee-table document. Read every PNG in
\`$AUDIT_DIR/\` via the Read tool, then evaluate the checklist below against
what you see — SCREENSHOT ONLY. You have no access to the HTML source.

## Checklist
\`$CHECKLIST\`

## Output
Write YAML to \`$DEFECTS_FILE\`:

\`\`\`yaml
iteration: $ITERATION
criteria_results:
  - id: PR-01
    page: <page_number>
    status: pass | fail
    severity: ERROR | WARNING
    observation: "what you see"
    fix_instruction: "actionable, specific"
verdict: pass | fail
failed_items: []
\`\`\`

A verdict of PASS requires zero ERROR-severity failures.
EOF

# For local scripted use (non-Claude-Code context): emit a sentinel "needs_agent"
# so wigum-loop.py knows to spawn the Task. In the Claude Code orchestration path,
# the skill protocol (phase4-verify.md) reads this file and handles the Task spawn.
if [ ! -f "$DEFECTS_FILE" ]; then
  cat > "$DEFECTS_FILE" <<EOF
iteration: $ITERATION
verdict: needs_agent
agent_prompt_file: "$AGENT_PROMPT_FILE"
criteria_results: []
failed_items: []
note: "Spawn a Task(model='opus') with agent_prompt_file contents to populate this file."
EOF
fi

echo "render-and-verify.sh: wrote $DEFECTS_FILE (iteration $ITERATION)" >&2
# Exit 0 indicates successful render + prompt emission; actual PASS/FAIL is in the YAML verdict.
# wigum-loop.py reads verdict and decides next action.
exit 0
