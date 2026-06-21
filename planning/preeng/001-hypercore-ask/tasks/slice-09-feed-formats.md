# slice-09-feed-formats — Downstream trusted-input feed formats + provenance/confidence display (Demo 3)

- **Parent story:** STORY-HCA-08 · **Parent epic:** EPIC-HCA-08 · **Demo:** Demo 3
- **Effort:** M · **Dependency order:** 10 · **Depends on:** slice-08-orchestration
- **Lattice refs:** proc-feed, meth-feedfmt, ent-bundle, std-icgrade, cq-13

## PM Section (Planner / Specifier — LCE)

### Objective
Render verified deliverables in **report / table / dataset (JSON/CSV)** formats and a **trusted-input feed schema** with embedded per-value provenance + confidence + a **manifest** (source-of-truth pointers, freshness, schema version, completeness proof), and demonstrate a downstream skill consuming it as a trusted input. This is **Demo 3**.

### Scope
**In scope:** feed renderers (JSON + CSV) emitting per-value provenance/confidence; the manifest schema + generator; a documented consumer contract; a Demo 3 walkthrough where a downstream skill (e.g. `acos-dataroom-v2`) ingests the dataset.
**Out of scope:** modifying downstream consumer skills' internals (only demonstrate consumption via the documented contract); security hardening (slice-10); live API.

### Guardrails / Allowed files
- `.claude/scripts/hca-feed.py` (report/table/dataset JSON+CSV renderers + manifest generator; stdlib only — `json`, `csv`)
- `.claude/skills/acos-hypercore-ask/schemas/feed-manifest.schema.json` (manifest schema)
- `.claude/skills/acos-hypercore-ask/feed-contract.md` (consumer contract doc)
- `.claude/skills/acos-hypercore-ask/demos/demo3-downstream-feed.md` (Demo 3 walkthrough)
- this task file + `.acos/evidence/[DATE]/slice-09-feed-formats/`
- Prohibited: emitting any feed value without provenance/confidence; emitting a feed without a completeness proof in the manifest; PII leakage into the feed beyond need.

### Definition of Done
- [ ] Dataset export in JSON and CSV where **every value row carries its provenance + confidence** — pass-condition: feed-render test; sample row independently resolves to Tier-1.
- [ ] Manifest generated and schema-valid: includes source-of-truth pointers, freshness, schema version, and a **completeness proof** (pagination-complete evidence) — pass-condition: manifest validates against `feed-manifest.schema.json` (REQUIRED).
- [ ] A downstream consumer ingests the feed via the documented contract and accepts it as a trusted input (Demo 3) — pass-condition: Demo 3 walkthrough reproducible.
- [ ] CSV is well-formed (stdlib `csv`, quoted, no field corruption) and round-trips with the JSON — pass-condition: round-trip test.
- [ ] Feed is PII-minimized (no borrower PII beyond need) — pass-condition: PII-scan of sample feed.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. `hca-feed.py`: render JSON + CSV from the report-tier output, embedding provenance/confidence per value.
2. Generate the manifest (source pointers, freshness, schema version, completeness proof) and validate it.
3. Author `feed-contract.md` (how consumers read provenance/confidence/manifest).
4. Demo 3: produce a verified collateral dataset (UC4) and show acos-dataroom-v2 consuming it via the contract.
5. Tests: feed-render, manifest-validate, round-trip, PII-scan.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (Sh1 feed formats, M9 provenance/confidence, std-icgrade, cq-13); Code Quality (stdlib json/csv); Functional (4 tests + Demo 3 transcript); Security (PII-minimized feed); Operational; Self-assessment.

### Dev Learnings
- `hca-feed.py` is a PURE serializer of an already-verified report envelope — it fetches
  nothing, makes no model call, and never mutates Tier-1. It uses stdlib `json` + `csv` only
  (ground rule). The renderers (`render_dataset`/`render_json`, `render_csv`, `render_feed`) all
  derive from the same per-figure projection helpers (`_figure_provenance`,
  `_figure_completeness`, `_figure_freshness`, `_figure_gate_summary`), so JSON / CSV / manifest
  stay consistent by construction.
- The CSV column order IS the round-trip contract: `render_csv` writes `CSV_COLUMNS` and
  `parse_csv` reads it back. Used `csv.DictWriter` with `QUOTE_MINIMAL` + `\r\n` terminator
  (RFC-4180-ish) so an embedded comma/quote/newline in a label never corrupts a field; a
  three-state `_csv_tribool` distinguishes True/False/unknown for nullable gate booleans.
- Wrote a SMALL stdlib JSON-Schema validator (`_validate` covering type/required/properties/
  items/enum) rather than taking a `jsonschema` dependency — the manifest schema only needs that
  subset, and stdlib-only is a hard ground rule. `validate_manifest` ALSO enforces the
  real-completeness-proof rule beyond pure structure: every figure's `pagination_complete` must
  be the actual gate boolean (or null), never a placeholder string.
- PII safety is enforced at two layers: (1) `_figure_is_pii_safe` classifies a figure as
  portfolio-level (aggregate or a `reported_total` count) vs per-record; in `pii_safe` mode a
  per-record figure's VALUE is redacted to None + flagged `pii_redacted`, keeping only the
  label/field-name/provenance pointer (pointers + field-names are not PII). (2) `write_artifact`
  refuses (PermissionError) to write a non-pii-safe artifact anywhere except the git-ignored
  `.acos/state/` runtime area — using `os.path.commonpath` to tell the tracked tree from the
  runtime dir.
- Refused figures are surfaced verbatim into BOTH `dataset.refusals` and `manifest.refusals` and
  are NEVER a dataset row — the feed cannot fabricate a value for a figure the report refused,
  and the manifest still validates with a refusal present.
- LIVE-VERIFIED 2026-06-18: the portfolio-summary report rendered to JSON + CSV + a trusted FEED
  whose manifest is schema-valid with per-figure provenance (141 contributing bindings on the
  aggregate) + a REAL completeness proof; JSON↔CSV round-trips clean; a PII scan of the written
  artifacts found no borrower-level values.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Take a sample feed row; independently resolve its provenance to a Tier-1 record and confirm the value + confidence.
2. Validate the manifest against `feed-manifest.schema.json`; confirm the completeness proof is real (matches the pagination-completeness gate result), not a placeholder.
3. Run the Demo 3 consumption; confirm the downstream skill reads provenance/confidence correctly.
4. Round-trip JSON<->CSV; confirm no data corruption.
5. Scan the feed for borrower PII beyond need.

### Evidence gates (all must pass)
- [ ] **Every feed value has resolvable provenance + confidence** — fail = REJECT.
- [ ] **Manifest schema-valid with a real completeness proof** — fail = REJECT (hard).
- [ ] Demo 3 downstream consumption reproducible.
- [ ] JSON/CSV round-trip clean.
- [ ] No PII beyond need.
- [ ] Learnings updated.

### QA Learnings
- A sample feed row's provenance independently resolves: `test_feed_row_provenance_resolves_to_tier1`
  takes a rendered row and re-resolves `row["provenance"]` to a Tier-1 value via
  `cache.resolve_binding`, confirming `value == row["value"]` — every feed value is traceable,
  not asserted.
- Manifest validity is a HARD gate: `validate_manifest` checks structure against
  `feed-manifest.schema.json` AND that `completeness.pagination_complete` is the real gate
  boolean. The count figure's `pagination_complete` is asserted True to match its gate verdict
  (the proof is real, not a placeholder).
- JSON↔CSV round-trip is checked field-by-field including the provenance pointers; a label with
  an embedded comma is shown to survive (stdlib csv quoting), proving no field corruption.
- PII: per-record figure values are redacted to None in pii_safe mode (both JSON and CSV), while
  portfolio aggregates/counts are NOT redacted; `write_artifact` is proven to refuse a
  non-pii-safe artifact into the tracked tree (PermissionError, file not created) and to allow it
  only under `.acos/state/`.
