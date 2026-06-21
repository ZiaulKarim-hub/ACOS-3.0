# `acos-hypercore-ask` trusted-feed — consumer contract (SLICE-HCA-09)

This document is the **contract** another ACOS skill honors when it consumes an
`acos-hypercore-ask` feed as a **trusted input**. A feed is the verified report data PLUS a
**manifest** that lets the consumer (a) trace every value back to a cached Tier-1 raw API
response, (b) confirm the completeness proof is real, and (c) honor refusals + confidence.

Renderer: `.claude/scripts/hca-feed.py` (`--format json|csv|feed`).
Manifest schema: `schemas/feed-manifest.schema.json`. Feed/schema version: **1.0**.

---

## 1. The three formats

| Format | Function | What it is |
|---|---|---|
| **JSON dataset** | `render_json(report)` / `render_dataset(report)` | the data + per-value provenance/confidence/completeness/gate verdict, machine-structured |
| **CSV table** | `render_csv(report)` | one row per delivered figure; well-formed (stdlib `csv`, quoted); round-trips with the JSON dataset |
| **Trusted FEED** | `render_feed(report)` | `{ kind, skill, schema_version, generated_at, manifest, dataset }` — the dataset + the trust manifest |

All three are produced from a **verified report envelope** (the output of slice-08
`hca-deliver.build_report` / `ReportBuilder.build`, or a single slice-07 answer envelope).

---

## 2. The feed object

```jsonc
{
  "kind": "hca-trusted-feed",
  "skill": "acos-hypercore-ask",
  "schema_version": "1.0",
  "generated_at": "2026-06-18T23:10:49Z",
  "manifest": { ...the trust header (see §3)... },
  "dataset": { ...the data the consumer ingests (see §4)... }
}
```

The consumer reads the **manifest first** to establish trust, then ingests `dataset.rows`.

---

## 3. The manifest (the trust header) — `schemas/feed-manifest.schema.json`

```jsonc
{
  "kind": "hca-trusted-feed:manifest",
  "skill": "acos-hypercore-ask",
  "schema_version": "1.0",
  "generated_at": "...",
  "title": "OKOA Portfolio Summary",
  "state": "DELIVERED",                 // DELIVERED | REFUSED | ESCALATED | NO_LIVE_DATA
  "pii_safe": true,
  "figure_count": 3, "delivered_count": 3, "refused_count": 0,
  "figures": [
    {
      "label": "total_commitment", "unit": "USD", "currency": "USD",
      "confidence": 1.0, "source_count": 141, "tier": "report",
      "provenance": {                   // HOW to re-resolve the value into Tier-1
        "aggregate": true,
        "raw_response_id": null, "json_field_path": null,
        "contributing": [ {"raw_response_id": "...", "json_field_path": "$.body.data[0].commitment"}, ... ],
        "source_count": 141
      },
      "completeness": {                 // REAL pagination-completeness gate result (not a placeholder)
        "complete": true, "pagination_complete": true,
        "gate_outcome": "pass", "gate_tier": "full"
      },
      "freshness": { "freshness_ok": true },
      "gate_verdict": { "outcome": "pass", "schema_ok": true, "pagination_complete": true,
                        "freshness_ok": true, "reconciliation_ok": true,
                        "normalization_applied": true, "schema_drift_ok": true,
                        "provenance_ok": true, "failures": [] }
    }
  ],
  "refusals": [ ...every figure that did NOT deliver (see §5)... ]
}
```

### What the consumer MUST do with the manifest

1. **Validate it.** Validate against `feed-manifest.schema.json` before trusting anything.
   `hca-feed.validate_manifest(manifest)` returns `{ok, errors:[...]}` using a stdlib
   structural validator (no `jsonschema` dependency). **A feed whose manifest does not validate
   MUST be rejected.**
2. **Confirm the completeness proof is real.** Each figure's `completeness.pagination_complete`
   is the **actual pagination-completeness gate boolean** (mirrored in
   `gate_verdict.pagination_complete`), not a placeholder string. A consumer that needs a
   complete dataset MUST require `completeness.complete == true` **and**
   `completeness.pagination_complete == true`.
3. **Trace each value.** For each figure, resolve `provenance` into Tier-1: a single value via
   `{raw_response_id, json_field_path}`; an aggregate via `provenance.contributing[]` (one
   pointer per source). `hca-cache.TwoTierCache.resolve_binding(pointer)` returns
   `(value, ok)`. **A value whose provenance does not resolve MUST NOT be trusted.**
4. **Honor confidence.** A single-source figure is capped at `confidence <= 0.7` and flagged;
   a multi-source (consensus) figure may exceed it. A consumer with a confidence floor MUST
   drop / down-weight figures below it.

---

## 4. The dataset (what the consumer ingests) — `dataset.rows`

```jsonc
{
  "kind": "hca-trusted-feed:dataset", "skill": "...", "schema_version": "1.0",
  "generated_at": "...", "title": "...", "pii_safe": true, "state": "DELIVERED",
  "rows": [
    { "label": "loan_count", "value": 141, "unit": null, "currency": null,
      "confidence": 0.7,
      "provenance": {"raw_response_id": "live:list:loan:...", "json_field_path": "$.body.reported_total", "aggregate": false, "source_count": 1},
      "completeness": {"complete": true, "pagination_complete": true, "gate_outcome": "pass", "gate_tier": "full"},
      "freshness": {"freshness_ok": true},
      "gate_verdict": { ... },
      "tier": "report", "pii_redacted": false }
  ],
  "refusals": [ ... ]                    // mirrors the manifest refusals
}
```

- **Only DELIVERED figures are rows.** A refused figure is **never** a row (no fabricated
  value) — it lives in `refusals[]` (§5).
- A row whose `pii_redacted == true` carries `value: null` (the value was a per-record
  borrower value, omitted in PII-safe mode — see §6). The consumer still gets the label, the
  field-name, the provenance pointer, the confidence, and the gate verdict.

### CSV equivalence

The CSV table is the same rows, one per line, with columns:
`label, value, unit, currency, confidence, raw_response_id, json_field_path, aggregate,
source_count, complete, pagination_complete, freshness_ok, gate_outcome, tier, pii_redacted`.
It is well-formed (stdlib `csv`, `QUOTE_MINIMAL`, `\r\n` terminator) and **round-trips** with
the JSON dataset (`parse_csv(render_csv(report))` reproduces the rows). Embedded commas /
quotes / newlines never corrupt a field.

---

## 5. Refusals — the consumer MUST honor them

```jsonc
"refusals": [
  { "figure": "loan_count", "tier": "report", "figure_state": "REFUSED",
    "reason_code": "FIGURE_REFUSED",          // FIGURE_REFUSED | NO_CONSENSUS | NO_LIVE_DATA | UNMAPPABLE_QUESTION
    "reason": "figure 'loan_count' did not deliver (REFUSED): delivery refused — gate(s) failed: pagination_completeness ...",
    "inner_reason_code": "GATE_FAIL", "inner_reason": "...",
    "failed_gates": ["pagination_completeness"] }
]
```

A refused figure is **surfaced, never silently dropped**. The consumer **MUST**:
- treat a refused figure as **absent data**, never substitute a guess;
- if the figure is required, **fail / flag** the ingest (do not proceed as if complete);
- surface the `reason` / `failed_gates` to its own caller (the trust chain is end-to-end).

`reason_code` values: `FIGURE_REFUSED` (a gate/binder refused the figure), `NO_CONSENSUS`
(the figure could not reach quorum → the figure state is `ESCALATED`), `NO_LIVE_DATA` (no live
creds), `UNMAPPABLE_QUESTION` (the figure named no fetchable entity).

---

## 6. PII safety (LOCKED)

- Feeds are **PII-safe by default** (`pii_safe=true`). A PII-safe feed emits **only
  portfolio-level** values (aggregates / counts) plus **field-names + provenance pointers**
  for any per-record figure — the per-record value is redacted to `null` and flagged
  `pii_redacted: true`. Pointers, counts, and field-names are **not** PII.
- A non-PII-safe feed (`pii_safe=false`, real per-record values) MUST be written **only** to
  the git-ignored runtime area (`.acos/state/`). `hca-feed.write_artifact(...)` **refuses**
  (raises `PermissionError`) to write a non-PII-safe artifact anywhere in the tracked tree.
- Therefore a consumer reading a feed **from the tracked tree / evidence** can assume it is
  PII-safe; a consumer that needs per-record values must read from the runtime area and apply
  its own PII handling.

---

## 7. Minimal consumer recipe

```python
import json
feed = json.load(open("portfolio-feed.json"))
# 1. validate the manifest (reject if invalid)
res = hca_feed.validate_manifest(feed["manifest"])
assert res["ok"], res["errors"]
# 2. honor refusals (treat as absent; fail if required)
for r in feed["dataset"]["refusals"]:
    handle_missing(r["figure"], r["reason_code"])
# 3. ingest delivered rows, tracing + confidence-gating each
for row in feed["dataset"]["rows"]:
    if row["pii_redacted"]:            # value omitted (per-record); use field-name only
        continue
    if (row["confidence"] or 0) < MY_FLOOR:
        continue
    value, ok = cache.resolve_binding(row["provenance"])   # re-resolve to Tier-1
    assert ok and value == row["value"]                    # trust only what resolves
    ingest(row["label"], row["value"], row["unit"], row["currency"])
```

This contract is what `demos/demo3-downstream-feed.md` exercises against a real downstream
skill (e.g. `acos-dataroom-v2`) — **without modifying the consumer's internals** (consumption
is via this documented contract only).
