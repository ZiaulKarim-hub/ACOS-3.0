# Research Dossier — Website Builder (`001-website-builder`)

**Command:** `/preeng.research`
**Precondition checked:** `spec.md` exists at the absolute feature directory. Satisfied.
**Outputs:** `domain-brief.md`, `domain-cqs.md`, `domain-lattice.json`, `evidence-ledger.json`, this dossier, `research_qa_report.json`.
**Protocol:** the four-phase constitutional domain compilation pipeline — Domain List Generation, Lattice Expansion, Evidence Ledger, Agent Emission — with a CQ coverage target of ≥95%.

**Marker discipline (inherited, enforced):** `[V]` verified against a named source, `[I]` inference, `[U]` unsourced or explicitly low-confidence. Markers carried from the source PRD are never promoted. **Every schedule, effort, duration and volume estimate is `[I]` with low confidence recorded in the ledger.**

---

## 1. Method and honest scope

### 1.1 What this pass could and could not do

This worker **cannot fetch external sources.** It structures what is available: the signed-off PRD, the open-decisions file, the settled decisions, and first-party repository facts. Every claim in the ledger is therefore one of:

- a claim the PRD itself verified against a named external source (the ledger carries the PRD's marker and cites the PRD section as the proximate reference);
- a first-party repository fact (tier T5, the strongest evidence directly available here);
- an internal adopted default traceable to a named open question (tier T5, low confidence, deliberately recorded so a later reversal is visible);
- or an explicit `Assumption` where no source exists.

**No source was fabricated.** Where the PRD marks something unverified, this dossier keeps it unverified.

### 1.2 What was read from the source PRD

The PRD is 641,327 bytes / 4,224 lines / 20 sections and was **never read whole**, by standing instruction. Reads this pass were offset-bounded windows against the section line map:

| Section | Window | Depth |
|---|---|---|
| 5 — interview bank | 236–315 | Head: delivery rules, tier semantics, ID grammar, branch roots, Wave 0, Wave 1 |
| 6 — design-system prompt | 509–598 | Head: the prompt template, both dependent artefacts, the answers→slot mapping |
| 7 — design-system inventory | 764–833 | Head: the count/kind/scope/priority keys, vector membership, the scale reality check |
| 8 — component inventory | 1230–1304 | Head: the variant definition, the tier budget with computed totals, behavioural primitives |
| 9 — motion and art containers | 1779–1848 | Head: the container contract and its seven rules, the motion-variant axis model |
| 10 — editor feature set | 2014–2133 | §10.1 through §10.6 |
| 11 — layout and dragging | 2246–2431 | **Full** |
| 12 — document model, persistence, LOCK | 2431–2670 | §12.1 through §12.9 |
| 13 — quality gates | 2874–3018 | **Full** |
| 14 — regeneration and variants | 3016–3113 | **Full** |
| 15 — warm start, publish, licences | 3113–3188 | **Full** |
| 19 — acceptance criteria | 4000–4131 | **Full** |
| 20 — appendix | 4132–4224 | **Full** |

Sections 1–4 (summary, goals, users, pipeline), 16 (architecture), 17 (risks and open questions) and 18 (phased delivery) were absorbed during normalization and are carried in the program's feature config; they were **not** re-read this pass. Sections 7.2–7.18, the full 8.3 table, 9.2–9.6, 10.7–10.10 and 12.10–12.17 were **not** read. **Nothing is asserted from an unread page.**

### 1.3 A deliberate posture on contradictions

The source contradicts itself in at least nine places that matter. This pass does **not** silently pick a winner. The rule applied is: **adopt the later, more specific, self-audited statement; record the contradiction as a named assumption; and require a cross-section fix before implementation.** Twenty such records are carried as NA-01…NA-20 in `spec.md`, and the load-bearing ones appear in the evidence ledger with their own entries (EL-069 through EL-073, EL-087, EL-088).

---

## 2. Phase 1 — Domain List Generation

**Output:** `domain-brief.md` and `domain-cqs.md`.

The domain was bounded as **generated visual web design systems with human-only aesthetic judgement**: visual-editor document models; constraint-based responsive layout and direct manipulation; design tokens and derived-value computation; machine-checkable web correctness (accessibility, performance, structured data, licensing); and local agent-harness engineering (long-running processes, single-writer concurrency, untrusted import, reproducible static export).

The brief enumerates 20 entities, 16 processes, ~60 named methods, 34 standards and external references, ~55 metrics, the domain-level risk set, 19 structurally excluded anti-patterns, and the term glossary. The distinguishing feature of this domain — and the thing every downstream artifact must respect — is the **deliberate inversion of the prevailing AI-design architecture**: the expensive loop is a human in a browser, and machines are permitted to enforce only what is mechanically checkable.

**Competency questions:** the required 18 were adopted verbatim as the CQ set. They are not a sample of the domain; they are the questions a practitioner must answer before writing code, and three of them (server survival, motion judgement, generation-channel ceiling) have answers weak enough that the entire Phase-0 spike suite exists to strengthen two of them and the third is stated as unsolved.

---

## 3. Phase 2 — Lattice expansion

**Output:** `domain-lattice.json`, conforming exactly to the canonical schema.

### 3.1 Structure

| Measure | Value |
|---|---|
| Nodes | **334** |
| Edges | **546** |
| Node types used | 10 of 10 (`entity` 20, `process` 16, `method` 114, `standard` 34, `metric` 56, `risk` 35, `pattern` 10, `anti_pattern` 19, `term` 12, `cq` 18) |
| Edge relations used | 8 of 8 (`uses` 157+, `measured_by` 125+, `constrained_by` 122+, `mitigates` 61, `part_of` 23, `contradicts` 19, `depends_on` 17, `implements` 10) |
| Dangling edge endpoints | **0** |
| Orphan nodes | **0** |
| Duplicate node ids | **0** |
| Duplicate edge ids | **0** |
| Nodes with an out-of-vocabulary type | **0** |
| Edges with an out-of-vocabulary relation | **0** |

### 3.2 Expansion rule

Each CQ was expanded into a bounded subgraph of at most two hops, following the required shapes:

- **Problem → Method → Metric → Standard.** Every CQ has direct `uses` edges to the methods that answer it; every such method carries `measured_by` edges to the metrics that would prove it works and `constrained_by` edges to the standards that bound it.
- **Risk → Control → Evidence.** 35 risk nodes receive 61 `mitigates` edges from the methods and processes that address them, and those methods carry their own metric edges — so every mitigated risk terminates in something measurable.
- **Anti-pattern → contradicts → Method.** 19 anti-patterns are wired to the method each one is the negation of, which is what makes the exclusions checkable rather than decorative.

### 3.3 Coverage

**Measured CQ coverage: 18/18 = 100.0%** against the ≥95% target.

Coverage was computed mechanically (not asserted) with the definition: a CQ is covered when it has at least one `method` neighbour **and** reaches at least one `metric` node **and** at least one `standard` node within two hops. Per-CQ first-hop degree ranges from 4 (CQ10, CQ16, CQ18) to 9 (CQ4).

### 3.4 Structural checks

No critical violations. Three checks were run and are reproducible from the artifacts alone: referential integrity of every edge endpoint; controlled-vocabulary conformance for node types, edge relations and tiers; and orphan detection. The only structural finding of the pass was nine initially-orphaned metric and standard nodes (lock wall-clock, interview duration, questions asked, lock events, structured data, script-disabled render, text spacing, status messages, structured-data vocabulary), which were connected by twelve additional edges before assembly rather than dropped — because each represents a real measured or constraining fact that belongs in the graph.

---

## 4. Phase 3 — Evidence ledger

**Output:** `evidence-ledger.json`, conforming exactly to the canonical schema.

### 4.1 Distribution

| Tier | Meaning | Entries |
|---|---|---|
| **T1** | Authoritative — specifications, vendor documentation, licence texts, recorded vulnerability classes | **37** |
| **T2** | Expert — reasoned positions, practitioner documentation, resolved lens disagreements | **17** |
| **T3** | Empirical — measured studies and dataset analyses | **6** |
| **T4** | Community/tool and vendor-surface facts that decay or are contested | **3** |
| **T5** | Internal / first-party repository reads and adopted defaults | **25** |
| | **Total** | **88** |

**13 entries carry confidence below 0.5.** Every one of them is either a schedule/effort figure, a carried-over unbenchmarked threshold, or an unverified external surface — exactly the classes the standing rule requires to be low-confidence.

### 4.2 Freshness posture

`freshness_days` is recorded as **0** for facts read directly from disk during this pass, **1** for claims carried from the PRD (dated one day before this compilation), and **8** for the twice-verified first-party harness observation whose second confirmation is dated. **This is a compile-time-relative measure, not an external verification date.** The PRD's own fetch dates for ecosystem facts (component libraries, pattern lists) are recorded in the entry notes where the PRD stated them; where it did not, the entry says so. Ecosystem facts decay fastest and several already drove reject/adopt decisions, so **every dependency licence must be re-verified against its actual licence file at pin time**, not against a registry summary (EL-068).

### 4.3 Traceability of adopted defaults

Per the evidence requirements, **every open question adopted as a default appears in the ledger as a low-confidence internal entry pointing at the decision item it came from**: EL-074 through EL-083 cover the fifteen open decision items and the ten open architecture/product questions, EL-084 and EL-085 cover the two conflicts this pass resolved against the source, and EL-059 records the publish commitment that overrides the normalization default. A later reversal of any of them is therefore traceable to a ledger id.

### 4.4 The weakest evidence in the set, named

| Entry | Claim | Why it is weak | Consequence |
|---|---|---|---|
| EL-066 | Generation-channel output ceilings | Figures were unverifiable and at least one referenced model name appears fabricated | Chunking is computed from measured artifact sizes at runtime; no published ceiling is designed against |
| EL-067 | Font policy on the generation surface | Assumed blocking; unverified | Embedded font data is mandated; a 60-second check must precede the prompt specification |
| EL-044 | Automated recall of aesthetic animation | Prior report; the source itself flags the area as unvalidated end to end | Never used as an acceptance signal; human plus deterministic lint only |
| EL-005 | Perceptual contrast bands | Inherited, not re-verified | Advisory stretch target only; the legally standing ratio remains the gate |
| EL-061 | Lock wall-clock budget | Inference sized against the expanded gate list | Validate against a prototype before treating as a service level |
| EL-062 | Motion-concurrency caps | Carried over, not benchmarked against this render stack | A starting default, not a validated ceiling |
| EL-063 | Override-accumulation thresholds | Stated starting numbers | Tunable in the project record; expect to tune after the first real site |
| EL-064 | Motion-kind homogeneity trigger | Carried-over default | Provisional until real usage data exists |
| EL-065 | All effort estimates | Anchored on comparable-project maturity, not measured work | No figure may be quoted as a measurement |
| EL-068 | A dependency licence discrepancy | Two registries disagree | Re-verify against the licence file at pin time, for every dependency |

---

## 5. Phase 4 — Agent emission

**Outputs emitted and validated:**

| Artifact | Contents | Validation |
|---|---|---|
| `domain-brief.md` | Domain statement, bounded scope, entities, processes, methods, standards, metrics, risks, anti-patterns, terms, CQ pointer, phase-1 assumptions | Read-back check; heading structure verified |
| `domain-cqs.md` | 18 CQs, each with why-it-matters, best answer at compile time with markers, residual unknown, and its lattice node ids; plus the coverage summary | Every cited node id exists in the lattice |
| `domain-lattice.json` | 334 nodes / 546 edges, canonical schema §2.3 | Parses; vocabulary-conformant; zero dangling; zero orphans; zero duplicate ids |
| `evidence-ledger.json` | 88 entries, canonical schema §2.4 | Parses; every required key present on every entry; tiers and confidences in range; every `lattice_node_ids` reference resolves |
| `research.md` | This dossier, including the validation note in §9 | — |
| `research_qa_report.json` | Mechanical QA verdict, schema §2.2 | Parses |

**PM/Dev/QA references.** The instruction sets produced by a later command must reference this lattice and this ledger by id: the PM slice definitions cite CQ ids as the questions a slice must not leave unanswered; Dev evidence bundles cite ledger ids for any claim they rely on; QA re-verifies by recomputing the metric nodes named on the slice rather than trusting a logged value. That expectation is recorded here so the later command has a fixed contract to implement.

---

## 6. Substantive findings

These are the research outputs that change what should be built, as opposed to restatements of the brief.

**F1 — The three weakest answers are all upstream of everything else.** Server survival (CQ6, confidence 0.45), motion judgement (CQ12, 0.35) and the generation-channel ceiling (CQ18, 0.25). Two are addressed by the Phase-0 spike suite. The third has **no known mitigation** and must be stated as a product limitation rather than a backlog item.

**F2 — The component inventory computes to more than twice the volume the schedule was sized against.** 216 rows / 1,228 variants `[V — computed from the section's own table]` versus 87/674 in the open decisions and ~50/~430 behind the timeline and gate budgets. The section states plainly that this is a real scope increase, not a re-labelling. **This is the largest open scope discrepancy in the product** and it compounds with the decision that pulled the canvas into the first shipping version.

**F3 — The purity-gate count and the lock-checklist count are both understated in the carried inputs.** Eight purity gates, not five; 32 lock-time checks, not 28. Both are recorded with the consequential cross-section edits the source could not make itself.

**F4 — The interview bank is 90 questions, not 78**, and the section's own honest estimate (45–55 tier-one questions, 25–35 minutes fast mode) makes the ≤45-answered acceptance criterion unachievable as written. The section says so explicitly and defers the fix rather than editing another section's criteria.

**F5 — Two accessibility criteria apply to the tool itself, not the output.** The design surface *is* a dragging interface, so without a single-pointer alternative the editor fails AA, and editor chrome fails target size by default. This is the most product-specific accessibility fact in the entire source and it is easy to lose when scoping "accessibility" as an output concern.

**F6 — Three Level-A gaps were closed late and carry unfinished cross-section work.** Skip-link presence (the component does not yet exist in the inventory), pause/stop/hide affordances (the container contract needs the field, or the gate can only catch violations after the fact), and asset-reference resolution. Each is a build prerequisite, not a gate to add later.

**F7 — Reading order is a normative invariant, with a hard block.** Document order is always the intended reading order; a per-breakpoint order override is **refused outright on focusable nodes** and warned on others, and any commit that changes mobile stacking must first show a numbered preview of the resulting sequence. This was absent from the carried technical requirements.

**F8 — The drop algorithm is fully specified and was not in the carried requirements.** Row derivation from a spacing-scale row unit with a runaway cap; span preservation with clamping shown before commit; displace-down occupancy with a ghost preview of every block that will move; art-container and opt-in stacking exceptions, both lint-counted; cross-section re-parenting with **no auto-compaction anywhere**; and nine acceptance branches. Building the canvas without this is building a different canvas.

**F9 — The free-position demotion width is contradicted between two sections**, and the resolution matters because one of the two numbers is a width no switcher, preview frame or gate ever renders — so a user could never see the demotion fire before it fired.

**F10 — The scene graph has a different filename in different sections.** Four sections and the carried technical requirements name a single layout file; the file-set and write-allowlist sections name per-page documents plus a project record. The write allowlist is the operative one, so the rename is a prerequisite rather than a cosmetic fix.

**F11 — Open-question identifiers collide four ways**, not two as previously recorded, and proposed acceptance-criterion numbers above ninety collide between two sections. Any downstream traceability that cites a bare identifier is unreliable.

**F12 — Reconciliation, not the guard hook, is the anti-clobber mechanism.** The source ranks its own defences and states each limit honestly: the command-text scan is defeatable, the file mode is a speed bump because both processes share a user, and only the hash journal holds regardless of how the write happened. Any plan that leads with the hook has inverted the ranking.

**F13 — The agent needs a sanctioned write path or the guard gets routed around.** This is stated as a design principle, not a nicety: an instruction the agent follows is cheaper and more reliable than a guard it can accidentally evade.

**F14 — Determinism is the load-bearing assumption of the entire drift story, and its failure mode is silent.** A verify step that produces false positives teaches users to ignore it, after which the guarantee is gone while still appearing to exist. Binary assets are therefore hash-compared rather than re-encoded, because encoders are not bit-stable and re-encoding would manufacture exactly those false positives.

**F15 — Bundler-level reproducibility is unestablished by any consulted source**, and the documented fallback explicitly weakens the export proof. The fallback exists because a gate that fails spuriously gets disabled by whoever is trying to ship — which is the same failure mode as F14, one layer up.

**F16 — Two gates protect against different failures that look identical.** Licence completeness confirms every *recorded* asset carries a licence; reference resolution confirms every *referenced* asset exists. A hallucinated path passes the first and ships a silently broken page.

**F17 — Font fallback metrics are a derived value, and they cannot be produced by the generation channel** because they require the actual selected font binary. That places them in the same computed-not-picked family as spacing and radius scales, and it is a token family the inventory does not yet name.

**F18 — The variant definition is what keeps the budget finite.** Without the line separating structural composition from computed axes, the same product category produces "5 buttons" and "940 variants" in two different libraries. Distinctness is then machine-checkable through a per-component axis vector, which is what makes the presentation rules implementable rather than aspirational.

**F19 — The choice-overload literature was resolved in favour of the meta-analysis**, retaining the thumbnail indistinguishability rule from the opposing lens. Ten variants are safe when the moderators are engineered away; the safeguard is distinguishability, not count.

**F20 — The publish commitment is stricter than the carried default.** Automated deploy is the v1 behaviour with a runbook fallback that **does not** satisfy the locked-and-published exit criterion — and the source flags its own commitment as requiring sign-off.

---

## 7. What must be verified before implementation depends on it

In priority order, all cheap, all recorded in the source's own pre-implementation list and carried into the spec as FR-001 through FR-008:

1. **The font-policy check on the generation surface** — 60 seconds; determines whether the prompt can ask for embedded font data or whether direction selection needs a different mechanism entirely.
2. **The turn-boundary survival probe** — determines whether the standing language rule and the only proven process recipe can coexist. **Blocking.**
3. **Copy-paste fidelity across all three realistic paste paths** — the entire file-header contract depends on fenced blocks surviving; test the rendered view, the per-block copy control, and the conversation export.
4. **The empirical output ceiling** — sets chunk sizes; do not use any published figure.
5. **Live-preview round-trip latency for a move operation** — determines whether the editor needs an optimistic local preview layer.
6. **The topology spike** — single-origin proxy versus two-origin frame with message passing, scored on channel size, preview-only capture achievability, latency and restart behaviour.
7. **Dependency licence re-verification at pin time, against the licence file** — not the registry summary, for every adopted dependency.
8. **The build-reproducibility spike** — because the exit criterion for the first shipping version depends on its outcome.

---

## 8. Risks to this research itself

- **Selective reading is a real limitation.** Roughly half of the design-system and component inventories, the motion sections beyond the container contract, and the later persistence subsections were not read. Requirements drawn from them in a later command must be sourced from the file, not inferred from this dossier.
- **Two inventory subsections are a reconstruction, not a recovery.** Anything derived from them is provisional and flagged for human confirmation.
- **Contradiction resolution is a judgement.** Nine adopted resolutions could each be reversed by the user; every one is recorded with a ledger id and a named cross-section fix so the reversal is cheap.
- **No external verification was possible.** Ecosystem facts are as fresh as the PRD, and the PRD's own fetch dates are the best available provenance.
- **The lattice is a compression.** 334 nodes cannot represent a 641KB requirements document losslessly; it represents the parts that answer the competency questions. Absence from the lattice is not evidence of absence from the product.

---

## 9. Validation note (required by §0.2 phase 4)

**Coverage.** 18 competency questions, 18 covered under the two-hop problem→method→metric→standard definition. **Measured coverage 100.0%, against a ≥95% target.** Coverage was computed from the emitted artifact, not asserted.

**Structural integrity.** 334 nodes, 546 edges, all ten node types and all eight edge relations exercised. Zero dangling endpoints, zero orphan nodes, zero duplicate node or edge ids, zero out-of-vocabulary types, relations or tiers. **No critical structural violations.**

**Evidence quality.** 88 ledger entries: 37 authoritative, 17 expert, 6 empirical, 3 community/vendor-surface, 25 internal. 183 of 334 lattice nodes are directly referenced by at least one ledger entry — the unreferenced remainder are structural nodes (terms, patterns, processes and intermediate metrics) whose support flows through the entries that cite their neighbours. 13 entries carry confidence below 0.5, and each is a schedule figure, an unbenchmarked threshold, or an unverified external surface. **Every open question adopted as a default is recorded as a low-confidence internal entry pointing at its decision item, so any later reversal is traceable.**

**Marker fidelity.** The source's `[V]`/`[I]`/`[U]` markers are preserved on every carried claim. No inference was promoted to fact. Every schedule, effort, duration and volume estimate is tagged inference with low confidence, including the canvas effort range, the decision-driven schedule delta, the inventory volume gap, and the interview duration bands.

**Honest gaps, stated rather than resolved.** Motion feel cannot be judged in-editor and has no known mitigation. Sibling-anchored free positioning is unprototyped. Bundler byte-reproducibility is unestablished. The generation-channel ceiling is unknown and its published figures are unreliable. The component-set volume is contested three ways. Two inventory subsections are reconstructions. Four open-question identifiers collide across sections.

**Verdict.** The research phase satisfies its gates: preconditions met, all six artifacts emitted to disk at the absolute feature directory, both JSON artifacts schema-conformant and machine-validated, coverage above target, and no fabricated sources. **QA status: APPROVED**, with the recorded conditions carried forward as assumptions rather than as blockers, per the determinism contract.
