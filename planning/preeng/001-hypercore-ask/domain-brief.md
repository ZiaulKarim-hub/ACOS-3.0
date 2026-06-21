# Domain Brief — acos-hypercore-ask

> Phase 1 of the Constitutional Domain Compilation Pipeline (Protocol 0.2 / DLG).
> Offline structuring of pre-seeded research only. Hypercore API specifics are **UNVERIFIED
> until partner-gated access** and are tagged `TBD`/`Assumption`. Evidence tiers per entry are in
> `evidence-ledger.json`; lattice in `domain-lattice.json`; CQs in `domain-cqs.md`.

## Domain framing

The domain has two coupled halves:

1. **The subject domain** — private-credit / direct-lending loan management as exposed by the
   **Hypercore platform** (hypercore.ai): origination → underwriting → servicing → amendments /
   restructurings → repayment, across facility types OKOA uses (bridge + construction; plus term,
   revolver, mezzanine, syndicated, hybrid). This is what the skill *reads about*.
2. **The verification domain** — the discipline that makes AI-delivered data trustworthy:
   provenance-binding, adversarial multi-model consensus, deterministic data-quality gates, a
   two-tier data model, and graceful degradation behind an isolated client/adapter. This is the
   skill's *distinguishing feature* and the reason it exists.

The product is an ACOS skill that mediates between the two: it answers natural-language questions
about Hypercore loan data and **only delivers values it can provenance-bind and verify**, otherwise
it refuses.

## Entities

**Subject-domain (Hypercore read) entities** (likely set; field-level schema `TBD` pending API docs):
- Loan / Facility (term, revolver, mezzanine, bridge, construction, syndicated, hybrid)
- Borrower / Entity
- Drawdown / Funding
- Payment / Repayment
- Fee
- Interest Accrual
- Amortization Schedule
- Covenant / Compliance Check
- Collateral
- Investor Allocation
- Document

**Skill-internal (verification) entities:**
- RawApiResponse (Tier-1 source-of-truth cached raw API JSON)
- ProvenanceBinding (value → endpoint + request params + timestamp + JSON field path)
- ConsensusResult (per-agent blind extractions + quorum/threshold + agreement status)
- VerificationGateResult (schema / pagination / freshness / reconciliation / normalization / confidence-cap outcomes)
- ConfidenceRecord (per-value confidence + single-source flag ≤ 0.7)
- NormalizedAnswerRecord (Tier-2 derived view)
- EvidenceBundle (per-slice evidence aggregate)

## Processes
- NL question intake → verification-tier routing (trivial lookup vs. report/aggregation/analysis).
- Read-only data acquisition through the stubbed client/adapter (live calls TODO; fixtures now).
- Raw-response caching (write to Tier-1 truth store; keyed for provenance lookup).
- Blind multi-agent extraction (independent agents, no shared context).
- Consensus evaluation (substance agreement; quorum; re-dispatch / escalate on disagreement).
- Deterministic gating (schema, pagination-completeness, freshness, cross-field reconciliation,
  unit/currency normalization, single-source confidence capping).
- Provenance-binding (refuse-on-missing-citation).
- Delivery / refusal / no-live-data degradation.
- Downstream feed emission (verified extract → trusted-input format + manifest).
- Schema-drift detection; webhook/polling cache invalidation.

## Methods / patterns
- Contract-first client/adapter isolation with a fixture/mock backend (build/test pre-access).
- Two-tier data model (LEARN-ARCH-002): raw cached truth + normalized derived view.
- Pre-generation verification gate (non-bypassable, between extraction and delivery).
- Adversarial multi-model consensus (blind agents + asymmetric/quorum gating).
- Provenance discipline (exact numeric/name/date preservation; per-field citation).
- Tiered verification routing (deterministic-only vs. full-consensus).
- Subscription-only model dispatch (Read / `Task()`; no API key).
- Graceful degradation ("no live data" vs. fabrication).

## Anti-patterns (to avoid)
- Silent pagination truncation (delivering a partial list as if complete).
- Serving stale data silently (no freshness check).
- Single-model "trust me" extraction (no consensus, no provenance).
- Fabricating a value when provenance is missing (guess instead of refuse).
- Leaking borrower PII / financials into logs/evidence beyond need.
- Hard-coupling the skill to a guessed API surface (no adapter).
- Using `ANTHROPIC_API_KEY` / separate API billing.
- Any write/mutate against Hypercore.

## Standards / regulations / posture
- Hypercore security posture: TLS 1.2+ (transit), AES-256 (rest), RBAC, SOC 2 Type II, GDPR,
  MFA + SSO.
- GDPR data-protection discipline for borrower PII / financials.
- OKOA standing rules: subscription-only Claude (no API key); IC-grade / boss-criticism-proof
  deliverables; provenance + confidence on every figure.
- ACOS conventions: skills + Python 3 stdlib scripts + general-purpose agents; evidence bundles;
  Independence Wall; `/acos-execute-slice` orchestration.

## Metrics
- Fabrication rate (0% target); provenance coverage (100% target); consensus pass / disagreement /
  escalation counts; pagination-completeness %; freshness-within-window %; single-source
  confidence-cap correctness; refusal rate (health signal); time-to-verified-answer.

## Risks
- Unknown API surface; stale data; silent pagination/rate-limit truncation; schema drift;
  aggregation/unit/currency errors; PII/GDPR leakage; user over-trust; consensus instability/cost;
  fabrication when no provenance.

## Key terms
- Provenance-binding; adversarial multi-model consensus; deterministic gate; verification tier;
  two-tier data model; raw-response cache; substance consensus; single-source confidence cap;
  graceful degradation / "no live data"; client/adapter contract; pagination-completeness;
  freshness window; schema drift; cross-field reconciliation; unit/currency normalization.

## Coverage note
This brief, the CQ list (`domain-cqs.md`), the lattice (`domain-lattice.json`), and the evidence
ledger (`evidence-ledger.json`) jointly satisfy the 4-phase pipeline. CQ coverage is computed in
`research.md` and the QA report; target ≥ 95% with no critical structural violations.
