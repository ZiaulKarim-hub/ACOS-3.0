# Demo 3 — Downstream trusted-input feed (SLICE-HCA-09)

A **verified** `acos-hypercore-ask` report is exported as a downstream **trusted-input feed**:
the data PLUS a **manifest** that lets another ACOS skill (e.g. `acos-dataroom-v2`) consume the
figures as trusted inputs **and trace every one** back to a cached Tier-1 raw API response.

Renderer: `.claude/scripts/hca-feed.py`. Consumer contract: `feed-contract.md`. Manifest
schema: `schemas/feed-manifest.schema.json`.

## What slice-08 hands slice-09

Slice-08 (`hca-deliver.build_report`) produces a report envelope where **each figure carries
its own** `{value, unit/currency, provenance, gate_verdict, confidence, complete}`. Slice-09
serializes that into three formats — **every emitted value keeps its provenance + confidence**,
and **refused figures are surfaced, never dropped**.

```
report envelope (slice-08)
  -> render_dataset / render_json   JSON dataset: per-value provenance + confidence + completeness
  -> render_csv                     CSV table:    one row per figure, round-trips with the JSON
  -> render_feed                    trusted FEED: {manifest, dataset}  (manifest = trust header)
```

## Run it

```bash
# Assemble a portfolio-summary report (live, read-only, under Doppler) and pipe it to the feed
# renderer. PII-safe by default: aggregates / counts / field-names only for tracked artifacts.
doppler run --project hypercore-ask --config dev_personal -- python3 - <<'PY' > /tmp/report.json
# ...build_report("OKOA Portfolio Summary", [loan_count, client_count, total_commitment])
# ...print(json.dumps(report))     (see demo-report-pipeline.md for the build snippet)
PY

# Render to each format:
python3 .claude/scripts/hca-feed.py --format json --in /tmp/report.json     # JSON dataset
python3 .claude/scripts/hca-feed.py --format csv  --in /tmp/report.json     # CSV table
python3 .claude/scripts/hca-feed.py --format feed --in /tmp/report.json --validate  # FEED + manifest
```

`--out <path>` writes the artifact (the PII guard refuses a non-PII-safe artifact into the
tracked tree). `--allow-pii` disables PII-safe mode (per-record values; runtime area only).

## Live-verified feed (2026-06-18 — aggregates only, NO PII)

From the live portfolio-summary report (`loan_count=141`, `client_count=124`,
`total_commitment=434,989,118.78 USD`):

### Manifest (trust header) — schema-valid, real completeness proof

```
MANIFEST schema-valid: True   errors: []
manifest.state: DELIVERED   delivered: 3   refused: 0
  loan_count:       conf=0.7 src=1   prov=$.body.reported_total  complete=True pagination_complete=True gate=pass
  client_count:     conf=0.7 src=1   prov=$.body.reported_total  complete=True pagination_complete=True gate=pass
  total_commitment: conf=1.0 src=141 prov=aggregate x141         complete=True pagination_complete=True gate=pass
```

- **Per-figure provenance:** the counts cite `$.body.reported_total`; the aggregate carries
  **141 contributing source pointers** (`raw_response_id` + `json_field_path` per source).
- **Completeness proof is REAL:** `pagination_complete` is the actual pagination-completeness
  gate boolean (mirrored in each figure's `gate_verdict`), not a placeholder.
- **Confidence:** single-source counts capped at `0.7`; the 141-source aggregate at `1.0`.

### CSV table — well-formed, round-trips with the JSON dataset

```
label,value,unit,currency,confidence,raw_response_id,json_field_path,aggregate,source_count,complete,pagination_complete,freshness_ok,gate_outcome,tier,pii_redacted
loan_count,141,,,0.7,live:list:loan:2026-06-18T23:10:44Z,$.body.reported_total,false,1,true,true,true,pass,report,false
client_count,124,,,0.7,live:list:client:2026-06-18T23:10:47Z,$.body.reported_total,false,1,true,true,true,pass,report,false
total_commitment,434989118.78,USD,USD,1.0,live:list:loan:2026-06-18T23:10:49Z,,true,141,true,true,true,pass,report,false
```

`parse_csv(render_csv(report))` reproduces the JSON dataset rows exactly — **round-trip
clean** (a label with an embedded comma is quoted and survives, per
`test_hca_report_feed.FeedRenderTest.test_csv_quotes_embedded_commas_no_corruption`).

## A downstream skill consumes it (via the documented contract only)

`acos-dataroom-v2` (or any ACOS skill) ingests the feed **without any change to its internals**
— consumption is purely via `feed-contract.md`:

```python
import json
feed = json.load(open("portfolio-feed.json"))

# 1) Validate the manifest — reject the feed if it does not validate.
res = hca_feed.validate_manifest(feed["manifest"])
assert res["ok"], res["errors"]

# 2) Honor refusals — a refused figure is absent data, never a guess.
for r in feed["dataset"]["refusals"]:
    flag_missing(r["figure"], r["reason_code"], r.get("failed_gates"))

# 3) Ingest delivered rows; trace + confidence-gate each.
for row in feed["dataset"]["rows"]:
    if row["pii_redacted"]:                       # per-record value omitted -> field-name only
        continue
    if (row["confidence"] or 0) < MY_FLOOR:        # honor confidence
        continue
    value, ok = cache.resolve_binding(row["provenance"])   # re-resolve to Tier-1
    assert ok and value == row["value"]            # trust only what resolves
    dataroom.ingest_verified(row["label"], row["value"], row["unit"], row["currency"])
```

The consumer reads **only** the documented surface (`manifest`, `dataset.rows`,
`dataset.refusals`) — it never reaches into `hca-*` internals. Each ingested figure is
independently re-resolved to its Tier-1 source, so the downstream skill trusts **only what it
can trace**.

## Refused figures surface in the feed (consumer MUST honor)

If a figure refuses (e.g. a truncated list fails `pagination_completeness`), it is **NOT** a
dataset row (no fabricated value) — it appears in `dataset.refusals` **and**
`manifest.refusals`, naming the figure + the failing gate. The manifest still validates with a
refusal present. The contract requires the consumer to treat it as absent data and fail/flag if
the figure is required (`feed-contract.md` §5). Proven by
`test_hca_report_feed.FeedRefusalSurfacingTest`.

## PII safety

- **PII-safe by default.** A per-record (per-borrower) figure's value is **redacted to `null`**
  and flagged `pii_redacted: true`; only its label / field-name / provenance pointer /
  confidence survive. Aggregate / count (portfolio-level) figures emit their values normally.
  Proven by `test_hca_report_feed.PiiSafetyTest`.
- `hca-feed.write_artifact(...)` **refuses** to write a non-PII-safe artifact into the tracked
  tree (raises `PermissionError`); per-record output goes **only** to the git-ignored runtime
  area (`.acos/state/`). The live demo artifacts written to evidence are aggregates only — a
  PII scan of them found **no** borrower-level values.

## Tests

`.claude/scripts/tests/test_hca_report_feed.py` (stdlib `unittest`, fixtures only, no network):
JSON dataset + CSV + feed render with per-value provenance/confidence; manifest schema-valid
with a real completeness proof; a sample feed row's provenance resolves into Tier-1; JSON↔CSV
round-trip clean; refused figure surfaces (not a row); PII-safe redaction + the write guard.

```bash
python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py'
```
