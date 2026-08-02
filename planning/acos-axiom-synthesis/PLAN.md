# acos-axiom-synthesis — Design & Build Blueprint

**Status:** Plan (not yet built)
**Date:** 2026-06-25
**Author:** Architect (orchestrator), from swarm-research session `swarm-20260625-113200`
**Source research:** `.acos/swarm/swarm-20260625-113200/synthesis/report.md` (12 isolated agents, cross-referenced)
**One-line purpose:** Fuse outputs from multiple AI agents and/or different LLMs into ONE coherent, authoritative, *defeasible* source-of-truth file — or an explicit refusal — never a fabricated consensus.
**Revised:** 2026-07-06 — added §15 Runtime rigor (single-writer invariants · formal state-machine spec · pure-function resumable frontier · oscillation guard) + three open decisions (§12.6–8), adapted from `acos-synthesis-protocol`.
**Revised:** 2026-07-22 — implemented two boss-requested improvements (§17): the boolean **confidence checklist** (veto + percentage → tier) and the concrete **four-family fan-out** (Claude · Gemini · z.ai/GLM · ChatGPT-browser). Closes/updates open decisions §12.2 and §12.4.

---

## 1. What this skill is (and is not)

`acos-axiom-synthesis` takes several independent analyses of the same question — produced by different agents, different models, or different runs — and produces a single **source-of-truth artifact** in which every claim carries a graded confidence tier, a citation back to its origin, the alternatives that were considered and rejected, and a tamper-evident provenance record.

**It is a refutation-and-grading engine, not a merger.** The defining research finding (reached independently by 8 of 12 isolated agents) is that naively merging agent outputs *propagates plausible-but-false claims* and *manufactures false confidence* from correlated sources. The skill's value is the discipline it imposes between "many opinions" and "one authoritative answer."

**It is NOT:**
- a general knowledge base (one file answers one scoped question);
- a place that trusts a model's self-reported confidence;
- a single big LLM that "writes the truth";
- a system that ever silently resolves a conflict or fabricates a winner.

### 1.1 Design philosophy (five non-negotiables)

1. **Independence is the currency.** Agreement only counts as corroboration when sources are genuinely independent. Correlated agreement is treated as a single vote.
2. **Confidence is derived, ordinal, and provenance-bound.** Never self-reported, never a fake decimal.
3. **Truth is defeasible.** The output is a timestamped snapshot of the current best-supported claim set, always re-openable. Nothing is "final."
4. **Refuse over fabricate.** When evidence cannot adjudicate, the engine emits `UNRESOLVED` and surfaces alternatives.
5. **Recompose, don't reinvent.** Most mechanisms already exist and are unit-tested inside ACOS; the skill wires them together.

---

## 2. The layered model (how the research stratifies)

The six seed ideas are not competing methodologies — they are the **layers of one pipeline**. This is the central architectural insight.

| Layer | Supplies | From seed idea / agent |
|-------|----------|------------------------|
| **Epistemology / state machine** | claims are graded & revisable; the 6-state lifecycle | Scientific method (Agent 03) |
| **Grading rubric** | two independent axes; baseline→downgrade→upgrade | CIA/Admiralty + GRADE (Agents 04, 06) |
| **Fusion math** | claim-level voting, median, linear opinion pool | Source-fusion theory (Agent 07) |
| **Weighting prior** | dual-track tally; believability as a *secondary* prior | Dalio/Bridgewater, inverted (Agents 01, 02) |
| **The gate** | falsification, ACH, independent refuter, nullification | Falsification (Agent 08) + LLM ensemble (Agent 09) |
| **The substrate** | hash-chained, provenance-bound, append-only ledger | Hashable evidence ledger (Agent 10) |
| **The output discipline** | living, scoped, supersede-not-overwrite SSOT | Output schema (Agent 12) |
| **The shortcut** | reuse `hca-*` engines, swarm harness, ACOS conventions | ACOS-native patterns (Agent 11) |

---

## 3. Core architecture — the 7-stage pipeline

Each stage operates on **atomic claims** (single, checkable assertions), not whole documents. The pipeline is the heart of the skill.

```
INPUTS (N artifacts, or a question to elicit on)
   │
   ▼
[1] DECOMPOSE & ELICIT (blind, cross-family diverse)
   │   → atomic claims with raw provenance
   ▼
[2] DE-CIRCULARIZE (collapse non-independent sources → 1)   ◄── citogenesis firewall
   │   → independence-clustered claims
   ▼
[3] GRADE ON TWO AXES (source reliability × claim certainty)
   │   → each claim carries Axis-A + Axis-B ordinal scores
   ▼
[4] FUSE PER CLAIM (vote / median / linear-pool + dual-track tally)
   │   → one candidate value per claim + divergence flag
   ▼
[5] FALSIFY (admissibility → steelman → ACH → independent refuter)
   │   → disposition: keep / downgrade / nullify
   ▼
[6] RESOLVE OR ABSTAIN (precedence ladder → else UNRESOLVED)
   │   → adopted claim + recorded alternatives, or abstention
   ▼
[7] WRITE THE LEDGER (append-only, hash-chained) + RENDER MD
   │
   ▼
OUTPUT: claims.jsonl (canonical) + source-of-truth.md (human)
```

### Stage 1 — Decompose & elicit (blind, diverse)
- If inputs are pre-existing artifacts: ingest and decompose each into atomic claims, tagging each claim with its source artifact + locator.
- If the skill is asked to *generate* the inputs: spawn **3–4 models from different families/providers** on the question (NOT the three strongest single models — they share correlated errors). Dispatch **blind** (information hiding: each agent knows only its own output path; no agent sees another's work). Reuse the `acos-swarm-research` / `blind-extractor` harness.
- Output: a flat list of atomic claims, each `{statement, source_ref, surfaced_by, raw_locator}`.

### Stage 2 — De-circularize (mandatory pre-pass)
- Cluster claims by **traced origin**. Collapse a cluster to a single representative if ANY trigger fires:
  - shared upstream source (chains terminate at the same document/dataset);
  - verbatim fingerprints (identical phrasing/numbers, or the *same error* reproduced);
  - same generative origin (same base model / provider / prompt / context → *presumed* correlated);
  - no traceable provenance (demote to single/unverified, never a corroborator);
  - the engine's own prior output reappearing as an input (self-citation loop).
- There is **no reliable automated independence detector** — use presumption + flags, not measurement.
- Output: independence-clustered claims; corroboration counting from here on uses *independent* count only.

### Stage 3 — Grade on two axes
Score every claim on two **separate** ordinal axes (never blended into one number):
- **Axis A — Source reliability** (prior): how trustworthy is the originating source/agent, from track record + family diversity. Admiralty-style A–F, or a 3-tier collapse.
- **Axis B — Claim certainty** (evidence): GRADE machine — baseline by source type → downgrade for defects → upgrade for corroboration → one ordinal ladder.
  - Baseline: cited primary artifact + ≥2 heterogeneous-family agreers = top; single-model assertion w/o grounding = bottom.
  - Downgrade (−1 serious / −2 very serious): source bias; cross-model inconsistency; indirectness/relevance mismatch; imprecision/thinness; selection bias.
  - Upgrade (+1/+2): strong unambiguous verbatim citation; consistency under perturbation; survives adversarial review.
- **Confidence is derived from independent agreement + provenance — never model self-report.**

### Stage 4 — Fuse per claim
- **Categorical claims** → (weighted) majority vote. Equal weights by default; use weights only when a verifiable calibration subset exists (log-odds / Nitzan–Paroush). Never self-assigned weights.
- **Numeric claims** → **median or trimmed mean** (one hallucinated outlier wrecks a plain mean).
- **Confidence values** → linear opinion pool (safe; never more confident than inputs). LogOP only with correlation discount.
- **Dual-track tally (the Dalio import, inverted):** compute BOTH the equal-weighted and the believability-weighted result. *Agreement between them = a confidence signal; divergence = an escalation trigger.* On divergence, prefer the **evidence-weighted** answer (not source-weighted), and flag for the falsification gate.
- Output: one candidate value per claim + a `divergence` flag.

### Stage 5 — Falsify (the load-bearing gate)
Every candidate claim must pass before it can be written. Default disposition of an unprocessed claim is `Unverified/quarantined`, NOT `accept`.
- **Step 0 — Admissibility (Popper):** Is it falsifiable? State the observation that would falsify it. Forbids nothing → nullify as opinion (recorded, labeled, outside the truth set).
- **Step 1 — Steelman:** reconstruct the strongest evidence-grounded version; attack *that* (don't inflate beyond evidence).
- **Step 2 — Independent corroboration:** count supporters NOT sharing source / model-family / derivation chain.
- **Step 3 — ACH disconfirmation:** enumerate alternatives (incl. "wrong / mis-attributed / stale / fabricated"); score by *inconsistency*; delete zero-diagnosticity "support"; keep the least-inconsistent; record disconfirmers as live nullification conditions.
- **Step 4 — Independent refuter (NON-NEGOTIABLE):** an adversarial critic that is a **different model family** from the claim's generator(s). A model cannot reliably falsify its own claims (intrinsic self-correction degrades accuracy; same-family judges show self-preference bias). Escalate contested/high-stakes claims to a short heterogeneous debate. Budget: cheap refuter on all claims, deep refuter only on contested ones.
- **Step 5 — Disposition** via the nullification checklist (§6.3).

### Stage 6 — Resolve conflicts or abstain
When claims about the same atomic fact conflict, apply the precedence ladder (§6.4) top-down; stop at the first rung that decides. If still unresolved → emit **`UNRESOLVED`**: record all surviving claims, tiers, provenance, capped confidence, surfaced as explicit alternatives. **Never fabricate a winner.**

### Stage 7 — Write the ledger + render
- Append each claim-version to the canonical, hash-chained `claims.jsonl` (§5).
- Re-render `source-of-truth.md` from the ledger (the human view is always generated, never hand-edited).
- Re-synthesis **appends + supersedes**, never overwrites.

---

## 4. The claim-state lifecycle

A state machine governs each claim across synthesis runs (enables the "living document" use case).

| State | Meaning | Entry condition |
|-------|---------|-----------------|
| `CONJECTURE` | single source, untested | asserted by one source, not cross-checked |
| `CORROBORATED` | survived ≥1 independent check; not refuted | independently checked, not contradicted, has provenance |
| `ESTABLISHED` | multi-source convergence; defends all attackers | independent corroboration ≥ threshold AND no surviving attacker (still defeasible) |
| `CONTESTED` | a comparably-supported contradiction exists | a surviving attack of comparable grade |
| `SUPERSEDED` | displaced by a better-supported claim | a stronger claim wins; old archived (not deleted) |
| `REFUTED` | directly contradicted by stronger evidence | higher-grade contradiction with no defense; archived with reason |

**Rules:** single-source claims are capped at `CORROBORATED`. Demotions **cascade** to dependent claims (lightweight dependency flags + a re-evaluation queue). `SUPERSEDED`/`REFUTED` claims are archived (revivable if their refuter is later refuted), never deleted.

### 4.1 Legal transitions (formal + mechanically enforced)
The lifecycle is not just a table — it is a **state machine with a fixed set of legal moves**, shipped as a companion `STATE-MACHINE.md` that is *the authority when prose and code disagree*. Exactly one component (`ledger-writer.py`, §15.1) may change a claim's `state`, and it **refuses any transition not in the legal set** by exiting non-zero. See §15.1–15.2 for the enforcement and the full legal-transition graph.

---

## 5. Data model — the evidence ledger

### 5.1 Physical form
- **Canonical:** `claims.jsonl` — append-only, one JSON object per line, hash-chained.
- **Human view:** `source-of-truth.md` — generated from the ledger; never hand-edited.
- **Evidence blobs:** `evidence/sha256-<hex>` — content-addressed raw agent outputs, referenced by hash.
- Everything git-tracked → free tamper-evidence via commit history + the dual-remote mirroring already in use.

### 5.2 Claim record (one line of claims.jsonl)
```json
{
  "id": "CLM-0007",
  "statement": "<the claim, stated plainly>",
  "claim_type": "categorical | numeric | textual",
  "core": "<core assertion>",
  "qualifiers": {"scope": "...", "as_of": "...", "units": "..."},
  "state": "ESTABLISHED",
  "confidence": "verified",
  "confidence_basis": {
    "independent_agreement": "3/3 distinct-family agents",
    "independent_sources": 2,
    "axis_a_source_reliability": "B",
    "axis_b_claim_certainty": "High"
  },
  "provenance": [
    {"source": "<doc/url/dataset>", "locator": "p.4 ¶2",
     "surfaced_by": "model-x", "family": "provider-x",
     "evidence_blob": "sha256-abc…"}
  ],
  "alternatives": [
    {"statement": "<conflicting claim NOT adopted>",
     "held_by": ["model-y"], "provenance": [...],
     "why_not_adopted": "weaker provenance; refuted by 2 primary sources"}
  ],
  "disconfirmers": ["<evidence that would overturn this>"],
  "depends_on": ["CLM-0003"],
  "supersedes": null,
  "superseded_by": null,
  "first_synthesized": "2026-06-20T09:00Z",
  "last_reviewed": "2026-06-25T11:32Z",
  "last_run": "run-0003",
  "prev_hash": "sha256-…",
  "entry_hash": "sha256-…"
}
```

### 5.3 Confidence tiers (pick ONE scale, embed definitions in the file)
Recommended (matches existing ACOS vocabulary):
- **verified** — ≥2 *distinct-family* agents AND ≥2 *independent* sources; re-synthesis unlikely to change it.
- **probable** — supported but single-source OR single-family agreement OR minor unresolved tension (single-source is capped here, never "verified").
- **unverified** — one agent, weak/absent provenance, or contested; a lead, not a fact.

> Do **not** run two certainty scales at once (e.g., GRADE 4-level + CIA 3-level). If numeric likelihood is needed, keep it as a *separate* axis using estimative-probability words, not a second certainty ladder.

### 5.4 Hashing & chaining (~150 LOC stdlib verifier)
- `entry_hash = SHA-256( domain_prefix + JCS-canonical(record_without_entry_hash) )`.
- Feasibility shortcut: store numbers as strings → `json.dumps(sort_keys=True, separators=(",",":"))` gives RFC-8785-equivalent determinism without a full JCS implementation.
- Each entry's `prev_hash` = the previous entry's `entry_hash`; a single `ledger.head` hash is the compact commitment, echoed into `source-of-truth.md` front-matter.
- **SKIP** blockchain, Merkle trees, full W3C PROV-O/RDF, Verifiable Credentials — git + hash-chain is sufficient.

### 5.5 Rendered source-of-truth.md
YAML front-matter (synthesis_question, schema_version, last_synthesized, contributors + family + diversity note, ledger.head, confidence_tier definitions) + body grouped by topic, with **prominent top-level sections**: `UNRESOLVED CONFLICTS`, `OPEN QUESTIONS`, `SUPERSESSION LOG`.

### 5.6 One writer, mechanically gated (see §15.1)
The ledger has exactly ONE writer, `ledger-writer.py`. Nothing else may set a claim's `state`/`confidence`. It enforces the corroboration gate, single-source cap, falsification gate, and dependency integrity by **refusing illegal writes with a non-zero exit** — turning the caps stated as *policy* in §4/§6 into mechanical invariants that cannot be forgotten under load.

---

## 6. Decision mechanics (the rubrics)

### 6.1 The two-axis grading rubric
See §3 Stage 3. Axis A (source reliability prior) and Axis B (claim certainty via GRADE machine) are scored and stored separately.

### 6.2 Confidence derivation
`confidence = f(independent_agreement_count, provenance_strength)` — bounded by the single-source cap. Self-reported model confidence is **ignored**.

### 6.3 Nullification checklist (Stage 5 disposition)
**HARD → NULLIFY** (drop or quarantine for human review):
- unfalsifiable (forbids no observation);
- refuted by higher-tier evidence;
- internal contradiction (with itself or an `ESTABLISHED` claim);
- fabrication / no traceable origin;
- emerged from ACH as the *most* inconsistent hypothesis.

**SOFT → DOWNGRADE one tier** (never "verified"):
- single-source / no independent corroboration (cap at probable);
- source conflict-of-interest;
- stale / superseded (fails currency);
- non-reproducible from stated inputs;
- vertical-only support (no lateral corroboration);
- consensus among non-independent sources (same-family ≈ one source);
- refuter raised a credible unrebutted objection (keep, downgrade, record as live disconfirmer).

### 6.4 Conflict-precedence ladder (deterministic tie-break)
- **Rung 0 — DE-CIRCULARIZE FIRST** (Stage 2; mandatory before any counting).
1. Directness / proximity to origin (primary > secondary > tertiary).
2. Best-evidence / originality (original > copy > paraphrase).
3. Source reliability track record (Axis A).
4. Authority / domain jurisdiction (authoritative *for that subject*).
5. Independent corroboration count (post-Rung-0).
6. Evidentiary weight / sample size.
7. Specificity & internal consistency.
8. Recency-with-supersession (newer wins only if an explicit correction from ≥ equal tier AND not outweighed by heavier independent corroboration; else stability wins).
9. Conflict-of-interest adjustment (down-weight self-serving; up-weight against-interest).
10. **TERMINAL — REFUSE TO FABRICATE A WINNER** → emit `UNRESOLVED`.

### 6.5 Consensus polarity (choose per decision type)
- **Asymmetric veto** (any single dissent wins, no loop) — where a false-accept is catastrophic (e.g., a safety/privilege/load-bearing financial claim).
- **Quorum-to-agree** (default 2-of-3) — for ordinary claims.
- **Unanimous-or-keep-all** — for "select the single winner" sub-tasks (asymmetric veto there yields "nobody wins").

---

## 7. Agent roster & model strategy

The skill is an **orchestrator skill** (thin main context) that spawns agents via `Task()`. Per ACOS convention, restricted agents in `.claude/agents/` need human approval — so prefer reusing `general-purpose` with role prompts (precedent: `acos-synthesis-protocol` spawns Builder/Verifier/Integrator as general-purpose).

| Role | Count | Independence | Model strategy |
|------|-------|--------------|----------------|
| **Claim extractor / elicitor** | 3–4 | blind, isolated | **cross-family** (e.g., Claude + a different provider via the model-profile system); NOT three of the strongest single model |
| **Grader** (two-axis) | per-claim, internal | — | can be a deterministic Python pass + one LLM judgment where needed |
| **Independent refuter** | 1 (+debate on contested) | adversarial | **different family** from the generators — structural requirement |
| **Synthesizer** | 1, *defended* | merge-never-author | grounded (every output claim cited + entailment-verified) + CoVe pass + independent verify |

> **Model access:** subscription-only Claude via `Task()`; NEVER `ANTHROPIC_API_KEY`. External/different-family models go through the existing model-profile system / `run-external-agent.py`. If only Claude is available, achieve diversity via different model *classes* (Opus/Sonnet) + prompt/temperature diversity, and clearly flag that cross-family independence is reduced.

---

## 8. ACOS reuse map (do not reinvent)

| Need | Reuse | Source |
|------|-------|--------|
| Substance consensus, asymmetric quorum, no-silent-pick → ESCALATE | `hca-consensus.py` (pure-Python, injected `agent_runner`) | acos-hypercore-ask |
| Provenance binding + content-addressed immutable cache | `hca-provenance.py`, `hca-cache.py` | acos-hypercore-ask |
| Deterministic post-consensus gates (schema, reconciliation, freshness, cap≤0.7) | `hca-gates.py` | acos-hypercore-ask |
| Blind isolation harness + synthesizer skeleton | `acos-swarm-research` SKILL + `blind-extractor.md` | swarm/hypercore |
| Dual-axis consensus thresholds + blind re-dispatch | grader (±5% rel / ±0.5 abs floor; ≥90% reasoning) | acos-grader |
| Asymmetric-veto pattern | dataroom-v2 (any single EXCLUDE wins) | acos-dataroom-v2 |
| Convergence-vs-synthesis modes + never-gives-numbers reconciler | fin-stmt-accountant | acos-financial-statement |
| Conflict-preservation table; confidence ladder | deep-research / swarm-research | both |
| Document pre-shrink for large inputs | `document-synthesis` synthdocs | document-synthesis |
| Entity resolution / cross-source linking | `knowledge-graph` (alias-aware dedup, SAME_AS) | knowledge-graph |
| Bounded blind re-dispatch → flag (Wigum loop) | grader / dataroom loop contract | multiple |
| Single status-writer + pure-function resumable frontier + formal state-machine | `set-status.py` / `next-ready.py` / `STATE-MACHINE.md` pattern (§15) | acos-synthesis-protocol |

**Conventions to conform to:** SKILL.md frontmatter; windowed batch-wait parallel `Task()`; state under `.acos/` (git-ignored); a **single status-writer** (§15.1) as the only mutator of claim state; a **pure-function resumable frontier** over on-disk state (§15.3), with `run_state.json` as a cache, not the source of truth; `resolve-agent-model.sh` for model overrides; stdlib-only Python; clickable `file://` links; the Independence Wall.

---

## 9. INCLUDE / SKIP (build vs avoid)

### INCLUDE
Cross-family diversity · blind elicitation · de-circularization pre-pass · two-axis ordinal grading · derived (not self-reported) confidence · dual-track tally with divergence-escalation · independent different-family refuter + ACH + nullification checklist · claim-level fusion (median/vote/linear-pool) · conflict preservation + first-class `UNRESOLVED` + refusal-over-fabrication · per-claim provenance binding · append-only hash-chained ledger · single-source cap · 6-state lifecycle · per-decision consensus polarity · Wigum bounded re-dispatch · missing/empty return = INCONCLUSIVE · explicit written merge rules + full audit trail · **single ledger-writer with exit-code-enforced invariants (§15.1)** · **formal `STATE-MACHINE.md` as authority (§15.2)** · **pure-function resumable frontier (§15.3)** · **oscillation guard / settled-objections injection (§15.4)** · **ACOS evidence/metrics mirror + final coverage gate (§15.5)**.

### SKIP
Trusting model self-reported confidence · fake numeric precision · single unconstrained synthesizer as sole arbiter · silent conflict resolution · overwrite-on-update · counting N runs of one model as N votes · full Dempster-Shafer · full truth-discovery EM · blockchain/Merkle/full-ontology stacks · Bridgewater's proprietary formula + human-org machinery · personality attributes in scoring · a precise automated LLM-independence detector · a second/bespoke consensus engine or confidence vocabulary · caching synthesized *values* across runs · scope creep into a general KB · literal "final truth/law," literal incommensurability, numeric LLM probabilities, pure majority-vote.

---

## 10. Skill interface

### 10.1 SKILL.md frontmatter (draft)
```yaml
---
name: acos-axiom-synthesis
description: Synthesize outputs from multiple AI agents and/or different LLMs into ONE
  coherent, authoritative, defeasible source-of-truth file — or an explicit refusal —
  never a fabricated consensus. Decomposes inputs into atomic claims, de-circularizes
  correlated sources, grades each claim on two axes, fuses claim-by-claim, runs an
  independent different-family falsification gate, preserves conflicts, and writes a
  hash-chained append-only claim ledger rendered to Markdown. Use to reconcile multiple
  analyses / model outputs / agent reports into a trusted single document.
user-invocable: true
argument-hint: "[question or path-to-inputs] [--mode actual|synthesis] [--models N]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, WebSearch, WebFetch
---
```

### 10.2 Invocation & wizard
- Wizard by default; CLI args override.
- Inputs: either (a) a set of existing artifacts/paths to reconcile, or (b) a question for the skill to elicit on with fresh cross-family agents.
- Mode: `actual` (truth is singular → require convergence, refuse if impossible) vs `synthesis` (judgment blend → expect divergence, synthesize best-supported).
- Args: `--models N` (default 3–4), `--scale` (confidence ladder), `--polarity` (per-decision default).

### 10.3 Outputs
- `claims.jsonl` (canonical), `source-of-truth.md` (rendered), `evidence/` blobs, `run_state.json` (resumable), and a clickable `file://` link to the rendered file.

### 10.4 Workspace layout
```
.acos/axiom/<session-id>/
  plan.md
  agent-NN/ (blind elicitation outputs)
  claims.jsonl
  evidence/sha256-<hex>
  source-of-truth.md
  run_state.json
```

---

## 11. Phased build sequence (with acceptance criteria)

### Phase 0 — Scaffolding
Create the skill dir + SKILL.md skeleton; wire `resolve-agent-model.sh`; create the `.acos/axiom/<session-id>/` workspace + `run_state.json` checkpointing.
**Accept:** skill is invocable; workspace + checkpoint created; health check passes.

### Phase 1 — Ledger + writer + verifier (the substrate)
Implement `claims.jsonl` append, `entry_hash`/`prev_hash` chaining, content-addressed `evidence/` blobs, and the ~150-LOC stdlib verifier. Implement the **single `ledger-writer.py`** (the only state mutator, exit-code-enforced invariants — §15.1), the companion **`STATE-MACHINE.md`** legal-transition spec (§15.2), the **pure-function `next-claims.py` frontier** (§15.3), and the `source-of-truth.md` renderer.
**Accept:** a hand-seeded ledger round-trips; verifier detects a tampered line; `ledger-writer.py` **refuses** an illegal transition (e.g. `verified` on a single source) with a non-zero exit; killing the process mid-run and re-running resumes from disk with no lost or duplicated work; rendered MD shows tiers, provenance, alternatives, and the three prominent sections.

### Phase 2 — Decompose + de-circularize
Atomic-claim extraction; the independence-clustering pre-pass with all five collapse triggers; presumption-based correlation flags.
**Accept:** on a fixture with two copies of one source, the duplicate collapses to one vote; a self-citation loop is excluded; flags are recorded.

### Phase 3 — Two-axis grading + fusion
Axis-A/Axis-B scoring; claim-level fusion (median/vote/linear-pool); dual-track tally + divergence flag; single-source cap. Reuse `hca-consensus.py` (injected `agent_runner`).
**Accept:** numeric outlier doesn't move the median; single-source claim caps at "probable"; divergence between equal- and weighted-tracks raises a flag.

### Phase 4 — Falsification gate (+ oscillation guard)
Admissibility → steelman → independent corroboration → ACH → **independent different-family refuter**; nullification checklist; graded downgrade. Add the **oscillation guard** (§15.4): record each adjudicated objection to `settled-objections.md` and inject it into every later refuter prompt.
**Accept:** an unfalsifiable claim is nullified; a fabricated/no-provenance claim is nullified; a claim the refuter breaks is downgraded with a recorded disconfirmer; the refuter is verifiably a different family from the generator; a settled objection is **not** re-raised in a later round (the loop converges, it doesn't just cap out).

### Phase 5 — Conflict resolution + abstention
Precedence ladder; `UNRESOLVED` emission with alternatives; per-decision consensus polarity; reuse `hca-gates.py`.
**Accept:** a genuine conflict with no deciding rung yields `UNRESOLVED` (not a fabricated winner); asymmetric-veto path vetoes on a single dissent for flagged decision types.

### Phase 6 — Lifecycle + living re-synthesis
6-state machine (enforced by `ledger-writer.py` against `STATE-MACHINE.md`, §15.2); supersede-not-overwrite; demotion cascade; archive (never delete).
**Accept:** re-running on updated inputs appends new versions, marks `superseded_by`, cascades demotion to dependents, and preserves history; a revived claim works; every illegal transition is refused by the writer.

### Phase 7 — Coverage gate, mirror, hardening + review
Add the **final coverage gate** (§15.5 — no sub-question of the scoped question left with zero claims), the **ACOS evidence/metrics mirror** (§15.5 — runs appear in `/acos-status`), and the **random spot-test** prompt (invite the user to check 2–3 `verified` claims against provenance). Run `/acos-robust-code-review` (or `/acos-swarm-review`); add fixtures; validate against the §13 ground-truth seed cases; write user-guide section.
**Accept:** the coverage gate blocks a run that leaves a sub-question uncovered; runs appear in `/acos-status`; review converges to zero findings; ground-truth cases pass; docs complete.

---

## 12. Open design decisions (tune during build)
1. **Model count / refuter count** — start 3–4 diverse + 1 different-family refuter; tune.
2. **Confidence thresholds** — corroborations→tier; contradiction-strength→demotion. Make configurable.
3. **How "defended" the synthesizer must be** — grounding + CoVe + independent verify vs cost.
4. **Claude-only fallback** — when no different-family model is available, how strongly to flag reduced independence.
5. **Flat ledger vs full lifecycle** — one-shot synthesis may use a flat graded ledger; "living" use needs the full state machine.
6. **Bounded, provenance-checked reuse vs. never-cache (tension from `acos-synthesis-protocol`).** §9 currently bans caching synthesized *values*. synthesis-protocol reuses proven artifacts gated by re-verification. Decide whether an already-`ESTABLISHED`, freshness-checked claim (especially one from a trusted upstream like `acos-hypercore-ask`) may be **reused *with* re-verification** instead of re-elicited from scratch. Reuse-with-recheck ≠ blind cache; gate on the staleness risk, not on reuse itself.
7. **Ranked-culprit drill-down + "upgrade, not retry" vs. blind cascade (tension).** §4 cascades demotion to *all* dependents blindly (which preserves independence). synthesis-protocol instead ranks the *likely* culprit and upgrades it with feedback. Decide per loop-type: keep **blind re-elicitation** for fresh independent claims, but allow **targeted, feedback-driven upgrade** when *repairing* a specifically-broken claim.
8. **Optional human-verification gate vs. autonomous abstain-only (tension).** The plan is fully autonomous (abstain → `UNRESOLVED`). synthesis-protocol pauses for a human verdict on claims a machine cannot verify ("an LLM cannot read a thrust gauge"). Decide whether high-stakes, un-independently-corroborable claims should optionally **pause for a human verdict** rather than only abstain.

---

## 13. Validation / test plan
- **Ground-truth seed cases** (Dalio "back-test" analog): assemble cases where the correct synthesized answer is known, plus adversarial cases (one confident-but-wrong source; two correlated copies of a wrong claim; an unfalsifiable assertion; a genuine irreducible conflict). The engine must: not be fooled by correlated agreement; nullify the unfalsifiable; abstain on the irreducible conflict; cap the single-source claim.
- **Tamper test** — verifier catches a mutated ledger line.
- **Independence test** — duplicate-source fixture collapses; cross-family refuter enforced.
- **Regression fixtures** — checked into the skill, runnable offline (no live API).

---

## 14. Risks & mitigations
| Risk | Mitigation |
|------|------------|
| Correlated models fake corroboration | de-circularization pre-pass; cross-family diversity; same-family ≈ one vote |
| Synthesizer LLM hallucinates / flattens disagreement | grounded + entailment-verified + CoVe + independent verify; conflict-preservation |
| Self-preference / self-confidence bias | different-family refuter; ignore self-reported confidence |
| False precision over-trusted by readers | ordinal tiers only, with embedded definitions + dates |
| Stale "source of truth" | freshness metadata; cheap idempotent re-synthesis; supersede-not-overwrite |
| Claude-only deployment reduces independence | flag reduced independence; use model-class + prompt diversity as partial substitute |
| Scope creep into a general KB | one file = one scoped question; refuse/spawn-new for out-of-scope |

---

## 15. Runtime rigor (borrowed from `acos-synthesis-protocol`)

The plan above is strong on *epistemology* (grading, falsification, independence) but was thin on *runtime rigor* — keeping the machine itself from losing or corrupting state while it runs. These mechanisms are adapted from `acos-synthesis-protocol` (the bottom-up build engine), whose `set-status.py` / `next-ready.py` / `STATE-MACHINE.md` design solves exactly this class of problem. Different domain (it composes built artifacts, not opinions), same discipline.

### 15.1 One ledger-writer that refuses illegal writes (mechanical invariants)
Make the claim-state invariants *mechanical*, not advisory. Exactly ONE component — `ledger-writer.py` — may change a claim's `state`/`confidence`; every other part of the pipeline calls it. It **refuses an illegal write by exiting non-zero** (a hard stop), so a violation halts the run instead of silently entering the ledger. Enforce at minimum:
- **Corroboration gate** — refuse `state=ESTABLISHED` (or `confidence=verified`) unless the record has ≥2 *independent, distinct-family* sources. (Mirrors synthesis-protocol's parent-gate, exit 3.)
- **Single-source cap** — refuse `verified` on a single-source claim (cap at `probable`).
- **Falsification gate** — refuse promoting a claim above `CONJECTURE` until it has passed the Stage-5 gate. (Mirrors the hardening-gate, exit 4.)
- **Dependency integrity** — refuse `ESTABLISHED` while any `depends_on` claim is `REFUTED`.

Rationale: a rule you only *write down* (in this plan) is a suggestion; a rule one gatekeeper *refuses to violate* is an invariant. This closes the gap where §4/§6 state the caps as policy.

### 15.2 A formal state-machine spec as the authority
Ship `STATE-MACHINE.md` alongside the skill: the states table (§4), the **explicit legal-transition graph**, and the hard invariants — declared as *"the authority when prose and code disagree."* The ONLY transitions the writer permits:
- `CONJECTURE → CORROBORATED → ESTABLISHED` (happy path; each step gated by §15.1).
- `* → CONTESTED` when a surviving comparable-grade attack appears.
- `ESTABLISHED`/`CORROBORATED → SUPERSEDED`/`REFUTED` (demotion; archived, not deleted).
- `SUPERSEDED`/`REFUTED → CONTESTED`/`CORROBORATED` only via **revival** (the claim's refuter was itself later refuted).

No other transition is writable. This removes ambiguity and gives the writer (§15.1) a definitive checklist to enforce.

### 15.3 A pure-function, resumable frontier
All state lives on disk (the ledger). Add `next-claims.py` — a **pure function** that reads the ledger and returns the work frontier: which claims still need elicitation, grading, falsification, or conflict-resolution. To resume after any interruption, re-run it; there is no in-memory to-do list to lose. This upgrades §8's vague "resumable `run_state.json`" into synthesis-protocol's proven model — the frontier is a *pure function of on-disk state*, so an interrupted synthesis resumes exactly where it stopped, and `run_state.json` is a cache/optimization, not the source of truth.

### 15.4 An oscillation guard for the refuter loop
The Stage-5 refuter is deliberately *fresh each round* (for independence), so it will re-raise objections already adjudicated — an infinite-loop risk. Fix: when an objection is ruled on, record the ruling in a per-session `settled-objections.md` and **inject it into every later refuter prompt** ("these points are settled — do not re-raise: …"). Keeps the refuter fresh for *new* attacks while silencing re-litigation. Mirrors synthesis-protocol's oscillation guard + `known-design-choices.md` injection. Bounds the Wigum loop by *convergence*, not merely an iteration cap.

### 15.5 Smaller integration & UX items
- **ACOS-visible evidence/metrics mirror** — besides the self-contained ledger, append a one-line completion record per run under `.acos/evidence/<date>/axiom-<session>/…` and log agent identity to `.acos/metrics/agent-completions.log`, so synthesis runs surface in `/acos-status` and metrics tooling (as synthesis-protocol mirrors its verdicts). The ledger stays the canonical source; this is a convenience mirror.
- **Live render + random spot-test** — re-render `source-of-truth.md` after each decision (not only at the end) for a live view; end each run by inviting the user to spot-check 2–3 random `verified` claims against their provenance.
- **Final coverage gate** — before declaring done, confirm the synthesis covers every facet of the scoped question (no sub-question with zero claims) — the epistemic analog of synthesis-protocol's success-criteria coverage gate.
- **Preflight state guard** — at startup, detect a stale prior-run lock / `run_state.json` for this question and resume-or-warn rather than silently starting over.

### 15.6 What does NOT transfer (and why the plan already covers the analog)
- **Hardening gate = literal code review** — synthesis-protocol code-reviews each built artifact. The axiom analog is the **falsification gate** (§3 Stage 5), already the load-bearing gate; a claim is not code.
- **Contract-based composition** — it wires child artifacts into a parent via contracts. Axiom claims aren't composed into a parent object; the "no silent assembly" guarantee is already covered by no-silent-conflict-resolution + refusal (§3 Stage 6).
- **Capability-tag reuse registry** — build-specific artifact matching. The reuse *principle* is captured as an open decision (§12.6), not the machinery.

---

## 16. Appendix — seed-idea provenance & verdicts

| Seed idea | Verdict | Where it lives in this plan |
|-----------|---------|------------------------------|
| 1. Dalio/Bridgewater | CONFIRM (protocol shape only) | §3 Stage 4 (dual-track tally), §7 |
| 2. Scientific method | CONFIRM (with refinements) | §4 (lifecycle), §1.1 (defeasibility) |
| 3. CIA tiers + precedence | CONFIRM (two axes; ladder; refuse-terminal) | §3 Stage 3, §6.1, §6.4 |
| 4. Hashable evidence ledger | INCLUDE (scoped) | §5 |
| 5. Dalio → tiered ledger | SOUND (inverted: evidence-first) | §3 Stage 4, §6.1–6.2 |
| 6. Falsify / nullify | CONFIRM (the load-bearing gate) | §3 Stage 5, §6.3 |
| "etc." — GRADE/CERQual, fusion theory, LLM-ensemble, SSOT/ADR, ACOS reuse | adopted | §3, §5, §6, §8 |
| Runtime rigor — single-writer invariants, formal state-machine, resumable frontier, oscillation guard | ADOPTED (§15); 3 tensions logged as open decisions (§12.6–8) | borrowed from `acos-synthesis-protocol` |

**Full evidence & citations:** `.acos/swarm/swarm-20260625-113200/synthesis/report.md` and `agent-{01..12}/findings.md`.

---

## 17. Implemented improvements — 2026-07-22 (boss feedback)

Two of the five boss-requested improvements were designed and built this pass. The other
three (a `FOLLOW_UP_REQUIRED` claim state, large-data quality at scale, standalone
competency-question tooling) remain **out of scope** and are logged for a later pass.

### 17.1 The boolean confidence checklist (Point 1) — BUILT

Confidence is now decided by an **auditable YES/NO checklist**, not a buried derivation.
`scripts/checklist.py` + `config/checklist.yaml`:

- **Veto + percentage** (decided with the user): 4 **veto** questions (any single NO — or
  unanswered, fail-closed — nullifies the claim outright); the remaining **normal**
  questions are scored to a percentage. This keeps the boss's threshold idea *and* the
  existing hard-nullify safety net, so a fatally-flawed claim can't ride a high score.
- **Graded into the existing tiers** (decided with the user): yes-share ≥ `verified_min`
  (default **0.90**, the boss's example) → `verified`; ≥ `probable_min` (default 0.70) →
  `probable`; below → `unverified`. The single-source cap is preserved via
  `verified_also_requires` (N1 + N2): a claim can hit 90% and still cap at `probable`
  without ≥2 independent sources from ≥2 families.
- **Universal core + optional domain packs** (decided with the user): 10 core normal
  questions apply to every claim; per-topic `domain_packs` add more (the "competency
  questions" idea), extending the denominator.
- **Deterministic vs semantic split:** N1/N2/N3/N5/N9 are computed by code; the vetoes and
  N4/N6/N7/N8/N10 are answered by a **blind judge that is never the claim's author**
  (`prompts/grader.md`), preserving "derived, not self-reported."
- **Integration:** `orchestrate.py` runs the checklist at stage 4.5 when a fact carries
  `checklist_answers`; the falsification gate still owns the `falsification` field +
  disconfirmers. Legacy facts (no judge answers) use the prior grade path unchanged.
- **Proof:** `tests/test_checklist.py` (21 assertions) — veto override, the 9/10 example,
  the single-source cap, domain packs, fail-closed, and end-to-end through the ledger.
  Total offline suite now **75 assertions**, all passing, no model calls.

Resolves **§12.2** (confidence thresholds are now configurable in `checklist.yaml`).

### 17.2 The four-family fan-out (Point 5) — WIRED (code) + human last-mile

Concrete cross-family diversity (SKILL.md "Model strategy"; `prompts/README.md`):

- **Claude** via `Task()`; **Gemini** via `run-external-agent.py --model google:...` (free
  Google AI Studio key); **z.ai/GLM** via a new `zai` provider in `providers.yaml` (the
  user's Coding Plan key via Doppler); **ChatGPT** via the Claude-in-Chrome **browser
  voice** (Plus has no API — documented with its ToS/fragility/scale caveats as an
  optional 4th family).
- The four agent prompts (`elicitor`, `grader`, `refuter`, `synthesizer`) are built and
  family-neutral, so the same prompt runs on every transport.
- **Human last mile (cannot be automated unattended):** create the free Gemini key, export
  the z.ai key, and log into ChatGPT for the browser voice. See SKILL.md "Wake-up
  checklist."

Updates **§12.4** (Claude-only fallback remains, but real cross-family is now the default
path when keys are present).

---
*Plan derived from cross-referenced swarm research. Build it as a refutation engine, not a merger.*
