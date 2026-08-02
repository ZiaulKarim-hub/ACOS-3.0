# /preeng.analyze — Cross-Artifact Analysis Report

**Feature:** `001-website-builder` — Website Builder (ACOS skill `acos-website-builder`)
**Feature directory:** `/Users/zee/Documents/Vibe Coding/ACOS 3.0/Website Builder/planning/preeng/001-website-builder/`
**Command:** `/preeng.analyze` · **Date:** 2026-07-26 · **Emitted by:** the deterministic pre-engineering worker (stage C1)
**Companion outputs:** `cage_preeng_nodes.csv` (40 nodes), `cage_preeng_edges.csv` (56 edges)

---

## 0. Method — what was computed and what was read

This report distinguishes three epistemic classes and never blurs them:

| Class | Meaning | How it appears below |
|---|---|---|
| **Computed** | Derived mechanically from the artifacts on disk by a script, at analysis time | stated as a number with the two files it was computed from |
| **Read** | Taken from a specific line or window of a specific file | stated with the file and, where it matters, the line |
| **Inference `[I]`** | Not measured; carried from the source with its own marker | tagged `[I]` and, for every schedule or effort figure, additionally tagged **low confidence** |

**Every coverage number in §3 was computed, not asserted.** The checks were run as TypeScript on Bun against `stories.json`, `spec.md`, `plan.md`, `tech_prd.md`, `data-model.md`, `domain-cqs.md`, `domain-lattice.json`, `evidence-ledger.json` and all 78 files under `tasks/`. Prose artifacts were read in windows, never whole; the 635,881-character source PRD was read only in the narrow windows named in §4.

**Marker discipline.** The PRD's `[V]` verified / `[I]` inference / `[U]` unsourced markers are preserved on every carried claim. No inference is promoted to fact anywhere in this report. Per the standing rule, **every schedule and effort figure in this document is inference, not measurement, and carries low confidence** — including the +16–24 day DECISION-1 delta, the ~25–35 day revised v1 band, the 30–60 day editor-full band, and the "under an hour" cost of Gate 16-A.

**Assumption (recorded).** Two coverage figures were produced by two different extraction methods during this run and disagree. The orchestrator's sweep reports 36 competency questions defined and 103 distinct A-ids cited with a maximum of A112; this analysis's own extraction, run directly against `domain-cqs.md` and against `stories.json`'s `acceptance_criteria` arrays, reports 18 competency questions of record and 90 canonical criteria cited (A1–A90) plus 11 section-qualified A91+ ids. The difference is scope of extraction, not disagreement about content: the larger CQ count includes repeated CQ mentions in cross-reference tables, and the larger A count includes A-ids appearing anywhere in prose across `plan.md` (which cites **A102 and A112**, neither of which exists in any A91+ set — see D-14). **This report uses the narrower, structurally-scoped numbers and states the method each time.** Both readings agree that zero cited CQ and zero cited evidence ref fails to resolve.

---

## 1. Artifact presence and integrity

All artifacts required by §1 of the command spec, except `agent_instructions/` (owned by a concurrent sibling agent and out of this stage's scope), are present at the absolute feature directory.

| Artifact | Bytes | Parses / structural check | Status |
|---|---:|---|---|
| `spec.md` | 140,031 | 13 required headings present; 188 FR rows; §4.1/§4.3 registers intact | PRESENT |
| `research.md` | 25,633 | evidence-ledger discipline enforced in prose | PRESENT |
| `research_qa_report.json` | 6,077 | JSON parses; keys `qa_status`, `issues`, `notes` | **APPROVED** |
| `domain-brief.md` | 15,826 | DLG output: entities, processes, methods, standards, metrics, risks, terms | PRESENT |
| `domain-cqs.md` | 39,842 | 18 competency questions, CQ1–CQ18 | PRESENT |
| `domain-lattice.json` | 191,489 | JSON parses; 334 nodes / 546 edges; schema §2.3 obeyed exactly | PRESENT |
| `evidence-ledger.json` | 64,133 | JSON parses; 88 entries; schema §2.4 obeyed exactly | PRESENT |
| `plan.md` | 48,992 | phases, epic table, demo table, sequencing rule | PRESENT |
| `tech_prd.md` | 67,259 | TR1–TR21, route contract, gate thresholds | PRESENT |
| `data-model.md` | 33,618 | file map §1 + entity sections §3.1–§3.2x | PRESENT |
| `planning_qa_report.json` | 9,031 | JSON parses; 15 issues, all NON-BLOCKING | **APPROVED** |
| `stories.json` | 152,839 | JSON parses; 20 epics / 26 stories / 78 slices | PRESENT |
| `tasks/*.md` | 394,515 | **78 of 78**; mean 5,058; min 3,183 (S22); max 7,361 (S67) | PRESENT |
| `tasks_qa_report.json` | — | emitted this stage | **APPROVED** |
| `analysis-report.md` | — | this file | EMITTED |
| `cage_preeng_nodes.csv` | — | 11-column header per §0.4; 40 node rows | EMITTED |
| `cage_preeng_edges.csv` | — | 4-column header per §0.4; 56 edge rows | EMITTED |
| `agent_instructions/pm.md`, `dev.md`, `qa.md` | — | **owned by a concurrent sibling agent; not written by this stage** | OUT OF SCOPE HERE |

**Truncation check (computed).** All 78 task files terminate inside their `## QA Learnings` italic block. Zero files are truncated, zero are empty, zero end mid-sentence.

---

## 2. ERROR-gate evaluation

The command spec's §3 preconditions were evaluated before this command produced anything.

| Gate | Requirement | Observed | Verdict |
|---|---|---|---|
| `/preeng.plan` gate | `research_qa_report.json.qa_status != "REJECTED"` | `APPROVED` | did not fire |
| `/preeng.tasks` gate | `planning_qa_report.json.qa_status != "REJECTED"` | `APPROVED` | did not fire |
| `/preeng.analyze` precondition | required upstream artifacts exist | all present (§1) | did not fire |

**No `ERROR:` line was emitted at any point in this stage.** Both upstream QA reports are `APPROVED` with all issues classified NON-BLOCKING, so `/preeng.analyze` was entitled to run and did.

---

## 3. Mechanical coverage — computed results

### 3.1 Slices ↔ task files

| Check | Result |
|---|---|
| Slices declared in `stories.json` | **78** |
| Files present under `tasks/` | **78** |
| Slices with no task file | **0** |
| Task files with no slice | **0** |
| Slices whose `task_file` field ≠ `tasks/<id>.md` | **0** |

Re-verified, not assumed. Every slice id maps to exactly one file and every file maps back.

**Structural conformance across all 78 files (computed):**

| Required element | Files missing it |
|---|---|
| `## PM …` section | 0 |
| `## Dev — execution contract` | 0 |
| `## QA — zero-trust verification` | 0 |
| `## Dev Learnings` | 0 |
| `## QA Learnings` | 0 |
| Learnings section shorter than 40 characters | 0 |
| Header rows Epic/Story · Type·MoSCoW·Size · Depends on · Requirements · Acceptance criteria | 0 |
| `slice.yaml` `acceptance_criteria` + `verification_method` mapping line | 0 |
| Seven-part evidence bundle | 0 |
| A named rejection condition in the QA section | 0 |
| LCE elements Objective / In scope / Out of scope / Allowed files / Steps / Definition of Done | **3** — S43 and S50 lack the literal `**Steps.**` label (both carry numbered step lists under their In-scope label); **S48 carries no numbered step list at all** |

### 3.2 Functional requirements — orphans in **both** directions

Requirements are **defined in `spec.md` §4.1** as table rows. `plan.md`, `tech_prd.md` and `data-model.md` reference requirements in prose rather than by id.

| Check | Result |
|---|---:|
| FR ids defined as `spec.md` table rows | **188** |
| Distinct FR ids claimed across `stories.json` `fr_ids` | **188** |
| Sum of all `fr_ids` entries (i.e. total claims) | **188** |
| **Defined but claimed by no slice (orphan direction A)** | **0** |
| **Claimed by a slice but not defined (orphan direction B)** | **0** |
| Claimed by more than one slice | **0** |
| FR ids cited in task-file prose but undefined | **0** |
| Slices whose task file omits a declared FR | **0** |
| Slices with empty `fr_ids` | **4** — S28, S40, S50, S72, all `type: demo` (deliberate convention) |

**The partition is exact:** 188 requirements, 74 requirement-bearing slices, every requirement owned by exactly one slice, in both directions, with no leakage into the demo gates.

Two observations that are **not** orphan defects but are recorded:

- `plan.md` cites only **4** FR ids (FR-016, FR-052, FR-091, FR-220); `tech_prd.md` and `data-model.md` cite **none**. Requirement traceability from `spec.md` to the backlog therefore runs through exactly one path — `stories.json` and the task files. It holds, but it has no independent second path. **(D-15)**
- The register runs FR-001…FR-253 with 188 allocated and **65 numbers unallocated** (block allocation by epic). Every allocated id is claimed; nothing is lost. An id-density check run in ignorance will read 65 missing requirements. **(D-16)**

### 3.3 Acceptance criteria — including the known-unstable range

**Source set of record: §19 as written holds A1–A90 — 90 criteria `[V — read in full]`. The "96 criteria" figure carried into the normalized config is unsupported by the section text.** This is recorded in `spec.md` as NA-20 and is re-affirmed here.

| Check | Result |
|---|---:|
| Canonical A-ids cited across slice `acceptance_criteria` | **90** (A1…A90, contiguous) |
| A-ids in the source set never cited by any slice | **0** |
| Canonical A-ids cited that fall outside A1–A90 | **0** |
| Section-qualified A91+ ids cited | **11** (`§12.17-A91` … `§12.17-A101`) + `§18-A91`, `§18-A101` in prose |
| Slice-local `SL-<slice>-<n>` criteria | **180** |
| SL- ids not namespaced to their own slice | **0** |
| SL- ids duplicated across slices | **0** |
| SL- criteria with no statement | **0** |
| Declared criteria not cited in their own task file (after normalising `section ` → `§`) | **0** |
| Declared criteria whose **exact** `stories.json` string never appears in the task file | **11** (see D-09) |

`verification_method` histogram across all 300 declared criteria: `exit-code` 118 · `grep-assert` 73 · `manual-observation` 54 · `recompute` 29 · `hash-compare` 19 · `probe` 9 · `screenshot-diff` 4. **58 % of criteria (exit-code + grep-assert + hash-compare) are machine-adjudicated**, which is what makes the "human is the sole aesthetic judge / machines enforce only machine-checkable correctness" split operable rather than rhetorical.

**The A91+ range is unstable and every downstream citation of it is section-qualified.** See D-02 for the full three-way collision, which is wider than previously recorded.

### 3.4 Competency questions and evidence references

| Check | Result |
|---|---:|
| CQs of record in `domain-cqs.md` | **18** (CQ1–CQ18) |
| CQs cited by at least one slice | **18** |
| **Cited CQ ids that do not resolve** | **0** |
| CQ ids cited in task-file prose that do not resolve | **0** |
| CQs never cited by any slice | **0** |
| Lattice `cq` nodes | **18** — one per CQ |
| **Measured CQ coverage** | **18/18 = 100.0 %** against the ≥95 % target |
| Evidence-ledger entries | **88** |
| Entries cited by a slice `evidence_refs` | **22** |
| **Cited evidence refs that do not resolve** | **0** |
| `EL-` refs in task-file prose that do not resolve | **0** |
| Ledger entries never cited by a slice or a task file | **66** (see D-17) |
| `lattice_node_ids` in the ledger that do not resolve | **0** |

**Lattice structural integrity (computed):** 334 nodes, 546 edges, **0** dangling endpoints, **0** out-of-vocabulary node types, **0** out-of-vocabulary edge relations, **0** out-of-vocabulary tiers, **0** confidence values outside [0,1], **0** entries with an empty `source_refs`. All ten node types and all eight edge relations are exercised: `method` 114 · `metric` 56 · `risk` 35 · `standard` 34 · `entity` 20 · `anti_pattern` 19 · `cq` 18 · `process` 16 · `term` 12 · `pattern` 10; `uses` 157 · `measured_by` 133 · `constrained_by` 126 · `mitigates` 61 · `part_of` 23 · `contradicts` 19 · `depends_on` 17 · `implements` 10.

**Evidence quality:** tier distribution T1 37 / T2 17 / T3 6 / T4 3 / T5 25. Mean confidence 0.763, range 0.30–0.95, **13 entries below 0.5** — every one of them a schedule figure, an unbenchmarked carried-over threshold, or an unverified external surface, exactly as the standing rule requires. Mean `freshness_days` 1, max 8: compile-time-relative, **not** an external verification date, because no external source could be fetched during this pipeline.

### 3.5 Dependency graph

| Check | Result |
|---|---:|
| `depends_on` edges | **120** |
| Edges referencing a non-existent slice | **0** |
| **Cycles** | **0 — the graph is a valid DAG** |
| Edges pointing at an equal-or-later slice number | **0** |
| Isolated slices (no dependencies and no dependents) | **0** |
| Roots (empty `depends_on`) | **4** — S01, S02, S03, S06 (the independent Phase-0 probes) |
| Leaves (nothing depends on them) | **15** |
| Maximum transitive prerequisite depth | **42** |

Cycle detection was a real colour-marking DFS over the emitted graph, not an inspection. The zero result is computed.

**Sequencing spot-checks (computed transitive reachability):**

| Claim the plan makes | Verified? |
|---|---|
| Gate 16-A (S01) precedes the server port (S08), and therefore all server-dependent scope | **YES** |
| The O1 font policy probe (S02) precedes the Stage-A prompt (S16) | **YES** |
| The substrate spike (S03) precedes the pure renderer (S25) | **YES** |
| The channel-ceiling battery (S06) precedes envelope chunking (S17) | **YES** |
| The byte-reproducibility spike (S05) precedes the purity gates (S67) | **YES** |
| **The O4 topology spike (S04) precedes the editor shell (S29)** | **NO — S04 has zero dependents** (D-13, new) |

### 3.6 Demo reachability

| Demo | Slice | Direct prereqs | Transitive prereqs | Prereqs ordered **after** the demo |
|---|---|---:|---:|---:|
| Demo 1 — interview → prompt → ingest → one direction rendered static | **S28** | 5 | 21 | **0** |
| Demo 2 — live editable surface surviving ≥2 turn boundaries | **S40** | 6 | 28 | **0** |
| Demo 3 — gridlines + constraint drag + per-breakpoint overrides (D2's first exercise) | **S50** | 6 | 29 | **0** |
| Demo 4 — LOCK with two-build byte-equality, published, evidence-complete | **S72** | 2 | 30 | **0** |

**All four demos are reachable: for every demo, every one of its transitive prerequisites is ordered before it.** Demo count from `stories.json` = 4 = `totals.demo_slices`. (Counting demo-bearing *headers* in the task files returns 6, because S70 and S71 mark themselves `Demo 4 (feeds)` — see D-11.)

### 3.7 Backlog shape

| Dimension | Distribution |
|---|---|
| Type | diagnostic **6** · build **68** · demo **4** = 78 |
| MoSCoW | MUST **77** · COULD **1** (S49, the canvas tail) · SHOULD **0** · WON'T **0** |
| Size class `[I — ordinal, explicitly non-temporal]` | S **13** · M **46** · L **18** · XL **1** |
| Epics | **20** (E0–E19), zero with no slices |
| Stories | **26**, zero with an unknown epic, zero with an unresolvable `slice_ids` entry |
| Blocking flag | **1** — S01 only |
| Structural cross-references | slice→epic **0 unknown** · slice→story **0 unknown** · story→slice **0 unresolved** · slices absent from every story **0** · slice/story back-reference disagreements **0** |

`totals` declared in `stories.json` (20 / 26 / 78 / 6 diagnostic / 68 build / 4 demo) match the recount exactly.

**Effort posture (computed):** no task file publishes a day figure. Size class is ordinal and tagged `[I]` in all 78 header rows. The only effort figures anywhere in the pipeline are the carried §18/L1–L5 bands, and they are **inference, low confidence** wherever they appear.

**Language rule (computed):** every mention of Python across the 78 files is a prohibition (`No .py file may be created anywhere in the skill tree`), the sign-off-gated F4 launcher rung, or the in-estate `server.py` being ported away. **Zero task files propose new Python.** New code is TypeScript on Bun throughout.

---

## 4. Defect register

Every defect carried into this stage is recorded below with its **status**. **Nothing in this list was silently fixed.** Where an artifact owes an edit, the owner of that edit is named.

### 4.1 Defects carried forward from earlier stages

**D-01 — DEMO ID CONTRADICTION (plan.md owes the edit). Status: OPEN, wider than recorded.**
`plan.md` §3.2's demo table places Demo 2 at slice **S41** and Demo 3 at slice **S51**, while `stories.json` assigns them to **S40** and **S50**. Verified this stage: the disagreement is **four-for-four**, not two — `plan.md` also places Demo 1 at **S30** (vs S28) and Demo 4 at **S73** (vs S72). The 78 task files follow `stories.json` throughout, and `stories.json` ids are the ones the ACOS bridge step will convert into `planning/slices/`. **`plan.md` needs the edit; this stage did not make it.**

**D-02 — ACCEPTANCE-CRITERION ID COLLISION ABOVE A90. Status: OPEN, three-way (previously recorded as two-way).**
§19 as written holds **A1–A90 — 90 criteria `[V]`**; the "96 criteria" figure is **unsupported by the section text** (`spec.md` NA-20). Above A90 the source PRD defines the same ids in **three** places, not two:

| Set | Source location | Range | Example content |
|---|---|---|---|
| Set 1 | §7 (PRD line 1221 ff) | **A91–A97** | A91 forced-colors render; A92 `text-wrap: balance`; A93 pick-extension fields; A94 direction-hash agreement; A95 editor renders zero controls for `direction-slot`/`derived` rows |
| Set 2 | §12.17 consistency register (PRD line 2861 ff) | **A91–A101** | A91 `base`+no-`sm` compiles to `grid-column: 1 / -1` under `@media (max-width: 479px)` |
| Set 3 | §18 (PRD line 3980 ff) | **A91–A101** | A91 asset-library pane lists and filters by direction affinity |

Additionally, **§12.5's amendment note announces "new criteria A91–A99"** while **§12.17's own table runs A91–A101** — the announcing sentence understates its own table by two rows. All A91+ ids are **unstable until a renumbering pass** reconciles three sets. Downstream mitigation in force: every A91+ citation in `stories.json` and in the task files is section-qualified (`§12.17-A9n`, `§18-A9n`), so nothing built is ambiguous.

**D-03 — OPEN-ITEM ID COLLISIONS. Status: OPEN, four-way for O31 and O32 (previously recorded as two-way).**
Computed from the source PRD's own table rows:

| Id | Distinct meanings | Sections |
|---|---:|---|
| **O31** | **4** | §7.17.3 (20 artworks: total or per family?) · §12.17 (breakpoint boundaries 991/479 vs preview widths 768/390) · §16.5.1 (does `allowed-tools` omitting `Task` suppress a later `Task(general-purpose)` call?) · §18 (which O10 branch — A, A+ or B?) |
| **O32** | **4** | §7.17.3 (median byte size of a generated SVG / a direction's token file) · §12.17 (no wide/`xl` override tier in v1) · §16.6.3 (launcher-ladder decision) · §18 (raster artwork with no asset library) |
| **O33** | **3** | §7.17.3 (container-query `var()` rejection / `light-dark()` safety) · §12.17 · §18 |
| **O34** | **2** | §7.0.3 (two directions sharing a `vectorHash`) · §12.7 |
| **O35** | **2** | §7 (what were categories K and M?) · §12.17 |

**Rule in force: every citation must be `§section-On`.** The research QA report already recorded a four-way collision; the carried defect list understated it as two-way. A renumbering pass is a prerequisite for trustworthy traceability.

**D-04 — `04-site/coherence-ledger.json` IS AN INFERRED PATH `[I]`. Status: OPEN.**
`data-model.md` §3.21 names the `CoherenceLedger` entity but the §1 file map gives it no path — the string `coherence-ledger.json` appears nowhere in `data-model.md`. The path is used by **S51** (slot contracts / swap safety) and **S62** (inline-authored path / coherence debt). Either the data model gains the path or those two slices must stop asserting one. Recorded as an inference, not adopted as fact.

**D-05 — INBOX NAMING. Status: OPEN, canonical form chosen and stated.**
`FR-228` names the channel `commands.jsonl`; `data-model.md` §3.23 makes **`.wb/inbox.jsonl`** canonical with `commands.jsonl` recorded as an alias (`.wb/inbox.jsonl` (a.k.a. `commands.jsonl`)). **`.wb/inbox.jsonl` was treated as canonical throughout**; `spec.md`'s file table carries both spellings on one row. The FR text owes an alignment edit.

**D-06 — DROP-ALGORITHM BRANCH COUNTING. Status: OPEN, divergence recorded inside the slice.**
`FR-106` labels the three legal rejections `§11.2.1 AC7–AC9`, while `SL-S43-1` enumerates **nine** branches with the rejections as the ninth. S43's task file records this explicitly as an `Assumption (recorded)` and follows the nine-branch enumeration, giving each rejection its own test case `[I]`. The §11.2.1 normative drop algorithm is itself carried as NA-17 (it was absent from the technical requirements handed into this pipeline).

**D-07 — S2 WORDING CONFLICT. Status: OPEN, semantics stated, name not yet changed.**
§4 calls the mechanism a **"one-paste protocol"** (one paste per chunk) while §2.3 budgets **≤3 pastes per chunk, ≤6 chunks**. Resolution in force (`spec.md` OQ-37, S2 row): **≤3 is a retry budget, not the mechanism**; each extra paste is logged as a near-miss; **hitting ≤3 on a majority of chunks is a defect against §4, not a pass**. `spec.md` §1 already renames it "bounded-paste protocol" in prose; §4 owes the same rename or an explicit retry-semantics statement.

**D-08 — SKIP-LINK COMPONENT ABSENT FROM THE INVENTORY. Status: OPEN, one row owed.**
Lock-time check **11a** (skip-link presence and first-tab-order) requires a skip-link component that the component inventory does not contain. **One row, single variant, owed.** The v1 component target carried in `stories.json` `scope_of_record` is **88 rows / 675 variants** precisely because it adds this one row to DECISIONS item 2's 87/674 — the addition is recorded, the inventory edit is not yet made.

**D-09 — ACCEPTANCE-CRITERION ID SPELLING DRIFT (new this stage, minor). Status: OPEN.**
Eleven ids are spelled `section 12.17-A9n` in `stories.json` and `§12.17-A9n` in the corresponding task file: S19 (A101), S24 (A92, A98), S26 (A91), S36 (A97), S37 (A100), S38 (A95), S39 (A96), S59 (A99), S67 (A93, A94). Every one resolves after normalisation; **none is missing and none is wrong**, but a byte-exact traceability join fails on all eleven — the precise failure mode the id register exists to prevent. One spelling should be chosen before the bridge step runs.

**D-10 — PERFORMANCE CRITERIA A66/A67 INCONSISTENT WITH THE CANONICAL THRESHOLD. Status: OPEN, subordination stated, §19 edit owed.**
**NFR-04 / §13.4 gate 20 is the canonical threshold statement:** LCP ≤2.5s · CLS ≤0.1 (internal stretch 0.05) · **INP ≤200ms** (or TBT ≤600ms floor / 300ms aspirational as proxy) · **pre-LCP transfer ≤1.5–2MB** (not total page weight), median-of-3, mobile, simulated Slow-4G + 4× CPU. **A66 omits INP entirely and A67 states a flat ≤2MB.** Both are explicitly recorded as **subordinate and inconsistent** in `spec.md` (NFR-04 row, NA-16) and in `tech_prd.md`. **A §19 edit is owed.**

**D-11 — DEMO HEADER OVER-CLAIM (new this stage, cosmetic). Status: OPEN.**
S70 and S71 carry `| Phase / Demo | Phase 5 / Demo 4 (feeds) |` while their `stories.json` `demo` field is `null`. A machine count of demo-bearing slices returns 6 from the task files and 4 from `stories.json`. `stories.json` is the record; the headers should read `feeds Demo 4 (S72)`.

**D-12 — COMPONENT-INVENTORY VOLUME SPREAD. Status: OPEN, three figures live simultaneously.**

| Figure | Meaning | Marker |
|---|---|---|
| **216 rows / 1,228 variants** | the **volume of record**, computed from §8.2/§8.3's own table | `[V]` |
| **87 rows / 674 variants** | the **v1 cut candidate** (DECISIONS item 2) — **UNSIGNED** | `[I]` on the cut mapping |
| **~50 rows / ~430 variants** | **stale sizing** that §18's timeline and §13's gate budgets were built against | `[I]`, superseded |

`stories.json` carries **88 / 675** as the working v1 target — 87/674 plus the D-08 skip-link row — and states that "the v1 cut list must be regenerated mechanically from the priority column". Until DECISIONS item 2 is signed, **the v1 component set is not a decided number**, and §18's timeline and §13's gate budgets remain sized against a figure roughly one quarter of the volume of record. This is the largest open scope discrepancy in the pipeline.

### 4.2 New defects found by this analysis

**D-13 — THE O4 TOPOLOGY ADR GATES NOTHING MECHANICALLY. Status: OPEN, new.**
`S04` (the O4 topology spike and its ADR) has **zero dependents** in the 120-edge dependency graph. The editor shell `S29` depends on `S25` and `S08` only. Both `plan.md` and the task prose state the binding rule — until the O4 ADR lands, only the topology-independent invariants **I1–I6** may be built — but that rule is expressed nowhere in `depends_on`, so a mechanical scheduler is free to build the entire editor before the topology is chosen. This is the exact inverse of `S01`, which is correctly wired as a transitive prerequisite of `S08` and therefore of all server-dependent scope. **Recommended edit: add `S04` to `S29`'s `depends_on`.** Not made here — this stage does not modify existing artifacts.

**D-14 — `plan.md` CITES A102 AND A112, WHICH EXIST IN NO CRITERION SET. Status: OPEN, new.**
All three A91+ sets stop at **A101**. `plan.md` prose cites **A102** and **A112**. Neither appears in `stories.json` or in any task file, so no slice is built on them, but they are unresolvable ids in a planning artifact and must be renumbered or removed as part of the D-02 pass.

**D-15 — TRACEABILITY HAS ONE PATH, NOT TWO (new this stage). Status: OPEN, structural.**
`plan.md` cites 4 FR ids; `tech_prd.md` and `data-model.md` cite none. Every requirement-to-backlog link therefore runs through `stories.json` and the task files alone. The link is provably complete (188/188, both directions, zero double-claims) but it has **no independent second path**, so a single systematic error in `stories.json` would be invisible to a cross-check.

**D-16 — REQUIREMENT-ID DENSITY LOOKS LIKE LOSS (new this stage, informational). Status: RECORDED.**
The FR register runs FR-001…FR-253 with **188 allocated and 65 numbers unallocated** (block allocation by epic). Nothing is lost — every allocated id is claimed exactly once — but any density check run without this note will report 65 missing requirements.

**D-17 — EVIDENCE-LEDGER CITATION COVERAGE IS 25 % (new this stage, informational). Status: RECORDED.**
22 of 88 ledger entries are cited by a slice or a task file; **66 are not**. Every cited ref resolves. The uncited majority is research-level evidence (market history, framework rejections, licence texts, harness facts) that informs `spec.md` rather than any single slice. Consequence: **the ledger cannot be used as a completeness check on the backlog** — absence of a citation says nothing about whether a slice honours the evidence.

**D-18 — MoSCoW IS EFFECTIVELY FLAT (new this stage). Status: OPEN, structural.**
**77 of 78 slices are MUST; exactly one (S49, the canvas tail) is COULD; SHOULD and WON'T are unused.** The backlog therefore offers the schedule exactly **one** trade-back-out lever, which sits uneasily beside the plan's framing of the canvas tail as merely "the first candidate to trade back out" — implying there are others. There are not. Honest cause: DECISION-1 option B made nearly everything mandatory. Consequence: **scope relief cannot be found in the backlog; it can only be found in the §18 sign-off table** (D-19). This should be stated to the human before build start rather than discovered at day 20.

**D-19 — S48 (FREE-POSITION ESCAPE HATCH) HAS NO ORDERED PROCEDURE (new this stage). Status: OPEN.**
S48 is the only one of 78 task files with **no numbered step list at all**; its execution sequence must be inferred from the In-scope paragraph and the Definition of Done. It is also the slice with the highest residual risk in the canvas epic — the one whose own text states that sibling anchoring is **UNPROTOTYPED with no known mitigation** and that the R9 residual stands unsolved. The slice most in need of an ordered procedure is the one that lacks it. (S43 and S50 also lack the literal `**Steps.**` label but do carry numbered lists, of nine and five steps respectively.)

**D-20 — S72's REQUIREMENTS HEADER CONTRADICTS THE DEMO CONVENTION (new this stage, minor). Status: OPEN.**
`S72-demo-4-locked-published-evidence` carries `| Requirements | FR-200, FR-216 |` while its `fr_ids` is empty — the deliberate demo convention that S28, S40 and S50 all follow and on which the exact 188-FR partition depends. FR-200 is owned by S66 and FR-216 by S71, so nothing is orphaned or double-claimed, but the header reads as a third claim. Should read `via S66, S71`.

**D-21 — `A<n>` IS OVERLOADED ACROSS THREE NAMESPACES IN THE SOURCE (new this stage). Status: OPEN.**
The bare token `A<n>` denotes three different things in the source PRD: **§5's interview-bank question ids** (A1–A5 observed as table rows), **§8's accessibility requirement rows** (A1–A6 observed), and **§19's acceptance criteria** (A1–A90). Downstream, an unqualified `A<n>` always means §19 — but **no artifact states that rule**, so a reader arriving at a task file from §5 or §8 can mis-resolve a low-numbered citation. The A91+ pass (D-02) should state the namespace rule for A1–A90 at the same time.

---

## 5. THE BUILD-START GATE — §18's four unsigned sign-off rows

**This is the single most consequential finding in this report, and it is not a defect in any emitted artifact.**

§18's own precondition is explicit: **nothing in v1 may be built until every sign-off row is resolved.** DECISION 1 (2026-07-26, option B) resolved rows **4(a)**, **4(b)** and consequentially **7**. **Four rows remain UNSIGNED:**

| Row | Subject | State |
|---|---|---|
| **4(c)** | rich text is v2 | **UNSIGNED** |
| **4(d)** | one direction only / no cross-direction swaps | **UNSIGNED** |
| **4(f)** | the editor still lacks zoom, pan, rulers and multi-select | **UNSIGNED** |
| **6** | charts partial | **UNSIGNED** |

**Stated plainly: build start is gated on these four signatures.** The backlog is complete — 78 slices, an exact requirement partition, a valid DAG, four reachable demos — **and unstartable at the same time.** Every hour spent on S01 before these are signed is spent against a v1 scope that four unresolved questions can still move.

Three of the four bear directly on the emitted backlog:

- **4(d)** one-direction-only is the premise of **S51** (superset-only swap offers) and the reason cross-direction swaps are out of v1. Reversing it re-opens R10 (re-skin destroys what the user liked; transplant destroys the system), for which the source records **no good implementation**.
- **4(f)** is precisely **S49**, the only COULD in the backlog (D-18). Signing it as accepted-absent removes the sole trade-back-out lever from the schedule; refusing it moves S49 to MUST and enlarges the largest and riskiest epic.
- **6** charts-partial is **S61** (build-time SVG, ≤4 mark types) and the dataviz sub-token work in **S60/S13**. It interacts with the recorded structural fact that **three brand hues cannot yield a 6-series colourblind-safe categorical palette**.

A second, independent gate sits underneath these: **DECISIONS item 2 (the v1 component set) is also UNSIGNED** (D-12), and §18's timeline and §13's gate budgets are sized against a figure roughly one quarter of the volume of record. Signing the four §18 rows without settling item 2 leaves the schedule baselined on a stale number.

---

## 6. Protocol-stack conformance (§0.1–§0.9)

| Protocol | Requirement | Observed | Verdict |
|---|---|---|---|
| §0.1 Three-agent pattern with LCE | PM/Dev/QA in every task file; PM slices carry objective, scope, guardrails, allowed files, steps, DoD | 78/78 carry all three roles; 75/78 carry all six LCE elements (D-19) | **CONFORMS** with 3 exceptions |
| §0.1 Dev evidence bundle | seven numbered sections | 78/78 name a seven-part bundle | **CONFORMS** |
| §0.1 QA zero-trust | assumes Dev did not do the work; recomputes; may reject | 78/78 name at least one explicit rejection condition; recompute/hash-compare used 48 times | **CONFORMS** |
| §0.1 `slice.yaml` mapping | DoD authored to map onto `acceptance_criteria` + `verification_method` | 78/78 carry the mapping line | **CONFORMS** |
| §0.2 Four-phase domain compilation | DLG → lattice expansion → evidence ledger → agent emission | all four emitted; brief, 18 CQs, 334-node lattice, 88-entry ledger | **CONFORMS** |
| §0.2 CQ coverage ≥95 % | measured, not asserted | **100.0 % (18/18)**, computed under the definition that a CQ must have a method neighbour and reach a metric and a standard within two hops | **CONFORMS** |
| §0.3 Diagnostic protocol | PRD space for diagnostics before locking solution requirements; ≥1 diagnostic slice | `spec.md` §2 Diagnostics present; **6 diagnostic slices** (S01–S06), all ordered ahead of all 68 build slices | **CONFORMS** |
| §0.4 Evidence ledger | schema §2.4 exactly | 88 entries, every required key, zero schema violations | **CONFORMS** |
| §0.4 CAGE encoding | exact headers; ≥1 full `BLOCKER→TOOL→FINDING→DECISION→ARTIFACT→OUTCOME→PATTERN` chain | `cage_preeng_nodes.csv` 11 columns / 40 rows; `cage_preeng_edges.csv` 4 columns / 57 rows; the N001→N007 chain is complete and labelled, and three further partial chains are present | **CONFORMS** |
| §0.5 Agent performance metrics | define SPD, QAP, TER, UAPS; name the instrumentation location | defined in §8 below and carried by **S78**; instrumentation points at `.acos/metrics/agent-completions.log` + `AGENT-METRICS.md` | **CONFORMS** |
| §0.6 Bloat management | Active / Review / Burn Pile; annotate canonical candidates; delete nothing | §9 below | **CONFORMS** |
| §0.7 Learning capture | `## Dev Learnings` + `## QA Learnings` on every slice; not Done until updated | 78/78 present, 78/78 non-trivial, and every one states the "Not Done until filled" rule with named required content | **CONFORMS** |
| §0.8 Vertical slices and demos | early slices deliver user-visible value; named Demo 1–4 checkpoints | 4 demo checkpoints, all reachable (§3.6); Demo 1 lands at S28 of 78, i.e. **36 % through the backlog** | **CONFORMS** |
| §0.9 Orchestration and edge constraints | durable execution, human-in-the-loop nodes, observability, role→node mapping | `tech_prd.md` TR2/TR20/TR21; SSE + inbox + blocking `tail -f`; resume-from-disk in **S73**; `verify.ts`/`doctor.ts` in **S74** | **CONFORMS** |

**One conformance observation, not a defect.** Demo 1 — the first user-visible increment — lands at slice **S28 of 78**. Twenty-seven slices produce infrastructure before anything renders. This is defensible: six are disqualifying probes and the rest are the generative pipeline that Demo 1 *is*. But under a strict vertical-slice reading, the first 27 slices are not independently demo-able, and the plan should say so rather than imply otherwise.

---

## 7. Traceability chain — end to end

```
business objective / user problem  (feature config: G1–G8, P1–P20)
        │
        ▼
spec.md §4.1  ── 188 FR ids ──────────────────────────────────┐
        │                                                      │
        ▼                                                      │
plan.md (phases, sequencing) + tech_prd.md (TR1–TR21) + data-model.md
        │        └─ prose references only; 4 FR ids cited total (D-15)
        ▼                                                      │
stories.json ── 20 epics · 26 stories · 78 slices ─────────────┤
        │        188 fr_ids, exact 1:1 partition ◄─────────────┘
        │        90 canonical criteria + 180 slice-local + 11 §-qualified
        │        18 CQ refs · 22 evidence refs · 120 DAG edges
        ▼
tasks/*.md ── 78 files · PM / Dev / QA / Dev Learnings / QA Learnings
        │        every declared FR and criterion restated in prose
        ▼
[ ACOS bridge step — NOT this worker ] → planning/slices/<id>/slice.yaml
        │        acceptance_criteria + verification_method
        ▼
/acos-execute-slice under hook enforcement → .acos/evidence/<date>/<slice>/
```

Every arrow above was verified in both directions where both directions are meaningful. The one weak link is annotated: `plan.md`/`tech_prd.md`/`data-model.md` do not carry FR ids, so the middle tier cannot independently corroborate the `spec.md` → `stories.json` mapping (D-15).

---

## 8. Agent performance metrics — definitions only (§0.5)

These are **defined, not computed**. No value is asserted anywhere in this pipeline.

**Production**
- **SPD — Story Points Delivered.** Qualitative approximation. Unit of account: the slice, weighted by its ordinal `size_class` (S/M/L/XL). `size_class` is **ordinal and explicitly non-temporal `[I]`** — it must never be converted to days without a measurement.
- **QAP — Quality-Adjusted Productivity.** `QAP = (Delivered_Value × Quality_Score) / (1 + Rejection_Count)`. `Rejection_Count` is the number of times the zero-trust QA section rejected the slice back to rework. `Quality_Score` is the fraction of the slice's declared acceptance criteria passing on the first QA pass.

**Efficiency**
- **TER — Token Efficiency Ratio.** Artifacts produced per 1K tokens consumed. For pre-engineering, "artifact" is a file written to the feature directory that parses and passes its structural check.
- **Volume per unit cost.** LOC (build slices) or bytes (pre-engineering slices) per unit cost, only where cost information exists. Absent cost data, this metric is **not** estimated.

**Composite**
- **UAPS — Universal Agent Performance Score.** `UAPS = 0.3×Quality + 0.4×Efficiency + 0.3×CostEffectiveness`.

**Instrumentation plan.** ACOS already logs agent identity (`agent_type`, `agent_id`) to **`.acos/metrics/agent-completions.log`**; that is the primary sink. Slice-level inputs (rejection counts, criteria-passed fractions, artifact counts) are recorded in **`AGENT-METRICS.md`** inside the project, authored by **S78 (`S78-agent-metrics-and-learning-capture`)**, whose scope is exactly this scaffolding plus the Dev/QA learnings sweep. Per-slice evidence bundles under `.acos/evidence/<date>/<slice-id>/` are the raw evidence these metrics are computed from later.

---

## 9. Bloat management and canonical candidates (§0.6)

**Nothing is deleted. This section only annotates.**

### Active — recent and needed for the next action
`spec.md` · `plan.md` · `tech_prd.md` · `data-model.md` · `stories.json` · all 78 `tasks/*.md` · `domain-lattice.json` · `evidence-ledger.json` · `domain-cqs.md` · `research_qa_report.json` · `planning_qa_report.json` · `tasks_qa_report.json` · `analysis-report.md` · both CAGE CSVs.

### Review — canonical-example candidates
Artifacts worth promoting into the estate as reusable exemplars, on the strength of a property this run can point at:

| Artifact | Why it is a canonical candidate |
|---|---|
| **`tasks/S01-gate-16a-and-launcher-rung.md`** | The cheapest-disqualifying-probe-first pattern, fully expressed: a sub-hour experiment that decides buildability, with a QA section that rejects a same-turn 200 as proof of life. The transferable shape for any harness-dependent product. |
| **The E0 spike suite (S01–S06) as a set** | Six diagnostic slices, all ordered ahead of all 68 build slices, each producing an ADR. This is §0.3's diagnostic protocol made operational rather than decorative. |
| **`stories.json`'s `scope_of_record` block** | Six contested counts (component inventory, editor rows, interview bank, purity gates, lock checks, acceptance criteria) each recorded with its marker, its source section and its rival figure. It is why the 15 non-blocking issues in each QA report are auditable. |
| **`tasks/S43-drag-to-place-and-drop-algorithm.md`** | Nine separately-tested branches for one interaction, with the FR-106 divergence recorded as an `Assumption (recorded)` inside the slice rather than resolved behind the reader's back. |
| **`tasks/S48-free-position-anchored-offset.md`** (content, not structure) | Carries a `**Stated limit, not solved.**` block naming an UNPROTOTYPED strategy with no known mitigation. Stating the limit inside the slice that would have to solve it is the honest alternative to a mitigation paragraph. Its missing step list (D-19) is a defect in an otherwise exemplary file. |
| **`evidence-ledger.json`'s low-confidence discipline** | 13 of 88 entries below 0.5 confidence, every one a schedule figure, an unbenchmarked threshold or an unverified external surface. The rule "every schedule figure is inference with low confidence" is visible in the data, not just in the prose. |

### Burn Pile — safe to archive later, delete nothing now
`_deterministic_prompt.md` (124,549 bytes — the compiled worker program; provenance value only once the run is complete) · `_runner_config.json` (231,012 bytes) · the four `_range?-slices.json` convenience extracts (99,068 bytes total — pure derivatives of `stories.json`, regenerable at any time) · `_coverage-computed.txt`.

These total roughly **455 KB of the feature directory** and are all either regenerable or single-use scaffolding. They should be archived **after** the bridge step runs, not before — the range extracts are cheap re-reads for whatever consumes `stories.json` next.

---

## 10. Assumptions carried forward

The 42 open questions normalized into this pipeline were **adopted as defaults and not re-decided**, per the binding execution instruction. They are recorded in full in `spec.md`'s `## Open Questions` section (OQ-01 … OQ-42) and are not restated here. The ones that bear directly on the emitted backlog:

| Assumption | Where it binds |
|---|---|
| DECISIONS item 2 defaulted to re-baselining at 87/674, radio group and toggle switch non-demotable — **UNSIGNED** | D-12; S51–S53 volume |
| DECISIONS item 4 defaulted to **Branch A+** (single page, `pages[]` of length 1, page-scoped ops from day one) — with the recorded caveat that item 4's *prose* argues Branch B behaviour while its *label* says A+ | S24, S36; if B was intended, v1 L3a roughly doubles `[I, low confidence]` |
| DECISIONS item 5 defaulted to running the reproducibility spike first; normalised comparison is the documented, **D3-weakening** fallback and itself needs sign-off | S05 → S67; success criterion S4 |
| DECISIONS item 6 defaulted to parent-edge and grid-cell anchors only; sibling anchoring held behind an **UNPROTOTYPED** prototype | S48 (D-19) |
| §17-O4 topology defaulted to building only invariants I1–I6 until the spike lands | S04 — **not enforced by the graph** (D-13) |
| §17-O5 / Gate 16-A defaulted to the first passing rung, preferring F3; F4 and F5 each require explicit sign-off | S01 |
| §17-O1 defaulted to assuming the artifact CSP **blocks** the WOFF2, mandating pre-subsetted base64 `data:font/woff2` | S02 → S15/S16 |
| §16.5.1-O31 defaulted to designing v1 so **nothing** depends on mid-skill `Task` availability | S07, S13, S62 (inline execution) |
| §17-O2 defaulted to computing chunking from measured artifact sizes at runtime, not from any published ceiling | S06 → S17 |
| §18's timeline, v1 scope-in list and §13's gate budgets defaulted to **STALE and re-baselined**; every resulting figure is **inference, low confidence** | D-12; the whole schedule |
| The ACOS vision document (`memory/source-of-truth/vision-document.md`) was **not consulted**; the signed-off PRD, `DECISIONS.md` and `memory/decisions/` (D1–D4) are the authoritative product input | whole pipeline |

**New assumptions recorded by this stage:**

- **Assumption (new).** `stories.json`'s section-qualified `section 12.17-A9n` ids and the task files' `§12.17-A9n` ids denote the same criteria; the two spellings were treated as equivalent for coverage purposes (D-09). If the bridge step joins on the exact string, all eleven will fail.
- **Assumption (new).** §12.17 is the table that §12.5's amendment note refers to when it says "new criteria A91–A99 **below** are appended"; on that reading the §12.5 announcement and the §12.17 table are one set, understated by two rows, rather than two further colliding sets (D-02).
- **Assumption (new).** The 65 unallocated FR numbers between FR-001 and FR-253 are deliberate block allocation by epic, not lost requirements. Evidence: every allocated id is claimed exactly once and no artifact cites an unallocated id (D-16).
- **Assumption (new).** S70's and S71's `Demo 4 (feeds)` header markers are annotations, not demo claims; `stories.json`'s `demo: null` is authoritative (D-11).

---

## 11. CAGE session encoding

`cage_preeng_nodes.csv` (40 nodes) and `cage_preeng_edges.csv` (56 edges) encode this pre-engineering session per §0.4, with the exact required headers.

The **required full chain** is present and labelled in the edge notes:

```
N001 BLOCKER   Turn-boundary server death
   → N002 TOOL      Gate 16-A probe (F1–F5 ladder)
   → N003 FINDING   Server survival is unproven in pure TypeScript
   → N004 DECISION  Gate 16-A blocks all server-dependent scope
   → N005 ARTIFACT  tasks/S01-gate-16a-and-launcher-rung.md
   → N006 OUTCOME   Buildability decided in under an hour [I]
   → N007 PATTERN   Cheapest disqualifying probe first
```

Three further partial chains are encoded: silent truncation → envelope manifest → the-prompt-is-a-lottery-ticket → Local Regeneration Mode; DOM-as-truth → `layout.json`-as-truth → re-render LOCK; and market-history → DECISION-1(B) → E9 → Demo 3 → retire-risk-by-scheduling. Two anti-patterns are recorded (`N027` a gate that fails spuriously gets disabled by whoever is shipping; and the rejected autonomous-aesthetic-judging architecture, carried as the constraint `N028`). Four nodes are labelled `canonical-candidate`, matching §9's Review list.

---

## 12. Verdict

| Question | Answer |
|---|---|
| Are all required pre-engineering artifacts present? | **Yes** — every artifact in §1 of the command spec except `agent_instructions/`, which a concurrent sibling agent owns. |
| Did any ERROR gate fire? | **No.** Both upstream QA reports are `APPROVED`. |
| Is the backlog complete and internally consistent? | **Yes, mechanically.** 78/78 slices↔task files; an exact 188/188 requirement partition in both directions with zero double-claims; zero unresolved CQ or evidence refs; a 120-edge DAG with zero cycles and zero dangling references; four reachable demos. |
| Are the acceptance criteria stable? | **A1–A90 yes `[V]`. A91+ no** — three colliding sets (D-02), mitigated downstream by section-qualified citation, unstable until a renumbering pass. |
| Are there orphan requirements? | **None in either direction.** |
| Is anything blocking? | **Yes, and it is not in these artifacts.** §18's sign-off rows **4(c), 4(d), 4(f) and 6 are UNSIGNED**, and §18's own precondition bars any v1 build until every row is resolved. **DECISIONS item 2** (the v1 component set) is likewise unsigned, leaving the schedule baselined on a stale figure. |
| What should be fixed before the bridge step runs? | In order: (1) the four §18 signatures; (2) `plan.md`'s demo slice ids, four-for-four (D-01); (3) the A91+ / O31–O35 renumbering pass, including A102/A112 (D-02, D-03, D-14, D-21); (4) one spelling for the section-qualified criterion ids (D-09); (5) `S04` wired into `S29`'s `depends_on` (D-13); (6) a step list for S48 (D-19). |

**Overall: the pre-engineering artifacts for `001-website-builder` are complete, mutually consistent, and mechanically verified. The defects that remain are inherited contradictions in the signed-off source, one missing dependency edge, one id-spelling drift and three structural gaps in three task files — every one recorded above with its status and its owner, and not one of them silently fixed.**

The honest summary is one sentence: **the plan is ready and the build is not permitted to start**, because four signatures that §18 itself declares mandatory have not been given.

