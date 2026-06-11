#!/bin/bash
# SubagentStart hook — logs when a subagent is created
# Completes the agent lifecycle audit trail (paired with log-agent-completion.sh)
# Runs async — does not block agent creation
#
# Input: JSON with agent_type, agent_id, description, parent session info
#        (no agent_name field exists in the payload — see line ~24)
# Output: Appends to .acos/state/agent-lifecycle.log

set -euo pipefail

STATE_DIR=".acos/state"
LOG_FILE="$STATE_DIR/agent-lifecycle.log"
mkdir -p "$STATE_DIR"

INPUT=$(cat)

# Extract agent info
python3 -c "
import sys, json
from datetime import datetime, timezone

try:
    data = json.load(sys.stdin)
    # Payload provides agent_type + agent_id; there is no agent_name field.
    def _clean(v):
        return str(v).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

    agent_type = _clean(data.get('agent_type') or data.get('agent_name') or 'unknown')
    agent_id = _clean(data.get('agent_id', ''))
    description = _clean(data.get('description', ''))
    session_id = _clean(data.get('session_id', ''))
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    desc_json = json.dumps(description[:100])
    log_line = f'{now} SPAWN agent={agent_type} id={agent_id} session={session_id} desc={desc_json}'
    print(log_line)
except Exception:
    pass
" <<< "$INPUT" >> "$LOG_FILE" 2>/dev/null

exit 0
