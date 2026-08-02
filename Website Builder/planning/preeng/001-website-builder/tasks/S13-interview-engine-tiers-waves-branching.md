# S13-interview-engine-tiers-waves-branching — Interview engine: tiers, waves, real branch map, policy questions, instrumentation

| Field | Value |
|---|---|
| Epic / Story | E3 / ST-04 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S12-interview-bank-90-questions |
| Requirements | FR-031, FR-032, FR-034, FR-035, FR-036, FR-037, FR-039 |
| Acceptance criteria | A3 (recorded unachievable as written) · SL-S13-1 · SL-S13-2 · SL-S13-3 |
| CQ / evidence | CQ1 · CQ11 · EL-060 |
| Risk | R21 — the interview is where the user's time is spent worst |

## PM — slice definition

**Objective.** Deliver the interview in hard-gated waves with honest tier semantics, a branch map that matches the bank, and elapsed-time instrumentation from the first run.

**In scope.** Tier semantics (T1 gates the prompt and is satisfied by a real answer **or** an explicit "I don't know / surprise me" that records a **stated concrete default**, never a null; T2 just-in-time, recorded not-applicable when its moment never arrives; T3 inferred with a visible "change this", bundled into one end-of-interview review in fast mode); waves of 5–8 questions with a shrinking progress count, visual alternating with verbal; Wave 0 first carrying the continuity and policy questions; the real branch map; the language and site-type questions; the structural-RTL and audience-access-needs questions; per-question elapsed timing.

**Out of scope.** Concept synthesis (S14). RTL **layout** (asked, not built). Loosening any gate threshold from an interview answer — the access-needs answer may only tighten.

**Allowed files / contexts.**
- `scripts/steps/step1.ts`, `scripts/lib/interview-engine.ts`, `scripts/lib/branch-map.ts`, `00-interview/answers.json` (write), `scripts/selftest.ts` (extend).

**Steps.**
1. Implement wave delivery with the shrinking count and the visual/verbal alternation; Wave 0 always first.
2. Implement tier semantics exactly, including the stated-default path with `source: skill-default`.
3. Encode the branch map as data: the continuity question gates one taste question and conditionally one motion question; the first localisation question prunes its three followers; the jurisdiction pair prunes one compliance question but **not** the third; the density question is **not** a branch root and prunes nothing; a no-forms answer skips both form questions.
4. Implement the two policy questions: the time-budget answer sets branching aggressiveness, tier reach and variant rounds; the variant-count answer sets the multiplier.
5. Ask the language question (needed for the document language attribute) and the site-type question mapped one-to-one to the structured-data types the gates require, always shown for confirmation and never silently applied.
6. Ask the structural-RTL question and the audience-access-needs question; route the latter through a function that can only tighten a threshold.
7. Instrument `askedAtMs`/`answeredAtMs` per question and write a session duration summary.

**Definition of Done.**
- Artifacts: engine, branch map, `answers.json` with source and override fields, selftest assertions for the branch map and the tighten-only rule.
- Validation: the fast-mode fixture records the measured Tier-1 count (expected 45–55) rather than asserting the older ≤45 figure; the tighten-only assertion fails if a loosening path is introduced.
- `slice.yaml` mapping — `acceptance_criteria: [A3, SL-S13-1, SL-S13-2, SL-S13-3]`, `verification_method: exit-code`.

## Dev — execution contract

Evidence bundle: (1) summary with the measured fast-mode question count and elapsed time; (2) traceability FR-031…FR-039 → file:line; (3) structural quality — branch map is data; (4) functional testing — three fixture runs (one sitting, a few sessions, open-ended) with recorded counts and durations; (5) security/compliance — the access-needs tighten-only assertion; (6) operational — resuming a partially completed interview from disk; (7) self-assessment: **all duration figures are projections until these measurements exist.**

## QA — zero-trust verification

- **Re-run** the fast-mode fixture and count answered questions yourself.
- **Attempt** to answer a Tier-1 question with "surprise me" and confirm the stored value is a concrete default, not null.
- **Attempt** to introduce a loosening threshold change through the access-needs path in a scratch branch and confirm the selftest fails.
- **Verify the branch map by table**, question by question, against the bank — especially that the density question prunes nothing.
- **Reject** if elapsed timing is absent; every published duration is otherwise unfalsifiable.

## Dev Learnings

_Not Done until filled. Required: the measured fast-mode count and duration, and which wave ran longest._

## QA Learnings

_Not Done until filled. Required: whether the branch map matched the bank on first pass, and which tier semantic was easiest to implement incorrectly._
