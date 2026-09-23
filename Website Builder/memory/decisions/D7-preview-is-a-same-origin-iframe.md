# D7 — The preview is a same-origin iframe; §11.7's title binds (closes §17-O4)

**Decided:** 2026-09-23, under Zee's standing instruction of the same date — "finish coding
website builder without asking any question" — given immediately after the four open rulings
were put to him in full (background, options, recommendation, and why, message of 2026-09-23).
The recommended option was adopted. **Reversible:** Zee can overturn this by saying so; the
losing topology's spike code is preserved.

**The decision.** PRD §11.7 is titled "Preview must be a same-origin iframe" and that title
binds. §17-O4 (which process topology hosts the preview) is CLOSED in favour of the
single-process, same-origin iframe design. §16.6.1's separate-helper-process description is
subordinate to §11.7 where they conflict.

**Evidence (S04, ADR-04 — measured, not argued):**
- Preview output byte-identical across both topologies: three PNGs, all sha256
  `6699982bd8fcffff1097c81c0018f950f227f8bda9fa1ff4cca9c1b0797eecbd`.
- Move latency favours the same-origin design: p50 5.0 ms vs 6.3 ms (n=24 each, warm-up
  discarded).
- The kill-preview test inverted the PRD's isolation claim for the separate process.
- Channel LOC: 48 (separate process) vs 4 (same-origin) — delta +44 for no measured benefit.
- NOT measured: HMR latency. ADR-04 records this and stays a non-decision document; this file
  is where the decision lives.

**Consequence.** §16.6.1 needs a conforming edit at the next PRD pass; until then this file
and ADR-04 are the authority for the contradiction.
