# ACOS v3.0 — Complete Deficiency Assessment

**Date:** 2026-06-04
**Method:** Deep grounded audit. Six read-only auditor agents (plus main-thread verification) read the actual skills, agents, hooks, scripts, config, planning artifacts, memory, and learning directories. Every Critical/High finding below was verified against a real file. Claims that contradicted `CLAUDE.md` were re-checked directly.
**Lens:** Holistic, anchored against the `preeng` (Pre-Engineering) skill where it exposes a structural gap.
**Scope audited:** Planning & pre-engineering · Execution & evidence · Review & Independence Wall · Agents & model profile · Hooks/enforcement/Oracle/continuity · Memory/learning/knowledge.

> **One-line verdict:** ACOS is a well-*designed* framework whose **prose substantially overstates what is mechanically active**. The dominant deficiency class is "documented but not enforced / not wired / write-only," not "badly designed." Most fixes are wiring, not redesign.

> ### ⚠️ VERIFICATION PASS APPLIED 2026-06-04 (v2)
> Every finding was independently re-verified against ground truth (live commands, exact file:line, and the full **4-file** settings merge — `~/.claude/settings{,.local}.json` + `.claude/settings{,.local}.json`). Result: **48 of 49 findings CONFIRMED, 1 REJECTED (former #1 / H-1), 1 NEW finding added (1.12), 5 wording revisions.** The original audit's fatal error was checking only the *project* settings file; corrections are marked inline below. Verdicts on the corrected items were re-run first-hand, not delegated.

---

## Executive Summary — Six Cross-Cutting Root Causes

1. **Documentation–reality drift (systemic).** The framework's self-description does not match the filesystem and cannot be trusted as ground truth. Verified examples: `MEMORY.md` claims "14 agents" vs **40** on disk; the removed `auto-load-handoff.sh` is still referenced in **5** live files. *(Note: the original "continuity hooks unregistered" example was itself a documentation-vs-single-file-read error — the hooks are active in the user-global settings file; see corrected 1.1 / 1.12.)*

2. **"Documented, not enforced."** Core guarantees are *prompt instructions to the very agent they constrain* rather than mechanical gates: verdict aggregation, the Independence Wall in interactive mode, scope (bypassable via Bash), evidence authenticity (self-attested). The "mechanical enforcement" ACOS advertises has holes.

3. **Fail-open everywhere.** Oracle, quality gates, scope check, and config parsing all default to *allow/skip* on error or missing file. Convenient, but governance loss is silent and indistinguishable from approval.

4. **Write-only knowledge.** The learning/memory/RAG/metrics machinery exists but is dark: RAG indexes **3.4%** of files, agent-metrics log is **1,972 lines of `unknown`**, **one** retrospective since February, learnings are never auto-retrieved into planning or execution.

5. **Planning rigor depends entirely on Architect discipline.** No mandatory research, domain compilation, competency questions, evidence tiers, diagnostics, data model, or coverage check. When ACOS output is good, it's because the Architect *chose* to add custom fields — the framework guarantees none of it. This is the area `preeng` most directly exposes.

6. **No one reviews the reviewers.** Re-review is not blind, evidence is self-reported, and a lazy reviewer returning PASS is indistinguishable from a rigorous one. The adversarial wall is one layer deep.

### Highest-priority items (the "fix these first" list)
| # | Deficiency | Severity | Subsystem |
|---|-----------|----------|-----------|
| ~~H-1~~ | ~~Continuity hooks registered to nothing~~ → **REJECTED** (active via user-global settings). Replaced by **1.12**: same hooks **double-registered** across 2 settings files | Low | Hooks |
| ~~H-2~~ | Scope enforcement bypassable via Bash; developer has Bash + acceptEdits — ✅ **FIXED 2026-06-04** | ~~Critical~~ | Execution/Hooks |
| ~~H-3~~ | Independence Wall inactive in default interactive mode — ✅ **FIXED 2026-06-04** | ~~Critical~~ | Review/Hooks |
| ~~H-4~~ | Learning loop write-only — retrieval now wired into plan + execute-slice — ✅ **FIXED 2026-06-04** | ~~Critical~~ | Memory/Learning |
| ~~H-5~~ | RAG index 5/145 → **145/145** (re-indexed + chunker/embedder bugs fixed) — ✅ **FIXED 2026-06-04**. *(agent-metrics `unknown` = separate finding 6.3, still open)* | ~~Critical~~ | Memory/Learning |
| H-6 | Oracle `hard_blocks: []` — force-push & inline `DROP TABLE` auto-approved — ⏸️ **DEFERRED (owner has separate Oracle plans, 2026-06-04)** | **High** | Hooks/Oracle |
| ~~H-7~~ | No mandatory research/domain-grounding before planning — added Step 1.6 (CQs + evidence tiers + diagnostics + coverage gate) — ✅ **FIXED 2026-06-04** | ~~Critical~~ | Planning |
| ~~H-8~~ | Verdict aggregation now mechanical (`aggregate-verdicts.sh`, binding exit code) — ✅ **FIXED**; evidence-authenticity 🟡 partial — 2026-06-04 | ~~High~~ | Review/Execution |
| ~~H-9~~ | Doc drift: agent count corrected (40); stale `auto-load-handoff.sh` refs purged from 5 files — ✅ **FIXED 2026-06-04** | ~~High~~ | Agents/Hooks |
| ~~H-10~~ | Quality gates now wired: added `quality-gates.yaml` (typecheck+test, verified passing) — ✅ **FIXED 2026-06-04** | ~~High~~ | Execution |

---

## 1. HOOKS, ENFORCEMENT, ORACLE & CONTINUITY

> Verified directly in main thread against `.claude/settings.local.json` and disk.

### 1.1 ~~Continuity hooks wired to nothing — `PreCompact` absent~~ — **REJECTED (false alarm)**
**This finding is withdrawn.** The original audit (and a first verification pass) checked only the *project* `.claude/settings.local.json`. Claude Code merges hooks from **four** files, and the continuity hooks are all registered in the **user-global** `~/.claude/settings.local.json` (verified directly): `token-gate.sh` @PreToolUse, `context-watchdog.sh` @PreCompact, `context-monitor.sh` @Stop. The documented continuity defense **does fire.** The real (different) issue this surfaced is config duplication — see **1.12**. *Lesson: every hook-registration claim in this report was re-checked against the 4-file merge.*

### 1.2 Scope enforcement bypassable via Bash — **Critical** — ✅ **FIXED 2026-06-04**
`check-scope.sh` is registered only for `Write|Edit`. The `developer` agent has `Bash` in its toolset (`developer.md:4`) and `permissionMode: acceptEdits`. Any write via `bash -c "echo … > file"`, `cp`, `mv`, or `python3 -c "open(...,'w')"` bypasses scope containment entirely. `ACTIVE_SLICE` is also a relative path → if hook CWD differs (e.g., a worktree), the check fails open (exit 0). **Impact:** the developer's containment boundary during a slice is porous.
> **FIX:** Added `.claude/scripts/check-scope-bash.sh` (best-effort Bash write-target scope guard) and registered a `Bash` PreToolUse matcher on the developer agent (`developer.md`). Heuristically detects `>`, `>>`, `tee`, `cp`, `mv`, `sed -i`, `dd of=`, `install`, `ln`, `touch` write targets, resolves them repo-relative, and blocks (exit 2) any that fall outside the slice's `files_allowed` (allow-prefixes: `.acos/evidence/`, `.acos/state/`, `memory/`; writes outside the repo are left to the Oracle). Verified 14/14 test cases (7 allow + 7 block). **Residual (not airtight):** idioms like `python3 -c "open(...,'w')"` or `eval`-obfuscated writes are not caught — the airtight containment is `isolation: worktree` on the developer (tracked separately). The relative-path/CWD sub-issue is finding **1.10** (still open).

### 1.3 Independence Wall inactive in default interactive mode — **Critical** — ✅ **FIXED 2026-06-04**
`block-review-rules-read.sh` is **not** in `settings.local.json`; it is registered only as an agent-level PreToolUse hook in `architect.md:17-21` (matcher `Read|Bash`). Agent-level hooks fire only when the architect runs as a spawned sub-agent. In the **default interactive mode the main conversation *is* the architect**, no agent boundary exists, and the hook never fires — the Architect can freely `Read("review-rules/…")`. Even when active, the match is literal-substring (`review_rules.yaml` underscore variant, indirect Python reads slip through). **Impact:** the Independence Wall — a foundational ACOS claim — is unenforced in the most common usage mode.
> **FIX:** (1) Registered `block-review-rules-read.sh` **globally** in project `.claude/settings.local.json` (matcher `Read|Bash|Grep|Glob`, **bare** — no `|| printf allow` wrapper, which would negate the exit-2 block) so it fires for the interactive main conversation. (2) Hardened the script to also inspect the `path` field (closing the `Grep`/`Glob` read-vector gap) and to block the underscore `review_rules` legacy variant. Verified 12/12 cases (7 block vectors + 5 allow), `assign-reviewers.sh` not self-blocked, and confirmed **live** (the hook blocked a real interactive Bash call this session). The architect agent-level hook is left in place (harmless redundancy in Task(architect) mode). **Note:** the wall is now active for *this* project's interactive sessions — agents/main conversation can no longer read `review-rules/`; edits to those files are human-only by design (relevant when addressing findings 4.7/4.8).

### 1.4 Oracle `hard_blocks` cleared to empty — **High** — ⏸️ **DEFERRED (owner has separate Oracle plans)** · applies to all Oracle findings 1.4–1.7
`.acos/config/oracle.yaml:76` sets `hard_blocks: []`, which *overrides* the Python defaults (force-push, `rm -rf /`, `DROP TABLE/DATABASE`). Live scoring: `git push --force origin main` → **allow**; `psql -c "DROP TABLE users;"` → **allow** (temp 5 < threshold 9). Only `rm -rf /` still escalates (regex match → temp 10). **Impact:** destructive operations the docs claim are "high-temperature" execute silently.

### 1.5 Oracle fail-open is total and silent — **High**
`oracle-evaluate.py:844-846` top-level `except Exception → allow`; `load_config` has bare `except: pass`; shell fallback `|| printf '…allow…'`. A corrupted/adversarial `oracle.yaml`, or any Python crash, disables all permission governance with **no degraded-mode signal**. The audit log skips `allow` decisions, so failure leaves no trace. **Impact:** Oracle failure is indistinguishable from Oracle approval.

### 1.6 Autopilot raises permissiveness and skips audit logging for approvals — **Medium** *(REVISED — "bypasses entirely" was overstated)*
`oracle-evaluate.py:550`: with the `autopilot-active` sentinel, non-hard-block tools return `allow` (reason `autopilot_allow`) without temperature scoring, and that allow is **not** audit-logged (`audit_log` skips `allow`, line 487). **Correction:** autopilot does **not** bypass the Oracle entirely — a destructive-op `AUTOPILOT_HARD_BLOCKS` list (lines 270-287) still escalates, and it **does** cover inline `DROP TABLE`/`TRUNCATE`/`DELETE`-without-WHERE plus dangerous `rm`/`find`/`xargs`/`dd`. What it **omits** is `git push`, `git push --force`, and `git reset --hard`. **Impact:** under autopilot those git operations execute with no prompt and no audit trace.

### 1.7 `oracle-session-threshold` persists across sessions — **Medium**
`session-cleanup.sh:14` intentionally preserves it; no TTL, no session-ID binding, no startup warning. A YOLO (11) session silently carries into the next, weeks later, with no audit trail. **Impact:** sticky governance-off state.

### 1.8 Evidence log is filename-only and tamperable — **Medium**
`post-write-evidence.sh:12` writes `timestamp MODIFIED path` — no hash, no diff, no size; runs `async`; relative `.acos/evidence/current` path. The log covers itself (a later Write can overwrite it), is not append-only, and has no external witness. Bash writes aren't logged at all (Write|Edit matcher). **Impact:** the evidence trail is neither complete nor tamper-evident.

### 1.9 Eternity/keystroke-injection system is fragile and macOS/Warp-locked — **High**
The cmux/warp protocol chains `register-session-pid.sh` → OSC-2 title stamp → `inject-keystroke.py` (pyobjc `CGEventPost` + AXTitle) → out-of-process `token-watcher.py`. It requires pyobjc (non-stdlib), macOS Accessibility (TCC) grants, and Warp specifically; it silently degrades on any TCC change, terminal switch, or Warp rename. History: ≥6 dedicated bug-fix commits for cross-session misfire, CGEventPostToPid no-op, self-`/clear` impossibility, orphan-JSONL false positive, reverted tmux IPC. **Impact:** high-complexity subsystem with a documented record of destroying live context; a maintenance liability.

### 1.10 Relative-path/CWD fragility across enforcement scripts — **Medium**
`check-scope.sh`, `post-write-evidence.sh`, `token-gate.sh` all use bare relative `.acos/...` paths and don't read the hook's `cwd` JSON field. Reviewer worktrees share the `.acos` symlink for some paths but can fragment state for others. **Impact:** state can split between main repo and worktrees; enforcement may read the wrong file.

### 1.11 Stale `auto-load-handoff.sh` references — **Medium** — ✅ **FIXED 2026-06-04**
> **FIX:** Purged/reworded all 5 stale references: `token-gate.sh` (removed from the required-scripts list at L173 + the health-check loop at L471 — eliminates the permanent false-FAIL), `context-monitor.sh` (handoff text now says "Load it next session with /acos-handoff"), `claude-loop.sh` (comment corrected), `handoff-agent.md` (reworded; restricted-file edit), and `acos-preflight.sh` (removed from the hook-completeness check — which also fixed a latent bug: it only grepped the project settings file for 5 hooks incl. the removed one, so it could never pass and re-bootstrapped every run; now checks project **and** user-global settings for the 4 real hooks).
`context-monitor.sh:339` and `handoff-agent.md:191` instruct future sessions to expect injection by `auto-load-handoff.sh`; `token-gate.sh:173,471` list it as `required` in health checks. That script was removed Apr 2026. **Impact:** health check permanently reports FAIL on a correct install (alarm fatigue); handoffs promise an injection that never happens.

### 1.12 Hook configuration is split-brain and duplicated across two settings files — **Medium** *(NEW — surfaced while rejecting 1.1)*
Both the project `.claude/settings.local.json` and the user-global `~/.claude/settings.local.json` define overlapping `hooks` blocks. **8 scripts are registered in both** and therefore fire twice per event (verified by diffing the two hooks blocks): `oracle-evaluate.py` and `check-scope.sh` (PreToolUse), `post-write-evidence.sh` (PostToolUse), `inject-agent-context.sh` + `log-agent-spawn.sh` (SubagentStart), `log-agent-completion.sh` (SubagentStop), `enforce-quality-gate.sh` (TaskCompleted), `session-cleanup.sh` (SessionEnd). Additionally the Stop event runs two *different* handlers (`context-monitor.sh` from user, `autopilot-stop-handler.py` from project), and continuity hooks live only in the user-global file while autopilot hooks live only in the project file — so there is no single source of truth. **Impact:** `oracle-evaluate.py` running twice risks double permission evaluation/prompts; `post-write-evidence.sh` writes duplicate log lines. The command strings differ between files (one is `cd … && script`, the other has a `|| printf allow` fallback), so exact-match dedup would not collapse them — runtime double-execution is highly likely though not empirically proven here. **Fix:** consolidate to one authoritative hooks block; dedupe the 8; decide whether dual Stop handlers are intentional.

**Strengths:** `find_project_root()` dual-strategy fallback; atomic `tmp+mv` writes in `token-gate.sh`/`context-watchdog.sh`; reviewer isolation via `permissionMode: plan` + `disallowedTools` (does not depend on hooks); autopilot `UserPromptSubmit` panic-stop; **the continuity defense (handoff-on-Stop, mechanical-on-PreCompact, token-gate) is genuinely active** via the user-global settings.

---

## 2. PLANNING & PRE-ENGINEERING

### 2.1 No mandatory research / feasibility gate before planning — **Critical** — ✅ **FIXED 2026-06-04**
`acos-interview/SKILL.md:29-83` goes from user Q&A straight to document creation; `acos-plan/SKILL.md:26-83` goes from interview to epic decomposition. No required step verifies prior art, feasibility, or domain constraints. (VISION-HVC-01 had a *voluntary* research pre-round — not mandated anywhere.) **preeng-contrast:** preeng's Phase 0 *requires* domain research, a knowledge lattice, and a `research.md`/`domain-brief.md` before requirements.
> **FIX:** Added **Step 1.6 "Domain Grounding & Competency Questions"** to `acos-plan/SKILL.md` — **mandatory at vision/epic level**, recommended at story, skippable at slice. It requires: diagnostics (problem-before-solution), 8–15 Competency Questions answered from tiered evidence (T1–T5), a **≥80% coverage gate** (gaps become explicit Open Questions/Assumptions, never silent), and a durable artifact written to `planning/domain-briefs/` from a new `templates/domain-brief.md`. Uses RAG (Step 1.5) for internal priors + `WebSearch`/`WebFetch` (added to allowed-tools) for external facts. This is the distilled preeng "Constitutional Domain Compilation" in ACOS idiom. **Note:** a process gate — its force is that grounding is now a *checkable, reviewable artifact* rather than architect discretion.

### 2.2 No evidence-quality tiers on planning claims — **Critical** — 🟡 **PARTIALLY FIXED 2026-06-04**
No template (`vision-document.md`, `vision.yaml`, `slice.yaml`) has a source/confidence field. Unverified assertions silently become requirements — exactly the cause of the EPIC-001 PPTX scope blow-up (`EPIC-001-…yaml:609-712`). The `deep-research` skill defines T1–T4 tiers but is **not wired into planning**. **preeng-contrast:** preeng tiers every claim T1–T5 and requires citations before locking T3+ requirements.
> **PARTIAL FIX:** The Step 1.6 domain-brief now tags every competency-question answer with a T1–T5 evidence tier and tracks % at T1–T3. **Still open:** tiers are not yet required on claims *inside* the vision/epic/story/slice YAML templates themselves (only in the domain brief). Full fix = add a source/tier field to those templates.

### 2.3 No diagnostic protocol ("problem before solution") — **High** — 🟡 **PARTIALLY FIXED 2026-06-04**
The interview has no structured "symptoms / affected users / current-vs-desired" category; templates have no Problem-Statement/Current-State section. **preeng-contrast:** preeng mandates a documented diagnosis before any requirement.
> **PARTIAL FIX:** Step 1.6's domain brief opens with a mandatory **Diagnostics** section (symptoms / affected users / current-vs-desired / root-cause hypotheses) at vision/epic planning. **Still open:** `acos-interview` itself has no diagnostics question category, and slice/story templates have no problem-statement field.

### 2.4 No competency-question / coverage exit condition — **High**
Interview exit (`acos-interview/SKILL.md:79-83`) is "Architect satisfied" / user signal / iteration count — all subjective. No mechanism detects domain blind spots or verifies feature→slice coverage. **preeng-contrast:** preeng writes 10–15 CQs and expands until ≥95% are answerable — a measurable exit gate.

### 2.5 No data-model / domain-model artifact required — **High**
`acos-plan` requires only vision/epic/story/slice YAML. The visual composer's central `ContainerRecord` type appeared only inside a story's `technical_notes` after the fact. Type contracts get invented slice-by-slice. **preeng-contrast:** preeng mandates `data-model.md` as a planning output.

### 2.6 No cross-artifact coverage check — **High**
`acos-plan` Step 2 is a single "read for alignment" — no audit that every Must-Have feature maps to ≥1 slice acceptance criterion, every risk to ≥1 epic. Features can silently fall through. **preeng-contrast:** preeng emits a traceability/analysis report flagging untraced requirements.

### 2.7 ADRs optional and unwired — **High**
`acos-decide` is referenced by no planning/execution skill. EPIC-003 (XL, multiple tech choices) has **zero** ADRs; decisions live as prose `technical_notes` invisible to the learning-agent. Only 2 project ADRs exist, both for an archived epic.

### 2.8 Vision-layer YAML never created — **High**
`planning/vision/` holds only `.template.yaml`. EPIC-003 references `VISION-HVC-01` but no machine-readable vision plan exists — only prose Markdown. Tooling cannot query "which epics belong to this vision."

### 2.9 Slice DoD has no explicit evidence gates — **Medium**
`slice.yaml:18-23` acceptance criteria are freeform checkboxes; no field specifies the required artifact/pass-condition (coverage %, benchmark file, screenshot path). "Done" is reviewer subjective judgment. **preeng-contrast:** preeng's DoD names explicit evidence gates.

### 2.10 No per-slice Dev/QA learnings field — **Medium**
`slice.yaml` has no `dev_learnings`/`qa_learnings`. Learnings are captured (if at all) only at epic end via manual `/acos-learn`. **preeng-contrast:** preeng mandates Dev/QA learnings per slice at completion.

### 2.11 No tech-PRD artifact — **Low**
NFRs (latency, error contracts, observability) scatter across `technical_notes`. No single artifact a reviewer can check for completeness. **preeng-contrast:** preeng mandates a standalone `tech-prd.md`.

**Strength:** When used well, ACOS output is genuinely high-quality (VISION-HVC-01 vision doc; STORY-003-001 acceptance criteria; ADR-001). The gap is that quality is *discretionary*, not *structural*.

---

## 3. EXECUTION & EVIDENCE

### 3.1 Quality gates fail-open and are absent on this project — **High** — ✅ **FIXED 2026-06-04**
> **FIX:** Created `.acos/config/quality-gates.yaml` with two `pre-review` gates targeting the active app — `typecheck` (`pnpm -C apps/visual-composer typecheck`) and `test` (`pnpm -C apps/visual-composer test`), both `required: true`. Verified end-to-end: `run-quality-gates.sh pre-review` → `passed: true, skipped: false`, both gates execute and pass (previously `skipped: true`, i.e. silently no-op). Commands use `pnpm -C` (not `cd &&`) because the runner uses `shlex.split`+`shell=False`. **Residual:** the fail-*open*-when-missing behavior of `run-quality-gates.sh` itself is unchanged (a design choice — gates are opt-in); now that a config exists it is moot for this project.
`run-quality-gates.sh` returns `{"passed": true, "skipped": true}` when `.acos/config/quality-gates.yaml` is missing — and it **is missing** here (verified). `acos-execute-slice/SKILL.md:85` confirms gates are "optional." So lint/typecheck/test gates silently pass on every slice. The `TaskCompleted → enforce-quality-gate.sh` hook fires but has no config to enforce. **Impact:** the pre-review quality gate is decorative on this (the framework's own) project.

### 3.2 Evidence is self-attested, not machine-verified — **High** — 🟡 **PARTIALLY FIXED 2026-06-04**
Evidence bundles contain `verify.log` + `Summary.md` + `git-diff.patch` + `modified-files.txt`. `verify.log` and `Summary.md` are **written by the developer being reviewed**; the QA reviewer "re-runs commands from verify.log" — commands chosen by that same developer. No mechanism generates independent verification from the acceptance criteria. **preeng-contrast:** preeng's QA independently recomputes rather than validating self-reported evidence.
> **PARTIAL FIX:** Two independent checks now exist that don't rely on developer self-report: (1) the mechanical **quality gates** (finding 3.1 / D fix) run typecheck+test from config before review, independent of `verify.log`; (2) `acos-execute-slice` Step 7's reviewer prompt now carries an **evidence-authority directive** telling reviewers to treat the quality-gate output as authoritative and independently derive ≥1 verification from the acceptance criteria rather than only re-running the developer's commands. **Still open (needs restricted `qa-reviewer.md` edit + tooling):** a mechanism for QA to *generate* its own test suite from acceptance criteria, and a structured/hashed evidence bundle (finding 3.3).

### 3.3 Evidence bundle has no structured schema — **High**
Bundles are an ad-hoc file set, not the preeng 7-part structure (Implementation Summary / Requirements Traceability / Quality Evidence / Functional Testing / Security-Compliance / Operational Considerations / Self-assessment with confidence + known limitations). No requirements-traceability and no confidence/limitations field exist as required artifacts. Naming is inconsistent (`SLICE-003-001-03` vs `shell-injection-fix` vs `PPTX-DEFECT-FIX`).

### 3.4 Scope bypass via Bash (see 1.2) — **Critical** *(cross-listed)* — ✅ **FIXED 2026-06-04** (see 1.2)
Developer has Bash + acceptEdits; `check-scope.sh` only guards Write|Edit. Closed by `check-scope-bash.sh` + Bash matcher on the developer agent; best-effort (residual: in-process write idioms; airtight = `isolation: worktree`).

### 3.5 No automatic rollback on slice failure — **Medium**
On repeated REJECT, the path is "escalate to human" (`acos-execute-slice/SKILL.md:151,169`) after 3 iterations. There is no automatic revert of partial/abandoned changes; the working tree is left mid-flight. Caps exist (good) but cleanup does not.

### 3.6 No demo-able vertical-slice enforcement — **Low**
Nothing requires a slice to produce a runnable/demo increment. **preeng-contrast:** preeng mandates named demo checkpoints and user-visible-value-early ordering.

**Strengths:** Iteration caps (max 3 quality-gate, max 3 feedback) with explicit human escalation; a clear error-handling table; `run-quality-gates.sh` uses `shlex.split`+`shell=False` (injection-safe); bundles are at least *present and dated* per slice.

---

## 4. REVIEW & INDEPENDENCE WALL

### 4.1 Independence Wall inactive in interactive mode (see 1.3) — **Critical** *(cross-listed)* — ✅ **FIXED 2026-06-04** (see 1.3)

### 4.2 Verdict aggregation is natural-language, applied by the Architect — **High** — ✅ **FIXED 2026-06-04**
`acos-review/SKILL.md` Step 6 / `acos-execute-slice` Step 8 instruct the Architect to "mark passed if ALL PASS." No `aggregate-verdicts.py` / mechanical gate runs. The entity being guarded against also interprets the verdicts and can rationalize a borderline REJECT into a PASS.
> **FIX:** Added `.claude/scripts/aggregate-verdicts.sh` (the authoritative gate) and rewrote `acos-execute-slice` Step 8 to be mechanical: the Architect records each reviewer's raw verdict to `.acos/state/review-verdicts/<slice>/<reviewer>.json` + the assigned list to `expected.json`, then runs the script whose **exit code is binding** ("you MUST NOT override it"). Rule: every *expected* reviewer must have a `PASS` file; any REJECT/INCONCLUSIVE/missing → exit 2 (blocks). Verified 6/6 cases incl. missing-reviewer → block (mechanizing the INCONCLUSIVE-blocks-like-REJECT policy). The Architect can no longer rationalize the aggregate — only record raw verdicts. **Residual:** `acos-review/SKILL.md` (the standalone review skill) still uses prose aggregation — same script should be wired there too.

### 4.3 No review of the reviewers — **High** — 🟡 **PARTIALLY FIXED 2026-06-04**
No agent/hook/step audits reviewer output for completeness. A reviewer returning `PASS` with zero findings on a 500-line security diff is treated identically to a thorough one. The independent-verification group exists only in the standalone `acos-swarm-review`, **not** in the standard `acos-execute-slice` path most work uses.
> **PARTIAL FIX:** `aggregate-verdicts.sh` now emits a `warnings[]` **rubber-stamp detector** — any PASS with no `issues` *and* no `checks_performed` is flagged (verified), and reviewers are now required to report `checks_performed` (execute-slice Step 7). The skill must surface these warnings, not silently accept. **Still open (deferred):** a true independent meta-reviewer agent that re-derives findings (the `acos-swarm-review` verification group ported into the standard path).

### 4.4 Re-review is not blind — **High** — ✅ **FIXED 2026-06-04**
`acos-feedback-resolution/SKILL.md:55` re-runs the *same* reviewer set, and the evidence bundle they read contains the Architect's synthesis of the prior round's findings — so re-reviewers learn what was flagged and anchor on "is it fixed?" rather than re-discovering issues. (`acos-robust-code-review` deploys fresh memoryless agents; the default path does not.) **preeng-contrast:** blind re-dispatch is a core preeng primitive.
> **FIX:** Rewrote `acos-feedback-resolution` Step 5 as **blind re-review**: re-reviewers receive ONLY the updated code, original spec, and acceptance criteria — never the prior round's feedback, verdicts, fix plan, or rationale — and re-evaluate from scratch. Step 6 now uses the mechanical `aggregate-verdicts.sh` gate (consistent with Step 8).

### 4.5 Reviewer assignment depends on Architect-authored `code_snippets` — **High** — ✅ **FIXED 2026-06-04**
`acos-execute-slice/SKILL.md:95` has the Architect populate `code_snippets`, which drives security/perf reviewer triggers (`assign-reviewers.sh`). Omit "jwt" when touching auth and the security reviewer is never assigned. No fallback mechanical extraction from modified files.
> **FIX:** `assign-reviewers.sh` now **mechanically reads the contents of every modified file** (`_read_modified_contents`) and matches code-pattern triggers against `snippets + actual file contents` (`code_haystack`). Assignment no longer depends on the Architect enumerating patterns — verified: an empty `code_snippets` with a file whose content contains a trigger still fires.

### 4.6 Trigger matching is plain substring — **High** — ✅ **FIXED 2026-06-04**
`assign-reviewers.sh` uses `pattern in filename`. Security patterns include `key`, `api`, `role`, `order`, `index` → `monkey.ts`, `capital.ts`, `controller.ts`, `border.ts` all spuriously trigger; conversely novel names evade. High noise + no false-negative defense.
> **FIX:** Replaced substring matching with `_matches()`: glob patterns → `fnmatch` (path + basename); patterns with `/` → substring (explicit path fragments); bare words → **word-boundary regex**. Verified 12/12: `key`↛`monkey.ts`, `api`↛`capital.ts`, `role`↛`controller.ts` no longer false-trigger, while `auth`→`src/auth/login.ts`, `*.sql`, and code-token matches still fire.

### 4.7 Coverage gaps: no a11y / observability / data-integrity / license / cost reviewer — **High**
`review-rules/` has only qa/security/performance/integration/legal. Inaccessible UI, a GPL-contaminated dependency, a removed telemetry span, or a cost regression pass with no findings.

### 4.8 `legal-analyst` can never be auto-assigned — **Medium**
`assign-reviewers.sh:100` globs `*-reviewer.yaml`, which **excludes** `legal-analyst.yaml`; and the file itself declares it non-gating (`legal-analyst.yaml:138-140`). For OKOA's lending domain, a slice touching loan-doc logic passes all gates with no legal surfacing.

**Strengths:** Reviewer isolation (`disallowedTools: Write,Edit,Task` + `permissionMode: plan` + `isolation: worktree`) is genuinely mechanical and sound; INCONCLUSIVE-blocks-like-REJECT is correct; the rule files themselves are well-constructed.

---

## 5. AGENTS & MODEL PROFILE

### 5.1 Roster documentation drift: 40 agents on disk vs "14" documented — **High** — ✅ **FIXED 2026-06-04**
> **FIX:** Corrected the count in `MEMORY.md:74` to **40 agents** with an accurate breakdown (10 core + 3 loan-doc + 2 fin-stmt + 15 dr2 + 8 grader + 2 domain), and noted that the project `CLAUDE.md` "Agent Roster" deliberately lists only the curated core (skill-internal `dr2-*`/`grader-*` families are intentionally omitted there). **Residual:** no automated roster-reconciliation check yet (finding 5.2 — would prevent future drift).
`ls .claude/agents/*.md` → **40** files (architect, developer, 4 reviewers, memory/learning, general-purpose, handoff, + domain families: **dr2-\*** ×15, **grader-\*** ×8, **loan-doc-\*** ×3, **fin-stmt-\*** ×2, electronics-expert, legal-analyst). *(Source correction: the "14 agents (9 original + 3 loan-doc + 2 financial-statement)" claim is in **`MEMORY.md` line 74**, not the project `CLAUDE.md` — grep of project CLAUDE.md returns 0 matches.)* The self-description is ~3× off. **Impact:** no source of truth for the roster; onboarding and reasoning about the system start from wrong premises.

### 5.2 No roster/skill reconciliation — **Medium**
Nothing verifies that every agent is spawned by some skill, or that every `Task(agent)` names an agent that exists. With 40 agents across many standalone skills, orphan agents and dangling references can accumulate undetected. (No manifest, no CI check.)

### 5.3 Premium-everywhere cost profile — **Medium**
`architect`, `developer`, and all reviewers declare `model: opus`; `default_profile: premium`. A full slice (architect + developer + 4 opus reviewers in worktrees, ×N feedback iterations) is expensive. The model-profile system *can* downshift, but the default runs the most costly configuration for routine slices. (User has explicitly chosen Premium — noted, not a defect per se, but a cost-exposure to be aware of.)

### 5.4 Developer is comparatively over-toolled — **Medium**
`developer.md` has `Bash` + `Write`/`Edit` + `permissionMode: acceptEdits` with scope only guarded on Write|Edit (→ 1.2/3.4). The Bash grant is what makes scope containment porous.

### 5.5 External-model fallback warning may not surface — **Low** *(REVISED — not "silent" at code level)*
`resolve-agent-model.sh:219-226` **does** emit an explicit `Warning: … requires Claude … falling back to '<fallback>'` to stderr, and `run-external-agent.py` `sys.exit(1)`s rather than silently falling back. **Correction:** the code is not silent. The real, narrower concern is a *runtime visibility gap* — stderr from `resolve-agent-model.sh` invoked inside a `Task()` subagent may not reach the user's terminal, so a fallback could go unnoticed in practice.

**Strengths:** The model-profile system **is** wired into the real orchestration path — `resolve-agent-model.sh` is referenced by `acos-execute-slice`, `-story`, `-epic`, `-review`, `-complete-vision`, `-learn`, `-status`, `-model-change`, `-robust-code-review`, and domain skills (not dead config). Reviewer frontmatter is consistent and correctly locked down. Architect tool-scoping (explicit `Task(...)` allowlist) is well done.

---

## 6. MEMORY, LEARNING & KNOWLEDGE

### 6.1 Learning loop is write-only — **Critical** — ✅ **FIXED 2026-06-04**
Neither `acos-plan` nor `acos-execute-slice` queries the learning-curve, memory-agent, or `rag-query.sh` before acting. The architect "learns from the learning curve" is a character description, not a wired step. `/acos-learn` is manual-only with no inbound trigger. **Impact:** every project starts cold; 20 prior runs confer no advantage. **preeng-contrast:** preeng captures *and applies* learnings.
> **FIX:** Added **Step 1.5 "Retrieve Prior Learnings (RAG)"** to both `acos-plan/SKILL.md` and `acos-execute-slice/SKILL.md`. Each queries `rag-query.sh` for the planning subject / slice objective before acting, prioritizes `category: decision|learning|handoff`, folds applicable lessons in (execute-slice passes them into the developer prompt), and falls back to grepping `memory/`+`learning-curve/` if the index is unavailable — never silently skipping. Added `Bash` to `acos-plan` allowed-tools. Closes the *retrieval* half of the loop (paired with the 6.2 index fix). **Still open:** the *capture* half — per-slice learnings written at completion (findings 2.10 / 6.10).

### 6.2 RAG index covers 3.4% of files — **Critical** — ✅ **FIXED 2026-06-04**
`rag-index.sh --stats` → 5 of 145 discoverable files indexed (25 chunks); the 5 are README/index files + two Feb handoffs. 120 archived handoffs, all learnings, decisions, evidence, reviews are invisible. Ollama/nomic-embed are installed and working — this is a maintenance failure, not a capability gap. RAG-first retrieval returns ~nothing; grep fallback always wins. **Impact:** the vector DB is effectively dark.
> **FIX:** Ran a full re-index → **145/145 files, 1,588 chunks, 0 errors** (was 5/145). En route, found & fixed two real RAG bugs: (1) `chunker.py` emitted oversized chunks (invalid-YAML / non-dict / oversized-scalar paths produced one ~19 KB chunk that 400'd the embedder) — added a `MAX_SIZE` enforcement pass (`_enforce_max_size` / `_split_text_to_max`) so no chunk exceeds 2 KB; (2) `embedder.py` `embed_texts` sent all chunks in one request — added sub-batching (16) with per-item fallback. Verified semantic retrieval returns relevant hits (`relevance` ~0.61). **Note:** indexer `SCAN_DIRS` is `memory/`+`learning-curve/` only — `review-rules/` is correctly NOT indexed, so RAG cannot leak it past the Independence Wall (1.3). **Residual:** index is refreshed manually; no auto-reindex hook yet (worth a SessionEnd/PostToolUse trigger — small follow-up).

### 6.3 Agent-performance metrics are permanently blank — **High**
`.acos/metrics/agent-completions.log` = **1,972 lines of `COMPLETED unknown`** (agent identity never wired). `agent-effectiveness/` subdirs hold only `.gitkeep`. Cannot answer which agent/reviewer/skill is effective. **preeng-contrast:** preeng specifies QAP/TER/UAPS formulas + instrumentation; ACOS has the log but no identity data.

### 6.4 One retrospective since February — **High**
`learning-curve/project-retrospectives/` holds a single file (`2026-04-10`, EPIC-001 only). ~9 major projects since (Ascent dataroom, eternity protocol's 6 bugs, grader, legal-analyst, etc.) produced none. The mechanism works; it just isn't run.

### 6.5 Memory search index does not exist — **High** *(minor wording fix)*
`memory/README.md:49` documents `memory/.index/` (keywords/timeline/agents) — directory is **missing**. `memory-agent.md:59-66` says to maintain it; nothing does. Tier-2 dirs: `feedback-history/` holds only `.gitkeep`; `code-rationale/` holds only a `.template.md` (no actual rationale entries) — *correction: not literally `.gitkeep`, but equally empty of real content.*

### 6.6 Domain-knowledge tier entirely empty — **High**
All of `api-design/ database/ performance/ security/ web-development/` hold only `.gitkeep`; `index.yaml` maps each to `[]`. Cross-project domain lessons (e.g., "bridge lending requires LTC") live only in the one retrospective, never promoted to a discoverable entry. **preeng-contrast:** preeng mandates a domain knowledge-graph lattice with CQ coverage.

### 6.7 ADRs thin and unlinked — **Medium**
3 files in `memory/decisions/`; no `links_to_slice`/`links_to_evidence` fields; no skill reads the directory before planning. Write-only.

### 6.8 No artifact-lifecycle / bloat management — **Medium**
120 untagged archived handoffs, no expiry, no value tiering; `index.yaml` `deprecated: []` never populated. As the archive grows, even a fixed RAG index returns noisier results. **preeng-contrast:** preeng tags artifacts Active/Review/Burn-pile.

**Strengths:** The infrastructure is *technically complete and runnable* (Ollama + LanceDB + working wrappers; correct memory-agent fallback spec). The single EPIC-001 retrospective is genuinely excellent. Schemas (learning entry, confidence/deprecation) are well-designed. These are good foundations awaiting operational wiring.

---

## 7. What `preeng` Specifically Exposes

The preeng skill is mostly a *planning-front-end* competitor, and it cleanly spotlights ACOS's weakest phase. The ideas worth harvesting (highest value first):

1. **Constitutional Domain Compilation + Competency Questions** → fixes 2.1, 2.4, 6.6. A measurable, domain-grounded gate before planning. *The single highest-value import.*
2. **Evidence tiers T1–T5** → fixes 2.2; cheap to add to both planning claims and evidence bundles.
3. **Diagnostic Protocol** → fixes 2.3; lightweight addition to the interview.
4. **Required `data-model.md` + `tech-prd.md`** → fixes 2.5, 2.11.
5. **7-part evidence bundle + per-slice Dev/QA learnings** → fixes 3.3, 2.10, 6.1.
6. **Hard QA-gate preconditions (step N+1 errors if step N rejected)** → reinforces 4.2.

What ACOS already does **better** than preeng (do not regress): mechanical enforcement via hooks (where wired), worktree-isolated parallel reviewers, multi-model consensus skills, full lifecycle beyond planning, real iteration caps with escalation. preeng "determinism" is prompt-discipline only — weaker than ACOS's tool-restriction model.

---

## 8. Recommended Remediation Order

**Phase 1 — Wiring (days, high impact, low risk):** register the 3 continuity hooks + `PreCompact` (1.1); add `quality-gates.yaml` for this repo (3.1); restore Oracle `hard_blocks` (1.4); fix the RAG index cron/refresh (6.2); wire agent identity into `agent-completions.log` (6.3); purge stale `auto-load-handoff.sh` refs (1.11); reconcile `CLAUDE.md` agent roster to the real 40 (5.1).

**Phase 2 — Close enforcement holes (weeks):** move Independence Wall + scope check to settings-level and cover Bash writes (1.2, 1.3, 3.4); add a mechanical verdict-aggregation gate (4.2); add mechanical `code_snippets` extraction + glob/word-boundary trigger matching (4.5, 4.6); make re-review blind (4.4).

**Phase 3 — Planning rigor (the preeng harvest):** domain-compilation/CQ gate, evidence tiers, diagnostics, data-model artifact, coverage check (2.1–2.6); 7-part evidence schema + per-slice learnings + learning *retrieval* at planning time (3.3, 2.10, 6.1).

**Phase 4 — Depth & coverage:** review-the-reviewers pass in the standard path (4.3); a11y/observability/license/cost reviewers (4.7); artifact lifecycle/bloat tiers (6.8); evaluate retiring or hardening the eternity keystroke system (1.9).

---

*Assessment generated 2026-06-04 via six grounded auditor agents + main-thread verification. Every Critical/High finding cites a real file; claims contradicting CLAUDE.md were independently re-checked. preeng source: `/Users/zee/Documents/OKOA/preeng-skill.zip` (extracted to `/tmp/preeng.VOdShl/`).*
