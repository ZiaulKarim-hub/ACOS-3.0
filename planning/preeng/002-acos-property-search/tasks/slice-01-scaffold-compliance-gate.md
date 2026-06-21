# slice-01-scaffold-compliance-gate — Skill scaffold + BLOCKING compliance gate

- **Parent story:** STORY-APS-01 · **Parent epic:** EPIC-APS-01 · **Demo:** -
- **Effort:** M · **Dependency order:** 2 · **Depends on:** slice-00-diagnostic
- **Lattice refs:** cq-17, proc-compliancegate, std-dppa, std-fcra, std-fdcpa, std-glba, std-scraping, std-skillform, ent-compliancerec, risk-legal, metric-compliance, anti-nocompliance

## PM Section (Planner / Specifier — LCE)

### Objective
Scaffold the project skill and implement the **BLOCKING compliance gate**. The skill must be
explicit-invocation-only (`disable-model-invocation: true`, `user-invocable: true`). Until a complete,
valid `ComplianceRecord` is captured, the run state is `COMPLIANCE_BLOCKED` and **no external lookup is
permitted**. GLBA anti-pretexting is a **hard block**.

### Scope
**In scope:** `SKILL.md` skeleton (frontmatter + command surface + gate-first orchestration stub);
`references/compliance.md` (permissible-purpose statute mapping + per-run record schema); gate logic that
captures permissible purpose (DPPA §2721(b)(3)/(b)(4); FCRA §1681b; dossier flag "asset location — NOT for
eligibility"), debt classification (consumer/commercial -> FDCPA scope), GLBA hard-block acknowledgment,
and scraping posture.
**Out of scope:** cache (slice-02), normalize/identity (slice-03), any channel/graph/swarm logic.

### Guardrails / Allowed files
- `.claude/skills/acos-property-search/SKILL.md` (scaffold only)
- `.claude/skills/acos-property-search/references/compliance.md`
- `.claude/scripts/aps_compliance.py` (stdlib only — validates + records the ComplianceRecord) and its test
- this task file + `.acos/evidence/[DATE]/slice-01-scaffold-compliance-gate/`
- Prohibited: any external network call from this slice; any channel/graph code; weakening the gate to
  non-blocking.

### Definition of Done
- [ ] Skill frontmatter sets `disable-model-invocation: true` + `user-invocable: true` — pass-condition: frontmatter assertion test.
- [ ] An incomplete/absent ComplianceRecord leaves state `COMPLIANCE_BLOCKED` and refuses all downstream work — pass-condition: **negative-case block test (REQUIRED; fail = REJECT)**.
- [ ] A complete record (purpose+statutes, debt class, GLBA ack, posture) transitions out of the blocked state — pass-condition: positive-case test.
- [ ] A GLBA-pretexting request (obtain financial info by misrepresentation) is refused outright — pass-condition: **GLBA hard-block negative test (REQUIRED; fail = REJECT)**.
- [ ] `references/compliance.md` documents the statute mapping + record schema — pass-condition: schema fields present.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Author `SKILL.md` frontmatter + a gate-first orchestration stub that calls the compliance validator
   before anything else.
2. Implement `aps_compliance.py`: build + validate a `ComplianceRecord`; expose `is_cleared(record)`;
   refuse a GLBA-pretexting purpose.
3. Write `references/compliance.md` (statute mapping + per-run schema).
4. Tests: positive (complete record clears), negative (incomplete -> blocked), GLBA hard-block.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (proc-compliancegate, std-dppa/fcra/fdcpa/glba/scraping, EV-018, NFR-Compliance);
Quality (stdlib only); Functional (positive + the two REQUIRED negatives); Security/Compliance (the gate IS
the security control); Operational (no network in this slice); Self-assessment.

### Dev Learnings
- (fill at execution) How the blocked-state invariant is enforced so no caller can skip it.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Re-author the negatives yourself: an empty record and a partial record (missing GLBA ack) MUST leave
   state `COMPLIANCE_BLOCKED`. Any downstream work permitted = REJECT.
2. Re-author a GLBA-pretexting purpose; confirm it is refused outright.
3. Confirm frontmatter is explicit-invocation-only.
4. Attempt to reach any downstream step without clearing the gate; confirm impossible.

### Evidence gates (all must pass)
- [ ] **Blocking enforced — proven by the negative block test** (hard; fail = REJECT).
- [ ] **GLBA hard block proven by negative test** (hard; fail = REJECT).
- [ ] Explicit-invocation-only frontmatter.
- [ ] compliance.md schema complete.
- [ ] Learnings updated.

### QA Learnings
- (fill at execution) Whether any code path could bypass the gate.
