# S46-override-cascade-and-precommit-chip — Per-breakpoint override cascade, pre-commit chip and overridden-here dots

| Field | Value |
|---|---|
| Epic / Story | E9 / ST-15 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 3 / — |
| Depends on | S43-drag-to-place-and-drop-algorithm · S26-breakpoint-vocabulary-and-cascade |
| Requirements | FR-113 |
| Acceptance criteria | A42 · SL-S46-1 · SL-S46-2 · SL-S46-3 |
| CQ / evidence | CQ2 · EL-063 |
| Note | **NA-14** — the accumulation thresholds (≥5 per page amber, ≥15 red, ≥40 per site, ≥25% of a page's nodes) are **stated starting numbers, not measurements** `[I — low confidence, EL-063]`. They are tunable in `site.json` and must be read from the project record, never hardcoded |

## PM — slice definition

**Objective.** Make invisible overrides visible and make every breakpoint-scoped edit announce its blast radius before it commits.

**In scope.** The desktop-down cascade applied at the editor layer: `base` is mandatory, `md`/`sm` are written **only where the user actually overrides**, so "overridden here" is a **key-presence test** — which holds only because canonical serialisation omits absent optional keys entirely rather than writing `null`. A **structurally prominent** persistent breakpoint indicator in the editor chrome — not a dropdown — with the active key also persisted to `.wb/session-ui.json` as `activeBreakpointKey`. A **pre-commit chip** naming exactly which sizes an edit affects, with one-click **"apply to all sizes instead"** (A42). An **"overridden here" dot** per overridden property with one-click **reset-to-inherited**, dispatched as the `reset-to-inherited` typed op. An inspector panel listing **every** breakpoint-specific value for the selected node. Override accumulation counting with escalation at the thresholds **read from `site.json`**, and the counts written into the gate report.

**Out of scope.** The breakpoint vocabulary itself and schema rejection of an upward key (S26/S24 own `§12.3-O32` and §12.17-A92) — v1 has no key above `base`. The reading-order invariant and the `order` override (S47). Free positioning per breakpoint (S48). The lock-time gate that consumes the counts (S68) — this slice emits them.

**Allowed files / contexts.**
- `scripts/lib/canvas/override-cascade.ts`, `scripts/lib/canvas/precommit-chip.ts` (extending S43's chip), `scripts/lib/canvas/override-dots.ts`, `scripts/lib/doctor/override-counts.ts`, the breakpoint compiler from S26 (read-only), `site.json` doctor thresholds (read via `set-doctor-thresholds`).

**Steps.**
1. Resolve the effective value for a property as `sm ?? md ?? base` at the active key, and record which key supplied it, so the dot and the panel share one resolution function with the compiler.
2. Write overrides sparsely: an edit at `base` never materialises `md`/`sm` keys; an edit at `md` writes only `md`.
3. Extend the pre-commit chip so every breakpoint-scoped edit states its blast radius **before** commit, with the "apply to all sizes instead" action wired to the same op batch.
4. Render the overridden-here dot from key presence, never from a value comparison — two keys holding the same value is still an override.
5. Count overrides per node, per page and per site; compare against thresholds loaded from `site.json`; emit amber at the first threshold and a **red finding that records the count without blocking LOCK** at the second.
6. Persist `activeBreakpointKey` in session UI state so a reload returns to the size the user was working at.

**Definition of Done.**
- Artifacts: cascade resolver, extended chip, dots with reset, the breakpoint indicator, the counting module, the gate-report fields.
- Validation: an edit at `md` produces an `md` key only; the chip names the affected sizes before commit; a dot appears where a key exists and disappears after reset-to-inherited; changing a threshold in `site.json` changes the escalation point.
- `slice.yaml` mapping — `acceptance_criteria: [A42, SL-S46-1, SL-S46-2, SL-S46-3]`, `verification_method: manual-observation` (SL-S46-3: `exit-code`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-113 → file:line; (3) structural quality — one resolution function shared by editor and compiler, proven by call graph; (4) functional testing — the sparse-write diffs, the chip transcript, the reset round-trip, the threshold-change run; (5) security/compliance — every write goes through the typed op; (6) operational — what the panel shows for a node with no overrides at all, and how counts behave across page add/delete; (7) self-assessment, tagging the thresholds as `[I]` starting numbers expected to be tuned after the first real site.

## QA — zero-trust verification

- **Recompute the override counts yourself** by walking `pages/<id>.doc.json` and counting `md`/`sm` key presence; a logged count you cannot reproduce is a rejection.
- **Edit a threshold in `site.json` yourself** and confirm the escalation point moves; then `grep` the source for the literal values `5`, `15`, `40` and `25` in the counting path — a hardcoded threshold is a rejection.
- **Diff the document after an `md` edit** and require that no `sm` key and no redundant `base` key was written.
- **Confirm the chip renders before commit**, by attempting the edit and cancelling; a chip shown after the write is a rejection.
- **Reject** if the overridden-here dot is derived from value equality rather than key presence, or if the breakpoint indicator is a dropdown.

## Dev Learnings

_Not Done until filled. Required: where sparse writing was hardest to keep honest, and whether the chip actually changed a commit decision in practice._

## QA Learnings

_Not Done until filled. Required: which override the count missed, and whether the key-presence test survived canonical re-serialisation._
