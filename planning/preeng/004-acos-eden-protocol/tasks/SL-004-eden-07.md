# SL-004-eden-07 — Two-axis reading-level engine + kb language rules

**Story:** ST-004-eden-4 · **Epic:** EP-004-eden-4 · **Demo:** 3 · **Effort:** L · **Priority:** P0

## PM (Planner / LCE)
- **Objective (single):** Make output actually read at the selected level via the two-axis spec, with
  knowledge-builder language rules adopted (and its tutor loop rejected).
- **In-scope:** per-level surface targets (FK/FRE, max sentence) + semantic jargon gate (data-model E2);
  adopt kb rules (jargon-defined-on-first-use, short sentences, concrete examples at L4-5, honest-
  uncertainty at ALL levels, misconception callouts, anti-condescension); explicitly do NOT chunk/
  advance-signal by default.
- **Out-of-scope:** self-verification heuristic (SL-08); overrides (SL-09).
- **Allowed files:** `~/.claude/skills/acos-eden-protocol/SKILL.md`.
- **Definition of Done:** sample answers at L1/L2/L3/L4/L5 visibly differ per the spec; L2 defines every
  domain term while L1 leaves jargon undefined (the 2-vs-1 gate); fidelity floor still holds.

## Dev — Evidence Bundle
1. Level rules as encoded. 2. Traceability (S1, S3, CQ5, CQ14). 3. Five worked examples (same source
answer at L1-L5) showing the dial. 4. L2-vs-L1 jargon-gate demonstrated on one domain term. 5. Proof no
tutor-loop mechanics leaked in. 6. Fidelity floor re-checked. 7. Limitations.

## QA (Zero-Trust)
- Sample each level; sanity-check surface (sentence length) + semantic (jargon handling) axes.
- Confirm honest-uncertainty/source-caveat markers survive at L5 (accuracy rules, all levels).
- **Evidence gates:** reject if levels are indistinguishable, if L2/L1 don't differ on jargon, if a
  tutor-loop mechanic appears by default, or if any fidelity invariant is broken.

## Dev Learnings
_(to be filled)_

## QA Learnings
_(to be filled)_
