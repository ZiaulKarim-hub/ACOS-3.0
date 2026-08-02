# /acos-reverse-cleanroom — Architecture (v1 design)

**Date:** 2026-07-22
**Status:** design spec, pre-build. Grounded in `research/deep-research-report.md`,
`.acos/swarm/swarm-20260721-231940/synthesis/report.md`, and `research/COMBINED-riff-brief.md`.
**One-line:** Observe an app from the outside → extract tool-agnostic functional INTENT →
have N blind heterogeneous models rebuild from that intent → fuse one executable rebuild spec
that lands natively into ACOS planning + Genesis, verified against parity oracles captured from
the original.

---

## 0. Recommended calls on the 9 open decisions (defaults; each overridable via config)

| # | Decision | v1 default | Why |
|---|---|---|---|
| D1 | Same-purpose vs same-behavior | **Per-project flag**, default `same-purpose` with a `behavior-critical[]` allowlist (APIs, exports) forced to `same-behavior` | Hyrum's Law: consumer-facing surfaces need bug-for-bug parity; internal logic wants purpose |
| D2 | Model roster / N | **N=5**: `claude-opus` + `claude-sonnet` (Task, subscription) + `glm-4.7` + `gemini-*paid*` + `deepseek-v4` | 5 distinct families; comparable strength; subscription backbone free |
| D3 | Fusion engine | **Reuse `acos-axiom-synthesis`** for the factual/requirement layer; **new backbone+graft synthesizer** for design layer | Facts are refutable (converge); design is choice (judge) |
| D5 | Proprietary-target egress | **ZDR/paid keys only**; self-host open weights when available; **Kimi excluded from proprietary path** | Kimi trains by default; only ZDR survived a court hold |
| D7 | Output format | **Land into ACOS Vision/Epic/Story/Slice + Genesis `component-tree.json`**; no parallel format | Genesis already consumes whole-app trees with verifiers |
| D8 | Human gates | **3 sharp gates** (scope confirm, validation gate, final-spec accept); `--autopilot` collapses to 1 | Few, pre-filtered gates beat review fatigue |
| D9 | Build shape | **Orchestrator skill** that calls existing `acos-design-system-forge` + new capture/intent/fusion agents; NOT a monolith | Two of three legs already exist |
| D4 | Consensus meaning | **Diversity-fusion**; security/edge = UNION; NEVER majority-vote | Correlated errors → "popularity trap" |
| D6 | Third-party targets | **Refuse auth-gated scraping**; `--target-class third-party` requires public/authorized attestation; framed as personal aid | ToS/CFAA/DMCA-1201; AI-cleanroom legality untested |

**v1 first target:** `okoa-loan-intake-system` — its existing 6,762-line behavior blueprint is built-in
ground truth to measure the intent spec against.

---

## 1. Governing principle: the pipeline IS a clean room

Three isolation zones, mechanically enforced (mirrors the ACOS Independence Wall):

```
┌─ DIRTY ROOM ──────────────┐   ┌─ SPEC WALL ─────────┐   ┌─ CLEAN ROOM ──────────────┐
│ sees the ORIGINAL app     │   │ monitor / gate      │   │ sees ONLY the intent spec │
│ capture + intent extract  │──▶│ strip expression,   │──▶│ N blind rebuild proposers │
│ runs ON-MACHINE ONLY      │   │ secrets, PII, tech  │   │ (external + Task)         │
│ raw output never egresses │   │ nouns; hash+log     │   │ never sees the original   │
└───────────────────────────┘   └─────────────────────┘   └───────────────────────────┘
```

- **Enforcement:** a new `PreToolUse` egress guard (`cleanroom-egress-guard.py`) blocks any Bash/WebFetch/
  external-model call whose payload hashes match dirty-room artifacts. Only `02-wall/spec-clean.md`
  (post-monitor) is egress-allowed. Fail-closed on the wall, unlike the Oracle (which is fail-open).
- **Audit:** `audit/wall-manifest.json` records every byte that crossed, its hash, the provider + key tier,
  and an attestation the original never crossed. This is the evidence bundle if independence is ever challenged.

---

## 2. Phase map (6 stages + 3 gates)

```
Phase 0  CAPTURE + BASELINE      (dirty room)     → 00-capture/
Phase 1  EXTRACT INTENT          (dirty room)     → 01-intent/
GATE A   scope confirm  [human/oracle]
Phase 2  WALL + VALIDATE         (spec wall)      → 02-wall/
GATE B   validation gate [human, pre-filtered]
Phase 3  PRIORITIZE (anti-inflation)              → 03-prioritize/
Phase 4  BLIND MULTI-MODEL REBUILD (clean room)   → 04-rebuild/
Phase 5  SYNTHESIZE (backbone-first)              → 05-synthesis/
Phase 6  EMIT + PARITY WIRE (ACOS-native)         → 06-emit/
GATE C   final-spec accept [human] → hand to /acos-execute-* or /acos-synthesis-protocol
```

Session workspace: `.acos/cleanroom/<session-id>/` with the seven sub-dirs above + `audit/`.

---

## 3. Phase-by-phase design

### Phase 0 — Capture + Baseline (the 7-layer truth stack)
Runs entirely on-machine. Produces the raw evidence corpus + the parity oracle.

| Layer | Tool | Output |
|---|---|---|
| Structure discovery | crawler + JS endpoint mining | `structure.json` (route/screen/endpoint census) |
| Behavioral capture | Playwright + Chrome DevTools Protocol + HAR | `har/`, interaction traces, state-flow graph |
| Contract inference | HAR→OpenAPI (two-pass) | `contracts.openapi.json` |
| Source-map extraction | source-map unpack (if present) | `sourcemaps/` (often collapses black-box → source) |
| Vision capture | screenshot + multimodal describe | `screenshots/`, `semantic-ui.json` |
| Auth-role sweep | multi-login (anon/user/admin/paid) | `roles/<role>/…` (the app IS different per role) |
| Server-invisible probe | rate-limit escalation, webhook/email sinks, heartbeat inference | `probes.json` (confidence-flagged inference, NEVER asserted) |

Also captured here (the acceptance oracle):
- `golden/parity-manifest.json` — characterization/golden-master recordings of observed input→output
  behavior, confidence-banded, with `knownDeviation[]`.
- `baselines/budgets.json` — non-functional baselines (Lighthouse, p95 latency, a11y score).
- `capture-manifest.json` — observation **epoch**, `source_ref` (pinned version fingerprint), artifact hashes.

Agents: `rc-capture-orchestrator` (spawns per-layer general-purpose workers). Reuses Claude-in-Chrome MCP
for live sites; falls back to source when a repo is provided.

### Phase 1 — Extract Intent (goal-oriented, evidence-linked, dual-blind)
The maximum-risk stage. Design counters every Agent-02 failure mode.

- **Format:** a WHY-graph — each feature = `{ intent, why_it_exists, actors_who_depend, what_satisfies_it }`
  (KAOS/JTBD-style), plus a UX-intent sub-spec (jobs/journeys/story-map + state matrix as statecharts +
  a11y-as-intent + perceived-performance classes + voice/tone).
- **Evidence-linking:** every intent claim cites a concrete Phase-0 observation. A separate verifier checks
  the *support relation* (does the observation entail the claim?), not just citation existence.
- **Rule ledger:** `rule-ledger.yaml` — numeric constants, formulas, rounding modes, day-counts, cutoff
  timezones captured VERBATIM with input→output examples, **exempt from abstraction**.
- **Confidence:** `intent-claims.jsonl` tags each claim `confirmed | inferred | gap` (Reversa schema);
  confidence is behavioral (agreement across blind extractions), never self-reported.
- **Dual/triple blind:** 3× `rc-intent-extractor` run blind in parallel → `rc-intent-synthesizer`
  (dr2 convergence rules: ≥2/3 keep, grounded-singleton keep-tagged, ungrounded drop, contradiction→OPEN_QUESTION).
  Divergence between extractions is flagged as a spec defect.
- **Completeness:** `surface-census.json` from Phase 0 is the denominator — the spec must map every route/
  screen/endpoint or explicitly mark it `gap`. Incompleteness becomes loud, not silent.
- **Adversarial check:** `rc-intent-qa` grep-audits every categorical claim (brand/entity/purpose) against the
  observation corpus; zero hits → reject. This is the direct fix for the Waldorf/Tapestry failure.

Agents: `rc-intent-extractor` (×3, blind), `rc-intent-synthesizer`, `rc-intent-qa` (adversarial).

### GATE A — Scope confirm (human or Oracle-autofire)
Presents only: `same-purpose vs same-behavior` per surface, the target-class (own/third-party) attestation,
and the model roster. One decision screen. Skippable in `--autopilot` with recorded defaults.

### Phase 2 — Wall + Validate (the monitor)
- `rc-spec-wall` + `cleanroom-egress-guard.py`: strip literal expression, identifiers, secrets, PII, and
  technology nouns (React/Convex/table names) via a contamination lint. Anonymize residual identifiers with
  **format-preserving synthetic substitutes** (not `[REDACT]`, which costs 75–80% quality).
- Emit `spec-clean.md` — the ONLY artifact egress-allowed to external models — plus `contamination-lint.json`
  and `wall-manifest.json` (hashes + attestation).

### GATE B — Validation gate (pre-filtered human review)
Shows ONLY: low-confidence/divergent intent claims, the verbatim rule ledger, and the coverage census
(mapped vs gap). Also solicits **tacit intent** the app can't exhibit ("what does this feature exist to
prevent?"). Designed to avoid review fatigue.

### Phase 3 — Prioritize (the anti-inflation stage)
- `rc-prioritizer`: inverted MoSCoW (`Must/Should/Could/Won't`) + feature-value archaeology. Produces
  `moscow.yaml` + `cut-list.md`. **This is where "100+ functions → ~60" happens by design** — the fix for the
  exact flaw your 2026-04-14 blueprint flagged in itself.

### Phase 4 — Blind Multi-Model Rebuild (the clean room)
- Roster resolved via existing `resolve-agent-model.sh`; Claude seats via `Task()`, external via
  `run-external-agent.py` + `providers.yaml`. Three infra fixes required (Agent 04): GPT-5.x param shim
  (`max_completion_tokens`, drop `temperature`), Kimi route via OpenRouter, raise `max_tokens`.
- **ONE verbatim proposer prompt** to all N (divergence is the product); vary only transport params.
- Blind + anonymized: proposals labeled `P1..P5`, no model sees another's work or identity. **No debate.**
- Dead lane = INCONCLUSIVE; require a **3-of-5 quorum** to proceed.
- Each proposer emits a full rebuild proposal: architecture, data model, API, frontend, ops.

### Phase 5 — Synthesize (backbone-first, not blend)
Two-lane fusion (Agents 07/08 guard catalog G1–G10):

1. **Backbone pick:** `rc-fusion-synthesizer` (a family that authored NONE of the proposals, to kill
   self-preference bias) picks ONE proposal as architectural backbone and states it.
2. **Graft:** mine other proposals only for compatible strengths; each graft justified against the backbone's
   assumption set (Garlan's 4 categories) → anti-frankenspec.
3. **Factual layer:** route requirement-level claims through `acos-axiom-synthesis` (convergence, de-circularization,
   hash-chained ledger, UNRESOLVED honesty).
4. **Bold-idea preservation:** extract each proposal's most distinctive design move; the synthesizer must dispose
   of each explicitly (adopt/reject-with-reason), never by omission.
5. **Security/edge = UNION** (keep everything any model caught); model-independent security baseline applied post-fusion.
6. **Asymmetric veto** on catastrophic axes (security/data-loss/dropped-requirement): any flag blocks.
7. **Conflict round:** ONE judged pass on OPEN_QUESTIONs only (no free debate); re-dispatch blind if section
   convergence <60%.
8. **Emit:** plan-then-write, section-sequential (LongWriter pattern), per-domain ~30K-token shards (beats
   lost-in-the-middle). Iterations are **diff patches at low temperature**, never full re-narration.
9. **Red-team:** `rc-red-team` (different family, blind to fusion rationale) adversarially attacks the fused
   spec; REJECT reopens fusion.

### Phase 6 — Emit + Parity Wire (ACOS-native)
- Render the fused spec into `vision.yaml`, `epics/`, `stories/`, `slices/` (measurable `success_criteria`;
  slices with testable `acceptance_criteria` + `files_allowed` scope walls + `verification_method`) AND a
  Genesis `component-tree.json` (per-component contracts + pluggable verifiers + 100%-coverage gate).
- **Parity wiring:** each acceptance criterion = a behavioral-parity golden test from `parity-manifest.json`,
  set as that slice's `verification_method` + evidence baseline. EARS-style binary criteria.
- **Traceability spine:** `traceability.json` maps every `intent_id` → spec section as a HARD GATE (every intent
  mapped or explicitly waived-with-reason). Mechanical count check blocks completion.
- **Drift control:** pin `source_ref`; a `--recheck` mode re-captures a sample of anchor behaviors and diffs
  against the epoch, flagging staleness.

### GATE C — Final-spec accept
Hands off to `/acos-synthesis-protocol` (Genesis leaves-first build) or `/acos-execute-epic`. Recommends
strangler-fig incremental adoption, never big-bang.

---

## 4. New components to build

**Skill:** `.claude/skills/acos-reverse-cleanroom/SKILL.md` (orchestrator; phase logic like acos-dataroom-v2).

**Agents (`.claude/agents/`):**
- `rc-capture-orchestrator` (spawns per-layer workers; Chrome MCP + Bash)
- `rc-intent-extractor` (blind, ×3)
- `rc-intent-synthesizer`
- `rc-intent-qa` (adversarial, grep-audit)
- `rc-spec-wall` (contamination lint + anonymize)
- `rc-prioritizer`
- `rc-fusion-synthesizer` (backbone+graft, cross-family)
- `rc-red-team` (adversarial, blind to rationale)
- (proposers are NOT new agent files — Claude via Task(), external via run-external-agent.py)

**Scripts (`.claude/scripts/`):**
- `cleanroom-egress-guard.py` (PreToolUse; fail-closed wall enforcement)
- `cleanroom-capture/*` (Playwright/HAR/source-map/Lighthouse drivers) — TypeScript per your language rule
- `cleanroom-parity.ts` (golden-master capture + replay)

**Config:** `.acos/config/cleanroom.yaml` (roster, N, target-class allowlist, egress policy, gate mode, budgets).

**Reused as-is:** `acos-design-system-forge` (visual tokens lane), `acos-axiom-synthesis` (factual fusion),
`resolve-agent-model.sh` + `run-external-agent.py` + `providers.yaml` (fan-out), Genesis + synthesis-protocol
(downstream), the Oracle + Independence Wall patterns, dr2 convergence rules (as agent templates).

---

## 5. Data-flow one-liner

`original app` → **[dirty room]** capture 7 layers + parity oracle → dual-blind intent WHY-graph + rule ledger
→ **[GATE A]** → **[spec wall]** strip+anonymize+hash → **[GATE B]** → prioritize (cut inflation) →
**[clean room]** N=5 blind proposals → backbone+graft fusion + union-security + red-team →
ACOS Vision/Epic/Story/Slice + Genesis tree, parity-wired, traceability-gated → **[GATE C]** → build.

---

## 6. What makes this the "best" version (traceable to research)

1. Intent-first, not behavior-first — fixes your blueprint's own architecture-inflation flaw (Phase 3).
2. Capture treats hidden/server logic as first-class, probed and confidence-flagged (Phase 0).
3. Confabulation defeated by evidence-relation checks + grep-audit + dual-blind + rule ledger (Phase 1).
4. Legal cleanroom enforced mechanically with an egress guard + audit trail (governing principle).
5. Ensemble is quality-first, blind, no-debate, union-security, backbone-fused — not naive voting (Phases 4–5).
6. Output is not orphaned — it lands into your existing build machinery with parity oracles (Phase 6).
7. Cost-aware: subscription backbone + N=5 sweet spot (~$0.40–$1.71/run marginal).

---

## 7. Known limits / honesty (carry into the SKILL.md)
- No benchmark exists for whole-app intent-extraction or multi-spec fusion — v1 defines a new eval axis.
- Same-family Claude diversity is unmeasured — flag reduced independence in the audit.
- Legal status of AI-authored cleanroom specs is untested — frame as a personal aid, not a clone-shipping product.
- Big rewrites fail; the skill outputs a spec for INCREMENTAL adoption, and says so.
