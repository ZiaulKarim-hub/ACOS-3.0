# slice-03-normalize-identity — Normalize/classify + Stage-1 identity resolution

- **Parent story:** STORY-APS-03 · **Parent epic:** EPIC-APS-03 · **Demo:** -
- **Effort:** M · **Dependency order:** 4 · **Depends on:** slice-02-cache-fetch-posture
- **Lattice refs:** cq-12, proc-identity, meth-anchors, ent-person, anti-leadasfact, risk-commonname, metric-fpr

## PM Section (Planner / Specifier — LCE)

### Objective
Implement `normalize.py` (person-vs-entity classification; alias / maiden / Jr-Sr / middle-name variants;
fuzzy match) and Stage-1 **identity resolution**: expand aliases, prior addresses, spouse / relatives /
associates from free people-search as **leads only** (corroborate against a primary record before scoring),
and **require ≥2 anchors for common names**. Reconcile the existing `scripts/normalize.py` stub to this.

### Scope
**In scope:** `scripts/normalize.py` (classify + variant generation + fuzzy match); identity-resolution
logic producing new search seeds tagged `leads_only` until corroborated; common-name anchor enforcement.
**Out of scope:** entity discovery against SoS/OpenCorporates (slice-07); graph construction (slice-04).

### Guardrails / Allowed files
- `.claude/skills/acos-property-search/scripts/normalize.py` (stdlib only; reconcile the stub)
- `.claude/skills/acos-property-search/scripts/tests/test_normalize.py`
- this task file + `.acos/evidence/[DATE]/slice-03-normalize-identity/`
- Prohibited: scoring a people-search lead as a fact; using DOB/age outside the gate-bound anchor role.

### Definition of Done
- [ ] Person vs. entity is classified correctly across a fixture set — pass-condition: classification test.
- [ ] Alias / maiden / Jr-Sr / middle-name variants are generated; fuzzy match is deterministic — pass-condition: variant + fuzzy test.
- [ ] People-search-derived seeds are tagged `leads_only` and NOT scorable until corroborated — pass-condition: **leads-only test (REQUIRED; a lead used as a fact = REJECT)**.
- [ ] A common name without ≥2 anchors is refused / down-ranked, not searched broadly — pass-condition: anchor-enforcement test.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Reconcile the `normalize.py` stub: classify input; generate variants; deterministic fuzzy match
   (stdlib `difflib` or an explicit ratio — no external libs).
2. Identity resolution: produce seeds for aliases/spouse/associates, each carrying `leads_only=True` and a
   provenance ref; corroboration flips the flag.
3. Enforce ≥2 anchors for common names.
4. Tests: classification, variants/fuzzy, leads-only, anchor enforcement.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (proc-identity, meth-anchors, anti-leadasfact, EV-012, risk-commonname); Quality
(stdlib, deterministic); Functional (the four DoD tests); Security/Compliance (DOB/age anchor-only,
gate-bound); Operational; Self-assessment.

### Dev Learnings
- (fill at execution) Fuzzy-match threshold choices; how leads-only is structurally enforced.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Re-author a fixture where a people-search lead is uncorroborated; confirm it cannot be scored as a fact.
2. Feed a common name with one anchor; confirm it is refused/down-ranked, not broadly searched.
3. Independently verify variant generation + fuzzy determinism on fresh inputs.

### Evidence gates (all must pass)
- [ ] **Leads-only enforced — proven by negative test** (hard; fail = REJECT).
- [ ] ≥2-anchor rule enforced for common names.
- [ ] Classification + variants + fuzzy deterministic.
- [ ] Learnings updated.

### QA Learnings
- (fill at execution) Whether any lead leaked into scorable state.
