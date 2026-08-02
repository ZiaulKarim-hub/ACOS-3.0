# SL-004-eden-04 — Re-arm across /clear (SessionStart)

**Story:** ST-004-eden-2 · **Epic:** EP-004-eden-2 · **Demo:** 1 · **Effort:** S · **Priority:** P0

## PM (Planner / LCE)
- **Objective (single):** Guarantee the active level survives `/clear` via a SessionStart (matcher
  `clear`) re-arm hook.
- **In-scope:** `eden-rearm.sh` registered on SessionStart matcher `clear`; ensures the directive is
  present immediately post-clear (state already on disk). Fail-open.
- **Out-of-scope:** cross-session persistence exclusion (that's SL-10's cleanup change).
- **Allowed files:** `.claude/scripts/eden-rearm.sh`, `.claude/settings.local.json`.
- **Definition of Done:** after `/clear`, the very next turn still reflects the active level (verified by
  the directive appearing); if off, no-op.

## Dev — Evidence Bundle
1. Re-arm hook. 2. Traceability (M4). 3. Test: set level → `/clear` → next turn shows the directive.
4. Off → no-op. 5. Fail-open. 6. Coexists with eternity's own SessionStart matcher `clear` hook. 7. Limitations.

## QA (Zero-Trust)
- Confirm the `/clear` path actually re-arms (not just a fresh SessionStart). Confirm it does not
  collide with `eternity-cmux-resume-inpane.sh` (same event+matcher).
- **Evidence gate:** reject if re-arm is unproven across an actual `/clear`, or if it disrupts eternity.

## Dev Learnings
_(to be filled)_

## QA Learnings
_(to be filled)_
