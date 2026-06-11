---
name: acos-eternity-protocol-stop
description: Opt the current session out of eternity protocol auto-fire at 400k tokens. Writes a session-scoped marker the daemon checks before firing either the cmux or warp variant. The marker is keyed to the CURRENT session ID — it is NOT actively cleaned (session-cleanup.sh only touches the project's .acos/state/, never the daemon's state/stop-<sid>), but any later session in this pane gets a new session ID and is therefore unaffected. Opt-out applies to THIS session only.
disable-model-invocation: false
user-invocable: true
allowed-tools: Bash
---

# ACOS Eternity Protocol — Stop (per-session opt-out)

## Overview

Disables auto-fire of the eternity protocol for the **current session only**.
After invoking this skill, the daemon will skip the 400k threshold-fire for
this session_id. Other panes / future sessions in this pane are unaffected —
not because the marker gets cleaned up (it doesn't; see Step 2's note), but
because it is keyed to *this* session ID and every later session in the pane
gets a fresh ID.

Use cases:
- You're in the middle of a delicate single-turn operation and don't want
  a /clear interrupting it
- You're testing something close to the threshold and want to override
- You're handing off to a colleague who'll take over this pane and don't
  want the protocol firing in between

## Execution Policy

Autonomous — invoking IS authorization. One bash block, no confirmation
prompts, no follow-up reasoning.

## Protocol

### Step 1: Resolve current session_id + write the opt-out marker

```bash
SESSION_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
JSONL=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$JSONL" .jsonl 2>/dev/null)
if [[ -z "$SESSION_ID" ]]; then
    echo "ERROR: could not determine session_id — no JSONL in $SESSION_DIR"
    exit 1
fi

STATE="$HOME/Library/Application Support/acos-token-monitor/state"
mkdir -p "$STATE"
STOP_MARKER="$STATE/stop-${SESSION_ID}"

# Atomic write: tmp + mv. Body records WHY we stopped so a future debugger
# (or the user reading the audit log) understands what happened.
TMP=$(mktemp "${STOP_MARKER}.XXXXXX")
cat > "$TMP" <<EOF
stopped_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
session_id: ${SESSION_ID}
stopped_by: acos-eternity-protocol-stop
scope: "session-only — keyed to this session_id; not actively cleaned"
EOF
mv "$TMP" "$STOP_MARKER"
chmod 600 "$STOP_MARKER" 2>/dev/null || true

if [[ ! -s "$STOP_MARKER" ]]; then
    echo "ERROR: failed to write stop marker at $STOP_MARKER"
    exit 1
fi

# Short session-id for the confirmation block (full UUID is noise).
SHORT_ID="${SESSION_ID:0:8}"
```

### Step 2: Print confirmation block

```bash
# Re-derive Step-1 vars: each fenced bash block runs in its OWN shell, so the
# $SESSION_ID / $SHORT_ID set in Step 1 are empty here.
SESSION_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
JSONL=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$JSONL" .jsonl 2>/dev/null)
SHORT_ID="${SESSION_ID:0:8}"

cat <<EOF

┌───────────────────────────────────────────────────────────────────────┐
│  Eternity protocol DISABLED for this session                          │
├───────────────────────────────────────────────────────────────────────┤
│  Session:  ${SHORT_ID}…                                                   │
│  Marker:   state/stop-${SESSION_ID}                                       │
│  Scope:    THIS session only (other panes unaffected)                 │
│                                                                       │
│  • Daemon will SKIP the 400k auto-fire for this session.              │
│  • The marker is NOT auto-cleaned — it persists on disk, but is       │
│    inert: it is keyed to THIS session id, and any later session       │
│    in this pane gets a new id and ignores it.                         │
│  • To re-enable mid-session: delete the marker file above.            │
└───────────────────────────────────────────────────────────────────────┘
EOF
```

### Step 3: Exit cleanly

Skill is complete. No follow-up work.

---

*ACOS Eternity Protocol Stop — per-session opt-out from the 400k auto-fire.*
