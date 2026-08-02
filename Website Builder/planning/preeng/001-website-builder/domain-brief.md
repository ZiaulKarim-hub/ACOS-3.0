# Domain Brief — Website Builder (`001-website-builder`)

**Compilation phase 1 of 4 (Domain List Generation).** Produced by the deterministic pre-engineering worker from `spec.md` and selectively-read windows of the signed-off PRD. No external sources were fetched; every claim below is either read from a first-party file (tier T5), carried from a PRD claim that itself cites a source (tier inherited), or marked `Assumption`.

**Evidence markers are preserved:** `[V]` verified, `[I]` inference, `[U]` unsourced. **Every schedule, effort and volume estimate is `[I]`.**

---

## 1. Domain statement

The domain is **generated visual web design systems with human-only aesthetic judgement**: the intersection of (a) visual website builders and their document models, (b) design-token systems and derived-value computation, (c) constraint-based responsive layout and direct manipulation, (d) machine-checkable web correctness (accessibility, performance, SEO, licensing), and (e) local agent-harness engineering — long-running servers, single-writer concurrency, untrusted code import and reproducible static export.

What makes this domain distinctive is a deliberate inversion of the prevailing AI-design architecture: **the expensive loop is a human sitting in a browser, not an autonomous multi-agent generation loop.** Machines are permitted to enforce only what is mechanically checkable. Taste is not delegated, scored or automated.

## 2. Bounded scope

**In domain:** document models for visual editors; constraint vs coordinate layout; design tokens and derivation; accessibility and correctness gating; font and asset licensing; static-build determinism and export purity; local-server lifecycle inside an agent harness; SSE + JSONL-inbox human-in-the-loop patterns; localhost security; untrusted-code import protocols; editor history and undo semantics; data visualisation under a narrow brand constraint; choice architecture; motion verification; headless capture correctness.

**Out of domain:** multi-user real-time collaboration and CRDT merge; server-rendered applications and CMS backends; AI aesthetic scoring of any kind; application-shell and commerce UI; interactive client-side charting runtimes; RTL layout mirroring (the structural question is asked; the layout is not built).

## 3. Entities

| Entity | Definition |
|---|---|
| Session | A single run of the skill against one project; carries warm-start mode, asset-library path, mined sources, D1 deviations and the branch choice |
| InterviewAnswer | A question-ID-keyed, tier-tagged answer with a source (`asked`, `pre-filled`, `inferred-default`, `skill-default`) and an override flag |
| Concept | A 200–300 word compression of the interview: point of view, ≥3 abstracted references, restraint budget, and what the site refuses to do |
| DirectionCapsule | A Stage-A lightweight direction proposal carrying self-audit fields (hue anchors, type pairing, motion character, forced-divergence axis position) |
| Direction | A fully expanded design identity: a 24-slot varying vector + 2 invariant records, plus derived values and direction-bound authored artefacts `[V — §7.0]` |
| DesignToken | A token in the interchange format plus its mirrored forge spec, carrying anchor-vs-derived provenance and the motion/spring extension shape |
| SystemLock | The frozen system of record for a build; per-file hashes of tokens and every component |
| ImportEnvelope | The declared file list, per-file line counts, sha256 prefixes, per-run terminator and quarantine records that make truncation and injection detectable |
| Doc (Layout) | The scene graph: pages, node tree, stable section ids, freeze flags, trash, per-breakpoint override maps and anchored-offset records |
| Content | Slot-keyed copy, plus the orphanage of displaced copy |
| Node | A component instance: id, component family, variant, layout per breakpoint key, props, slots, text, override, locked, notes, migration flags |
| SlotContract | A typed slot definition `{name, type, cardinality, required}` enabling superset-only swap offers and placeholder detection |
| Variant | A structurally distinct composition of one component within one direction, identified by its variant-axis vector |
| Asset / Artwork | A manifest entry with lane, token-referencing flag, direction affinity, licence class, provenance and encoder settings |
| FontCatalogEntry | A licence-cleared typeface with classification, foundry, source, hash, glyph coverage and pre-subsetted base64 cuts |
| DirectionTourLog | The per-round record of directions shown, order shown, pick and the user's stated reason |
| HistoryOp | An op-log entry carrying the forward patch, its inverse, a transaction group and the actor |
| GateResult | A structured verdict: gate id, tier, pass/fail/inconclusive, measured value, threshold, evidence reference |
| EvidenceBundle | The licence, gate, contrast, screenshot, direction-tour, substitution and disclosure record shipped at publish |
| ServerState | `{port, pid, url, sessionId}` — the re-attach contract |

## 4. Processes

| Process | Definition |
|---|---|
| Warm start | Glob prior design systems and sites, detect an asset library, split reusable system assets from identity, and emit prior identity as negative constraints |
| Interview | Three tiers, waves, hard gates, branching and pre-fill, producing answers and a concept document |
| Prompt generation | Two-stage prompt assembly from skill-owned artefacts (font catalog, frozen token manifest) plus interview-derived slots, with envelope and chunking computed locally |
| Hand-carry / local regeneration | Moving a generated design system across an untrusted, lossy, manual channel — or bypassing it entirely with an identical-format local path |
| Ingest and validation | Tolerant parsing, envelope verification, deterministic re-verification of claims, quarantine, repair-prompt emission |
| Token compilation | Expanding the interchange tokens into custom properties and a theme layer, once per direction change |
| Direction tournament | Bracketed selection with bounded simultaneous comparison and a logged reason per heat |
| Direct manipulation | Snap-to-real-grid dragging that writes integers, with keyboard parity and a pre-commit breakpoint chip |
| Variant generation | Deterministic, lazy, append-only expansion of a component family within one direction |
| Scoped regeneration | Note-driven regeneration of one section, inline, as a single undo step |
| Migration | Remapping references after a system change, never silently dropping a node |
| LOCK | Re-render with the editor disabled, scrub, assert, snapshot, tag |
| Publish | Automated static deploy, or an emitted runbook fallback |
| Evidence bundling | Assembling licence, gate, contrast, capture and provenance records with an explicit disclosure |
| Resume | Recomputing the pipeline phase from disk and re-attaching to a live server |

## 5. Methods (the techniques the product is built out of)

Two-tier truth with a pure render; annotation-by-descent DOM↔doc mapping; zero DOM injection with a single sibling overlay; grid-integer placement derived from computed styles; desktop-down cascade with sparse overrides and a full-bleed small-breakpoint default; anchored-offset free positioning with an authored flow fallback; container queries for component internals; named grid areas with per-block promotion to explicit integers; derived-value computation from anchors plus seed tables; validity lists for repickable rows; frozen token-name manifests; envelope manifests with per-run terminators; tolerant block parsing with quarantine; deterministic variant generation with append-only indices; bracketed tournaments; op logs with inverse patches and transactional grouping; recovery bins independent of undo; hash-journal reconciliation; optimistic concurrency with 409; typed semantic ops; six-control localhost posture; detached-spawn ladders with post-turn-boundary probing; SSE + JSONL inbox with a zero-token blocking read; two-config two-outdir builds; manifest-based byte comparison; frozen-clock deterministic generation; scoped and full-page accessibility sweeps; dual contrast gating; device-height-pinned headless capture; licence manifests as asset allowlists.

## 6. Standards, specifications and external references invoked

| Standard / reference | Role in this domain | Tier |
|---|---|---|
| WCAG 2.2 AA | The pass/fail accessibility floor. Two criteria apply to the **editor itself**: 2.5.7 Dragging Movements and 2.5.8 Target Size `[V — w3.org understanding page quoted in §13.2]` | T1 |
| WCAG 2.4.1 Bypass Blocks (A) | Skip link present and first in tab order — gate 11a | T1 |
| WCAG 2.2.2 Pause/Stop/Hide (A) | Unconditional wherever qualifying continuous motion exists — gate 13a | T1 |
| WCAG 2.4.3 Focus Order (A) / 1.3.2 Meaningful Sequence (A) | Why an `order` override is hard-blocked on focusable nodes and warned on others | T1 |
| WCAG 1.4.10 Reflow / 1.4.12 Text Spacing / 1.4.11 Non-text Contrast / 2.3.1 Photosensitivity / 2.5.4 Motion Actuation / 4.1.3 Status Messages | The reflow, stress, contrast, flash, orientation and live-region gates | T1 |
| APCA | Advisory only — a WCAG 3.0 candidate, still draft, **no independent legal standing today**. Dual gate: pass WCAG 2 and compute APCA as a stricter internal target `[V — draft status]`; the specific Lc bands are `[U — U1, inherited, not re-verified]` | T2 |
| Design-token interchange format (2025.10) | The token JSON shape; spring/motion tokens are an out-of-standard extension every tool must agree on or motion degrades to none | T1 |
| RFC 6902 JSON Patch | The op log's patch/inverse representation | T1 |
| HTTP ETag / 409 semantics | Optimistic concurrency on document writes | T1 |
| SHA-256 | Envelope verification, per-file build manifests, asset derivation pinning | T1 |
| `SOURCE_DATE_EPOCH` and reproducible-build practice | Frozen clock, pinned locale and timezone for two-build comparison | T2 |
| OFL and foundry licence classes | What may be embedded, subsetted and redistributed; commercial faces emit a pre-launch blocker | T1 |
| Trademark practice on third-party marks | Platform badges, social icons, trust badges and map tiles are used **as supplied**, never redrawn | T2 |
| Copyright / trade-dress practice on look-and-feel | The ≥3-reference triangulation rule and the >70% single-reference regeneration trigger `[V — cited in §15.6]` | T2 |
| CVE-2025-24010 class | Localhost is not a trust boundary; Origin allowlists and bearer tokens are mandatory | T1 |
| schema.org | JSON-LD matched to the site-type answer | T1 |
| Core Web Vitals (2026 thresholds) | LCP ≤2.5s, CLS ≤0.1, INP ≤200ms; INP replaced FID in March 2024 and is now the most commonly failed vital `[V]` | T1 |
| Baseline platform status | Container queries, `:has()`, `@property`, cascade layers, nesting and logical properties are widely available; subgrid is universally supported; **anchor positioning is still a carryover Interop item and must not carry load-bearing layout** `[V — §11.5]` | T1 |
| ARIA Authoring Practices patterns | 22 inventory rows map to an APG pattern; their variants are skin-only over one audited implementation `[V — full pattern list retrieved]` | T1 |
| Deque Accessibility Coverage Report | Automated testing catches **57.38%** of real issues across 13,000+ page-states `[V]` — the reason no conformance claim is ever made | T3 |
| Choice-architecture literature | The 2015 meta-analysis finding a near-zero mean choice-overload effect with four engineerable moderators, against the earlier jam study; resolved in favour of the meta-analysis, retaining the indistinguishability rule | T3 |

## 7. Metrics

Interview elapsed time; questions asked vs bank size; pastes per chunk and chunks per cycle; resolved tokens per direction; variants per family and indistinguishable-pair count; directions surfaced vs generated; contrast ratio and APCA Lc per pairing; target-size violations; accessibility findings by severity; reflow findings per breakpoint; document overflow assertions; free-position and overlap counts; override counts per page and per site; motion instances by cost class; distinct motion kinds in use; LCP / CLS / INP and pre-LCP transfer; published JS byte size; screenshot-diff delta; dangling asset references; licence-class coverage; unresolved reference count; canonical-serialisation diff; two-build manifest equality; post-turn-boundary HTTP status and pid liveness; LOCK wall-clock; completed LOCK events per project per 90 days.

## 8. Risks (domain-level, not project-schedule)

Structural undeliverability of raster art from the generation channel; unrenderable typography at the moment of choice; silent truncation producing valid-but-wrong output; DOM-as-truth drift; harness reaping of long-running servers; two writers with no lock; the market record of constraint editors; ungraceful free-position degradation; unjudgeable motion feel; determinism false positives; untrusted local code import; portfolio homogenisation through warm start; choice overload and indistinguishability; charts breaking coherence by construction; legally-shaped components mistaken for aesthetically-shaped ones; invented third-party marks; unversioned month-six rot; deploy as a second manual boundary.

## 9. Anti-patterns (named, and structurally excluded)

HTML→JSON round-tripping; DOM wrappers injected for hit-testing; decorative gridlines that are not the real grid; two independent per-breakpoint layouts; raw absolute positioning as the free-position implementation; a flattened cross-product variant list; an N-up thumbnail grid for direction selection; treating the signature moment as a catalogue pick; independent picking of derived values; per-save git commits; a raw JSON Patch over HTTP; a base64 document blob in local storage; a `run_in_background` process treated as a live server; a same-turn 200 treated as proof of life; hard aesthetic blocking after a deliberate human choice; claiming conformance from automated gates; re-deriving a system from a stored prompt; copy-and-strip export.

## 10. Key terms

Direction, capsule, variant, derived value, anchor, identity vector, validity list, envelope, terminator, semantic op, freeze (never "lock" at element level), LOCK / UNLOCK, purity gate, coherence lint, coherence debt, content orphanage, flow fallback, pre-commit chip, overridden-here dot, cost class, reduced-motion sibling, Lane A/B/C, warm start, negative constraint, Gate 16-A, launcher rung, re-attach, tab claim, recovery bin, migration report, evidence bundle, disclosure line.

## 11. Competency questions

18 competency questions are carried in `domain-cqs.md`. They are the required set; the lattice is expanded until every one of them has a bounded subgraph connecting the problem to methods, metrics and standards. **Target coverage ≥95%; achieved coverage is recorded in `research.md` and in the validation note.**

## 12. Assumptions recorded in this phase

- `Assumption` — No external sources were fetched during this compilation. Every ecosystem fact (star counts, versions, last-push dates, licence strings) is carried from the PRD with its own marker and a `freshness_days` value recorded as unknown-at-compile-time where the PRD did not state a date. Re-verify at pin time.
- `Assumption` — Where the PRD contradicts itself across sections (see the ID-collision register and NA-01…NA-20 in `spec.md`), the **later, more specific and self-audited** statement is adopted, and the contradiction is recorded rather than silently resolved.
- `Assumption` — The domain boundary excludes anything that would require porting the rejected autonomous-judge architecture, regardless of technical merit.
