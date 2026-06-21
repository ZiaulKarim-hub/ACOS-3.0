# Overview

**Feature ID:** `001-hypercore-ask`
**Product:** `acos-hypercore-ask` (an ACOS skill, plus Python 3 stdlib supporting scripts and optional `general-purpose` agents)
**Project:** ACOS 3.0
**Owner persona:** OKOA Capital staff / associates; consumed by the OKOA Investment Committee (IC) and by downstream ACOS skills.

`acos-hypercore-ask` is an ACOS skill that answers any natural-language question about — and mines
data from — the **Hypercore loan-management platform** (hypercore.ai), with a **zero-hallucination,
provenance-verified** data guarantee. Output is usable as a direct deliverable (reports, tables,
datasets) or as a **trusted, verified input feed** for other ACOS skills (acos-dataroom-v2,
acos-financial-statement, the prospectus pipeline, legal-analyst).

The product being pre-engineered *is this skill*. Its distinguishing feature is the **verification
architecture**: provenance-binding (every delivered value cites the exact raw cached API response)
PLUS adversarial multi-model consensus (N blind independent extraction/answer agents must agree on
substance before delivery), with deterministic gates layered underneath (schema validation,
pagination-completeness, freshness window, cross-field reconciliation, unit/currency normalization,
single-source confidence cap ≤ 0.7).

> **Critical ground state:** Hypercore API access is **NOT yet provisioned**. The full skill is
> designed now, with **all live API calls stubbed/TODO behind a clearly isolated client/adapter
> layer**. Until credentials arrive the skill is built and tested against fixtures/mocks and
> **degrades gracefully — it explicitly says "no live data" rather than fabricate.**

---

## Diagnostics

> Problem-before-solution (Protocol 0.3). Solution requirements are not locked until the symptoms,
> affected roles, current-vs-desired behavior, and unknowns are explicit. Where diagnosis is
> incomplete, downstream assumptions are tagged `Assumption` and routed to a dedicated diagnostic
> slice (see Rollout Plan and `tasks/`).

### Symptoms (what is going wrong today)
- **S1 — Direct querying is slow/technical/error-prone.** Staff who need a loan-portfolio answer
  must query Hypercore (UI or API) directly; this is slow, requires technical skill, and is
  mistake-prone.
- **S2 — AI answers are untrustworthy.** Ad-hoc AI querying produces fabrication, **stale data**,
  **silent pagination cutoffs**, and **aggregation errors**, making outputs unusable for IC-grade
  work.
- **S3 — No canonical verified feed.** Other ACOS skills need clean, verified loan data, but no
  provenance-backed source feed exists; each consumer re-pulls and re-validates ad hoc.
- **S4 — No repeatable question→report path.** Turning a question into a verified report/table
  requires bespoke scripting every time.

### Affected roles / personas
- **OKOA associate / staff** — asks portfolio questions; needs fast, defensible answers.
- **OKOA Investment Committee (IC)** — consumes IC-grade deliverables; will not review intermediate
  artifacts; final output must be boss-criticism-proof on first cold look (per OKOA prior).
- **Downstream ACOS skills** — acos-dataroom-v2, acos-financial-statement, prospectus pipeline,
  legal-analyst — consume verified extracts as trusted inputs.

### Current vs. desired behavior
| Dimension | Current | Desired |
|---|---|---|
| Answer trust | Possibly fabricated/stale/truncated | Every value provenance-bound + consensus-verified, or refused |
| Speed | Slow manual pull | Materially faster time-to-verified-answer |
| Completeness | Silent pagination truncation | Pagination-completeness gate; no silent truncation |
| Freshness | Unknown staleness | Stated freshness window; never serve stale silently |
| Aggregation | Unverified math | Cross-field reconciliation + adversarial recomputation |
| Reusability | Bespoke scripts | One skill; standard verified-extract feed formats |
| Failure mode | Guess/fabricate | Refuse + explicit "no live data" / "cannot provenance-bind" |

### Hypotheses
- **H1** — The dominant trust failure is not raw fabrication but *aggregation / units / currency /
  truncation* errors that look plausible. → reconciliation + completeness gates + adversarial
  recompute are higher-leverage than text-similarity checks. (`Assumption`, validate in diagnostic slice.)
- **H2** — A two-tier data model (raw cached truth + normalized derived view) is sufficient to
  guarantee provenance without ballooning token cost. (Internal prior LEARN-ARCH-002; high confidence.)
- **H3** — A 2-of-3 asymmetric quorum of blind agents catches substance disagreement on
  reports/aggregations at acceptable cost. (`Assumption`, reused from acos-dataroom-v2 / grader;
  finalize quorum N at plan time.)

### Unknowns (open; routed to diagnostic slice / Open Questions)
- **U1** — Exact Hypercore read endpoints, request/response schemas, auth model, pagination scheme,
  webhook event contract (partner-gated; **UNVERIFIED until access**).
- **U2** — Secret/credential provisioning mechanism (env vs dedicated secret store).
- **U3** — Concrete freshness-window length (configurable; value TBD at plan time).
- **U4** — Final consensus quorum N per verification tier.
- **U5** — Final scripting language decision (defaulted Python 3 stdlib; confirm at plan time).

---

## Users & Use Cases

### Primary users
1. **OKOA Capital staff / associates** — natural-language portfolio queries.
2. **OKOA Investment Committee** — IC-grade deliverable consumers (boss-criticism-proof first look).
3. **Downstream ACOS skills** — acos-dataroom-v2, acos-financial-statement, prospectus pipeline,
   legal-analyst — consume verified extracts as trusted inputs.

### Representative use cases
- **UC1 — Single-value lookup.** "What is the current outstanding principal on loan X?" → trivial
  lookup tier (deterministic gates + universal provenance), single provenance-bound value or refusal.
- **UC2 — Filtered list / table.** "List all bridge loans with a maturity in the next 90 days." →
  pagination-completeness + schema validation gates; provenance per row.
- **UC3 — Aggregation / report.** "Total committed vs. funded across the construction book by
  borrower." → full adversarial consensus tier; cross-field reconciliation + adversarial recompute;
  per-figure provenance + confidence.
- **UC4 — Dataset export for a downstream skill.** "Produce a verified collateral dataset for the
  data room." → trusted-input feed format (JSON/CSV) with embedded provenance + confidence + a
  manifest; consumed by acos-dataroom-v2.
- **UC5 — No-access degradation.** Any query while credentials/API are absent → explicit **"no live
  data — Hypercore access not yet provisioned"** with the design path shown against fixtures, never
  a fabricated answer.
- **UC6 — Diagnostic / validation.** Confirm symptoms, unknowns, Python 3 stdlib decision, and the
  stubbed-access ground rules before solution build (problem-before-solution slice).

---

## Requirements

### 4.1 Functional Requirements (MoSCoW)

**MUST**
- **M1** Accept a natural-language question about Hypercore loan-portfolio data and route it to the
  correct verification tier (trivial lookup vs. report/aggregation/analysis).
- **M2** Bind **every** delivered value to its exact raw cached API response provenance (endpoint +
  request params + timestamp + JSON field path). **No citation → refuse delivery; never guess.**
- **M3** Run **adversarial multi-model consensus**: dispatch N blind independent extraction/answer
  agents (via `Task()`, subscription-only); deliver only on substance consensus among ≥N agents;
  disagreement → re-dispatch / escalate, never a silent pick.
- **M4** Enforce the **deterministic gate suite**: schema validation, pagination-completeness,
  freshness window, cross-field reconciliation, unit/currency normalization, single-source
  confidence cap ≤ 0.7 — layered *underneath* consensus.
- **M5** Be **read-only** against Hypercore: no write/mutate code path against the API under any
  circumstance.
- **M6** Isolate all live Hypercore calls behind a **stubbed/TODO client-adapter** with a
  fixture/mock backend; the entire skill is buildable/testable pre-access.
- **M7** **Degrade gracefully**: explicit "no live data" state when credentials/API absent — never
  fabricate.
- **M8** Maintain the **two-tier data model**: raw cached API responses = source of truth (full
  provenance); normalized answer layer = token-efficient derived view; each agent gets only the
  tier it needs.
- **M9** Surface **provenance + confidence on every answer** (mandatory display; refusal-on-uncertainty).
- **M10** Subscription-only Claude: all model work via main-thread Read or `Task()` sub-agents;
  **never** `ANTHROPIC_API_KEY`.
- **M11** Provide at least one **diagnostic slice** (problem-before-solution) confirming unknowns
  and the Python 3 stdlib decision.

**SHOULD**
- **Sh1** Produce verified extracts in **report + table + dataset (JSON/CSV)** formats plus a
  trusted-input feed schema with embedded provenance/confidence + manifest.
- **Sh2** Detect **schema drift** against expected entity schemas and surface it (not silently absorb).
- **Sh3** Provide **freshness/staleness policy** with webhook-driven (or polling) cache invalidation.
- **Sh4** PII/GDPR-aware logging and evidence handling (no sensitive leakage beyond need).
- **Sh5** Durable/resumable execution + per-agent/slice observability consistent with
  `/acos-execute-slice`.

**COULD**
- **C1** Cache-warming / scheduled refresh of high-traffic entities.
- **C2** Confidence-trend tracking per entity over time.
- **C3** A "show your work" verbose mode dumping the full provenance + consensus trace.

**WON'T (this iteration)**
- **W1** Any write/mutate operation against Hypercore (permanent constraint, not just this iteration).
- **W2** Live API integration *before* credentials are provisioned (stubbed/TODO only now).
- **W3** New restricted `.claude/agents/` files without human approval (use `general-purpose`).
- **W4** Use of `ANTHROPIC_API_KEY` / separate API billing (permanent OKOA rule).

### 4.2 APIs, Data & States

**External API (Hypercore) — UNVERIFIED until access (`Assumption`/`TBD`):**
- REST read endpoints + real-time webhook events; integrations include Salesforce, NetSuite,
  document repositories. Exact endpoints, request/response schemas, auth model, pagination scheme,
  and webhook contract are **partner-gated and TBD**. All API specifics are stubbed behind the
  adapter contract.

**Read entities to model (likely; `Assumption` pending schema):** loans/facilities (term, revolver,
mezzanine, bridge, construction, syndicated, hybrid), borrowers/entities, drawdowns/fundings,
payments/repayments, fees, interest accruals, amortization schedules, covenants/compliance checks,
collateral, investor allocations, documents.

**Skill-internal data (two-tier):**
- **Tier 1 (truth):** `RawApiResponse` — cached raw API JSON keyed for provenance lookup (endpoint,
  request params, timestamp, body).
- **Tier 2 (derived):** normalized answer layer; `ProvenanceBinding`, `ConsensusResult`,
  `VerificationGateResult`, `ConfidenceRecord`.

**Core states (NL question → verified answer):**
`RECEIVED → TIER_ROUTED → (NO_LIVE_DATA stub state) → FETCH_OR_CACHE → RAW_CACHED →
EXTRACT(blind agents) → CONSENSUS → GATES → BOUND(provenance) → DELIVERED | REFUSED | ESCALATED`.

- **NO_LIVE_DATA** — credentials/API absent → explicit message; against fixtures in dev.
- **REFUSED** — value cannot be provenance-bound, or a gate fails hard → refuse, never guess.
- **ESCALATED** — consensus disagreement that re-dispatch did not resolve → escalate to user.

### 4.3 Non-Functional Requirements (NFRs)

- **NFR-Trust (paramount):** 0% fabrication target; 100% provenance coverage on delivered values;
  values that cannot be provenance-bound are refused. Exact numeric/name/date preservation.
- **NFR-Completeness:** pagination-complete (no silent truncation); a completeness gate must pass
  before any list/aggregate is delivered.
- **NFR-Freshness:** never serve stale data silently; deliveries carry a freshness stamp within the
  stated window or are refused/flagged.
- **NFR-Security:** honor TLS 1.2+, AES-256 at rest, RBAC, SOC 2 Type II, GDPR, MFA/SSO; secrets via
  env/secret store only, no credentials in repo.
- **NFR-Privacy:** borrower PII / financials must not leak into logs or evidence beyond need; RBAC
  + GDPR honored.
- **NFR-Read-only:** no mutating code path against the Hypercore API; enforced structurally.
- **NFR-Subscription:** no `ANTHROPIC_API_KEY`; model work via Read / `Task()` only.
- **NFR-Performance:** time-to-verified-answer materially faster than a manual pull (target;
  measured later — see Metrics).
- **NFR-Resilience:** durable/resumable execution; graceful degradation to "no live data".
- **NFR-Maintainability:** Python 3 stdlib preferred (`Assumption`, confirm at plan time); adapter
  contract isolates API churn from the rest of the skill.
- **NFR-Observability:** per-agent/slice logs/traces/metrics consistent with ACOS orchestration.

---

## Prioritization & Scope Cut

- **In scope (this pre-eng):** full design of the skill + adapter contract + two-tier data model +
  provenance engine + deterministic gate suite + adversarial-consensus orchestrator + NL→report
  pipeline + downstream feed formats, all built/tested against fixtures with live calls stubbed.
- **Scope cut for first demo-able increments (vertical slices):**
  1. Diagnostic slice (symptoms/unknowns/Python-stdlib confirmation).
  2. Thin end-to-end verified-answer path against fixtures (Demo 1) — deterministic-tier only.
  3. Adversarial-consensus layer on a report/aggregation (Demo 2).
  4. Completeness/freshness/schema-drift hardening + downstream feed (Demo 3).
- **Deferred:** live API wiring (until credentials), cache-warming, confidence-trend tracking.
- **Hard exclusions:** any write path; `ANTHROPIC_API_KEY`; fabricating values when no provenance.

---

## Metrics & Analytics

> Pre-engineering only *defines* formulas + logging locations (Protocol 0.5). Computation happens later.

**Product success metrics**
- Hallucination/fabrication rate (target 0%).
- Provenance coverage on delivered values (target 100%).
- Adversarial-consensus pass rate; disagreement/re-dispatch/escalation counts.
- Completeness (pagination-complete %), freshness-within-window %.
- Single-source figures flagged at confidence ≤ 0.7 (% correctly capped).
- Refusal rate (values refused for missing provenance) — a *health* signal, not a defect.
- Time-to-verified-answer vs. baseline manual pull.

**Agent performance metrics (defined, not computed)**
- **SPD** — Story Points Delivered (qualitative approximation).
- **QAP** = `(Delivered_Value * Quality_Score) / (1 + Rejection_Count)`.
- **TER** — Token Efficiency Ratio: artifacts per 1K tokens.
- **UAPS** = `0.3*Quality + 0.4*Efficiency + 0.3*CostEffectiveness`.

**Instrumentation plan**
- Agent identity logged to `.acos/metrics/agent-completions.log` (agent_type/agent_id).
- Skill-level run metrics + verification outcomes to `AGENT-METRICS.md` and per-slice evidence
  bundles under `.acos/evidence/[DATE]/[SLICE-ID]/`.
- Consensus/gate outcomes logged to the verification/consensus ledger (PII-scrubbed).

---

## UX & Content

- **Answer envelope (always):** the value(s) + provenance citation(s) + confidence + freshness
  stamp + verification tier used. Single-source figures visibly flagged (confidence ≤ 0.7).
- **Refusal envelope:** clear "cannot provenance-bind / gate failed — refusing rather than guessing"
  with what would unblock it.
- **No-live-data envelope:** explicit "no live data — Hypercore access not yet provisioned"; shows
  the design/fixture path; never a fabricated number.
- **Feed format (downstream):** machine-readable JSON/CSV with embedded per-value provenance +
  confidence + a manifest (source-of-truth pointers, freshness, schema version, completeness proof).
- **Tone/standard:** IC-grade, boss-criticism-proof on first cold look; spell out terms; no
  unexplained abbreviations in user-facing output.

---

## Rollout Plan

> Vertical slices, demo-able increments (Protocol 0.8). Named demo checkpoints below.

- **Demo 0 — Diagnostic.** Symptoms/unknowns confirmed; Python 3 stdlib decision recorded;
  stubbed-access ground rules locked. No solution code yet.
- **Demo 1 — Thin verified-answer path (fixtures, deterministic tier).** NL question → stubbed
  client → raw cached fixture → provenance-bound value → deterministic gates → provenance/confidence
  display. Shows a *verified* single-value answer with **zero live API**, plus the "no live data"
  degradation path.
- **Demo 2 — Adversarial consensus on a report/aggregation.** Blind multi-agent agreement on a
  report/aggregation against fixtures; cross-field reconciliation + adversarial recompute;
  disagreement → re-dispatch/escalate visibly.
- **Demo 3 — Completeness/freshness/schema-drift hardening + downstream feed.** A verified dataset
  produced with pagination-completeness + freshness + schema-drift handling, then consumed as a
  trusted input by a downstream skill (e.g., acos-dataroom-v2) via the feed format.
- **Post-access milestone (deferred):** swap the fixture/mock backend for the live adapter
  implementation behind the *unchanged* contract once credentials arrive.

---

## Risks & Mitigations

| ID | Risk | Mitigation |
|---|---|---|
| R1 | API surface unknown until access | Isolate Hypercore client behind a contract/adapter; build/test on fixtures/mocks now |
| R2 | Stale data served silently | Freshness policy + window; webhook/polling invalidation; freshness gate; never serve stale silently |
| R3 | Silent pagination / rate-limit truncation | Pagination-completeness gate (record-count/cursor reconciliation) before delivery |
| R4 | Schema drift on Hypercore side | Schema validation + drift detection against expected entity schemas; surface, don't absorb |
| R5 | Aggregation / units / currency errors | Cross-field reconciliation + unit/currency normalization + adversarial recomputation |
| R6 | PII / GDPR leakage | PII-scrubbed logs/evidence; RBAC-honoring; GDPR-aware; secrets in env/secret store |
| R7 | Over-trust by users | Mandatory provenance + confidence display; refusal-on-uncertainty; single-source cap ≤ 0.7 |
| R8 | Consensus instability / cost | Tiered verification (deterministic-only for trivial lookups; consensus for reports); bounded re-dispatch then escalate |
| R9 | Fabrication when no provenance | Refuse-on-missing-citation is non-bypassable; "no live data" explicit state |

---

## Dependencies & Stakeholders

**Dependencies**
- Hypercore platform API (hypercore.ai) — REST read + webhooks; **partner-gated docs, not yet in hand.**
- Credentials / secret management — to be provisioned.
- ACOS framework — skill loader, `Task()` sub-agents (general-purpose), evidence bundles, memory/RAG.
- Optional downstream consumers — acos-dataroom-v2, acos-financial-statement, prospectus pipeline, legal-analyst.

**Stakeholders**
- OKOA staff/associates (primary users), OKOA Investment Committee (deliverable consumers), OKOA
  boss (final-look critic), downstream-skill owners, ACOS framework maintainers.

---

## Open Questions

- **OQ1 (U1)** Exact Hypercore read endpoints/schemas/auth/pagination/webhook contract — partner-gated,
  UNVERIFIED until access. *Handling:* stubbed adapter + fixtures; mark all specifics TBD/Assumption.
- **OQ2 (U2)** Secret/credential provisioning mechanism (env vs dedicated secret store). *Default:*
  env/secret store, no creds in repo; finalize at provisioning.
- **OQ3 (U3)** Concrete freshness-window length. *Default:* configurable, never-serve-stale-silently;
  value TBD at plan time.
- **OQ4 (U4)** Consensus quorum N per tier. *Default:* configurable ≥N, 2-of-3 asymmetric start
  (acos-dataroom-v2 / financial-statement / grader pattern); finalize at plan time.
- **OQ5 (U5)** Final scripting language. *Default:* Python 3 stdlib; confirm in diagnostic/plan phase.
- **OQ6** Exact downstream feed formats per consumer. *Default:* report + table + dataset (JSON/CSV)
  + trusted-input feed schema; refine per consumer at plan/tasks time.

---

## Appendix

**Glossary**
- **Provenance-binding** — attaching to each delivered value the exact raw cached API response it
  derives from (endpoint + request params + timestamp + JSON field path).
- **Adversarial multi-model consensus** — N blind independent agents must agree on substance before
  a result is delivered; disagreement triggers re-dispatch/escalate.
- **Two-tier data model** — raw cached API responses (source of truth) + normalized derived answer
  layer (token-efficient view).
- **Deterministic gate** — a mechanical, non-LLM check (schema, pagination, freshness, reconciliation,
  normalization, confidence cap).
- **Verification tier** — trivial-lookup (deterministic-only) vs. report/aggregation (full consensus);
  provenance is universal.

**Reused ACOS priors**
- `pre-generation-verification-gate` (LEARN) — mandatory non-bypassable gate; confidence ≤ 0.7 cap on
  single-source figures.
- `two-tier-data-model` (LEARN-ARCH-002).
- Provenance discipline (real OKOA loan extractions).
- Adversarial-consensus pattern (acos-dataroom-v2 / acos-financial-statement / acos-grader).

**Assumptions register (carried)**
- project_name defaulted to "ACOS 3.0"; primary_users derived; quorum N defaulted (2-of-3 start);
  Python 3 stdlib defaulted; freshness window configurable/TBD; feed formats defaulted; secret store
  env-based pending provisioning. All flagged for confirmation at plan time.

---

## PRD Summary (One-Page Digest)

**What:** `acos-hypercore-ask` — an ACOS skill that turns any natural-language question about OKOA's
Hypercore loan-portfolio data into a **verified** answer/report/dataset, or **refuses**.

**Why:** Direct querying is slow/error-prone; ad-hoc AI answers are untrustworthy (fabrication,
stale data, silent pagination cutoffs, aggregation errors); downstream skills need a canonical
provenance-backed feed.

**How (distinguishing feature):** **Provenance-binding** (every value cites its exact raw cached API
response; no citation → refuse) + **adversarial multi-model consensus** (N blind agents must agree)
+ **deterministic gates** (schema, pagination-completeness, freshness, reconciliation, unit/currency
normalization, single-source confidence cap ≤ 0.7), layered tier-appropriately over a **two-tier
data model** (raw cached truth + normalized derived view).

**Ground state:** API not yet provisioned → **stubbed client/adapter + fixtures**; the skill says
**"no live data"** rather than fabricate.

**Guardrails:** read-only; subscription-only Claude (no `ANTHROPIC_API_KEY`); PII/GDPR discipline;
zero-hallucination.

**Demos:** D0 diagnostic → D1 thin verified-answer (fixtures) → D2 consensus on a report → D3
completeness/freshness/schema-drift + downstream feed.

**Success:** 0% fabrication, 100% provenance coverage, consensus-pass on reports, pagination-complete,
freshness-within-window, single-source figures capped ≤ 0.7, faster than manual pull.
