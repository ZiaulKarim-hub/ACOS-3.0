#!/bin/bash
# SubagentStop hook — logs agent completion for learning curve
mkdir -p ".acos/metrics"

AGENT=$(cat | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent_name','unknown'))" 2>/dev/null)

if [ -n "$AGENT" ]; then
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) COMPLETED $AGENT" >> ".acos/metrics/agent-completions.log"
fi

exit 0
