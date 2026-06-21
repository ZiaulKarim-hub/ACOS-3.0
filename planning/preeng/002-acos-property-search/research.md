# Research Dossier — acos-property-search (`002-acos-property-search`)

> Output of `/preeng.research`. **Precondition:** `spec.md` exists -> OK. This dossier structures the
> **already-completed research in PLAN.md** (treated as authoritative input; the worker cannot fetch
> external sources). The 4-phase Constitutional Domain Compilation Pipeline (Protocol 0.2) is enforced:
> Phase 1 (DLG) -> `domain-brief.md` + `domain-cqs.md`; Phase 2 (Lattice) -> `domain-lattice.json`;
> Phase 3 (Evidence Ledger) -> `evidence-ledger.json`; Phase 4 (Emission) -> this file + the QA report.
> Numerics PLAN.md left tunable are carried as `Assumption`/`TBD`, never fabricated.

## 1. Method & sources

- **Primary source:** `.claude/skills/acos-property-search/PLAN.md` (v-final), the agreed design with
  embedded research, the headline principle, the 9-channel completeness strategy, the graph engine and
  hub-guard, the scoring rubric, the equity rollup, the compliance gate, and the decisions log (D1–D8).
- **Secondary context:** the worker spec (artifact schemas + determinism contract) and ACOS conventions.
- **Tiering convention (Protocol 0.4):** PLAN.md's locked hard constraints (free-only, stdlib, blocking
  compliance gate, hedged language, statute citations) are treated **T1**; PLAN.md design claims derived
  from its research are **T2**; portal-availability/empirical specifics that vary in the wild are noted as
  volatile (T2/empirical). No external T1 fetch was performed; PLAN.md is the authority of record.

## 2. Domain compilation summary

- **Phase 1 (DLG):** `domain-brief.md` lists entities/processes/methods/standards/metrics/risks/terms +
  anti-patterns; `domain-cqs.md` poses **18 competency questions** (`CQ-01`…`CQ-18`) a practitioner must
  answer, each with an offline answer sketch.
- **Phase 2 (Lattice Expansion):** `domain-lattice.json` encodes **114 nodes / 146 edges**. Every CQ node
  connects within 2 hops to a method, a metric-or-standard, and a risk. Node types are drawn only from the
  controlled vocabulary {entity, process, method, standard, metric, risk, pattern, anti_pattern, term, cq};
  edges only from {uses, measured_by, constrained_by, mitigates, depends_on, part_of, implements,
  contradicts}.
- **Phase 3 (Evidence Ledger):** `evidence-ledger.json` holds **24 entries** (EV-001…EV-024), each with
  id/claim/source_refs/tier/confidence/freshness_days/notes/lattice_node_ids; every `lattice_node_ids`
  reference resolves to a real node.
- **Phase 4 (Emission):** this dossier + the QA report; the downstream plan/tech_prd/data-model/tasks/
  instructions all reference the lattice and ledger.

## 3. CQ coverage computation

Coverage rule (Protocol 0.2): a CQ is "covered" if, within 2 undirected hops, it reaches at least one
`method`, at least one `metric` **or** `standard`, and at least one `risk` node.

- **Result: 18 / 18 CQs covered = 100%** (mechanically recomputed; exceeds the ≥95% target).
- Structural checks: 0 dangling edges, 0 duplicate node/edge ids, 0 orphan nodes, all confidences in
  [0,1], all node/edge types in the controlled vocabularies. **No critical violations.**

## 4. Key findings (the design bets, with evidence)

- **F1 — There is no free national owner search; widest net = union of channels + pivots** (EV-001).
  Drives the 9-channel architecture and the entity-graph engine rather than a single search.
- **F2 — The recorder grantor-grantee index is the highest-yield free channel and the name-blocked-state
  workaround** (EV-004). v1 centers on channels 1–4 + recorder (Decision D4).
- **F3 — Corroboration must come from blind isolation** (EV-010): "Verified = 2+ independent isolated
  agents" is only non-circular because agents work blind to each other. Drives swarm isolation + the
  between-rounds synthesizer.
- **F4 — Precision needs a hub-guard** (EV-008, EV-009): stop-list + dynamic detection (default 25) + hop
  limit (default 2) + inverse-frequency weighting + **log every prune**, or a hub registered agent /
  shared address explodes the graph (N² false links). Threshold/hop are tunable defaults (D7/D8).
- **F5 — Conflicts are preserved, never harmonized** (EV-011, EV-016): the synthesizer flags conflicting
  owner names for manual review.
- **F6 — Concealment is pierced via recorded instruments** (EV-013): CABI + guaranty + vesting clause +
  UCC debtor name + tax-bill mailing triangulation; statute-anchored (765 ILCS 405, FL §689.071).
- **F7 — Equity is estimated from FREE data and always labeled** (EV-017): assessed value + original
  recorded mortgage − amortization assumption; true AVM/payoff stated as a limitation, never fabricated.
- **F8 — Compliance is a BLOCKING gate** (EV-018, Decision D3): DPPA/FCRA/FDCPA permissible purpose, debt
  classification, GLBA anti-pretexting hard block, scraping posture, per-run record.
- **F9 — FinCEN BOI is unusable; paid APIs/brokers excluded** (EV-014): free-sources-only is locked.
- **F10 — Hedged language is mandatory** (EV-020): "likely controlled by"; "owns" only with direct title.

## 5. Assumptions made (carried forward)

- **A1 (config absence):** No `feature_config.json` was supplied; the primary user / permissible-purpose
  default (OKOA collections context, Zee) is inferred. The compliance gate forces the real purpose to be
  recorded at run time, so this is self-correcting.
- **A2 (tunable numerics):** Confidence-tier cutoffs **75/50** (D6), hub threshold **25** (D7), hop limit
  **2** (D8), cache TTLs (corporate ~30 d, property ~30–60 d) are PLAN.md defaults — `Assumption`.
- **A3 (swarm wiring):** v1 **embeds** the adapted hub-guarded swarm (D1 default) rather than composing
  `acos-swarm-research`.
- **A4 (portal availability):** Per-portal free availability / 403-block behavior varies and degrades; the
  owner-search-by-state matrix is maintained in a reference file and probed in a dry run (slice-11).
- **A5 (subscription-only):** OKOA standing rule (no `ANTHROPIC_API_KEY`); swarm agents dispatched via
  `Task()` / main-thread `Read` only.

## 6. Open items routed downstream

- **OQ1–OQ7** (spec Open Questions) carry to plan-time decisions; the diagnostic slice locks D1–D8 via an
  `acos-decide` ADR. The dry-run slice (slice-11) probes real portal availability and the false-positive
  rate at the 75/50 cutoffs.

## 7. Evidence quality note

24 ledger entries: locked constraints + statutes at **T1** (EV-014, EV-018, EV-020, EV-021, EV-023,
EV-024 and the statute nodes), design claims at **T2**. No fabricated portal specifics; volatile
empirical facts (portal availability, big-county gating) are flagged as such. Distinguishing disciplines —
multi-channel union, blind-isolated swarm + synthesizer, hub-guard, conflict preservation, concealment
piercing, estimated-equity rollup, blocking compliance gate, hedged language — are first-class across all
artifacts and not diluted.
