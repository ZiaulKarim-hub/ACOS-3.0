# SL-004-eden-06 — Precision appendix ("Exact figures & terms")

**Story:** ST-004-eden-3 · **Epic:** EP-004-eden-3 · **Demo:** 2 · **Effort:** M · **Priority:** P1

## PM (Planner / LCE)
- **Objective (single):** Append a default-on collapsible "Exact figures & terms" block reproducing
  every exempt span verbatim, sourced from the ORIGINAL answer.
- **In-scope:** trigger (reply has ≥1 exempt span), rendering rule, source-from-original constraint,
  session toggle to hide for casual use.
- **Out-of-scope:** the classifier itself (SL-05); reading-level engine (SL-07).
- **Allowed files:** `~/.claude/skills/acos-eden-protocol/SKILL.md`.
- **Definition of Done:** a simplified answer with figures/terms shows the collapsible appendix with
  every value verbatim; appendix content is derived from the original composition, never re-derived from
  the simplified text; togglable off.

## Dev — Evidence Bundle
1. Appendix rule as encoded. 2. Traceability (S2, E6). 3. Example: L5 answer + appendix listing exact
$/%/date/legal-term. 4. Proof the appendix values equal the original (not the simplified). 5. Toggle
works. 6. Limitations.

## QA (Zero-Trust)
- Confirm every exempt span in the body appears verbatim in the appendix; confirm appendix ≠ re-derived.
- **Evidence gate:** reject if any exempt span is missing from the appendix or altered.

## Dev Learnings
_(to be filled)_

## QA Learnings
_(to be filled)_
