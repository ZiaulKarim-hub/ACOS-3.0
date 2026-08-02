# S68-lock-time-checklist-32-checks — The 32-check ordered lock-time checklist

| Field | Value |
|---|---|
| Epic / Story | E14 / ST-23 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 5 / — |
| Depends on | S67-eight-purity-gates, S64-live-checks-scoped |
| Requirements | FR-204 |
| Acceptance criteria | A60 · A61 · A62 · A63 · A64 · A65 · A66 (inconsistent, NA-16) · A67 (inconsistent, NA-16) · A68 · A69 · A70 · A71 · SL-S68-1 · SL-S68-2 |
| CQ / evidence | CQ11 · CQ10 · EL-061 · EL-005 |
| Note | **NA-04 — 32 checks: 28 base gates plus lettered insertions 4a (motion-concurrency caps), 11a (skip-link presence and first tab order), 13a (pause/stop/hide affordance), 23a (asset-reference resolution).** Three of the four carry unfinished cross-section build prerequisites |

## PM — slice definition

**Objective.** Run all **32** checks **cheapest-and-most-foundational first**, including the four lettered insertions and their build prerequisites.

**In scope.** The ordered lock-time checklist as whole-document batch checks (the live/lock line is **scoped arithmetic vs whole-document render pass**, not "a11y vs performance"); reflow (no two-dimensional scroll at 320 CSS px except exempted content A60 · a 40-char unbroken token A61 · **+35% pseudolocalisation** A62 · 200% zoom with no horizontal scroll and no content loss A63); the accessibility floor (WCAG 2.2 AA contractual floor, **WCAG 2 is the pass/fail gate**, APCA advisory `[U — the perceptual bands are inherited and not re-verified, EL-005]`); SEO and structured data (unique title, 50–160-char description, canonical, OG+Twitter with image, `<html lang>` matching the interview answer, single `<h1>` with no skipped levels, 100% alt coverage, `robots.txt` + `sitemap.xml` from the page tree, JSON-LD matched **1:1** to the site-type answer — A69, A70); **no-JS** usability (content visible, nav usable, forms submittable — A71); fonts (`font-display: swap` on every `@font-face`, exactly the committed families preloaded, **a fourth family introduced by a late swap fails**, metric-matched local fallback computed from the real font binary — A68); and the four insertions with their prerequisites — the skip-link component row (NA-B08), `pauseAffordanceRef` on the container contract, the font-fallback-metrics token family.

**Out of scope.** The eight purity gates (S67) — they run first and separately. Live checks (S64). Repairing findings. Loosening any threshold to make a run pass.

**Allowed files / contexts.**
- `scripts/lib/gates/locktime/*.ts`, `scripts/lib/checklist-order.ts`, `07-lock/gate-report.json` (append rows).

**Steps.**
1. Encode the checklist as **ordered data** — 28 base rows plus `4a`, `11a`, `13a`, `23a` at their insertion points — so the count and the order are both machine-readable and neither is a comment.
2. Implement the canonical performance thresholds (NFR-04): **LCP ≤2.5s · CLS ≤0.1** (internal stretch 0.05) **· INP ≤200ms** (or TBT ≤600ms floor / 300ms aspirational as proxy) **· pre-LCP transfer ≤1.5–2MB** — *not* total page weight — median-of-3, mobile, simulated Slow-4G + 4× CPU.
3. Record that **A66 omits the interaction metric and A67 states a flat cap** (NA-16): the gate implements the **canonical** statement and both criterion texts are flagged as amendments owed, never silently satisfied.
4. Implement 4a (motion-concurrency caps `[I — provisional]`), 11a (skip-link presence **and first tab order**), 13a (pause/stop/hide affordance) and 23a (asset-reference resolution).
5. Keep **licence completeness and reference resolution as two separate gates**: completeness confirms every *recorded* asset carries a licence class; resolution confirms every *referenced* asset exists on disk **and** in `assets/manifest.json`. A hallucinated asset path passes the first and ships a silently broken page.
6. Emit every row as a structured verdict with `measured` and `threshold`; INCONCLUSIVE blocks like a fail.
7. Record wall-clock per check and in total.

**Definition of Done.**
- Artifacts: 32 check modules or table-driven equivalents, `checklist-order.ts`, gate rows appended to `gate-report.json`, the timing record.
- Validation: the emitted row count is **32**; a hallucinated asset path fails 23a while passing licence completeness; a pseudolocalised fixture at +35% produces no overflow; a fourth-family font swap fails.
- `slice.yaml` mapping — `acceptance_criteria: [A60, A61, A62, A63, A64, A65, A66, A67, A68, A69, A70, A71, SL-S68-1, SL-S68-2]`, `verification_method: recompute` (A64/A71: `manual-observation`; A65/A69/A70/SL-S68-1/SL-S68-2: `exit-code`; A68: `grep-assert`).

**Assumption.** `[I]` §13.1's LOCK wall-clock budget **p50 ≤90s / p95 ≤180s** for a representative 5-page site is an **inference sized against this 32-gate list, with an unproven sampling fallback** (EL-061, confidence 0.35). It is recorded as a measurement target, **never reported as measured**, and must not be treated as an SLA until this slice's timing record exists.

## Dev — execution contract

Evidence bundle: (1) summary with the **measured** total and per-check wall clock, explicitly compared against the `[I]` budget rather than asserting it; (2) traceability FR-204 → file:line per check, with the four insertions named; (3) structural quality — the order is data, so inserting a check renumbers nothing; (4) functional testing — one seeded failure per tier-one check with its recorded verdict; (5) security/compliance — the accessibility claim ceiling is respected in every string this slice emits; (6) operational — how to run one check in isolation; (7) self-assessment naming which prerequisites (skip-link row, `pauseAffordanceRef`, fallback-metrics family) were still missing.

## QA — zero-trust verification

- **Count the rows yourself** in `gate-report.json`. 28 is a rejection; 32 with four rows that always pass is also a rejection.
- **Recompute two contrast pairings** from the built page and compare against the contrast proof table.
- **Write your own hallucinated asset path** into a document, re-run, and confirm 23a fails while licence completeness still passes — this is the whole reason 23a exists separately.
- **Re-run the performance gate yourself**, median-of-3, and confirm the interaction metric is present; a gate implementing A66 literally (no interaction metric) is a rejection.
- **Disable JavaScript** and confirm content, nav and form submission yourself.
- **Reject** any string anywhere in this slice's output that claims conformance; the only honest form is *"Automated accessibility gates passed: N. Manual and screen-reader review not performed."*
- **Reject** if a threshold was loosened to obtain a pass, or if the timing record is presented as validating the `[I]` budget.

## Dev Learnings

_Not Done until filled. Required: the measured LOCK wall clock against the `[I]` p50/p95 budget, and which check dominated it._

## QA Learnings

_Not Done until filled. Required: which of the 32 was easiest to implement as a no-op that always passes, and whether the pseudolocalisation fixture found anything real._
