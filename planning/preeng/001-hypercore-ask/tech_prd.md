# Technical PRD — acos-hypercore-ask

> Output of `/preeng.plan` (companion to `plan.md`, `data-model.md`). Technical specification of the
> components, contracts, gates, consensus protocol, configuration, and stubbing strategy. All
> Hypercore API specifics are `TBD`/`Assumption` until partner-gated access; everything is designed
> behind the adapter so the skill is buildable/testable on fixtures now.

## 1. Component inventory

| Component | Kind | Location (planned) | Responsibility |
|---|---|---|---|
| `acos-hypercore-ask` skill | ACOS skill | `.claude/skills/acos-hypercore-ask/SKILL.md` (+ prompts/) | Orchestrates the pipeline; defines the NL command surface; wires evidence bundles |
| Intake & Tier Router | script | `.claude/scripts/hca-route.py` | Classify NL question → verification tier (trivial-lookup vs report/aggregation/analysis) |
| **Hypercore Adapter (contract)** | script/module | `.claude/scripts/hca-adapter.py` | Read-only client contract; **fixture backend now**, live backend stubbed/TODO; raises `NoLiveDataError` absent creds |
| Fixture/Mock backend | fixtures | `.claude/skills/acos-hypercore-ask/fixtures/` | Canned raw API responses standing in for real endpoints |
| Raw-Response Cache | script | `.claude/scripts/hca-cache.py` | Persist/lookup Tier-1 `RawApiResponse` truth records keyed for provenance |
| Normalizer | script | `.claude/scripts/hca-normalize.py` | Build Tier-2 `NormalizedAnswerRecord` derived view; unit/currency normalization |
| Blind Extraction Agents | `general-purpose` via `Task()` | (dispatched at runtime) | N independent blind extractions; no shared context; subscription-only |
| Consensus Evaluator | script | `.claude/scripts/hca-consensus.py` | Substance consensus; quorum; re-dispatch/escalate logic |
| Deterministic Gate Suite | script | `.claude/scripts/hca-gates.py` | schema/pagination/freshness/reconciliation/normalization/confidence-cap |
| Provenance Binder | script | `.claude/scripts/hca-provenance.py` | Bind value→provenance; refuse-on-missing |
| Delivery / Feed Layer | script | `.claude/scripts/hca-deliver.py` | Answer envelope; refusal; no-live-data; feed format + manifest |
| Schema/Drift definitions | data | `.claude/skills/acos-hypercore-ask/schemas/` | Expected entity schemas for validation + drift detection |

> All scripts are **Python 3 stdlib only** (Decision, plan §2). No third-party deps. Model work is
> never done with `ANTHROPIC_API_KEY`; blind agents are spawned via `Task()`; any in-script "model"
> step is a `Task()` dispatch or a main-thread Read, never a direct API call.

## 2. Hypercore Adapter contract (read-only, stubbed-until-access)

The adapter is the **only** module that talks to Hypercore. Everything else depends on the contract,
not the live API. This is what makes the skill buildable before credentials.

**Contract surface (read-only; signatures are stable, bodies stubbed):**
- `is_live() -> bool` — true only when credentials + endpoint config are present and valid.
- `get_entity(entity_type, id, *, params) -> RawApiResponse` — single-record read.
- `list_entities(entity_type, *, filters, cursor) -> RawApiResponsePage` — paginated read; returns
  cursor + reported total for the **pagination-completeness gate**.
- `get_schema(entity_type) -> SchemaDescriptor` — declared/expected schema for **drift detection**.
- `subscribe_events(...) -> EventStream` — webhook/polling hook for **freshness invalidation** (TODO;
  polling fallback default).
- **No** `create_*`, `update_*`, `delete_*`, `post_*`, or any mutating method exists on the contract.
  Read-only is enforced by omission *and* by a guard test that asserts no mutating verb is callable.

**Backends behind the contract:**
- `FixtureBackend` (active now) — serves canned `RawApiResponse` JSON from `fixtures/`; deterministic;
  used for all dev/test.
- `LiveBackend` (stubbed/TODO) — raises `NotImplementedError("Hypercore live backend TODO — access
  not yet provisioned")`; to be implemented behind the *unchanged* contract once credentials arrive.

**Degradation:** if `is_live()` is false and the caller requested live data, the pipeline enters the
`NO_LIVE_DATA` state and the delivery layer emits an explicit "no live data — Hypercore access not
yet provisioned" envelope. **It never fabricates.** Fixture-backed runs are clearly labeled as
fixture data, not live.

**Auth/security (TBD specifics):** credentials read from env/secret store at runtime; TLS 1.2+
enforced on live transport; no credentials in repo; RBAC scope honored per request; exact auth
scheme (OAuth/API-key/etc.) `TBD` pending docs.

## 3. Two-tier data model boundary

- **Tier 1 — `RawApiResponse` (source of truth):** the exact raw JSON returned by the adapter, plus
  `{endpoint, request_params, timestamp, http_status, cursor, reported_total}`. Immutable once
  cached. **Provenance points here.** (See `data-model.md`.)
- **Tier 2 — `NormalizedAnswerRecord` (derived view):** token-efficient normalized projection
  (typed, unit/currency-normalized) built deterministically from Tier 1. Every normalized field
  carries a back-pointer (`json_field_path`) into its Tier-1 source for provenance binding.
- **Agent tiering:** blind extraction agents receive the **minimum tier** needed — typically a scoped
  Tier-1 slice for the value(s) in question — never the full cache (token efficiency + PII minimization).

## 4. Verification pipeline (technical detail)

### 4.1 Tier routing
- **Trivial lookup** (single value, single record, no aggregation) → deterministic-gates-only path
  (consensus optional / N may be 1); provenance still universal.
- **Report / aggregation / analysis** (multi-record, math, cross-entity) → **full adversarial
  consensus mandatory** + full gate suite.

### 4.2 Blind extraction + consensus protocol
- Dispatch **N blind `general-purpose` agents via `Task()`** (default N=3, configurable), each given
  only its scoped Tier-1 slice and the question, **no shared context, no sight of each other's output**.
- Each returns `{value, json_field_path, raw_response_id, agent_confidence}`.
- **Substance consensus** = agreement on the **normalized substance** of the value (exact number/
  name/date after unit/currency normalization), not on prose. Default quorum **2-of-3 asymmetric**
  (configurable per tier).
- **Disagreement → blind re-dispatch** (fresh agents, bounded retries, default 1 retry) → if still no
  quorum, **ESCALATE** to the user; never a silent pick.
- Single-source values (only one agent / single raw response) are capped at **confidence ≤ 0.7** and
  flagged.

### 4.3 Deterministic gate suite (layered underneath consensus)
Run on the consensus-agreed value(s) before binding/delivery. Any hard failure → **REFUSE**.
1. **Schema validation** — value's source record conforms to the expected entity schema.
2. **Pagination-completeness** — for lists/aggregates, fetched count / cursor exhaustion reconciles
   with `reported_total`; otherwise refuse (no silent truncation).
3. **Freshness window** — Tier-1 source `timestamp` within the configured window for that entity
   class; else refuse or flag-and-refresh (never serve stale silently).
4. **Cross-field reconciliation** — related fields agree (e.g., drawdowns + repayments vs.
   outstanding; sum of parts vs. reported total).
5. **Unit/currency normalization** — units/currencies normalized before any comparison/aggregation.
6. **Single-source confidence cap** — single-source figures forced to confidence ≤ 0.7.

### 4.4 Provenance binding (universal)
Every delivered value gets a `ProvenanceBinding` = `{endpoint, request_params, timestamp,
json_field_path, raw_response_id}` resolving to a cached `RawApiResponse`. **Missing binding →
REFUSE.** Aggregated values carry bindings for each contributing source.

### 4.5 Delivery
Answer envelope = `value(s) + provenance citation(s) + confidence + freshness stamp + verification
tier`. Single-source figures visibly flagged. Alternative terminal states: `REFUSED`, `ESCALATED`,
`NO_LIVE_DATA`. Downstream feed = report/table/dataset (JSON/CSV) with embedded per-value provenance/
confidence + a manifest (source pointers, freshness, schema version, completeness proof).

## 5. Configuration (env/secret + skill config)

```yaml
# planned skill config (values configurable; secrets NOT here)
consensus:
  default_quorum: "2-of-3"        # configurable per tier
  agent_count: 3
  redispatch_retries: 1
freshness_windows_days:           # per entity class (conservative defaults; Assumption)
  balances_servicing: 1
  payments_drawdowns: 1
  reference_static: 30
confidence:
  single_source_cap: 0.7
adapter:
  backend: "fixture"              # "fixture" until access; "live" after
  # credentials: read from env/secret store at runtime; NEVER stored here
```

Secrets (`HYPERCORE_API_*`) are read from the environment / secret store at runtime only; **no
credentials in repo**. Exact variable names + secret store `TBD` at provisioning.

## 6. Security & compliance (technical)

- Read-only adapter (no mutating methods exist); guard test enforces it.
- TLS 1.2+ on live transport; AES-256 at rest for any persisted cache (honor Hypercore posture).
- RBAC scope honored per request; SOC 2 / GDPR posture respected.
- **PII discipline:** logs and evidence bundles are PII-scrubbed (borrower PII / financials redacted
  to need-to-know); raw cache access is least-privilege; agents receive minimal tier slices.
- Subscription-only: no `ANTHROPIC_API_KEY`; all model work via Read / `Task()`.

## 7. Orchestration / durability / observability

- Eventual executor: `/acos-execute-slice`. Each pipeline stage is checkpointed; resume from the last
  persisted Tier-1 cache without re-fetching.
- Human-in-the-loop: PM/QA approval pauses; `ESCALATED` consensus pauses for user decision.
- Observability: per-agent/slice logs/traces/metrics; consensus + gate outcomes recorded
  (PII-scrubbed) into the evidence bundle; agent identity → `.acos/metrics/agent-completions.log`.

## 8. Stubbing / fixture strategy (buildable before access)

- All live calls live **only** in `LiveBackend` (stubbed `NotImplementedError`).
- `FixtureBackend` + `fixtures/` provide canned `RawApiResponse` records for every modeled entity,
  enough to exercise: trivial lookup, paginated list (incl. a deliberately-truncated fixture to test
  the completeness gate), an aggregation/report (to test reconciliation + consensus), a stale fixture
  (to test freshness), and a drifted-schema fixture (to test drift detection).
- Tests run entirely offline; no network, no credentials, no API key.

## 9. Open technical items (carried)

- Exact endpoints/schemas/auth/pagination/webhook contract — `TBD` until access (OQ1).
- Secret store + env var names — `TBD` at provisioning (OQ2).
- Concrete freshness-window numeric defaults — configurable; starting values above are `Assumption` (OQ3).
- Final per-tier quorum N — default 2-of-3, configurable (OQ4, decided).
- Per-consumer feed-format refinements — `Assumption` set above (OQ6).
