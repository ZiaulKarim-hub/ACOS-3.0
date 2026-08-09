#!/usr/bin/env python3
"""
Shared helpers for detecting eternity-protocol in-flight state.

Per user spec 2026-06-15: **Oracle Protocol is never above Eternity Protocol.**
Whenever any in-flight eternity marker exists for the current project's
sessions, every Oracle and autopilot hook must SUBORDINATE — stand down
entirely (plain allow / silent exit) until the markers clear. This module is
the single source of truth for that detection so all five hook scripts behave
identically.

In-flight markers (daemon-written; consumed/moved after handoff completes):
  - pending-resume-<sid>.txt    Resume content awaiting injection
  - .resume-pending-<sid>       Daemon arming flag (paired with pending-resume)
  - .compact-fired-<sid>        Compaction just fired (transitional)
  - .clear-requested-<sid>      cmux: daemon was asked to inject /clear
  - cmux-unhealthy-<sid>        cmux failed N consecutive injects; daemon
                                  paused dispatch for this session until cmux
                                  recovers (added 2026-06-15 — see the
                                  broken-pipe storm postmortem for why this
                                  is a critical autopilot brake)

Steady-state markers (NOT in-flight — explicitly ignored):
  - cmux-surface-<sid>          Per-session surface registration
  - pid-<pid>                    PID pointer
  - heartbeat                    Daemon liveness signal
  - consumed/                    Directory of finished artifacts

Why cmux-unhealthy is an in-flight marker (not steady-state):
  When cmux is unhealthy the daemon cannot auto-/clear, so any continued
  token generation pushes the session further past threshold with no
  recovery path until the user restarts cmux. Treating cmux-unhealthy as
  in-flight makes autopilot stand down — the session naturally idles until
  the user intervenes. Without this, autopilot would happily burn through
  600k+ tokens (the actual 2026-06-10 Auto-Blogger failure mode).

Project-scoping: a marker is "ours" iff its embedded session_id matches a
JSONL file in this project's ~/.claude/projects/<sanitized>/ directory. This
mirrors the canonical logic in .claude/scripts/eternity-resume-prepend.sh.

Fail-open: any error → False. Autopilot continues with normal behavior;
debug via the daemon's own logs.
"""

import time
from pathlib import Path


DAEMON_STATE = (
    Path.home() / "Library" / "Application Support" / "acos-token-monitor" / "state"
)

# 2026-06-24 (freeze-early): the eternity fire writes this marker as its VERY FIRST
# action — BEFORE acos-handoff (Step 0.5 in acos-eternity-protocol/SKILL.md) — so that
# Oracle + autopilot subordination covers the WHOLE sequence (handoff → resume → /clear),
# closing the Step-1→Step-2 window where new continuation work used to slip in AFTER the
# handoff snapshot was frozen (the stale-handoff failure mode).
#
# AUTONOMY GUARANTEE: this marker SELF-EXPIRES (age-GC, see _marker_is_live). If the fire
# ever crashes after arming but before /clear, the stale marker stops counting after
# ARMING_MARKER_TTL_SECONDS and autopilot resumes ON ITS OWN — it can NEVER freeze forever
# and depends on NO daemon action to clear. The /clear trigger path is untouched.
ARMING_MARKER_PREFIX = ".eternity-arming-"
ARMING_MARKER_TTL_SECONDS = 600  # 10 min — mirrors the skill's handoff-freshness window.

# 2026-08-06 ROOT-CAUSE FIX — the forever-freeze.
#
# The autonomy guarantee above (self-expiry) was written for the arming marker ONLY. Every
# other marker was treated as "daemon-managed: always counts while present", on the
# assumption the daemon always clears it. It does not always clear it. Observed live:
# TEN stale .compact-fired-* markers had accumulated in DAEMON_STATE, the oldest from
# 2026-06-15. Because they belong to sessions of THIS project, they matched, counted as
# live forever, and autopilot subordinated on EVERY Stop hook — iteration_count never left
# 0/150 across a three-hour run. The user's requirement is explicit: the work must never be
# stuck; after a /clear it must auto-continue.
#
# So the self-expiry principle now covers EVERY marker type. A genuine eternity fire runs
# its whole sequence (handoff -> resume -> /clear -> inject) in minutes, so a marker older
# than this TTL cannot belong to a live fire — the fire either finished or died. Ageing them
# out preserves the intended behaviour (subordinate DURING a real fire) while making a
# permanent freeze impossible, with no daemon action required.
#
# Deliberately generous (10x a normal fire) so a slow-but-real fire is never cut short.
# NOTE: this is a pure READ-side age check. No marker file is ever deleted here — in
# particular pending-resume-*.txt is left untouched on disk, so an aged-out resume can still
# be injected or recovered by hand.
DEFAULT_MARKER_TTL_SECONDS = 1800  # 30 min

# (filename_prefix, filename_suffix) — sid is the substring between them.
IN_FLIGHT_MARKERS = [
    ("pending-resume-", ".txt"),
    (".resume-pending-", ""),
    (".compact-fired-", ""),
    (".clear-requested-", ""),
    # 2026-06-15: cmux-unhealthy means the daemon cannot auto-clear; autopilot
    # must subordinate so we don't keep burning tokens into a session that can't
    # be cleared. Cleared by the daemon's pre-dispatch ping probe (auto-recover)
    # or manual `rm` after restarting cmux.
    ("cmux-unhealthy-", ""),
    # 2026-06-24: freeze-early arming marker (age-GC'd — see ARMING_MARKER_* above).
    (ARMING_MARKER_PREFIX, ""),
]


def _marker_is_live(entry, prefix):
    """Whether a matched marker file should still count as in-flight.

    EVERY marker type self-expires by mtime (2026-08-06). The arming marker keeps its
    tighter ARMING_MARKER_TTL_SECONDS; all others use DEFAULT_MARKER_TTL_SECONDS. This is
    a pure read (no unlink) — the autonomy guarantee lives entirely in this age check, so a
    crashed fire, a daemon that never cleaned up, or a marker left by a long-dead session
    can never freeze autopilot permanently.

    Errs toward NOT-live (don't freeze) on any stat failure: an unreadable or vanished
    marker is not a live freeze signal, and biasing toward autopilot-continues protects
    autonomy, which is the whole point of the guarantee.
    """
    ttl = (ARMING_MARKER_TTL_SECONDS if prefix == ARMING_MARKER_PREFIX
           else DEFAULT_MARKER_TTL_SECONDS)
    try:
        return (time.time() - entry.stat().st_mtime) <= ttl
    except OSError:
        return False


def project_session_ids(cwd):
    """Set of session_ids whose JSONL transcripts live in this project's
    Claude Code projects directory.

    Sanitization mirrors Claude Code's own: slashes/spaces/dots → dashes.
    """
    sanitized = str(cwd).replace("/", "-").replace(" ", "-").replace(".", "-")
    project_dir = Path.home() / ".claude" / "projects" / sanitized
    if not project_dir.is_dir():
        return set()
    return {p.stem for p in project_dir.glob("*.jsonl")}


def _extract_sid(marker_name, prefix, suffix):
    """Return the session_id portion of a marker filename, or None if no match."""
    if not marker_name.startswith(prefix):
        return None
    rest = marker_name[len(prefix):]
    if suffix:
        if not rest.endswith(suffix):
            return None
        rest = rest[: -len(suffix)]
    if not rest:
        return None
    return rest


def is_eternity_protocol_active(cwd):
    """True iff any in-flight eternity marker exists for THIS project's sessions.

    Returns False on any IO/permissions error — never raises. Calling hooks
    should treat False as "proceed with normal autopilot/Oracle behavior."
    """
    try:
        if not DAEMON_STATE.is_dir():
            return False
        sessions = project_session_ids(cwd)
        if not sessions:
            return False
        for entry in DAEMON_STATE.iterdir():
            name = entry.name
            for prefix, suffix in IN_FLIGHT_MARKERS:
                sid = _extract_sid(name, prefix, suffix)
                if sid and sid in sessions and _marker_is_live(entry, prefix):
                    return True
        return False
    except OSError:
        return False


def detect_eternity_marker(cwd):
    """Return (sid, marker_filename) of the FIRST in-flight marker matched,
    or (None, None) if not active. Useful for audit logging context.
    """
    try:
        if not DAEMON_STATE.is_dir():
            return None, None
        sessions = project_session_ids(cwd)
        if not sessions:
            return None, None
        for entry in DAEMON_STATE.iterdir():
            name = entry.name
            for prefix, suffix in IN_FLIGHT_MARKERS:
                sid = _extract_sid(name, prefix, suffix)
                if sid and sid in sessions and _marker_is_live(entry, prefix):
                    return sid, name
        return None, None
    except OSError:
        return None, None
