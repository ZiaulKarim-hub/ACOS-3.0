# Demo — Report-tier orchestration (SLICE-HCA-08)

The full **report / aggregation-tier** vertical of `acos-hypercore-ask`: a multi-figure
report/table is assembled where **EACH figure carries its own provenance + confidence + gate
verdict + completeness**, and the report **delivers only if every figure delivers** — any
refusing figure surfaces (naming the figure + the failing gate), never silently dropped, never
fabricated.

Orchestrator: `.claude/scripts/hca-deliver.py`
(`ReportBuilder` / `build_report` / `route_figure_tier`). It composes slices 02–06 end to end
and WRAPS the thin spine (slice-07) once **per figure**; it does not replace it.

## The state machine

```
RECEIVED
  -> TIER_ROUTED        route_figure_tier(question)  (delegates to hca-route.classify)
       | trivial single value                 -> DETERMINISTIC SPINE  (DeliverySpine.ask)
       | report/aggregation/high-stakes        -> CONSENSUS  (run_consensus, N blind agents)
  -> FETCH_OR_CACHE     read-only adapter; LIVE walks pages to completion under Doppler
       | no creds + live backend               -> NO_LIVE_DATA   (never fabricate)
  -> RAW_CACHED         Tier-1 RawApiResponse written immutably (content-addressed id)
  -> EXTRACT            pick the figure's value(s)
  -> [CONSENSUS]        report tier only: >= quorum substance agreement, else bounded BLIND
                        re-dispatch, else ESCALATE (no silent pick)
  -> GATES              deterministic gate suite; any hard FAIL -> REFUSE (names the gate)
  -> BOUND              provenance binder re-reads Tier-1 at the cited path + matches
  -> DELIVERED | REFUSED | ESCALATED | NO_LIVE_DATA   (per figure)
  -> REPORT             bind the per-figure terminal states (DELIVERED iff every figure did)
```

The report's terminal state is the **worst** of its figures' states:
all DELIVERED → `DELIVERED`; any `NO_LIVE_DATA` → `NO_LIVE_DATA`; any `ESCALATED` →
`ESCALATED`; otherwise any `REFUSED` → `REFUSED`.

## Tier routing

`route_figure_tier(question)` calls the deterministic intake router (`hca-route.classify`) and
maps its class onto the two delivery tiers:

| Question | Router class | Delivery tier |
|---|---|---|
| `what is the status of loan L-001?` | `trivial-lookup` | **trivial** → deterministic spine (one extraction, gated) |
| `how many loans are there?` | `report/aggregation/analysis` | **report** → consensus-required |
| `what is the total commitment across all loans?` | `report/aggregation/analysis` | **report** → consensus-required |

The conservative default is report-tier (consensus-required): when in doubt, demand consensus.

## Who spawns the blind agents

The **real blind-agent `Task()` spawning is the MAIN Claude conversation's job** (the only
context with the `Task` tool — see the consensus section in `SKILL.md` / `demo2-consensus.md`).
A Python script cannot spawn `Task()` agents, so `run_consensus(question, agent_runner, ...)`
takes an **injected** `agent_runner`. For the orchestration's **own** live/offline demo each
figure is assembled via the **deterministic spine** per figure; consensus is unit-tested
separately with injected runners. A figure spec may opt into the consensus path by supplying
its own `agent_runner` — `ReportBuilder` then plans+fetches+caches the figure and hands the
consensus engine the real `gate_source`, so consensus stays **additive** (the agreed value
still passes the binder + the gate suite).

## Build a report

```python
import importlib.util, os, sys
def load(m, f):
    s = importlib.util.spec_from_file_location(m, os.path.join(".claude/scripts", f))
    mod = importlib.util.module_from_spec(s); sys.modules[m] = mod; s.loader.exec_module(mod); return mod
adapter = load("hca_adapter", "hca-adapter.py")
deliver = load("hca_deliver", "hca-deliver.py")

ad = adapter.HypercoreAdapter(adapter.select_backend(backend="live"))   # read-only, Doppler creds
builder = deliver.ReportBuilder(adapter=ad)
report = builder.build("OKOA Portfolio Summary", [
    {"label": "loan_count",       "question": "how many loans are there?"},
    {"label": "client_count",     "question": "how many clients are there?"},
    {"label": "total_commitment", "unit": "USD",
     "question": "what is the total commitment across all loans?"},
])
```

Each figure spec is `{label, question, unit?, agent_runner?, force_tier?, quorum?, n?,
max_redispatch?}`.

## Live-verified portfolio-summary report (2026-06-18 — aggregates only, NO PII)

`build_report("OKOA Portfolio Summary", [loan_count, client_count, total_commitment])` on the
live read-only backend under Doppler:

```
report.state: DELIVERED
figure_states: ['DELIVERED', 'DELIVERED', 'DELIVERED']
  FIGURE loan_count:       value=141              tier=report gate=pass complete=True conf=0.7  prov=$.body.reported_total
  FIGURE client_count:     value=124              tier=report gate=pass complete=True conf=0.7  prov=$.body.reported_total
  FIGURE total_commitment: value=434989118.78 USD tier=report gate=pass complete=True conf=1.0  prov=aggregate x141
```

- **Each figure carries its own resolvable provenance** — the count figures cite
  `$.body.reported_total`; the aggregate cites **141 contributing source bindings**, so QA can
  re-resolve each contributor into Tier-1 and re-add the sum (= 434,989,118.78).
- **Each figure has its own gate verdict** (`pass`), `complete: true`, and confidence
  (single-source counts capped at 0.7; the 141-source aggregate lifts to 1.0).

## A refusing figure surfaces — never a silent drop, never a number

Plant a truncated loan list (a real Hypercore truncation, or a truncated fixture). The
**count figure** fails the `pagination_completeness` hard gate; the report surfaces it:

```
report.state: REFUSED
delivered figures: ['loan_status']
refusals: [('loan_count', 'FIGURE_REFUSED', ['pagination_completeness'])]
```

- The refused figure is **NOT** among delivered figures (no fabricated value).
- It **IS** in `refusals[]`, naming the figure **and** the failing gate (no silent drop).
- A single figure's gate failure refuses **only that figure** — the other figure
  (`loan_status`) still delivered. The report as a whole is `REFUSED` because not every figure
  delivered.

A mixed-currency aggregate refuses on `unit_currency_normalization` the same way.

## The four terminal states (all reachable)

| State | How it is reached |
|---|---|
| `DELIVERED` | every figure delivered (provenance bound + gates pass) |
| `REFUSED` | a figure's hard gate / binder refused, or its question is unmappable |
| `ESCALATED` | a report-tier figure could not reach consensus quorum after bounded blind re-dispatch |
| `NO_LIVE_DATA` | the live backend has no creds — explicit, never a fabricated number |

`ESCALATED` is exercised by routing a figure through `run_consensus` with three disagreeing
blind agents (and a re-dispatch that still disagrees): the engine **escalates with no silent
pick**, and the report carries that figure's `NO_CONSENSUS` refusal.

## Checkpointable / resumable

Tier-1 records are **content-addressed** (hash of operation + variables, not of `fetched_at`)
and the cache is **append-only / immutable**. A re-run of the same figures resolves each query
to the same id; an identical re-write is an idempotent no-op (never an `ImmutableCacheError`).
A re-run therefore produces the **identical report off the same immutable Tier-1 ids** —
resume == consistent result, no Tier-1 divergence (proven by
`test_hca_report_feed.CheckpointResumeTest`).

## Tests

`.claude/scripts/tests/test_hca_report_feed.py` (stdlib `unittest`, fixtures only, no network):
multi-figure report with per-figure provenance; per-figure provenance re-resolves into Tier-1
+ re-does the arithmetic; one refusing figure surfaces (no silent drop); the four terminal
states; consensus escalation (no quorum) → `ESCALATED` and quorum → `DELIVERED`; checkpoint/
resume off the immutable cache.

```bash
python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py'
```
