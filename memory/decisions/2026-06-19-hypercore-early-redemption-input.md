# Decision: Known-good early-redemption (payoff) input for `getLoanRepaymentDistribution`

**Date:** 2026-06-19
**Decision Maker:** human (confirmed) + developer (proposed)
**Status:** accepted
**Supersedes:** N/A
**Slice:** SLICE-HCA-12 / SLICE-HCA-13 (payoff / early-redemption figure)
**Related:** `memory/decisions/2026-06-18-hca-build-ground-rules.md`
**Source of truth:** `.claude/skills/acos-hypercore-ask/SKILL.md` (Ask → Payoff / early-redemption intent),
`.claude/scripts/hca-figures.py`, `.claude/scripts/hca-resolve.py`

> This record documents the empirically determined, live-verified input shape and
> resolution path for the payoff / early-redemption figure. It records ONLY what the
> skill already documents and live-verified on 2026-06-19; no new claims are invented.

---

## Context

The payoff / early-redemption figure (`payoff_as_of`) answers questions of the form
"what is the payoff for `<loan>` as of `<date>`" by calling the Hypercore GraphQL
query `getLoanRepaymentDistribution(input:…)` — a read-preview Query, NOT a mutation.

Two facts about the live Hypercore API forced the resolution path and the exact input
shape:

1. **The resolver is input-shape-sensitive.** A minimal input, or an input that merely
   sets `isPrepayment:true`, CRASHES the resolver with **HTTP 500**. Only the EXACT
   known-good input (the full field set the resolver expects) returns a valid
   distribution. The known-good shape is carried verbatim in `hca-figures.py`; this
   record exists so the shape's provenance and constraints are not lost.

2. **The single-loan and transaction-preview resolvers are FLAKY.** The single-loan
   resolver `loan(id)` and the transaction-PREVIEW resolvers return **intermittent
   HTTP 500s** — they are unreliable for production resolution.

## Decision

- **Loan resolution rides the RELIABLE list query, not `loan(id)`.** Fuzzy loan-name
  resolution (`hca-resolve.py`) fetches real loans via
  `loans(filter:{searchString:"…"})` and scores client-side. The flaky `loan(id)`
  resolver is not used on the resolution path. Candidates always come from real API
  rows; an ambiguous / low-confidence match DISAMBIGUATES (returns the candidate list,
  never a silent pick).

- **The payoff figure uses the EXACT known-good input.** `hca-figures.py` calls
  `getLoanRepaymentDistribution(input:…)` with the full known-good input shape. It does
  NOT send a minimal input and does NOT set `isPrepayment:true` (either crashes the
  resolver with HTTP 500).

- **Retry up to 3× on the intermittent 500.** Because the underlying transport is
  flaky, the call retries up to three times on an intermittent HTTP 500 before giving
  up; a persistent failure surfaces as a structured refusal, never a fabricated number.

- **Component reconciliation to $0.01.** The figure provenance-binds the returned
  `total` to a cached Tier-1 record and RECONCILES the components —
  `principal + indexedPrincipal + interest + compoundingInterest +
  accruedCompoundingInterest + totalFees + totalPenalties + totalTaxes == total`
  within **$0.01** — REFUSING if it does not reconcile. Currency is taken from
  `loan.currency`. Default date is today (UTC); an explicit "as of `<date>`" is honored.

## Rationale

- **Reliability over the obvious resolver.** The obvious single-record path
  (`loan(id)`) is unreliable on the live API; the list query is reliable and yields the
  same loan with real, citable rows. Choosing reliability keeps the trust-first contract
  intact (no silent failures, no fabricated fallbacks).

- **The exact input avoids a known 500.** Pinning the full known-good input is the only
  shape that does not crash the resolver; a minimal / prepayment-flag input is a known
  HTTP-500 trigger, so it is structurally avoided.

- **Reconciliation is the trust gate.** Binding `total` to Tier-1 and re-summing the
  components to the cent is what makes the delivered payoff defensible — a value that
  cannot reconcile is refused, never served.

## Consequences

- The payoff figure is **live-verified**: loan **134 "Beehive Waldorff"**, as-of
  **2026-06-30**, returns **total 31,888,682.99** which reconciles to the cent.

- The resolution path is coupled to the reliable list query
  `loans(filter:{searchString})` and to `getLoanRepaymentDistribution`. If Hypercore
  later stabilizes `loan(id)` / the preview resolvers, this decision can be revisited;
  until then those resolvers are intentionally not on the resolution path.

- The exact known-good input shape is load-bearing. Any future change to it must be
  re-verified live (the minimal / `isPrepayment:true` HTTP-500 behavior is a standing
  hazard), and the retry-on-500 plus $0.01 reconciliation gates must remain.

- An intermittent 500 that survives 3 retries, or a non-reconciling distribution, yields
  a structured refusal (the failing condition is named) — consistent with the skill's
  never-fabricate guardrail.
