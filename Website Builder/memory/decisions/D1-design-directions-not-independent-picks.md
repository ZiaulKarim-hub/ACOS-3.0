# D1 — Coherent design directions, not independent per-item picks

**Status:** SETTLED · **Date:** 2026-07-25 · **Decided by:** Zee, in conversation
**Do not reopen.** A later session may implement this; it may not re-litigate it.

## Context

The original brief asked for **10 variants of each item**, and **20 variants for artwork**.
Applied literally to the real design-system inventory, that is roughly **80 items × 10 ≈ 800
artifacts**, plus 20 artworks. (The 80-item figure was my estimate at the time; the audited
inventory later came in larger — §7 has 261 rows and §8 has 324.)

Two problems, one practical and one structural:

1. **Volume.** 800+ artifacts is a very large generation job to push through a manual paste
   boundary (step 3).
2. **Incoherence.** Independent picks clash. Button variant 3, ribbon variant 7 and cursor
   variant 9 need not belong to the same visual world. Coherence dies by a thousand small
   choices, each individually reasonable.

## Decision

- Generate **~10 COMPLETE, internally consistent design DIRECTIONS**, each covering the
  identity-carrying items (font pairing, colour scheme, button, cursor, background, ribbon,
  hero animation).
- **20 artworks**, tagged by which directions they suit.
- **Within a chosen direction**, 10 variants of each swappable component, generated **on
  demand** rather than all upfront.
- **Derived values — spacing, radius, shadow scales — are COMPUTED from the direction**, never
  picked independently.

The user's 10 and 20 are preserved. They arrive as coherent sets rather than a pile.

## Consequences

- The design system must distinguish **identity-carrying** items (must be picked) from
  **derived** items (must not be picked). §7 carries this split.
- A component bar swapping across direction boundaries is a coherence risk; §18 makes
  cross-direction swaps a v2 feature because only one direction is generated in full in v1.
- Open follow-ups this decision spawned: whether "20 artworks" means 20 pieces or 20 style sets
  (DECISIONS.md #3), and whether the direction tournament actually surfaces all ~10
  (§4, caught as a gap in the audit).

## Rejected alternative

**Literal independent per-item variants.** Rejected for the two reasons above. Note this was
rejected on coherence and volume grounds, *not* because the user's instinct was wrong — 10
options per identity item is exactly the right amount of choice; the fix was to bundle them.
