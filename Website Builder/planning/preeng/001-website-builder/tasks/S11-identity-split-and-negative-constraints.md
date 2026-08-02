# S11-identity-split-and-negative-constraints — System/identity split, negative constraints and mined-source pre-fill

| Field | Value |
|---|---|
| Epic / Story | E2 / ST-03 |
| Type · MoSCoW · Size | build · MUST · S `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S10-warm-start-and-asset-library-detection |
| Requirements | FR-022, FR-023, FR-024 |
| Acceptance criteria | SL-S11-1 · SL-S11-2 |
| CQ / evidence | CQ16 |
| Risk | R26 — warm start homogenises the portfolio and produces a house style the user never chose, invisible until site three |

## PM — slice definition

**Objective.** Carry forward exactly what is reusable, deliberately exclude what is identity, and inject prior identities into the next prompt as **negative** constraints.

**In scope.** The carried set — token-name schema, component slot contracts, motion-primitive library, font catalog, anti-slop deny-list, editor configuration and user-level interview answers. The excluded set — hue anchors, type pairings, radius/density, motion character, artwork, grid personality and the signature moment. Negative-constraint emission unless the sibling-site question is answered yes. Mining prior sources to pre-fill answers.

**Out of scope.** Writing the prompt itself (S16). Carrying any excluded item "just in case" — that is the failure this slice exists to prevent.

**Allowed files / contexts.**
- `scripts/lib/warmstart.ts` (extend), `scripts/lib/identity-split.ts` (new), `session.json` (write), `00-interview/answers.json` (pre-fill only, with `source: pre-filled`).

**Steps.**
1. Encode both sets as explicit lists in code, not as a heuristic.
2. On warm start, copy only the carried set into the session; record what was carried and what was withheld in `session.json`.
3. Emit prior hue anchors and type pairings as negative constraints ("do not produce a direction within 30° of these hues or reusing these type pairings") into the Step-2 input bundle.
4. Honour the sibling-site answer: when the user says yes, suppress the negative constraints and record that suppression.
5. Mine prior sources (existing site trees, token bundles, licence registers) into pre-filled answers marked `source: pre-filled` with an override flag.

**Definition of Done.**
- Artifacts: `identity-split.ts`, the session record of carried vs withheld, the negative-constraint block.
- Validation: a grep over the carried session shows **zero** excluded-set items; the negative-constraint block contains the prior hues; pre-filled answers are marked and overridable.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S11-1, SL-S11-2]`, `verification_method: grep-assert`.

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-022–FR-024 → file:line; (3) structural quality — both lists are data, not scattered conditionals; (4) functional testing — a warm-start fixture with a prior system, showing the carried/withheld record and the emitted constraints; (5) security/compliance — no cross-project write; (6) operational — what happens when a prior system is partially corrupt; (7) self-assessment.

## QA — zero-trust verification

- **Grep the carried session yourself** for every excluded-set item by name; a single hue anchor found is a rejection.
- **Read the emitted negative-constraint block** and confirm it names the actual prior values, not a placeholder.
- **Reject** if pre-filled answers are indistinguishable from asked answers — provenance is the point.
- **Reject** if the sibling-site suppression path is undocumented in the session record.

## Dev Learnings

_Not Done until filled. Required: which item was tempting to carry forward that the split forbids, and why._

## QA Learnings

_Not Done until filled. Required: whether a second site would visibly inherit anything it should not._
