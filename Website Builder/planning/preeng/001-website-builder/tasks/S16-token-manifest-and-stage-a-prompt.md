# S16-token-manifest-and-stage-a-prompt — Mechanical token manifest and the Stage-A capsule prompt

| Field | Value |
|---|---|
| Epic / Story | E4 / ST-05 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S14-concept-document-synthesis · S15-font-catalog-and-snapshot |
| Requirements | FR-041, FR-042, FR-043, FR-044, FR-046 |
| Acceptance criteria | A6 · A4 · SL-S16-1 · SL-S16-2 |
| CQ / evidence | CQ5 · CQ14 |
| Precondition | The font-policy answer (S02) must exist before this prompt spec is written |

## PM — slice definition

**Objective.** Emit a frozen token-name manifest generated mechanically from the inventory, and a Stage-A capsule prompt that is greppably complete and traceable to interview ids.

**In scope.** `01-prompt/token-manifest.json` (names only, no values) generated from the inventory item list; the Stage-A prompt containing, greppably: the worked token example, the hue-warning line verbatim, the pinned font shortlist with base64 display cuts, the frozen manifest and prior-identity negative constraints, the content-security constraint, the small-viewport preview requirement, and the self-audit instruction; capsule request (26-slot vector + 40–80 word manifesto, plus a gallery artifact at a desktop frame **and** a 390px portrait frame); over-generation, machine pre-filter on self-audit fields, then user cut to the direction floor; every emitted directive citing its interview question id.

**Out of scope.** Stage B and the envelope (S17). Judging capsules on aesthetics — the pre-filter is mechanical only (hue-anchor collisions, deny-list hits).

**Allowed files / contexts.**
- `scripts/steps/step2.ts`, `scripts/lib/prompt-stage-a.ts`, `scripts/lib/token-manifest.ts`, `01-prompt/**` (write), `session.json` (deviation record).

**Steps.**
1. Generate the manifest mechanically from the inventory list; assert it contains names only and no values.
2. Assemble the Stage-A prompt from typed sections; each of the seven required contents is a named section so a grep can prove presence.
3. Emit the capsule request with both preview frames.
4. Implement the mechanical pre-filter: reject capsules whose hue anchors collide beyond the threshold or that hit the anti-slop deny-list; present the remainder for the human's cut.
5. Record any relaxation of the direction floor in `session.json` as a signed-off deviation.
6. Attach the originating question id to every emitted directive.

**Definition of Done.**
- Artifacts: manifest generator, Stage-A assembler, a generated prompt sample, the deviation record shape.
- Validation: seven greps prove the seven required contents; a diff proves the manifest is byte-identical wherever it is re-pasted; a sample directive shows its question id.
- `slice.yaml` mapping — `acceptance_criteria: [A6, A4, SL-S16-1, SL-S16-2]`, `verification_method: grep-assert` (SL-S16-1: `hash-compare`, SL-S16-2: `exit-code`).

## Dev — execution contract

The prompt is a lottery ticket, not a build artifact: it is stored for provenance only, and the **result** is the artifact of record. Evidence bundle: (1) summary; (2) traceability FR-041…FR-046 → file:line; (3) structural quality — the prompt is assembled from typed sections, never string-concatenated ad hoc; (4) functional testing — the seven greps, the manifest hash comparison, a pre-filter fixture; (5) security/compliance — the content-security constraint is present verbatim; (6) operational — regenerating the prompt after a catalog refresh; (7) self-assessment.

## QA — zero-trust verification

- **Run all seven greps yourself** against the generated prompt.
- **Hash the manifest in every chunk yourself** and require equality.
- **Recompute** the pre-filter on a fixture with a deliberate hue collision and confirm it is rejected mechanically, not by opinion.
- **Sample five directives** and confirm each cites a question id that exists in the bank.
- **Reject** if the direction floor was relaxed without a recorded, signed deviation.

## Dev Learnings

_Not Done until filled. Required: what the pre-filter caught in practice, and whether the manifest generation exposed inventory gaps._

## QA Learnings

_Not Done until filled. Required: which required content was easiest to omit unnoticed._
