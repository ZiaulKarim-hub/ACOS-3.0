# S14-concept-document-synthesis — Concept-document synthesis, inline, with the refusal requirement

| Field | Value |
|---|---|
| Epic / Story | E3 / ST-04 |
| Type · MoSCoW · Size | build · MUST · S `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S13-interview-engine-tiers-waves-branching |
| Requirements | FR-038 |
| Acceptance criteria | A5 · SL-S14-1 · SL-S14-2 |
| CQ / evidence | CQ1 |

## PM — slice definition

**Objective.** Turn answers into a 200–300 word concept document the human recognises, and refuse to advance to the prompt step without a stated refusal.

**In scope.** Inline synthesis against `prompts/interview-synthesizer.md` executed by the main session with already-declared tools; `00-interview/concept.md` containing a point of view, **at least three abstracted references from different eras/genres/cultures**, a restraint budget and **at least one thing the site refuses to do**; the hard stop when the refusal is missing; the final `answers.json` shape.

**Out of scope.** Any subagent call (mid-skill availability is unresolved and nothing may depend on it). Prompt generation (S16). Judging the concept's quality — the human is the only aesthetic judge.

**Allowed files / contexts.**
- `prompts/interview-synthesizer.md`, `scripts/steps/step1.ts` (extend), `00-interview/{concept.md,answers.json}` (write).

**Steps.**
1. Write the synthesis rubric as a prompt file; state in it that it is executed inline.
2. Implement synthesis in the main session: read the rubric, produce the document, validate it, write it.
3. Validate structurally: word count 200–300; ≥3 distinct references; a restraint budget; a non-empty refusal clause.
4. Block advancement to Step 2 when the refusal is missing, with a message naming what is missing.
5. Finalise `answers.json`: question-ID-keyed, tier-tagged, `source ∈ {asked, pre-filled, inferred-default, skill-default}`, override flag.

**Definition of Done.**
- Artifacts: rubric, synthesis code, a sample `concept.md`, a sample `answers.json`.
- Validation: a fixture without a refusal is blocked; a fixture with one advances; word count and reference count are computed, not eyeballed.
- `slice.yaml` mapping — `acceptance_criteria: [A5, SL-S14-1, SL-S14-2]`, `verification_method: exit-code` (SL-S14-1: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-038 → file:line; (3) structural quality — validation is a pure function over the document; (4) functional testing — both fixtures with recorded exit codes; (5) security/compliance — no external call; (6) operational — what a user does when the refusal is genuinely hard to state; (7) self-assessment.

## QA — zero-trust verification

- **Recompute** the word count and the reference count yourself from the produced document.
- **Run your own** grep proving no subagent call exists on this path.
- **Run the no-refusal fixture yourself** and confirm the pipeline actually stops rather than warning.
- **Read `answers.json`** and confirm every entry carries a source value from the closed set.
- **Reject** if the synthesis silently invents a reference the interview never supplied — spot-check three references against the answers.

## Dev Learnings

_Not Done until filled. Required: whether the refusal requirement produced a better concept or an annoyed user, and how the rubric handled sparse answers._

## QA Learnings

_Not Done until filled. Required: whether any concept content could not be traced back to an answer._
