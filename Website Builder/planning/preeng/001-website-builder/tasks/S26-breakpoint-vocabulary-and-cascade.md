# S26-breakpoint-vocabulary-and-cascade — Breakpoint vocabulary and the desktop-down cascade compiler

| Field | Value |
|---|---|
| Epic / Story | E7 / ST-08 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S24-doc-schema-and-canonical-serialisation |
| Requirements | FR-072, FR-073 |
| Acceptance criteria | A41 · §12.17-A91 · SL-S26-1 |
| CQ / evidence | CQ2 |
| Note | **NA-06** — the free-position **auto-demote trigger is ≤390px** while the **`sm` media-query boundary is ≤479px**. They are *not* the same number, and 479 is a width no switcher, preview frame or gate ever renders. Both call sites are fixed here (`§12.3-O31`) |

## PM — slice definition

**Objective.** Make one breakpoint vocabulary normative across switcher, cascade, free-position rules, save format and gates.

**In scope.** The vocabulary as one exported table — `base` (no media query, 12 tracks, previewed at 1280 and full), `md` (`max-width: 991px`, 6 tracks, previewed at 768), `sm` (`max-width: 479px`, 4 tracks, previewed at 390); the cascade compiler emitting in order `base → md → sm` so the narrower rule wins by **source order** with no `!important`; `base` mandatory on every node and `md`/`sm` written **only where the user overrides**, so "overridden here" stays a key-presence test; **a node with a `base` entry and no `sm` entry compiles to `grid-column: 1 / -1` inside the `sm` media query**; 1440 as a preview-only fifth switcher option carrying no overrides; the two NA-06 numbers named separately at their own call sites with a comment at each stating they are deliberately different.

**Out of scope.** The override UI — the pre-commit chip, the "overridden here" dots and reset-to-inherited (S46). Free position itself (S48) — this slice only fixes its trigger number. The switcher chrome (S29).

**Allowed files / contexts.**
- `scripts/lib/breakpoints.ts`, `scripts/lib/render/emit-css.ts` (cascade emission only), `04-site/site.json` (`breakpoints`, `preview`, `freePositionPolicy` fields).

**Steps.**
1. Export the vocabulary once; every consumer — switcher, cascade, free-position policy, save format, gates — imports it and none restates a number.
2. Compile a node's `layout` map to rules in the fixed order `base`, then `md`, then `sm`; assert the emitted order by reading the compiled stylesheet.
3. Implement the sparse-override rule: a missing key means inherit, and a missing `sm` key compiles to `grid-column: 1 / -1`.
4. Reject any upward key through S24's validator, with the message naming the desktop-down rule.
5. Record `freePositionPolicy.demoteAtMaxWidth: 390` and `breakpoints.sm.maxWidth: 479` in `site.json`, each with the comment that they are not the same number.
6. Add the `!important` assertion over all emitted CSS.

**Definition of Done.**
- Artifacts: the vocabulary module, the cascade emitter, the compiled stylesheet for the seeded page, the two annotated call sites.
- Validation: the emitted rule order is `base, md, sm`; a base-only node yields `grid-column: 1 / -1` under `max-width: 479px`; `grep -c '!important'` over emitted CSS is 0; the 390 and 479 assertions both pass.
- `slice.yaml` mapping — `acceptance_criteria: [A41, "§12.17-A91", SL-S26-1]`, `verification_method: exit-code` (SL-S26-1: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-072, FR-073 → file:line, including every consumer that imports the vocabulary; (3) structural quality — one table, zero restated literals; a grep for a bare `991`, `479` or `390` outside the module and the two annotated call sites returns nothing; (4) functional testing — the compiled stylesheet for a three-node fixture with a `base`-only node, a `base`+`md` node and a fully overridden node; (5) security/compliance — n/a, note it; (6) operational — what changes if a fourth key is ever added, and why an upward key is not that; (7) self-assessment.

## QA — zero-trust verification

- **Read the compiled stylesheet yourself** and record the rule order; a claimed order in prose is not evidence.
- **Recompute the full-width rule**: take the `base`-only node and confirm `grid-column: 1 / -1` appears inside the `max-width: 479px` block and nowhere else.
- **Run your own** `grep -rn '!important'` over every emitted file and require zero.
- **Grep for the literals `991`, `479` and `390` yourself** outside the vocabulary module; each hit must be one of the two annotated NA-06 call sites, and any code treating 390 and 479 as interchangeable is a rejection.
- **Reject** if the switcher, the gates or the free-position policy carry their own copy of any breakpoint number.

## Dev Learnings

_Not Done until filled. Required: which consumer was still carrying a private copy of a breakpoint number, and whether source-order-only cascading held without a single `!important`._

## QA Learnings

_Not Done until filled. Required: whether the 390-versus-479 distinction survived review without being "tidied" into one number._
