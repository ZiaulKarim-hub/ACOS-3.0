#!/bin/bash
# eternity-cmux-inpane.sh — IN-PANE Stop hook for cmux eternity auto-fire.
#
# WHY THIS EXISTS (2026-06-18):
# The token-watcher daemon is a DETACHED process (reparented to launchd, no
# controlling tty, outside the cmux pane's process tree). cmux's Unix socket
# ONLY accepts connections from a process running INSIDE a live pane, so the
# daemon's `cmux send` always fails with "Broken pipe". A Stop hook, by
# contrast, runs IN-PANE (child of claude), so its `cmux send` works.
#
# So we split responsibilities: the daemon DETECTS (writes .last-total-<sid>
# every event) and the skill GENERATES the handoff (writes .clear-requested-<sid>);
# this hook does the in-pane INJECTION that the daemon cannot.
#
# Activated only when the global marker state/.cmux-inpane-inject exists, and
# only for cmux sessions with a recorded surface. No-op otherwise (safe to wire
# globally for every session/project).
#
# Flow:
#   1. .clear-requested-<sid> (or its .failed sidecar the daemon renames it to)
#      present  ->  `cmux send /clear`  (the skill already produced the handoff)
#   2. else, .last-total-<sid> >= threshold and not already fired this session
#      ->  `cmux send /acos-eternity-protocol`  (Claude generates the handoff)

set +e
MON="$HOME/Library/Application Support/acos-token-monitor"
STATE="$MON/state"

# Gate 1: in-pane mode must be enabled.
[ -f "$STATE/.cmux-inpane-inject" ] || exit 0

# Session id from the hook's stdin payload.
INPUT=$(cat 2>/dev/null)
SID=$(printf '%s' "$INPUT" | python3 -c "import sys,json
try: print(json.load(sys.stdin).get('session_id',''))
except Exception: pass" 2>/dev/null)
[ -z "$SID" ] && exit 0
[[ "$SID" =~ ^[a-zA-Z0-9_-]{1,128}$ ]] || exit 0

# Must be a cmux session (surface recorded) and not opted out.
[ -f "$STATE/cmux-surface-$SID" ] || exit 0
[ -f "$STATE/stop-$SID" ] && exit 0

SURF="${CMUX_SURFACE_ID:-$(cat "$STATE/cmux-surface-$SID" 2>/dev/null)}"
[ -z "$SURF" ] && exit 0
CMUX="${CMUX_CLAUDE_HOOK_CMUX_BIN:-cmux}"
command -v "$CMUX" >/dev/null 2>&1 || CMUX="cmux"

# Send $1 to the surface and submit with a SEPARATE Enter keypress (2026-07-06 fix).
# cmux turns a trailing \n into Enter but delivers "text\n" as ONE burst, which Claude
# Code's TUI can treat as a bracketed PASTE — absorbing the newline as a soft-newline
# instead of submitting (observed live: injected text landed in the prompt but was
# never entered). Splitting the Enter into its own delayed send makes it a distinct
# keypress after the paste settles; a second Enter backstops the case where the first
# raced a still-busy frame (a stray Enter on an empty/submitted prompt is a harmless
# no-op). Returns the TEXT send's exit code — the submit Enters are best-effort.
send() {
    "$CMUX" send --surface "$SURF" -- "$1" >/dev/null 2>&1 || return 1
    sleep 0.4; "$CMUX" send --surface "$SURF" -- '\n' >/dev/null 2>&1
    sleep 0.4; "$CMUX" send --surface "$SURF" -- '\n' >/dev/null 2>&1
    return 0
}

# ── Priority 0: an /exit was requested (acos-complete finished archiving) ─────
# Mirrors the /clear split: the /acos-complete skill writes the surface-keyed
# request flag after archiving; this in-pane Stop hook does the actual
# `cmux send /exit` (the detached daemon cannot reach cmux's in-pane-only socket).
# Unlike /clear, /exit is TERMINAL — no re-arm, no .fired bookkeeping. Remove the
# flag BEFORE sending so a second Stop event can't type a stray second /exit.
if [ -f "$STATE/.exit-requested-surface-$SURF" ] || [ -f "$STATE/.exit-requested-$SID" ]; then
    rm -f "$STATE/.exit-requested-surface-$SURF" "$STATE/.exit-requested-$SID" 2>/dev/null
    send "/exit"
    exit 0
fi

# ── Priority 1: a /clear was requested (skill finished the handoff) ──────────
# Prefer a SURFACE-keyed flag: one cmux pane churns through many session ids
# (multiple transcripts / /clear cycles, sometimes two written near-simultaneously),
# but its surface ($SURF) is stable and BOTH this hook and the skill read it
# reliably. Fall back to the legacy sid-keyed flags.
# Determine which clear-request applies. The surface- and sid-keyed flags are the
# skill's own live output (it writes BOTH per cycle). The .failed sidecar is the
# DAEMON's give-up evidence — and in in-pane mode the daemon is detection-only and
# never creates it, so any .failed here is historical UNLESS very recent. Ghost
# .failed files persist on disk for weeks (nobody GC's them); honoring a stale one
# would drive a stray /clear with no matching handoff, so accept .failed only FRESH.
CR=""
for _c in "$STATE/.clear-requested-surface-$SURF" "$STATE/.clear-requested-$SID"; do
    [ -f "$_c" ] && { CR="$_c"; break; }
done
if [ -z "$CR" ] && [ -f "$STATE/.clear-requested-$SID.failed" ]; then
    _fm=$(stat -f %m "$STATE/.clear-requested-$SID.failed" 2>/dev/null || echo 0)
    [ $(( $(date +%s 2>/dev/null || echo 0) - _fm )) -lt 1800 ] && CR="$STATE/.clear-requested-$SID.failed"
fi
if [ -n "$CR" ]; then
    # Health-gate + VERIFY the /clear send BEFORE destroying recovery state
    # (2026-07-06 audit). The OLD code did a bare `send "/clear"` — return code
    # swallowed, no ping — then UNCONDITIONALLY wrote .clear-fired and removed the
    # flags + guard + .last-total. A silently-failed /clear then left the context
    # UN-cleared but all recovery state gone: the daemon rewrites .last-total (still
    # over threshold) → Priority-2 re-fires a fresh handoff = re-handoff/re-clear
    # THRASH, and the false .clear-fired fools the sibling resume hook's Gate-3 into
    # resuming an un-cleared session. So commit the bookkeeping ONLY on a verified
    # send; on failure leave the flags + guard + .last-total intact so the next Stop
    # retries THIS path (we exit 0 either way, never falling through to Priority-2).
    if "$CMUX" ping >/dev/null 2>&1; then
        if send "/clear"; then
            date -u +%Y-%m-%dT%H:%M:%SZ > "$STATE/.clear-fired-$SID" 2>/dev/null
            # Consume the WHOLE request set for this cycle, not just the matched flag.
            # The skill arms both a surface- and a sid-keyed flag; removing only the one
            # we matched leaves its twin to re-trigger a SECOND, context-destroying
            # /clear on the next Stop (cmux keeps the same surface + sid across /clear).
            rm -f "$STATE/.clear-requested-surface-$SURF" \
                  "$STATE/.clear-requested-$SID" \
                  "$STATE/.clear-requested-$SID.failed" 2>/dev/null
            # RE-ARM for the next cycle. cmux /clear keeps the SAME session id, so the once-per-session
            # .inpane-fired guard (set when we fired the handoff) would otherwise block every future
            # 400k crossing — the eternity loop would run exactly once. Drop the guard, and drop the now-
            # stale pre-clear total so we don't instantly re-fire on it: the next fire waits for the daemon
            # to write a fresh post-clear total that climbs back over the threshold.
            rm -f "$STATE/.inpane-fired-$SID" 2>/dev/null
            rm -f "$STATE/.last-total-$SID" 2>/dev/null
            # Recovered — reset the one-shot alert so a FUTURE failure can re-alert.
            rm -f "$STATE/.alerted-$SID" 2>/dev/null
        else
            # ESCALATE (2026-07-09): cmux is UP (ping OK) but the /clear SEND failed —
            # the target surface is unreachable/gone (cmux was restarted and this
            # session's surface id died, or the session moved out of cmux). Unlike a
            # cmux-down blip this will NOT self-heal, and if the session now goes idle
            # there is no next Stop to retry — the exact silent stall that stranded the
            # IC session. Raise the SAME alert channel the daemon uses (.eternity-ALERT
            # log + one-shot macOS notification via the shared .alerted-<sid> marker) so
            # the user knows to /clear manually. Leave the .clear-requested flag in place
            # so a later Stop still retries if the surface ever comes back.
            if [ ! -f "$STATE/.alerted-$SID" ]; then
                date -u +%Y-%m-%dT%H:%M:%SZ > "$STATE/.alerted-$SID" 2>/dev/null
                printf '%s  session=%s  in-pane /clear undeliverable — surface %s unreachable (cmux up, surface gone); /clear this pane manually  (in-pane Priority-1)\n' \
                    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$SID" "$SURF" >> "$STATE/.eternity-ALERT" 2>/dev/null
                osascript -e 'display notification "Eternity /clear could not be delivered — the cmux surface is gone. /clear this pane manually." with title "ACOS Eternity Protocol"' >/dev/null 2>&1 &
            fi
        fi
    fi
    # cmux DOWN (ping failed) → app itself is unreachable (may recover); leave the
    # flag + guard + .last-total intact so the next Stop retries. No alert here — a
    # transient cmux restart is expected to self-heal, and the daemon's own health
    # gate escalates a persistent cmux-down separately.
    exit 0
fi

# ── Priority 2: threshold crossed → trigger the handoff skill (once) ─────────
THRESH=$(grep -E '^threshold:' "$MON/config.yaml" 2>/dev/null | grep -oE '[0-9]+' | head -1)
[ -z "$THRESH" ] && THRESH=400000
TOTAL=$(grep -oE '[0-9]+' "$STATE/.last-total-$SID" 2>/dev/null | head -1)
[ -z "$TOTAL" ] && exit 0

GUARD="$STATE/.inpane-fired-$SID"

# Self-healing stale-guard reaper (2026-07-06 audit, revised after re-review). A
# healthy fire→/clear cycle REMOVES this guard within ~1-2 min (Priority-1 above) and
# drops tokens below threshold. A guard still present, over threshold, and older than
# the stale window means an earlier fire's cycle never completed — e.g. the send
# verified but the skill crashed before writing .clear-requested (the skill has
# several early exit paths). Nothing else recovers that: Priority-1 acts only on a
# live .clear-requested, and with the arm-after-verify fix a failed *send* no longer
# leaves a guard at all — so a lingering guard is a *silently-dead* fire. Reap it so
# the fire below can retry (the FruitSync Jul-5 / Jobsync Jun-30 stall class).
#
# We deliberately DO NOT gate this on .eternity-arming / .clear-requested markers.
# Those age from the SAME instant as the guard (arming is stamped once at the skill's
# Step 0, ≈ the guard's mtime, and is NEVER refreshed during generation), so an
# age-bounded marker check is mathematically REDUNDANT with GUARD_AGE — while a bare-
# existence check is actively harmful: a ghost arming/.failed file (left behind when
# the skill aborts before its Step-5 disarm; nothing physically unlinks it — dozens
# persist on disk for weeks) would block the reap FOREVER, re-opening the exact
# permanent-stall class this reaper exists to cure. A live *blocked* /clear is already
# protected upstream: if any .clear-requested* exists, Priority-1 matched it and
# exited before reaching here.
#
# Residual: a genuinely in-flight handoff whose GUARD_AGE exceeds the window (an
# extraordinarily long generation, or wall-clock inflated by a mid-handoff laptop
# sleep) is reaped and re-fired — a BOUNDED, self-correcting double-fire (the second
# /acos-eternity-protocol just regenerates the handoff; the first /clear to land
# wins). That is a deliberate, strictly-better trade than a permanent stall. The
# window is 2h so no realistic handoff (seconds-to-minutes) is ever near it, while a
# truly-dead guard still self-heals within 2h instead of never.
STALE_SECS=7200
if [ -f "$GUARD" ]; then
    GUARD_MTIME=$(stat -f %m "$GUARD" 2>/dev/null || echo 0)
    NOW=$(date +%s 2>/dev/null || echo 0)
    GUARD_AGE=$(( NOW - GUARD_MTIME ))
    if [ "$GUARD_AGE" -ge "$STALE_SECS" ] && [ "$TOTAL" -ge "$THRESH" ]; then
        rm -f "$GUARD" 2>/dev/null   # silently-dead fire — allow retry
    fi
fi

if [ "$TOTAL" -ge "$THRESH" ] && [ ! -f "$GUARD" ]; then
    # Arm-AFTER-verify + health gate (2026-07-06 audit): the OLD code did
    # `touch $GUARD` and THEN a blind `send`. If the send silently failed (cmux app
    # down / stale socket / PATH gap), the guard stayed armed forever and the
    # session fired exactly once then stalled permanently — the root cause of the
    # stuck FruitSync/Jobsync guards. Now: (1) gate on `cmux ping` so we never arm
    # when cmux is unreachable; (2) claim the guard optimistically so a concurrent
    # Stop event can't double-fire during the send window; (3) confirm the guard
    # with a timestamp ONLY on a verified send, and RELEASE it on failure so the
    # next Stop event retries. Mirrors eternity-cmux-resume-inpane.sh's pattern.
    if "$CMUX" ping >/dev/null 2>&1; then
        touch "$GUARD" 2>/dev/null
        if send "/acos-eternity-protocol"; then
            date -u +%Y-%m-%dT%H:%M:%SZ > "$GUARD" 2>/dev/null   # verified — confirm
        else
            rm -f "$GUARD" 2>/dev/null   # send failed — release so next Stop retries
        fi
    fi
    # cmux unhealthy → no arm, no fire; the next Stop event retries.
fi
exit 0
