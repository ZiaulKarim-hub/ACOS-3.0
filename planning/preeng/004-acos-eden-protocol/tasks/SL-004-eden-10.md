# SL-004-eden-10 — Cross-session persistence, status UX & docs

**Story:** ST-004-eden-5 · **Epic:** EP-004-eden-5 · **Demo:** 3+ · **Effort:** M · **Priority:** P1/P2

## PM (Planner / LCE)
- **Objective (single):** Make the level persist across sessions, polish discoverability, and document
  the whole skill.
- **In-scope:** modify `session-cleanup.sh` to EXCLUDE `.acos/state/eden-level` from SessionEnd purge;
  the one-time banner on level change; `status` output + first-use grammar table; SKILL.md docs
  (grammar, levels, fidelity floor, non-guarantees); `.gitignore` for the state file.
- **Out-of-scope:** engine behavior (earlier slices).
- **Allowed files:** `.claude/scripts/session-cleanup.sh` (additive exclusion — human-reviewed),
  `~/.claude/skills/acos-eden-protocol/SKILL.md`, `.gitignore`.
- **Definition of Done:** level survives SessionEnd (not purged); change→banner once; `status` reports
  clearly; docs state all non-guarantees (heuristic self-check, U1 assumption, L1/L2 interpolation).

## Dev — Evidence Bundle
1. The cleanup exclusion diff (additive). 2. Traceability (M3 persistence, S5, R6). 3. Test: set level →
  end session → new session still has it. 4. Banner-on-change demo. 5. `status` output. 6. Docs excerpt
  with non-guarantees. 7. Limitations.

## QA (Zero-Trust)
- Confirm the cleanup change is additive (an exclusion) and does not disturb other purges.
- Confirm docs state the non-guarantees honestly. Confirm banner fires only on change (not every turn).
- **Evidence gates:** reject if cleanup change is non-additive/risky, if the state file is committed to
  git, or if docs over-promise.

## Dev Learnings
_(to be filled)_

## QA Learnings
_(to be filled)_
