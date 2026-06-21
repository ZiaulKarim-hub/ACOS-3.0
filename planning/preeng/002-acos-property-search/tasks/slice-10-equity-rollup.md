# slice-10-equity-rollup — Estimated equity / value / debt rollup

- **Parent story:** STORY-APS-10 · **Parent epic:** EPIC-APS-10 · **Demo:** -
- **Effort:** M · **Dependency order:** 11 · **Depends on:** slice-09-scoring-review-flags
- **Lattice refs:** cq-16, meth-rollup, ent-equity, ent-loan, anti-fabricate, risk-equitymisread, std-freeonly

## PM Section (Planner / Specifier — LCE)

### Objective
Implement `rollup.py`: per confirmed parcel, compute an **estimated** equity picture from **FREE** data —
assessed value (flag "assessed, not market; assessment ratio varies by state"), last sale price + date,
original recorded mortgage/deed-of-trust amount + date with a **stated amortization assumption** for the
remaining balance, and **estimated equity = value − estimated encumbrances**. Flag "no mortgage data found"
where relevant. **Every figure is labeled "estimated"; true AVM / current payoff is stated as a limitation,
never fabricated.** Roll up per portfolio.

### Scope
**In scope:** `scripts/rollup.py` (per-parcel + per-portfolio estimated equity; explicit labels + flags;
amortization assumption clearly an estimate).
**Out of scope:** report rendering (slice-11); paid AVM data (excluded).

### Guardrails / Allowed files
- `.claude/skills/acos-property-search/scripts/rollup.py` (stdlib only)
- `.claude/skills/acos-property-search/scripts/tests/test_rollup.py`
- this task file + `.acos/evidence/[DATE]/slice-10-equity-rollup/`
- Prohibited: presenting an estimate as an AVM; fabricating a payoff; any paid-data call; an unlabeled figure.

### Definition of Done
- [ ] Each figure (assessed value, last sale, mortgage, remaining balance, equity) is explicitly labeled "estimated" — pass-condition: **labeling test (REQUIRED; an unlabeled figure = REJECT)**.
- [ ] Estimated equity = value − estimated encumbrances, using the stated amortization assumption — pass-condition: equity-math test (hand-recompute).
- [ ] A parcel with no mortgage data carries a "no mortgage data found" flag (no fabricated debt) — pass-condition: **no-data flag test (REQUIRED)**.
- [ ] True AVM / current payoff is stated as a limitation, never produced — pass-condition: no-AVM test.
- [ ] Portfolio rollup sums per-parcel estimates with the same labeling — pass-condition: portfolio test.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Implement per-parcel estimate: pull assessed value + last sale + original mortgage; apply a stated
   amortization assumption for the remaining balance; equity = value − encumbrances.
2. Attach explicit "estimated" labels + flags ("assessed, not market"; "no mortgage data found").
3. Portfolio rollup.
4. Tests: labeling, equity math (hand-recomputed), no-data flag, no-AVM, portfolio.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (meth-rollup, ent-equity/loan, anti-fabricate, risk-equitymisread, EV-017,
std-freeonly); Quality (stdlib); Functional (the five DoD tests); Security; Operational; Self-assessment.

### Dev Learnings
- (fill at execution) Amortization-assumption model; how labeling is structurally guaranteed.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Scan every output figure for an "estimated" label — any unlabeled figure = REJECT.
2. Re-author a no-mortgage parcel; confirm the "no mortgage data found" flag and NO fabricated debt.
3. Hand-recompute estimated equity for one parcel.
4. Confirm no AVM/current-payoff value is produced (only a stated limitation).

### Evidence gates (all must pass)
- [ ] **Every figure labeled "estimated"** (hard; fail = REJECT).
- [ ] **No fabricated debt; no-data flagged** (hard; fail = REJECT).
- [ ] Equity math correct; no AVM produced.
- [ ] Learnings updated.

### QA Learnings
- (fill at execution) Any figure that read as a market valuation.
