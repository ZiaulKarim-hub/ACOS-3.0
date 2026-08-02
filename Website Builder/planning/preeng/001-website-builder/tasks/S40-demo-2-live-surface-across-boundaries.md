# S40-demo-2-live-surface-across-boundaries — DEMO 2: a live editable surface proven across at least two turn boundaries

| Field | Value |
|---|---|
| Epic / Story | E8 / ST-12 |
| Type · MoSCoW · Size | demo · MUST · M `[I]` |
| Phase / Demo | Phase 2 / **Demo 2** |
| Depends on | S32-inline-plaintext-editing · S33-image-replace-focal-point-alt-gate · S34-reorder-duplicate-paste-freeze · S35-snapshots-variations-recovery-bin · S36-page-ops-seo-preview-and-health-hud · S39-ownership-guard-wb-op-and-inbox |
| Requirements | — (demo slice: it exercises the requirements its dependencies introduced, and introduces none) |
| Acceptance criteria | A80 · SL-S40-1 · SL-S40-2 |
| CQ / evidence | CQ6 · CQ7 |
| Note | **The editor premise is the thing on trial here, not any single feature.** A same-turn 200 is never proof of life — the whole slice exists to produce post-boundary evidence |

## PM — slice definition

**Objective.** Prove the editor premise holds in this harness, with survival evidence rather than a same-turn response.

**In scope.** One recorded session that performs, against a real generated direction: an inline plaintext edit, a section reorder, a variant swap and an autosave — then crosses a turn boundary, health-checks the server **in a separate tool call**, crosses a second boundary and health-checks again, with the original pid alive at each check. The recording names **which launcher rung (F1–F5) was in use**, because that is the fact worth carrying into the estate's memory. The evidence bundle collects the raw curl transcript, the `ps` output per check, and the doc hashes before and after each edit.

**Out of scope.** Any canvas mechanic — gridlines, snap, drag-to-place and per-breakpoint overrides all land in Phase 3 (S41 onward) and must not appear in this demo. Any new product code: if a defect is found, it is fixed in its owning slice and this slice re-runs. LOCK, publish and the evidence bundle proper (Phase 5).

**Allowed files / contexts.**
- `evidence/demo-2/**` (recording, transcripts, hashes), `docs/demos/demo-2.md`.
- Read-only: everything the demo exercises. **No product file may be edited by this slice.**

**Steps.**
1. Launch the server through the rung ADR-01 recorded as passing; confirm bind with retrying curl in the same turn; record the rung name.
2. Perform the four operations in one session; capture a screenshot and the doc sha256 after each.
3. **End the turn.**
4. In a **separate later tool call**, curl `/health`, then `ps -p <pid>` against the pid in `state.json`. Record both.
5. **End the turn again**, repeat step 4.
6. Confirm autosave reached disk by comparing the recorded hashes to the on-disk file, and that `history.jsonl` carries one entry per operation with the reorder and swap each grouped as a single transaction.
7. Write `demo-2.md`: what was shown, which rung, which evidence path proves each claim.

**Definition of Done.**
- Artifacts: the recording, per-step screenshots, the raw curl/`ps` transcript, the hash table, `demo-2.md` naming the rung.
- Validation: at least two post-boundary checks, each in its own tool call, each 200 with the original pid alive; four operations demonstrated; autosave verified against disk.
- `slice.yaml` mapping — `acceptance_criteria: [A80, SL-S40-1, SL-S40-2]`, `verification_method: probe` (SL-S40-2: `manual-observation`).

## Dev — execution contract

Absolute paths in every command; the agent thread's cwd resets between Bash calls. **Never use `timeout`/`gtimeout`** — no such binary exists here and it yields empty output rather than an error. Evidence bundle: (1) summary of what was demonstrated; (2) traceability — each demonstrated behaviour → the slice that owns it; (3) structural quality — n/a for a demo, note it; (4) functional testing — the full transcript, unsummarised; (5) security/compliance — confirm the eight controls were live during the demo and that the token never appears in the recording; (6) operational — the exact launch invocation and how to re-run the demo; (7) self-assessment, stating explicitly whether the pass was observed across ordinary boundaries only or also across an eternity `/clear`.

## QA — zero-trust verification

- **Re-run the post-boundary probe yourself**, in your own separate tool call, and record your own exit code and status.
- **Read `state.json` and run your own `ps -p <pid>`** — a "still running" claim without your own output is a rejection.
- **Recompute the doc sha256 yourself** and compare to the demo's table; autosave claimed but not on disk is a rejection.
- **Watch the recording** and confirm all four operations actually occur, in the product, not in a mock.
- **Reject** if any post-boundary check shares a turn with the launch, if fewer than two boundaries were crossed, or if the launcher rung is not named.
- **Reject** if the recording shows any canvas mechanic — that is Phase 3 scope leaking into Demo 2.

## Dev Learnings

_Not Done until filled. Required: which rung was in use, and anything the live surface did across a boundary that the unit tests did not predict._

## QA Learnings

_Not Done until filled. Required: which demonstrated claim was weakest under independent re-probing._
