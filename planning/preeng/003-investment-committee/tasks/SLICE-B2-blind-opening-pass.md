# SLICE-B2-blind-opening-pass — Independence-first blind opening pass

**Parent story:** STORY-B2 · **Epic:** EPIC-B · **Effort:** M · **Demo:** Demo 1
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Dispatch every roster seat as an **isolated, parallel**
`Task()` that reads the deal materials ALONE with zero cross-visibility and emits an opening
verdict + >=1 falsifiable objection to `rounds/round-00/opening/{seat}.json`. This is the #1
anti-groupthink lever and applies in BOTH modes.

**In-scope:** `blind_openings.py` — resolve roster; for each seat, spawn a `Task()` with the
seat template + deal context ONLY (no sibling output in context); write each seat's opening
JSON immediately; emit `reduced_independence` flag when all seats share one provider.

**Out-of-scope:** Round 2+ cross-talk (Mode B, D1); the fact-builder (C1); the tally.

**Allowed files/contexts:** `scripts/blind_openings.py`; READ-ONLY: `seats/*.md`,
`resolve_seat_model.sh`, `manifest.yaml`, domain-lattice `proc-independence-first` +
`method-blind-first-pass`.

**Step-by-step:**
1. Read the active roster from the manifest; resolve each seat's model/persona.
2. Spawn seats in parallel via `Task()`; each context = seat template + deal materials, NEVER
   another seat's output.
3. Persist each opening verdict to `rounds/round-00/opening/{seat}.json` as it returns; set
   `manifest.reduced_independence` accordingly.

**Definition of Done:**
- Artifacts: `scripts/blind_openings.py`; a `rounds/round-00/opening/` set for a fixture deal.
- Validation: N seats produce N opening JSONs each with a verdict + >=1 falsifiable objection +
  Axis S self-score; NO seat's context contained any sibling output (independence proof);
  single-provider run sets the flag.
- Evidence bundle: dispatch transcript + the opening JSONs + an independence attestation.

## Dev (Executor)

**Execution notes:** subscription-only via `Task()`; strictly no cross-seat context bleed.
Write-to-disk is immediate (durability). Respect the Independence Wall / Oracle hooks.

**Evidence Bundle:** 1) Summary; 2) Traceability (FR-M3, FR-M4, FR-S4); 3) Quality (opening
JSON schema lint); 4) Testing (N-seat dispatch transcript, each JSON validated); 5) Compliance
(no cross-visibility; subscription-only); 6) Operational (immediate persistence); 7)
Self-assessment.

## QA (Zero-Trust Verifier)

Verify: (a) count opening JSONs == roster voting seats; (b) each JSON has a verdict + >=1
falsifiable objection + Axis S score (recompute presence, do not trust a summary); (c) inspect
the dispatch to confirm each seat's prompt/context contained ZERO sibling output — this is the
load-bearing independence check; (d) force single-provider and confirm the flag is set. Reject
if any seat could see another's opening.

**Evidence gates:** N openings; falsifiable objection each; zero cross-visibility proven;
flag correct.

## Dev Learnings
_(fill: Task() isolation gotchas; TaskStop discard-vs-count behavior observed.)_

## QA Learnings
_(fill: any subtle context bleed; independence attestation method.)_
