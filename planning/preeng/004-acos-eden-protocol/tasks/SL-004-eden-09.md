# SL-004-eden-09 — Per-message override (raw: / L1:)

**Story:** ST-004-eden-5 · **Epic:** EP-004-eden-5 · **Demo:** 3+ · **Effort:** S · **Priority:** P1

## PM (Planner / LCE)
- **Objective (single):** Let the user get ONE reply at a different level (or raw) without changing the
  session default.
- **In-scope:** parse a `raw:` (off for this reply) or `L{n}:` (level n for this reply) prefix on the
  user's message; apply to that reply only; never write `.acos/state/eden-level`.
- **Out-of-scope:** persistent level changes (SL-01).
- **Allowed files:** `~/.claude/skills/acos-eden-protocol/SKILL.md`.
- **Definition of Done:** `raw: give me the exact regex` returns an unfiltered reply while the session
  stays at its level; state file unchanged; the following turn returns to the session level.

## Dev — Evidence Bundle
1. Override parse rule. 2. Traceability (S4, E8, CQ15). 3. Test: session=L4, `raw:` reply is unfiltered,
  state file still `4`, next turn back to L4. 4. `L1:` one-off works too. 5. Limitations.

## QA (Zero-Trust)
- Confirm the state file is NOT mutated by an override; confirm the override applies to exactly one reply.
- **Evidence gate:** reject if an override leaks into session state or persists beyond one reply.

## Dev Learnings
_(to be filled)_

## QA Learnings
_(to be filled)_
