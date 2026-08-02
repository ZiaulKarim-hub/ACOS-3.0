# Phase 5 — fusion rules (backbone-first, not blend)

The synthesizer does NOT "merge N proposals." Merging averages away the boldest,
best ideas (lowest-common-denominator) and stitches architecturally incompatible
fragments ("frankenspec"). Instead:

## Core method

1. **Backbone pick.** Choose ONE proposal as the architectural backbone. State it
   explicitly. The backbone's assumption set (components, connectors, global
   structure, build procedure — Garlan's four categories) becomes the frame.
2. **Graft.** Mine the other proposals ONLY for strengths compatible with the
   backbone's assumptions. Every graft is justified against the frame. Reject
   grafts that import a conflicting assumption set.
3. **Bold-idea disposition.** Extract each proposal's most distinctive design move
   into an explicit list. Dispose of each one on the record — adopt or reject with
   reason. Never drop a bold idea by silent omission.

## Two lanes per section

- **Factual / requirement claims** (entities, endpoints, functional intent):
  convergence rules — asserted in ≥2 proposals → keep; grounded singleton → keep,
  tagged; ungrounded singleton → drop; contradiction → OPEN_QUESTION. Route through
  `acos-axiom-synthesis` where a hash-chained ledger is wanted.
- **Design decisions** (architecture, patterns): pairwise-judged trade-offs against
  explicit criteria (robustness > effectiveness > efficiency). Fuse the winner with
  any superior sub-idea from losers.

## Hard guards (the guard catalog)

| Guard | Rule |
|---|---|
| G1 anti-frankenspec | backbone-first; grafts justified against the assumption set; never per-section best-of |
| G2 decorrelate | different families; treat unanimity as WEAK evidence, flag for verification |
| G3 anti-LCD | bold-idea disposition list; every distinctive move adopted or rejected on record |
| G4 self-preference | synthesizer family authored NONE of the proposals (or anonymize/normalize first) |
| G5 position/length | randomize proposal order; compare in both orders; score length-normalized |
| G6 anti-telephone | ONE generative fusion pass; iterations are diff patches at low temp; length ≤ ~1.3× longest proposal |
| G7 lost-constraint | intent_id → spec-section traceability matrix as a HARD GATE (count check) |
| G8 consistency | normalize requirements to rows; mechanical checks where formalizable; LLM (different family) for the rest; never a single "any contradictions?" prompt |
| G9 no deliberation | proposals stay blind end-to-end; conflicts → OPEN_QUESTIONS, not a chat |
| G10 red-team | independent critic (different family, blind to fusion rationale) can REJECT and reopen fusion |

## Security & edge = UNION, never vote

A same-spec study had EVERY clone tool skip the same protections (CSRF, rate-limit,
HSTS, CSP). Ensembles cannot catch a universal blind spot by voting. So: take the
UNION of all security/edge/error requirements any proposal raised, then apply a
model-independent security baseline checklist on top. Majority-vote is banned for
these axes.

## Emission

Plan-then-write: build the fused outline first, then generate each section
sequentially (per-domain ~30K-token shards to beat lost-in-the-middle and fit
agent windows). Concatenate, then a minimal-diff QA loop. Never regenerate the
whole spec per iteration.
