# Implementation Plan — 005-resurrection-protocol
*(`/preeng.plan`. Inputs: `spec.md`, `research.md`. Preconditions OK — both exist; `research_qa_report.json`
= APPROVED. Vertical-slice, demo-driven; each slice ships a working increment + an evidence bundle + Dev/QA
learnings. Priority is non-negotiable: **Phase 0 (diagnostic) FIRST.**)*

## 1. Build strategy
Six epics, built in strict priority order. Each epic decomposes into vertical slices (see `stories.json` /
`tasks/`). Every slice is authored under the three-agent LCE pattern (PM=architect / Dev=developer /
QA=reviewers) and is not **Done** until its evidence bundle AND `## Dev Learnings` / `## QA Learnings` are
updated. **Ship is gated on Demo 3 (DR-1); a placebo close is a higher-risk product than none.**

- **EPIC-0 — Phase-0 prerequisites & probe battery (THE DIAGNOSTIC SLICE, §0.3).** cmux 0.64.19 verification
  battery (in-pane hook firing #5427; `rpc workspace.list` JSON; `--description` round-trip; `workspace.select`
  focus; DP2 sacrificial `workspace.close`/last-workspace/`customDescription`-restart; DP4 hibernation);
  fix residual #10 (`eternity-resume-prepend.sh:158-169` pane-blind tier-3); fix `head -40`
  (`eternity-protocol-core.sh:139` + byte-identical Application Support bin twin + bin-manifest regen); close
  P1-F fail-open (`token-watcher.py:1113` + manifest); 147-run provenance (0.6); `--command` probe (0.7);
  optional `archive-project.sh --yes` hardening (0.8).
- **EPIC-1 — Registry core.** `registry_lib.py` (atomic write, schema, casefold index, inode re-link,
  tombstone, audit); `enroll-project.sh` + additive user-level SessionStart hook + `realpath(cwd)==root`
  assertion; `rebuild-registry.py` (v1 + DP5 seeder); seed + one ~10-min human curation pass.
- **EPIC-2 — Safe close.** `close-project.sh` steps 0–10 + four guards + last-workspace guard (parameterized
  by 0.2c) + agent-03 7-check gate; `acos-safe-close/SKILL.md` thin router; blind round-trip verifier (step 5,
  general-purpose Task, Wigum cap 5 → DEGRADE).
- **EPIC-3 — The menu.** `resurrect-view.py` (fresh book, liveness joins, tiers, BROKEN red, no green) +
  `acos-resurrect/SKILL.md` (surface per DP1, menu-first) + finish verb; `launch-project.sh` focus-or-launch
  (SPINE 1 acceptance test); loop mechanics (parked→active, completed on finish; `/acos-complete` untouched).
- **EPIC-4 — DR-1 ship gate.** Full cycle on a real project; recording/receipts → `.acos/evidence/`.
- **EPIC-5 — (DP1-conditional, optional) Browser window.** `resurrection-server.py` at `127.0.0.1:8820`.

## 2. Priority order (build sequence)
1. **EPIC-0 Phase-0 FIRST** — fix residual #10 BEFORE the registry makes two-panes-one-project routine; fix
   `head -40`; close P1-F; run the cmux 0.64.19 probe battery + DP2 sacrificial tests; check 147-run provenance.
2. EPIC-1 Registry core (enrollment before any close; rebuild proven; seed + curate).
3. EPIC-2 Safe close (enrich-not-create; verified receipt; validated fail-closed `workspace.close`).
4. EPIC-3 The menu (fresh book; focus-never-launch SPINE 1 acceptance; loop mechanics).
5. EPIC-4 DR-1 ship gate — nothing ships until the recorded round-trip exists.
6. EPIC-5 Optional browser window (only if DP1 selects it).

## 3. Rollout & demo checkpoints (§0.8 vertical slices)
- **Demo 1 — Enrollment.** New session in a marker dir → derived row; `rebuild-registry.py` reproduces 16/16;
  ACOS 3.0's two live workspaces (4 and 5) render as ONE row.
- **Demo 2 — Safe close on a THROWAWAY.** Receipt says SAFE only on full pass; tab closes as the literal last
  act; artifacts co-located under `closed/<slug>/` and glob-invisible to Eternity.
- **Demo 3 — DR-1 (the ship gate).** Full close→resume round-trip on a real project with user-confirmed
  continuity; recording archived. **Ship gated here.**

## 4. Orchestration & edge constraints (§0.9)
- **Target stack:** ACOS's own skill+agent+hook system; the eventual executor is `/acos-execute-slice`. PM≈
  architect (spawns), Dev≈developer (scoped), QA≈qa/security/performance/integration-reviewers (isolated,
  behind the Independence Wall).
- **Durable execution / resume-after-interruption:** the feature IS a durability mechanism — enrollment +
  native transcripts + rebuild-from-disk mean an interrupted build resumes with no registry loss. Build-time
  continuation is carried by the Eternity Protocol (pane-durable), which this feature must never contaminate.
- **Human-in-the-loop nodes (PM/QA approval pauses):** DP1–DP5 decisions (defaulted, each an Assumption to
  confirm); the ~10-min DP5 curation pass; the DP2 user-scheduled cmux restart; and the DR-1 user
  confirmation of continuity — the single mandatory human gate before ship.
- **Observability (logs/traces/metrics per agent/slice):** append-only `~/.acos/registry-audit.jsonl`
  (enroll/close/resume/finish/tombstone); Phase-0 evidence bundles + tamper transcripts + DR-1 recording under
  `.acos/evidence/[DATE]/[SLICE-ID]/`; agent identity at `.acos/metrics/agent-completions.log`.
- **Edge constraints:** stdlib-only Python (`/usr/bin/python3` 3.9.6, no `yaml`, no `timeout`/`gtimeout`);
  absolute binary paths always; O(1) fail-open enrollment that never blocks session start; the daemon state
  dir is off-limits except `state/stop-<sid>`.

## 5. Metric & governance scaffolding (§0.5)
- **Production:** SPD (qualitative); `QAP = (Delivered_Value * Quality_Score) / (1 + Rejection_Count)`.
- **Efficiency:** TER = artifacts per 1K tokens; artifact-volume per unit cost.
- **Universal:** `UAPS = 0.3*Quality + 0.4*Efficiency + 0.3*CostEffectiveness`.
- **Product success:** DR-1 achieved; rebuild ≥16/16; daemon-writes==1; workspace-count-constant on open pick;
  `listed N of M` == `git status --porcelain | wc -l`; adoption ≥1×/week at day 60 (baseline ~30%).
- **Instrumentation plan (recording locations):** `.acos/metrics/agent-completions.log` (agent identity) +
  `~/.acos/registry-audit.jsonl` (product events). Formulas are defined, not computed here.

## 6. Bloat management & canonicalization (§0.6)
- **Active:** all EPIC-0…EPIC-4 artifacts (recent + needed for ship).
- **Review (canonical-example candidates):** `registry_lib.py` atomic-write path (the mkstemp/fsync/replace
  reference); the verified-read-back receipt; the blind round-trip verifier. Annotated in `analysis-report.md`.
- **Burn Pile (annotate only, never delete):** superseded probe transcripts once the behavior is settled; the
  DP5 pre-curation seed listing. Nothing is deleted; rows are tombstoned, artifacts are annotated.

## 7. Assumptions carried into build (each to confirm)
DP1=A (terminal-first), DP2=A (full battery + one restart), DP3=OFF, DP4=A (opt-in post-test), DP5=A (seed +
curate). All cmux 0.64.x *behavior* requirements are Assumptions until the Phase-0 battery settles them; slices
resting on them declare the Assumption in their DoD and attach the probe evidence.

## 8. Touched vs left-alone (exhaustive)
- **TOUCHED:** `eternity-resume-prepend.sh` (0.3); `eternity-protocol-core.sh:139` + its Application Support
  bin twin + bin-manifest (0.4); `token-watcher.py:1113` + bin-manifest (0.5); `~/.claude/settings.json`
  (one additive SessionStart entry, 1.2); optionally `archive-project.sh` (0.8); plus all NEW files under
  `.claude/scripts/resurrection/` and the two new skills.
- **LEFT ALONE:** the daemon state dir (except `state/stop-<sid>`); `pending-resume-*.txt` /
  `RESCUED-resume-*.txt`; top-level `memory/handoffs/` + `memory/handoffs/archive/`; `register-session-pid.sh`
  and the rest of the token-monitor bin; `/acos-complete`, `/acos-handoff`, `/acos-resume-prompt`, the Eternity
  skills; the human-editable reviewer trigger-rules directory; agent definitions (no new agents — the round-trip
  verifier uses a general-purpose Task).
