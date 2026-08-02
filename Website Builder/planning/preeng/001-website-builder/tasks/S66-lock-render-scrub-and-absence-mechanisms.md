# S66-lock-render-scrub-and-absence-mechanisms — LOCK as a re-render, with five layered editor-absence mechanisms

| Field | Value |
|---|---|
| Epic / Story | E14 / ST-22 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 5 / — |
| Depends on | S27-determinism-contract, S63-gates-ts-verdicts-and-tiers |
| Requirements | FR-200, FR-201, FR-206 |
| Acceptance criteria | A49 · A50 · SL-S66-1 · SL-S66-2 |
| CQ / evidence | CQ9 |
| Note | **`§17-O6` — the single most consequential architectural decision in the eight steps.** LOCK is `build → scrub → assert → snapshot`, a **re-render with `editor:false`**, taken *against* the in-estate precedent of copy-and-strip, which required hand-rewriting links and hand-excluding dev pages. A49–A59 are all written assuming re-render |

## PM — slice definition

**Objective.** Build the published tree by **re-rendering with the editor flag false**, never by copying `dist/` and stripping attributes out of it.

**In scope.** The `build → scrub → assert → snapshot` pipeline entry point (`wb lock`, gates deferred to S67, snapshot deferred to S69); all **five** layered editor-absence mechanisms — (1) two configs / two commands / two out-dirs so the editor is **not in the publish build graph at all**; (2) dev-only injection **gated on the build command**; (3) dev-toolbar-class chrome that **physically cannot leak**; (4) `import.meta.env.WB_DESIGN` guards **explicitly defined as `false` in the publish config** (an *undefined* variable may not be tree-shaken — filed bug); (5) a post-build hook that **scrubs every emitted HTML file and then asserts**; and the LOCK strip set — recovery bin, `node.locked` freeze flags, per-section notes and asset-pane state removed from published output while `assets/manifest.json` **stays** in the project and in the evidence bundle.

**Out of scope.** The eight purity gates (S67) — this slice makes the tree clean, S67 proves it. The 32-check checklist (S68). Snapshots, tag and unlock (S69). Publishing (S70). Copy-and-strip in any form, including "just for a spike".

**Allowed files / contexts.**
- `scripts/lock.ts`, `scripts/lib/publish-config.ts`, `scripts/lib/scrub.ts`, `scripts/lib/strip-editor-state.ts`, the publish build config, `07-lock/dist/` (write).
- **No `.py` file anywhere.** No `rm -rf` in the export path — write-to-new-dir-then-swap only (the permission layer scores destructive commands +5).

**Steps.**
1. Create the second config, second command and second out-dir; prove the editor entry points are absent from the publish build graph, not merely unreferenced.
2. Gate dev-only injection on the build command itself, so an editor asset cannot be emitted by a publish run under any flag combination.
3. Give editor chrome a dev-toolbar class whose emission path does not exist in the publish graph.
4. Define `WB_DESIGN: false` **explicitly** in the publish config; add a selftest assertion that fails if it is ever left undefined.
5. Scrub every emitted HTML file, then **assert** on the scrubbed output — scrub without assert is the failure mode this mechanism exists to prevent.
6. Strip recovery bin, freeze flags, section notes and asset-pane state from published output. The user-visible word for the freeze verb is **Freeze**, never "Lock" (`§17-O33`) — LOCK is the terminal publish verb, and only the word is cosmetic.
7. Keep `assets/manifest.json` in the project tree and in the bundle; it is the licence allowlist and must not be stripped.

**Definition of Done.**
- Artifacts: `lock.ts` (build+scrub+assert stages), publish config, scrub module, the scrub output file, one re-rendered tree.
- Validation: `grep -r 'data-wb-'` over the published tree returns zero; the dev-runtime patterns return zero; a deliberately reintroduced `WB_DESIGN` undefined fails the selftest; the strip set is absent from published output and present in the project.
- `slice.yaml` mapping — `acceptance_criteria: [A49, A50, SL-S66-1, SL-S66-2]`, `verification_method: grep-assert`.

## Dev — execution contract

Evidence bundle: (1) summary naming which of the five mechanisms caught what during development; (2) traceability FR-200, FR-201, FR-206 → file:line per mechanism; (3) structural quality — scrub and assert are separate functions and the assert cannot be skipped by a flag; (4) functional testing — a build with an editor string deliberately injected must fail the build; (5) security/compliance — the published tree contains no bearer token, no session path, no editor endpoint; (6) operational — how to re-run LOCK's build stage alone; (7) self-assessment, stating plainly that this is a re-render and pointing at the code path that would have been a copy.

## QA — zero-trust verification

- **Read `lock.ts` yourself** and confirm the published tree is produced by a *build invocation*, not by a copy of the design output. A copy-and-strip implementation is an outright rejection regardless of how clean the grep is.
- **Run your own** `grep -r 'data-wb-'` and the dev-runtime pattern grep over the emitted tree.
- **Inject an editor string** into a source file in a scratch branch and confirm the build **fails** rather than scrubbing it silently.
- **Count the five mechanisms in code** — four implemented and one described in prose is a rejection.
- **Grep published output** for recovery-bin, freeze-flag, section-note and asset-pane keys; **and** confirm `assets/manifest.json` still exists in the project.
- **Reject** if any user-visible string calls the freeze verb "Lock".

## Dev Learnings

_Not Done until filled. Required: which mechanism actually caught a leak, and whether the undefined-vs-false tree-shaking bug reproduced on this substrate._

## QA Learnings

_Not Done until filled. Required: how convincingly a copy-and-strip implementation could have passed the greps, and what test distinguishes them._
