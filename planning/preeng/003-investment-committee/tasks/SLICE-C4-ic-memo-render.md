# SLICE-C4-ic-memo-render — 13-section IC memo render (Risk->Mitigant->Residual + CP)

**Parent story:** STORY-C2 · **Epic:** EPIC-C · **Effort:** M · **Demo:** Demo 1 (short) -> Demo 2 (full 13-section)
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Render `recommendation.md` **from the ledger** (never
hand-edited) in the 13-section IC canon, with a BLUF verdict box and the repeating
**Risk -> Mitigant -> Residual** triplet table where every Condition Precedent is tagged to the
risk it retires. For Demo 1, a short 3-seat memo; for Demo 2, the full 13 sections.

**In-scope:** `render_memo.py` — read `verdict.md` + `ledger/`; emit the 13 sections (BLUF ->
Exec Summary -> Transaction/Loan -> Sponsor & Guarantor -> Collateral & Valuation -> Market ->
Financial Analysis -> Sensitivities/Downside -> Risks & Mitigants (triplet) -> Structure &
Covenants -> Conditions Precedent -> Legal/Title/Environmental -> Exit/Repayment ->
Recommendation + Key Judgment Calls); surface the reduced-independence note; map the 4-tier
severity language.

**Out-of-scope:** the verdict computation (C3); Mode B. No hand-editing of the memo.

**Allowed files/contexts:** `scripts/render_memo.py`; READ-ONLY: `verdict.md`, `ledger/`, spec
§UX (memo content) + Appendix A, domain-lattice `artifact-ic-memo` +
`pattern-risk-mitigant-residual`.

**Step-by-step:**
1. Read the ledger + verdict; assemble the BLUF box mirroring the deterministic verdict.
2. Build the Risks & Mitigants triplet table — every non-fatal finding gets a named mitigant +
   an explicit residual + CP cross-refs ("Mitigated" with no residual is disallowed).
3. Emit all sections; tag each CP to the risk it retires; include the independence note.

**Definition of Done:**
- Artifacts: `scripts/render_memo.py`; `recommendation.md` for a fixture ledger.
- Validation: all 13 sections present (Demo 2); every triplet row has risk+mitigant+residual
  (no bare "mitigated"); every CP references a risk id; memo `rendered_from_ledger == true`
  (byte-derivable from ledger, no manual prose injected); BLUF verdict == `verdict.md`.
- Evidence bundle: rendered memo + a triplet-completeness check + BLUF/verdict match proof.

## Dev (Executor)

**Execution notes:** the memo is a projection of the ledger, not authored prose. Must be
boss-criticism-proof on a first cold look (OKOA final-artifact standard). subscription-only.

**Evidence Bundle:** 1) Summary; 2) Traceability (FR-M8, NFR-8); 3) Quality (section-presence
+ triplet-completeness lint); 4) Testing (render transcript + BLUF match); 5) Compliance
(rendered-from-ledger, no hand edit); 6) Operational; 7) Self-assessment.

## QA (Zero-Trust Verifier)

Verify: (a) confirm all 13 sections exist (Demo 2) / the required subset (Demo 1); (b) for
EVERY triplet row confirm a non-empty residual (reject any "mitigated" with no residual —
recompute from the ledger); (c) confirm every CP tags a real risk id; (d) confirm the BLUF box
verdict equals `verdict.md` exactly; (e) confirm no manual prose was injected outside the
render (diff against a re-render). Reject on missing residual, orphan CP, or BLUF mismatch.

**Evidence gates:** 13 sections; residual on every triplet; CP->risk tagging; BLUF==verdict;
rendered-from-ledger.

## Dev Learnings
_(fill: triplet table rendering; severity-language mapping choices.)_

## QA Learnings
_(fill: bare-"mitigated" rows caught; any hand-edit drift.)_
