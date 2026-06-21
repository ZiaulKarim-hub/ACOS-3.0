# slice-05-channels-arcgis-assessor-recorder — Discovery channels 1-4 + recorder index

- **Parent story:** STORY-APS-05 · **Parent epic:** EPIC-APS-05 · **Demo:** -
- **Effort:** L · **Dependency order:** 6 · **Depends on:** slice-04-graph-hubguard
- **Lattice refs:** cq-02, cq-03, cq-04, cq-05, meth-routing, meth-recorderindex, meth-mailpivot, proc-channels, ent-parcel, ent-deed, std-ca7928, std-njdaniels, std-cook, risk-nameblocked, anti-singlechannel

## PM Section (Planner / Specifier — LCE)

### Objective
Implement the v1 discovery channels: `arcgis_query.py` (query county/state parcel layers by **OWNER** or
**MAIL_ADDR LIKE**), the **assessor owner-name** search (free states FL/TX/AZ/NV + statewide MD/MA/MT), the
**recorder grantor-grantee index** (highest-yield; the **name-blocked-state workaround**), and the
**owner-search-by-state routing** matrix. Name-blocked states (CA §7928.205 / Cook / NJ Daniel's Law) route
to the recorder index.

### Scope
**In scope:** `scripts/arcgis_query.py`; channel adapters for assessor owner-name + recorder index;
`references/owner-search-by-state.md` (the routing matrix); `references/sources.md` (free source catalog).
All lookups go through the slice-02 cache and respect the slice-01 gate.
**Out of scope:** swarm orchestration (slice-06); channels 5-9 (v2/v3).

### Guardrails / Allowed files
- `.claude/skills/acos-property-search/scripts/arcgis_query.py` (stdlib only — `urllib` for REST)
- `.claude/skills/acos-property-search/references/owner-search-by-state.md`
- `.claude/skills/acos-property-search/references/sources.md`
- `.claude/skills/acos-property-search/scripts/tests/test_arcgis_query.py` (fixture-driven)
- this task file + `.acos/evidence/[DATE]/slice-05-channels-arcgis-assessor-recorder/`
- Prohibited: paid APIs; login-gated pages; bypassing cache or gate; single-channel-only design.

### Definition of Done
- [ ] ArcGIS REST query by OWNER and by MAIL_ADDR LIKE returns normalized parcel records (against a fixture layer) — pass-condition: arcgis query test.
- [ ] The owner-search-by-state router picks statewide / friendly / name-blocked correctly — pass-condition: routing test (CA/NJ/Cook -> recorder; MD/MA/MT -> statewide; FL/TX/AZ/NV -> friendly).
- [ ] Name-blocked states use the recorder grantor-grantee index instead of owner-name search — pass-condition: **name-blocked-routing test (REQUIRED)**.
- [ ] Every returned parcel carries provenance (`source_url`) + a freshness stamp from cache — pass-condition: provenance test.
- [ ] Channels feed the graph (parcels + edges), not a flat list — pass-condition: graph-integration test.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. `arcgis_query.py`: build the REST `where` clause for OWNER / MAIL_ADDR LIKE; parse features into
   normalized `Parcel` records; route through cache.
2. Channel adapters: assessor owner-name (free states), recorder grantor-grantee index; normalize outputs.
3. Router reads `owner-search-by-state.md`; name-blocked -> recorder.
4. Push parcels + edges into the graph (slice-04).
5. Tests: arcgis query, routing, name-blocked routing, provenance, graph integration — all fixture-driven.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (meth-routing/recorderindex/mailpivot, std-ca7928/njdaniels/cook, EV-002/003/004/005);
Quality (stdlib `urllib`); Functional (the DoD tests); Security/Compliance (free + cached + gated);
Operational; Self-assessment.

### Dev Learnings
- (fill at execution) ArcGIS layer quirks; how the routing matrix is kept current.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Re-author a CA / NJ / Cook query; confirm it routes to the recorder index, NOT an owner-name search.
2. Independently verify the ArcGIS `where` clause for a MAIL_ADDR LIKE pivot against a fixture.
3. Confirm every parcel carries `source_url` + freshness; none fabricated.
4. Confirm parcels land in the graph with provenance edges.

### Evidence gates (all must pass)
- [ ] **Name-blocked states route to recorder** (hard; fail = REJECT).
- [ ] ArcGIS OWNER + MAIL_ADDR queries correct.
- [ ] Provenance + freshness on every parcel.
- [ ] Cache + gate respected.
- [ ] Learnings updated.

### QA Learnings
- (fill at execution) Any channel that returned data without provenance.
