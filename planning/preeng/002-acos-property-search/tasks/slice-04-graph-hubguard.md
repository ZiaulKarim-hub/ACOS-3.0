# slice-04-graph-hubguard — Entity graph engine + hub-guard

- **Parent story:** STORY-APS-04 · **Parent epic:** EPIC-APS-04 · **Demo:** -
- **Effort:** L · **Dependency order:** 5 · **Depends on:** slice-03-normalize-identity
- **Lattice refs:** cq-06, cq-07, cq-08, cq-09, meth-graph, meth-edgeschema, meth-edgestrength, meth-invfreq, meth-hubguard, meth-stoplist, meth-dynhub, meth-hoplimit, anti-hubexpand, anti-unboundedexp, metric-prunect, ent-edge

## PM Section (Planner / Specifier — LCE)

### Objective
Implement `graph.py`: the entity-graph engine with the **temporal/provenance edge schema** on every edge,
**edge-strength ordering**, **inverse-frequency weighting**, and the **hub-guard** — registered-agent
stop-list (`hub_agents.txt`) + dynamic hub detection (≥ **25**, configurable) + bounded hops (**2**,
configurable) + **log every prune**. Keep the inverse signal: a *non-commercial* agent on a few related
entities is a *strong* control link.

### Scope
**In scope:** `scripts/graph.py` (add_node/add_edge with the full edge schema enforced; strength_rank
assignment; inverse-frequency weighting; hub detection via stop-list + frequency threshold; hop-bounded
expansion; prune log); `references/hub_agents.txt` (the stop-list).
**Out of scope:** the actual channel lookups (slice-05); swarm/round logic (slice-06).

### Guardrails / Allowed files
- `.claude/skills/acos-property-search/scripts/graph.py` (stdlib only)
- `.claude/skills/acos-property-search/references/hub_agents.txt`
- `.claude/skills/acos-property-search/scripts/tests/test_graph.py`
- this task file + `.acos/evidence/[DATE]/slice-04-graph-hubguard/`
- Prohibited: persisting an edge missing `source`/`source_url`/`date_last_verified`; expanding siblings
  through a hub node; unbounded expansion.

### Definition of Done
- [ ] Every persisted edge carries the full temporal/provenance schema; an edge missing source/url/date is rejected — pass-condition: **edge-schema invariant test (REQUIRED; fail = REJECT)**.
- [ ] Expansion through a stop-listed registered agent is pruned and **logged** — pass-condition: **hub-prune test (REQUIRED)**; a sibling expanded through a hub = REJECT.
- [ ] An agent/address at/over the frequency threshold (default 25) is detected as a hub and pruned — pass-condition: dynamic-hub test.
- [ ] Expansion never exceeds the hop limit (default 2); every prune is logged — pass-condition: hop-limit + prune-log test.
- [ ] A non-commercial agent on a few entities is kept as a strong link (inverse signal) — pass-condition: inverse-signal test.
- [ ] Edge strength ordering + inverse-frequency weighting applied — pass-condition: strength/weight test.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Implement node/edge stores; `add_edge` rejects an edge missing required provenance/temporal fields.
2. Assign `strength_rank` per the ordering; weight by inverse frequency of the shared value.
3. Hub detection: stop-list match OR frequency ≥ threshold -> mark hub; expansion skips hub edges and
   appends to the prune log (so coverage stays honest).
4. Bound expansion to the hop limit from each seed.
5. Tests: edge-schema invariant, stop-list prune, dynamic-hub prune, hop-limit, prune-log, inverse signal,
   strength/weight.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (meth-graph/edgeschema/edgestrength/invfreq/hubguard, anti-hubexpand/unboundedexp,
EV-006/007/008/009, metric-prunect); Quality (stdlib); Functional (the seven DoD tests); Security; Operational
(prune log = observability); Self-assessment.

### Dev Learnings
- (fill at execution) Threshold/hop-limit tuning notes; how the prune log keeps coverage honest.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Re-author a graph with a CT-Corporation-style hub; confirm siblings are NOT expanded through it and the
   prune is logged.
2. Try to persist an edge with no `source_url`; confirm rejection.
3. Confirm expansion stops at the hop limit and a deep seed cannot reach 3+ hops.
4. Confirm a lone individual agent on 3 related entities is kept as a strong link, not pruned.

### Evidence gates (all must pass)
- [ ] **Edge-schema invariant enforced** (hard; fail = REJECT).
- [ ] **Hub expansion pruned + logged** (hard; fail = REJECT).
- [ ] Hop limit enforced; every prune logged.
- [ ] Inverse signal preserved.
- [ ] Learnings updated.

### QA Learnings
- (fill at execution) Any path that let a hub leak a control link.
