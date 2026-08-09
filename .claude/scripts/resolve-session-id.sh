#!/bin/bash
# resolve-session-id.sh — SINGLE SOURCE OF TRUTH for "which Claude Code
# session is this?"
#
# Background (2026-08-09): this exact question — "which session am I" —
# used to be answered independently, and inconsistently, in half a dozen
# places across the eternity-protocol subsystem (eternity-protocol-core.sh,
# acos-eternity-protocol/SKILL.md x3, acos-continue/SKILL.md,
# acos-resume-prompt/SKILL.md). Some copies had the 2026-07-06 pane-scoped
# fix, some had the ORIGINAL buggy `ls -t *.jsonl | head -1` heuristic
# (racy in a multi-session project — see
# reference_claude_code_session_id_authoritative memory note, reproduced
# live 2026-07-20 and again 2026-08-08/09). Two OTHER subsystems
# (acos-safe-close 2026-07-20, acos-handoff/handoff-agent 2026-08-08)
# independently discovered the actually-correct fix: Claude Code exports
# $CLAUDE_CODE_SESSION_ID into every Bash tool call, and it is authoritative
# — no heuristic needed. That fix never got backported into this
# subsystem's files, which is why the bug kept resurfacing after "being
# fixed" — every file had its own copy of the derivation, so fixing one
# copy never fixed the others.
#
# This script is the ONE place this logic now lives. Every consumer in the
# eternity-protocol subsystem should call this instead of embedding its own
# derivation. That way there is only ever one file to fix.
#
# Usage:
#   SESSION_ID=$(bash .claude/scripts/resolve-session-id.sh) || exit 1
#
# Resolution order:
#   1. $CMUX_ETERNITY_SESSION_ID — explicit human/operator pin, always wins.
#   2. $CLAUDE_CODE_SESSION_ID   — authoritative, exported by Claude Code
#      itself into every Bash tool call. Verified against its own transcript
#      file on disk before being trusted (defense in depth: a stale/copied
#      env var with no matching transcript is not trusted blindly).
#   3. Fallback heuristic (pre-2026-08 method, kept only for the rare case
#      $CLAUDE_CODE_SESSION_ID is unset) — pane-scoped via $CMUX_SURFACE_ID
#      when available, newest-transcript otherwise. Fails SAFE: if 2+
#      same-pane transcripts are freshly active (<90s) it refuses to guess.
#
# On success: prints the session id to stdout, exits 0.
# On failure: prints an error to stderr, exits 1. Never guesses silently.

set -u

SESSION_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
SESSION_ID=""

# ── 1. Explicit pin ─────────────────────────────────────────────────────
if [[ -n "${CMUX_ETERNITY_SESSION_ID:-}" ]]; then
    SESSION_ID="$CMUX_ETERNITY_SESSION_ID"

# ── 2. Authoritative: $CLAUDE_CODE_SESSION_ID ──────────────────────────
elif [[ -n "${CLAUDE_CODE_SESSION_ID:-}" && -f "$SESSION_DIR/${CLAUDE_CODE_SESSION_ID}.jsonl" ]]; then
    SESSION_ID="$CLAUDE_CODE_SESSION_ID"

# ── 3. Fallback: pane-scoped transcript-mtime heuristic ────────────────
else
    _ETS="$HOME/Library/Application Support/acos-token-monitor/state"
    _fresh=0; _now=$(date +%s)
    if [[ -n "${CMUX_SURFACE_ID:-}" ]]; then
        while IFS= read -r _j; do
            [[ -n "$_j" ]] || continue
            _s=$(basename "$_j" .jsonl)
            [[ "$(head -1 "$_ETS/cmux-surface-$_s" 2>/dev/null)" == "$CMUX_SURFACE_ID" ]] || continue
            [[ -z "$SESSION_ID" ]] && SESSION_ID="$_s"
            _m=$(stat -f %m "$_j" 2>/dev/null || stat -c %Y "$_j" 2>/dev/null)
            [[ -n "$_m" ]] && (( _now - _m < 90 )) && _fresh=$(( _fresh + 1 ))
        done < <(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null)
        if (( _fresh > 1 )); then
            echo "ERROR: \$CLAUDE_CODE_SESSION_ID is unset/stale, and $_fresh sessions in this cmux surface are freshly active — cannot safely pick one. Set CMUX_ETERNITY_SESSION_ID to override." >&2
            exit 1
        fi
    fi
    [[ -z "$SESSION_ID" ]] && SESSION_ID=$(basename "$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)" .jsonl 2>/dev/null)
fi

if [[ -z "$SESSION_ID" ]]; then
    echo "ERROR: could not determine session_id (no JSONL in $SESSION_DIR, and \$CLAUDE_CODE_SESSION_ID unset)" >&2
    exit 1
fi

# Mirror token-watcher.py's validation EXACTLY: ^[a-zA-Z0-9_-]{1,128}$.
[[ "$SESSION_ID" =~ ^[a-zA-Z0-9_-]{1,128}$ ]] || { echo "ERROR: invalid session_id: $SESSION_ID" >&2; exit 1; }

echo "$SESSION_ID"
