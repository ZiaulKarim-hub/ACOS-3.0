# Data Model — acos-property-search

> Output of `/preeng.plan`. Stdlib-only, JSON-on-disk (no DB). All records are produced from FREE public
> sources; every attribution carries provenance; every estimated figure is labeled. Field sets marked
> `Assumption` are PLAN.md-derived and refined at build time.

## 0. Principles

- **Provenance-first:** every edge and every parcel attribution carries `{source, source_url,
  date_first_seen, date_last_verified}`; no figure without a source.
- **Time-variant ownership:** edges carry `effective_date` / `expiration_date` — an ownership claim needs
  an "as of."
- **Estimates labeled:** every value/equity figure is explicitly "estimated"; AVM/payoff never fabricated.
- **Conflicts preserved:** conflicting owner names produce a `ReviewFlag`, never a silent merge.

## A. Graph nodes (subject domain — `node_type` + attributes)

### A1. Name / Person
- `node_id`, `full_name`, `aliases[]`, `maiden`, `suffix` (Jr/Sr/III), `dob_or_age?` (anchor only,
  gate-bound), `prior_addresses[]`, `phones[]`, `emails[]`, `relatives[]`, `associates[]`,
  `provenance{}`. *(People-search-sourced fields are leads-only until corroborated.)*

### A2. Entity (LLC / corp / trust)
- `node_id`, `legal_name`, `entity_type`, `state`, `status` (active/dissolved), `officers[]`, `members[]`,
  `registered_agent`, `principal_address`, `mailing_address`, `dba[]`, `provenance{}`.

### A3. Address
- `node_id`, `normalized_addr`, `is_mailing`, `is_principal`, `is_situs`, `is_cmra_or_virtual` (flag),
  `frequency` (for hub detection), `provenance{}`.

### A4. Agent (registered agent)
- `node_id`, `name`, `is_commercial_hub` (stop-list or ≥ threshold), `frequency`, `provenance{}`.

### A5. Phone / A6. Email
- `node_id`, `value`, `frequency`, `provenance{}`.

### A7. Parcel
- `node_id` = **APN** (canonical), `county`, `state`, `situs`, `owner_of_record`, `mailing_address`,
  `assessed_value?`, `last_sale_price?`, `last_sale_date?`, `legal_description?`, `provenance{}`,
  `freshness{roll_updated_days_ago}`.

### A8. Loan / Deed / Lien / UCC / Court-case
- **Loan/Deed:** `node_id`, `instrument_type`, `recorded_date`, `original_amount?`, `borrower`,
  `guarantor?`, `signatories[]`, `vesting_clause?`, `apn?`, `provenance{}`.
- **Lien:** `node_id`, `lien_type` (judgment/mechanics/tax/lis-pendens), `debtor`, `apn?`, `provenance{}`.
- **UCC:** `node_id`, `debtor_name`, `secured_party`, `collateral`, `is_fixture`, `provenance{}`.
- **Court-case:** `node_id`, `case_type` (divorce/probate/foreclosure/bankruptcy), `parties[]`,
  `property_refs[]`, `provenance{}`.

## B. Graph edge — **the universal contract**

```json
{
  "from": "node_id", "to": "node_id",
  "edge_type": "OWNS | MANAGES | MEMBER_OF | OFFICER_OF | REGISTERED_AGENT_OF | TRUSTEE_OF | TAX_BILLED_TO | MAILS_TO | REGISTERED_AT | LIVED_AT | SOLD_TO | BORROWER_ON | GUARANTOR_OF | SPOUSE_OF | ASSOCIATE_OF | RELATED_TO",
  "strength_rank": 0,
  "source": "string", "source_url": "string",
  "confidence": 0.0,
  "date_first_seen": "ISO8601", "date_last_verified": "ISO8601",
  "effective_date": "ISO8601 | null", "expiration_date": "ISO8601 | null",
  "raw_evidence": "string"
}
```
**Invariant:** an edge missing `source`/`source_url`/`date_last_verified` is not persisted. `strength_rank`
follows the edge-strength ordering; hub edges are pruned (and logged), not persisted as control links.

## C. Skill-internal records (method domain)

### C1. ComplianceRecord — **per run, blocking precondition**
- `permissible_purpose`, `statute_refs[]` (DPPA (b)(3)/(b)(4), FCRA §1681b), `dossier_flag`
  ("asset location — NOT for eligibility"), `debt_class` (consumer/commercial → FDCPA scope),
  `glba_ack` (hard-block acknowledgment), `scraping_posture`, `recorded_by`, `recorded_at`.
- **Invariant:** run state stays `COMPLIANCE_BLOCKED` until this record is complete and valid.

### C2. Seed
- `seed_id`, `kind` (name/address/entity/person), `value`, `anchors[]`, `round_introduced`,
  `parent_seed?`, `hop_distance`.

### C3. ChannelAgentRun
- `run_id`, `round`, `channel`, `jurisdiction`, `entity_or_seed`, `findings_path`
  (`workspace/<sid>/round-NN/agent-NN/findings.md`), `started_at`, `completed_at`, `isolated: true`.

### C4. RoundSynthesis
- `round`, `corroborated_nodes[]` (≥2 independent sources), `conflicts[]` (→ ReviewFlags),
  `pruned[]` (hub/hop-limit prunes, **logged**), `next_seeds[]`, `new_high_confidence_count`
  (loop-stop signal when 0).

### C5. ConfidenceRecord (per parcel attribution)
- `apn`, `score` (rubric sum), `signals[]` (each +/− with reason), `tier` (high/candidate/weak),
  `independent_source_count`, `capped_through_hub: bool`.

### C6. ReviewFlag
- `apn?`, `node_id?`, `flag` (common-name | registered-agent-only | inactive-dissolved |
  recently-transferred | mailing-law-firm/virtual/CMRA | trust-ownership | no-mortgage-data |
  conflicting-owner-names | data>90d), `detail`, `source_refs[]`.

### C7. EquityRollup (per parcel)
- `apn`, `assessed_value?` (flag "assessed, not market"), `last_sale{price,date}?`,
  `original_mortgage{amount,date}?`, `amortization_assumption`, `estimated_remaining_balance?`,
  `estimated_equity?`, `flags[]` (e.g., "no mortgage data found"), `all_figures_estimated: true`.

### C8. CacheEntry
- `key` (person/entity/address/parcel/query), `fetched_at`, `ttl_days`, `is_stale` (derived),
  `status` (ok/403/rate-limited), `payload`, `source_url`.

### C9. AuditArtifact
- `workspace/<session-id>/round-NN/agent-NN/findings.md` (per-agent), `workspace/<session-id>/round-NN/
  synthesis/` (per-round), pruned-node log. Forms the resumable, auditable trail.

### C10. ReportV1 (Markdown)
- `compliance_header` (from ComplianceRecord) → `high_confidence_tier[]` → `candidate_tier[]` →
  per-parcel `{apn, county/state, situs, owner_of_record, mailing, matched_through (evidence chain),
  confidence + signals, freshness, source_urls}` → `estimated_portfolio{value, debt, equity}` →
  `coverage_and_limits{counties_searched, hops_reached, hubs_pruned}` → `review_flags[]`. Hedged language
  throughout.

## D. Key relationships & invariants

- A **Parcel** is attributed to a subject only through an evidence chain of edges; the chain is recorded
  in `ConfidenceRecord.signals` and rendered as `matched_through`.
- **Verified** requires `independent_source_count >= 2` from **isolated** agents.
- An attribution whose only graph link runs through a **hub** node is capped at score ≤ 40 (candidate at
  best) and carries `capped_through_hub: true`.
- **Dedup** is on canonical **APN**; cross-channel duplicates merge, unioning provenance + freshness.
- **No external lookup** occurs while `COMPLIANCE_BLOCKED`.
- Every estimated figure has `all_figures_estimated: true`; AVM/payoff is never fabricated.

## E. Open / TBD (carried)

- Exact county/state field names in assessor/recorder/ArcGIS payloads (`Assumption`; mapped per source in
  `references/sources.md`).
- Amortization-assumption model for estimated remaining balance (`Assumption`; stated openly as an
  estimate).
- v2 entities for channels 5–9 at depth + monitoring deltas.
