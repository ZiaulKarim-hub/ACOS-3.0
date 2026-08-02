# Overview

**Product:** ACOS Resurrection Protocol (project `005-resurrection-protocol`, within ACOS 3.0).

The Resurrection Protocol is a durable **per-project registry** ("the book"), a **safe-close ritual**
(`/acos-safe-close`), and a **menu-based resume** (`/acos-resurrect`) that together make cmux terminal
tabs disposable without losing working context. The book is one unified *view* rendered fresh on every
invocation over a sharded on-disk store (one JSON file per project); each row carries a **generated**
`next_action` headline (≤90 chars) — the single artifact no vendor ships. Closing a tab becomes a cheap,
verified, daily habit; reopening focuses the existing workspace (never duplicates it) or launches the
parked project at its own root with verified argv reentry delivery.

**Strategy (economics inversion):** the MENU is the way IN — immediate felt payoff on every open (it
repairs the lying tab bar with real titles and next-actions). Closing is the safe *byproduct*, never a
deferred-payoff tax. Membership is by **enrollment-on-first-sight** (marker-gated), never by closing and
never by naive scan; the close step only ENRICHES the reasoning that no scan can recover. Deliberate-with-
deferred-payoff is dead; deliberate-with-immediate-payoff (proven by 147 hand-run `/acos-complete`) survives.

**Ship gate:** DR-1 — one recorded close→resume round-trip on a real project with user-confirmed continuity,
receipts archived to `.acos/evidence/`. Until it exists, the skill is not shipped.

> Assumption: RAG index unavailable (venv missing); internal priors are drawn from swarm report
> `swarm-20260714-084532` and project memory. Marked T5 in the evidence ledger.

---

## Diagnostics
*(Problem-before-solution — §0.3. This section is referenced by the diagnostic slice EPIC-0 / Phase-0.)*

### Symptoms (what is going wrong)
- **S1 — Reasoning dies on force-quit.** Force-quitting cmux/Warp loses the working context with no way
  back to what was being worked on. Files, git tree, `memory/`, `planning/` survive; the *reasoning* dies.
- **S2 — Tabs accumulate because closing feels unsafe.** Measured 2026-07-14: 21 live sessions ≈ 7 real
  projects, 13/21 the same project; live again 2026-07-16 — cmux workspaces 4 and 5 both sit on ACOS 3.0.
  This is a **duplicate problem, not a switcher problem** (cmux does NO dedup).
- **S3 — Parked projects are invisible.** Not-open projects appear in no sidebar and no live-session
  listing; there is no index of them at all.
- **S4 — The durable handoff archive is a graveyard.** All 17 top-level `.resume.md` files lost their
  sibling handoff; ~10/17 show atime==mtime (written, never read); unnoticed for five weeks. The durable
  half of the current system is demonstrably unused.
- **S5 — The Mac slows/freezes under RAM-resident session pile-up.**

### Affected roles / personas
- **Solo operator (Zee)** — runs many concurrent Claude Code + cmux sessions across OKOA PE real-estate
  deal work and ACOS framework development on one macOS machine. The only persona; no multi-user surface.

### Current vs desired behavior
- **Current:** closing a tab is an unverified leap of faith; no index of parked work exists; the durable
  handoff loop has deferred payoff and is unused; opening a project from anywhere multiplies workspaces.
- **Desired:** closing prints a script-verified receipt read back from disk (`SAFE TO CLOSE THIS TAB` only
  on full pass); the book lists every active/parked project with a generated next-action; a pick FOCUSES an
  open project (constant workspace count) or launches a parked one at its own root; the whole thing is
  disjoint from and never contaminates Eternity.

### Hypotheses and unknowns
- **H1 (adoption):** the loop failed because payoff was deferred, not because it broke. Counter-evidence:
  147 hand-run `/acos-complete`. → Menu-first economics + DR-1 gate + audit-log measurement.
- **H2 (next_action quality):** highest-risk dependency — real next-step fields run 400–800 chars; the
  ≤90-char headline must be GENERATED at close, never truncated ("twelve options is zero options").
- **U1 (cmux 0.64.x behavior):** hibernation, auto-resume, `customDescription` restart survival,
  `workspace.select`/`workspace.close` against a live Claude session — all UNVERIFIED doc-claims, settled
  only by the Phase-0 probe battery + DP2 sacrificial tests.
- **U2 (147-run provenance):** hand vs hook — if hook-fired, adoption expectation drops ~30% → ~15%.
- **U3 (1-in-6 silent prompt drop):** cause unknown; mitigated by read-screen delivery verification + retry.

If diagnosis is incomplete, solution assumptions are marked `Assumption` and attached to the Phase-0
diagnostic slice; nothing ships past a green that was never verified.

---

## Users & Use Cases
- **Primary user:** Solo operator (Zee), macOS, subscription-only Claude ($200/mo Max).
- **UC1 — Enroll on first sight:** starting a Claude session in a marker directory (`.acos/` OR `CLAUDE.md`
  OR `memory/handoffs/`) creates a derived registry row automatically (O(1), fail-open, never blocks start).
- **UC2 — Safe close:** `/acos-safe-close` enriches the existing row with reasoning, verifies zero-loss by
  reading receipts back from disk, and closes the tab as the literal last act.
- **UC3 — Resume via the menu:** `/acos-resurrect` renders the book fresh; picking an OPEN project focuses
  its workspace; picking a PARKED project launches it at its own root with verified argv reentry.
- **UC4 — Finish for good:** a finish verb sets `status: completed`; the row is hidden in ARCHIVED, never
  deleted. `/acos-complete` is left untouched.
- **UC5 — Rebuild from disk:** `rebuild-registry.py` reconstructs the proven 16/16-row baseline reading no
  registry file (crash / accidental-delete recovery; also the DP5 day-one seeder).

---

## Requirements

### 4.1 Functional Requirements (MoSCoW)

**MUST**
- FR-M1 Per-project sharded JSON store `~/.acos/registry.d/<project_uuid>.json`; append-only audit
  `~/.acos/registry-audit.jsonl`. NEVER a shared mutable master, NEVER YAML/SQLite/cmux-state.
- FR-M2 Atomic write path: `mkstemp(dir=target's own dir)` → write → `fsync(tmp)` → `os.replace` →
  `fsync(dir)`; never a fixed `.tmp` name; one writer per file.
- FR-M3 Identity: `project_uuid` (uuid4) minted once at enrollment → `<root>/.acos/project-id` (git-ignored);
  lookup index `realpath(root).casefold()`; re-link key `(st_dev, st_ino)`. BANNED as identity:
  `sanitize(cwd)`, git remote, workspace UUID, session UUID, tab title.
- FR-M4 Enrollment-on-first-sight, marker-gated (`.acos/` | `CLAUDE.md` | `memory/handoffs/`); never naive
  scan, never close-time creation (DR-8). SessionStart hook is O(1), fail-open, additive user-level entry.
- FR-M5 `rebuild-registry.py` reproduces the 16/16 baseline from handoff artifacts across BOTH parents
  (Vibe Coding, OKOA) + `~/.claude.json` paths (lossy hint only); flags the Vibe Coding-root anomaly.
- FR-M6 `close-project.sh` implements steps 0–10 with four non-negotiable guards + last-workspace guard;
  close is the literal last statement, gated on the 7-check verification gate AND the read-back.
- FR-M7 `next_action` headline is GENERATED at close (imperative verb first, ≤90 chars), never truncated
  from the 400–800-char next-step field.
- FR-M8 Receipt honesty: every receipt line read back from disk; `listed N of M` with
  M == `git status --porcelain | wc -l`; `SAFE TO CLOSE THIS TAB` printed only by the script on full pass.
- FR-M9 Close target is the VALIDATED `CMUX_WORKSPACE_ID` (`grep -qx` against `rpc workspace.list`) — fail
  CLOSED; never fall back to `identify --surface` (fails open). Refuse auto-close if last workspace in window.
- FR-M10 Blind round-trip verifier (step 5): fresh general-purpose Task, handoff text ONLY, no repo/cwd;
  Wigum cap 5 then DEGRADE (never halt); no new `.claude/agents/` files.
- FR-M11 `resurrect-view.py` renders the book FRESH per request; liveness computed live (never a stored
  flag) via `lsof` PID→cwd + `ps` tty → `cmux tree --all --json`; workspace join via `[key:<uuid>]`
  description tag; tiers OPEN NOW / RECENT / COLD(>30d) / NO HANDOFF / ARCHIVED; dirty as a COUNT; BROKEN
  rows red, never hidden; NEVER a green badge.
- FR-M12 `launch-project.sh` focus-or-launch: same-root → newest `.reentry.md` re-resolved at open time
  inline; open elsewhere → `workspace.select` focus (never a second workspace); not open → new-workspace
  with argv reentry delivery + read-screen delivery verification + one retry + trust-gate detection +
  `[ -d "$CWD" ]` precheck. SPINE 1: workspace count stays constant on an open pick.
- FR-M13 Full Eternity disjointness: artifacts under `memory/handoffs/closed/<slug>/` (glob-invisible to
  Eternity), `.reentry.md` never `.resume.md`, single contact point `state/stop-<sid>` at close step 0.
- FR-M14 Phase-0 diagnostic slice: cmux 0.64.19 probe battery + DP2 sacrificial tests; fix residual #10
  (`eternity-resume-prepend.sh:158-169`), `head -40` (`eternity-protocol-core.sh:139` + bin twin + manifest),
  P1-F fail-open (`token-watcher.py:1113` + manifest); 147-run provenance.
- FR-M15 DR-1 ship gate: one recorded close→resume round-trip on a real project with user-confirmed
  continuity; recording/receipts to `.acos/evidence/`. Skill not shipped until it exists.

**SHOULD**
- FR-S1 Audit JSONL records `{ts, event∈(enroll|close|resume|finish|tombstone), project_uuid, details}`,
  one `os.write` per line — the sole adoption measurement (never a nagger).
- FR-S2 Tombstone-never-delete; deletion is a human act only; no age-based reaper.
- FR-S3 Registry writes the tab's own `--name`/`--description` (`<next_action> [key:<uuid>]`) on launch,
  repairing the tab bar.
- FR-S4 `realpath(cwd) == registry.root` assertion at SessionStart, logs loudly on mismatch (risk #7).
- FR-S5 One ~10-minute human curation pass after the DP5 seed; junk rows tombstoned by hand.

**COULD**
- FR-C1 (DP1-conditional, EPIC-5) optional browser surface `resurrection-server.py` at `127.0.0.1:8820`,
  skill-started never launchd, NO idle reaper, singleton via `/api/whoami`, opaque-ID launch,
  Origin+Host+Content-Type validation, `textContent` only, `open -a "Google Chrome"`, 5s visible-only poll.
- FR-C2 (DP4-conditional) opt into cmux Agent Hibernation only after the in-pane-hook firing test passes
  on a hibernated-then-resumed throwaway.
- FR-C3 (0.8, optional) harden `archive-project.sh:199` `-delete` behind an explicit `--yes` flag.

**WON'T (this release — the DO NOT BUILD list)**
- Registry rows created by closing; a green "verified resumable" badge; any hand-maintained/typed field; a
  notifier/nagger; a second handoff/resume writer touching the daemon state dir; cmux-state-backed registry;
  recency-as-selector; auto-stash at close; naive filesystem-scan membership; idle reaper / port-hopping /
  launchd hosting / `ACAO:*` / `innerHTML` on the optional server; auto-close at a token threshold; AI
  auto-naming enabled (DP3 OFF).

### 4.2 APIs, Data & States

**Data entities** (full schema in `data-model.md`):
- Project registry row (`~/.acos/registry.d/<project_uuid>.json`).
- Audit event (append-only `~/.acos/registry-audit.jsonl`).
- `project-id` file (`<root>/.acos/project-id`, git-ignored uuid4).
- Close handoff (`memory/handoffs/closed/<slug>/handoff.yaml`, `type: close-project`, `status: parked`).
- Reentry doc (`memory/handoffs/closed/<slug>/<slug>.reentry.md` — never `.resume.md`).
- cmux workspace description tag (`<next_action> [key:<uuid>]`, tag at END, ~45-char overhead).
- Daemon stop marker (`state/stop-<SESSION_ID>` — the ONLY permitted daemon-state write, at close step 0).

**Interfaces (all binaries called ABSOLUTELY):**
- `/Applications/cmux.app/Contents/Resources/bin/cmux` — prefer `rpc workspace.list` (never parse text form);
  `rpc workspace.select` (focus); `rpc workspace.close '{"workspace_id":"<validated>"}'`; `new-workspace
  --name --description --cwd --command`; `read-screen`; `tree --all --json`.
- `/Users/zee/.claude/local/claude` — `--resume`, `--session-id`, `--fork-session`, `-n/--name`,
  `--no-session-persistence`, `project purge`.
- Both names are shadowed on PATH (broken `_acos_cli` at `~/.zshrc:215` + a cmux shim) — absolute paths only.

**State machine (project status):** `active` ⇄ `parked` (park on close, `parked → active` on resume) →
`completed` (finish verb; hidden in ARCHIVED) ; any → `tombstoned` (human curation only). Rows are
tombstoned, never deleted.

### 4.3 Non-Functional Requirements (NFRs)
- NFR-Durability: crash/second-writer never leaves a valid-but-silently-wrong record; atomicity proven by a
  6×60 contention crash-test → 0 errors, 0 torn (mirrors 180/360 → 0). Truncated JSON fails LOUDLY.
- NFR-Portability: stdlib-only Python targeting system `/usr/bin/python3` 3.9.6 (no `yaml`; no
  `timeout`/`gtimeout`); JSON everywhere; Bash for glue.
- NFR-Isolation: zero writes to the daemon state dir except `state/stop-<sid>`; `pending-resume-*.txt` /
  `RESCUED-resume-*.txt` never touched; top-level `memory/handoffs/*.{md,yaml}` never written.
- NFR-Observability: append-only audit JSONL + Phase-0 evidence bundles + DR-1 recording under
  `.acos/evidence/`; ACOS agent identity logged to `.acos/metrics/agent-completions.log`.
- NFR-Honesty: facts not verdicts; red/amber only; no green anything; silence means fine; a single false
  green costs permanent trust in the whole registry.
- NFR-Performance: enrollment O(1) never blocks session start; book render is fresh-per-request over sharded
  files (row ~few KB; 1,000 closed ≈ 10 MB — no reaping argument).
- NFR-Security: no registry-derived string enters `--command` (only the skill-controlled reentry file PATH);
  names/next_action go in `--name`/`--description` via list-form subprocess (XSS-not-shell surface).
- NFR-Version-control: all new code lives in the ACOS 3.0 repo where it executes (highest-severity doc-drift
  lesson: a repo-only edit to a script whose live twin lives elsewhere is a silent no-op).

---

## Prioritization & Scope Cut
Priority order (build sequence): **EPIC-0 Phase-0 prerequisites FIRST** (non-negotiable — fix residual #10
BEFORE the registry makes two-panes-one-project routine; fix `head -40`; close P1-F; run the cmux probe
battery + DP2; check 147-run provenance) → **EPIC-1 Registry core** → **EPIC-2 Safe close** → **EPIC-3 The
menu** → **EPIC-4 DR-1 ship gate** → **EPIC-5 optional browser (only if DP1 selects it)**.

**Cut from v1 (search-fodder or disqualified):** git branch column, last-action column, health score, static
description; keep-alive daemons; per-session rows; title-based matching; auto-close at a token threshold.
Nothing ships until Demo 3 (DR-1); a placebo close is a higher-risk product than none.

---

## Metrics & Analytics
*(Formulas defined here; not computed — §0.5. Instrumentation → `.acos/metrics/agent-completions.log`
and `~/.acos/registry-audit.jsonl`; see AGENT-METRICS scaffolding in `plan.md`.)*
- **Production:** Story Points Delivered (SPD, qualitative); Quality-Adjusted Productivity
  `QAP = (Delivered_Value * Quality_Score) / (1 + Rejection_Count)`.
- **Efficiency:** Token Efficiency Ratio (TER) = artifacts per 1K tokens; artifact-volume per unit cost.
- **Universal Agent Performance Score:** `UAPS = 0.3*Quality + 0.4*Efficiency + 0.3*CostEffectiveness`.
- **Product success:** DR-1 achieved (bool); rebuild reproduces ≥16/16; daemon-writes == 1 (only stop-marker);
  workspace-count-constant on open pick; `listed N of M` == `git status --porcelain | wc -l`; adoption =
  menu used ≥1×/week at day 60 (baseline ~30%), from audit JSONL.

---

## UX & Content
- Terminal-first menu (DP1=A). Row = project name + generated `next_action` (≤90 chars, imperative verb
  first) + facts (dirty COUNT, amber staleness, clickable `file://` handoff link). No verdicts, no green.
- Tiers, top to bottom: **OPEN NOW / RECENT / COLD(>30d) / NO HANDOFF / ARCHIVED** (last three collapsible).
- BROKEN rows render red, never hidden. Silence means fine.
- The launch side repairs the tab bar: the tab stops saying `⠐ Claude Code` and starts saying the actual
  next action (registry writes `--name`/`--description`).
- Receipt is script-printed, plain text, every line a verified read-back; ends with `SAFE TO CLOSE THIS TAB`
  only on full pass, else the tab stays open (the failure signal).

---

## Rollout Plan
Vertical slices; each a working demo-able increment producing an evidence bundle.

- **Demo 1 — Enrollment.** A new session in a marker dir yields a derived row; `rebuild-registry.py`
  reproduces 16/16; ACOS 3.0's two live workspaces (4 and 5) render as ONE row.
- **Demo 2 — Safe close on a THROWAWAY.** Receipt says SAFE only on full pass; the tab closes as the literal
  last act; artifacts co-located under `closed/<slug>/` and glob-invisible to Eternity.
- **Demo 3 — DR-1 (the ship gate).** Full close→resume round-trip on a real project with user-confirmed
  continuity; recording archived to `.acos/evidence/`. **Ship is gated on Demo 3.**

---

## Risks & Mitigations
- **R1 Adoption decay (~30% at day 60; decay mode = "stopped closing").** → Menu-first economics; DR-1 gate;
  audit-log measurement; Phase 0.6 checks 147-run provenance (hook-fired → ~15%).
- **R2 `next_action` generation quality (highest-risk dependency).** → Generated at close, never truncated;
  imperative verb first; blind round-trip must quote the reconstructed next step.
- **R3 cmux 0.64.x behavior UNVERIFIED.** → Phase-0 probe battery + DP2 sacrificial tests before close ships.
- **R4 Eternity cross-contamination (2026-06-26 class).** → `realpath(cwd)==registry.root` assertion at
  SessionStart; disjoint namespaces; only `state/stop-<sid>` contact.
- **R5 In-pane hook regression on cmux upgrade (#5427 class).** → Verify hook firing on 0.64.19 first.
- **R6 Confidentiality — auto-naming endpoint undocumented.** → DP3 OFF; registry writes titles anyway.
- **R7 Silent failure is the base rate (ALL-GREEN doctor over 2,000+ failures; `head -40` hiding 34/74).** →
  Verified reads; model never composes receipts; red/amber only; no green.
- **R8 Duplicate launch → cross-pane resume contamination (residual #10).** → Fix
  `eternity-resume-prepend.sh:158-169` FIRST; focus-not-launch.
- **R9 Trust death — one silent loss ends the tool permanently.** → DR-1 demonstration, not a promise.

---

## Dependencies & Stakeholders
- **Stakeholder:** Zee (sole operator, decision-maker, DR-1 confirmer).
- cmux 0.64.19 (present; behavior UNVERIFIED — Phase-0). Claude Code 2.1.212 (flags re-verified).
- Native persistence: 643 non-subagent transcripts / 1.2 GB; `~/.claude.json` 42 rows / 32 lastSessionId.
- Enrollment ground truth: 18 `memory/handoffs` dirs across TWO parents.
- Daemon state dir: 963 entries; off-limits except the stop marker.
- Reused (not rebuilt): handoff-agent + existing semantic handoff content model; Eternity Protocol
  (unchanged except the two prerequisite Phase-0 fixes).
- Phase-0 script fixes: `eternity-resume-prepend.sh` 158-169; `eternity-protocol-core.sh:139` (+ bin twin +
  manifest); `token-watcher.py:1113` (+ manifest).

---

## Open Questions
- **DP1 menu surface** — default A (terminal-first; browser optional Phase 5). *Assumption.*
- **DP2 sacrificial cmux tests** — default A (full battery + one scheduled restart before close ships). *Assumption.*
- **DP3 AI auto-naming** — default OFF (never enable before endpoint identified). *Assumption.*
- **DP4 hibernation** — default A (opt in only after hook-firing test passes). *Assumption.*
- **DP5 seeding** — default A (scanner seed + one ~10-min curation pass). *Assumption.*
- **U1** cmux `workspace.close` against a live Claude session — prompt or instant kill? (Phase-0 DP2c)
- **U2** 147-run provenance — hand vs hook? (Phase 0.6)
- **U3** 1-in-6 silent prompt drop — cause unknown; mitigated by delivery verification + retry.
- **U4** `customDescription` survival across cmux restart (the `[key:uuid]` join depends on it).
- **U5** last-workspace close — closes window or quits cmux? (Phase-0 DP2b)

---

## Appendix
- **SPINE rules 1–7 (binding):** (1) focus-not-launch; (2) derived/generated only; (3) verified reads
  (facts not verdicts, red/amber only, no green); (4) load-bearing logic in scripts not prose; (5) cmux is
  UI never the database; (6) never select by recency; (7) never write the daemon state dir (one exception:
  `state/stop-<sid>`).
- **Three-agent LCE pattern:** PM (architect) / Dev (developer) / QA (reviewers), zero-trust verification.
- **Namespace boundary:** Resurrection is pane-INDEPENDENT (cross-window, days-later park+resume); Eternity
  is pane-DURABLE (same-pane continuation, per-PID pointer). Opposite invariants, not a config difference.
- **Source corpus:** `_preseed/` (product-context, design, build-plan, vision-deltas, decision-points,
  digests) + swarm report `swarm-20260714-084532`.

---

## PRD Summary (One-Page Digest)
Resurrection Protocol makes closing a cmux tab a cheap, verified daily habit and gives parked projects a
home. **The book** = one fresh-rendered view over a sharded per-project JSON store; each row carries a
GENERATED ≤90-char `next_action`. **Membership** = enrollment-on-first-sight (marker-gated), rebuildable
from disk (16/16 proven) — never created by closing (survives force-quit, DR-8). **Safe close** = a thin
router over `close-project.sh` (steps 0–10) that enriches the row, verifies zero-loss by reading receipts
back from disk, and closes the tab as the literal last act (fail CLOSED on an unvalidated workspace id).
**Resume** = a menu that focuses an open project (never duplicates — SPINE 1) or launches a parked one at
its own root with verified argv reentry. **Identity** = uuid4 minted once; lookup `realpath.casefold`;
re-link `(st_dev,st_ino)`; `sanitize(cwd)`/remote/workspace-UUID/session-UUID/title all BANNED. **Isolation**
= fully disjoint from Eternity; only contact `state/stop-<sid>`. **Honesty** = facts not verdicts, no green
badge ever; a single false green is permanent trust death. **Ship gate** = DR-1: one recorded, user-confirmed
close→resume round-trip. Highest risks: `next_action` generation quality and adoption decay; both answered by
generate-not-truncate + menu-first economics + the DR-1 demonstration.
