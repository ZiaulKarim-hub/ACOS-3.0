# S50-demo-3-d2-exercised — DEMO 3: gridlines, constraint drag, per-breakpoint overrides and the free-position hatch

| Field | Value |
|---|---|
| Epic / Story | E9 / ST-16 |
| Type · MoSCoW · Size | demo · MUST · M `[I]` |
| Phase / Demo | Phase 3 / **Demo 3** |
| Depends on | S43-drag-to-place-and-drop-algorithm · S44-span-resize-and-spacing-handles · S45-keyboard-parity-and-target-size · S46-override-cascade-and-precommit-chip · S47-reading-order-and-stack-preview · S48-free-position-anchored-offset |
| Requirements | — (demo slice: it exercises the requirements its dependencies introduced, and introduces none) |
| Acceptance criteria | A39 · A40 · A41 · A42 · A43 · SL-S50-1 · SL-S50-2 |
| CQ / evidence | CQ2 · CQ4 · EL-065 |
| Note | **This is D2's first real exercise** — the moment the constraint-layout decision is either survived or diagnosed (R8). The demo must **show constraint dragging working**, not assert that it does |

## PM — slice definition

**Objective.** Exercise the settled constraint-layout decision for the first time and either survive or diagnose the friction risk it carries.

**In scope.** One recorded session against a real generated direction that demonstrates, in this order:
1. **Gridlines painted from resolved tracks** (A39) — visible, and shown to be the snap target rather than decoration.
2. **Constraint drag committing grid integers** (A40) — a block spanning 6 of 12 measured at **50% at both 768 and 1440**, with the persisted value shown to be integers.
3. **The `sm` compile rule** (A41) — a node with **no `sm` entry** shown compiling to `grid-column: 1 / -1` inside the `sm` media query.
4. **The pre-commit chip** (A42) — a breakpoint-scoped edit naming exactly which sizes it affects before it commits, and the "apply to all sizes instead" action taken once.
5. **Free-position auto-demotion** (A43) — fired at the recorded demotion width of **≤390px**, with the authored `flowFallback` visible in the Navigator.

Plus the two slice-local requirements: **the friction test** — move a hero headline up by one spacing step using **each of the three verbs** (align to, space above/below, order) **and** the keyboard path, recording whether the tool fought the user; and **elapsed effort for the three placement sub-slices (S41, S42, S43) recorded**, because it is the only path from inference to a defensible schedule number.

**Out of scope.** The canvas tail (S49) — it is COULD and first in the trade-back-out order, so its presence or absence must not gate this demo. LOCK, purity gates and publish (Phase 5). Any new mechanic: a defect found here is fixed in its owning slice and this demo re-runs.

**Allowed files / contexts.**
- `evidence/demo-3/**` (recording, screenshots, measurements, timings), `docs/demos/demo-3.md`.
- Read-only: everything the demo exercises. **No product file may be edited by this slice.**

**Assumption (recorded).** The plan names the sub-slices to measure as "S41–S43" in its open-item table and "S42–S44" in its schedule section; this demo records elapsed effort for **S41, S42 and S43** — the three placement sub-slices — and flags the discrepancy `[I]`.

**Definition of Done.**
- Artifacts: the recording, per-claim screenshots with measured numbers, the friction-test transcript across four paths, the effort table, `demo-3.md`.
- Validation: each of A39–A43 demonstrated with a measurement, not a claim; the 6-of-12 block measured at both 768 and 1440; the `1 / -1` compile read from generated CSS; demotion observed at ≤390px; four friction paths recorded with a verdict on each.
- `slice.yaml` mapping — `acceptance_criteria: [A39, A40, A41, A42, A43, SL-S50-1, SL-S50-2]`, `verification_method: recompute` (A41 and A43: `exit-code`; A42, SL-S50-1, SL-S50-2: `manual-observation`).

## Dev — execution contract

Absolute paths in every command; cwd resets between Bash calls. **Never use `timeout`/`gtimeout`** — it yields empty output rather than an error here. Evidence bundle: (1) summary naming each demonstrated criterion and the evidence path that proves it; (2) traceability — each behaviour → the slice that owns it; (3) structural quality — n/a for a demo, note it; (4) functional testing — the measurement table and the friction transcript, unsummarised; (5) security/compliance — confirm the eight controls were live and the token never appears in the recording; (6) operational — how to re-run the demo and which launcher rung was in use; (7) self-assessment, and a plain verdict on R8: did the tool fight the user, and where. **Every effort figure is tagged `[I]`, low confidence (EL-065), and none may be quoted as a measurement of anything beyond these three sub-slices.**

## QA — zero-trust verification

- **Recompute the 6-of-12 measurement yourself** at 768 and 1440 from the rendered page; a logged 50% you cannot reproduce is a rejection.
- **Read the generated `sm` CSS yourself** and confirm the node with no `sm` entry compiles to `grid-column: 1 / -1`.
- **Render at 390px yourself** and confirm demotion fires there; a demo that demonstrates demotion at the `sm` media-query boundary instead has demonstrated the wrong thing and is a rejection.
- **Watch the drag in the recording** and confirm it is a real constraint drag committing integers — a scripted document edit presented as a drag is a rejection.
- **Re-read the chip's text** and confirm it names the affected sizes before commit.
- **Reject** if the friction test is missing any of the four paths, or if the effort figures are presented without the `[I]` tag.

## Dev Learnings

_Not Done until filled. Required: the R8 verdict — which of the four paths for "move the headline up one step" was fastest, which fought back, and the measured elapsed effort for S41, S42 and S43._

## QA Learnings

_Not Done until filled. Required: which demonstrated criterion was weakest under independent recomputation, and whether any demo step masked a defect in its owning slice._
