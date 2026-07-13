#!/usr/bin/env bash
# ic-launch.sh — start the FULL live Investment-Committee engine for ONE session, in its own tab.
#
# Everything here runs OFF the main Claude session: a warm `claude -p` pool (ic-pool.py) generates
# each seat's turn, ic-live.py routes chair commands to it, and ic-server.py serves + broadcasts the
# room. Because none of it goes through the main conversation, chatting in the main cmux tab never
# stops the committee. This tab OWNS the engine — closing it tears the engine down.
#
# Usage: ic-launch.sh <session-dir> [port]
set -u
CR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESS="$(cd "${1:?usage: ic-launch.sh <session-dir> [port]}" && pwd)"
PORT="${2:-8930}"
TAG="$(basename "$SESS")"
SOCK="/tmp/ic-pool-$TAG.sock"
POOL_LOG="/tmp/ic-pool-$TAG.log"
LIVE_LOG="/tmp/ic-live-$TAG.log"
unset ANTHROPIC_API_KEY   # Max subscription only — a set key would silently bill per-token

cleanup() {
  pkill -f "ic-pool.py --socket-path $SOCK" 2>/dev/null
  pkill -f "ic-live.py --session $SESS"     2>/dev/null
  rm -f "$SOCK"
}
trap cleanup EXIT INT TERM HUP

echo "════════ Investment Committee — live engine ════════"
echo "session : $SESS"
echo "room    : http://127.0.0.1:$PORT/"
echo "(keep this tab open — closing it stops the committee)"
echo

# make sure the served page reflects the latest template + this session's state
python3 "$CR/build_meeting.py" --session "$SESS" --out "$CR/meeting.html" >/dev/null 2>&1 || true

echo "[1/3] warming the claude pool (one-time init; ~5-15s)…"
: > "$POOL_LOG"
nohup python3 "$CR/ic-pool.py" --socket-path "$SOCK" --models sonnet,haiku >> "$POOL_LOG" 2>&1 &
ready=0
for _ in $(seq 1 150); do
  if grep -q pool_ready "$POOL_LOG" 2>/dev/null; then ready=1; break; fi
  if grep -q pool_failed "$POOL_LOG" 2>/dev/null; then echo "      POOL FAILED:"; cat "$POOL_LOG"; exit 1; fi
  sleep 1
done
[ "$ready" = 1 ] && echo "      pool ready." || { echo "      pool warmup timed out"; exit 1; }

echo "[2/3] starting the live consumer (moderator-free turn generation)…"
: > "$LIVE_LOG"
nohup python3 "$CR/ic-live.py" --session "$SESS" --socket "$SOCK" >> "$LIVE_LOG" 2>&1 &
echo "      consumer up."

echo "[3/3] serving the committee room — chair in the browser."
open -a "Google Chrome" "http://127.0.0.1:$PORT/" >/dev/null 2>&1 || true
# foreground (NOT exec) so the EXIT trap fires and tears the engine down when this tab closes
python3 "$CR/ic-server.py" --session "$SESS" --port "$PORT" --page meeting.html
