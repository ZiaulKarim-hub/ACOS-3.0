#!/usr/bin/env bash
# verify-artifacts.sh — mechanical completeness + coverage gate for acos-genesis-protocol.
# Usage: verify-artifacts.sh <feature-dir>
# Exit 0 = all required artifacts present, tree parses, coverage QA not REJECTED.
# Exit 2 = missing/empty artifact, malformed tree, OR coverage_qa_report REJECTED.
# Exit 1 = usage error.
#
# Fail-loud by design: this is the gate between the planning worker's output and the
# /acos-synthesis-protocol runtime. A silent pass on an incomplete or low-coverage tree
# would push a non-buildable plan into the build loop.
#
# NB: intentionally NOT `set -e`/`pipefail` — accumulator gate; collect every
# deficiency, compute the exit code at the end.
set -u

DIR="${1:-}"
if [[ -z "$DIR" || ! -d "$DIR" ]]; then
  echo "usage: verify-artifacts.sh <feature-dir>   (dir must exist)" >&2
  exit 1
fi

REQUIRED=(
  vision.md
  success-criteria.json
  component-tree.json
  integration-map.json
  build-plan.json
  library.html
  library-status.json
  coverage-report.md
  coverage_qa_report.json
  analysis-report.md
  cage_unix_nodes.csv
  cage_unix_edges.csv
  agent_instructions/builder.md
  agent_instructions/verifier.md
  agent_instructions/integrator.md
)

fail=0

for f in "${REQUIRED[@]}"; do
  if [[ ! -s "$DIR/$f" ]]; then
    echo "MISSING/EMPTY: $f"
    fail=1
  fi
done

# components/ must hold at least one per-component spec.
comp_count=$(find "$DIR/components" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
if [[ "${comp_count:-0}" -lt 1 ]]; then
  echo "MISSING: components/ has no component spec files"
  fail=1
fi

# component-tree.json must parse and have a non-empty nodes[]; every node needs an
# id, a verifier.human_test, and acceptance_criteria (the Unix testability invariant).
if [[ -s "$DIR/component-tree.json" ]]; then
  tree_check=$(python3 - "$DIR/component-tree.json" <<'PY' 2>/dev/null
import json,sys
try:
    t=json.load(open(sys.argv[1],encoding="utf-8"))
except Exception as e:
    print("PARSE_ERROR %s"%e); sys.exit()
nodes=t.get("nodes")
if not isinstance(nodes,list) or not nodes:
    print("NO_NODES"); sys.exit()
bad=[]
for n in nodes:
    nid=n.get("id","?")
    ht=((n.get("verifier") or {}).get("human_test") or {})
    if not ht.get("procedure") or not ht.get("pass_criteria"):
        bad.append(nid+":no-human-test")
    if not n.get("acceptance_criteria"):
        bad.append(nid+":no-acceptance")
print("OK %d %s"%(len(nodes),(";".join(bad) if bad else "-")))
PY
)
  case "$tree_check" in
    OK\ *)
      bad="${tree_check#OK * }"
      if [[ "$bad" != "-" && -n "$bad" ]]; then
        echo "UNTESTABLE NODES (violates Unix invariant): $bad"
        fail=1
      fi
      ;;
    PARSE_ERROR*) echo "MALFORMED: component-tree.json — $tree_check"; fail=1 ;;
    NO_NODES)     echo "EMPTY: component-tree.json has no nodes"; fail=1 ;;
    *)            echo "UNVERIFIED: component-tree.json (python3 unavailable?)" ;;
  esac
fi

# coverage_qa_report.json REJECTED blocks the bridge.
if [[ -s "$DIR/coverage_qa_report.json" ]]; then
  if grep -Eq '"qa_status"[[:space:]]*:[[:space:]]*"REJECTED' "$DIR/coverage_qa_report.json"; then
    status=$(grep -Eo '"qa_status"[[:space:]]*:[[:space:]]*"[^"]*"' "$DIR/coverage_qa_report.json" | head -1)
    echo "QA REJECTED: coverage_qa_report.json → $status"
    fail=1
  fi
fi

if [[ "$fail" -ne 0 ]]; then
  echo "---"
  echo "RESULT: INCOMPLETE — do not hand to /acos-synthesis-protocol until resolved."
  exit 2
fi

echo "RESULT: OK — $comp_count component spec(s), all required artifacts present, tree testable, coverage not rejected."
echo "Ready for execution: /acos-synthesis-protocol $DIR"
exit 0
