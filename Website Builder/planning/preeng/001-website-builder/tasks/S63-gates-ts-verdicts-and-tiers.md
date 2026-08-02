# S63-gates-ts-verdicts-and-tiers — Structured gate verdicts and the four severity tiers

| Field | Value |
|---|---|
| Epic / Story | E17 / ST-21 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 5 / — |
| Depends on | S23-versioned-coherence-lint-set · S25-pure-renderer-and-resolution-policy |
| Requirements | FR-230, FR-233, FR-237 |
| Acceptance criteria | SL-S63-1 · SL-S63-2 · SL-S63-3 |
| CQ / evidence | CQ11 · EL-061 |
| Note | **§13.4 gate 20 is the canonical performance threshold statement.** A66 (omits INP) and A67 (flat ≤2MB vs ≤1.5–2MB) are recorded **inconsistent** with it and owe a §19 edit — this slice encodes gate 20's numbers, not theirs |

## PM — slice definition

**Objective.** Give every gate one shape — measured value, threshold, verdict, evidence reference — and never throw on a normal fail.

**In scope.** `GateResult` `{gateId, tier: 0|1|2|3, status: "pass"|"fail"|"inconclusive", measured, threshold, evidenceRef, waiver?}` returned by every gate; **INCONCLUSIVE blocks exactly like a fail**; `gate-report.json` `{runId, at, gates[], waivers[], summary}`; the **four tiers enforced in code** — Tier 0 blocks the individual placement/edit inline, Tier 1 blocks **LOCK only** and never interrupts live editing, Tier 2 is advisory, dismissible and batched into the **Design Health pill** (never a toast stream), Tier 3 is a silent end-of-session record; repeated violations collapsing into **one counted badge**; the canonical performance thresholds from **§13.4 gate 20** — LCP ≤2.5s · CLS ≤0.1 (internal stretch 0.05) · INP ≤200ms (or TBT ≤600ms floor / 300ms aspirational as proxy) · pre-LCP transfer ≤1.5–2MB — recorded with the A66/A67 inconsistency noted.

**Out of scope.** Running the live checks (S64) and the lock-time checklist (S68) — this slice ships the shape, the tier engine and at least two real gates so the increment is demo-able, not a scaffold. Capture (S65).

**Allowed files / contexts.**
- `scripts/lib/gates.ts`, `scripts/lib/tiers.ts`, `scripts/lib/gate-report.ts`, `07-lock/gate-report.json` (write), the Design Health pill's consumption point.
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.**

**Steps.**
1. Define `GateResult` and make every gate a function returning it; a thrown exception on a normal fail is a defect, not a style issue.
2. Map `inconclusive` to the same blocking behaviour as `fail` at every consumption point.
3. Implement the tier engine as data-driven routing: tier decides the consequence, the gate never decides its own consequence.
4. Implement the badge collapse: N violations of one gate become one badge carrying N.
5. Ship at least two real gates end to end (one Tier 0, one Tier 1) writing a real `gate-report.json`.
6. Encode gate 20's thresholds as the canonical set and record in the report that A66 and A67 are inconsistent and owe a §19 edit.

**Definition of Done.**
- Artifacts: `gates.ts`, the tier engine, `gate-report.json`, the two shipped gates, the recorded A66/A67 inconsistency.
- Validation: a forced failure returns a verdict rather than an exception; an inconclusive verdict blocks like a fail; each tier produces its documented consequence; ten identical violations show one badge reading 10.
- Demo-able increment: trigger a Tier 0 violation in the editor and watch the edit blocked, then a Tier 2 and watch it land in the pill.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S63-1, SL-S63-2, SL-S63-3]`, `verification_method: exit-code` (SL-S63-3: `manual-observation`).

## Dev — execution contract

Evidence bundle: (1) summary listing every gate with its tier; (2) traceability FR-230, FR-233, FR-237 → file:line; (3) structural quality — one verdict type, one report writer, tiers as data; (4) functional testing — the forced-failure fixture, an inconclusive fixture, one fixture per tier, the badge-collapse fixture; (5) security/compliance — the report records waivers explicitly and never silently skips; (6) operational — how a waiver is recorded and who may set one; (7) self-assessment noting that the lock wall-clock target is `[I]` and unmeasured (EL-061).

## QA — zero-trust verification

- **Force a gate to fail yourself** and confirm a verdict object comes back; an exception is a rejection.
- **Force an inconclusive** and confirm it blocks identically to a fail — "logged as inconclusive, proceeded anyway" is a rejection.
- **Exercise all four tiers** and observe the consequence yourself; a Tier 2 finding shown as a toast is a rejection.
- **Fire the same violation ten times** and count the badges; ten badges is a rejection.
- **Read the encoded thresholds** and reject if A66's or A67's numbers were used instead of §13.4 gate 20's, or if the inconsistency is unrecorded.

## Dev Learnings

_Not Done until filled. Required: which gate wanted to throw rather than return, and how inconclusive was distinguished from a crash._

## QA Learnings

_Not Done until filled. Required: whether any consumption point treated inconclusive as a pass._
