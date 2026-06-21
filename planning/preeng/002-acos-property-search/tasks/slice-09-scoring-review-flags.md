# slice-09-scoring-review-flags — Scoring + confidence tiers + review-flag taxonomy

- **Parent story:** STORY-APS-09 · **Parent epic:** EPIC-APS-09 · **Demo:** -
- **Effort:** M · **Dependency order:** 10 · **Depends on:** slice-08-dedup-apn
- **Lattice refs:** cq-15, meth-scoring, meth-tiers, ent-confidence, ent-reviewflag, meth-conflictpreserve, term-verified, risk-commonname, metric-fpr

## PM Section (Planner / Specifier — LCE)

### Objective
Implement `score.py`: the **merged scoring rubric** → score + per-signal breakdown; **confidence tiers**
(**≥75 high / 50–74 candidate / <50 weak**, configurable); the **hub cap** (score ≤ 40 if the only graph
link runs through a hub); the **common-name penalty**; and emission of **manual-review flags** from the
taxonomy (`references/review-flags.md`).

### Scope
**In scope:** `scripts/score.py` (rubric: +40 owner-of-record exact / +25 tax-mailing / +25 manager-member-
officer / +20 shared phone-email / +10 spouse-associate / +10 per independent corroborating channel
(cap +20); −40 registered-agent-only / −30 common-name-only / −20 hub-virtual-office mailing / −10 inactive-
dissolved / −10 conflicting owner names; cap ≤40 through a hub); tier assignment; review-flag emission;
`references/review-flags.md`.
**Out of scope:** equity rollup (slice-10); report rendering (slice-11).

### Guardrails / Allowed files
- `.claude/skills/acos-property-search/scripts/score.py` (stdlib only; pure/deterministic)
- `.claude/skills/acos-property-search/references/review-flags.md`
- `.claude/skills/acos-property-search/scripts/tests/test_score.py`
- this task file + `.acos/evidence/[DATE]/slice-09-scoring-review-flags/`
- Prohibited: silently resolving a conflict instead of flagging it; exceeding the hub cap; non-deterministic
  scoring.

### Definition of Done
- [ ] The rubric produces the exact documented score for fixture cases, with each +/− signal itemized — pass-condition: rubric test (recompute by hand).
- [ ] Tiers assigned at the 75/50 cutoffs (configurable) — pass-condition: tier-cutoff test.
- [ ] An attribution whose only link runs through a hub is capped at ≤40 (candidate at best) — pass-condition: **hub-cap test (REQUIRED)**.
- [ ] A common-name-only match is penalized (−30) and flagged — pass-condition: common-name test.
- [ ] Conflicting owner names emit a review flag (never silently resolved) — pass-condition: **conflict-flag test (REQUIRED)**.
- [ ] Scoring is deterministic given identical inputs — pass-condition: determinism test.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Implement the rubric as a pure function returning `score`, `signals[]`, `tier`, `capped_through_hub`.
2. Apply the hub cap and the common-name penalty; emit review flags from the taxonomy.
3. Write `references/review-flags.md` (the full taxonomy).
4. Tests: rubric (hand-recomputed), tier cutoffs, hub cap, common-name, conflict flag, determinism.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (meth-scoring/tiers, ent-confidence/reviewflag, EV-015/016, risk-commonname,
metric-fpr); Quality (stdlib, pure); Functional (the six DoD tests); Security; Operational; Self-assessment.

### Dev Learnings
- (fill at execution) Cutoff/penalty tuning notes; corroboration-bonus cap behavior.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Hand-recompute the score for 2 fixtures and compare signal-by-signal.
2. Re-author a hub-only-link case; confirm the score is capped ≤40.
3. Re-author conflicting owner names; confirm a review flag (no silent resolution).
4. Re-run on identical inputs; confirm identical output (determinism).

### Evidence gates (all must pass)
- [ ] **Hub cap (≤40) enforced** (hard; fail = REJECT).
- [ ] **Conflicts flagged, not resolved** (hard; fail = REJECT).
- [ ] Rubric matches hand-recompute; tiers correct.
- [ ] Deterministic.
- [ ] Learnings updated.

### QA Learnings
- (fill at execution) Any mis-scored signal or unflagged conflict.
