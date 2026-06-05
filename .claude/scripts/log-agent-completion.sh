#!/bin/bash
# SubagentStop hook — logs agent completion for the learning curve / metrics.
#
# The SubagentStop payload provides `agent_type` (e.g. "developer", "qa-reviewer",
# "general-purpose") and `agent_id`. There is NO `agent_name` field — reading that
# is what logged "COMPLETED unknown" ~1988 times before the 2026-06-04 fix.
# Log format: "<ts> COMPLETED <agent_type> <agent_id>" (field 3 = agent identity).
mkdir -p ".acos/metrics"

INPUT=$(cat)
read -r AGENT AID <<EOF
$(printf '%s' "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent_type') or d.get('agent_name') or 'unknown', d.get('agent_id',''))" 2>/dev/null)
EOF

[ -z "$AGENT" ] && AGENT="unknown"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) COMPLETED $AGENT $AID" >> ".acos/metrics/agent-completions.log"

exit 0
