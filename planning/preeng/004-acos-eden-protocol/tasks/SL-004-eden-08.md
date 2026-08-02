# SL-004-eden-08 — Self-verification heuristic (with non-guarantee caveat)

**Story:** ST-004-eden-4 · **Epic:** EP-004-eden-4 · **Demo:** 3 · **Effort:** M · **Priority:** P1

## PM (Planner / LCE)
- **Objective (single):** Add a lightweight internal self-check that estimates whether a reply hit its
  level's band before sending — explicitly NOT a certified numeric FK.
- **In-scope:** heuristic checklist (approx sentence length, syllable-heavy word scan, undefined-acronym
  scan, jargon-gate for L2/L5); a stated caveat that it is heuristic; a soft correct-if-off behavior.
- **Out-of-scope:** any non-stdlib NLP dependency (WON'T W1).
- **Allowed files:** `~/.claude/skills/acos-eden-protocol/SKILL.md`, optional `.claude/scripts/eden-selfcheck.py`.
- **Definition of Done:** the skill self-checks + nudges toward the band; docs state the non-guarantee
  clearly (no false promise of a certified metric).

## Dev — Evidence Bundle
1. Heuristic as encoded. 2. Traceability (C3, CQ4). 3. Example where the heuristic catches an
  over-complex L5 draft and simplifies further. 4. The non-guarantee caveat text. 5. Limitations.

## QA (Zero-Trust)
- Confirm the caveat is present and unambiguous (no "guaranteed grade N" claim).
- **Evidence gate:** reject if the skill over-promises a certified metric.

## Dev Learnings
_(to be filled)_

## QA Learnings
_(to be filled)_
