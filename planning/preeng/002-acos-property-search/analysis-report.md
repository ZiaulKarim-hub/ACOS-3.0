# Cross-Artifact Analysis Report — acos-property-search (`002-acos-property-search`)

> Output of `/preeng.analyze`. Cross-artifact presence + QA roll-up + coverage/evidence quality +
> consistency + bloat categorization + canonical-candidate flags + CAGE trace summary. Annotate-only
> (Protocol 0.6): nothing is deleted.

## 1. Artifact presence

| Artifact | Present | Notes |
|---|---|---|
| `spec.md` | yes | 13 required PRD sections incl. Diagnostics + Rollout (Demos 0-3) + One-Page Digest |
| `research.md` | yes | 4-phase pipeline summary; CQ coverage computation (100%) |
| `research_qa_report.json` | yes | APPROVED |
| `domain-brief.md` | yes | entities/processes/methods/standards/metrics/risks/anti-patterns/terms |
| `domain-cqs.md` | yes | 18 CQs (CQ-01..CQ-18) + answer sketches |
| `domain-lattice.json` | yes | 114 nodes / 146 edges; controlled vocab; 100% CQ coverage |
| `evidence-ledger.json` | yes | 24 entries (EV-001..EV-024); all lattice refs resolve |
| `plan.md` | yes | Protocol-0 sections; D1-D8 plan-time decisions |
| `tech_prd.md` | yes | component inventory + edge contract + gate + swarm + config |
| `data-model.md` | yes | graph nodes + universal edge contract + internal records + invariants |
| `planning_qa_report.json` | yes | APPROVED |
| `stories.json` | yes | 12 epics / 12 stories / 12 slices; graph-consistent |
| `tasks/*.md` | yes | 12 files, one per slice, PM/Dev/QA + Dev/QA Learnings |
| `tasks_qa_report.json` | yes | APPROVED |
| `cage_preeng_nodes.csv` / `cage_preeng_edges.csv` | yes | full BLOCKER->...->PATTERN chain |
| `agent_instructions/{pm,dev,qa}.md` | yes | role/inputs/workflow/DoD/prohibited/evidence/learning |

## 2. QA status roll-up

- **research_qa_report.json:** APPROVED.
- **planning_qa_report.json:** APPROVED.
- **tasks_qa_report.json:** APPROVED.
- No phase rejected; no precondition violated. Pre-eng is complete and bridge-ready.

## 3. Coverage & evidence quality

- **CQ coverage:** 18/18 = **100%** (mechanically recomputed; >=95% target exceeded). Each CQ reaches a
  method, a metric-or-standard, and a risk within 2 hops.
- **Lattice structural checks:** 0 dangling edges, 0 duplicate node/edge ids, 0 orphan nodes, all
  confidences in [0,1], all node/edge types in the controlled vocabularies. No critical violations.
- **Evidence ledger:** 24 entries. Locked hard constraints + statutes at **T1** (free-only EV-014,
  compliance gate EV-018, hedged language EV-020, skill form EV-021, limitations EV-023, decisions EV-024,
  plus statute nodes); design claims derived from PLAN.md research at **T2**; volatile portal-availability
  facts flagged as such. All `lattice_node_ids` resolve.
- **Distinguishing disciplines** (multi-channel union, blind-isolated swarm + synthesizer, hub-guard,
  conflict preservation, concealment piercing, estimated-equity-labeled rollup, BLOCKING compliance gate,
  hedged language) are first-class across every artifact and not diluted.

## 4. Cross-artifact consistency

- **spec <-> plan <-> tech_prd <-> data-model:** the 9 channels, the entity-graph edge schema, the
  hub-guard defaults (25 / 2), the 75/50 tiers, the blocking compliance gate, and hedged language are
  consistent across all four.
- **lattice <-> ledger:** every `cq-*` node maps to a CQ in `domain-cqs.md`; every ledger
  `lattice_node_ids` entry resolves to a real node.
- **stories <-> tasks:** 12 slices <-> 12 task files (no orphans); every `depends_on` resolves; dependency
  order contiguous 1..12; Demos D0(slice-00)/D1(slice-07)/D2(slice-06)/D3(slice-11) mapped.
- **tasks <-> data-model/tech_prd:** each slice's DoD/QA gates reference the concrete artifacts (scripts,
  reference files, ComplianceRecord, edge schema) defined in tech_prd/data-model.
- **Decisions:** spec Open Questions OQ1-OQ7 <-> plan-time decisions D1-D8 <-> EV-024 <-> CAGE n07/n08 — consistent.

## 5. Bloat management categorization (Protocol 0.6 — annotate only, delete nothing)

- **Active:** the full pre-eng artifact set + the planned reference files (sources.md,
  owner-search-by-state.md, hub_agents.txt, review-flags.md, compliance.md).
- **Review (canonical-example candidates):** the hub-guard + between-rounds synthesizer design, and the
  blocking-compliance-gate + provenance-first discipline (see Section 6).
- **Burn Pile:** none. (The two PLAN.md exploration stubs — `SKILL.md`, `scripts/normalize.py` — are
  reconciled at build time, not by this worker; annotation-only.)

## 6. Canonical-candidate flags (Protocol 0.6)

- **Multi-channel-union-with-hub-guarded-blind-swarm** (CAGE n12) — a reusable pattern for any
  embarrassingly-parallel free-source discovery problem: union many independent channels over an entity
  graph; corroborate via blind isolated agents; bound precision with a hub-guard + hop limit +
  log-every-prune. **Canonical candidate.**
- **Compliance-gated-provenance-first-discovery** (CAGE n13) — a reusable pattern for legally-sensitive
  free-source dossiers: a BLOCKING permissible-purpose gate + per-datum provenance + conflict preservation
  + hedged language + estimated-figures-labeled. **Canonical candidate.**

## 7. CAGE pre-eng session trace summary

- Full required chain present: **BLOCKER (n01 no-free-national-search) -> TOOL (n03 union+graph+hub-guard)
  -> FINDING (n05 H1/H2/H3) -> DECISION (n07 embed-swarm + 75/50/25/2) -> ARTIFACT (n09 pre-eng suite) ->
  OUTCOME (n11 bridge-ready) -> PATTERN (n12 multi-channel-union-with-hub-guarded-blind-swarm)**.
- A parallel chain runs through n02 -> n04 -> n06 -> n08 -> n09 -> n11 -> n13 (the compliance/correctness
  spine), with anti-patterns a01/a02/a03 countered by the two patterns.

## 8. Overall analysis verdict

**APPROVED / bridge-ready.** All artifacts present; all three QA phases APPROVED; CQ coverage 100% with no
structural violations; evidence tiers sound; distinguishing disciplines first-class and undiluted; CAGE
chain complete; determinism honored (no questions; tunable specifics carried as Assumption/configurable,
volatile portal facts routed to a reference file + the slice-11 dry run). Ready for the ACOS slice bridge
(`planning/slices/*.yaml`) and `/acos-execute-slice`. NOTE: this is the planning RECORD; it runs in
parallel with the actual `acos-property-search` skill-file build (both derive from PLAN.md).
