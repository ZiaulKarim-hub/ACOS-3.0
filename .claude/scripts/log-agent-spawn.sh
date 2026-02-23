#!/bin/bash
# SubagentStart hook — logs when a subagent is created
# Completes the agent lifecycle audit trail (paired with log-agent-completion.sh)
# Runs async — does not block agent creation
#
# Input: JSON with agent_name, agent_type, description, parent session info
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
    agent_name = data.get('agent_name', 'unknown')
    agent_type = data.get('agent_type', 'unknown')
    description = data.get('description', '')
    session_id = data.get('session_id', '')
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    log_line = f'{now} SPAWN agent={agent_name} type={agent_type} session={session_id} desc=\"{description[:100]}\"'
    print(log_line)
except Exception:
    pass
" <<< "$INPUT" >> "$LOG_FILE" 2>/dev/null

exit 0
