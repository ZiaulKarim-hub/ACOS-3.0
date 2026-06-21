# slice-07-entity-discovery-loop-integration — Entity discovery wiring + graph-expansion loop (Demo 1)

- **Parent story:** STORY-APS-07 · **Parent epic:** EPIC-APS-07 · **Demo:** Demo 1
- **Effort:** M · **Dependency order:** 8 · **Depends on:** slice-06-swarm-synthesizer
- **Lattice refs:** cq-06, proc-entitydisc, proc-loop, meth-graph, meth-union, ent-reportv1, meth-hedged, proc-audit, ent-auditartifact

## PM Section (Planner / Specifier — LCE)

### Objective
Wire **SoS + OpenCorporates entity discovery** into the graph (person→officer/agent→entities→siblings) and
integrate the full thin pipeline in `SKILL.md`: **compliance gate → normalize → identity → entity
discovery → channels → swarm → synthesizer**, looping until dry. Produce a **hedged thin Markdown report**
plus the **audit trail** on a sample name. This is **Demo 1** (the compliant thin slice end to end).

### Scope
**In scope:** entity-discovery adapter (SoS + OpenCorporates, hub-guarded via slice-04, cached via
slice-02); SKILL.md orchestration tying the stages into the loop-until-dry; a thin hedged report stub +
`workspace/<sid>/` audit artifacts.
**Out of scope:** dedup (slice-08); scoring (slice-09); equity rollup (slice-10); the full dossier (slice-11).

### Guardrails / Allowed files
- `.claude/skills/acos-property-search/SKILL.md` (orchestration section)
- `.claude/skills/acos-property-search/scripts/entity_discovery.py` (stdlib only) + its test
- this task file + `.acos/evidence/[DATE]/slice-07-entity-discovery-loop-integration/`
- Prohibited: bypassing the compliance gate; un-hedged language in the report; expanding through hubs;
  paid APIs.

### Definition of Done
- [ ] Entity discovery resolves a seed person to controlled entities (officers/agents/siblings) and feeds the graph, hub-guarded — pass-condition: entity-discovery test.
- [ ] The end-to-end thin loop runs gate→normalize→identity→discovery→channels→swarm→synthesizer and terminates — pass-condition: e2e thin-path test on a sample fixture.
- [ ] The report uses **hedged language** throughout ("likely controlled by"; "owns" only with direct title) — pass-condition: **hedged-language test (REQUIRED)**.
- [ ] An audit trail (`workspace/<sid>/round-NN/agent-NN/findings.md` + synthesis/) is written and resumable — pass-condition: audit-trail test.
- [ ] Nothing runs while `COMPLIANCE_BLOCKED` — pass-condition: gate-respect test.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. `entity_discovery.py`: query SoS + OpenCorporates (cached); add entity/officer/agent nodes + edges via
   the graph engine (hub-guarded).
2. SKILL.md: sequence the stages into the loop; the synthesizer drives the worklist until no new
   high-confidence nodes.
3. Render a thin hedged report; write audit artifacts per round.
4. Tests: entity discovery, e2e thin path, hedged language, audit trail, gate respect.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (proc-entitydisc/loop, meth-union/hedged, EV-006/020/021); Quality (stdlib);
Functional (the DoD tests); Security/Compliance (gate-first, free, hedged); Operational (resumable audit
trail); Self-assessment.

### Dev Learnings
- (fill at execution) Loop-termination behavior on the sample; any hub that needed pruning during discovery.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Run the thin loop on a fresh sample fixture; confirm it terminates and writes the audit trail.
2. Scan the report for un-hedged claims ("definitely owns" / bare "owns" without title support) — any = REJECT.
3. Confirm entity discovery is hub-guarded (no sibling expanded through a commercial agent).
4. Confirm the gate blocks a run with no ComplianceRecord.

### Evidence gates (all must pass)
- [ ] **Hedged language throughout** (hard; fail = REJECT).
- [ ] E2E thin loop terminates with audit trail.
- [ ] Entity discovery hub-guarded.
- [ ] Compliance gate respected.
- [ ] Learnings updated.

### QA Learnings
- (fill at execution) Any un-hedged phrasing or gate bypass found.
