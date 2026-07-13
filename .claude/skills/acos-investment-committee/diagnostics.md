# Diagnostics — acos-investment-committee (SLICE-DIAG-01)

**Purpose (§0.3 Diagnostic Protocol — problem before solution).** This is the
diagnostic slice: it captures the symptoms of the current problem BEFORE any expert
seat logic exists, so every downstream requirement can be traced to a diagnosed
cause. Mirrors `planning/preeng/003-investment-committee/spec.md` §Diagnostics.

## Symptoms → owning requirement

| # | Symptom | Affected role | Current behavior | Desired behavior | Owning requirement(s) |
|---|---------|---------------|-------------------|-------------------|------------------------|
| D1 | Single-analyst review structurally misses discipline-specific holes (legal, valuation, environmental, concentration, fraud) | OKOA associate/analyst (IC chair) | One person reads the whole deal; blind spots go unchecked | A fixed panel of complementary disciplines each interrogates its own risk category; a gap-hunter chases risks nobody claimed | **FR-M1** (numbered, stable 8-seat core roster) |
| D2 | LLM/analyst reviews are sycophantic and drift toward rubber-stamping the deal framing | Deal team, decision-makers | Reviewer agrees with the packaged narrative (~58% sycophancy baseline; 63.7% agreement with an asserted incorrect belief) | Independence-first blind opening pass; mandatory falsifiable objection per seat; evidence-only (derived, not self-reported) confidence | **FR-M3** (independence-first isolated opening) + **FR-M4** (mandatory falsifiable objection) |
| D3 | No structured way to separate deal-breakers from mitigable risks, each with a mitigant + residual-risk statement | IC chair, decision-makers | Findings are a bare list; "mitigated" with no residual; deal-breakers buried among minor items | Every non-fatal finding carries a named mitigant + explicit residual risk + CP cross-ref; deal-breakers derived by a deterministic rule and surfaced first | **FR-M8** (risk triplet: risk→mitigant→residual) + **FR-M7** (deterministic verdict / deal-breaker rule) |
| D4 | No way to run an adversarial, human-participated deliberation like a real IC | IC chair | Reviews are static documents; no live challenge / interjection | Mode B moderated relay with chair command vocabulary, stance-tagged turns, human injection as a first-class turn | **FR-M9–FR-M14** (Mode B moderator loop, transcript, round structure, human injection, deterministic tally) + **FR-M22** (one-to-one toggle) |
| D5 | Two risks are nobody's job by default: fund-level concentration and financial-statement fraud | Portfolio manager, decision-makers | Each reviewer reads only the deal folder → concentration gets a silent PASS; T-12 veracity is unowned across seats | A fund-scoped Portfolio & Concentration seat (#7) with loan-tape access; an explicit adversarial Sponsor & Fraud-Forensics mandate (#6, "assume fabricated until externally corroborated") | **FR-M17** (concentration ownership) + **FR-M18** (fraud ownership) |
| D6 | Verdicts are narrated by an LLM and can be fabricated (a confident PROCEED / DECLINE with no auditable basis) | Decision-makers | The recommendation is prose an LLM wrote; consensus is treated as correctness | Verdict computed deterministically from the ledger via `resolve.py` polarity (asymmetric-veto on deal-breakers); UNRESOLVED is a first-class output | **FR-M7** (deterministic verdict) + **FR-M6** (vendored axiom-synthesis engine, standalone) |

## Validation pointer

Where a diagnosis is incomplete, the derived requirement is marked `Assumption` in
`spec.md` and carries a validation story (see `spec.md` §Hypotheses & unknowns: H1–H3,
U1–U3). This slice (SLICE-DIAG-01 / Wave 0) does not itself validate D1–D6 against
live deliberation outcomes — it establishes the traceability from symptom to
requirement and stands up the mechanical substrate (vendored synthesis engine +
session scaffold) that later waves use to implement the desired behavior. Live
validation of the desired-behavior column happens once seat agents exist (Wave 1+,
`SLICE-A1`–`SLICE-A3`, `SLICE-B*`).

## Cross-reference

Full requirement text: `planning/preeng/003-investment-committee/spec.md` §4.1
(Functional Requirements, MoSCoW). Component → requirement traceability:
`planning/preeng/003-investment-committee/tech_prd.md` §5.
