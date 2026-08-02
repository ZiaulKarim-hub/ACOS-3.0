# S18-import-parser-and-envelope-validation — Tolerant FILE-block parser with envelope validation and no partial writes

| Field | Value |
|---|---|
| Epic / Story | E5 — Step 3 ingest / ST-06 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S17-stage-b-envelope-and-chunking |
| Requirements | FR-050, FR-051 |
| Acceptance criteria | A7 · A8 · SL-S18-1 |
| CQ / evidence | CQ13 |

## PM — slice definition

**Objective.** Ingest a complete chunk in a single paste, and fail a truncated chunk loudly **without writing a partial system**.

**In scope.** A tolerant parser splitting on fenced `FILE:` blocks; envelope validation (declared file list, per-file line counts, hash prefixes, terminator presence); staging to a temporary area and promoting atomically only when the whole chunk validates; a failure message naming the missing files.

**Out of scope.** Code safety validation (S19) — that is a separate layer with a different failure mode. Contrast re-verification (S19). Repair-prompt emission (S19).

**Allowed files / contexts.**
- `scripts/steps/step3.ts`, `scripts/lib/import-parser.ts`, `scripts/lib/envelope.ts` (reuse), `.wb/tmp/import/**` (staging), `02-system/**` (promote only).

**Steps.**
1. Read the clipboard content; split on fenced `FILE:` headers into per-file payloads.
2. Validate against the envelope: every declared file present, line counts equal, hash prefixes equal, terminator present and matching this run.
3. Stage every parsed file under the temporary import area; **never write into the system directory during parsing**.
4. On full validation, promote atomically (write-temp then rename) and record the result.
5. On any mismatch, delete the staging area, write nothing to the system directory, and print the missing or mismatched files by name.

**Definition of Done.**
- Artifacts: parser, validation, staging/promotion, both fixtures (complete and truncated).
- Validation: a directory hash of the system tree before and after the truncated fixture is **identical**.
- `slice.yaml` mapping — `acceptance_criteria: [A7, A8, SL-S18-1]`, `verification_method: exit-code` (SL-S18-1: `hash-compare`).

## Dev — execution contract

Never `rm -rf`; remove the staging directory with a scoped delete of known paths. Evidence bundle: (1) summary; (2) traceability FR-050, FR-051 → file:line; (3) structural quality — parsing is pure over a string; (4) functional testing — both fixtures with the before/after directory hashes; (5) security/compliance — note explicitly that this layer does **not** make the payload safe; S19 owns that; (6) operational — one-paste ingest instructions; (7) self-assessment.

## QA — zero-trust verification

- **Run the truncated fixture yourself** and hash the system directory before and after; any difference is a rejection.
- **Confirm the failure message names the missing files**, not a generic error.
- **Corrupt one line count** by hand and confirm the ingest refuses.
- **Replay a previous run's payload** and confirm the terminator mismatch refuses it.
- **Reject** if any parsed file was written outside the staging area before validation.

## Dev Learnings

_Not Done until filled. Required: which paste path produced the cleanest fenced blocks in practice (feeds back into S06's findings)._

## QA Learnings

_Not Done until filled. Required: whether the staging/promotion boundary was airtight under a partial write._
