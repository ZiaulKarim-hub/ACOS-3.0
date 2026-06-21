# Implementation Plan — acos-property-search

> Output of `/preeng.plan`. **Preconditions:** `spec.md` + `research.md` exist; `research_qa_report.json`
> = APPROVED (not REJECTED) -> plan gate satisfied. Encodes Protocol 0 (three-agent pattern, diagnostics,
> evidence governance, metrics, bloat, learning capture, vertical slices, orchestration) and the PLAN.md
> design. Tunable numerics carried as plan-time decisions (Assumption).

## 1. Architecture overview

A user-invoked **project skill** (`.claude/skills/acos-property-search/`) = methodology `SKILL.md` +
**stdlib-only** Python helpers + reference files. Pipeline:

```
Compliance gate (BLOCKING) -> Normalize/classify -> Stage-1 identity resolution
  -> GRAPH-EXPANSION LOOP (loop-until-dry, hop-limited):
       worklist(seeds) -> FAN-OUT isolated blind agents (channel x jurisdiction x entity, each -> findings.md)
       -> BETWEEN-ROUNDS SYNTHESIZER (cross-ref -> confidence; preserve conflicts; hub-prune + hop-limit; next seeds)
       -> stop when a round yields no new high-confidence nodes
  -> Dedup on APN -> Scoring + tiers + review flags -> Equity/value/debt rollup
  -> Markdown report + audit trail
  (Cache layer w/ freshness TTLs wraps every external lookup throughout)
```

- **Entity graph** is the spine: nodes {name, person, entity, address, agent, phone, email, parcel, loan,
  lien, deed, court-case, UCC}; edges = "shares attribute X" with temporal+provenance.
- **9 discovery channels**; v1 ships channels 1–4 + recorder full; 5–9 phased (Decision D4).
- **Hub-guard** held by the synthesizer (stop-list + dynamic detection ≥25 + hop limit 2 + inverse-freq +
  log-every-prune).
- **Scripts (stdlib, Decision D5):** normalize, score, dedup, arcgis_query, graph, swarm_dispatch,
  synthesize_round, rollup, cache.
- **Reference files:** sources.md, owner-search-by-state.md, hub_agents.txt, review-flags.md, compliance.md.

## 2. Architecture constraints (from PLAN.md / spec, locked)

- **Free / open-web sources only** — no paid APIs / data brokers (T1, EV-014).
- **Project-skill form factor** — SKILL.md + stdlib helpers + reference files; explicit-invocation-only
  (`disable-model-invocation: true`, `user-invocable: true`) (T1, EV-021).
- **No external infrastructure** — no Neo4j / Elasticsearch / Postgres / billing (T1).
- **BLOCKING compliance gate** — runs first every time; nothing proceeds without a permissible-purpose
  record; GLBA anti-pretexting hard block (T1, EV-018; Decision D3).
- **Hedged language** — "likely controlled by"; "owns" only with direct title support (T1, EV-020).
- **Per-datum provenance** on every edge/attribution; full audit trail under `workspace/<session-id>/`.
- **Subscription-only Claude (Assumption A5)** — model work via `Task()` / main-thread `Read`; never
  `ANTHROPIC_API_KEY`.

### Plan-time decisions (resolving spec Open Questions / PLAN.md D1–D8)
- **OQ1/D1 — Swarm wiring:** **embed** the adapted hub-guarded swarm in v1 (compose `acos-swarm-research`
  pattern, not the skill). *Assumption (default).*
- **OQ2/D6 — Confidence tiers:** **≥75 high / 50–74 candidate / <50 weak** (configurable). *Assumption.*
- **OQ3/D7 — Hub frequency threshold:** **25** entities/addresses (tunable per state). *Assumption.*
- **OQ4/D8 — Hop limit:** **2 degrees** from the seed (3 for deep dives). *Assumption.*
- **D2 — Renderer:** Markdown v1; `acos-loan-doc-generator-with-visual-verification` render v2.
- **D3 — Compliance gate:** hard, blocking.
- **D4 — v1 channel depth:** channels 1–4 + recorder full; 5–9 phased.
- **D5 — v1 scripts:** the full nine listed above.
- **OQ7 — Cache TTLs:** corporate ~30 d, property ~30–60 d, deed/transfer faster. *Assumption.*
- All locked in an `acos-decide` ADR at slice-00 (Decision D1–D8, EV-024).

## 3. Three-agent pattern mapping (Protocol 0.1)

- **PM (Planner / Specifier)** ≈ ACOS **architect** — authors each slice with LCE (narrow objective,
  explicit scope/guardrails, allowed files, step-by-step, DoD with required artifacts + validation +
  evidence-bundle expectations).
- **Dev (Executor)** ≈ ACOS **developer** — executes the slice exactly (only allowed files), produces the
  7-part Evidence Bundle.
- **QA (Zero-Trust Verifier)** ≈ ACOS **qa-reviewer / security-reviewer** — assumes Dev did it wrong;
  independently re-runs tests, re-authors negative/hostile cases (e.g., a hub fixture that must be pruned;
  a conflicting-owner fixture that must surface a review flag; a compliance-gate-bypass attempt that must
  be refused), can REJECT until gates pass.
- The bridge step turns these task files into native ACOS slices executed by `/acos-execute-slice` under
  hook enforcement; DoD/evidence sections are written to map cleanly to `slice.yaml`
  `acceptance_criteria` + `verification_method`.

## 4. Vertical slice plan + demos (Protocol 0.8)

12 vertical slices across 10 epics (see `stories.json`). Each is a demo-able increment.

- **Demo 0 — Diagnostics locked (slice-00).** Symptoms/hypotheses/unknowns confirmed; D1–D8 ADR;
  stdlib-only + compliance-blocking ground rules recorded.
- **Demo 1 — Compliant thin slice (slices 01→02→03→ thin 11 path).** Compliance gate blocks → normalize →
  identity resolution → cache → minimal Markdown report on a sample name, channels stubbed. Proves the
  blocking gate + pipeline skeleton + hedged language + audit trail.
- **Demo 2 — Hub-guarded discovery + graph (slices 04→05→06→07).** Entity graph + hub-guard + hop-limit;
  channels 1–4 + recorder returning real parcels; embedded swarm + synthesizer producing corroborated
  nodes with conflicts preserved.
- **Demo 3 — Ranked dossier (slices 08→09→10→11).** Dedup → scoring + tiers + review flags → equity
  rollup → full Markdown dossier with coverage/limits footer + provenance, on a real sample subject.

**Global build order** (dependency_order in `stories.json`): 00 diagnostic → 01 scaffold+compliance-gate →
02 cache+fetch+posture → 03 normalize+identity → 04 graph+hub-guard → 05 channels(arcgis/assessor/recorder)
→ 06 swarm+synthesizer → 07 entity-discovery+routing → 08 dedup → 09 scoring+review-flags → 10 equity-rollup
→ 11 report+coverage-footer+dry-run.

## 5. Diagnostics (Protocol 0.3)

Problem-before-solution is slice-00. It validates **H1** (widest net = union of channels/pivots, not one
search), **H2** (blind isolation makes corroboration non-circular), **H3** (no hub-guard → N² blow-up),
and locks the tunable defaults (D6/D7/D8) + the blocking-compliance + stdlib-only + free-only ground rules.
Incomplete-diagnosis items (portal availability, false-positive rate at cutoffs) are carried as
`Assumption` and validated empirically in slice-11 (dry run).

## 6. Evidence governance + CAGE (Protocol 0.4)

- **Evidence Ledger** (`evidence-ledger.json`) backs every major claim with a tier/confidence/freshness +
  lattice node refs. Per-slice **Evidence Bundles** live under `.acos/evidence/[DATE]/[SLICE-ID]/`.
- **CAGE pre-eng trace** (`cage_preeng_nodes.csv` / `cage_preeng_edges.csv`) records the
  BLOCKER→TOOL→FINDING→DECISION→ARTIFACT→OUTCOME→PATTERN chain for this pre-eng session.

## 7. Agent performance metrics (Protocol 0.5)

- **Production:** SPD (qualitative); `QAP = (Delivered_Value * Quality_Score) / (1 + Rejection_Count)`.
- **Efficiency:** `TER` = artifacts per 1K tokens; volume per unit cost (if cost data exists).
- **Universal:** `UAPS = 0.3*Quality + 0.4*Efficiency + 0.3*CostEffectiveness`.
- **Domain quality signals:** channel-coverage, corroboration rate, hub-prune count, false-positive rate
  at 75/50, freshness-within-TTL %, compliance-record completeness (100%), hedged-language conformance.
- **Instrumentation:** ACOS logs agent identity to `.acos/metrics/agent-completions.log`; formulas +
  domain signals recorded in a feature-local `AGENT-METRICS.md`. (Formulas defined; not computed here.)

## 8. Bloat management (Protocol 0.6)

Per-slice evidence grouped into bundles. Artifacts categorized **Active** (this pre-eng set + reference
files), **Review** (canonical-example candidates — the hub-guard + between-rounds synthesizer and the
blocking-compliance-gate patterns), **Burn Pile** (none yet; the two PLAN.md stub files reconciled at build
time are annotation-only). Nothing is deleted; annotation lives in `analysis-report.md`.

## 9. Learning capture (Protocol 0.7)

Every task file carries `## Dev Learnings` and `## QA Learnings`. A slice is **not Done** until both are
updated. Agent instructions restate this rule.

## 10. Orchestration & edge constraints (Protocol 0.9)

- **Executor:** `/acos-execute-slice` (ACOS skill+agent+hook system).
- **Durable execution:** the cache (JSON + freshness TTLs) + the per-round `workspace/<session-id>/round-NN/`
  audit artifacts make a run **resumable after interruption** — a re-run reuses cached lookups and resumes
  the loop from the last completed round.
- **Human-in-the-loop:** the BLOCKING compliance gate is a mandatory approval pause; manual-review flags
  are PM/QA review points.
- **Observability:** per-agent `findings.md`, per-round `synthesis/`, logged hub prunes, per-record
  freshness stamps, and `.acos/metrics/agent-completions.log` give logs/traces/metrics per agent/slice.
- **PM/Dev/QA → nodes:** PM = slice authoring; Dev = channel-agent / script execution; QA = zero-trust
  verification gate before a slice is Done.

## 11. Risks → plan mitigations (cross-ref spec Risks)

| Risk (lattice) | Plan mitigation | Slice |
|---|---|---|
| `risk-nofree` | 9-channel union + entity graph | 05/06/07 |
| `risk-nameblocked` | recorder index + owner-search-by-state routing | 05/07 |
| `risk-commonname` | ≥2 anchors + scoring penalty + review flag | 03/09 |
| `risk-block` | cache + freshness TTLs + scraping posture | 02 |
| `risk-legal` | blocking compliance gate + per-run record + GLBA hard block | 01 |
| `risk-equitymisread` | every figure labeled "estimated" + "no mortgage data" flag | 10 |
| `anti-hubexpand`/`anti-unboundedexp` | hub-guard + hop limit + log-every-prune | 04/06 |
| `anti-harmonize` | synthesizer preserves conflicts as review flags | 06/09 |
| `risk-boiunusable`/`anti-paidapi` | free-only constraint; BOI flag-only | 01 (gate)/global |

## 12. Definition of Done (plan-level)

- `plan.md`, `tech_prd.md`, `data-model.md`, `planning_qa_report.json` exist and are non-empty.
- All Protocol-0 sections present; D1–D8 plan-time decisions recorded; distinguishing disciplines
  first-class and undiluted; determinism honored (no questions; gaps as Assumption/TBD).
- Maps cleanly into `stories.json` + `tasks/*.md` (vertical slices, Demos 0–3, Dev/QA learnings) for the
  ACOS bridge.
