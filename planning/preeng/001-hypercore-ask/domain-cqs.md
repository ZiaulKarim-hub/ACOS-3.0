# Competency Questions — acos-hypercore-ask

> Phase 1 (DLG) output. A practitioner building/operating this skill must be able to answer each.
> Each CQ has a stable id (`CQ-01`…`CQ-15`), maps to a `cq`-type node in `domain-lattice.json`, and
> is connected to method/metric/standard/risk nodes there (≥95% coverage target). Hypercore API
> specifics are `UNVERIFIED until access` and answered with `Assumption`/`TBD` where required.

| ID | Competency Question |
|---|---|
| **CQ-01** | What are the exact Hypercore read endpoints, their request/response schemas, auth model, and pagination scheme (once docs are in hand)? |
| **CQ-02** | Which Hypercore entities and fields map to OKOA's loan, borrower, facility, drawdown, payment, fee, interest, amortization, covenant, collateral, and investor-allocation concepts? |
| **CQ-03** | How is provenance bound to each delivered value (endpoint + request params + timestamp + JSON field path) and stored as the source of truth? |
| **CQ-04** | What constitutes substance consensus among N blind extraction agents, and what N / quorum threshold is required per verification tier? |
| **CQ-05** | How is the single-source confidence cap (≤ 0.7) computed and surfaced to the user? |
| **CQ-06** | What is the freshness policy (live fetch vs. cached vs. webhook-invalidated) and how is stale data prevented from being served silently? |
| **CQ-07** | How is pagination-completeness verified so no records are silently truncated by rate limits or cutoffs? |
| **CQ-08** | How is schema drift on Hypercore's side detected and handled? |
| **CQ-09** | How are aggregation, unit, and currency errors caught (cross-field reconciliation + adversarial recomputation)? |
| **CQ-10** | How does the stubbed/isolated client/adapter layer let the entire skill be built and tested against fixtures/mocks before API access is granted? |
| **CQ-11** | How does the skill degrade gracefully and explicitly signal "no live data" rather than fabricate when credentials are absent? |
| **CQ-12** | How is borrower PII / financial data kept out of logs and evidence beyond need while honoring RBAC and GDPR? |
| **CQ-13** | How are verified extracts shaped to be consumable as trusted inputs by downstream skills (acos-dataroom-v2, acos-financial-statement, prospectus, legal-analyst)? |
| **CQ-14** | What is the two-tier data model boundary between raw cached API truth and the normalized derived answer layer? |
| **CQ-15** | When is the deterministic-gate-only path sufficient (trivial lookups) versus when is full adversarial consensus mandatory (reports/aggregations/analysis)? |

## Answer sketches (offline; full reasoning lives in research.md)

- **CQ-01** — `TBD`/`Assumption` (partner-gated). Modeled behind the adapter contract; fixtures stand
  in for real endpoints/schemas/auth/pagination until access.
- **CQ-02** — Mapped via the data-model entity list; field-level mapping `TBD` pending schema, held
  as the normalized layer over RawApiResponse.
- **CQ-03** — ProvenanceBinding records `{endpoint, request_params, timestamp, json_field_path}`
  pointing at a RawApiResponse (Tier-1 truth). No binding → refuse.
- **CQ-04** — Substance consensus = agreement on the *value/answer substance* (exact numbers/names/
  dates, normalized) among ≥N blind agents. Default `Assumption`: configurable, 2-of-3 asymmetric
  start (reuse acos-dataroom-v2 / financial-statement / grader). Finalize N per tier at plan time.
- **CQ-05** — ConfidenceRecord; single-source figures capped at ≤ 0.7 and visibly flagged in the
  answer envelope.
- **CQ-06** — Freshness window (configurable, `TBD` length); webhook-driven (or polling) cache
  invalidation; freshness gate; never serve stale silently.
- **CQ-07** — Pagination-completeness gate: reconcile expected vs. fetched record counts / cursor
  exhaustion before any list/aggregate is delivered.
- **CQ-08** — Schema validation against expected entity schemas + drift detection; surface drift,
  don't silently absorb.
- **CQ-09** — Cross-field reconciliation + unit/currency normalization + adversarial recomputation
  by independent agents.
- **CQ-10** — Contract-first client/adapter with a fixture/mock backend; everything downstream of the
  adapter is exercised on fixtures pre-access.
- **CQ-11** — Explicit `NO_LIVE_DATA` state + answer envelope ("no live data — access not yet
  provisioned"); never fabricate.
- **CQ-12** — PII-scrubbed logging/evidence; need-to-know; RBAC + GDPR honored; secrets in env/secret
  store.
- **CQ-13** — Trusted-input feed format (report + table + dataset JSON/CSV) with embedded
  per-value provenance + confidence + a manifest (source pointers, freshness, schema version,
  completeness proof).
- **CQ-14** — Tier-1 RawApiResponse = truth (full provenance); Tier-2 NormalizedAnswerRecord =
  token-efficient derived view; agents get only the tier they need.
- **CQ-15** — Deterministic-only path for trivial lookups; full adversarial consensus mandatory for
  reports/aggregations/analysis that feed other tasks; provenance-binding universal across tiers.
