# D4 — Motion is a design-system item, living in draggable art containers

**Status:** SETTLED · **Date:** 2026-07-26 · **Decided by:** Zee, in conversation
**Do not reopen.** A later session may implement this; it may not re-litigate it.

## Context

An earlier draft treated motion as a separate verification channel, following the prior swarm
research — which had named motion verification "the single largest engineering-risk area" and
recorded that no controlled study shows frame-sequence feedback improves generated animation
quality (Data Gap 2, still unresolved).

Zee's clarification: motion is already covered by the **"animation"** item named in the design
system, and animated pieces will sit in **picture- or art-like draggable containers**, the same
as artwork.

## Decision

- **Animation is an ordinary design-system item with variants** — it goes through the same
  generate-10-variants, pick-one flow as fonts, buttons and cursors.
- **Animated pieces live in the same draggable containers as artwork.** The editor manipulates
  an animated container exactly as it manipulates an art container.
- Motion is **not** a separate parallel subsystem.

## Consequences

- §9 enumerates both the animation kinds and the container kinds (still image, image sequence,
  video loop, vector animation, CSS/GSAP-driven element, canvas/WebGL slot, scroll-driven
  sequence, decorative background layer, ambient layer), each with the data it needs.
- Every container carries a **reduced-motion variant reference** — an art-directed alternative,
  not a switch that simply turns motion off.
- The audit added a hard requirement this decision made necessary: every container needs a
  **pause affordance reference**, so an unpausable marquee is structurally unbuildable
  (WCAG 2.2.2 Pause, Stop, Hide — Level A). Automated checkers do not reliably catch this.
- Open follow-ups: variant-count mismatches between kinetic-type containers (8) and text
  reveal/kinetics (10), and between cursor-reactive containers (5) and hover micro-reactions
  (10). Both left as explicit open questions in §9.7 — no source establishes which is right.
- Unchanged caveat, carried from the research: motion remains the weakest thing to verify and
  the strongest thing award juries reward. Folding it into the system does not solve that.

## Rejected alternative

**A separate motion verification channel** (filmstrip capture, interaction-manifest walking) as
a parallel subsystem in v1. Deferred rather than adopted: it is the one research-grade item in
the whole plan, and this product puts a human in the judging seat anyway.
