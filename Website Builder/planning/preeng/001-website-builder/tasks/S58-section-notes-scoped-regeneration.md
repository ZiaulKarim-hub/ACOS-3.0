# S58-section-notes-scoped-regeneration — Per-section notes driving scoped inline regeneration as one undo step

| Field | Value |
|---|---|
| Epic / Story | E12 / ST-19 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 4 / — |
| Depends on | S57-more-variants-and-more-like-this · S20-local-regeneration-mode · S31-typed-ops-autosave-history-undo |
| Requirements | FR-180 |
| Acceptance criteria | A32 · SL-S58-1 · SL-S58-2 · SL-S58-3 |
| CQ / evidence | CQ15 |
| Note | **§17-O21** — this is the human-authored replacement for the rejected autonomous critique loop, and the middle gear between swapping one variant and regenerating everything |

## PM — slice definition

**Objective.** Ship the middle gear between swapping one variant and regenerating everything, executed inline with no second hand-carry.

**In scope.** `SectionNote` `{sectionId, note, status: "open"|"applied"|"dismissed", regenerationId?}` attached to a section; the `regenerate-section` typed op `{sectionId, noteId}` writing doc + content under **one `txn`** so it is **ONE undo step** (A32); execution **inline via Local Regeneration Mode** (S20) — **never a second hand-carry back out to the generation channel**; an append-only regeneration log entry per run; section notes **stripped from published output at LOCK**; a document diff proving no section other than the target changed.

**Out of scope.** Whole-direction redesign and migration (S59). Any autonomous critique loop — it was rejected and is not reinstated here. Changing the note UI into a chat.

**Allowed files / contexts.**
- `scripts/lib/regenerate-section.ts`, `scripts/lib/section-notes.ts`, the `regenerate-section` op handler, `04-site/pages/<id>.doc.json` + `04-site/content.json` (through typed ops only), the regeneration log, the LOCK strip list as a call site.
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.**

**Steps.**
1. Model the note, attach it to a section, and expose open/applied/dismissed transitions.
2. Implement the op so every mutation it causes shares one `txn` and one inverse, making Cmd+Z restore the whole section, never a hybrid.
3. Route generation through Local Regeneration Mode inline; assert by grep that no prompt-emission-and-await path is reachable from here.
4. Hash every page document before and after; require the target section's page to change and every other page to hash identically.
5. Append `{regenerationId, sectionId, noteId, at, result}` to the regeneration log on every run, including failures.
6. Add section notes to the LOCK strip set and prove absence in the published tree.

**Definition of Done.**
- Artifacts: the note model, the scoped regeneration path, the regeneration log, the LOCK strip entry.
- Validation: a scoped run changes one section only, verified by document hashes; one Cmd+Z restores the pre-run state exactly; a grep of published output finds zero section notes; the log has one entry per run.
- Demo-able increment: write a note on a section in the editor, regenerate it inline, then undo it in one step.
- `slice.yaml` mapping — `acceptance_criteria: [A32, SL-S58-1, SL-S58-2, SL-S58-3]`, `verification_method: exit-code` (SL-S58-1: `hash-compare`, SL-S58-3: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-180 → file:line; (3) structural quality — the scoping logic is pure and testable without the editor; (4) functional testing — the hash-diff run, the single-undo run, the strip check, a failure run that still logs; (5) security/compliance — regeneration writes only through typed ops and never accepts a file path; (6) operational — what happens when a note is regenerated twice, and how a failed run leaves the document; (7) self-assessment.

## QA — zero-trust verification

- **Recompute every page hash yourself** before and after; a changed hash on an untouched page is a rejection.
- **Press undo once** and compare to your own pre-run snapshot; a partially restored section is a rejection (R22 is exactly this failure).
- **Grep the published tree** for section-note content; one hit is a rejection.
- **Grep the regeneration path** for any hand-carry or prompt-emission step; the requirement is inline execution.
- **Reject** if the regeneration log is written only on success.

## Dev Learnings

_Not Done until filled. Required: what leaked outside the section boundary on the first attempt, and how the txn grouping was proven rather than assumed._

## QA Learnings

_Not Done until filled. Required: whether a single undo genuinely restored content and layout together, or only one of them._
