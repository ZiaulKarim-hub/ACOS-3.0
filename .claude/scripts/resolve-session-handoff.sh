#!/bin/bash
# resolve-session-handoff.sh — given a session id, return the path to the
# handoff file in memory/handoffs/ that actually belongs to THAT session.
#
# Background (2026-08-09): every consumer of memory/handoffs/ used to pick
# a handoff with `ls -t memory/handoffs/*.md memory/handoffs/*.yaml | grep -v
# '\.resume\.md$' | head -1` — i.e. "whichever handoff file is newest,
# repo-wide, regardless of who wrote it." That is fine when only one
# session is active, but this project is routinely worked on by several
# Claude Code sessions/windows at once. When two sessions write a handoff
# within the same few minutes, the newest-wins rule can silently hand a
# session someone ELSE'S handoff. This is exactly what happened on
# 2026-08-08/09: session 26c28ec4-d9cc-435c-b8d7-ef50eddd33e9 needed its own
# handoff (memory/handoffs/2026-08-08-emergency-handoff-5.yaml) but the
# newest-wins rule grabbed session 71335b10-16c8-46e7-b5c8-3c16e0d0a5e4's
# handoff-6.yaml instead.
#
# Every handoff file has carried a top-level `session_id:` field recording
# who wrote it since well before this bug — the 2026-08-08 handoff-agent fix
# made that field reliably ACCURATE, but nothing downstream ever CHECKED it.
# This script is the one place that check now lives. Every consumer in the
# eternity-protocol subsystem should call this instead of doing its own
# `ls -t | head -1`.
#
# Usage:
#   HANDOFF=$(bash .claude/scripts/resolve-session-handoff.sh "$SESSION_ID") || exit 1
#
# Must be run from the project root (same convention as every other script
# in this subsystem — memory/handoffs/ is resolved relative to $PWD).
#
# On success: prints the matching handoff's path to stdout, exits 0.
# On failure: prints an error to stderr, exits 1. Never falls back to
# "just take the newest one anyway" — a wrong handoff is worse than none.

set -u

SESSION_ID="${1:-${SESSION_ID:-}}"
if [[ -z "$SESSION_ID" ]]; then
    echo "ERROR: resolve-session-handoff.sh requires a SESSION_ID (arg1 or \$SESSION_ID env var)" >&2
    exit 1
fi
[[ "$SESSION_ID" =~ ^[a-zA-Z0-9_-]{1,128}$ ]] || { echo "ERROR: invalid SESSION_ID: $SESSION_ID" >&2; exit 1; }

MATCH=""
while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    fsid=$(grep -m1 '^session_id:' "$f" 2>/dev/null | sed -E 's/^session_id:[[:space:]]*"?([^"[:space:]]*)"?.*/\1/')
    if [[ "$fsid" == "$SESSION_ID" ]]; then
        MATCH="$f"
        break
    fi
done < <(ls -t memory/handoffs/*.md memory/handoffs/*.yaml 2>/dev/null | grep -v '\.resume\.md$')

if [[ -z "$MATCH" ]]; then
    echo "ERROR: no handoff in memory/handoffs/ has session_id matching '$SESSION_ID' — the acos-handoff skill may not have run for this session yet, or ran before the 2026-08-08 session_id fix" >&2
    exit 1
fi

echo "$MATCH"
