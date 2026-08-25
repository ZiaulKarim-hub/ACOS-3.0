#!/bin/bash
# Regression test — close-project.sh --park-to-new (Zee, 2026-08-24).
#
# The close menu's option 2 is "create a new row". Before this flag, `0` could
# only reuse the row the tab already had, which is filing onto something rather
# than creating anything. Zee's words: "the intention was not to replace
# anything, just to create a new row in an empty number."
#
# CASE A: the new row is MINTED, takes the next ledger number, and the work
#         files onto it.
# CASE B: the tab's OWN row is left completely untouched — not orphaned, not
#         retired, same status, same number. This is the half that distinguishes
#         --park-to-new from --park-to, and the half Zee named explicitly.
# CASE C: a name already used at this root is REFUSED. Creating is not reusing.
# CASE D: --park-to and --park-to-new together are REFUSED, not silently ranked.
# CASE E: on a tab that owns NO row, .acos/project-id must name a row that
#         EXISTS. The first cut of this flag left it naming the uuid the
#         resolution had merely pencilled in, which then never became a row —
#         MEASURED 2026-08-24: the file held a4dcacf4-... while the only row on
#         disk was 12fda98d-... A pointer that resolves to nothing would misfile
#         every later close of that folder.
#
# Runs entirely in a throwaway registry home; the real ~/.acos is never touched.
# Usage: bash .claude/scripts/tests/test-close-park-to-new.sh [resurrection-dir]

CLOSEDIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/scripts/resurrection}"
OWN="33333333-0000-0000-0000-00000000cccc"
OTHER="44444444-0000-0000-0000-00000000dddd"
FAILED=0

setup() {
  T=$(mktemp -d)
  export ACOS_REGISTRY_HOME="$T" RESURRECTION_STATE_DIR="$T/state"
  export RESURRECTION_PROJECT_ROOT="$T/proj" RESURRECTION_SKIP_CMUX=1
  mkdir -p "$T/proj/.acos" "$T/state"
  printf '%s\n' "$OWN" > "$T/proj/.acos/project-id"   # folder-level identity
  python3 - <<PY
import sys; sys.path.insert(0, "$CLOSEDIR")
import registry_lib
home = "$T"
registry_lib.upsert_row({"project_uuid": "$OWN", "root": "$T/proj", "status": "active"}, home)
registry_lib.upsert_row({"project_uuid": "$OTHER", "root": "$T/proj",
                         "workspace_name": "Taken Name", "status": "active"}, home)
PY
  printf 'next_action: file this work onto a brand new row of its own\n' > "$T/intent.txt"
}

run_new() {  # $1 = the new row's name
  CMUX_WORKSPACE_ID="" bash "$CLOSEDIR/close-project.sh" \
    --intent-file "$T/intent.txt" --session-id "sandbox-sid-0002" \
    --park-to-new "$1" 2>&1
}

ok()   { echo "  $1  (correct)"; }
bad()  { echo "  $1  <-- FAILED"; FAILED=1; }

echo "=== CASE A — the new row is minted and takes the next number ==="
setup
before=$(python3 -c "
import sys; sys.path.insert(0,'$CLOSEDIR')
import ordinal_lib
print(ordinal_lib.next_ordinal('$T'))")
run_new "Brand New Thing" | grep -E "park-to-new:|step 6b|step 7  registry"
got=$(python3 -c "
import sys, os, json; sys.path.insert(0,'$CLOSEDIR')
import registry_lib
d = registry_lib.registry_dir('$T')
hit = None
for f in sorted(os.listdir(d)):
    if not f.endswith('.json'): continue
    r = json.load(open(os.path.join(d, f)))
    if r.get('workspace_name') == 'Brand New Thing':
        hit = r
print('%s|%s|%s' % (hit['pick_ordinal'], hit['status'], bool(hit['last_close'])) if hit else 'MISSING')")
IFS='|' read -r gotord gotstatus gotclose <<< "$got"
[ "$gotord" = "$before" ] && ok "new row number: $gotord (= next_ordinal was $before)" \
                          || bad "new row number: $gotord EXPECTED $before"
[ "$gotstatus" = "parked" ] && ok "new row status: parked" || bad "new row status: $gotstatus EXPECTED parked"
[ "$gotclose" = "True" ]   && ok "new row carries last_close" || bad "new row has no last_close"

echo ""
echo "=== CASE B — this tab's OWN row is untouched (not orphaned, not retired) ==="
python3 -c "
import sys; sys.path.insert(0,'$CLOSEDIR')
import registry_lib
r = registry_lib.load_row('$OWN','$T')
print('%s|%s|%s' % (r['status'], r['pick_ordinal'], bool(r['last_close'])))" > "$T/own.txt"
IFS='|' read -r ownstatus ownord ownclose < "$T/own.txt"
[ "$ownstatus" = "active" ] && ok "own row status: active (never parked, never tombstoned)" \
                            || bad "own row status: $ownstatus EXPECTED active"
[ -n "$ownord" ] && ok "own row keeps number $ownord" || bad "own row lost its number"
[ "$ownclose" = "False" ] && ok "own row got NO last_close — the work went to the new row" \
                          || bad "own row was written to; it should have been untouched"

echo ""
echo "=== CASE C — a name already used at this root is refused ==="
setup
out=$(run_new "Taken Name")
echo "$out" | grep -q "already names a row at this root" \
  && ok "refused, and it names the clash" || bad "did not refuse a duplicate name"
echo "$out" | grep -q "Creating is not the same as reusing" \
  && ok "the refusal says why" || bad "the refusal gave no reason"

echo ""
echo "=== CASE D — --park-to and --park-to-new together are refused ==="
setup
out=$(CMUX_WORKSPACE_ID="" bash "$CLOSEDIR/close-project.sh" \
        --intent-file "$T/intent.txt" --session-id "sandbox-sid-0003" \
        --park-to "$OTHER" --park-to-new "Third Thing" 2>&1)
echo "$out" | grep -q "two different destinations" \
  && ok "refused rather than ranking one over the other" || bad "did not refuse the pair"

echo ""
echo "=== CASE E — a tab with NO row: the folder identity file must resolve ==="
T=$(mktemp -d)
export ACOS_REGISTRY_HOME="$T" RESURRECTION_STATE_DIR="$T/state"
export RESURRECTION_PROJECT_ROOT="$T/proj" RESURRECTION_SKIP_CMUX=1
mkdir -p "$T/proj" "$T/state"
printf 'next_action: file this work onto a brand new row of its own\n' > "$T/intent.txt"
run_new "Fresh Project" | grep -E "step 6b|project-id now names"
res=$(python3 -c "
import os, json
T = '$T'
pid = open(os.path.join(T, 'proj', '.acos', 'project-id')).read().strip()
d = os.path.join(T, '.acos', 'registry.d')
have = [json.load(open(os.path.join(d, f)))['project_uuid']
        for f in sorted(os.listdir(d)) if f.endswith('.json')]
print('%s|%s' % (pid in have, len(have)))")
IFS='|' read -r resolves nrows <<< "$res"
if [ "$resolves" = "True" ]; then ok "project-id names a row that exists"; else bad "project-id points at no row (dangling)"; fi
if [ "$nrows" = "1" ]; then ok "exactly one row was created, not two"; else bad "expected 1 row, found $nrows"; fi

echo ""
if [ "$FAILED" = "0" ]; then echo "ALL CASES PASSED"; else echo "SOME CASES FAILED"; fi
exit "$FAILED"
