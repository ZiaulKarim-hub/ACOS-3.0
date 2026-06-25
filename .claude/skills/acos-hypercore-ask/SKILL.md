---
name: acos-hypercore-ask
description: Trust-first natural-language interface to the Hypercore loan-servicing platform. Turns a portfolio question into a provenance-bound, consensus-verified answer, report, table, or downstream feed — or an explicit refusal — NEVER a fabricated number. Every delivered value carries a citation back to a cached raw API response; aggregations are reconciled and pagination-completeness-checked; stale data is refused not served; single-source figures are confidence-capped. Read-only by construction (no mutating method exists on the data adapter). Subscription-only Claude (blind extraction via Task(), never ANTHROPIC_API_KEY). Live against the Hypercore GraphQL API via Doppler (read-only) and fixture-testable. Resolves fuzzy loan names, computes private-credit figures + KG-joined leverage ratios (LTV/DSCR/debt-yield, dual-provenance via the OKOA knowledge graph), and runs portfolio analysis (rankings, roll-ups, concentration, covenant scan). Use for "ask Hypercore" portfolio questions, verified report/table generation, leverage/coverage ratios, portfolio analysis, and producing a trusted verified-extract feed for other ACOS skills.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Task
---

# acos-hypercore-ask

> **Status: FULL — live-verified 2026-06-19.** All pipeline stages are built and the skill
> answers live against the Hypercore GraphQL API (Doppler `hypercore-ask/dev_personal`):
> read-only adapter, two-tier provenance cache, deterministic gates, adversarial consensus,
> deliver/report/feed envelopes, fuzzy loan-name resolution, a PRISM-seeded domain ontology +
> figures registry (native + derived), KG-joined leverage ratios (LTV/DSCR/debt-yield via the
> OKOA knowledge graph, dual provenance + per-loan refusal where collateral data is absent),
> and a portfolio analysis layer (rankings, roll-ups, concentration, covenant scan vs PRISM
> 75%/1.25x/8% thresholds). Every delivered value is provenance-bound or the skill REFUSES —
> it never fabricates. 450+ stdlib-only tests, date-independent.

## Purpose

`acos-hypercore-ask` is the **trust layer** between OKOA staff (and downstream ACOS
skills) and the Hypercore loan-servicing platform. It exists because ad-hoc AI querying
of Hypercore produces *plausible-looking* wrong answers — aggregation errors, silent
pagination cutoffs, stale data, unit/currency mistakes — that pass a casual read. This
skill refuses to deliver any value it cannot provenance-bind and verify.

## Locked guardrails (apply to every stage)

1. **Read-only.** The data adapter (`hca-adapter.py`) exposes read methods ONLY
   (`is_live`, `get_entity`, `list_entities`, `get_schema`, `subscribe_events`). No
   create/update/delete/post/put/patch/write/mutate method exists — enforced structurally
   (by omission) AND by a guard test.
2. **Subscription-only Claude.** Blind extraction agents are spawned via `Task()`
   (`general-purpose`). **Never `ANTHROPIC_API_KEY`.** No external model API calls.
3. **Stubbed-until-access.** All live Hypercore calls live ONLY inside `LiveBackend`,
   which currently raises `NotImplementedError`. `FixtureBackend` is active and serves
   canned data labeled as fixture. Live wiring is deferred behind the unchanged contract.
4. **Never fabricate.** Absent credentials (`is_live() == false`) → explicit
   `NO_LIVE_DATA` envelope / `NoLiveDataError`, never a made-up record, never a crash.
5. **Secrets via env / Doppler only.** Credentials are read from environment variables
   (`CLIENT_ID` + `HYPERCORE_CLIENT_SECRET` by default; names configurable in
   `config.yaml`). `HYPERCORE_BASE_URL` is an OPTIONAL GraphQL-URL override, not a
   credential. They are injected by `doppler run` (project `hypercore-ask`, config
   `dev_personal`). No key or URL is ever committed.
6. **Python 3 stdlib only.** No third-party dependencies in any supporting script.

(See `memory/decisions/2026-06-18-hca-build-ground-rules.md` for the full decision record.)

## Natural-language command surface

The skill is invoked with a portfolio question or a report/feed request:

- **Ask** — `/acos-hypercore-ask "<question>"`  *(BUILT — SLICE-HCA-07, thin tier)*
  Returns a single verified answer envelope: value + provenance citation(s) +
  confidence + freshness stamp + verification tier. Or a terminal state:
  `REFUSED`, `ESCALATED`, `NO_LIVE_DATA`.

  **PRIMARY ENTRY — the smart orchestrator (`hca-ask.py`).** Prefer this for arbitrary
  questions (especially investor/funding questions). It tries the deterministic spine first
  (unchanged), then a FUNDING interpretation (splits a question into investor + loan + metric →
  reconciled funding figure), then a confidence-graded EXPLORER fallback:

  ```bash
  doppler run --project hypercore-ask --config dev_personal -- \
      python3 .claude/scripts/hca-ask.py --ask "what is XL's outstanding on the Beehive loan?"
  ```

  **Implementation (deterministic spine, no model call):** the spine itself is
  `.claude/scripts/hca-deliver.py --ask "<question>"`, which wires the full vertical
  `plan -> fetch (read-only adapter) -> Tier-1/Tier-2 cache -> provenance bind+verify ->
  deterministic gates -> answer envelope`. `hca-ask.py` calls it first and returns a clean
  delivery verbatim; the examples below run either entry. Live reads run under Doppler:

  ```bash
  doppler run --project hypercore-ask --config dev_personal -- \
      python3 .claude/scripts/hca-deliver.py --ask "how many loans are there?"
  ```

  Supported thin-tier intents today: **count** ("how many loans/clients are there?"),
  **lookup** (a single non-PII field of a named record), one **aggregate**
  ("total commitment across all loans" — exercises the reconciliation + currency gates),
  and **payoff / early redemption** (see below). The envelope is `{state, answer,
  values:[{value, provenance:{raw_response_id, json_field_path}, confidence}], gate_verdict,
  complete, refusals[]}`. Consensus (slice-06) and report/feed orchestration (slice-08/09)
  WRAP this spine; they do not replace it. An unmappable question, a failed gate, or a
  missing binding yields a structured `REFUSED` (the failing gate is NAMED — never a number).
  No creds -> explicit `NO_LIVE_DATA`. See `demos/demo1-thin-path.md` for the full walkthrough.

  **Payoff / early-redemption intent (SLICE-HCA-12).** A question containing *payoff* /
  *early redemption* / *amount to redeem* (e.g. `--ask "what is the payoff for Beehive
  Waldorff as of 2026-06-30"`) routes to the **payoff figure**:
    1. **Fuzzy loan-name resolution** (`hca-resolve.py`) — fetches REAL loans via the
       RELIABLE list query `loans(filter:{searchString:"..."})` and scores client-side
       (stdlib `difflib` + token-set overlap). Exactly one high-confidence match →
       resolve **and ECHO** it ("matched 'beehive' → 'Beehive Waldorff' (134)"). Multiple /
       low-confidence → **DISAMBIGUATE** (return the candidate list; **never silently pick**).
       No match → REFUSE. Candidates always come from real API rows (never invented).
    2. **The `payoff_as_of` figure** (`hca-figures.py`) — calls
       `getLoanRepaymentDistribution(input:…)` (a Query / read-preview, NOT a mutation) with
       the **EXACT known-good input** (a minimal / `isPrepayment:true` input CRASHES the
       resolver with HTTP 500), **retries up to 3× on the intermittent 500**, provenance-binds
       the `total` to a cached Tier-1 record, and **RECONCILES** principal + indexedPrincipal +
       interest + compoundingInterest + accruedCompoundingInterest + totalFees + totalPenalties
       + totalTaxes == total within $0.01 — REFUSING if it does not reconcile. Default date =
       today (UTC); an explicit "as of <date>" is honored. Live-verified 2026-06-19 (loan 134
       "Beehive Waldorff", 2026-06-30 → total 31,888,682.99, reconciles to the cent).

  The single-loan resolver `loan(id)` and the transaction-PREVIEW resolvers are FLAKY
  (intermittent HTTP 500) — resolution and the payoff figure ride the RELIABLE list query +
  `getLoanRepaymentDistribution`. See
  `memory/decisions/2026-06-19-hypercore-early-redemption-input.md`.

  The **figure abstraction** (`hca-figures.py`: `Figure` / `FigureRegistry`) is the seed of
  a future figures registry — each figure declares a name + synonyms + kind (direct|derived)
  + a fetch-and-verify function returning the standard answer envelope, so new figures slot
  straight into the deliver / consensus / report spine.

  Resolve a name on its own:
  ```bash
  doppler run --project hypercore-ask --config dev_personal -- \
      python3 .claude/scripts/hca-resolve.py --resolve "beehive"
  ```
  Compute the payoff for a resolved id on its own:
  ```bash
  doppler run --project hypercore-ask --config dev_personal -- \
      python3 .claude/scripts/hca-figures.py --loan-id 134 --date 2026-06-30
  ```

- **Report** — `/acos-hypercore-ask report "<request>"`  *(BUILT — SLICE-HCA-08; consensus wrap BUILT — SLICE-HCA-06)*
  Returns a verified report/table assembled from MULTIPLE figures, where **EACH figure
  carries its own** `{value, unit/currency, provenance, gate_verdict, confidence, complete}`.
  Aggregations are reconciled and pagination-completeness-checked. For report / aggregation /
  high-stakes values the orchestrator does NOT trust a single extraction — it runs the
  **adversarial consensus** wrap (see below) over N blind agents before any figure is
  delivered. A report **DELIVERS only if every figure delivers**; any figure that REFUSES
  surfaces as a refusal in the report (the report **names which figure / which gate failed**)
  — never silently dropped, never fabricated. See **the report-tier state machine** below and
  `demos/demo-report-pipeline.md`.

- **Feed** — `/acos-hypercore-ask feed "<request>" --format json|csv`  *(BUILT — SLICE-HCA-09)*
  Emits a verified dataset (JSON/CSV) with embedded per-value provenance/confidence and a
  **manifest** (source pointers, freshness, schema version, **real** completeness proof) for
  consumption by other ACOS skills as a trusted input. Renderer: `.claude/scripts/hca-feed.py`
  (`--format json|csv|feed`). Consumer contract: `feed-contract.md`. Walkthrough:
  `demos/demo3-downstream-feed.md`. PII-safe by default (aggregates / counts / field-names only
  for any tracked artifact; per-record output goes ONLY to the git-ignored runtime area).

## Adversarial consensus orchestration (Demo 2 — SLICE-HCA-06)

> **BUILT.** Engine: `.claude/scripts/hca-consensus.py`. Blind-agent prompt:
> `prompts/blind-extractor.md`. Walkthrough: `demos/demo2-consensus.md`. Tests:
> `.claude/scripts/tests/test_hca_consensus.py`.

For **report / aggregation / high-stakes** questions, a single extraction is not trusted. The
**main Claude conversation** (the only context with the `Task` tool) WRAPS the deterministic
spine with **blind N-agent consensus**. A Python script cannot spawn `Task()` sub-agents, so
the work is split:

- **`hca-consensus.py` — the pure-Python adjudication engine.** It takes N independent agent
  returns and decides DELIVER vs RE-DISPATCH vs ESCALATE. It makes **no model call**; the
  agent dispatch is injected as an `agent_runner` callable.
- **This SKILL.md / the orchestrator — the dispatcher.** It spawns the N blind
  `general-purpose` agents via `Task()` (**subscription-only — never a direct model-API key /
  env secret**), collects their structured returns, and passes them to the engine.

### The flow (what the main Claude does)

1. **Plan + scope.** Run the deterministic plan (`hca-deliver.plan_question`) to get the
   entity/intent and fetch the Tier-1 raw response via the read-only adapter + cache. Build a
   PII-minimized scoped slice with `TwoTierCache.minimal_slice(rid, fields)`.
2. **Spawn N blind agents (one round).** For `n = config consensus.agent_count` (default 3),
   spawn N **`general-purpose`** `Task()` agents IN PARALLEL, each with the **identical**
   `prompts/blind-extractor.md` prompt filled with the SAME question + SAME scoped slice. No
   agent sees another's prompt or output; none is told another exists.
3. **Adjudicate.** Pass the N returns to the engine:
   ```python
   run_consensus(question, agent_runner, *, quorum=None, n=None, max_redispatch=None,
                 binder=..., gate_suite=..., gate_source=..., entity_type=..., value_ref=...)
   ```
   where `agent_runner(question, n) -> [agent_return, ...]` wraps the Task() spawn for one
   round. Each `agent_return` is the blind-extractor JSON `{value, json_field_path,
   raw_response_id, agent_confidence}` (or an `hca-deliver` envelope — both are accepted).
4. **The engine decides (no model call):**
   - **Substance consensus** — it normalizes each agent's `value` to a substance key (numbers
     agree within tolerance; text by normalized equality; lists by set membership) and counts
     the largest agreeing group. `>= quorum` (default **2-of-3, asymmetric** — 2 agreeing
     agents suffice) → an agreed value.
   - **Disagreement → bounded BLIND re-dispatch.** Below quorum, the engine simply calls
     `agent_runner(question, n)` **again with identical args** (default `redispatch_retries`
     = 1). There is **no parameter** through which "you disagreed" / values-seen / a peer
     answer can reach the agents — re-dispatch is structurally blind. The orchestrator MUST
     spawn a **fresh** cohort for each round and MUST NOT inject any prior-round hint.
   - **Still split → ESCALATE = structured REFUSAL** (`NO_CONSENSUS`, `value == null`). The
     engine NEVER silently picks a plurality / first / most-confident answer.
   - **Agreed value still verified.** A consensus value is re-run through the **non-bypassable
     provenance binder** (`bind_and_verify` / `bind_aggregate`) AND the **deterministic gate
     suite** (when a `gate_source` is supplied). A bind/gate failure → REFUSE (pass-through
     `PROVENANCE_REFUSED` / `GATE_FAIL`). Consensus is **additive**, never a substitute.
   - **Confidence by agreeing count.** `confidence_record(source_count=agreeing_count)`: a
     lone source is capped at `<= 0.7` and flagged single-source; `>= 2` agreeing sources lift
     above the cap.

### The consensus envelope
```
{ state ∈ {DELIVERED, REFUSED}, answer, value, agreeing_count, quorum, n,
  provenance, gate_verdict, confidence, redispatches,
  disagreement:{values_seen, spread, distinct_groups}, refusals[] }
```
Refusal reason codes: `NO_CONSENSUS` (escalation after re-dispatch), plus pass-through
`GATE_FAIL` / `PROVENANCE_REFUSED`.

### Asymmetric rules (read carefully)
- **Quorum is asymmetric, not majority-by-headcount.** "2-of-3" means **2 agreeing agents
  deliver**; it does NOT require a strict majority of however many actually returned. A lone
  agent never constitutes consensus (it falls to the single-source cap path).
- **Agreement is on SUBSTANCE, refusal is on ANY hard failure.** It takes `quorum` agents to
  AGREE, but it takes only ONE failing hard gate (or one unbindable agreed value) to REFUSE —
  delivery is the high bar, refusal is the safe default.
- **Re-dispatch is blind both ways.** Agents never learn they disagreed; the engine never
  learns which agent was "right". The only thing that crosses the wall is the structured
  `value` + its `json_field_path`.

### Subscription-only (locked)
The engine contains no model call and no API key. The blind agents are `general-purpose`
`Task()` agents that run on the **Claude Code subscription** — never `doppler`/env model keys,
never a third-party model SDK. (Doppler injects only the read-only Hypercore data creds for
the live adapter, never a model key.)

## Report-tier orchestration + the state machine (Demo — SLICE-HCA-08)

> **BUILT.** Orchestrator: `.claude/scripts/hca-deliver.py`
> (`ReportBuilder` / `build_report` / `route_figure_tier`). Walkthrough:
> `demos/demo-report-pipeline.md`. Tests: `.claude/scripts/tests/test_hca_report_feed.py`.

A **report / table** is assembled from **MULTIPLE figures**. Each figure runs the same
per-figure vertical the thin spine proves (plan → fetch → Tier-1 cache → provenance
bind+verify → deterministic gates), and the figures are bound into one report envelope. Each
figure carries its **own** `{label, value, unit/currency, provenance, gate_verdict,
confidence, complete}` so QA can independently re-resolve each figure into Tier-1 and re-do
the arithmetic.

### The report contract (hard)
- A report **DELIVERS only if EVERY figure delivers.**
- **Any figure that REFUSES surfaces as a refusal** in the report — the report **NAMES which
  figure / which gate failed**. A refusing figure is **never silently dropped** and a missing
  figure is **never fabricated**.
- The report's terminal state is the **WORST** of its figures' states:
  all DELIVERED → `DELIVERED`; any figure `NO_LIVE_DATA` → `NO_LIVE_DATA`; any figure
  `ESCALATED` (no quorum) → `ESCALATED`; otherwise any figure `REFUSED` → `REFUSED`.

### The full state machine

```
RECEIVED
  -> TIER_ROUTED            route_figure_tier(question)  (hca-route.classify, deterministic)
       | trivial single value                 -> DETERMINISTIC SPINE  (DeliverySpine.ask)
       | report/aggregation/high-stakes        -> CONSENSUS  (run_consensus over N blind agents)
  -> FETCH_OR_CACHE         read-only adapter; LIVE walks pages to completion under Doppler
       | no creds + live backend               -> NO_LIVE_DATA   (never fabricate)
  -> RAW_CACHED             Tier-1 RawApiResponse written immutably (content-addressed id)
  -> EXTRACT                normalize / pick the figure's value(s)
  -> [CONSENSUS]            report tier only: >= quorum blind-agent substance agreement,
                            else bounded BLIND re-dispatch, else ESCALATE (no silent pick)
  -> GATES                  deterministic gate suite (schema | pagination | freshness |
                            reconciliation | currency | drift); any hard FAIL -> REFUSE
  -> BOUND                  provenance binder re-reads Tier-1 at the cited path + matches
  -> DELIVERED | REFUSED | ESCALATED | NO_LIVE_DATA     (per figure)
  -> REPORT                 bind the per-figure terminal states (DELIVERED iff every figure did;
                            else surface each non-delivered figure in refusals[])
```

### Who spawns the blind agents (consensus vs spine)
The **real blind-agent `Task()` spawning is the MAIN Claude conversation's job** (the only
context with the `Task` tool — see the consensus section above). A Python script cannot spawn
`Task()` agents, so `run_consensus(question, agent_runner, ...)` takes an **injected**
`agent_runner` callable; the orchestrator wires it to N blind `general-purpose` agents. For
the orchestration's **own** live/offline demo (and for the report-binder unit tests) each
figure is assembled via the **deterministic spine** per figure; consensus is unit-tested
separately in `test_hca_consensus.py` with injected runners. A figure spec may opt into the
consensus path by supplying its own `agent_runner` (`ReportBuilder` then plans+fetches+caches
the figure and hands the consensus engine the real `gate_source`, so consensus stays
**additive** — the agreed value still passes the binder + the gate suite).

### Checkpointable / resumable
Every figure reads through the **same** Tier-1 cache. Tier-1 records are **content-addressed**
(hash of operation + variables, not of `fetched_at`), and the cache is **append-only /
immutable**: a re-run of the same figures resolves each query to the same id and the immutable
store returns the prior record (an identical re-write is an idempotent no-op, never an error).
A re-run therefore produces the **identical report off the same immutable Tier-1 ids** — resume
== consistent result, no Tier-1 divergence.

### The report envelope
```
{ state ∈ {DELIVERED, REFUSED, ESCALATED, NO_LIVE_DATA}, title,
  figures: [ {label, value, unit, currency, provenance, gate_verdict, confidence,
              complete, tier, state} ],          # DELIVERED figures only
  refusals: [ {figure, tier, figure_state, reason_code, reason,
               inner_reason_code, inner_reason, failed_gates?} ],  # every non-delivered figure
  generated_at, meta:{figure_count, delivered_count, refused_count, figure_states, skill} }
```
Report refusal reason codes: `FIGURE_REFUSED` (a constituent figure's gate/binder refused),
`NO_CONSENSUS` (a figure could not reach quorum → `ESCALATED`), `NO_LIVE_DATA`, plus the
pass-through `UNMAPPABLE_QUESTION` for a figure that names no fetchable entity.

## Forward pipeline (left → right)

```
NL question
  -> [Intake & Tier Router]            BUILT (SLICE-HCA-01) — hca-route.py
        trivial-lookup | report/aggregation/analysis  (deterministic; no data fetch)
  -> [Hypercore Adapter (CONTRACT)]    BUILT (SLICE-HCA-02) — hca-adapter.py
        read-only; FixtureBackend active; LiveBackend stubbed (NotImplementedError)
        |-- (no creds) --> NO_LIVE_DATA -> explicit "no live data" envelope (never fabricate)
  -> [Raw-Response Cache]              BUILT (SLICE-HCA-03) — Tier-1 RawApiResponse (truth)
  -> [Normalizer]                      BUILT (SLICE-HCA-03) — Tier-2 NormalizedAnswerRecord
  -> [Blind Extraction Agents x N]     BUILT (SLICE-HCA-06) — Task() general-purpose, no shared context
  -> [Consensus Evaluator]             BUILT (SLICE-HCA-06) — hca-consensus.py: substance consensus;
                                       bounded blind re-dispatch; ESCALATE (no silent pick)
  -> [Deterministic Gate Suite]        BUILT (SLICE-HCA-05) — schema | pagination-completeness
                                       | freshness | reconciliation | normalization | cap<=0.7
  -> [Provenance Binder]               BUILT (SLICE-HCA-04) — bind value->source; else REFUSE
  -> [Report Orchestration]            BUILT (SLICE-HCA-08) — hca-deliver.ReportBuilder:
                                       multi-figure report; per-figure provenance; DELIVERED iff
                                       every figure did; refusals name the figure+gate
  -> [Delivery / Feed Layer]           BUILT spine (SLICE-HCA-07) + consensus wrap (SLICE-HCA-06)
                                       + report (SLICE-HCA-08) + feed/manifest (SLICE-HCA-09) —
                                       envelope | REFUSED | ESCALATED | NO_LIVE_DATA |
                                       JSON/CSV/feed + schema-valid manifest
```

## What is built now (foundation)

| Stage | Artifact | Status |
|---|---|---|
| Intake & tier router | `.claude/scripts/hca-route.py` | BUILT — `--selftest` exits 0 |
| Shared vocabulary leaf | `.claude/scripts/hca-vocab.py` | BUILT — single source of truth for payoff / utilization / aggregation-analysis phrasing vocab + figure-kind constants, imported by route/deliver/figures/ontology (imports nothing from the skill); `--selftest` exits 0 |
| **Smart ask orchestrator (PRIMARY ENTRY)** | `.claude/scripts/hca-ask.py` | **BUILT** — `--ask "<question>"`: tries the deterministic spine first (unchanged), else FUNDING interpretation (investor + loan + metric → per-loan funding figure; investor + metric, NO loan → PORTFOLIO figure), else the confidence-graded EXPLORER fallback. Normalizes possessives ("XL's" → "XL"). Prefer this over `hca-deliver.py --ask` for arbitrary questions; the deterministic spine is still used verbatim for the questions it owns. **LEARNING LAYER:** when uncertain (unmapped metric like "amount due", or an ambiguous investor) it returns `NEEDS_SELECTION` with candidate choices for the caller to present as an MCQ; `--record '<candidate.record JSON>'` persists the pick (via `hca-learned.py`) and `--ask` re-runs it. Learned routing is consulted at the front of routing thereafter — so the same phrasing resolves directly next time, while the VALUE is always re-fetched live. |
| **General entity resolver** | `.claude/scripts/hca-entities.py` | **BUILT** — resolve ANY searchable entity by name (loans / clients / equities / **fundingEntities** = investors), reusing the loan resolver's scoring + thresholds + no-silent-pick. `resolve_entity(name, entity_type)`. |
| **Investor / funding figures** | `.claude/scripts/hca-funding.py` | **BUILT** — PER-LOAN: `funding_outstanding` (an investor's outstanding on a loan via `loanFunding.repaymentSchedule.summary.totalOutstanding`, reconciled to $0.01 + provenance-bound) + `funding_commitment` / `funding_participation` / `funding_receivable` (reliable 2-step assetId→loanFundingId). PORTFOLIO (`FundingPortfolioFigure`, across ALL an investor's loans): `portfolio_receivable` (reconciled, full InstallmentComponents identity; verified all 62 funding entities reconcile) + `portfolio_outstanding` (RECONCILED AGGREGATE — pages `loanFundings(fundingEntityId)` to completion and SUMS each position's `totalOutstanding`; every contributor reconciles its 5-component identity AND is provenance-bound to its own Tier-1 record, the page set is completeness-checked, the sum is `bind_aggregate`-verified; REFUSES on any unreconciled contributor or incomplete fetch — never a partial sum) + `portfolio_commitment` / `portfolio_disbursement` / `portfolio_contributed` / `portfolio_active_loans` (single-source). DERIVED: `per_diem_interest` (an investor's daily interest = `outstanding principal × (currentInterestRate / 100) ÷ day_count`; BOTH inputs read off the SAME cached `LoanFunding` record and INDEPENDENTLY provenance-bound, value COMPUTED live never cached; `currentInterestRate` is a PERCENT — the field returns `14` meaning 14%, verified live so it is `/100`; basis is outstanding PRINCIPAL not the net `total`; **Hypercore exposes NO day-count field anywhere in the schema**, so the convention is ASSUMED + STATED — default Actual/360, `day_count`-parameterizable; REFUSES on absent/non-positive rate or principal, never fabricates). Routed by "per diem" / "perdiem" / "daily interest" keywords (stripped from entity resolution). Live-verified XL (fundingEntity 3): on Beehive 134 → 6,922,294.60; portfolio receivable → 27,040,395.55; per-diem on Lux II 171 (loanFunding 338) → 1,029.236923/day (Actual/360). |
| **Confidence-graded explorer (fallback)** | `.claude/scripts/hca-explorer.py` | **BUILT** — when no verified figure matches, introspect the entity's type, match question keywords → fields (scalars AND **depth-1 nested objects**, e.g. `receivables.total` → `$.fundingEntity.receivables.total`), fetch live, return values with HIGH/MEDIUM/LOW confidence + provenance (best-effort, never fabricates — values are fetched-real or omitted). |
| **Learned-routing store** | `.claude/scripts/hca-learned.py` | **BUILT** — persistent JSON store backing the learning loop. Two tables: `metric_aliases` (phrase → canonical metric word, e.g. "amount due" → outstanding) and `entity_resolutions` (name → {entity_type, id}). CARDINAL RULE enforced by shape: **learn the ROUTING, never the VALUE** — there is no API that accepts a money value, so a stale number can never be replayed; the orchestrator re-applies the routing and re-fetches the live figure. Default path `~/Library/Application Support/acos-hypercore-ask/learned.json` (override `HCA_LEARNED_PATH`); atomic writes; fail-open reads; audit trail. |
| Skill scaffold + config | this `SKILL.md`, `config.yaml`, `README.md` | BUILT |
| Read-only adapter + fixtures | `.claude/scripts/hca-adapter.py`, `fixtures/`, `schemas/` | BUILT |
| Adapter tests (incl. read-only guard) | `.claude/scripts/tests/test_hca_adapter.py` | BUILT |
| Two-tier cache + normalize | `.claude/scripts/hca-cache.py`, `hca-normalize.py` | BUILT (SLICE-HCA-03) |
| Provenance binder | `.claude/scripts/hca-provenance.py` | BUILT (SLICE-HCA-04) |
| Deterministic gate suite | `.claude/scripts/hca-gates.py` | BUILT (SLICE-HCA-05) |
| **Thin end-to-end answer spine (Demo 1)** | `.claude/scripts/hca-deliver.py`, `demos/demo1-thin-path.md` | **BUILT (SLICE-HCA-07)** — `--ask` count/lookup/aggregate; live-verified |
| **Adversarial consensus engine (Demo 2)** | `.claude/scripts/hca-consensus.py`, `prompts/blind-extractor.md`, `demos/demo2-consensus.md` | **BUILT (SLICE-HCA-06)** — blind N-agent substance consensus; bounded blind re-dispatch; ESCALATE; binder+gates additive |
| **Report-tier orchestration** | `.claude/scripts/hca-deliver.py` (`ReportBuilder`/`build_report`/`route_figure_tier`), `demos/demo-report-pipeline.md` | **BUILT (SLICE-HCA-08)** — multi-figure report; per-figure provenance; DELIVERED iff every figure did; refusing figure surfaces (no silent drop); 4 terminal states; checkpointable |
| **Downstream feed / report / table formats (Demo 3)** | `.claude/scripts/hca-feed.py`, `schemas/feed-manifest.schema.json`, `feed-contract.md`, `demos/demo3-downstream-feed.md` | **BUILT (SLICE-HCA-09)** — JSON dataset + CSV table + trusted FEED w/ schema-valid per-figure-provenance manifest; real completeness proof; PII-safe; JSON↔CSV round-trip |
| **Fuzzy loan-name resolver** | `.claude/scripts/hca-resolve.py`, `tests/test_hca_resolve.py` | **BUILT (SLICE-HCA-12)** — real loans via `loans(filter:{searchString})`; difflib + token-set scoring; single high-confidence match → resolve+echo; ambiguous → candidates (no silent pick); live-verified beehive→134 |
| **Fuzzy loan-name resolver** | `.claude/scripts/hca-resolve.py`, `tests/test_hca_resolve.py` | **BUILT (SLICE-HCA-12)** — see Ask section |
| **Figure abstraction + payoff/early-redemption figure** | `.claude/scripts/hca-figures.py`, `tests/test_hca_figures.py` | **BUILT (SLICE-HCA-12/13)** — extensible `Figure`/`FigureRegistry`; `payoff_as_of` via `getLoanRepaymentDistribution` (exact known-good input, retry-on-500, provenance-bound `total`, component reconciliation $0.01, **currency from loan.currency**); live-verified loan 134 / 2026-06-30 → 31,888,682.99 USD |
| **Hypercore-native figures + derived utilization + requires_external** | `.claude/scripts/hca-figures.py`, `tests/test_hca_figures.py` | **BUILT (SLICE-HCA-13)** — 9 native LoanSummary figures (outstanding/principal/interest/penalties/due/overdue/commitment/disbursed/maturity), derived `utilization` (transparent formula), 4 `requires_external` (LTV/DSCR/debt_yield/cap_rate → clean KG-pending REFUSAL, never fabricate; PRISM covenant thresholds carried as metadata); live-verified loan 134 + 141-loan portfolio total |
| **Private-credit domain ontology** | `.claude/scripts/hca-ontology.py`, `tests/test_hca_ontology.py` | **BUILT (SLICE-HCA-13)** — PRISM-seeded concept map (15 concepts: name + synonyms + plain-English definition + kind + source + unit + covenant); resolves a phrasing → concept (synonyms + fuzzy + verbatim-substring); unmapped concept REFUSES (named), never guesses |
| Evidence-bundle wiring | `python3 hca-route.py` + `hca_evidence_bundle_dir()` helper | STUB |

Every pipeline stage above is BUILT and live-verified; only the evidence-bundle wiring
remains a STUB (see the table row above).

## Evidence bundles

Each slice writes a 7-part evidence bundle under
`.acos/evidence/[DATE]/[SLICE-ID]/`. The foundation bundle for slices 00–02 lives at
`.acos/evidence/2026-06-18/SLICE-HCA-00-02/`.

## Open items (carried until access)

- Exact Hypercore endpoints / schemas / auth scheme / pagination cursor semantics — `TBD`
  (partner-gated; OQ1). Fixtures and schemas here are **PLACEHOLDER** modeling targets.
- Secret store finalization — defaulted to env vars via Doppler (OQ2).
- Concrete freshness-window numeric defaults — configurable; current values `Assumption` (OQ3).
