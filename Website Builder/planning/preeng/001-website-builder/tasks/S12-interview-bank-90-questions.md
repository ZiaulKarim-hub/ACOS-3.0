# S12-interview-bank-90-questions — The 90-question interview bank with its ID grammar

| Field | Value |
|---|---|
| Epic / Story | E3 — Step 1 interview / ST-04 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S09-install-config-session-selftest |
| Requirements | FR-030, FR-033 |
| Acceptance criteria | SL-S12-1 · SL-S12-2 |
| CQ / evidence | CQ1 · EL-060 |
| Volume of record | **90 questions `[V — §5 row-count self-audit; NA-01]`**, not the 78 carried elsewhere |

## PM — slice definition

**Objective.** Author the question bank as a reference file with stable ids, correct tier labels, and no id collision with the tier notation.

**In scope.** `references/interview-bank.md` carrying all 90 questions with `<wave-prefix><n>` ids from the reserved prefix set (`C, P, B, A, TS, D, M, N, X, L, G, H, U, Z, V`); tier tags; wave assignment; the branch-root annotations the engine will read; a mechanical row-count assertion.

**Out of scope.** The engine (S13). Concept synthesis (S14). Reducing the bank — any cut is a scope decision and belongs to the user, not to this slice.

**Allowed files / contexts.**
- `references/interview-bank.md` (new), `scripts/lib/interview-bank.ts` (parser + assertions), `scripts/selftest.ts` (extend).

**Steps.**
1. Author all 90 rows with id, tier, wave, question text, answer type, branch role and pre-fill source.
2. Name the ten taste questions `TS1`–`TS10`. **Never `T1`–`T10`** — those collide with the tier labels and break the directive-to-question traceability criterion.
3. Add a parser that reads the bank into typed records and a selftest assertion for the row count.
4. Add a selftest assertion that no question id matches `^T[0-9]`.
5. Record in the file's own header that A3 ("≤45 answered") is **unachievable as written** against this bank, and that the source itself says to move it to ≤55 or cut the bank.

**Definition of Done.**
- Artifacts: the bank, the parser, two selftest assertions.
- Validation: parsed row count is exactly 90; the `^T[0-9]` grep returns zero; every id is unique.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S12-1, SL-S12-2]`, `verification_method: exit-code` (SL-S12-2: `grep-assert`).

## Dev — execution contract

Do not silently drop questions to hit an older number. Evidence bundle: (1) summary with the counted total; (2) traceability FR-030, FR-033 → bank sections; (3) structural quality — the bank is data, parsed once; (4) functional testing — parser output plus both assertions; (5) security/compliance — n/a, note it; (6) operational — how a question is added without breaking ids; (7) self-assessment, including that the duration implications are inference.

## QA — zero-trust verification

- **Recount the rows yourself** with your own command and compare to 90; a stated count is not evidence.
- **Run your own** `grep -nE '^\|\s*T[0-9]' references/interview-bank.md` and require zero.
- **Check uniqueness yourself** by sorting ids and diffing against their unique set.
- **Reject** if any question was removed to make an older acceptance criterion pass.
- **Reject** if the A3 note is missing — a criterion known to be unachievable must be recorded, not quietly satisfied.

## Dev Learnings

_Not Done until filled. Required: which waves carry the most Tier-1 weight, and where a cut would hurt least if the user later asks for one._

## QA Learnings

_Not Done until filled. Required: whether the id grammar survived authoring without a collision._
