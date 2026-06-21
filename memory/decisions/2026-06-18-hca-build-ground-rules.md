# Decision: acos-hypercore-ask Build Ground Rules + Diagnostic Record

**Date:** 2026-06-18
**Decision Maker:** human (confirmed) + developer (proposed)
**Status:** accepted
**Supersedes:** N/A
**Slice:** SLICE-HCA-00-diagnostic (Demo 0)
**Related (proposed):** VISION-HCA-01 / EPIC-HCA-00 / STORY-HCA-00
**Source of truth:** `planning/preeng/001-hypercore-ask/spec.md` §Diagnostics, `plan.md` §2
(Plan-time decisions), `tech_prd.md` §5

> Problem-before-solution gate (Protocol 0.3). This record locks the build ground
> rules and confirms the trust-failure diagnosis BEFORE any solution code is written.
> It contains NO solution code. All symptoms / hypotheses / unknowns below are
> re-derived faithfully from `spec.md` §Diagnostics — no new claims are invented.

---

## 1. Diagnostic record

### 1.1 Symptoms (what is going wrong today) — S1–S4

- **S1 — Direct querying is slow / technical / error-prone.** Staff who need a
  loan-portfolio answer must query Hypercore (UI or API) directly; slow, requires
  technical skill, mistake-prone.
- **S2 — AI answers are untrustworthy.** Ad-hoc AI querying produces fabrication,
  **stale data**, **silent pagination cutoffs**, and **aggregation errors** — unusable
  for IC-grade work.
- **S3 — No canonical verified feed.** Other ACOS skills need clean, verified loan
  data, but no provenance-backed source feed exists; each consumer re-pulls and
  re-validates ad hoc.
- **S4 — No repeatable question→report path.** Turning a question into a verified
  report/table requires bespoke scripting every time.

### 1.2 Affected roles / personas

- **OKOA associate / staff** — asks portfolio questions; needs fast, defensible answers.
- **OKOA Investment Committee (IC)** — consumes IC-grade deliverables; will not review
  intermediate artifacts; final output must be boss-criticism-proof on first cold look.
- **Downstream ACOS skills** — acos-dataroom-v2, acos-financial-statement, prospectus
  pipeline, legal-analyst — consume verified extracts as trusted inputs.

### 1.3 Current vs. desired behavior

| Dimension | Current | Desired |
|---|---|---|
| Answer trust | Possibly fabricated/stale/truncated | Every value provenance-bound + consensus-verified, or refused |
| Speed | Slow manual pull | Materially faster time-to-verified-answer |
| Completeness | Silent pagination truncation | Pagination-completeness gate; no silent truncation |
| Freshness | Unknown staleness | Stated freshness window; never serve stale silently |
| Aggregation | Unverified math | Cross-field reconciliation + adversarial recomputation |
| Reusability | Bespoke scripts | One skill; standard verified-extract feed formats |
| Failure mode | Guess/fabricate | Refuse + explicit "no live data" / "cannot provenance-bind" |

### 1.4 Hypotheses — H1–H3

- **H1** — The dominant trust failure is not raw fabrication but *aggregation / units /
  currency / truncation* errors that look plausible. → reconciliation + completeness
  gates + adversarial recompute are higher-leverage than text-similarity checks.
- **H2** — A two-tier data model (raw cached truth + normalized derived view) is
  sufficient to guarantee provenance without ballooning token cost. (Internal prior
  LEARN-ARCH-002; high confidence.)
- **H3** — A 2-of-3 asymmetric quorum of blind agents catches substance disagreement
  on reports/aggregations at acceptable cost. (`Assumption`, reused from
  acos-dataroom-v2 / grader; finalize quorum N at plan time.)

### 1.5 Unknowns — U1–U5

- **U1** — Exact Hypercore read endpoints, request/response schemas, auth model,
  pagination scheme, webhook event contract (partner-gated; **UNVERIFIED until access**).
- **U2** — Secret/credential provisioning mechanism (env vs dedicated secret store).
- **U3** — Concrete freshness-window length (configurable; value TBD at plan time).
- **U4** — Final consensus quorum N per verification tier.
- **U5** — Final scripting language decision (defaulted Python 3 stdlib; confirm at plan time).

---

## 2. H1 status (confirmed vs Assumption)

**Status: CONFIRMED (for gate-priority purposes), with a residual-magnitude validation
hook routed to SLICE-HCA-11-completeness-hardening.**

**Rationale.** H1 asserts that the dominant *trust* failure is plausible-looking
aggregation / units / currency / silent-truncation error, not raw text fabrication.
The spec's own symptom S2 enumerates the failure modes as "fabrication, **stale data**,
**silent pagination cutoffs**, and **aggregation errors**" — three of the four named
failure modes (stale, truncation, aggregation) are exactly the H1 class, and all three
are *invisible to a text-similarity check* because the prose reads fluently while the
number is wrong. The desired-state table independently prescribes the H1 mitigations
(pagination-completeness gate, freshness window, cross-field reconciliation, adversarial
recomputation) as the trust controls — i.e., the spec's own remediation design already
weights the H1 class above text checks. This is sufficient to **confirm the gate
*ordering*** (reconciliation/completeness/freshness/normalization outrank text-similarity).

**What remains Assumption (routed, not resolved here):** the *relative magnitude* of each
failure mode in live OKOA traffic is unmeasured (we have no production error-rate sample,
because the live API is not yet provisioned — U1). H1's *ranking* is confirmed from the
spec; H1's *quantitative weighting beyond the mandatory gate set* stays `Assumption` and
is validated against real captured responses in **SLICE-HCA-11-completeness-hardening**
(the validation hook). This matches `plan.md` §5: "Until H1 is confirmed, gate weighting
beyond the mandatory set is marked `Assumption` and validated in [the hardening slice]."

No new claim is invented: every symptom/hypothesis/unknown above is a faithful restatement
of `spec.md` §Diagnostics.

---

## 3. Gate-priority recommendation (ranked, derived from H1)

Given H1 (plausible-looking aggregation/units/currency/truncation errors dominate),
the highest-leverage gates, ranked:

1. **Pagination-completeness gate** — fetched count / cursor exhaustion must reconcile
   with `reported_total`; else refuse. (Directly kills silent truncation — S2.)
2. **Cross-field reconciliation** — related fields must agree (drawdowns + repayments vs
   outstanding; sum-of-parts vs reported total). (Kills aggregation error — S2.)
3. **Unit/currency normalization** — normalize before any compare/aggregate. (Removes the
   units/currency error class that makes wrong totals look right.)
4. **Freshness window** — Tier-1 `timestamp` within the per-entity-class window; never
   serve stale silently. (Kills the stale-data failure — S2.)
5. **Schema validation + drift detection** — source record conforms to expected schema;
   drift surfaced not absorbed. (Guards the inputs the above gates rely on.)
6. **Single-source confidence cap (≤ 0.7)** — single-source figures flagged + capped.
   (Calibrates trust where consensus is unavailable.)

**Lower-leverage by comparison (still present, just not top of the trust budget):**
text-similarity / prose-style checks — H1 says these catch the *least* of the actual
trust failures, so they do not lead the gate suite.

Adversarial multi-model consensus (blind N agents, 2-of-3 quorum) sits *above* the
deterministic gates for report/aggregation/analysis tier, catching substance
disagreement the deterministic gates cannot express. This ranking is consistent with H1.

---

## 4. Locked build ground rules (the Decision)

These are LOCKED for the entire `acos-hypercore-ask` feature (all 12 slices):

1. **Python 3 stdlib only — no third-party dependencies.** (Resolves OQ5 / U5.)
   Rationale: consistency with existing ACOS scripts; offline-buildable; no supply-chain
   surface; tests run with zero install. *Decision.*

2. **Stubbed-client-until-access.** No live Hypercore API call is made until access is
   provisioned. All live calls live ONLY inside `LiveBackend` behind the adapter contract;
   `LiveBackend` raises the documented `NotImplementedError("Hypercore live backend
   TODO — access not yet provisioned")` until wired. `FixtureBackend` is the active backend
   and serves canned `RawApiResponse` records from `fixtures/`. (Resolves OQ1 / U1 posture;
   real endpoints/schemas/auth remain `TBD`.) *Decision.*

3. **Read-only, structurally enforced.** The adapter contract exposes read methods only
   (`is_live`, `get_entity`, `list_entities`, `get_schema`, `subscribe_events`). NO mutating
   verb (create/update/delete/post/put/patch/write/mutate) exists on the contract. Enforced
   by omission AND by a guard test that introspects the contract and rejects any mutating
   method name.

4. **Graceful degradation, never fabricate.** When `is_live() == false` and live data is
   requested, the surface returns an explicit `NO_LIVE_DATA` envelope / raises
   `NoLiveDataError` — never a fabricated record, never a crash.

5. **Secrets via env / secret store only — none in repo.** Credentials are read from
   environment variables at runtime (Doppler injects them via `doppler run`; project
   `acos-3-0`, config `dev`). Default env var names `HYPERCORE_API_KEY` and
   `HYPERCORE_BASE_URL`, names configurable via skill config. No key/URL is ever hardcoded
   or committed. (Resolves OQ2 / U2 posture; exact secret store finalized at provisioning.)

6. **Subscription-only Claude.** Model work is done via main-thread Read or `Task()`
   (`general-purpose` blind agents). **Never `ANTHROPIC_API_KEY`.** No external model calls.

7. **Consensus quorum default 2-of-3 asymmetric, configurable per tier.** Trivial lookups
   may run deterministic-gates-only; reports/aggregations require ≥ 2-of-3. (Resolves OQ4 /
   U4 default; configurable.)

8. **Freshness windows configurable per entity class.** Conservative defaults in
   `tech_prd.md` §5 are `Assumption`; never serve stale silently. (Resolves OQ3 / U3.)

9. **Live read-only calls authorized by the user** once access is provisioned — but only
   through the unchanged read-only contract; the swap is fixtures→`LiveBackend`, no contract
   change.

10. **Build cadence:** all 12 slices built autonomously per the vertical-slice plan; this
    foundation work delivers only slices 00 (diagnostic), 01 (scaffold), 02 (adapter).

---

## 5. Traceability

- Symptoms S1–S4, current-vs-desired, H1–H3, U1–U5 — faithful restatement of
  `spec.md` §Diagnostics (lines 28–81).
- OQ5 (Python 3 stdlib), OQ1 (stubbed-until-access), OQ4 (quorum), OQ3 (freshness),
  OQ2 (secrets) — `plan.md` §2 Plan-time decisions + `spec.md` §Open Questions.
- Read-only contract surface + degradation + fixtures strategy — `tech_prd.md` §2, §8.
- Config defaults (`consensus`, `freshness_windows_days`, `confidence.single_source_cap`,
  `adapter.backend`) — `tech_prd.md` §5.

## 6. No-PII attestation

This record contains no borrower PII, no credentials, no real loan numbers — only the
diagnostic abstractions from the spec and the locked ground rules.
