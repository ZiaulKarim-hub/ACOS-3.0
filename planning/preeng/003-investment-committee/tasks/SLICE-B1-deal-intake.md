# SLICE-B1-deal-intake — Shared deal extraction layer + session scaffold

**Parent story:** STORY-B1 · **Epic:** EPIC-B · **Effort:** M · **Demo:** Demo 1
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Read a deal dataroom directory **exactly ONCE** — not once
per seat — and build the `Deal` + `SessionManifest`, a structured **shared deal-brief** +
**evidence-index** that every subsequent expert reads as its deal-materials context, and
scaffold the durable session layout so downstream slices have a Deal object and a place for
all artifacts. This shared extraction pass is now the CORE of this slice (it was previously
framed as plain document cataloging; it is now the single upfront read that removes N
redundant per-seat reads and gives #3 Accounting's normalized-NOI claim exactly one canonical
place to live).

**In-scope:** `intake.py` — resolve `--deal <dir>`; build `Deal` (deal_id, asset_type, ask,
jurisdictions, fund_id); enumerate documents -> `EvidenceCitation`s, assembled into a single
**`evidence-index.yaml`**; run ONE upfront structured-extraction pass over the dataroom into
**`deal-brief.yaml`** (asset overview, key terms, rent-roll/T-12/financial-statement summary,
and a reserved `normalized_noi` slot — the single canonical location Accounting's #3 seat
populates and #1/#2 subsequently read, so no seat re-derives or re-stores its own private
copy); write `manifest.yaml` (status `open`, roster placeholder, round_config defaults) and
scaffold `rounds/`, `ledger/`, `transcript.md`.

**Out-of-scope:** per-seat DEEP or external research (that is each expert's own private
swarm — SLICE-B3); seat dispatch (SLICE-B2); synthesis. This slice produces the shared
baseline facts every seat starts from; it does not do discipline-specific research.

**Allowed files/contexts:** `.claude/skills/acos-investment-committee/scripts/intake.py`;
READ-ONLY (deal dir), `session_scaffold.py` (SLICE-DIAG-01), tech_prd §2 layout, data-model
Deal/SessionManifest/EvidenceCitation.

**Step-by-step:**
1. Parse args; derive `deal_id` slug from the directory name.
2. Build `Deal` with best-effort asset_type + ask + jurisdictions (mark unknowns
   `Assumption`); set `fund_id` if a loan-tape reference is present.
3. Catalog files as EvidenceCitations exactly once and write them into a single
   `evidence-index.yaml` (source_ref + tier per citation) that every downstream expert and
   private research swarm reads instead of re-scanning the dataroom.
4. Run the shared extraction pass: read every dataroom document ONE time and populate
   `deal-brief.yaml` with structured shared facts (asset overview, key terms, rent-roll/T-12/
   financial-statement summary). Reserve — do NOT populate — a `normalized_noi` field/slot;
   this is the single canonical location Accounting (#3) later writes its normalized-NOI
   claim into, and the only place #1/#2 read it from (fact-builder/synthesis-time
   reconciliation, per SLICE-A2, still applies on top of this shared baseline).
5. Write `manifest.yaml` + scaffold via the DIAG-01 routine (idempotent).

**Definition of Done:**
- Artifacts: `scripts/intake.py`; a populated sample session `manifest.yaml`; a document
  catalog (`evidence-index.yaml`); a shared `deal-brief.yaml` with the reserved
  `normalized_noi` slot.
- Validation: intake on a fixture deal dir produces a valid `manifest.yaml` (status `open`,
  round_config defaults 5-6 / 150-250w / every-3), a non-empty `evidence-index.yaml`, and a
  `deal-brief.yaml` whose `normalized_noi` slot is present but unset/`Assumption`-marked
  (never fabricated at intake time); unknown deal fields are `Assumption`-marked, not
  fabricated; the dataroom is read exactly once (no per-seat re-read of raw source documents
  observable in the intake transcript).
- Evidence bundle: intake transcript + rendered manifest + rendered deal-brief +
  evidence-index for a fixture deal.

## Dev (Executor)

**Execution notes:** subscription-only; do NOT confabulate deal metadata from folder names
(names are not authoritative — cross-check current-state). stdlib-only. The shared
deal-brief is a read-many/write-once-per-field artifact: intake writes the raw/reported
shared facts and the reserved (empty) `normalized_noi` slot; only the Accounting seat's own
opening pass (a later slice) ever writes into that slot.

**Evidence Bundle:** 1) Summary; 2) Traceability (Deal/SessionManifest/EvidenceCitation
fields; shared deal-brief + normalized_noi slot); 3) Quality (manifest + deal-brief schema
lint); 4) Testing (fixture intake transcript, single-read proof); 5) Compliance (no
name-based confabulation; Assumption markers); 6) Operational (idempotent scaffold); 7)
Self-assessment.

## QA (Zero-Trust Verifier)

Verify: (a) run `intake.py` on the fixture and confirm `manifest.yaml` validates against the
data-model shape; (b) confirm every uncertain field is `Assumption`-marked (not silently
guessed from the folder name); (c) confirm the `evidence-index.yaml` catalog matches the
actual files on disk (recount); (d) confirm `deal-brief.yaml` exists, contains the shared
structured facts, and its `normalized_noi` slot is present but unpopulated/`Assumption`-marked
(reject if intake fabricates a normalized-NOI figure itself — that is Accounting's #3 job,
not intake's); (e) confirm scaffold idempotency; (f) confirm the dataroom is read exactly
once in the intake transcript (no evidence of a second, per-seat raw-document read baked into
this slice's scope). Reject on any confabulated metadata or a prematurely populated
normalized-NOI value.

**Evidence gates:** valid manifest; Assumption markers on unknowns; citation count == file
count; deal-brief present with the reserved (unset) `normalized_noi` slot; idempotent
scaffold; single-read proof.

## Dev Learnings
_(fill: folder-name-trap avoidance; asset_type inference heuristics; how the deal-brief
schema balanced "structured enough to be useful" against "not pre-judging what Accounting
will later determine".)_

## QA Learnings
_(fill: metadata confabulation caught; citation-count mismatches; any place the
normalized_noi slot was pre-populated at intake time, which would violate the single-owner
rule.)_
