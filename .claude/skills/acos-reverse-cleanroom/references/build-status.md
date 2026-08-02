# Build status — /acos-reverse-cleanroom

Authored + self-verified 2026-07-22. This records what is DONE, what is TESTED, and the
user-side prerequisites that only you can supply before a live run.

## Design update 2026-07-23 — adaptive capture + POV intent matrix
DONE (spec/design level — SKILL.md, agents, config, reference, schema, docx):
- **Adaptive Phase-0 capture:** 27-layer library + selection protocol to `coverage_benchmark`
  (default 0.99); layer count varies per app (not fixed). Server-invisible probe ALWAYS runs.
- **Two capture loops:** inner top-up (add layers until benchmark vs the census denominator) +
  outer re-run (re-run whole capture until a fresh pass adds nothing material; `max_reruns` default 2;
  normalized-features compare; vary conditions each pass).
- **0.2 merged into capture-layer 3** (one contract-inference pass, not two). Phase-0 steps
  renumbered 0.1–0.5 (+ outer loop).
- **Robustness bundle** documented for 0.1–0.5 (multi-session HAR merge, published-doc cross-check,
  oracle multi-sample, baseline spread, disposable sinks + two-signal probes, manifest version-stamp +
  auto drift-compare, secret/PII scan + multi-granularity fingerprint).
- **Phase-1 POV matrix:** 9 blind extractors = 3 POV lenses (`pov-user`/`pov-operator`/`pov-risk`) × 3,
  ALL Claude on-machine (external models forbidden pre-wall). Two-level synthesis: L1 within-lens ≥2/3;
  L2 cross-lens UNION (contradiction = defect). `pov` field added to intent-claims schema.
- Config: `.acos/config/cleanroom.yaml` gained `capture:` + `intent:` + `wall:` + `prioritize:` blocks (all parse under strict YAML).
- **Phase-1 QA/synth bundle (1.2–1.4):** synthesizer deterministic claim-key matching + `provenance` (which of ≤9 reads); QA falsification pass + `unresolved`-on-cap (never silent-keep); re-fingerprint assert-coverage + pre-wall tech-noun lint. Schema gained `unresolved` status + `provenance`.
- **Phase-2 wall bundle (2.1–2.3):** mechanical detectors under the LLM + fail-closed-on-doubt + consistent pseudonymization map + independent second-wall re-scan; forbidden-tokens from detectors+corpus + armed-guard probe; wall-manifest enriched with detector/second-wall/probe results + egress-log, hash-chained.
- **Phase-3 false-cut guards (7) + new agent `rc-cut-defender`:** non-destructive quarantine cuts; machine protected-set HARD GATE (block+halt on rule-ledger/behavior-critical/human-essential); positive-evidence-to-cut; strong BLIND adversarial defender (single-story veto); Gate-B sign-off; traceability waiver; re-includable downstream.
- **NEW Phase 3.5 — PRD synthesis (2 new agents `rc-prd-drafter`, `rc-prd-synthesizer`):** N blind convergent PRD drafters (post-wall → heterogeneous families OK, see spec-clean + parity IDs only) → synthesizer merge + HARD completeness gate (every kept intent/surface/rule/parity item → a `REQ-####` or explicit waiver, else FAIL/loop, cap 3). PRD is 9-section, WHAT-not-HOW (architecture stays OPEN for Phase 4). PRD (`035-prd/prd.md`) added to egress allow-list. Config `prd:` block.
- **Phase-4/5/6 robustness + build backend:** Phase 4 proposers now design from the PRD with a mandatory requirements-trace + declared key-risks (drop a REQ → rejected). Phase 5 adds a completeness gate + leaves-first buildability dry-run; red-team blockers now falsification-backed (`falsify.py` + oscillation guard). Phase 6 REWIRED: the DEFAULT build backend is `acos-genesis-protocol` → `acos-synthesis-protocol` (component-tree plan → leaves-first parity-verified build with up→down→up repair); Phase-0 parity cases bind as each component's verifier; `acos-preeng-classic` is an OPTIONAL depth add-on (off by default, assumptions Gate-B-gated). Config `build:` block. Roster now **12** rc-* agents.
- **Correction logged:** an earlier design note wrongly paired `acos-preeng-classic` output → `acos-synthesis-protocol`. synthesis consumes a GENESIS tree, not preeng output; preeng bridges to the slice lifecycle. Fixed: genesis+synthesis is the matched build pair; preeng is depth-only + optional.

## Code update 2026-07-23 — adaptive-capture + gates + robustness IMPLEMENTED & TESTED
The TypeScript that was PENDING above is now WRITTEN and mechanically verified (`bun selftest.ts`
→ **67/67 pass**, the original 12 among them; no live target, keys, or Playwright needed). Design
principle: pure decision-logic was split into `lib/*.ts` so ~90% is unit-tested now; only the
browser-driving shell stays live-only.

**Relocated 2026-07-24:** the scripts moved from `.claude/scripts/cleanroom/` → `.claude/skills/acos-reverse-cleanroom/scripts/`
to match the repo's dominant convention (single-use skill code co-located inside the skill; 13 other skills do this).
All 5 live references updated (SKILL.md, rc-capture-orchestrator.md, this file, egress-and-cleanroom.md, capture.ts comments);
imports are relative so nothing broke; `bun selftest.ts` → 67/67 at the new path; no other skill/agent/settings affected.
Historical `memory/handoffs/*` notes still cite the old path — left as-is (frozen records, not live links).

NEW modules (all pure, fully tested):
- `lib/layers.ts` — the 27-layer library as data + the adaptive **selection protocol** (seed core →
  core-role when >1 role → fire conditionals on detected signals → ext top-up to `coverage_benchmark`).
  `selectLayers()` / `coverageOf()` / `applicableLayers()` / `remainingExtByValue()`. Layer count varies
  per app (demoed: 7-signal/3-role app → 21/21 applicable; minimal app → far fewer).
- `lib/loops.ts` — `materialDelta()` (NORMALIZED feature-key diff, never raw bytes) + `outerConverge()`
  (re-run driver, caps at `max_reruns`, converges when a fresh pass adds nothing material).
- `lib/gates.ts` — `completenessGate` (Phase 3.5 + 5), `protectedSetGate` (Phase 3 BLOCK+HALT),
  `buildabilityGate` (Phase 5, Kahn topo-sort leaves-first + untestable-leaf catch), `traceabilityGate`
  (Phase 6). All return structured verdicts, never throw on a normal fail.
- `lib/scan.ts` — secret/PII pattern + entropy scanner (a SECOND gate under the wall) + multi-granularity
  fingerprint (file + chunk + phrase).
- `lib/stats.ts` — `spread()` / `percentile()` / `volatileFields()` for oracle-multisample + baseline-spread.

NEW CLIs (spawn-tested): `select-layers.ts` (signals → adaptive layer set), `gate.ts`
(completeness|protected-set|buildability|traceability, exit 0/1 for the orchestrator to branch on),
`capture-diff.ts` (outer-loop convergence, exit 0=converged / 3=material), `parity-bind.ts` (Phase-6
parity-as-verifier wiring — binds Phase-0 golden cases into a genesis component tree, deterministic transform).

MODIFIED (additive, back-compat — original behavior + tests preserved):
- `capture.ts` — `--recon` mode (heuristic anon crawl → `recon/signals.json` + `surface-census.json`)
  and `--layers <ids>` gating (client-storage / console / security-header layers gate on the selection).
- `fingerprint-build.ts` — `--secret-scan` (folds scanned secret/PII tokens into `forbidden_tokens`,
  writes `audit/secret-pii-scan.json`) and `--multigranularity` (adds `chunk_shingles`).
- `egress-guard.ts` — additive chunk-overlap check against raw string FIELD VALUES (paragraph-preserving,
  not the JSON blob — the design seam the test caught); no-op when the fingerprint carries no `chunk_shingles`.
- `parity.ts` — `--samples N` oracle multisample + `volatile_fields` tagging (N=1 keeps the old shape).
- `package.json` — script aliases for recon / select-layers / gate / capture-diff / parity-bind / selftest.

STILL live-only (cannot be end-to-end tested without the prerequisites — this is inherent, not skipped):
- `capture.ts` `--recon` signal-detection quality + the `--layers` browser capture paths (need a live app;
  detection heuristics are calibration on first runs, by design).
- Robustness pieces that need real I/O: disposable email/webhook sinks, multi-session HAR merge,
  published-doc/source-map cross-check, actual Lighthouse/a11y baselines (the `spread()` math is tested; the
  measurement tooling is live).
- The genesis→synthesis BUILD itself is an agent-driven skill invocation (`acos-genesis-protocol` →
  `acos-synthesis-protocol`); `parity-bind.ts` supplies the deterministic verifier-binding transform, but the
  actual tree-build + up→down→up repair runs through those skills at Phase 6, not a standalone script.
- The outer-loop *orchestration* (re-run capture N times, vary conditions) is driven by
  `rc-capture-orchestrator` calling `capture.ts` + `capture-diff.ts`; the convergence LOGIC is tested,
  the live re-run wiring is exercised only during a real Phase 0.

## Complete (authored)
- Orchestrator `SKILL.md` (6 phases + 3 gates) + 3 references + 4 templates.
- 9 agents: rc-capture-orchestrator, rc-intent-extractor, rc-intent-synthesizer, rc-intent-qa,
  rc-spec-wall, rc-prioritizer, rc-rebuild-proposer, rc-fusion-synthesizer, rc-red-team.
- 6 TypeScript scripts (run via `bun`): egress-guard, fingerprint-build, capture,
  har-to-openapi, parity, selftest + lib/fingerprint.
- Config `.acos/config/cleanroom.yaml`.

## Verified (mechanical, no live target needed)
- `bun selftest.ts` → **67/67** assertions pass (was 12/12; extended 2026-07-23). Covers: fingerprint
  functions, egress-guard's decision paths incl. the new chunk-overlap path, HAR→OpenAPI inference
  (numeric-id generalization + request-schema inference), the adaptive layer-selection protocol
  (core/core-role/conditional/ext + top-up + unreachable-benchmark termination), both convergence loops,
  all four mechanical gates, secret/PII scan + entropy + multi-granularity, stats/spread/volatile-fields,
  and the select-layers / gate / capture-diff / parity-bind / fingerprint-build CLIs (spawned).
- Egress guard: fail-closed on forbidden-token leak and >3 shared 8-word shingles; no-op with
  exit 0 outside an active session.
- run-external-agent.py reasoning-model param shim: o1/o3/o4/gpt-5.x → `max_completion_tokens`
  (no `temperature`); classic models keep `max_tokens` + `temperature`.
- providers.yaml parses under both the runner's parser AND strict YAML; moonshot provider +
  openrouter models (deepseek/deepseek-chat, moonshotai/kimi-k2, z-ai/glm-4.7) present.
- cleanroom.yaml parses under strict YAML; all 5 seats resolve to registered providers
  (fixed: `gemini:` → `google:`; deepseek-v4 → deepseek/deepseek-chat).
- Full cross-reference audit: every agent/script/template/reference the skill names exists;
  every agent frontmatter `name` matches its filename.

## Fixes applied this session (were flagged as prerequisites, now DONE)
- GPT-5.x / reasoning-model param shim in run-external-agent.py.
- Kimi routing: moonshot provider added + openrouter kimi-k2 model added; excluded from proprietary path.
- Gemini seat provider-name bug (`gemini` → `google`).
- Proposer dispatch gap: run-external-agent.py requires `--agent`, so proposers are now the real
  agent `rc-rebuild-proposer` (used by both Task() and the external runner); `--max-tokens 32000`.

## User-side prerequisites for a LIVE run (only you can provide these)
1. **Playwright** (browser automation for Phase-0 capture), one-time:
   `cd .claude/skills/acos-reverse-cleanroom/scripts && bun add playwright && bunx playwright install chromium`
2. **API keys** for external seats you enable: `ZAI_API_KEY` (GLM `zai:glm-4.7`, direct z.ai
   Coding-Plan endpoint — inject via Doppler), `OPENROUTER_API_KEY` (DeepSeek + Kimi), and
   `GOOGLE_API_KEY` for Gemini (`gemini-flash-latest` runs on the FREE tier — but for an `own`-target
   run see prereq 3: the free tier may train on inputs, so a billing-linked PAID no-train key is
   required there). Claude seats use the session (no key).
3. **Proprietary-target posture:** for `target.class: own`, use ZDR/no-train/self-hosted endpoints only;
   Kimi is auto-excluded; Gemini must be the paid key.
4. **Egress hook arming:** the skill adds the session-scoped PreToolUse hook at Phase −1 and removes it
   at close (see `references/egress-and-cleanroom.md`). It is deliberately NOT globally auto-wired.
5. **Authed roles:** provide a Playwright storage-state per non-anon role (a human login) — the skill
   never automates a login-wall bypass.

## Not attempted (out of scope for authoring)
- No end-to-end run against a live app yet (needs the prerequisites above).
- No benchmark for intent-spec fidelity exists — the skill defines a new eval axis; treat first
  runs as calibration.
- Legality of AI-authored clean-room specs is untested — personal aid, output for incremental
  (strangler-fig) adoption, never big-bang.
