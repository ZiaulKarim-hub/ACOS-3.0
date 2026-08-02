# S02-o1-font-policy-probe — Generation-surface font-policy probe (60 seconds)

| Field | Value |
|---|---|
| Epic / Story | E0 / ST-01 |
| Type · MoSCoW · Size | diagnostic · MUST · S `[I]` |
| Phase / Demo | Phase 0 / — |
| Depends on | none |
| Requirements | FR-004 |
| Acceptance criteria | SL-S02-1 · SL-S02-2 |
| CQ / evidence | CQ5 · EL-067 (assumed blocking, unverified) |
| Blocking | Must complete **before the Step-2 prompt spec is written** (S16) |

## PM — slice definition

**Objective.** Establish whether an artifact on the generation surface actually renders a linked web font, or silently falls back to a system face — because if it falls back, the human picks a look they have never seen (R2, critical).

**In scope.** One minimal artifact that links a hosted font stylesheet and renders a display-size specimen; a devtools network observation of the font-file request; the same specimen with a base64 `data:font/woff2` `@font-face`; ADR-02.

**Out of scope.** Building the font catalog (S15). Writing any prompt template. Changing any product code. Attempting to circumvent a content-security policy.

**Allowed files / contexts.**
- `docs/adr/ADR-02-font-policy.md` (new)
- `scripts/probes/font-policy/*.html` (new, throwaway fixtures)
- Screenshots and a network log under the slice's evidence directory.
- **No product path may be touched.**

**Steps.**
1. Render fixture A: stylesheet link + a display-size specimen at 96px.
2. Open devtools, record whether the font binary request succeeds or is blocked, and capture the network entry verbatim.
3. Screenshot the specimen. Compare glyph shapes against a known reference render of the same family.
4. Render fixture B: the same specimen using a pre-subsetted base64 `data:font/woff2` `@font-face`. Screenshot.
5. Write ADR-02: does the surface render the linked face, or must the skill embed the binary?

**Definition of Done.**
- Artifacts: both fixtures, both screenshots, the raw network entry, ADR-02.
- Validation: the answer is derived from an observed network entry **and** a visual comparison — one alone is insufficient, because a fallback can look plausible.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S02-1, SL-S02-2]`, `verification_method: probe`.

## Dev — execution contract

Open previews with the browser invoked explicitly (`open -a "Google Chrome" <url>`), never the default handler. Evidence bundle: (1) summary stating the answer in one sentence; (2) traceability FR-004 → fixture; (3) structural quality — fixtures are throwaway and contain no product code; (4) functional testing — both screenshots plus the network entry; (5) security/compliance — no credential, no external write; (6) operational — how to re-run in under a minute when the surface changes; (7) self-assessment — state plainly that this is a point-in-time observation of a third-party surface and will decay.

## QA — zero-trust verification

- **Re-render** fixture A yourself and take your own screenshot; do not accept Dev's image as proof.
- **Recompute** the visual comparison: if the rendered glyphs match a system fallback rather than the named family, the "it renders" claim is false regardless of what the network panel appears to show.
- **Reject** if the conclusion rests on the absence of an error message rather than on a positive observation.
- **Reject** if ADR-02 states a conclusion stronger than the evidence (e.g. "fonts work" from a single family on a single day).
- Record freshness: this fact decays; the ADR must carry the observation date.

## Dev Learnings

_Not Done until filled. Required: the exact network-panel wording observed, and whether the fallback was visually detectable without devtools._

## QA Learnings

_Not Done until filled. Required: whether an independent re-render agreed, and what would make this probe cheaper to repeat every few months._
