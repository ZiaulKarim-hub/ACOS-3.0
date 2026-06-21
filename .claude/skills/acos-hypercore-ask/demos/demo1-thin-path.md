# Demo 1 — Thin end-to-end verified-answer path (SLICE-HCA-07)

The first demo-able vertical of `acos-hypercore-ask`: a natural-language portfolio question
becomes a **provenance-bound, gate-verified answer envelope** — or an explicit refusal — with
**no consensus and no model call**. This is the deterministic SPINE that slice-06 (consensus)
and slice-08/09 (report/feed orchestration) WRAP; they do not replace it.

Engine: `.claude/scripts/hca-deliver.py` (`--ask "<question>"`).

## The spine (left → right)

```
NL question
  -> [plan]        hca-deliver.plan_question
                     map question -> (intent, entity_type, query) via the live entity
                     registry (hca-live.ENTITY_REGISTRY) + introspected schema.
                     UNMAPPABLE (no fetchable entity / no supported intent) => REFUSE — never guess.
  -> [fetch]       hca-adapter (read-only contract: get_entity / list_entities)
                     LIVE when creds present: LiveBackend walks OFFSET pages (skip/limit) to
                     COMPLETION. No creds + live backend => NO_LIVE_DATA (never fabricate).
                     FixtureBackend serves clearly-labeled fixture data for tests.
  -> [cache]       hca-cache.TwoTierCache
                     Tier-1 RawApiResponse written immutably (content-addressed); Tier-2
                     normalized view derived from Tier-1 only (never invented).
  -> [provenance]  hca-provenance.ProvenanceEngine.bind_and_verify / bind_aggregate
                     EVERY delivered value is re-read from Tier-1 at its cited json_field_path
                     and must MATCH. Any unbindable/mismatched value => REFUSE.
  -> [gates]       hca-gates.GateSuite
                     trivial single-value lookup  -> deterministic_subset (schema, freshness,
                                                      drift, single-source confidence cap)
                     count / aggregate (list)      -> run_all (adds pagination-completeness,
                                                      cross-field reconciliation, mixed-currency
                                                      refusal)
                     verdict.outcome == "refuse"  => structured REFUSAL naming the failing
                     gate — NEVER a number.
  -> [envelope]    { state, answer, values:[{value, provenance:{raw_response_id,
                     json_field_path}, confidence}], gate_verdict, complete, refusals[] }
```

### Non-bypassable

A value reaches the `answer` field ONLY after (a) its provenance binding VERIFIED against
Tier-1 **and** (b) the gate suite returned `outcome == pass`. There is no code path that emits
`answer` while skipping the binder or the gates. A tampered Tier-1 record (value no longer
matches the cited path) is caught because the binder re-reads + compares — proven by
`test_hca_deliver.NonBypassableTest`.

## Supported thin-tier intents

| Intent | Example question | Gate tier | Headline gate(s) |
|---|---|---|---|
| **count** | "how many loans/clients are there?" | `run_all` | pagination-completeness |
| **lookup** | "what is the status of loan L-001?" | `deterministic_subset` | schema + freshness + drift |
| **aggregate** | "what is the total commitment across all loans?" | `run_all` (aggregating) | reconciliation + unit/currency |

Lookups read NON-PII fields only (status, name, commitment, refId, start/end dates) — contact
PII is minimized out of the Tier-2 view by `hca-normalize` and is never the lookup target.

## Run it

```bash
# Live (read-only) via Doppler — the credentials are injected at runtime, never stored:
doppler run --project hypercore-ask --config dev_personal -- \
    python3 .claude/scripts/hca-deliver.py --ask "how many loans are there?"

# Force a backend / page size / full envelope:
python3 .claude/scripts/hca-deliver.py --ask "..." --backend fixture
python3 .claude/scripts/hca-deliver.py --ask "..." --full
```

Exit code: `0` only on `DELIVERED`; `1` on any `REFUSED` / `NO_LIVE_DATA` terminal state
(so shell callers can branch). The default print is a PII-safe summary (counts, aggregates,
field NAMES, provenance pointers, gate outcome) — never a raw borrower record.

## Sample DELIVERED envelope (live-verified 2026-06-18 — counts only, no PII)

`--ask "how many loans are there?"`:

```json
{
  "state": "DELIVERED",
  "answer": "There are 141 loans.",
  "values": [
    {
      "value": 141,
      "currency": null,
      "confidence": 0.7,
      "provenance": {
        "raw_response_id": "live:list:loan:2026-06-18T22:44:47Z",
        "json_field_path": "$.body.reported_total"
      }
    }
  ],
  "gate_verdict": {
    "outcome": "pass",
    "tier": "full",
    "failures": [],
    "schema_ok": true,
    "pagination_complete": true,
    "freshness_ok": true,
    "reconciliation_ok": true,
    "normalization_applied": true,
    "schema_drift_ok": true,
    "provenance_ok": true
  },
  "complete": true,
  "refusals": [],
  "meta": { "reported_total": 141, "fetched": 141, "pages": 3, "backend": "live" }
}
```

Other live-verified results (same envelope shape):
- `"how many clients are there?"` → **124 clients**, gate `pass`, `complete: true`, 3 pages walked.
- `"what is the total commitment across all loans?"` → **434,989,118.78 USD** across 141
  loans, `aggregate: true` with 141 contributing source bindings, multi-source `confidence: 1.0`,
  reconciliation + currency gates `pass`.

## Sample REFUSED envelope (gate fail — names the gate, NEVER a number)

A truncated list walk (a real Hypercore truncation, or the `gql_list_loan_truncated__short`
fixture) fails pagination-completeness:

```json
{
  "state": "REFUSED",
  "answer": null,
  "values": [],
  "gate_verdict": { "outcome": "refuse", "failures": ["pagination_completeness"], "...": "..." },
  "complete": false,
  "refusals": [
    {
      "reason_code": "GATE_FAIL",
      "reason": "delivery refused — deterministic gate(s) failed: pagination_completeness (no value is delivered while a hard gate fails)",
      "failed_gates": ["pagination_completeness"]
    }
  ]
}
```

A mixed-currency aggregate refuses on `unit_currency_normalization` the same way. An
unmappable question (`"who is the CEO?"`) refuses with `reason_code: "UNMAPPABLE_QUESTION"`.

## Sample NO_LIVE_DATA envelope (no creds — explicit, never fabricated)

With the live backend selected but credentials absent (`is_live() == false`):

```json
{
  "state": "NO_LIVE_DATA",
  "answer": null,
  "values": [],
  "gate_verdict": null,
  "complete": false,
  "refusals": [
    { "reason_code": "NO_LIVE_DATA", "reason": "live data requested but adapter is not live (Hypercore access not yet provisioned)" }
  ],
  "meta": { "message": "no live data — Hypercore access not yet provisioned" }
}
```

The same question NEVER returns a fabricated number on this path (slice acceptance: REQUIRED,
fail = REJECT). The FixtureBackend, by contrast, legitimately serves clearly-labeled fixture
data — that is not the no-live-data state.

## Tests

`.claude/scripts/tests/test_hca_deliver.py` (stdlib `unittest`, fixtures only, no network):
happy path (lookup/count/aggregate with resolvable provenance + gate pass), unmappable ⇒
refuse, gate-fail ⇒ refusal-naming-the-gate (mixed currency + truncation), NO_LIVE_DATA,
non-bypassable binder (tampered Tier-1), and a no-network-import guard.

```bash
python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py'
```
