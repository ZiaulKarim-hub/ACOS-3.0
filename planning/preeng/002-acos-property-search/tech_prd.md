# Technical PRD — acos-property-search

> Output of `/preeng.plan`. Technical contract for the skill. Stdlib-only Python, no external infra,
> free-sources-only, explicit-invocation-only. Numerics are configurable defaults (Assumption per D6/D7/D8).

## 1. Component inventory

| Component | File (planned) | Responsibility | Slice |
|---|---|---|---|
| Skill methodology | `.claude/skills/acos-property-search/SKILL.md` | Orchestration narrative; invokes scripts + swarm | 01/07/11 |
| Compliance gate | `references/compliance.md` + `SKILL.md` gate logic | Blocking permissible-purpose record; GLBA hard block | 01 |
| Cache | `scripts/cache.py` | JSON cache w/ freshness TTLs wrapping every lookup | 02 |
| Normalize/classify | `scripts/normalize.py` | Person vs. entity; alias/variant; fuzzy match | 03 |
| Graph engine | `scripts/graph.py` | Temporal/provenance edges + hub pruning | 04 |
| ArcGIS query | `scripts/arcgis_query.py` | Query parcel layers by OWNER or MAIL_ADDR | 05 |
| Swarm dispatch | `scripts/swarm_dispatch.py` | Build channel×jurisdiction×entity agent matrix per round | 06 |
| Round synthesizer | `scripts/synthesize_round.py` | Cross-ref, confidence, conflict-flag, hub-prune, next seeds | 06 |
| Scoring | `scripts/score.py` | Rubric + tiers + review flags | 09 |
| Dedup | `scripts/dedup.py` | APN canonicalization + per-owner aggregation | 08 |
| Rollup | `scripts/rollup.py` | Assessed value + recorded mortgage → estimated equity | 10 |
| Reference data | `references/*.md`, `hub_agents.txt` | Sources catalog, state matrix, hub stop-list, review flags | 01/04/05 |
| Report | `SKILL.md` render section | Markdown dossier (v1) | 11 |

## 2. Compliance gate (BLOCKING — runs first, every time)

- **Pre-condition for all downstream work.** Until a `ComplianceRecord` is captured, the run state is
  `COMPLIANCE_BLOCKED` and no external lookup is permitted.
- **Record (per `references/compliance.md`):** permissible purpose mapped to statute (DPPA §2721(b)(3)
  debt recovery / (b)(4) judgment enforcement; FCRA §1681b(a)(3)(A) for any credit pull; dossier flagged
  "asset location / debt recovery — NOT for eligibility"); debt classification (consumer vs. commercial →
  FDCPA scope); GLBA anti-pretexting acknowledgment (HARD BLOCK — no financial info by misrepresentation);
  scraping posture (official feeds/record APIs preferred, public no-login pages only, respect robots/rate
  limits, per-datum provenance).
- **Hard block:** any attempt to obtain bank/financial info by misrepresentation is refused outright.
- **Human-in-the-loop:** the gate is an approval pause; counsel sign-off noted as out-of-scope (not legal
  advice).

## 3. Entity graph contract

- **Nodes:** `{name, person, entity, address, agent, phone, email, parcel, loan, lien, deed, court-case,
  ucc}` (string `node_type` + `node_id` + attributes).
- **Edge schema (every edge, hard requirement):**
  `{from, to, edge_type, source, source_url, confidence, date_first_seen, date_last_verified,
  effective_date, expiration_date, raw_evidence}`.
- **Edge types:** `OWNS, MANAGES, MEMBER_OF, OFFICER_OF, REGISTERED_AGENT_OF, TRUSTEE_OF, TAX_BILLED_TO,
  MAILS_TO, REGISTERED_AT, LIVED_AT, SOLD_TO, BORROWER_ON, GUARANTOR_OF, SPOUSE_OF, ASSOCIATE_OF,
  RELATED_TO`.
- **Edge strength (strongest→noisiest):** shared officer/member > shared mailing/principal address >
  shared phone > shared email/domain > shared filing batch/organizer > shared registered agent
  (only if non-commercial).
- **Hub-guard (precision):** registered-agent stop-list (`hub_agents.txt`); dynamic hub detection at a
  frequency threshold (default **25**); bounded hops (default **2 degrees**); inverse-frequency weighting;
  **log every prune**. Inverse signal kept: a non-commercial agent on a few related entities is a strong
  control link. CMRA / virtual-office / UPS-Store addresses flagged.

## 4. Discovery channels (v1 = 1–4 + recorder full)

1. **Assessor owner-name search** — free states (FL/TX/AZ/NV) + statewide (MD/MA/MT).
2. **Recorder grantor-grantee name index** — highest-yield; name-blocked-state workaround.
3. **Mailing-address pivot** — ArcGIS REST `MAIL_ADDR LIKE` / bulk-roll group-by; FL statewide cadastral.
4. **Entity graph** — SoS + OpenCorporates: person→officer/agent→entities→parcels.
- **Phased (v2/v3):** 5 lien/judgment (+UCC fixtures), 6 bankruptcy A/B+SOFA, 7 court records,
  8 people-search (leads only — used in identity resolution v1), 9 concealment piercing.

## 5. Swarm + between-rounds synthesizer

- **Decomposition axis:** channel × jurisdiction × entity (not research lenses).
- **Per round:** `swarm_dispatch.py` builds the agent matrix from the current worklist; each agent runs
  **blind** (isolated; no shared context) and writes `workspace/<session-id>/round-NN/agent-NN/findings.md`.
- **Dispatch:** subscription-only via `Task()` / main-thread `Read` (no API key).
- **Between rounds (`synthesize_round.py`):** cross-reference → confidence (**Verified = 2+ independent
  isolated agents**); **preserve conflicts** → manual-review flags (never silently harmonize); **hub-prune
  + enforce hop limit** (holds the stop-list + hop counter); emit newly discovered seeds → next worklist.
- **Stop condition:** a round yields no new high-confidence nodes.

## 6. Scoring, dedup, rollup (deterministic, stdlib, unit-tested)

- **`score.py`** — merged rubric (+40/+25/+25/+20/+10/+10-per-corroboration cap+20; −40/−30/−20/−10/−10;
  cap ≤40 through a hub) → score + signals; tiers **≥75 high / 50–74 candidate / <50 weak**; emits review
  flags from the taxonomy. Pure function; deterministic given identical inputs.
- **`dedup.py`** — canonicalize APN; aggregate per owner; merge duplicate parcels across channels.
- **`rollup.py`** — assessed value (flag "assessed, not market") + last sale + original recorded mortgage −
  stated amortization assumption → **estimated** equity; "no mortgage data found" flag; never fabricate
  AVM/payoff. Every figure labeled "estimated."

## 7. Caching, freshness, resilience

- **`cache.py`** — JSON cache keyed by person/entity/address/parcel/query; freshness TTLs (corporate
  ~30 d, property ~30–60 d, deed/transfer faster — configurable). Absorbs rate limits + 403 blocks; makes
  re-runs cheap and resumable. Per-record freshness stamps surface in the report.

## 8. Configuration (skill config; no secrets)

```yaml
# planned skill config (values configurable; no secrets here)
confidence_tiers: { high: 75, candidate: 50 }   # D6 default
hub_frequency_threshold: 25                       # D7 default
hop_limit: 2                                       # D8 default
corroboration_bonus_per_source: 10
corroboration_bonus_cap: 20
cache_ttl_days: { corporate: 30, property: 45, deed: 7 }
channels_enabled_v1: [assessor_owner, recorder_index, mailing_pivot, entity_graph]
swarm: { min_agents: 5, max_agents: 20, dispatch: task }   # subscription-only
hedged_language: required
compliance_gate: blocking
sources_only: free
```

- **No `ANTHROPIC_API_KEY`** (subscription-only, Assumption A5). No paid-API credentials anywhere.

## 9. Security & compliance (technical)

- **Free-sources-only, public no-login pages only**; respect robots/rate limits; per-datum provenance.
- **GLBA anti-pretexting hard block** in the gate.
- **PII discipline:** DOB/age only as a disambiguation anchor, subject to the gate; people-search results
  are leads-only and corroborated before scoring; the audit trail records source + URL, not unnecessary
  PII.
- **Read-only against the world** — the skill never writes to any external system; it only reads public
  records and queries free APIs.

## 10. Orchestration / durability / observability

- **Executor:** `/acos-execute-slice`. **Durability:** cache + per-round audit artifacts → resume after
  interruption from the last completed round. **HITL:** blocking compliance gate + manual-review flags.
  **Observability:** per-agent `findings.md`, per-round `synthesis/`, logged prunes, freshness stamps,
  `.acos/metrics/agent-completions.log`.

## 11. Open technical items (carried)

- Per-portal availability / 403-block behavior (volatile) — probed in slice-11 dry run.
- Exact ArcGIS layer URLs per county/state — maintained in `references/sources.md`.
- False-positive rate at the 75/50 cutoffs — measured in slice-11; cutoffs tunable.
- v2 wiring of `acos-loan-doc-generator-with-visual-verification` render + `/schedule` monitoring.
