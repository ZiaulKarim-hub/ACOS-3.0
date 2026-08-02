# S25-pure-renderer-and-resolution-policy — Pure, total renderer with the normative resolution policy

| Field | Value |
|---|---|
| Epic / Story | E7 / ST-08 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S24-doc-schema-and-canonical-serialisation |
| Requirements | FR-071, FR-076, FR-118 |
| Acceptance criteria | A46 · SL-S25-1 · SL-S25-2 · SL-S25-3 · SL-S25-4 |
| CQ / evidence | CQ3 |
| Note | **R4** — if the DOM is the source of truth this is a 2003 WYSIWYG, and worse, because Claude also writes the source. Zero DOM serialisation is **structural** here, not a convention |

## PM — slice definition

**Objective.** Render from documents with one code path for the design surface and for LOCK, and define exactly what happens when a reference does not resolve.

**In scope.** `render(doc, systemLock, library) → files`, **pure and total**; the *same* renderer for the design surface and for LOCK, switched by `editor: false` (D3) — zero editor artifacts **emitted** when false, never stripped afterwards; the §12.16 resolution policy applied at editor open, at generate and at lock gate 6 — unknown component id is a hard fail opening the editor read-only in a migration-required state naming every affected node and page; unknown variant falls back to the direction's canonical variant, writes `node.variantMigrated = {from, to, reason, at, auto:true}` and blocks LOCK until acknowledged; a changed slot contract moves content to `node.orphaned.<slotName>`; a removed prop takes the imported migration map or the variant default; an unknown motion preset falls back to `motion.none` through the same code path; an unknown token and an asset id absent from `assets/manifest.json` both hard-fail at generate naming the offender; a `formatVersion` newer than the tool refuses to open naming both versions. Component internals emit `@container` with `container-type: inline-size` on **every block wrapper**, never `@media` (A46).

**Out of scope.** `wb migrate` and `migration-report.json` (S59) — this slice writes the flags, not the migration. The breakpoint cascade compiler (S26). Editor chrome (S29).

**Allowed files / contexts.**
- `scripts/lib/render/**`, `scripts/lib/resolve.ts`, `scripts/lib/render/emit-css.ts`, `src/substrate/*` (the only place a framework import may appear, invariant I6).

**Steps.**
1. Implement `render` as a pure function of its three arguments; no ambient reads, no mutation of its inputs.
2. Implement `resolve.ts` as one table matching §12.16 row for row; every row returns a structured verdict, never a thrown exception on a normal miss.
3. Wire the `editor` flag at emission, not at post-processing; prove with a diff of the two output trees.
4. Emit component internals under `@container` with `container-type: inline-size` on every block wrapper; assert no `@media` inside component internals.
5. Implement the orphan store move; a migration may relocate content, **never destroy it**.
6. Write the migration-required read-only state and make both `generate` and `lock` refuse while it holds.
7. Assert by grep that no code path parses rendered output back into JSON.

**Definition of Done.**
- Artifacts: renderer, resolution table, the two output trees, the migration-required state, the orphan store.
- Validation: unknown-component, unknown-variant, removed-slot, unknown-token, absent-asset and future-`formatVersion` fixtures each produce their specified outcome; the reverse-parse grep is empty; `@media` inside component internals is zero.
- `slice.yaml` mapping — `acceptance_criteria: [A46, SL-S25-1, SL-S25-2, SL-S25-3, SL-S25-4]`, `verification_method: exit-code` (A46 and SL-S25-4: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-071, FR-076, FR-118 → file:line per resolution row; (3) structural quality — one renderer, one resolution table, no second rendering path for LOCK; (4) functional testing — six resolution fixtures plus the `editor: true`/`false` output diff; (5) security/compliance — the renderer reads only the session root and the library; (6) operational — what the user sees in the migration-required state, and how they get out of it; (7) self-assessment.

## QA — zero-trust verification

- **Render twice yourself**, with `editor: true` and `editor: false`, and diff the trees; any editor artifact present in the second and merely absent from a scrub step is a rejection.
- **Grep for reverse parsing yourself** — `innerHTML`, `outerHTML`, any DOM-to-document writer — and require zero hits.
- **Grep the emitted component internals for `@media`** and require zero; then confirm `container-type: inline-size` is on every block wrapper, counted.
- **Write your own removed-slot fixture** and prove the content lands in `node.orphaned`, not in a diff.
- **Reject** if any resolution miss throws instead of returning a verdict.

## Dev Learnings

_Not Done until filled. Required: which resolution row was hardest to make total, and whether the single-renderer constraint forced any compromise in the editor surface._

## QA Learnings

_Not Done until filled. Required: which editor artifact came closest to leaking into the `editor: false` tree, and how it was caught._
