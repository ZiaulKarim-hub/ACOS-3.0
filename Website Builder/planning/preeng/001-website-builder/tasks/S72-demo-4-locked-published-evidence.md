# S72-demo-4-locked-published-evidence — DEMO 4 — locked, published, evidence-complete

| Field | Value |
|---|---|
| Epic / Story | E15 / ST-24 |
| Type · MoSCoW · Size | demo · MUST · M `[I]` |
| Phase / Demo | Phase 5 / **Demo 4** |
| Depends on | S70-publish-automated-with-runbook-fallback, S71-licence-and-evidence-bundle |
| Requirements | — (demo slice; exercises FR-200…FR-216 end to end) |
| Acceptance criteria | A51 (or the signed-off normalised fallback) · A72 · A73 · SL-S72-1 |
| CQ / evidence | CQ9 · CQ10 |
| Note | **The bundle is the deliverable, not a by-product.** This demo is the exit condition of Phase 5 and the gate on epic E15 |

## PM — slice definition

**Objective.** Demonstrate the **full exit condition** in one recorded run: a locked site with proof of purity, **published**, with a complete bundle.

**In scope.** One end-to-end recorded run from an editable project to a published site: `wb lock` running the **eight** purity gates and the **32**-check checklist; the snapshot, the `lock-manifest.json` and the `wb-lock/<n>` tag; `wb publish` taking the **automated** path; the evidence bundle assembled with **zero missing licence classes**; the publish record stating plainly that the site is live; the recorded transcript, the gate report and the screenshot matrix as demo artifacts.

**Out of scope.** Building anything new — every mechanism this demo exercises is owned by S65–S71 and is only *composed* here. Repairing a failure inline: a failed demo returns the finding to the owning slice. Accepting the runbook path as a pass.

**Allowed files / contexts.**
- `demos/demo-4/**` (transcript, artifacts, README), `.acos/evidence/<date>/website-<session>/` (verdict mirror).
- **No product source file may be edited by this slice.** If the demo cannot pass without a code change, the demo **fails** and the change is made in its owning slice.

**Steps.**
1. Start from a project in the `editing` phase with real content, real assets and a selected direction — not a fixture stub.
2. Run `wb lock`. Record: eight purity-gate verdicts, all tier-one lock-check verdicts, the wall clock.
3. If gate 2 reports the **normalised-comparison fallback** rather than byte-identity, record it as such and record that it **weakens D3's proof and requires sign-off** (`§12.5-O33`; sign-off row 8 is **unsigned, contingent**). Do not present the fallback as byte-identity.
4. Run `wb publish` on the **automated** path; capture the live URL. **A runbook-fallback run does not satisfy this demo** (NA-09) — if the credential is absent, the demo is blocked, not passed.
5. Assemble the evidence bundle and assert zero missing licence classes (criterion S8).
6. Verify the disclosure line reads *"Automated accessibility gates passed: N. Manual and screen-reader review not performed."* and that no conformance claim appears anywhere.
7. Mirror the one-line verdict into the framework evidence directory and write the demo README with the exact reproduction commands.

**Definition of Done.**
- Artifacts: the run transcript, `gate-report.json`, `lock-manifest.json`, the tag, the publish record with a live URL, the complete bundle, the screenshot matrix, the demo README.
- Validation: eight purity gates pass (or gate 2 records the signed-off fallback with its enumerated exception set); all tier-one lock checks pass; `publishRecord.live` is `true`; zero missing licence classes; zero conformance strings.
- `slice.yaml` mapping — `acceptance_criteria: [A51, A72, A73, SL-S72-1]`, `verification_method: exit-code` (A51: `hash-compare`; A72/A73: `grep-assert`).

**Assumption.** `[I]` The demo is run against a **representative 5-page site**, matching the site shape NFR-02's `[I]` LOCK wall-clock budget was sized against, so the recorded timing is comparable to that budget. The timing is reported as a measurement of this run only — it does not convert the `[I]` budget into a measured SLA.

## Dev — execution contract

This is a composition slice: its value is the recording, so record everything, including the failures that were repaired upstream before the final run. Evidence bundle: (1) summary — locked yes/no, published yes/no, bundle complete yes/no, in three lines; (2) traceability — each demo step to its owning slice; (3) structural quality — no product source was edited by this slice, provable by diff; (4) functional testing — the full transcript with exit codes; (5) security/compliance — the published tree carries no design-time origin, no editor string and no credential; (6) operational — the exact command sequence to reproduce, in absolute paths; (7) self-assessment stating which of gate 2's two outcomes occurred.

## QA — zero-trust verification

- **Run the whole demo yourself** from the README. A transcript you cannot reproduce is a rejection.
- **Open the published URL yourself** and confirm it serves the locked tree; a `publishRecord` claiming `live: true` with a URL that does not resolve is the most serious possible defect here.
- **Run your own** `grep -r 'data-wb-'` and the design-time-origin grep over the published tree.
- **Recount the licence classes yourself** against `assets/manifest.json`; one missing class is a rejection.
- **Confirm which gate-2 outcome occurred** and reject any wording that presents the normalised fallback as byte-identity.
- **Reject** if the run took the runbook path — locked is not published.
- **Reject** if any product source file was modified by this slice.

## Dev Learnings

_Not Done until filled. Required: what broke on the first full end-to-end run that every individual slice's tests had passed._

## QA Learnings

_Not Done until filled. Required: whether the demo was reproducible from the README alone, and what the transcript omitted that you needed._
