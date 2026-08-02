# Implementation Plan — Website Builder (`001-website-builder`)

**Command:** `/preeng.plan`
**Inputs:** `{feature_id: "001-website-builder", spec_path: "spec.md", research_path: "research.md"}` (absolute feature directory: `/Users/zee/Documents/Vibe Coding/ACOS 3.0/Website Builder/planning/preeng/001-website-builder/`)
**Preconditions checked:**

| Precondition | Result |
|---|---|
| `spec.md` exists | **PASS** (140,031 bytes, 948 lines) |
| `research.md` exists | **PASS** (25,633 bytes, 246 lines) |
| `research_qa_report.json.qa_status != "REJECTED"` | **PASS** — status is `APPROVED` with 15 recorded non-blocking conditions |

**Outputs of this command:** `plan.md` (this file), `tech_prd.md`, `data-model.md`, `planning_qa_report.json`.

**Marker discipline (inherited, normative).** `[V]` verified against a named, read source. `[I]` inference. `[U]` unsourced / explicitly low-confidence. Markers are never promoted. **Every schedule, effort, duration and volume estimate in this plan is `[I]` with low confidence**, and this plan deliberately declines to synthesise a single v1 day total (see §6.4).

**Language law.** All new product code is **TypeScript run by Bun**. No new Python anywhere except the sign-off-gated F4 launcher rung. This plan proposes no Rust (nothing here is performance-critical or needs a single binary).

---

## 1. What this plan commits to

### 1.1 The five fixed decisions

| Id | Decision | Planning consequence |
|---|---|---|
| **D1** | ~10 coherent whole design directions; 20 artworks per direction; 10 variants per component on demand (12 for hero, CTA band, card, badge, feature grid, pricing); derived values are **computed from anchors, never picked** | E6 emits `pickable:false` on every derived token; the editor renders no control for them (A15, A24) |
| **D2** | Constraint-based dragging; gridlines are the snap target; per-component free-position escape hatch. **Not** free x/y layout | E9 exists, is v1, and is sub-sliced in dependency order |
| **D3** | LOCK is a **re-render** with `editor:false`, reversible, provably zero editor runtime | E14 is a compiler, not a copier; UNLOCK = restart the design server |
| **D4** | Motion is a design-system item inside draggable art-style containers | Motion is `props.motion` on an `ArtContainer` node — one code path, not a parallel subsystem |
| **DECISION-1 (2026-07-26, option B)** | **v1 ships gridlines AND full constraint dragging** | §18's editor-lite v1 scope is **REJECTED**; §18's timeline, its v1 scope-in list and §13's gate budgets are **stale and re-baselined here**; R47 is retired |

### 1.2 The scope of record this plan settles

The three source volumes disagreed. This plan settles them once, and every downstream artifact (`stories.json`, `tasks/*.md`, `tech_prd.md`, `data-model.md`) uses these numbers and no others.

| Dimension | Volume of record | v1 build target | Basis |
|---|---|---|---|
| **Component inventory** | **216 rows / 1,228 variants** `[V — §8.2 computed from §8.3 as written; NA-02]` | **88 rows / 675 variants** `[I on the cut mapping]` | 87 rows / 674 variants is DECISIONS item 2's re-baseline (OQ-01), **plus one new row**: the skip-link component that §13.4 gate 11a requires and the inventory does not contain (research F6). See NA-B08 |
| **Editor feature rows** | **116 rows** (56 v1 / 55 v2 / 5 v3 under editor-lite) `[V — §10, mechanically recounted; NA-12]` | **66 of 116** `[I]` | 56 editor-lite v1 rows **+ the 10 canvas rows NA-12 names as promoted** by DECISION-1 B (real-grid overlay, snap engine, smart guides, align tools, padding/gap handles, drag-to-place, span resize, keyboard nudge, full cascade UI, free-position hatch). Inside NA-12's 65–70 band. No recount was performed — see NA-B09 |
| **Interview bank** | **90 questions** `[V — §5 row-count self-audit; NA-01]` | 90 authored; **~45–55 Tier-1 asked in fast mode** `[I]` | A3 ("≤45 answered") is recorded as **unachievable as written**; §5 itself says move it to ≤55 or cut the bank |
| **LOCK purity gates** | **8** `[V — §12.5; NA-03]` | 8 | Not five. Gates 6/7/8 (unresolved references, design-time origins, verify-clean) are the additions |
| **Lock-time checklist** | **32 checks** (28 base + 4a, 11a, 13a, 23a) `[V — §13.4; NA-04]` | 32 | 11a, 13a and 23a each carry an unfinished cross-section build prerequisite (research F6) |
| **Acceptance criteria** | **A1–A90 (90)** `[V — §19 read in full; NA-20]` | 90 mapped + two colliding A91+ sets carried section-qualified | The "96" figure is unsupported by the section text. **§12.17 enumerates A91–A101 (11 doc/persistence criteria) and §18 enumerates a disjoint A91–A101** — see NA-B05 |
| **Security controls** | **8 controls** `[V — §12.12 read this pass]` | 8 | The carried "six-control posture" is understated: `Access-Control-Allow-Origin` exact-never-`*`, **`Host`-header validation** and the security-header/CSP row are additional. **Host validation, not the bearer token, is the anti-DNS-rebinding control.** See NA-B02 |
| **Coherence lints** | **Versioned set, not a fixed count** `[NA-05]` | Required members named by name | Minimum: elevation-model lint (border-only ⇒ zero shadow tokens, A17), logical-properties-only lint, and §7's lints 7–10 |

### 1.3 What "done" means for v1

The v1 ship bar is `spec.md` §Metrics: **S1** (interview ≤30 min — at risk against the honest 25–35 min estimate), **S2** (bounded pastes), **S3** (zero editor strings in `dist/published/**`), **S4** (two-build equality, contingent on the reproducibility spike), **S5** (all Tier-1 lock gates pass), **S6** (the human can name why), **S8** (zero unlicensed shipped assets or fonts), **S9** (repeat use, measured from local session files in a 90-day window). **S7 is v2 and is not in the bar** — a v1 sign-off checklist containing S7 unqualified is invalid.

---

## 2. Architecture of record, and what is deliberately still open

### 2.1 Shape

A thin router `SKILL.md` (9 phases) + TypeScript scripts on Bun + **one** local server + a browser editor. Explicitly **not** an autonomous multi-agent generation loop: the expensive loop in this product is a human sitting in a browser, and NG1 forbids AI aesthetic judging. The prior swarm report's rubrics, anti-slop lint, stack analysis, licensing policy, performance gates and capture protocol are reused; **its VLM judge loop is not ported under any circumstances.**

### 2.2 Committed invariants (build these before the spikes land)

| Id | Invariant |
|---|---|
| **I1** | **One writer.** `wb-server` is the only process that writes the doc-owned set |
| **I2** | The route contract: `GET /doc` (ETag/304), `POST /ops` (typed ops, 409 on stale ETag), `GET /events` (SSE, ~15s keepalive), `POST /variants`, `POST /lock`, `POST /internal/*`, static, health |
| **I3** | Semantic ops only — never a raw file write, never a raw JSON Patch, never a path in a request body |
| **I4** | Preview isolation is a **requirement, not a mechanism**: a capture of the preview contains zero editor chrome |
| **I5** | The editor survives a preview-process restart without losing unsaved state |
| **I6** | The preview substrate is **open**: nothing may hard-depend on one framework. If the substrate spike resolves to plain generated HTML, "process 1" collapses to a static file watcher plus reload |

### 2.3 Deliberately open, with a spike attached

| Open item | Default adopted (do not re-decide) | Spike |
|---|---|---|
| §17-O5 / Gate 16-A — does a pure-TS detached spawn survive the turn boundary? | Run Gate 16-A **first**; take the first passing rung F1→F5, preferring F3 (POSIX `sh`) because it keeps 100% of the server in TypeScript. F4/F5 each need sign-off; if both are refused, **the browser-editor premise must be rescoped** | S01 |
| §17-O4 — single-origin proxy vs two-origin iframe + postMessage | Build only I1–I6 until the ADR lands; Candidate A is documented so the spike has something to test, and is **not** the architecture of record | S05 |
| §17-O8 — Astro vs plain generated HTML | Substrate-agnostic construction (I6). The user's own estate ships plain generated HTML | S04 |
| §17-O1 — does the generation surface render a web font? | Assume it **blocks**; mandate pre-subsetted base64 `data:font/woff2`. 60-second test **before** the Step-2 prompt spec is written | S03 |
| §12.5-O33 — bundler byte reproducibility | Spike before committing S4; documented fallback is normalised comparison with an enumerated, individually justified exception set, and it **weakens D3's proof and needs sign-off** | S06 |
| §16.5.1-O31 — mid-skill `Task` availability | Design v1 so **nothing depends on it**; both role prompts run inline in the main session. ~10-minute probe, not a v1 blocker | S06b (folded into S06's sibling slice S07) |
| §12.16-O35 — semantic cross-direction variant matching vs canonical fallback in `wb migrate` | **New this pass (NA-B04).** Default = option (a) canonical fallback only, always reviewed — the section's own stated v1 choice | — (v2 question) |

**Every open-question id is cited section-qualified (`§12.3-O31`, `§16.6.3-O32`, …) throughout this plan.** Bare `O31`/`O32`/`O33`/`O34` are ambiguous across four collisions (NA-08).

---

## 3. Delivery method

### 3.1 The three-agent pattern with Lean Context Engineering (protocol §0.1)

Every slice is executed by three roles, and the roles are walled from each other by construction:

- **PM (planner/specifier)** — writes the slice: one narrow objective, explicit in-scope/out-of-scope, an **allowed-files list**, step-by-step instructions, and a Definition of Done naming required artifacts, required validation and evidence-bundle expectations. PM never implements.
- **Dev (executor)** — executes the assigned slice **exactly**: no scope expansion, only allowed files. Produces a 7-part **Evidence Bundle** (implementation summary; requirements traceability; code/structural quality evidence; functional testing; security/compliance; operational/runtime; self-assessment with confidence and known limitations).
- **QA (zero-trust verifier)** — assumes Dev did **not** do the work correctly. Independently verifies scope respect against the allowed-files list, **recomputes** rather than trusts (hashes, counts, contrast ratios, grep results, exit codes), and confirms every acceptance criterion and evidence gate. QA may **reject** back to rework. A crashed or inconclusive verification blocks exactly like a reject.

**ACOS mapping.** PM ≈ `architect`; Dev ≈ `developer`; QA ≈ `qa-reviewer` + `security-reviewer` + `performance-reviewer` + `integration-reviewer`, assigned programmatically by `.claude/scripts/assign-reviewers.sh` from `review-rules/`. The Independence Wall is mechanical: reviewers never see architect decisions and the architect never reads `review-rules/`. **This plan does not write `planning/slices/` skeletons** — the skill's bridge step does that, consuming each task file's DoD as `slice.yaml` `acceptance_criteria` + `verification_method`.

### 3.2 Vertical slices and demos (protocol §0.8)

**No slice may deliver only a schema or only a stub.** Every slice produces a working, demo-able increment; the four named checkpoints are the plan's spine:

| Demo | Content | Lands at |
|---|---|---|
| **Demo 1** | interview → prompt → ingest → **one direction rendered as a static page** | end of Phase 1 (slice S30) |
| **Demo 2** | a **live editable surface** (inline text, reorder, variant swap, autosave) **proven to survive at least two turn boundaries** — proof is a curl in a *separate tool call* after each boundary, never a same-turn 200 | end of Phase 2 (slice S41) |
| **Demo 3** | **gridlines + constraint drag + per-breakpoint overrides + free-position escape hatch** — D2's first real exercise, and the moment R8 is either survived or diagnosed | end of Phase 3 (slice S51) |
| **Demo 4** | **LOCK with two-build byte-equality, published, evidence-complete** — the bundle is the deliverable, not a by-product | end of Phase 5 (slice S73) |

### 3.3 The diagnostic slice requirement (protocol §0.3)

Phase 0 **is** the diagnostic phase: six spike slices (S01–S06) plus a channel-fidelity battery (S07). They exist because the diagnosis in `spec.md` §Diagnostics carries five hypotheses whose validating evidence does not exist yet. **Nothing server-dependent may be treated as committed until Gate 16-A passes** — this is the single sequencing rule of the whole plan.

### 3.4 Definition-of-Done template (identical in every task file)

A slice is Done when, and only when:

1. Every artifact named in the slice's DoD exists at its absolute path.
2. Every named validation ran and its **recorded output** is in the evidence bundle (exit codes, counts, hashes, screenshots — not prose claims).
3. Every mapped acceptance criterion (`A<n>` from §19, or a slice-local criterion where §19 has no row) is demonstrated by the stated `verification_method`.
4. The Dev evidence bundle has all seven sections.
5. QA has independently re-verified and returned PASS (not INCONCLUSIVE).
6. **`## Dev Learnings` and `## QA Learnings` are updated** (protocol §0.7). A slice with empty learnings is **not Done**, regardless of code state.

---

## 4. Phase plan

Sequencing law: **risk-first, then vertical value, with the canvas front-loaded only after the pipeline it edits exists.** DECISION-1 B front-loads the highest-risk unproven mechanic (the canvas), which is precisely why Gate 16-A and the Phase-0 spikes must precede all canvas work.

### Phase 0 — Diagnostics (blocking) — epic E0

Gate 16-A first. Outputs: the launcher-rung decision, the topology ADR, the CSP-font answer, the substrate answer, the reproducibility answer, the `Task`-availability answer, and the channel-fidelity battery (three paste paths, empirical output ceiling, HMR round-trip latency for a move op, dependency licence re-verification **against the actual LICENSE file at pin time**).

**Exit condition:** Gate 16-A passes at some rung, or F4/F5 is signed off, or the browser-editor premise is rescoped. No other exit exists.

### Phase 1 — Generative pipeline — epics E1, E2, E3, E4, E5, E6, E7

Skill scaffold and the TypeScript spine (**`server.py` → `server.ts` port is the first code written**, to establish the TS spine against R12 Python-gravity), warm start with asset-library detection, the 90-question interview, the two-stage prompt generator with the font catalog and frozen token manifest, the importer with envelope validation and quarantine and Local Regeneration Mode, the token compiler with the versioned coherence-lint set, and the document model plus the pure renderer.

> **DEMO 1.**

### Phase 2 — Editor core + security — epics E8, E16

Three-pane shell with the out-of-iframe overlay, Navigator, inline `plaintext-only` editing, image handling with the blocking alt gate, reorder, undo with transactional grouping, autosave over typed ops, recovery bin, freeze, per-page SEO, preview mode, Design Health HUD — **with the eight-control security posture, one-writer enforcement, hash-journal reconciliation and the file-ownership guard landing *with* the first live editor, not after it.**

> **DEMO 2.**

### Phase 3 — The canvas — epic E9 (v1 by DECISION-1 B)

Strict dependency order: gridline overlay → snap engine → drag-to-place writing grid integers (with §11.2.1's normative drop algorithm and AC1–AC9) → span/padding/gap handles → keyboard parity → override cascade with the pre-commit chip → reading-order invariant and mobile stack preview → free-position escape hatch. Zoom/pan, rulers, fraction-stored guides and multi-select/align/distribute are the **tail**.

> **DEMO 3.**

### Phase 4 — Variants, artwork, regeneration, custom components — epics E10, E11, E12, E13

Typed slot contracts and superset-only offers with the content orphanage and LOCK-blocking placeholders; the hand-authored variant-axis schema and the lazy deterministic generator with the 200×120px indistinguishability rule; the art/motion container contract (D4) and artwork lanes A and B with the direction-affinity filter chips; Step-5 regeneration with reviewed application and the migration report; the minimal Step-6 registry with build-time SVG charts.

### Phase 5 — Gates, LOCK, publish, evidence — epics E17, E14, E15

`gates.ts` structured verdicts and the live/lock-time split; capture at pinned device heights; LOCK with the **eight** purity gates and the **32**-check ordered checklist; two-build equality (or the signed-off normalised fallback); publish with the runbook fallback; the licence-and-evidence bundle.

> **DEMO 4.**

### Phase 6 — Durability, acceptance, learning — epics E18, E19

Resume from disk and re-attach across an eternity `/clear`; `verify.ts` and `doctor.ts`; the gotchas reference; the A1–A90 acceptance sweep; `bun selftest.ts` at 100% of assertions; demo evidence; `AGENT-METRICS.md`; Dev/QA learnings recorded on every slice.

---

## 5. Epic register

| Epic | Title | Phase | Size class `[I]` | Inherited effort band `[I]` | Gate / demo |
|---|---|---|---|---|---|
| **E0** | Phase-0 spikes and blocking gates | 0 | M | not in the L-list | **Gate 16-A blocks everything server-dependent** |
| **E1** | Skill scaffold and the TypeScript spine | 1 | M | L1 | — |
| **E2** | Step 0 warm start | 1 | S | L1 | — |
| **E3** | Step 1 interview (90 questions) | 1 | L | L1 (sized against 78; NA-01 raises it) | — |
| **E4** | Step 2 prompt generator | 1 | L | L1 | O1 must precede |
| **E5** | Step 3 ingest + Local Regeneration Mode | 1 | L | L2 | — |
| **E6** | Token compiler + coherence lints | 1 | M | L2 | — |
| **E7** | Document model + pure renderer | 1 | L | L2 | **Demo 1** |
| **E8** | Editor shell and core operations | 2 | XL | L3a | **Demo 2** |
| **E16** | Security, concurrency, lifecycle | 2 | M | not separately sized | lands *with* E8 |
| **E9** | **The canvas** (DECISION-1 B) | 3 | XL | L3b | **Demo 3** |
| **E10** | Component bar and deterministic variants | 4 | L | L2 | — |
| **E11** | Artwork lanes, asset library, containers | 4 | M | L2 | — |
| **E12** | Step 5 regeneration | 4 | M | L2 | — |
| **E13** | Step 6 custom components | 4 | M | L5 (~per family) | sign-off rows 5, 6 |
| **E17** | Quality gates and capture | 5 | L | L4 | — |
| **E14** | Step 7 LOCK | 5 | L | L4 | — |
| **E15** | Step 8 publish and evidence | 5 | M | L4 | **Demo 4** |
| **E18** | Durability and diagnostics | 6 | S | — | — |
| **E19** | Acceptance, demos, learning capture | 6 | M | — | ship bar |

**Size class is ordinal and explicitly non-temporal** (S < M < L < XL). It exists so sequencing decisions can be made without fabricating day figures. See §6.4 for why no per-slice day estimate is given.

---

## 6. Schedule posture — re-baselined, and honestly incomplete

### 6.1 The source figures, quoted not derived

`[I]` every one; none is a measurement:

| Band | Source statement |
|---|---|
| L1 | interview + prompt — **2–4 days** |
| L2 | ingest / tokens / variants — **8–12 days** |
| L3a | editor-lite — **8–12 days** |
| L3b | editor-full (canvas, anchors, snapping, layers, per-breakpoint overrides, free-position, undo, marquee, keyboard nudge) — **30–60 days "and it never feels finished"** |
| L4 | lock / export / publish / evidence — **3–5 days** |
| L5 | custom components — **~5 days per family** |
| DECISION-1 delta | **+~16–24 days**; **~25–35 days against the revised baseline** |

### 6.2 What DECISION-1 B changes

§18's timeline, §18's v1 scope-in list and §13's gate budgets were all written against **editor-lite**. They are **stale**. This plan re-baselines by moving L3b's content into v1 (epic E9) and retiring R47, at the cost the (overridden) recommendation named: the highest-risk unproven mechanic now runs before the pipeline around it is proven. The mitigation is sequencing — Gate 16-A and the Phase-0 spikes precede canvas work, and E9 is sub-sliced so it can be stopped at any sub-slice boundary.

### 6.3 Two source figures that cannot both be right

**NA-B10 (new).** The DECISION-1 delta (**+16–24 days**) and §17-R18's L3b band (**30–60 days**) describe the same canvas layer and are inconsistent by roughly a factor of two. **This plan carries both verbatim, refuses to average them, and does not publish a reconciled total.** Whoever needs a commitment date must measure the first three canvas sub-slices (S42–S44) and extrapolate from measured work — that is the only path from `[I]` to a defensible number.

### 6.4 Why there are no per-slice day estimates

Two source volumes (216/1,228 components; 90 interview questions) and one scope decision (DECISION-1 B) each independently invalidate the baseline the day figures were computed against. Publishing 77 fabricated day numbers on top of that would convert three inferences into a schedule that looks measured. Instead every slice carries an **ordinal size class** and its epic's inherited L-band, and the plan states plainly: **no figure here is a measurement, and none should be quoted as one.**

### 6.5 Trade-back-out order (if the canvas overruns)

Canvas tail first (zoom/pan → rulers → fraction-stored guides → marquee/multi-select → align/distribute), then the free-position escape hatch, then smart-guide distance labels, then padding/gap handles. **Gridlines, snap, drag-to-place, keyboard parity and the override cascade are the irreducible core of DECISION-1 B and are not tradable** — trading them re-creates R47 and makes the decision meaningless.

---

## 7. Work breakdown — epics → stories → slices

The authoritative machine-readable breakdown is `stories.json`; the per-slice contracts are `tasks/<slice-id>.md`. This section is the human index.

**Slice-id grammar:** `S<nn>-<slug>`, stable, never renumbered. `type ∈ {diagnostic, build, demo}`.

| Slice | Title | Epic | Story | Type | Depends on |
|---|---|---|---|---|---|
| S01 | Gate 16-A turn-boundary probe and launcher-rung decision | E0 | ST-01 | diagnostic | — |
| S02 | O1 generation-surface font-policy probe | E0 | ST-01 | diagnostic | — |
| S03 | O8 substrate spike | E0 | ST-01 | diagnostic | — |
| S04 | O4 topology spike and ADR | E0 | ST-01 | diagnostic | S01, S03 |
| S05 | Build byte-reproducibility spike | E0 | ST-01 | diagnostic | S03 |
| S06 | Channel-fidelity, output-ceiling, latency and licence battery (+ `Task` probe) | E0 | ST-01 | diagnostic | — |
| S07 | Thin router `SKILL.md` + Phase-0 Confirmation Gate | E1 | ST-02 | build | S01 |
| S08 | `server.py` → `server.ts` port (the TypeScript spine) | E1 | ST-02 | build | S01 |
| S09 | Symlink installer, project config, session dir, git init, selftest harness | E1 | ST-02 | build | S07 |
| S10 | Warm-start scan and asset-library detection | E2 | ST-03 | build | S09 |
| S11 | System/identity split, negative constraints, mined-source pre-fill | E2 | ST-03 | build | S10 |
| S12 | The 90-question interview bank (`references/interview-bank.md`) | E3 | ST-04 | build | S09 |
| S13 | Interview engine: tiers, waves, branch map, policy questions, instrumentation | E3 | ST-04 | build | S12 |
| S14 | `concept.md` synthesis, inline, with the refusal requirement | E3 | ST-04 | build | S13 |
| S15 | `font-catalog.json` + per-session hash-pinned snapshot | E4 | ST-05 | build | S02 |
| S16 | Mechanical token manifest + Stage-A capsule prompt + pre-filter and cut | E4 | ST-05 | build | S14, S15 |
| S17 | Stage-B prompt, envelope manifest, terminator, chunk computation | E4 | ST-05 | build | S16, S06 |
| S18 | Tolerant `FILE:`-block parser + envelope validation + no-partial-write refusal | E5 | ST-06 | build | S17 |
| S19 | AST-resolving import validator, quarantine, repair prompts, re-verification | E5 | ST-06 | build | S18 |
| S20 | Local Regeneration Mode (zero-paste path, identical validator) | E5 | ST-06 | build | S19 |
| S21 | Token compiler: DTCG JSON + forge YAML + CSS custom properties + `@theme` | E6 | ST-07 | build | S19 |
| S22 | Flat variable layer, machine-owned `tokens.css`, `extract-override.ts` | E6 | ST-07 | build | S21 |
| S23 | Versioned coherence-lint set (logical properties, elevation, §7 lints 7–10) | E6 | ST-07 | build | S21 |
| S24 | Doc schema + canonical serialisation (`site.json` + `pages/<id>.doc.json`) | E7 | ST-08 | build | S03, S21 |
| S25 | Pure, total renderer + §12.16 resolution policy | E7 | ST-08 | build | S24 |
| S26 | Breakpoint vocabulary and the desktop-down cascade compiler | E7 | ST-08 | build | S24 |
| S27 | Determinism contract: six hazards designed out, generation is a pure function | E7 | ST-08 | build | S25 |
| S28 | **DEMO 1** — interview → prompt → ingest → one direction rendered static | E7 | ST-08 | demo | S14, S20, S22, S26, S27 |
| S29 | Editor shell, three panes, out-of-iframe overlay, same-origin preview iframe | E8 | ST-09 | build | S25, S08 |
| S30 | Navigator/layers tree and three-way selection parity | E8 | ST-09 | build | S29 |
| S31 | Typed-op engine, autosave, `history.jsonl`, undo/redo, transactional grouping | E8 | ST-10 | build | S29 |
| S32 | Inline `plaintext-only` text editing | E8 | ST-10 | build | S31 |
| S33 | Image replace, focal point, blocking alt gate, auto-recompression | E8 | ST-10 | build | S31 |
| S34 | Section reorder, duplicate/copy/paste with overrides, freeze | E8 | ST-10 | build | S31 |
| S35 | Named snapshots, save-as-variation, recovery bin with restore-in-place | E8 | ST-11 | build | S31 |
| S36 | Per-page SEO fields, page-scoped ops (Branch A+), preview mode, Design Health HUD | E8 | ST-11 | build | S31 |
| S37 | Eight-control security posture | E16 | ST-12 | build | S08, S29 |
| S38 | Hash-journal reconciliation, 409 optimistic concurrency, editor lock + tab claim | E16 | ST-12 | build | S31, S37 |
| S39 | PreToolUse ownership guard, `wb op` legal write path, agent inbox | E16 | ST-12 | build | S38 |
| S40 | **DEMO 2** — live editable surface surviving ≥2 turn boundaries | E8/E16 | ST-12 | demo | S32, S33, S34, S35, S36, S39 |
| S41 | Gridline overlay derived from `getComputedStyle` | E9 | ST-13 | build | S29, S26 |
| S42 | Snap engine: interval indexes, priority classes, tolerance ÷ zoom | E9 | ST-13 | build | S41 |
| S43 | Drag-to-place writing grid integers + the normative drop algorithm (AC1–AC9) | E9 | ST-13 | build | S42, S31 |
| S44 | Span resize, padding/gap handles on the spacing scale, smart guides | E9 | ST-14 | build | S43 |
| S45 | Keyboard parity and editor-chrome target size (WCAG 2.5.7 / 2.5.8) | E9 | ST-14 | build | S43 |
| S46 | Per-breakpoint override cascade, pre-commit chip, overridden-here dots | E9 | ST-15 | build | S43, S26 |
| S47 | Reading-order invariant, `order` hard block, numbered mobile stack preview | E9 | ST-15 | build | S46 |
| S48 | Free-position escape hatch: anchored offset, `flowFallback`, demote, LOCK gate | E9 | ST-15 | build | S46 |
| S49 | Canvas tail: zoom/pan, rulers, guides, marquee/multi-select, align/distribute | E9 | ST-16 | build | S44, S45 |
| S50 | **DEMO 3** — D2 exercised: gridlines + drag + overrides + free position | E9 | ST-16 | demo | S43, S44, S45, S46, S47, S48 |
| S51 | Typed slot contracts, superset-only swaps, content orphanage, blocking placeholders | E10 | ST-17 | build | S31, S25 |
| S52 | Hand-authored variant-axis schema | E10 | ST-17 | build | S21 |
| S53 | `variants.ts`: deterministic, lazy, append-only, indistinguishability-checked | E10 | ST-17 | build | S52, S51 |
| S54 | Art/motion container contract (D4) with `pauseAffordanceRef` and reduced-motion pairing | E11 | ST-18 | build | S21, S25 |
| S55 | Lane A: code-drawn, token-parameterised artwork that re-skins on hue change | E11 | ST-18 | build | S54 |
| S56 | Lane B: asset ingestion, `assets/manifest.json`, filter chips, Lane C runbook | E11 | ST-18 | build | S54, S10 |
| S57 | "More variants" and "more like this" | E12 | ST-19 | build | S53 |
| S58 | Per-section notes → scoped inline regeneration as one undo step | E12 | ST-19 | build | S57, S20, S31 |
| S59 | Redesign fork, reviewed application, `wb migrate`, `migration-report.json` | E12 | ST-19 | build | S25, S58 |
| S60 | Registry components: table, embed, form | E13 | ST-20 | build | S51, S23 |
| S61 | Build-time SVG charts, dataviz sub-tokens, ≤4 mark types, two shipped data states | E13 | ST-20 | build | S60 |
| S62 | Inline-authored custom path, coherence debt, signature-moment lint, `[3P]` rule | E13 | ST-20 | build | S23, S60 |
| S63 | `gates.ts` structured verdicts and the Tier 0/1/2/3 model | E17 | ST-21 | build | S23, S25 |
| S64 | Live checks: scoped, sub-100ms, drop/mouseup only | E17 | ST-21 | build | S63, S43 |
| S65 | Capture wrapper: Chrome CLI headless, wait recipe, device-height pinning | E17 | ST-21 | build | S63 |
| S66 | LOCK re-render, scrub, five layered editor-absence mechanisms | E14 | ST-22 | build | S27, S63 |
| S67 | The eight purity gates | E14 | ST-22 | build | S66, S05, S65 |
| S68 | The 32-check ordered lock-time checklist | E14 | ST-23 | build | S67, S64 |
| S69 | Snapshots, `lock-manifest.json`, git tag, non-mutating LOCK, UNLOCK path | E14 | ST-23 | build | S67 |
| S70 | Publish: automated deploy with the runbook fallback | E15 | ST-24 | build | S69 |
| S71 | Licence-and-evidence bundle with the fixed disclosure wording | E15 | ST-24 | build | S69, S56 |
| S72 | **DEMO 4** — locked, published, evidence-complete | E15 | ST-24 | demo | S70, S71 |
| S73 | Resume from disk, re-attach-not-relaunch across an eternity `/clear` | E18 | ST-25 | build | S09, S37 |
| S74 | `verify.ts` and `doctor.ts` | E18 | ST-25 | build | S27, S69 |
| S75 | `references/gotchas.md`, provenance, do-not-hand-edit banners | E18 | ST-25 | build | S09 |
| S76 | Acceptance sweep: A1–A90 mapped, A91+ collision handled | E19 | ST-26 | build | S68, S72 |
| S77 | `bun selftest.ts` at 100% of assertions; per-slice evidence bundles | E19 | ST-26 | build | S09, S76 |
| S78 | `AGENT-METRICS.md` scaffolding and the learning-capture loop | E19 | ST-26 | build | S77 |

**Count: 78 slices across 20 epics and 26 stories** (6 diagnostic, 68 build, 4 demo). This decomposition is a planning artifact, not a source figure (NA-B14).

---

## 8. Orchestration and edge constraints (protocol §0.9)

### 8.1 Target orchestration stack

The executing orchestration stack is **ACOS itself**: skills + agents + the PreToolUse hook chain, with `/acos-execute-slice` as the eventual executor of each `slice.yaml` the bridge step generates from `tasks/*.md`. There is no external workflow engine, and none should be introduced — adding one would duplicate the hook-enforced wall that already exists.

The **product's own** runtime orchestration is deliberately smaller: one long-lived local server, one browser, one Claude session, and an append-only inbox between them. **The server never calls `Task()`. The Claude session is the only engine.**

### 8.2 Durable execution (resume after interruption)

| Requirement | Mechanism |
|---|---|
| Resume after a context reset | `--resume` recomputes the pipeline phase **from disk alone** — which directories are populated and which gates passed. Never from conversation memory (the axiom-synthesis frontier principle) |
| Resume after an eternity `/clear` | The resume prompt says **RE-ATTACH** to the fixed port via `state.json`, never relaunch. A `/clear` kills the `tail -f` loop; re-attaching restores it |
| Resume across a server death | `state.json` carries `{phase, step, awaiting, nextAction, port, pid, url, sessionId}` `[V — §12.11; NA-B03 records that this is a superset of the carried four-field shape]`; regenerate-if-stale on startup |
| Resume across a machine restart | Everything durable is on disk under the session tree; `.wb/locks/**` is committed, `.wb/tmp/**` and `.wb/conflicts/**` are ignored |
| Slice-level durability | Per-slice evidence bundles under `.acos/evidence/[DATE]/[SLICE-ID]/`; a re-run of a slice is idempotent because its DoD names artifacts, not steps |

### 8.3 Human-in-the-loop nodes (the pauses that are *supposed* to exist)

1. **Phase-0 Confirmation Gate** — restate the brief, wait for an explicit yes, then write anything (both `CLAUDE.md` files mandate it; A90 tests it).
2. **The interview** — five hard-gated waves; the interview *is* the confirmation artifact.
3. **Direction tournament** — a bracketed tournament, never an N-up grid; every heat's pick and stated reason is written to `direction-tour-log.json` **as it happens**.
4. **Quarantine review** — nothing leaves import quarantine without an explicit per-item accept recorded in `inbound/import-report.json`.
5. **Migration acknowledgement** — LOCK is blocked until every `variantMigrated` flag is acknowledged (per node or bulk with a count).
6. **Sign-off rows** — ten of them, listed in `spec.md`; two are contingent (normalised-comparison fallback; launcher rungs F4/F5) and each is a hard stop, not a warning.
7. **LOCK itself** — the human is the sole LOCK authority.

**Machines may refuse; only the human may approve.** Machines enforce only machine-checkable correctness and may block on it; no machine judges aesthetics (NG1).

### 8.4 Observability

| Signal | Where |
|---|---|
| Per-gate verdicts | `gate-report.json` — `{gateId, tier, status: pass\|fail\|inconclusive, measured, threshold, evidenceRef}`, never a thrown exception on a normal fail |
| Op history | `history.jsonl` — `{seq, ts, actor, op, target, patch, inverse, label}`, append-only |
| Pipeline events | `events.jsonl` in the session root |
| Conflicts | `.wb/conflicts/<iso>/` — the divergent on-disk version is preserved *before* any resolution |
| Import decisions | `inbound/import-report.json`, per item, with the offending snippet |
| Design decisions | `direction-tour-log.json`, `provenance.json`, `concept.md`, `session.json` (`d1Deviations[]`) |
| Agent identity | ACOS already logs to `.acos/metrics/agent-completions.log` |
| Evidence | `.acos/evidence/<date>/website-<session>/` receives a one-line verdict mirror |

**Anti-requirement:** no product telemetry, ever. NG3 makes this structural, and S9's local-session-file measurement design is the direct consequence.

### 8.5 Role → orchestration mapping

| Pre-eng role | ACOS agent | Node type | Blocking? |
|---|---|---|---|
| PM | `architect` | planner; writes `slice.yaml` from the task file | writes, does not verify |
| Dev | `developer` | executor, scope-walled by `check-scope.sh` | produces the evidence bundle |
| QA | `qa-reviewer`, `security-reviewer`, `performance-reviewer`, `integration-reviewer` | isolated worktrees, spawned in parallel, cannot see each other | **all must PASS; crash ⇒ INCONCLUSIVE ⇒ blocks** |
| Human | the ACOS owner | approval pause | sole aesthetic judge, sole LOCK authority |

### 8.6 Harness edge constraints that change the design

Absolute paths everywhere (agent-thread cwd resets between Bash calls). There is **no `timeout`/`gtimeout` binary** on this machine — it yields *empty output*, not an error, so long runs use `run_in_background` plus polling. Never `rm -rf` in the export path (write-to-new-dir-then-swap; the Oracle scores destructive commands +5). Never treat a same-turn HTTP 200 as proof of life. Do not assume `Task` is callable mid-skill — every named feature has an inline main-session path. `session-cleanup.sh` touches `.acos/state/` only, so durable artifacts live under `.acos/website-builder/`. Open previews with `open -a "Google Chrome" <url>`. APFS is case-insensitive: sibling direction directory names must not differ only by case. **Subagents are policy-blocked from `Write`** — agent-produced code returns as text and the main thread writes it (A89).

---

## 9. Quality strategy

### 9.1 The dividing line

**Scoped arithmetic/DOM-read vs whole-document render pass** — not "accessibility vs performance". LIVE checks are sub-100ms, fire on drop/mouseup (**never mid-drag, never per-frame**) and are scoped to the touched subtree. LOCK-TIME checks are whole-document and batch.

### 9.2 Severity tiers

| Tier | Behaviour |
|---|---|
| **Tier 0** | Blocks the individual placement or edit, inline and immediately (contrast below floor on placed text, target <24px with no valid exception, missing alt/decorative choice, duplicate ARIA id) |
| **Tier 1** | Blocks **LOCK only**; never interrupts live editing |
| **Tier 2** | Advisory, dismissible, batched into the Design Health pill — **never a toast stream** (A37) |
| **Tier 3** | Silent end-of-session record |

### 9.3 Verification methods used by task DoDs

`grep-assert` · `exit-code` · `hash-compare` · `recompute` (contrast, counts, ratios) · `screenshot-diff` · `structured-gate-verdict` · `manual-observation` (human-judged, evidence-recorded) · `probe` (Phase-0 diagnostics, incl. cross-turn-boundary curl). Each task file names exactly one primary method per acceptance criterion so the bridge step can emit `verification_method` mechanically.

### 9.4 The claim ceiling

Automated tooling catches **57.38%** of real accessibility issues `[V — Deque, 13,000+ page-states, ~300,000 issues]`. Therefore the product **never** claims conformance. The fixed wording is: **"Automated accessibility gates passed: N. Manual and screen-reader review not performed."** (A72, A73.)

### 9.5 Two gates that look identical and are not

**Licence completeness** confirms every *recorded* asset carries a licence class. **Reference resolution** confirms every *referenced* asset actually exists. A hallucinated asset path passes the first and ships a silently broken page — which is why gate 23a exists separately from gate 26 (research F16).

---

## 10. Metrics and governance scaffolding (protocol §0.5)

**Defined here; computed nowhere.** `AGENT-METRICS.md` at the feature root is the instrumentation contract.

| Metric | Definition |
|---|---|
| **SPD** — Story Points Delivered | Qualitative approximation of delivered slice weight per agent per run, recorded per slice in the evidence bundle |
| **QAP** — Quality-Adjusted Productivity | `QAP = (Delivered_Value * Quality_Score) / (1 + Rejection_Count)` where `Rejection_Count` counts QA rejections that slice absorbed |
| **TER** — Token Efficiency Ratio | Artifacts produced per 1K tokens consumed; artifact volume per unit cost where cost data exists |
| **UAPS** — Universal Agent Performance Score | `UAPS = 0.3*Quality + 0.4*Efficiency + 0.3*CostEffectiveness` |

**Instrumentation plan.** Agent identity is already logged by ACOS to `.acos/metrics/agent-completions.log` (agent_type / agent_id). Per-slice inputs (`Delivered_Value`, `Quality_Score`, `Rejection_Count`, artifact counts) are recorded in each slice's evidence bundle under `.acos/evidence/[DATE]/[SLICE-ID]/`. `AGENT-METRICS.md` states the formulas, their inputs, and where each input is read from — and states explicitly that no value in it is computed by the pre-engineering pipeline.

---

## 11. Bloat management and canonicalisation (protocol §0.6)

Nothing is deleted; artifacts are annotated. Categories:

| Category | Meaning | Applied to |
|---|---|---|
| **Active** | Recent and needed by a live slice | `spec.md`, `plan.md`, `tech_prd.md`, `data-model.md`, `stories.json`, `tasks/**`, both domain artifacts |
| **Review** | Canonical-example candidates worth promoting into the estate's pattern library | Nominated in `analysis-report.md` by `/preeng.analyze`, not here |
| **Burn pile** | Safe to archive later, retained for now | Part files (deleted on successful assembly), superseded drafts, `_deterministic_prompt.md` and `_runner_config.json` after the run closes |

Evidence is grouped into **per-slice bundles**, never a shared dumping ground, so a rejected slice's evidence is isolated and re-runnable. The month-six rot risk (R20 — the precedent already rotted: unversioned tree, ~30 opaque variant directories, no manifest) is addressed structurally by `git init` at Step 0, `provenance.json`, generated-file banners, `assets/manifest.json` and `doctor.ts` — not by discipline.

---

## 12. Learning capture (protocol §0.7)

Every task file carries `## Dev Learnings` and `## QA Learnings`. **A slice is not Done until both are updated** (NFR-27). Learnings are written where the work happened, not aggregated into a document nobody reads. At the end of each phase the learning-agent lifts cross-project patterns into `learning-curve/`; that lift is `S78`'s job and is explicitly a slice, not a habit.

Three learning obligations are named up front because they are the ones most likely to be lost:

1. **Gate 16-A's result** — whichever rung passes is a first-party harness fact worth more than any documentation, and belongs in `references/gotchas.md` and in the estate's memory.
2. **The canvas sub-slice measurements** — S41–S43's actual elapsed effort is the only evidence that can turn §6.3's contradiction into a number.
3. **Every contradiction found in the source** — the 20 NA items plus the new ones in §13 exist because reading two sections against each other found them; that reading protocol is itself the reusable pattern.

---

## 13. Assumptions recorded by this command

Carried forward without re-deciding: **OQ-01…OQ-42** and **NA-01…NA-20**, as recorded in `spec.md` §Open Questions. The following are **new to this planning pass** and were forced by reading §12.10–§12.17 and §19 of the source directly.

| Id | Finding | Adopted default |
|---|---|---|
| **NA-B01** | FR-091 makes a multi-page manager and site-wide global regions v1 MUST, while OQ-03 adopted **Branch A+** (single page; `pages[]` of length 1; every op page-scoped) | Adopt **Branch A+** as binding: page-scoped ops, `site.json` page list and per-page SEO fields ship in v1 so multi-page is a v2 *feature addition, not a data migration*; the multi-page **manager UI** and **global regions** are v2. Recorded as a sign-off row |
| **NA-B02** | §12.12 specifies **eight** security controls, not the carried six: `Access-Control-Allow-Origin` set to the exact origin (never `*`), **`Host`-header validation on every request including the bootstrap `GET /`**, and a security-header/CSP row are additional. The section proves that the bearer token does **not** defeat DNS rebinding and `Host` validation does `[I — the four-step argument is the PRD's own inference, written to be auditable]` | Adopt **eight controls**; FR-220 is amended; §12.17-A100 is the test |
| **NA-B03** | `state.json` is `{phase, step, awaiting, nextAction, port, pid, url, sessionId}` `[V — §12.11]`, a superset of the carried `{port, pid, url, sessionId}` | Adopt the superset; `--resume` reads `phase`/`step`/`awaiting`/`nextAction` |
| **NA-B04** | **§12.16-O35 is a new open question** absent from the carried 42 and from NA-01…NA-20: whether `wb migrate` should attempt semantic cross-direction variant matching (slot-signature) or always fall back to canonical | Adopt the section's stated v1 choice: **canonical fallback only, always reviewed**. Semantic matching is a v2 question and "no known mitigation removes the risk" |
| **NA-B05** | The A91+ collision is now fully enumerated on both sides: **§12.17 defines A91–A101** (doc/persistence: `1/-1` compile, upward-key rejection, design-time-origin grep, worktree isolation, out-of-band write detection, `/systemLock` rejection, allowlist coverage, canonical re-serialisation, migration flags, `Host` rejection, AST quarantine) and **§18 defines a disjoint A91–A101** | Cite as `§12.17-A91…A101` and `§18-A91…A101`, never bare. Recommend renumbering §18's set to **A102–A112**; treat A91+ ids as unstable until that lands |
| **NA-B06** | §12.14 requires an **AST-resolving** validator with scope tracking, fail-closed quarantine on the undecidable, sandboxed-iframe first render under a `connect-src`-free CSP, and per-item human accept. The carried FR-052 reads as a substring denylist, which §12.14 explicitly rejects as insufficient | Adopt the AST design. A9's `fetch(` case is the easy subset; **§12.17-A101 (`window["fe"+"tch"]`) is the real bar**. State the honest limit: a mistake-catcher and tamper-detector, **not** a sandbox-escape-proof boundary |
| **NA-B07** | §12.10 amends R6's mitigation from "every-save-is-a-commit" to **"op log + atomic writes + hash reconciliation"**; the carried architecture constraint still says every-save-is-a-commit | Adopt: durability is `history.jsonl` + atomic write-temp-then-rename + `.wb/doc-hashes.json`; **git commits happen at milestones**, with `wb autosave --git` available opt-in |
| **NA-B08** | The skip-link component that §13.4 gate 11a requires **does not exist in the component inventory** | Add one row with a **single canonical variant** (not a 10-variant family), making the v1 target **88 rows / 675 variants**. Flagged for confirmation when the inventory audit runs |
| **NA-B09** | NA-12 gives a 65–70 band for v1 editor rows and explicitly says no recount was performed | Settle **66 of 116** as the planning figure `[I]` (56 editor-lite + the 10 promoted canvas rows), and require a real recount before it is quoted anywhere as a commitment |
| **NA-B10** | The DECISION-1 delta (+16–24 d) and §17-R18's L3b band (30–60 d) describe the same canvas layer and disagree by ~2× | Carry **both verbatim**, refuse to average, publish **no** reconciled v1 total; use ordinal size classes and measure S41–S43 to escape the inference |
| **NA-B11** | `site/` must be **its own git repo** and `.acos/website-builder/sessions/*/site/` must be in the ACOS `.gitignore` `[V — §12.11, A83]`; the carried FR-016 says only "git init at Step 0" | Adopt the nested-repo requirement as a v1 build requirement in S09; otherwise every milestone commit pollutes ACOS history and every `wb-lock/<n>` tag collides |
| **NA-B12** | §12.11 fixes the on-disk session tree (`00-interview/` … `07-lock/`, `.wb/**`, `ACTIVE`, `events.jsonl`) at `.acos/website-builder/sessions/WB-<ts>-<slug>/` | Adopt §12.11's tree verbatim as the canonical layout, with `04-site/` holding `site.json` + `pages/*.doc.json` (NA-07's rename applied) |
| **NA-B13** | The command spec defines **no** `stories.json` schema | Adopt a minimal deterministic schema — `{feature_id, schema_version, scope_of_record, epics[], stories[], slices[]}` — documented in §7 and in `stories.json` itself, so the bridge step has a stable contract. No existing schema was altered |
| **NA-B14** | The 78-slice / 26-story / 20-epic decomposition is a planning choice | Recorded as a planning artifact, not a source figure |
| **NA-B15** | §12.13's write-allowlist **table** supersedes A78's three-shape assertion (the source says so explicitly), and adds `/systemLock`-pointer rejection and symlink rejection | Adopt the table as the normative allowlist; A78 is amended, not satisfied as written |
| **NA-B16** | Protocol §4 requires each command to echo full file contents into chat; this stage's output contract forbids pasting artifact contents into the final message | Artifacts are authoritative **on disk** at the absolute feature directory; the chat echo is suppressed. No artifact content was withheld from disk |

---

## 14. Traceability contract

Every downstream artifact must be able to answer three questions mechanically:

1. **Where did this requirement come from?** Every `FR-xxx` in `spec.md` carries a source column (a PRD section, a TR, a settled decision, or an explicit Assumption). Task files cite `FR-xxx`; they never restate a requirement without its id.
2. **How will we know it works?** Every slice maps to `A<n>` from §19 where one exists, or declares a slice-local criterion with a named `verification_method` where §19 has no row. Criteria above A90 are cited **section-qualified** (NA-B05).
3. **What is the evidence worth?** Claims that a slice relies on cite an evidence-ledger id (`EL-0xx`) and inherit its tier and confidence. Competency questions (`CQ1`–`CQ18`) are cited on the slices that must not leave them unanswered — CQ6 (server survival) on S01, CQ4 (canvas requirements) on S41–S48, CQ9 (proving zero editor runtime) on S66–S67, CQ12 (motion judgement, **unsolved**) on S54, CQ18 (channel ceiling, **unsolved**) on S06/S17.

**Coverage assertion for this command:** every MUST-level functional requirement in `spec.md` §4.1 maps to at least one slice in §7; every NFR in §4.3 maps to at least one gate or slice; all 90 §19 acceptance criteria are mapped in `stories.json` and swept by S76. The mechanical check is recorded in `planning_qa_report.json`.

---

**End of `plan.md`.** Companion artifacts: `tech_prd.md` (technical contracts), `data-model.md` (field-level entities and file formats), `stories.json` + `tasks/*.md` (produced by `/preeng.tasks`).
