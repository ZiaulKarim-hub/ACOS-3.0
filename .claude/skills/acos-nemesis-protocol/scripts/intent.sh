#!/bin/bash
# intent.sh — what the acos-nemesis-protocol build MEANT (R-050). Exit 0 = every intent holds.
# Paths resolve from this file's location, so it runs unchanged in a worktree sandbox, in the
# merged tree under the merge gate (WORKTREE_INTENT set), and in the real project tree.
set -e
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$SKILL/../../.." && pwd)"
BUN=/Users/zee/.bun/bin/bun
MAKER="$ROOT/.claude/skills/acos-skill-maker"
fail() { echo "INTENT FAIL: $1"; exit 1; }

echo "[1] rulebook generated from source (never hand-edited)"
$BUN "$SKILL/scripts/build-rulebook.ts" --check | grep -q "fresh" || fail "rulebook stale"

echo "[2] no python under nemesis scripts"
[ -z "$(find "$SKILL/scripts" -name '*.py')" ] || fail "python found under nemesis scripts"

echo "[3] skill md names enforcement"
grep -q "^## Enforcement" "$SKILL/SKILL.md" || fail "SKILL.md lacks Enforcement section"

echo "[4] trace gate clean (design phase)"
$BUN "$MAKER/scripts/trace.ts" check "$SKILL/prd/TRACE.json" --phase design | grep -q "TRACE: clean" || fail "design-phase trace not clean"

echo "[5] selftest (all guarantees)"
$BUN "$SKILL/scripts/nemesis.ts" selftest | tail -1 | grep -q "selftest: all guarantees hold" || fail "nemesis selftest"

echo "[6] oracle: unreadable verdicts never allowed"
! grep -q 'reason: "oracle reply unparseable' "$ROOT/.claude/scripts/oracle/oracle-daemon.ts" || fail "oracle fallback allow still present"
grep -q "classifyFailure" "$ROOT/.claude/scripts/oracle/oracle-daemon.ts" || fail "oracle daemon lacks classifyFailure"
grep -q "classify_failure" "$ROOT/.claude/scripts/_oracle_judge.py" || fail "oracle direct layer lacks classify_failure"
python3 -c "import ast;ast.parse(open('$ROOT/.claude/scripts/_oracle_judge.py').read())" || fail "oracle python syntax"

echo "all nemesis intents hold"
