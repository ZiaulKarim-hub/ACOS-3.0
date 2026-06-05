#!/usr/bin/env bash
# verify-artifacts.sh — mechanical completeness + QA gate for acos-preeng-classic.
# Usage: verify-artifacts.sh <feature-dir>
# Exit 0 = all required artifacts present and no QA report REJECTED.
# Exit 2 = missing/empty artifact OR a *_qa_report.json with qa_status REJECTED*.
# Exit 1 = usage error.
#
# Fail-loud by design: this is the gate between the worker's output and the
# ACOS slice bridge. A silent pass on incomplete artifacts would push a broken
# plan into the lifecycle.

# NB: intentionally NOT `set -e`/`pipefail` — this is an accumulator gate that must
# keep going, collect every deficiency, and compute its own exit code at the end.
# `set -e` would abort on the first expected non-zero (e.g. find on a missing tasks/).
set -u

DIR="${1:-}"
if [[ -z "$DIR" || ! -d "$DIR" ]]; then
  echo "usage: verify-artifacts.sh <feature-dir>   (dir must exist)" >&2
  exit 1
fi

# Required single-file artifacts (non-empty).
REQUIRED=(
  spec.md
  research.md
  domain-brief.md
  domain-cqs.md
  domain-lattice.json
  evidence-ledger.json
  plan.md
  tech_prd.md
  data-model.md
  stories.json
  analysis-report.md
  cage_preeng_nodes.csv
  cage_preeng_edges.csv
  agent_instructions/pm.md
  agent_instructions/dev.md
  agent_instructions/qa.md
)

fail=0

for f in "${REQUIRED[@]}"; do
  if [[ ! -s "$DIR/$f" ]]; then
    echo "MISSING/EMPTY: $f"
    fail=1
  fi
done

# tasks/ must hold at least one task file.
task_count=$(find "$DIR/tasks" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
if [[ "${task_count:-0}" -lt 1 ]]; then
  echo "MISSING: tasks/ has no task files"
  fail=1
fi

# Any *_qa_report.json with a REJECTED status blocks the bridge.
while IFS= read -r qa; do
  [[ -z "$qa" ]] && continue
  if grep -Eq '"qa_status"[[:space:]]*:[[:space:]]*"REJECTED' "$qa"; then
    status=$(grep -Eo '"qa_status"[[:space:]]*:[[:space:]]*"[^"]*"' "$qa" | head -1)
    echo "QA REJECTED: $(basename "$qa") → $status"
    fail=1
  fi
done < <(find "$DIR" -maxdepth 1 -name '*_qa_report.json' 2>/dev/null)

if [[ "$fail" -ne 0 ]]; then
  echo "---"
  echo "RESULT: INCOMPLETE — do not bridge to slices until resolved."
  exit 2
fi

echo "RESULT: OK — $task_count task file(s), all required artifacts present, no QA rejections."
echo "Ready for Step 5 (bridge to ACOS slices)."
exit 0
