# S20-local-regeneration-mode — Local Regeneration Mode: the zero-paste path

| Field | Value |
|---|---|
| Epic / Story | E5 / ST-06 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S19-ast-validator-quarantine-and-reverification |
| Requirements | FR-056 |
| Acceptance criteria | A12 · SL-S20-1 |
| CQ / evidence | CQ18 |
| Risk | R7 — the hand-carry is the most likely quiet death of the product; this slice is what makes the web hop optional |

## PM — slice definition

**Objective.** Produce a design-system bundle locally, from the identical prompt, with **zero pastes**, that passes the identical validator.

**In scope.** Running the same Stage-A/Stage-B prompt content through a local path in the main session; emitting the identical envelope-wrapped format; routing the output through the same importer and validator; a mode flag on the skill invocation.

**Out of scope.** A different prompt, a different format, or a "simplified" local path — divergence here silently creates two products. Any subagent dependency.

**Allowed files / contexts.**
- `scripts/lib/local-regen.ts`, `scripts/steps/step3.ts` (extend), `02-system/**` via the existing importer only.

**Steps.**
1. Read the same prompt artifacts the hand-carry path emits — no separate template.
2. Produce the response inline in the main session and write it to the same staging area the paste path uses.
3. Run the identical envelope validation and AST validation over it.
4. Record in `import-report.json` that the bundle arrived by the local path, so provenance stays honest.
5. Add the mode flag and document that it is a first-class path, not a fallback.

**Definition of Done.**
- Artifacts: local-regeneration module, a produced bundle, its import report.
- Validation: the same validator binary accepts both a pasted fixture and a locally produced bundle; a diff of the two formats shows the same envelope structure.
- `slice.yaml` mapping — `acceptance_criteria: [A12, SL-S20-1]`, `verification_method: exit-code`.

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-056 → file:line; (3) structural quality — one importer, two producers; (4) functional testing — both bundles validated by the same code path, with recorded exit codes; (5) security/compliance — the local path still goes through the AST validator, because the same mistakes are possible; (6) operational — when a user should choose it (long chunks, repeated Step-5 loops); (7) self-assessment.

## QA — zero-trust verification

- **Run the validator yourself** over the locally produced bundle and record your own exit code.
- **Diff the envelope structure** of a pasted and a local bundle yourself.
- **Reject** if the local path bypasses any validation step the paste path runs — the whole point is one validator.
- **Reject** if the local path uses a different prompt or a different output schema.
- **Confirm the import report records the arrival path**; provenance is not optional.

## Dev Learnings

_Not Done until filled. Required: whether the local path actually removed pastes end-to-end, and where the format was tempted to diverge._

## QA Learnings

_Not Done until filled. Required: whether both producers can be kept in step long-term, or whether one will drift._
