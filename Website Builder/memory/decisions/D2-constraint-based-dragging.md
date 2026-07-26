# D2 — Constraint-based dragging, with a free-position escape hatch

**Status:** SETTLED · **Date:** 2026-07-25 · **Decided by:** Zee, in conversation
**Do not reopen.** A later session may implement this; it may not re-litigate it.

## Context

The brief asks for **drag-movable components** and **gridlines for precise placement**. Free
x/y dragging fights responsive layout: a site must work at **390px** and **1440px** wide. If a
headline is dragged 40px left on the large screen, nothing in the brief says what happens on
the phone.

Real visual builders solve this one of two ways:

- **Constraint dragging** — every component is pinned to something (an edge, a centre, the box
  above it) and reflows automatically. Less freedom, always correct.
- **Per-breakpoint dragging** — total freedom, but the page must be arranged separately for
  each screen size. Roughly three times the work.

## Decision

**Constraint dragging is the default.** Components are pinned or anchored (left, centre,
stretch, relative to a parent or the element above), so layout reflows on smaller screens.

An explicit **per-component "free position" escape hatch** exists for cases that need it.

**Gridlines are what components actually snap to** — they are the layout substrate, not
decoration that gets hidden later.

## Consequences

- The dragging model must be specified concretely enough to implement, including what the
  escape hatch does at small screen sizes (§11).
- **⚠ D2 is currently inert in v1.** §18's deviations table records that v1 as drafted ships no
  gridlines and only section-reorder dragging. That deviation is awaiting sign-off — see
  `DECISIONS.md` #1. Until it is resolved, this decision has nothing to govern.
- Whether sibling anchoring ships at all is a live open question (DECISIONS.md #6); the
  subgrid-promotion strategy behind it is unprototyped.
- Risk R47 records that D2 is **unvalidated at first ship**, with a mitigation marked explicitly
  PARTIAL: there is no way to validate a constraint drag model without building one.

## Rejected alternative

**Free x/y positioning as the default.** Rejected because it silently produces broken phone
layouts, and the brief never specified per-breakpoint arrangement work.
