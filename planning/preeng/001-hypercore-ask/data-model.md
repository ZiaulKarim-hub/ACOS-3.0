# Data Model — acos-hypercore-ask

> Output of `/preeng.plan` (companion to `plan.md`, `tech_prd.md`). Models **both** halves:
> (A) the Hypercore **read entities** (subject domain) and (B) the skill's **internal artifacts**
> (verification domain). The two-tier boundary is explicit: **Tier-1 `RawApiResponse` = source of
> truth (full provenance); Tier-2 normalized layer = derived view.** All Hypercore field-level
> schemas are `TBD`/`Assumption` pending partner-gated access and live **only** behind the adapter
> contract; the field lists below are the **likely/expected** modeling target used to build fixtures
> and schema validators now.

## 0. Tiering & provenance principle

- **Tier 1 (truth):** raw API JSON exactly as returned, wrapped in `RawApiResponse`. Immutable.
  **All provenance points here.**
- **Tier 2 (derived):** `NormalizedAnswerRecord` and the typed subject entities below are
  *projections* of Tier 1. Every Tier-2 field carries a `json_field_path` + `raw_response_id` back to
  its Tier-1 source. **A Tier-2 value with no resolvable Tier-1 binding cannot be delivered (refuse).**
- **Read-only:** no entity has create/update/delete semantics against Hypercore.

---

## A. Hypercore read entities (subject domain — fields `TBD`/`Assumption` until access)

> These are modeled as Tier-2 typed projections over Tier-1 raw responses. Field names are expected/
> likely and serve fixtures + schema validators; real fields are confirmed once API docs arrive.

### A1. Loan / Facility
- `loan_id` (PK), `facility_type` {term, revolver, mezzanine, **bridge**, **construction**,
  syndicated, hybrid}, `borrower_id` (FK→Borrower), `commitment_amount`, `funded_amount`,
  `outstanding_principal`, `currency`, `interest_rate`/`rate_type`, `origination_date`,
  `maturity_date`, `status`, `collateral_ids` (FK→Collateral[]).
- Relationships: 1—N Drawdown, Payment, Fee, InterestAccrual; 1—1 AmortizationSchedule; N—M
  Covenant, Collateral, InvestorAllocation; N—M Document.

### A2. Borrower / Entity
- `borrower_id` (PK), `legal_name`, `entity_type`, `jurisdiction`, `relationship_manager`,
  `contact` (PII — minimized in derived view), `loan_ids` (FK→Loan[]).

### A3. Drawdown / Funding
- `drawdown_id` (PK), `loan_id` (FK), `amount`, `currency`, `funding_date`, `status`.

### A4. Payment / Repayment
- `payment_id` (PK), `loan_id` (FK), `amount`, `currency`, `payment_date`, `allocation`
  {principal, interest, fees}, `status`.

### A5. Fee
- `fee_id` (PK), `loan_id` (FK), `fee_type` {origination, exit, extension, ...}, `amount`,
  `currency`, `assessed_date`, `paid` (bool).

### A6. Interest Accrual
- `accrual_id` (PK), `loan_id` (FK), `period_start`, `period_end`, `accrued_amount`, `currency`,
  `rate_applied`, `day_count_convention`.

### A7. Amortization Schedule
- `schedule_id` (PK), `loan_id` (FK), `entries[]` {`period`, `due_date`, `principal_due`,
  `interest_due`, `balance_after`}, `currency`.

### A8. Covenant / Compliance Check
- `covenant_id` (PK), `loan_id` (FK), `covenant_type`, `threshold`, `measured_value`, `as_of_date`,
  `status` {in_compliance, breach, waived}.

### A9. Collateral
- `collateral_id` (PK), `loan_ids` (FK[]), `collateral_type`, `description`, `appraised_value`,
  `currency`, `as_of_date`, `lien_position`.

### A10. Investor Allocation
- `allocation_id` (PK), `loan_id` (FK), `investor_id`, `allocation_amount`/`allocation_pct`,
  `currency`, `as_of_date`.

### A11. Document
- `document_id` (PK), `loan_id` (FK), `doc_type`, `repository_ref`, `created_date`, `metadata`.

---

## B. Skill-internal artifacts (verification domain)

### B1. RawApiResponse  — **Tier-1 source of truth**
| Field | Type | Notes |
|---|---|---|
| `raw_response_id` | string (PK) | Stable key for provenance lookup |
| `endpoint` | string | Hypercore read endpoint called (`TBD` real value) |
| `request_params` | object | Exact request params/filters/cursor |
| `timestamp` | datetime | When fetched (drives freshness) |
| `http_status` | int | Response status |
| `cursor` | string/null | Pagination cursor returned |
| `reported_total` | int/null | Server-reported total (for completeness gate) |
| `body` | object | **Exact raw JSON** (immutable) |
| `backend` | enum | `fixture` \| `live` (labels fixture vs live data) |

### B2. NormalizedAnswerRecord — **Tier-2 derived view**
| Field | Type | Notes |
|---|---|---|
| `record_id` | string (PK) | |
| `entity_type` | enum | Loan, Borrower, ... |
| `fields` | object | Typed, unit/currency-normalized projection |
| `field_bindings` | map<field, {raw_response_id, json_field_path}> | Back-pointer to Tier-1 for each field |
| `derived_from` | string[] | `raw_response_id`s contributing |

### B3. ProvenanceBinding  — **universal; refuse-on-missing**
| Field | Type | Notes |
|---|---|---|
| `binding_id` | string (PK) | |
| `value_ref` | string | The delivered value it cites |
| `endpoint` | string | From the source RawApiResponse |
| `request_params` | object | From the source RawApiResponse |
| `timestamp` | datetime | From the source RawApiResponse |
| `json_field_path` | string | Exact path into the raw body (e.g. `$.data[3].outstanding_principal`) |
| `raw_response_id` | string (FK→RawApiResponse) | Resolves to Tier-1 truth |
| `contributing` | string[] | For aggregates: all source bindings |

> Invariant: **every delivered value has ≥1 resolvable ProvenanceBinding, else it is refused.**

### B4. ConsensusResult
| Field | Type | Notes |
|---|---|---|
| `consensus_id` | string (PK) | |
| `question_ref` | string | The NL question / value sought |
| `tier` | enum | trivial-lookup \| report/aggregation/analysis |
| `agent_extractions` | array | Per blind agent: `{agent_id, value, json_field_path, raw_response_id, agent_confidence}` |
| `quorum` | string | e.g. `2-of-3` |
| `agreement_status` | enum | consensus \| disagreement \| escalated |
| `redispatch_count` | int | Bounded retries used |
| `agreed_value` | any/null | Null unless quorum reached |

### B5. VerificationGateResult
| Field | Type | Notes |
|---|---|---|
| `gate_result_id` | string (PK) | |
| `value_ref` | string | |
| `schema_ok` | bool | Schema validation |
| `pagination_complete` | bool | Count/cursor reconciliation (no silent truncation) |
| `freshness_ok` | bool | Within configured window |
| `reconciliation_ok` | bool | Cross-field reconciliation |
| `normalization_applied` | bool | Unit/currency normalized |
| `confidence_capped` | bool | Single-source cap ≤0.7 applied |
| `outcome` | enum | pass \| refuse |
| `failures` | string[] | Which gate(s) failed |

### B6. ConfidenceRecord
| Field | Type | Notes |
|---|---|---|
| `confidence_id` | string (PK) | |
| `value_ref` | string | |
| `confidence` | float [0,1] | |
| `single_source` | bool | If true, confidence forced ≤0.7 |
| `basis` | string | What drives the score (consensus agreement, source count, freshness) |

### B7. SchemaDescriptor (expected schema + drift)
| Field | Type | Notes |
|---|---|---|
| `entity_type` | enum | |
| `expected_fields` | object | Expected field→type map (fixtures-based now) |
| `version` | string | Schema version |
| `drift_detected` | bool | Set when observed shape diverges from expected |
| `drift_details` | string[] | Surfaced, not absorbed |

### B8. EvidenceBundle (per slice)
| Field | Type | Notes |
|---|---|---|
| `slice_id` | string (PK) | |
| `summary` / `traceability` / `quality` / `testing` / `security` / `operational` / `self_assessment` | sections | 7-part bundle (Protocol 0.1) |
| `consensus_refs` / `gate_refs` / `provenance_refs` | string[] | Links to B3–B6 (PII-scrubbed) |
| `path` | string | `.acos/evidence/[DATE]/[SLICE-ID]/` |

### B9. AnswerEnvelope / FeedRecord (delivery)
| Field | Type | Notes |
|---|---|---|
| `value(s)` | any | Delivered value(s) |
| `provenance` | ProvenanceBinding[] | Mandatory citations |
| `confidence` | ConfidenceRecord | |
| `freshness_stamp` | datetime | |
| `tier` | enum | |
| `state` | enum | delivered \| refused \| escalated \| no_live_data |
| `manifest` (feed only) | object | source pointers, freshness, schema version, completeness proof |

---

## C. Key relationships & invariants

- `RawApiResponse (Tier-1)` —derives→ `NormalizedAnswerRecord (Tier-2)` —cites→ `ProvenanceBinding`
  —resolves to→ `RawApiResponse`. (Provenance always closes back to Tier-1 truth.)
- `ConsensusResult` + `VerificationGateResult` + `ConfidenceRecord` gate a value before it can enter
  an `AnswerEnvelope`/`FeedRecord`.
- **Invariants:**
  1. No delivered value without a resolvable `ProvenanceBinding` → else `refused`.
  2. Reports/aggregations require `ConsensusResult.agreement_status == consensus` (≥ quorum).
  3. Lists/aggregates require `VerificationGateResult.pagination_complete == true`.
  4. Stale (`freshness_ok == false`) → never delivered silently.
  5. Single-source values → `ConfidenceRecord.confidence ≤ 0.7`, flagged.
  6. Adapter exposes read methods only; no entity has Hypercore-mutating operations.
  7. When adapter `is_live() == false` and live data requested → `state == no_live_data` (no fabrication).

## D. Persistence & PII notes

- Tier-1 cache persisted at rest with AES-256 (honor posture); least-privilege access.
- Logs/evidence bundles **PII-scrubbed** (borrower PII / financials redacted to need-to-know).
- Agents receive **minimal Tier-1 slices**, never the full cache (token + PII minimization).
- Secrets read from env/secret store at runtime; never persisted in repo or in any of these records.

## E. Open / TBD (carried)

- All Hypercore field-level schemas (A1–A11) are expected/`Assumption` until access (OQ1).
- Real `endpoint` values, auth scheme, and pagination cursor semantics are `TBD` (OQ1).
- Concrete freshness-window values per entity class are configurable (OQ3).
