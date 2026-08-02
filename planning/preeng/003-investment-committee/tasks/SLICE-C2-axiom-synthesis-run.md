# SLICE-C2-axiom-synthesis-run — Run the vendored synthesis engine over IC facts

**Parent story:** STORY-C1 · **Epic:** EPIC-C · **Effort:** M · **Demo:** Demo 1
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Drive the objection facts through the VENDORED synthesis engine
copy at `.claude/skills/acos-investment-committee/scripts/synthesis/` (decircularize -> grade ->
fuse -> falsify -> resolve -> hash-chained ledger), including the independent
DIFFERENT-discipline refuter step, producing a per-claim ledger with truth states and preserved
dissent — with NO runtime dependency on the `acos-axiom-synthesis` skill directory. The IC
fact-builder's Axis-S `severity` field must flow through the run untouched and orthogonal to
the engine's own truth-grading.

**In-scope:**
- Vendoring provenance: this slice assumes the one-time vendored copy (substrate + pipeline +
  tests, plus `VENDORED_FROM.md` recording source path + git commit) already exists at
  `scripts/synthesis/`, established by SLICE-IC-DIAG-01's walking skeleton. If for any reason
  the copy is absent or stale, this slice (re-)vendors it and updates `VENDORED_FROM.md`
  accordingly — but does not fork or edit the copied logic.
- `run_synthesis.py` — feed `ledger/facts-input.json` to the VENDORED `orchestrate.run()`
  (imported ONLY from the local `scripts/synthesis/` copy, never from
  `.claude/skills/acos-axiom-synthesis/`); assign the falsification-gate refuter to a DIFFERENT
  discipline than the raiser; write the hash-chained ledger + `settled-objections.md`; surface
  the reduced-independence flag from de-circularization.
- Axis S: ensure the IC fact-builder's `severity` field (`informational | limitation |
  material-risk | deal-breaker-candidate`, owned by SLICE-IC-C1-objection-fact-adapter-axis-s's
  fact schema) passes through the synthesis run unmodified and orthogonal to the engine's
  truth-grade axis; surface it alongside the truth state in the ledger + `settled-objections.md`.

**Out-of-scope:** the overall verdict (C3); the memo (C4). No engine LOGIC edits — the vendored
copy's contents/behavior must match its recorded source commit; drift is documented in
`VENDORED_FROM.md`, never silently patched.

**Allowed files/contexts:** `scripts/run_synthesis.py`; `scripts/synthesis/` (vendored copy:
substrate + pipeline + tests + `VENDORED_FROM.md`); READ-ONLY (one-time vendoring SOURCE only —
NOT a runtime dependency): `acos-axiom-synthesis` scripts + tests, `ledger/facts-input.json`,
domain-lattice `engine-axiom-synthesis` + `proc-falsification-gate` +
`anti-llm-aggregator-blend`.

**Step-by-step:**
1. Confirm (or, if missing/stale, create) the vendored copy in `scripts/synthesis/` and its
   `VENDORED_FROM.md` (source path + git commit hash).
2. `run_synthesis.py` imports ONLY from the local `scripts/synthesis/` copy; invoke
   `orchestrate.run()` over the input facts (stages 2->7).
3. For the falsification gate, route each objection to a refuter of a DIFFERENT discipline (or
   a fresh steelman "why this is NOT a problem"); never an aggregator-LLM prose blend.
4. Persist the hash-chained ledger + `settled-objections.md`; propagate the de-circularization
   reduced-independence flag.
5. Carry the Axis-S `severity` field through untouched on every fact/claim record — never let
   truth-grading overwrite or infer it.

**Definition of Done:**
- Artifacts: `scripts/synthesis/` (vendored substrate + pipeline + tests) + `VENDORED_FROM.md`;
  `scripts/run_synthesis.py`; a populated `ledger/` + `settled-objections.md` for a fixture,
  with Axis-S severity present on fact records.
- Validation: the vendored `test_pipeline.py` passes IN-TREE (proves the engine copy is
  intact); `run_synthesis.py` has ZERO import/reference to
  `.claude/skills/acos-axiom-synthesis/` (grep-clean); ledger is hash-chain-valid
  (`verify_ledger`); every objection has a truth state; same-fact conflicts appear as `conflict`
  (not blended away); reduced-independence flag correct; Axis-S severity is populated and
  orthogonal to (does not alter) the truth-grade axis; zero edits to the vendored copy's logic
  relative to `VENDORED_FROM.md`'s recorded commit.
- Evidence bundle: synthesis transcript + `verify_ledger` output + a CONTESTED/UNRESOLVED
  example preserved + the vendored `test_pipeline.py` pass log + `VENDORED_FROM.md` contents.

## Dev (Executor)

**Execution notes:** the vendored copy is a black box at RUN time — do not modify its logic;
any drift from the recorded source must be documented in `VENDORED_FROM.md`, not silently
patched. Refuter MUST be a different discipline. subscription-only for any Task() refuter
spawns.

**Evidence Bundle:** 1) Summary; 2) Traceability (FR-M6); 3) Quality (hash-chain integrity;
Axis-S orthogonality); 4) Testing (synthesis + verify_ledger transcript + vendored
`test_pipeline.py` pass); 5) Compliance (no runtime dependency on `acos-axiom-synthesis/`; no
engine logic edits; no MoA blend); 6) Operational (ledger append-only); 7) Self-assessment.

## QA (Zero-Trust Verifier)

Verify: (a) run the vendored `test_pipeline.py` yourself in-tree and confirm it passes; (b)
grep `run_synthesis.py` (and its imports) to confirm ZERO references to
`.claude/skills/acos-axiom-synthesis/` at runtime; (c) run `verify_ledger` yourself and confirm
the hash chain is intact (recompute); (d) confirm every objection fact reached a truth state;
(e) confirm at least one same-fact conflict is preserved as `conflict` and NOT arbitrated away
by a narrator (grep for any aggregator blend); (f) confirm the refuter discipline differs from
the raiser; (g) confirm the Axis-S severity field exists on fact records and is independent of
(does not move) the truth-grade; (h) confirm `VENDORED_FROM.md` records a real source path +
git commit. Reject on a failing vendored test, a live runtime dependency on
`acos-axiom-synthesis/`, hash break, blended conflict, or a missing/incorrect Axis-S field.

**Evidence gates:** vendored `test_pipeline.py` passes in-tree; zero runtime dependency on
`acos-axiom-synthesis/`; hash-chain valid; all facts stated; conflicts preserved;
different-discipline refuter; Axis-S present + orthogonal; provenance recorded.

## Dev Learnings
_(fill: vendoring-copy mechanics; orchestrate.run() wiring; refuter-assignment strategy fixed
vs rotating; Axis-S schema placement.)_

## QA Learnings
_(fill: any MoA-blend temptation caught; oscillation-guard behavior; any accidental runtime
import of the non-vendored engine.)_
