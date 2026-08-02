#!/bin/bash
# eternity-protocol-core.sh
#
# Shared post-skill plumbing for the eternity protocol variants (cmux + warp).
#
# Both variants follow the same pre-clear orchestration:
#   1. acos-handoff skill writes a handoff yaml.
#   2. acos-resume-prompt skill writes state/pending-resume-<sid>.txt.
#   3. THIS SCRIPT (sourced or executed by the variant SKILL.md) handles the
#      rest: verify both artifacts exist, capture the pre-clear token total
#      from the watcher log, and atomically write state/.resume-pending-<sid>
#      with the daemon-consumed metadata.
#
# After this script returns successfully, the cmux variant goes on to write
# state/.clear-requested-<sid> (daemon-side automation), while the warp
# variant prints a visible block and stops (user-driven manual /clear).
#
# Modes:
#   - sourced (.) — exports vars for the caller to use: $RESUME_FILE,
#     $PRE_CLEAR_TOTAL, $HANDOFF, $RESUME_PENDING, $SESSION_ID.
#   - executed   — same work but exits non-zero on error; caller uses $?.
#
# Created 2026-05-28 as part of the -cmux + -warp variant split.

# ── Idempotency: refuse to double-run inside the same shell ────────────────
if [[ -n "$ETERNITY_PROTOCOL_CORE_RAN" ]]; then
    echo "ERROR: eternity-protocol-core.sh already ran in this shell — refusing to re-execute" >&2
    return 1 2>/dev/null || exit 1
fi
export ETERNITY_PROTOCOL_CORE_RAN=1

# ── Resolve session_id ─────────────────────────────────────────────────────
# Same sanitization pattern Claude Code uses for project-dir names:
# slashes/spaces/dots → dashes. The newest *.jsonl in that dir is this session.
SESSION_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
# 2026-07-06 ROBUST, PANE-SCOPED session-id derivation (mirrors the skill fix).
# The old `ls -t *.jsonl | head -1` was RACY in a multi-session project and could
# resolve a DIFFERENT (superseded) same-pane session, arming /clear + resume for
# the WRONG session. Honor an explicit CMUX_ETERNITY_SESSION_ID pin; else scope to
# THIS pane ($CMUX_SURFACE_ID) + newest surface-matching transcript; fail SAFE if
# 2+ same-pane transcripts are freshly active (<90s).
_ETS="$HOME/Library/Application Support/acos-token-monitor/state"
SESSION_ID="${CMUX_ETERNITY_SESSION_ID:-}"; _fresh=0; _now=$(date +%s)
if [[ -z "$SESSION_ID" && -n "${CMUX_SURFACE_ID:-}" ]]; then
    while IFS= read -r _j; do
        [[ -n "$_j" ]] || continue
        _s=$(basename "$_j" .jsonl)
        [[ "$(head -1 "$_ETS/cmux-surface-$_s" 2>/dev/null)" == "$CMUX_SURFACE_ID" ]] || continue
        [[ -z "$SESSION_ID" ]] && SESSION_ID="$_s"
        _m=$(stat -f %m "$_j" 2>/dev/null || stat -c %Y "$_j" 2>/dev/null)
        [[ -n "$_m" ]] && (( _now - _m < 90 )) && _fresh=$(( _fresh + 1 ))
    done < <(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null)
    if (( _fresh > 1 )); then
        echo "ERROR: $_fresh sessions in this cmux surface are freshly active — cannot safely pick the current one; aborting (set CMUX_ETERNITY_SESSION_ID to override)" >&2
        return 1 2>/dev/null || exit 1
    fi
fi
[[ -z "$SESSION_ID" ]] && SESSION_ID=$(basename "$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)" .jsonl 2>/dev/null)
JSONL="$SESSION_DIR/$SESSION_ID.jsonl"
if [[ -z "$SESSION_ID" ]]; then
    echo "ERROR: could not determine session_id (no JSONL in $SESSION_DIR)" >&2
    return 1 2>/dev/null || exit 1
fi
# Mirror token-watcher.py's validation EXACTLY: ^[a-zA-Z0-9_-]{1,128}$. A real
# Claude session id is a UUID, which always passes — this can never reject an
# id Python already accepted. A failure here means the derivation is broken
# (and SESSION_ID is about to be used in paths/heredocs), so refuse loudly.
[[ "$SESSION_ID" =~ ^[a-zA-Z0-9_-]{1,128}$ ]] || { echo "ERROR: invalid session_id: $SESSION_ID" >&2; return 1 2>/dev/null || exit 1; }
export SESSION_ID

STATE="$HOME/Library/Application Support/acos-token-monitor/state"
LOGS="$HOME/Library/Application Support/acos-token-monitor/logs"

# ── Verify Step 1 artifact: a fresh handoff was created ───────────────────
# 2026-06-10 fix: accept BOTH .md and .yaml handoffs (acos-handoff was updated
# at some point to emit .md, but this script was still hardcoded to .yaml,
# blocking all variant fires when only .md handoffs existed). Both globs run
# in parallel; stderr suppressed to avoid "no matches" noise from either one
# when its extension isn't present.
#
# 2026-06-11 fix: exclude eternity `.resume.md` siblings. They are resume-PROMPT
# copies (written below at RESUME_SIBLING), NOT session handoffs. Without this,
# `ls -t` can return a `*.resume.md` as the newest, so HANDOFF points at a
# resume-prompt copy and the downstream basename strip (~line 200) produces a
# doubled `...resume.resume.md` pointer to a nonexistent file. Mirrors
# context-monitor.sh's `case "$f" in *.resume.md) continue;; esac` exclusion.
HANDOFF=$(ls -t memory/handoffs/*.md memory/handoffs/*.yaml 2>/dev/null | grep -v '\.resume\.md$' | head -1)
if [[ ! -s "$HANDOFF" ]]; then
    echo "ERROR: no handoff produced — expected newest .md or .yaml in memory/handoffs/" >&2
    return 1 2>/dev/null || exit 1
fi
# Freshness check: handoff should have been written in the last 5 minutes.
# Older means the acos-handoff skill probably no-op'd and we're about to arm
# the daemon with a stale-context resume — refuse and surface the error.
HANDOFF_AGE=$(( $(date +%s) - $(stat -f%m "$HANDOFF") ))
if [[ $HANDOFF_AGE -gt 300 ]]; then
    echo "ERROR: newest handoff is ${HANDOFF_AGE}s old (>300s) — acos-handoff may have failed to write" >&2
    echo "       handoff: $HANDOFF" >&2
    return 1 2>/dev/null || exit 1
fi
export HANDOFF

# ── Verify Step 2 artifact: resume prompt for this session exists ─────────
RESUME_FILE="$STATE/pending-resume-${SESSION_ID}.txt"
if [[ ! -s "$RESUME_FILE" ]]; then
    echo "ERROR: resume prompt missing or empty at $RESUME_FILE" >&2
    echo "       acos-resume-prompt skill may have failed" >&2
    return 1 2>/dev/null || exit 1
fi
export RESUME_FILE

# ── 2026-06-24 GIT-STATE CAPTURE (inform-only, fail-open) ─────────────────
# The handoff is a point-in-time snapshot. Work committed/edited AFTER it was written
# (e.g. autopilot units produced in the lead-up to /clear) is otherwise invisible to the
# resumed session — the stale-handoff failure mode. Append a DETERMINISTIC git snapshot to
# the resume content (which the daemon injects, and which is copied to the archival
# .resume.md sibling below) so the next session can DETECT drift (HEAD advanced / dirty
# tree) and reconcile from git before trusting the handoff's "completed" claims.
#
# AUTONOMY: pure information. This NEVER commits, stashes, refuses, or blocks /clear — any
# git error or non-repo simply skips the block. /clear fires exactly as before.
if git -C "$PWD" rev-parse --git-dir >/dev/null 2>&1; then
    GS_HEAD=$(git -C "$PWD" rev-parse --short=12 HEAD 2>/dev/null)
    GS_BRANCH=$(git -C "$PWD" rev-parse --abbrev-ref HEAD 2>/dev/null)
    GS_DIRTY=$(git -C "$PWD" status --porcelain 2>/dev/null)
    if [[ -n "$GS_DIRTY" ]]; then
        GS_DIRTY_COUNT=$(printf '%s\n' "$GS_DIRTY" | grep -c .)
    else
        GS_DIRTY_COUNT=0
    fi
    {
        printf '\n\n---\n## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)\n'
        printf 'At /clear time the repository was:\n'
        printf -- '- branch: `%s`\n' "${GS_BRANCH:-?}"
        printf -- '- HEAD: `%s`\n'   "${GS_HEAD:-?}"
        printf -- '- uncommitted changes: %s file(s)\n' "${GS_DIRTY_COUNT}"
        if [[ "${GS_DIRTY_COUNT}" -gt 0 ]]; then
            printf '\nUncommitted working-tree files (these are in NO handoff — inspect FIRST):\n```\n'
            # 2026-07-18 (SLICE-RES-01): the old `head -40` silently hid every
            # file past 40 INSIDE a block captioned "inspect FIRST" (74 dirty
            # files → 34 invisible). List up to 200; past that, say so LOUDLY —
            # a truncated list must never read as a complete one.
            printf '%s\n' "$GS_DIRTY" | head -200
            if [[ "${GS_DIRTY_COUNT}" -gt 200 ]]; then
                printf -- '... (listed 200 of %s — TRUNCATED; run `git status --porcelain` for the rest)\n' "${GS_DIRTY_COUNT}"
            fi
            printf '```\n'
        fi
        printf '\nRecent commits at fire time:\n```\n'
        git -C "$PWD" log --oneline -8 2>/dev/null
        printf '```\n'
        printf '\n**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `%s`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)\n' "${GS_HEAD:-?}"
    } >> "$RESUME_FILE" 2>/dev/null \
        && echo "Git-state snapshot appended to resume (HEAD ${GS_HEAD:-?}, ${GS_DIRTY_COUNT} dirty)." \
        || echo "WARN: git-state snapshot append failed — resume still valid (non-fatal)."
else
    echo "Not a git repo — skipping git-state snapshot (non-fatal; resume unaffected)."
fi

# ── Step 3: capture pre-clear token total (fallback chain) ────────────────
# Authoritative source is the daemon's per-session .last-total marker, written
# atomically on every JSONL event (single line, ASCII integer). When that's
# unavailable we degrade through progressively weaker fallbacks and flag the
# result as defaulted so the daemon can warn.
#
# Fallback order:
#   1. STATE/.last-total-<sid>          (real measured total — normal path)
#   2. watcher log scrape of approx=    (secondary, kept from prior behavior)
#   3. config.yaml `threshold: N`       (configured threshold, not measured)
#   4. hardcoded 400000                 (last resort)
#
# PRE_CLEAR_DEFAULTED is set to 1 for cases 2–4 (anything that is NOT a real
# .last-total measurement) so the .resume-pending sidecar gets the
# `pre_compact_total_defaulted: true` line per the daemon contract.
PRE_CLEAR_TOTAL=""
PRE_CLEAR_DEFAULTED=0

# --- 1. authoritative .last-total marker ---
LAST_TOTAL_FILE="$STATE/.last-total-${SESSION_ID}"
if [[ -s "$LAST_TOTAL_FILE" ]]; then
    CANDIDATE=$(tr -d '[:space:]' < "$LAST_TOTAL_FILE" 2>/dev/null)
    if [[ "$CANDIDATE" =~ ^[0-9]+$ ]]; then
        PRE_CLEAR_TOTAL="$CANDIDATE"
    fi
fi

# --- 2. watcher log scrape (secondary) ---
WATCHER_LOG="$LOGS/${SESSION_ID}.log"
if [[ -z "$PRE_CLEAR_TOTAL" ]]; then
    CANDIDATE=$(tail -100 "$WATCHER_LOG" 2>/dev/null \
        | grep -oE 'approx=\s*[0-9,]+' \
        | tail -1 | grep -oE '[0-9,]+' | tr -d ',')
    if [[ -n "$CANDIDATE" ]]; then
        PRE_CLEAR_TOTAL="$CANDIDATE"
        PRE_CLEAR_DEFAULTED=1
        echo "WARN: .last-total-${SESSION_ID} unavailable — used watcher-log scrape fallback (${PRE_CLEAR_TOTAL})" >&2
    fi
fi

# --- 3. configured threshold from config.yaml ---
if [[ -z "$PRE_CLEAR_TOTAL" ]]; then
    CONFIG_YAML="$HOME/Library/Application Support/acos-token-monitor/config.yaml"
    if [[ -f "$CONFIG_YAML" ]]; then
        # Grab the first `threshold:` line, strip the key, trailing comments,
        # and all whitespace; validate it is a pure integer before trusting it.
        CANDIDATE=$(grep -E '^[[:space:]]*threshold:' "$CONFIG_YAML" 2>/dev/null \
            | head -1 \
            | sed -E 's/^[[:space:]]*threshold:[[:space:]]*//; s/#.*$//' \
            | tr -d '[:space:]')
        if [[ "$CANDIDATE" =~ ^[0-9]+$ ]]; then
            PRE_CLEAR_TOTAL="$CANDIDATE"
            PRE_CLEAR_DEFAULTED=1
            echo "WARN: no .last-total and no log scrape — used configured threshold fallback from config.yaml (${PRE_CLEAR_TOTAL})" >&2
        fi
    fi
fi

# --- 4. hardcoded last resort ---
if [[ -z "$PRE_CLEAR_TOTAL" ]]; then
    PRE_CLEAR_TOTAL=400000
    PRE_CLEAR_DEFAULTED=1
    echo "WARN: all pre-clear total sources failed (.last-total, log scrape, config.yaml) — defaulting to 400000" >&2
fi
export PRE_CLEAR_TOTAL PRE_CLEAR_DEFAULTED

# ── Step 4: arm the daemon — write .resume-pending-<sid> atomically ───────
PROJECT_DIR_KEY=$(basename "$SESSION_DIR")
RESUME_PENDING="$STATE/.resume-pending-${SESSION_ID}"
TMP=$(mktemp "${RESUME_PENDING}.XXXXXX")
cat > "$TMP" <<EOF
pre_compact_total: ${PRE_CLEAR_TOTAL}
resume_prompt_file: ${RESUME_FILE}
project_dir_key: ${PROJECT_DIR_KEY}
armed_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
armed_by: ${ETERNITY_PROTOCOL_VARIANT:-unknown}
EOF
# Per the daemon contract: when pre_compact_total did NOT come from a real
# .last-total measurement (i.e. any of the fallbacks fired), append the
# defaulted marker so the daemon parses it and logs a warning.
if [[ "${PRE_CLEAR_DEFAULTED:-0}" == "1" ]]; then
    echo "pre_compact_total_defaulted: true" >> "$TMP"
fi
mv "$TMP" "$RESUME_PENDING"
chmod 600 "$RESUME_PENDING" 2>/dev/null || true
export RESUME_PENDING

# ── Sanity: confirm what we just wrote is on disk ─────────────────────────
if [[ ! -s "$RESUME_PENDING" ]]; then
    echo "ERROR: failed to write .resume-pending file at $RESUME_PENDING" >&2
    return 1 2>/dev/null || exit 1
fi

# ── Step 5 (2026-06-04): handoff-paired resume sibling + per-PID pointer ──
# Solves the "any time" resume problem: when the user types
# /acos-eternity-protocol-resume hours or days after the warp/cmux fire,
# the resume skill needs to find the correct handoff for THIS pane.
#
# Mechanism:
#   - Copy the resume prompt content next to the handoff yaml as a sibling
#     `.resume.md` file. This file lives in memory/handoffs/ forever — never
#     auto-consumed. Acts as the authoritative, archival resume artifact.
#   - Write a tiny per-claude-PID pointer file containing the handoff basename.
#     The pointer is keyed by claude OS PID (which survives /clear in the same
#     pane — claude PID stays stable until the claude process is restarted).
#     Different panes have different PIDs → no cross-pane interference.
#   - The resume skill reads the pointer for the current pane's claude PID to
#     find the correct handoff sibling. Atomic, unambiguous, even days later.
#
# Backward compat: state/pending-resume-<sid>.txt is STILL written above. The
# resume skill falls back to it if the pointer or sibling is missing.

# Strip whichever extension is present (.md OR .yaml). basename takes a single
# suffix arg, so we run the right one based on what we found.
case "$HANDOFF" in
    *.md)   HANDOFF_BASENAME=$(basename "$HANDOFF" .md) ;;
    *.yaml) HANDOFF_BASENAME=$(basename "$HANDOFF" .yaml) ;;
    *)      HANDOFF_BASENAME=$(basename "$HANDOFF") ;;
esac
RESUME_SIBLING="memory/handoffs/${HANDOFF_BASENAME}.resume.md"

# Copy resume content to the sibling. cp preserves contents; never modifies
# the original pending-resume file (which legacy paths still need).
if cp "$RESUME_FILE" "$RESUME_SIBLING" 2>/dev/null; then
    chmod 644 "$RESUME_SIBLING" 2>/dev/null || true
else
    echo "WARN: failed to write handoff-paired resume sibling at $RESUME_SIBLING" >&2
    # Non-fatal: legacy pending-resume-<sid>.txt path still works.
fi
export RESUME_SIBLING HANDOFF_BASENAME

# Per-claude-PID pointer. Resolves the user's "how do I make sure the correct
# handoff is loaded no matter when I run resume" concern: PID is the only
# identifier stable across /clear within the same pane.
CLAUDE_PID=""
CLAUDE_LSTART=""
PID_FILE="$STATE/pid-${SESSION_ID}"
if [[ -f "$PID_FILE" ]]; then
    CLAUDE_PID=$(head -1 "$PID_FILE" 2>/dev/null)
    # Validate before it's used to build the pointer path. A non-numeric value
    # (corrupt pid file) must not become part of a filename. On failure, blank
    # it so the code below falls through to the pick-from-list pointer fallback
    # (log-and-proceed — never abort the auto-loop over a bad pointer write).
    if [[ -n "$CLAUDE_PID" ]] && ! [[ "$CLAUDE_PID" =~ ^[0-9]+$ ]]; then
        echo "WARN: pid file $PID_FILE held non-numeric value '$CLAUDE_PID' — ignoring; resume skill will use pick-from-list fallback" >&2
        CLAUDE_PID=""
    fi
    # Line 2 of the pid file is the process start time (lstart) recorded by
    # register-session-pid.sh. Carrying it into the pointer lets the resume
    # skill detect PID reuse (claude exited, OS recycled the PID for an
    # unrelated process) and refuse a stale pointer.
    CLAUDE_LSTART=$(sed -n '2p' "$PID_FILE" 2>/dev/null)
fi
if [[ -n "$CLAUDE_PID" ]]; then
    POINTER="$STATE/.eternity-pointer-pid-${CLAUDE_PID}"
    TMP_PTR=$(mktemp "${POINTER}.XXXXXX")
    cat > "$TMP_PTR" <<EOF
handoff_basename: ${HANDOFF_BASENAME}
resume_sibling: ${RESUME_SIBLING}
session_id_at_write: ${SESSION_ID}
project_dir_key: ${PROJECT_DIR_KEY}
claude_pid: ${CLAUDE_PID}
claude_lstart: ${CLAUDE_LSTART}
written_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
written_by: ${ETERNITY_PROTOCOL_VARIANT:-unknown}
EOF
    mv "$TMP_PTR" "$POINTER"
    chmod 600 "$POINTER" 2>/dev/null || true
    export ETERNITY_POINTER="$POINTER"
else
    echo "WARN: could not resolve claude PID for pointer write (pid file missing); resume skill will use pick-from-list fallback" >&2
fi

# ── Success: caller now has handoff + resume_file + sibling + pointer ─────
# Caller diverges from here based on variant (cmux vs warp).
return 0 2>/dev/null || exit 0
