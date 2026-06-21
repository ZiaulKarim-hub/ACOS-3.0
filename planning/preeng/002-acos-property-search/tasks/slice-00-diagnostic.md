# slice-00-diagnostic — Diagnostics + decision lock (problem-before-solution)

- **Parent story:** STORY-APS-00 · **Parent epic:** EPIC-APS-00 · **Demo:** Demo 0
- **Effort:** S · **Dependency order:** 1 · **Depends on:** (none)
- **Lattice refs:** cq-01, cq-09, cq-10, cq-14, cq-17, meth-union, meth-hubguard, meth-blindswarm, pat-decisiondefaults, risk-nofree, risk-legal

## PM Section (Planner / Specifier — LCE)

### Objective
Lock the problem before any build. Confirm symptoms/hypotheses/unknowns from `spec.md` Diagnostics;
**validate H1** (widest net = union of channels/pivots, not one search), **H2** (blind isolation makes
"Verified = 2+ sources" non-circular), **H3** (no hub-guard => N^2 blow-up); and **record D1-D8** plus the
free-only / stdlib-only / blocking-compliance ground rules in an `acos-decide` ADR. **No solution code.**

### Scope
**In scope:** a diagnostic note confirming H1/H2/H3 against PLAN.md; an ADR (via `acos-decide`) capturing
D1 (embed swarm), D2 (Markdown v1 / doc-render v2), D3 (hard blocking gate), D4 (channels 1-4 + recorder
full), D5 (v1 script set), D6 (75/50 tiers), D7 (hub threshold 25), D8 (hop limit 2).
**Out of scope:** any script, SKILL.md logic, or external lookup.

### Guardrails / Allowed files
- `planning/preeng/002-acos-property-search/tasks/slice-00-diagnostic.md` (this file; learnings)
- the ADR file produced by `acos-decide` (its own conventional location)
- `.acos/evidence/[DATE]/slice-00-diagnostic/`
- Prohibited: creating any `scripts/*.py`, `SKILL.md`, or reference data file; any network call.

### Definition of Done
- [ ] H1/H2/H3 explicitly confirmed (or refined) against PLAN.md, with rationale — pass-condition: each hypothesis has a written verdict.
- [ ] An `acos-decide` ADR records D1-D8 with chosen defaults + alternatives — pass-condition: ADR exists and lists all eight.
- [ ] Free-only / stdlib-only / blocking-compliance / hedged-language ground rules recorded — pass-condition: each rule named.
- [ ] Open unknowns (portal availability, false-positive rate at cutoffs) routed to slice-11 — pass-condition: routing noted.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Re-read `spec.md` Diagnostics + PLAN.md §§1-4, 16-17; write a one-paragraph verdict per hypothesis.
2. Run `acos-decide` to author the ADR capturing D1-D8 (defaults + alternatives from PLAN.md §16).
3. Record the ground rules and route the two empirical unknowns to slice-11.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (H1/H2/H3 -> spec Diagnostics; D1-D8 -> PLAN.md §16 / EV-024); Quality (ADR
well-formed); Functional (n/a — structural: hypotheses + decisions present); Security/Compliance (records
the blocking-gate + free-only rules); Operational (no code, no network); Self-assessment.

### Dev Learnings
- (fill at execution) Which hypothesis was sharpest; any default reconsidered.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Confirm each of H1/H2/H3 has a written verdict grounded in PLAN.md, not hand-waving.
2. Confirm the ADR lists all eight decisions with chosen default + at least one alternative each.
3. Confirm no scripts/SKILL.md/reference files or network calls were produced (scope respect).
4. Confirm the empirical unknowns are routed to slice-11.

### Evidence gates (all must pass)
- [ ] H1/H2/H3 verdicts present and grounded.
- [ ] ADR captures D1-D8 (default + alternative).
- [ ] Ground rules (free-only, stdlib-only, blocking-compliance, hedged-language) recorded.
- [ ] Scope respected (no code, no network).
- [ ] Learnings updated.

### QA Learnings
- (fill at execution) Any decision QA judged under-justified.
