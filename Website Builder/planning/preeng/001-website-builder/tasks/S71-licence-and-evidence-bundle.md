# S71-licence-and-evidence-bundle — The licence-and-evidence bundle with fixed disclosure wording

| Field | Value |
|---|---|
| Epic / Story | E15 / ST-24 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 5 / Demo 4 (feeds) |
| Depends on | S69-lock-snapshots-manifest-and-unlock, S56-lane-b-asset-library-and-chips |
| Requirements | FR-212, FR-213, FR-214, FR-215, FR-216 |
| Acceptance criteria | A72 · A73 · A74 · SL-S71-1 · SL-S71-2 · SL-S71-3 |
| CQ / evidence | CQ10 · CQ11 |
| Note | **The bundle is the deliverable, not a by-product.** Success criterion **S8** — zero shipped assets or fonts without a recorded licence class — is grep/lint-asserted **against this bundle and is build-failing** |

## PM — slice definition

**Objective.** Make the bundle the deliverable: **every licence**, every **measured** gate value, the direction tour, and a claim ceiling that is never exceeded.

**In scope.** `evidence/` assembled as `{fonts, assets, thirdPartyMarks, gateReport, contrastProofTable, screenshots, directionTour, referenceTriangulation, substitutionLog, publishRecord, disclosure}`; per-font `{family, foundry, licenceClass, fileHash, sourceUrl, attributionRequired}`; per-asset `{generator, model, planTier, licenceClass, prompt, alt, source}`; third-party marks with usage rules and confirmation they were **used as supplied** (A75 — no `[3P]` mark may be redrawn; generating a platform badge is a trademark violation, which is legal exposure, not aesthetic); the gate report with thresholds **and measured values**; the contrast proof table with **WCAG ratio and APCA Lc per pairing**; the screenshot matrix across breakpoints × light/dark × full/reduced motion **including the pinned-device-height captures** from S65; the **direction tour** rendered from `direction-tour-log.json` with every heat's pick and **stated reason**; reference triangulation under the **≥3-reference rule** (each direction abstracts ≥3 references from different eras/genres/cultures; **>70% overlap with any single reference forces regeneration**); the substitution log; the publish record from S70; the **fixed disclosure line**; commercial-foundry faces emitting a **pre-launch blocker** rather than being embedded (A74); and a one-line verdict mirrored into `.acos/evidence/<date>/website-<session>/`.

**Out of scope.** Judging whether a licence is *acceptable* — the bundle records the class and blocks where the rule says block; the human decides. Rewriting or redrawing a third-party mark for any reason. Any wording that implies conformance.

**Allowed files / contexts.**
- `scripts/lib/evidence-bundle.ts`, `scripts/lib/licence-audit.ts`, `scripts/lib/direction-tour-render.ts`, `evidence/**` (write), `.acos/evidence/<date>/website-<session>/` (one-line mirror, write).

**Steps.**
1. Walk `assets/manifest.json` and the font catalog snapshot; assemble the per-font and per-asset records with every named field populated. A missing `licenceClass` is a **build failure**, not a warning (criterion S8 is binary).
2. Emit the pre-launch blocker for any commercial-foundry face rather than embedding it (A74).
3. Copy the gate report in with `measured` **and** `threshold` on every row — a threshold with no measurement is an assertion, and this bundle exists to replace assertions with measurements.
4. Build the contrast proof table with both the WCAG ratio and the APCA Lc per pairing; APCA is advisory `[U — the perceptual bands are inherited and not re-verified]`.
5. Attach the screenshot matrix, carrying S65's `devicePinned` and `measuredFrameHeight` fields; a `contentReviewOnly` capture may not stand in for a pinned one.
6. Render the direction tour from `direction-tour-log.json` — every heat, every pick, every stated reason, in the order they happened.
7. Record reference triangulation per direction: ≥3 abstracted references from different eras/genres/cultures, plus the regeneration trigger above the 70% single-reference overlap threshold.
8. Write the disclosure **verbatim**: *"Automated accessibility gates passed: N. Manual and screen-reader review not performed."* — N is read from the gate report, never typed by hand.
9. Mirror a one-line verdict into the framework evidence directory.

**Definition of Done.**
- Artifacts: the complete bundle with all eleven members, the licence audit output, the rendered direction tour, the mirrored verdict line.
- Validation: zero fonts or assets without a licence class; a grep over the bundle **and all product copy** for `compliant|conformant|certified|WCAG AA` returns zero; every direction carries ≥3 references; the disclosure string matches byte-for-byte.
- `slice.yaml` mapping — `acceptance_criteria: [A72, A73, A74, SL-S71-1, SL-S71-2, SL-S71-3]`, `verification_method: exit-code` (A72/A73/SL-S71-1: `grep-assert`).

## Dev — execution contract

Automated accessibility tooling catches **57.38%** of real issues `[V — 13,000+ page-states, ~300,000 issues]`, so the bundle says *"passed N automated gates"* and **never** "AA compliant". Evidence bundle: (1) summary — counts of fonts, assets, marks, gates and screenshots; (2) traceability FR-212…FR-216 → file:line per bundle member; (3) structural quality — one assembler, one writer, no member assembled by hand; (4) functional testing — a seeded asset with no licence class fails the build; a seeded commercial-foundry face emits the blocker; (5) security/compliance — no credential, no remote host reference, no telemetry; (6) operational — how to regenerate the bundle from disk without re-running LOCK; (7) self-assessment naming which member was thinnest.

## QA — zero-trust verification

- **Recount the fonts and assets yourself** from `assets/manifest.json` and the font snapshot; compare against the bundle. A count you cannot reproduce is a rejection.
- **Seed an asset with no licence class** and confirm the build **fails** — a warning is a rejection, because criterion S8 is binary and build-failing.
- **Run your own** `grep -rniE 'compliant|conformant|certified|WCAG[ -]?AA' evidence/ app/ scripts/` and require zero hits, including in comments and UI strings.
- **Recompute two contrast pairings** from the shipped CSS and compare to the proof table.
- **Read the direction tour** and confirm every heat carries a **stated reason**, not just a winner — a tour without reasons cannot answer why the site looks the way it does.
- **Check the reference triangulation** for ≥3 references per direction from different eras/genres/cultures, and that the >70% overlap trigger is recorded, not merely described.
- **Reject** if any `[3P]` mark was redrawn or regenerated rather than used as supplied.

## Dev Learnings

_Not Done until filled. Required: which asset class most often arrived without a licence class, and whether the ≥3-reference rule was satisfiable from the tour log alone._

## QA Learnings

_Not Done until filled. Required: where conformance language tried to creep back in, and which bundle member was easiest to assemble as plausible-looking filler._
