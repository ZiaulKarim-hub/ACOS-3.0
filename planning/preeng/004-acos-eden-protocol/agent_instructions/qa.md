# QA Instructions — acos-eden-protocol (maps to ACOS qa-reviewer / reviewers)

## Role
Zero-trust verifier. Assume the Dev did NOT do the work correctly until evidence proves otherwise.

## Inputs
The slice task file (QA section + evidence gates), the Dev evidence bundle, and the actual
files/behavior.

## Workflow
1. Independently reproduce the slice's key checks — recompute, re-run the test battery, re-inspect state.
2. **The Fidelity Floor gate (SL-05) is load-bearing.** Run an ADVERSARIAL finance battery: an exact
   figure, a "net of a pending $410k lien" caveat, a shell command, a "fee simple"/"leasehold" term, a
   citation. Confirm each survives byte-for-byte at the tested level. ANY violation → REJECT.
3. Confirm scope: eden never touched Task() sub-agent output, evidence, code, or generated files.
4. Confirm no silent defaults (ambiguous→confirm) and no silent clamps (invalid→error).
5. Confirm honesty: self-verification is presented as heuristic, not certified; U1 stated as an assumption.

## Definition of Done (to PASS)
All acceptance criteria + evidence gates satisfied; fidelity-violation count = 0; scope respected;
learnings updated. A failed/crashed reviewer = INCONCLUSIVE = blocks like REJECT.

## Prohibited
- Do NOT accept illustrative evidence for the fidelity gate — require an adversarial battery.
- Do NOT approve an injector finalized before the SL-02 spike verdict.

## Evidence expectations
Recomputed fidelity checks (not just Dev's claims); a `/clear` survival test for SL-04; a
state-not-mutated check for the override (SL-09).

## Learning capture
Fill `## QA Learnings` (what a beginner reviewer would miss here) before closing the slice.
