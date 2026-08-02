# S10-warm-start-and-asset-library-detection — Warm-start scan and asset-library detection

| Field | Value |
|---|---|
| Epic / Story | E2 — Step 0 warm start / ST-03 |
| Type · MoSCoW · Size | build · MUST · S `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S09-install-config-session-selftest |
| Requirements | FR-020, FR-021 |
| Acceptance criteria | A1 · A2 |
| CQ / evidence | CQ16 |

## PM — slice definition

**Objective.** Offer any reusable prior system inside the first three exchanges, and determine early whether the artwork category is real for this project or theatre.

**In scope.** Globbing the framework design-library, the skill's own systems directory and the target project's framework directory; offering any hit inside the first three exchanges; asking for and recording an asset-library path in `session.json`; warning immediately when there is none.

**Out of scope.** The identity split and negative constraints (S11). Ingesting assets (S56). Any interview question beyond the continuity questions.

**Allowed files / contexts.**
- `scripts/lib/warmstart.ts`, `scripts/steps/step0.ts`, `session.json` (write).
- Read-only globs over the design-library, systems and project framework directories.

**Steps.**
1. Glob the three source locations; rank hits by recency and by whether they carry a complete token set.
2. Present hits **within the first three exchanges** — later than that and the warm start is decoration.
3. Ask for an asset-library path; validate it exists and is readable; record `assetLibraryPath` in `session.json`.
4. If absent, record the absence explicitly and set the flag the interview reads to warn (consumed by S56).
5. Emit a one-line summary of what was found for the session log.

**Definition of Done.**
- Artifacts: `warmstart.ts`, `step0.ts`, a `session.json` sample for both branches (library present, library absent).
- Validation: a fixture project with a design-library entry produces an offer within three exchanges; a fixture with a real asset path records it; a fixture with none sets the warn flag.
- `slice.yaml` mapping — `acceptance_criteria: [A1, A2]`, `verification_method: exit-code` (A1: `manual-observation`).

## Dev — execution contract

Absolute paths only. Evidence bundle: (1) summary; (2) traceability FR-020, FR-021 → file:line; (3) structural quality — the scan is pure and testable without a session; (4) functional testing — all three fixtures with recorded output; (5) security/compliance — the scan reads only, never writes outside the session; (6) operational — behaviour when a globbed path is unreadable; (7) self-assessment.

## QA — zero-trust verification

- **Count the exchanges yourself** in the transcript; "within three" claimed but not demonstrated is a rejection.
- **Read `session.json`** and confirm `assetLibraryPath` is an absolute, existing path — not a user-typed string accepted unvalidated.
- **Run the absent-library fixture yourself** and confirm the warn flag is set; this is the binary that decides whether the artwork category is real, so a missing flag is a serious defect, not a cosmetic one.
- **Reject** if the scan wrote anything outside the session tree.

## Dev Learnings

_Not Done until filled. Required: what the scan found in practice and whether ranking by recency was the right default._

## QA Learnings

_Not Done until filled. Required: whether the three-exchange rule was honoured under a slow start._
