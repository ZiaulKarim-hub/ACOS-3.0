# Research Dossier — acos-hypercore-ask

> Output of `/preeng.research`. Offline structuring of pre-seeded research (no external fetch).
> Companion artifacts: `domain-brief.md`, `domain-cqs.md`, `domain-lattice.json`,
> `evidence-ledger.json`, `research_qa_report.json`. Evidence tiers per Protocol 0.4; lattice per
> §2.3; ledger per §2.4. Hypercore API specifics are **UNVERIFIED until partner-gated access** and
> are marked `TBD`/`Assumption`.

## 0. Method & precondition

- **Precondition:** `spec.md` exists ✓ (written by `/preeng.specify`).
- **4-phase Constitutional Domain Compilation (Protocol 0.2):**
  1. **DLG** — `domain-brief.md` + 15 competency questions (`domain-cqs.md`).
  2. **Lattice expansion** — `domain-lattice.json` (94 typed nodes, 119 typed edges, controlled
     vocab; 2-hop subgraphs per CQ connecting problem → method → metric/standard and risk → control).
  3. **Evidence ledger** — `evidence-ledger.json` (16 entries, T1–T5 tiers, confidence, freshness,
     source_refs, lattice_node_ids).
  4. **Agent emission** — these artifacts plus the validation note (§6) feed plan/tasks/instructions.
- **Coverage result (machine-verified):** CQ coverage **100% (15/15)** with **0 critical structural
  violations** and **0 orphan nodes** (each CQ reaches a method, a metric/standard, and a risk within
  2 hops). Exceeds the ≥95% target.

## 1. Subject domain — Hypercore loan-management platform (T3, UNVERIFIED until access)

Hypercore (hypercore.ai) is loan-management software for private credit / direct lending covering
origination → underwriting → servicing → amendments/restructurings → repayment. It reportedly
supports term, revolver, mezzanine, **bridge**, **construction**, syndicated, and hybrid facilities
(OKOA does bridge + construction lending). It exposes a REST API plus real-time webhook events and
integrates with Salesforce, NetSuite, and document repositories; it automates fee/interest
calculation, amortization schedules, funding/drawdowns, and compliance checks with real-time
reporting and audit-ready controls. (EV-001, EV-002.)

**Read entities to model (likely set; field-level schema `TBD`):** loans/facilities, borrowers/
entities, drawdowns/fundings, payments/repayments, fees, interest accruals, amortization schedules,
covenants/compliance, collateral, investor allocations, documents. (EV-003.)

**Critical caveat:** exact endpoints, request/response schemas, auth model, pagination scheme, and
webhook contract are **partner-gated and not in hand**. Everything API-specific is an `Assumption`/
`TBD` and is **stubbed behind the client/adapter contract**; the design proceeds against
fixtures/mocks (EV-002, EV-011). This is the single largest source of residual uncertainty and is
explicitly accepted, not hidden.

## 2. Security & compliance posture (T3 vendor / T1 OKOA discipline)

Hypercore posture: TLS 1.2+ (transit), AES-256 (rest), RBAC, SOC 2 Type II, GDPR, MFA + SSO
(EV-012). OKOA-side hard rules: borrower PII/financials must not leak into logs/evidence beyond
need; secrets via env/secret store with no credentials in repo (EV-012); read-only against Hypercore
(EV-015, T1); subscription-only Claude — never `ANTHROPIC_API_KEY` (EV-016, T1).

## 3. Verification domain — the distinguishing feature (T2 internal priors)

This is why the skill exists; it must not be diluted.

- **Provenance-binding (universal).** Every delivered value cites its exact raw cached API response
  (endpoint + request params + timestamp + JSON field path). No citation → refuse, never guess.
  Grounded in the ACOS `pre-generation-verification-gate` LEARN (EV-004) and OKOA provenance
  discipline. Lattice: `meth-prov`, `ent-provbind`, `pat-refuse`, `proc-bind`.
- **Adversarial multi-model consensus.** N blind independent extraction/answer agents run with no
  shared context; a result is delivered only on **substance** consensus (agreement on the normalized
  value substance — exact numbers/names/dates). Disagreement → blind re-dispatch, then escalate;
  never a silent pick. Reused from acos-dataroom-v2 / acos-financial-statement / acos-grader
  (EV-005). Default quorum **2-of-3 asymmetric** (`Assumption`; finalize per tier at plan time).
  Lattice: `meth-consensus`, `ent-consensus`, `term-substance`, `pat-blindredispatch`,
  `anti-singletrust`.
- **Deterministic gate suite (layered underneath consensus).** schema validation (EV-008),
  pagination-completeness (EV-007), freshness window (EV-006), cross-field reconciliation (EV-009),
  unit/currency normalization (EV-009), single-source confidence cap ≤ 0.7 (EV-004). Lattice:
  `proc-gate` and the `meth-*` gate nodes; outcomes captured in `ent-gateresult`.
- **Tiered verification routing.** Deterministic-gates-only suffices for trivial lookups; full
  adversarial consensus is mandatory for reports/aggregations/analysis that feed other tasks;
  provenance-binding is universal across tiers (EV-004, EV-005). Lattice: `meth-tiered`, `term-tier`.
- **Two-tier data model (LEARN-ARCH-002).** Raw cached API responses = source of truth (full
  provenance); normalized answer layer = token-efficient derived view; each agent gets only the tier
  it needs (EV-010). Lattice: `meth-twotier`, `ent-rawresp`, `ent-normrec`, `proc-cache`.
- **Stubbed-client-until-access + graceful degradation.** Contract-first adapter isolation with a
  fixture/mock backend; absent credentials the skill emits an explicit "no live data" state rather
  than fabricate (EV-011). Lattice: `meth-adapter`, `meth-degrade`, `pat-fixturefirst`,
  `term-nolivedata`.

## 4. Competency-question findings (offline answers)

Full answer sketches live in `domain-cqs.md`. Summary of resolution status:

| CQ | Status | Notes |
|---|---|---|
| CQ-01 (API surface) | `TBD`/`Assumption` | Partner-gated; modeled behind adapter contract + fixtures |
| CQ-02 (entity/field map) | Partial + `TBD` | Entity set known (likely); field map pending schema |
| CQ-03 (provenance binding) | Resolved (design) | `ProvenanceBinding`→`RawApiResponse`; refuse-on-missing |
| CQ-04 (consensus/quorum) | Resolved w/ `Assumption` | Substance consensus; 2-of-3 asymmetric default per tier |
| CQ-05 (confidence cap ≤0.7) | Resolved (design) | `ConfidenceRecord`; flagged in answer envelope |
| CQ-06 (freshness) | Resolved w/ `TBD` | Window length TBD; webhook→polling fallback |
| CQ-07 (pagination completeness) | Resolved (design) | Count/cursor reconciliation gate; mechanism `TBD` on real pagination |
| CQ-08 (schema drift) | Resolved (design) | Validate + drift-detect; surface not absorb |
| CQ-09 (aggregation/unit/currency) | Resolved (design) | Reconciliation + normalization + adversarial recompute |
| CQ-10 (stubbed adapter) | Resolved (design) | Contract-first; fixtures backend; live backend later |
| CQ-11 (no-live-data) | Resolved (design) | Explicit state; never fabricate |
| CQ-12 (PII/GDPR/RBAC) | Resolved (design) | Scrubbed logs/evidence; env secrets; honor posture |
| CQ-13 (downstream feeds) | Resolved w/ `Assumption` | report+table+dataset+manifest; refine per consumer |
| CQ-14 (two-tier boundary) | Resolved (design) | Raw truth vs normalized derived |
| CQ-15 (tiered routing) | Resolved (design) | Deterministic-only vs full-consensus |

## 5. Evidence ledger summary

16 entries (`evidence-ledger.json`). Tier distribution:
- **T1 (Authoritative):** EV-015 (read-only), EV-016 (subscription-only) — hard permanent constraints.
- **T2 (Expert / validated internal priors):** EV-004, EV-005, EV-007, EV-008, EV-009, EV-010,
  EV-011, EV-013, EV-014 — the verification architecture is built on these.
- **T3 (Empirical / vendor-public, UNVERIFIED):** EV-001, EV-002, EV-003, EV-006, EV-012 — all
  Hypercore-platform specifics; marked UNVERIFIED until access.
- **T4 / T5:** none required (no community-tool or internal-only-experiment claims relied upon).

Every entry records confidence, freshness_days, source_refs, and `lattice_node_ids`. Lowest-confidence
entries (EV-002 0.40, EV-001/EV-003 0.5–0.6) are exactly the partner-gated API specifics, correctly
flagged and quarantined behind the adapter.

## 6. Validation note (coverage + evidence quality)

- **CQ coverage:** 100% (15/15), machine-verified; ≥95% target met.
- **Structural integrity:** 0 critical violations, 0 dangling edges, 0 duplicate ids, 0 orphan nodes;
  controlled-vocabulary node types and edge relations only; all 10 node types present.
- **Evidence quality:** verification-architecture claims rest on T1/T2 internal priors (high
  confidence). All Hypercore platform/API specifics are T3 and explicitly UNVERIFIED/`TBD` pending
  access — the dominant residual risk, openly accepted and isolated behind the stubbed adapter.
- **Distinguishing feature preserved:** provenance-binding + adversarial consensus + deterministic
  gates + two-tier model + stubbed-adapter degradation are all first-class in brief, CQs, lattice,
  and ledger.
- **Assumptions register:** quorum N (2-of-3 start), Python 3 stdlib, freshness-window length,
  feed-format set, and secret-store mechanism are all flagged for confirmation at plan time.

## 7. Open items carried to plan

- Finalize consensus quorum N per verification tier (OQ4).
- Confirm Python 3 stdlib scripting decision (OQ5).
- Set concrete freshness-window length (OQ3).
- Confirm secret/credential provisioning mechanism (OQ2).
- All Hypercore API specifics remain `TBD` until access (OQ1) — design proceeds on fixtures.
