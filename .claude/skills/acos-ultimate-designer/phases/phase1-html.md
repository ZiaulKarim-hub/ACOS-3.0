# Phase 1 — HTML Emission

## Purpose
Transform user content into a self-contained Brad-styled HTML file with coffee-table composition and empty photo slots. Exits on QA gate failure.

## Scripts Invoked
- `scripts/decompose-content.py` — content → page-plan
- `scripts/html-emit.py` — page-plan → HTML
- `scripts/html-qa-gate.py` — HTML validation

## Bash Block

```bash
set -e
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE:-$0}")/.." && pwd)"
SESSION_DIR=".acos/ultimate-designer/sessions/{session_id}"
MANIFEST="$SESSION_DIR/manifest.yaml"

CONTENT_PATH="$(python3 -c "import yaml; m=yaml.safe_load(open('$MANIFEST')); print(m['inputs']['content_path'])")"

# Decompose content into page plan
FIX_CONTEXT_ARG=""
[ -f "$SESSION_DIR/fix-instructions.yaml" ] && FIX_CONTEXT_ARG="--fix-context $SESSION_DIR/fix-instructions.yaml"

python3 "$SKILL_DIR/scripts/decompose-content.py" \
  "$CONTENT_PATH" \
  "$SESSION_DIR/phase1/page-plan.yaml" \
  $FIX_CONTEXT_ARG

# Emit HTML
python3 "$SKILL_DIR/scripts/html-emit.py" \
  "$SESSION_DIR/phase1/page-plan.yaml" \
  "$SESSION_DIR/phase1/output.html" \
  --tokens "$SKILL_DIR/templates/tokens.css" \
  --templates "$SKILL_DIR/templates/page-templates"

# Pre-conversion QA gate
python3 "$SKILL_DIR/scripts/html-qa-gate.py" \
  "$SESSION_DIR/phase1/output.html" \
  "$SESSION_DIR/phase1/qa-report.yaml"

QA_VERDICT=$?
if [ $QA_VERDICT -ne 0 ]; then
  echo "HTML QA gate FAILED — see $SESSION_DIR/phase1/qa-report.yaml"
  exit 1
fi

# Propagate outputs for Phase 2
cp "$SESSION_DIR/phase1/output.html" "$SESSION_DIR/output.html"
cp "$SESSION_DIR/phase1/page-plan.yaml" "$SESSION_DIR/page-plan.yaml"

echo "Phase 1 complete"
```

## Outputs
- `{SESSION_DIR}/page-plan.yaml` — ordered list of page specs
- `{SESSION_DIR}/output.html` — self-contained Brad-styled HTML with empty photo slots
- `{SESSION_DIR}/phase1/qa-report.yaml` — Brad 22-item + 8-item coffee-table checklist results

## Fix-Context Channel (Wigum re-entry)
When Phase 4's Wigum loop fails and routes defects to decomposer/emitter/qa-gate, it writes `{SESSION_DIR}/fix-instructions.yaml` with per-stage guidance. Phase 1 passes this to `decompose-content.py --fix-context`.
