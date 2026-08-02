---
name: acos-reverse-cleanroom
description: Reverse-engineer any website/app into tool-agnostic functional INTENT, have N blind heterogeneous AI models independently propose rebuilds from that intent alone, and synthesize one executable rebuild spec that lands natively into ACOS planning + Genesis, verified against behavioral-parity oracles captured from the original. Enforces a mechanical clean-room wall (dirty room → spec wall → clean room) with a fail-closed egress guard and a full audit trail. Use to rebuild an app you own on a new stack, shed inherited architecture inflation, or produce a vendor-neutral rebuild specification.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch, Task
---

# Reverse Cleanroom

## Purpose

Turn an existing app into the BEST possible rebuild specification — not a clone.
The skill strips the app to *why each feature exists* (intent), not *how it was
built* (implementation), then lets several different AI models rebuild it blind,
and fuses their proposals into one spec that sheds accidental complexity and lands
straight into the ACOS build machinery with parity tests wired in.

Design rationale and evidence: `planning/acos-reverse-cleanroom/ARCHITECTURE.md`,
`.../research/deep-research-report.md`, `.acos/swarm/swarm-20260721-231940/synthesis/report.md`.

## When to use

- Rebuild an app you OWN on a new stack (e.g. Convex → Cloudflare) without porting bloat.
- Produce a vendor-neutral, intent-level rebuild spec for a team.
- A third-party target ONLY if public/authorized (never auth-gated scraping).

**Not** a "clone this competitor and ship it" tool. The legality of AI-authored
clean-room specs is untested — this is a personal orchestration aid. Output is a
spec for INCREMENTAL (strangler-fig) adoption, never a big-bang cutover.

## Invocation

```
/acos-reverse-cleanroom --base <url> [--repo <path>] [--roles anon,user,admin]
                        [--seed /,/dashboard,...] [--target-class own|third-party]
                        [--fidelity same-purpose|same-behavior] [--n 5] [--autopilot]
```
Wizard prompts for anything omitted. Config defaults live in `.acos/config/cleanroom.yaml`.

## Governing principle — the pipeline IS a clean room

Three isolation zones (`references/egress-and-cleanroom.md`):
- **Dirty room** (`00-capture/`, `01-intent/`) sees the original; on-machine only.
- **Spec wall** (`02-wall/`) strips expression/secrets/PII/tech-nouns; hashes what crosses.
- **Clean room** (`04-rebuild/`+) — external models see ONLY `02-wall/spec-clean.md`.

A fail-closed PreToolUse egress guard (`.claude/skills/acos-reverse-cleanroom/scripts/egress-guard.ts`)
blocks any external send that leaks dirty-room content. Arm it at init, disarm at close.

---

## Phase −1 — Init

1. Read `.acos/config/cleanroom.yaml`; apply CLI overrides. If `--target-class third-party`,
   REQUIRE an explicit public/authorized attestation and REFUSE auth-gated capture.
2. Generate `session-id = cleanroom-<YYYYMMDD>-<HHMMSS>`. Create
   `.acos/cleanroom/<session-id>/{00-capture,01-intent,02-wall,03-prioritize,04-rebuild,05-synthesis,06-emit,audit}`.
3. Write the `ACTIVE` marker. Snapshot config to `audit/config-snapshot.yaml`.
4. Arm the egress guard: add the PreToolUse hook to `.claude/settings.local.json`
   (see `references/egress-and-cleanroom.md`). Verify with a probe call.
5. For a proprietary target, verify the model roster's data posture (drop Kimi; force
   paid Gemini key; prefer self-hosted GLM/DeepSeek). Record posture in `audit/`.

## Phase 0 — Capture + Baseline (dirty room)

Capture runs an **ADAPTIVE layer set** — not a fixed count. The orchestrator selects the
subset of the **27-layer library** (`references/capture-layers.md`) predicted to reach the
`coverage_benchmark` (default `0.99`) of THIS app's features + intent, always includes the
server-invisible probe, and runs two convergence loops (below). Layer count varies per app
(illustratively 7–27, no hardcoded number). Contract inference is **capture-layer 3** — the
former standalone "Infer API contracts" step is merged there (one contract-inference pass, not two).

1. **Adaptive capture.** Spawn **`rc-capture-orchestrator`** (Task). It (a) runs a cheap recon
   pass (structure discovery + a light behavioral pass) to detect the app's shape; (b) SELECTS
   the layers needed to hit `coverage_benchmark` for this app (selection protocol in
   `references/capture-layers.md`); (c) drives the selected layers per auth role via
   `.claude/skills/acos-reverse-cleanroom/scripts/capture.ts` (Playwright — install once:
   `cd .claude/skills/acos-reverse-cleanroom/scripts && bun add playwright && bunx playwright install chromium`).
   Layer 3 emits `contracts.openapi.json`. **Robustness:** merge HAR across sessions/roles/runs
   before inference; cross-check any published API doc / source-maps when present.
   **Inner (top-up) loop:** after the selected layers run, measure coverage against the
   `surface-census.json` denominator; if gaps remain, add the next-best layers and re-measure —
   repeat until the benchmark is met or the library is exhausted.
2. **Acceptance oracle + baselines.** Record golden cases via `parity.ts record`; NFR baselines
   (Lighthouse/latency/a11y) into `baselines/budgets.json`. **Robustness:** capture multiple
   samples per golden case and tag stable-vs-volatile fields; run baselines a few times and keep
   the spread, not a single number.
3. **Server-invisible probe (ALWAYS ON).** Probe rate limits/webhooks/emails → `probes.json`,
   all `inferred`. Runs on EVERY app regardless of the adaptive selection. **Robustness:** point
   emails/webhooks at disposable catch-all sinks; require two independent signals before marking
   a probe "likely."
4. **Capture manifest.** Emit `capture-manifest.json` with the observation epoch + pinned
   `source_ref`. **Robustness:** content-hash the captured surfaces + a build/version stamp; on a
   re-run, auto-diff the new manifest vs the old (feeds the outer loop).
5. **Dirty fingerprint.** `bun fingerprint-build.ts .acos/cleanroom/<sid>`. **Robustness:** add a
   secret/PII pattern scan as a second gate; fingerprint at multiple granularities (file + chunk +
   phrase) to catch partial leaks.

**Outer (re-run) loop.** After a full pass, re-run the whole capture until a fresh pass adds nothing
MATERIAL, capped by `capture.max_reruns` (default `2` → 3 passes max). Compare on NORMALIZED
features/intent (against the census + intent ledger), never raw bytes; VARY conditions each pass
(data/timing/inputs) so a re-run probes new ground, not just re-confirms. "No new material findings"
is the convergence proxy for the benchmark — evidence, not proof; unreachable states stay `UNKNOWN`.

## Phase 1 — Extract Intent (dirty room)

1. Spawn **9× `rc-intent-extractor`** BLIND in parallel (Task) — a **3 POV × 3 instance**
   matrix: 3 point-of-view groups (`pov-user`, `pov-operator`, `pov-risk`) × 3 blind
   instances each. Pass each spawn its `<pov>` + instance letter in the task prompt; it
   writes to `01-intent/<pov>/extract-<A|B|C>/`. ALL nine are Claude via `Task()` — on-machine,
   wall-safe (Phase 1 is dirty-room; external/cloud models are FORBIDDEN here — they would
   egress raw capture; heterogeneous families run only post-wall at Phase 4). Each emits an
   intent WHY-graph + `intent-claims.jsonl` (`templates/intent-claims.schema.json`, each claim
   `pov`-tagged) + a `rule-ledger.yaml` (`templates/rule-ledger.example.yaml`) + a UX-intent
   sub-spec, extracted THROUGH its assigned lens. `--n-pov`/`--pov-group-size` (default 3×3=9)
   scale it; a group size of 1 collapses to one blind reader per lens (3 total).
2. Spawn **`rc-intent-synthesizer`** (Task): merge the nine blind extractions in TWO LEVELS —
   **(L1) within each POV group** by ≥2/3 convergence (within-group divergence = defect), then
   **(L2) across the three lenses** by UNION (different lenses seeing different things = coverage,
   NOT a defect; a claim confirmed in ≥2 lenses is strongest; only a genuine cross-lens
   CONTRADICTION on the same surface is a spec defect → OPEN_QUESTION, conservative reading).
   Emit `intent-spec.md` (claims `pov`-tagged), merged `intent-claims.jsonl`, `rule-ledger.yaml`,
   `surface-census.json` (completeness denominator).
3. Spawn **`rc-intent-qa`** (Task, adversarial): verify the support RELATION of every claim
   (does the cited observation entail it?) AND actively try to FALSIFY it (search for contradicting
   evidence, not just confirm the citation); grep-audit every categorical claim (brand/entity/purpose)
   against the corpus — zero hits → reject. Set `evidence[].entails`. Loop back to extraction for
   rejected/divergent claims (cap 3 rounds); on cap-exhaustion mark leftover claims `unresolved` and
   route to Gate B — NEVER silently keep a failed claim as `confirmed`.
4. Re-run `fingerprint-build.ts` so intent artifacts join the dirty fingerprint; ASSERT it covers every
   new intent file (fail loud on a miss), and run a pre-wall contamination lint scanning the intent spec
   for technology/vendor nouns (cheap early catch; the wall re-checks at Phase 2).

### GATE A — Scope confirm
Present ONLY: per-surface `same-purpose vs same-behavior`, target-class attestation, model roster.
`--autopilot` uses config defaults and records them. (Uses AskUserQuestion.)

## Phase 2 — Wall + Validate (spec wall)

1. Spawn **`rc-spec-wall`** (Task): from `intent-spec.md` produce `02-wall/spec-clean.md` —
   run MECHANICAL detectors first (secret/entropy/PII regex + tech-vendor noun list), then the
   semantic strip of literal expression, identifiers, secrets, PII, and technology nouns; anonymize
   residual identifiers with CONSISTENT format-preserving synthetic substitutes (NOT `[REDACT]`),
   fail-closed on any doubt. Emit `contamination-lint.json` and `forbidden-tokens.txt` (derived from the
   detectors + raw corpus, not only the first pass). Then an INDEPENDENT second-wall re-scan of
   `spec-clean.md` — HOLD if any residue survives.
2. Re-run `fingerprint-build.ts` → clean-spec hash into `allow_hashes`, forbidden tokens armed. **Test the
   alarm:** send a known dirty token through the egress path and confirm it is DENIED before proceeding.
3. Write `audit/wall-manifest.json` (hashes + attestation the original never crossed), enriched with the
   detector + second-wall + armed-probe results and `audit/egress-log.jsonl`, and HASH-CHAINED (tamper-evident).

### GATE B — Validation gate (pre-filtered)
Present ONLY: low-confidence/divergent claims, the verbatim rule ledger, and the coverage
census (mapped vs gap). Solicit TACIT intent ("what does this feature exist to prevent?").
Fold answers back into `intent-claims.jsonl` as `human-tacit` evidence, re-wall, re-fingerprint.

## Phase 3 — Prioritize (anti-inflation, false-cut-proof)

1. Spawn **`rc-prioritizer`** (Task): inverted MoSCoW + feature-value archaeology over the intent +
   usage signals. Emit `moscow.yaml` + a PROPOSED cut-list. Cuts are NON-DESTRUCTIVE (quarantine, not
   delete — the intent stays in the ledger, reversible); a cut needs a positive bloat reason
   (absence-of-use only FLAGS, never auto-cuts).
2. **Protected-set hard gate:** mechanically BLOCK + HALT if any proposed cut is `rule-ledger`-linked,
   `behavior-critical` (public API/export/integration), or Gate-B human-essential (`protected-gate.json`).
3. Spawn **`rc-cut-defender`** (Task, BLIND to the prioritizer's rationale): defends each proposed cut;
   a single plausible essential-use story VETOES it (returns to KEEP). Only defender-UPHELD cuts survive
   to the final `cut-list.md`, each carrying an explicit waiver-with-reason.
4. The final cut-list is surfaced at **Gate B** for human sign-off; every cut is an explicit waiver feeding
   the Phase-6 traceability hard gate (nothing disappears silently). Cuts stay re-includable downstream by
   a proposer or `rc-red-team`.
5. `Won't`-list items are removed from the spec-clean copy sent to proposers; re-wall + re-fingerprint after
   the cut. This is where inherited bloat ("100+ functions → ~60") is trimmed ON PURPOSE.

## Phase 3.5 — PRD synthesis (post-wall, convergent)

Turn the prioritized intent into ONE complete, buildable **Product Requirements Document (PRD)** before any
rebuild. This is CONVERGENT (unlike Phase 4): drafts must AGREE on WHAT to build; divergence is a defect signal.
It runs POST-WALL, so heterogeneous model families are allowed — each sees ONLY `02-wall/spec-clean.md` +
parity-case IDs (never raw captured values), so nothing dirty egresses.

1. Dispatch **N× `rc-prd-drafter`** BLIND (default 3; heterogeneous families allowed post-wall — Claude via
   `Task()`, external via `run-external-agent.py --agent rc-prd-drafter` on `02-wall/spec-clean.md`). Each drafts
   the full 9-section PRD — functionality + product/UX design + intent + data model + rules (verbatim) +
   observable constraints + acceptance criteria + an OPEN architecture section + known-unknowns — tool-agnostic
   (WHAT, not HOW; internal architecture stays OPEN for Phase 4).
2. Spawn **`rc-prd-synthesizer`** (Task): merge the drafts by convergence (contradiction → OPEN_QUESTION,
   conservative reading), then run the **COMPLETENESS GATE** — every kept `intent_id`, surface (from the census),
   rule-ledger entry, and parity case MUST map to a requirement or be explicitly waived, else `verdict: FAIL` and
   loop back to draft (cap 3 rounds). Emit `035-prd/prd.md` + `requirements.jsonl` + `completeness-report.json`.
3. The PASSING PRD (`prd.md`) is Phase 4's input — proposers design from the PRD, not raw intent. Architecture
   stays OPEN, so the blind rebuild keeps real design freedom.

## Phase 4 — Blind multi-model rebuild (clean room)

1. Resolve the roster via `resolve-agent-model.sh` for each seat in `cleanroom.yaml`.
2. Dispatch N proposers — all running the SAME agent `rc-rebuild-proposer` (its system prompt
   IS the verbatim proposer instructions; `templates/proposer-prompt.md` is the reference copy).
   The input is the PASSING PRD `035-prd/prd.md` (post-wall, egress-cleared — architecture is OPEN, so
   proposals still diverge on HOW). Each proposal MUST include a **requirements-trace**: every `REQ-####`
   in the PRD → how this design satisfies it; a proposal that silently drops a requirement is REJECTED.
   It must also declare its **key risks + assumptions** so fusion can weigh them.
   - Claude seats → `Task(rc-rebuild-proposer)` with the PRD in the task prompt (subscription-safe).
   - External seats → `Bash`:
     `python3 .claude/scripts/run-external-agent.py --agent rc-rebuild-proposer --model <spec> --task "Design the rebuild from the PRD in context; include a requirements-trace + key-risks." --context .acos/cleanroom/<sid>/035-prd/prd.md --max-tokens 32000`
     (proposals need ~20–30k output; the runner auto-applies the reasoning-model param shim —
     o1/o3/o4/gpt-5.x → `max_completion_tokens`, no `temperature`). Kimi routes via `moonshot:kimi-k2`
     or `openrouter:moonshotai/kimi-k2` and is DROPPED for proprietary (`target.class: own`) targets.
   Each external send passes the egress guard — a payload leaking dirty-room content is DENIED.
3. Collect proposals as `04-rebuild/P1.md … PN.md` (ANONYMIZED — strip model identity; external
   stdout is captured straight to the file), each with its requirements-trace + key-risks. A proposal
   missing a requirement or its trace is rejected. Dead lane = INCONCLUSIVE. Require the `quorum`
   (default 3-of-5) to proceed.

## Phase 5 — Synthesize (backbone-first)

Spawn **`rc-fusion-synthesizer`** (Task; a family that authored NO proposal). Apply
`references/fusion-rules.md`: backbone pick → graft → bold-idea disposition → two-lane
per-section fusion (facts via convergence / `acos-axiom-synthesis` de-circularize→corroborate→falsify;
design via judged trade-offs) → security/edge UNION → asymmetric veto on catastrophic axes → ONE conflict
round on OPEN_QUESTIONs → plan-then-write section-sequential emission (diff-patch iterations).
Then apply two hard checks before release:
- **Completeness gate:** every PRD `REQ-####` maps to a component/section of the fused plan, or is an
  explicit waiver-with-reason — else FAIL back to fusion. (Same guarantee as the PRD gate, now on the design.)
- **Buildability dry-run:** confirm the fused plan can decompose leaves-first into an acyclic component tree
  (no circular dependency, every leaf independently testable) — a plan that can't be built bottom-up FAILS.
Then spawn **`rc-red-team`** (Task; different family, blind to fusion rationale): adversarial attack, backed by
`acos-axiom-synthesis` `falsify.py` + oscillation guard so a REJECT is an auditable, non-oscillating verdict
(not prose). REJECT reopens fusion. Emit `05-synthesis/fused-spec/` + `traceability.json` + `red-team.md`.

## Phase 6 — Compile → Build (genesis + synthesis, parity-verified)

The build backend is **`acos-genesis-protocol` → `acos-synthesis-protocol`** (the matched pair): genesis
plans a tree of independently-testable components; synthesis builds it bottom-up, proving each part. This is
where the rebuild is CONSTRUCTED + VERIFIED, not just specced.

1. **Compile to a genesis component-tree.** Render the fused spec + PRD into a genesis tree via
   `acos-genesis-protocol` (config `emit.genesis_component_tree: true`): `component-tree.json` +
   `integration-map.json` + `build-plan.json`, each component carrying a contract + a **pluggable verifier**.
   Also emit the ACOS `planning/<project>/vision.yaml` + `epics/`/`stories/`/`slices/` mirror for status tooling.
2. **Parity-as-verifier wire (the key win).** Bind each component's acceptance criterion to its PRD `REQ-####`
   AND its Phase-0 golden parity case (`parity-manifest.json`) as the component's `verifier.auto_check`. So each
   rebuilt part is proven against the ORIGINAL's observed behavior. EARS-style binary criteria.
3. **Build for real** with `acos-synthesis-protocol <feature-dir>`: leaves-first Builder → fresh zero-trust
   Verifier (+ code-leaf hardening gate) → compose via Integrator → on integration fail, the up→down→up repair
   loop — until the root Product passes its whole-product verifier against the PRD/vision. Bounded repair; the
   Component Library shows live pass/fail.
4. **OPTIONAL depth (off by default):** for complex/regulatory/audit-heavy targets, enrich the plan with
   `acos-preeng-classic` DEPTH artifacts only (evidence ledger, ≥95% coverage gate, decision trace, per-task
   Dev/QA instructions). Do NOT use its PRD front (we have one). Every preeng `Assumption` is Gate-B-gated,
   never baked in (it conflicts with clean-room grounding). Controlled by `build.preeng_depth_addon` (default false).
5. **Hard gates:** the **traceability** gate (`traceability.json` maps every `intent_id`/`REQ-####` → a component
   or explicit waiver) AND the **completeness** gate BLOCK completion. **Drift control:** pin `source_ref`;
   document `--recheck` (re-capture anchors, diff vs epoch).

### GATE C — Final-spec accept
Present the fused spec summary, the traceability coverage, the red-team verdict, and the
parity-wiring count. On accept, hand off to `/acos-synthesis-protocol` (Genesis leaves-first
build) or `/acos-execute-epic`. Recommend strangler-fig incremental adoption.

## Phase 7 — Close
Remove `ACTIVE`; de-register the egress hook; finalize `audit/wall-manifest.json` and
`audit/egress-log.jsonl`; write a session summary to `06-emit/README.md`.

---

## Agent roster (all in `.claude/agents/`)
`rc-capture-orchestrator` · `rc-intent-extractor` (×9 blind = 3 POV × 3) · `rc-intent-synthesizer` ·
`rc-intent-qa` · `rc-spec-wall` · `rc-prioritizer` · `rc-cut-defender` (blind anti-false-cut) ·
`rc-prd-drafter` (×N blind, convergent) · `rc-prd-synthesizer` (+ completeness gate) ·
`rc-rebuild-proposer` (×N blind) · `rc-fusion-synthesizer` · `rc-red-team`. The proposer is a single agent run on every seat —
Claude via `Task(rc-rebuild-proposer)`, external via `run-external-agent.py --agent rc-rebuild-proposer`.

## Reused ACOS components
`acos-design-system-forge` (visual-token lane, called in Phase 0 for the design layer),
`acos-axiom-synthesis` (factual-layer fusion + `falsify.py`/oscillation guard for red-team),
`resolve-agent-model.sh` + `run-external-agent.py` + `providers.yaml` (fan-out),
**`acos-genesis-protocol` → `acos-synthesis-protocol`** (the DEFAULT build backend — component-tree
plan → leaves-first parity-verified build), `acos-preeng-classic` (OPTIONAL depth add-on, off by
default, depth-artifacts-only with assumptions Gate-B-gated), the Oracle + Independence-Wall patterns,
dr2 convergence rules.

## Quality checklist
- [ ] Egress guard armed BEFORE any capture; disarmed at close.
- [ ] Every intent claim evidence-linked AND entailment-verified; categorical claims grep-audited.
- [ ] Rule ledger captured verbatim with observed input→output examples.
- [ ] Completeness measured against the external surface census (gaps marked, not hidden).
- [ ] Proposers blind + anonymized; one verbatim prompt; no debate; quorum met.
- [ ] Fusion backbone-first; security/edge UNION not vote; bold-ideas disposed on record.
- [ ] Traceability hard gate passes; parity tests wired into slice verification.
- [ ] Proprietary target: ZDR/paid/self-hosted only; Kimi excluded; posture in audit.
- [ ] Honest limits carried into output (unmeasured eval axis; untested legality; incremental adoption).

---
*Reverse Cleanroom — observe the app, keep the WHY, rebuild it many ways blind, fuse the best, prove parity.*
