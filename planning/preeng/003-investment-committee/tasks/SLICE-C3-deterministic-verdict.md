# SLICE-C3-deterministic-verdict — Deterministic verdict + deal-breaker rule

**Parent story:** STORY-C2 · **Epic:** EPIC-C · **Effort:** M · **Demo:** Demo 1 (basic) -> Demo 2 (full)
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Compute the overall verdict **deterministically** via
`resolve.py` as one `resolve_conflict()` over per-discipline roll-ups — asymmetric-veto
polarity on deal-breaker-flagged claims, quorum/ladder otherwise — terminating in `UNRESOLVED`.
The verdict is NEVER narrated by an LLM.

**In-scope:** `compute_verdict.py` — derive the deal-breaker set via the rule
`state ∈ {ESTABLISHED,CORROBORATED} AND axis_s ∈ {material-risk,deal-breaker-candidate} AND no
depends_on mitigant reaches {CORROBORATED,ESTABLISHED}`; build the verdict-as-fact with
discipline roll-up candidates; run `resolve.py` with asymmetric_veto gated on deal-breakers;
write `verdict.md` with the deciding rung/polarity.

**Out-of-scope:** the memo prose (C4); Mode B. No engine edits.

**Allowed files/contexts:** `scripts/compute_verdict.py`; READ-ONLY: `acos-axiom-synthesis`
`resolve.py`, the `ledger/`, spec FR-M7 + Appendix C, domain-lattice
`proc-deterministic-verdict` + `method-asymmetric-veto` + `term-deal-breaker` + `term-unresolved`.

**Step-by-step:**
1. Read ledger truth states + Axis S; compute the deal-breaker set (derived, not stored).
2. Build the final verdict-fact: candidates = per-discipline roll-ups; polarity =
   asymmetric_veto on deal-breaker claims, quorum/ladder for ordinary limitations.
3. Run `resolve.py`; map to `PROCEED | PROCEED-WITH-CONDITIONS | DECLINE | UNRESOLVED`; write
   `verdict.md` citing which rung/polarity decided. Re-run -> identical verdict (NFR-3).

**Definition of Done:**
- Artifacts: `scripts/compute_verdict.py`; `verdict.md` for a fixture ledger.
- Validation: same ledger -> same verdict (reproducible); a fabricated deal-breaker fixture ->
  DECLINE (asymmetric veto); a no-deciding-rung fixture -> UNRESOLVED; NO LLM narration in the
  verdict path; zero engine edits.
- Evidence bundle: two verdict runs on the same ledger (identical) + a DECLINE + an UNRESOLVED
  fixture transcript.

## Dev (Executor)

**Execution notes:** the verdict word is COMPUTED, never written by a model. Deal-breaker is a
derived predicate at compute time, not an engine field. subscription-only.

**Evidence Bundle:** 1) Summary; 2) Traceability (FR-M7, FR-W2, NFR-3); 3) Quality
(determinism proof); 4) Testing (DECLINE + UNRESOLVED + PROCEED-WITH-CONDITIONS fixtures); 5)
Compliance (no narration; no engine edits); 6) Operational (reproducible); 7) Self-assessment.

## QA (Zero-Trust Verifier)

Verify: (a) run `compute_verdict.py` twice on the same ledger and diff `verdict.md` — must be
identical (recompute NFR-3, do not trust a claim); (b) recompute the deal-breaker set by hand
from the ledger and confirm it matches; (c) confirm a fabricated unmitigated deal-breaker
yields DECLINE via asymmetric veto; (d) grep the entire verdict path for any LLM/`Task()` call
that writes the verdict word — there must be NONE; (e) engine `git diff --stat` empty. Reject
on nondeterminism or any narrated verdict.

**Evidence gates:** identical re-run; deal-breaker set correct; DECLINE/UNRESOLVED behavior;
zero narration; engine untouched.

## Dev Learnings
_(fill: resolve.py polarity wiring; verdict-as-fact roll-up construction.)_

## QA Learnings
_(fill: determinism recomputation; any narration path found and killed.)_
