#!/bin/bash
# Regression test — eternity-resume-prepend.sh project-key gate (2026-08-18).
#
# Reproduces the 2026-08-18 incident: Research to Portfolio and FruitSync both
# ran in the "ACOS 3.0" folder AND both claimed cmux surface F354478B, so the
# folder gate and the surface gate both passed for each other's sessions and
# `ls -t` served FruitSync's handoff (session ff036fd7) to the R2P pane.
#
#   CASE 1 must be BLOCKED  — no cross-project serve.
#   CASE 2 must be SERVED   — the gate must not over-block a real same-project
#                             resume, which would silently break recovery.
#
# Runs inside a throwaway $HOME; the live state directory under
# ~/Library/Application Support/acos-token-monitor/state is never touched.
#
# Usage: bash .claude/scripts/tests/test-resume-project-gate.sh [hook-path]
#        exit 0 = both cases correct; exit 1 = a case failed.
# Sandboxed test for the project-key gate in eternity-resume-prepend.sh.
# Builds a fake HOME so the live state dir is never touched.
HOOK="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/scripts/eternity-resume-prepend.sh}"
LABEL="${2:-eternity-resume-prepend.sh project-key gate}"
FAILED=0
T=$(mktemp -d)
export HOME="$T"
CWD="/Users/zee/Documents/Vibe Coding/ACOS 3.0"
SAN=$(echo "$CWD" | tr '/' '-' | tr ' ' '-' | tr '.' '-')
PD="$T/.claude/projects/$SAN"
ST="$T/Library/Application Support/acos-token-monitor/state"
mkdir -p "$PD" "$ST"

A="aaaaaaaa-1111-2222-3333-444444444444"   # this pane   (project UUID-A)
B="bbbbbbbb-5555-6666-7777-888888888888"   # other project in the SAME folder
touch "$PD/$A.jsonl" "$PD/$B.jsonl"

# Both sessions claim the SAME surface — the real 2026-08-18 condition.
echo "SURF-SHARED" > "$ST/cmux-surface-$A"
echo "SURF-SHARED" > "$ST/cmux-surface-$B"

# Only B has a pending resume, and it is the newest file.
echo "RESUME-CONTENT-BELONGING-TO-PROJECT-B" > "$ST/pending-resume-$B.txt"

echo "PROJECT-UUID-A" > "$ST/project-$A"
echo "PROJECT-UUID-B" > "$ST/project-$B"

run() {
  printf '{"session_id":"%s","cwd":"%s"}' "$A" "$CWD" \
    | CMUX_SURFACE_ID="SURF-SHARED" bash "$HOOK" 2>/dev/null
}

echo "=== $LABEL ==="
OUT=$(run)
if echo "$OUT" | grep -q "PROJECT-B"; then
  echo "  CASE 1 (different projects): LEAKED  <-- project B's resume served to pane A"; FAILED=1
else
  echo "  CASE 1 (different projects): blocked"
fi

# Now make them the SAME project. The resume SHOULD be served.
rm -rf "$ST/consumed"; echo "RESUME-CONTENT-BELONGING-TO-PROJECT-B" > "$ST/pending-resume-$B.txt"
echo "PROJECT-UUID-A" > "$ST/project-$B"
OUT2=$(run)
if echo "$OUT2" | grep -q "PROJECT-B"; then
  echo "  CASE 2 (same project):      served  <-- correct, not over-blocked"
else
  echo "  CASE 2 (same project):      BLOCKED <-- over-blocked, regression"; FAILED=1
fi
rm -rf "$T"
exit "$FAILED"
