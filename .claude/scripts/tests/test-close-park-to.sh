#!/bin/bash
# Regression test — close-project.sh --park-to and the guarded orphan retire.
#
# CASE A: an EMPTY scratch row is retired after its work parks elsewhere.
# CASE B: a scratch row holding even ONE knowledge fact must NOT be retired.
#
# CASE B is the important one. On 2026-08-18 the FruitSync row a156b1b8 looked
# disposable and held 14 facts; retiring it would have put half a project's
# memory out of normal reach. The guard exists so that cannot happen silently.
#
# Runs entirely in a throwaway registry home; the real ~/.acos is never touched.
# Usage: bash .claude/scripts/tests/test-close-park-to.sh [resurrection-dir]

CLOSEDIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/scripts/resurrection}"
SCRATCH="11111111-0000-0000-0000-00000000aaaa"
TARGET="22222222-0000-0000-0000-00000000bbbb"
FAILED=0

setup() {  # $1 = seed a fact on the scratch row? yes/no
  T=$(mktemp -d)
  export ACOS_REGISTRY_HOME="$T" RESURRECTION_STATE_DIR="$T/state"
  export RESURRECTION_PROJECT_ROOT="$T/proj" RESURRECTION_SKIP_CMUX=1
  mkdir -p "$T/proj/.acos" "$T/state"
  printf '%s\n' "$SCRATCH" > "$T/proj/.acos/project-id"   # folder-level identity
  python3 - "$1" <<PY
import sys; sys.path.insert(0, "$CLOSEDIR")
import registry_lib, knowledge_lib
home = "$T"
registry_lib.upsert_row({"project_uuid": "$SCRATCH", "root": "$T/proj", "status": "active"}, home)
registry_lib.upsert_row({"project_uuid": "$TARGET", "root": "$T/proj",
                         "workspace_name": "Skill Workshop", "status": "active"}, home)
if sys.argv[1] == "yes":
    knowledge_lib.append_fact("$SCRATCH", {"kind":"machine","subject":"traps",
        "claim":"a real learning that must not be hidden",
        "evidence":{"type":"command","value":"echo x"}}, home=home)
PY
  printf 'next_action: file this scratch work onto Skill Workshop\n' > "$T/intent.txt"
}

run() {
  CMUX_WORKSPACE_ID="" bash "$CLOSEDIR/close-project.sh" \
    --intent-file "$T/intent.txt" --session-id "sandbox-sid-0001" --park-to "$TARGET" 2>&1
}

check() {  # $1 = expected scratch status, $2 = label
  got=$(python3 -c "
import sys; sys.path.insert(0,'$CLOSEDIR')
import registry_lib
print(registry_lib.load_row('$SCRATCH','$T')['status'])")
  if [ "$got" = "$1" ]; then echo "  scratch row: $got  (correct)"; else echo "  scratch row: $got  EXPECTED $1  <-- $2 FAILED"; FAILED=1; fi
}

echo "=== CASE A — empty scratch row: it should be retired ==="
setup no; run | grep -E "step 6b|step 7b|step 7  registry"
check tombstoned "CASE A"
python3 -c "
import sys; sys.path.insert(0,'$CLOSEDIR')
import registry_lib
t=registry_lib.load_row('$TARGET','$T')
print('  target row: %s, has last_close: %s' % (t['status'], bool(t['last_close'])))"
rm -rf "$T"

echo
echo "=== CASE B — scratch row holds 1 fact: the retire must be REFUSED ==="
setup yes; run | grep -E "step 6b|step 7b|Merge what it holds"
check active "CASE B"
rm -rf "$T"
exit "$FAILED"
