# Product Context — 005-resurrection-protocol
Prepared 2026-07-16 by /acos-preeng-classic Step 1, from: the user's confirmed 5-point vision
(2026-07-16), swarm research report `swarm-20260714-084532` (12 agents, 6 sub-questions), a
5-agent digest+synthesis workflow run 2026-07-16 (files in this directory), and a live machine
inventory of 2026-07-16. RAG pre-seed was attempted and unavailable (venv missing) — internal
priors below come from the swarm report and project memory instead (Assumption noted).

## 1. Product / Feature Name
**ACOS Resurrection Protocol** — a durable project registry ("the book"), a safe-close ritual,
and a menu-based resume system that makes cmux terminal tabs disposable.

## 2. Business Objectives
- Make closing a project tab feel (and be) safe: verified zero-loss capture, so closing becomes
  a cheap daily habit and tabs stop accumulating.
- Maintain one trustworthy index ("the book") of every active project, each row carrying a
  generated `next_action` headline (≤90 chars) — the one artifact no vendor ships.
- Kill the duplicate-workspace pile-up at its source: selecting an open project FOCUSES the
  existing workspace, never launches a second (SPINE 1).
- Survive force-quits: the registry and resume path must never depend on a clean close (DR-8).
- Coexist with, and never contaminate, the Eternity Protocol continuation system.

## 3. User Problems (ranked)
1. Force-quitting cmux/Warp loses working context with no way back to what was being worked on.
2. Tabs accumulate because closing feels unsafe (measured 2026-07-14: 21 live sessions ≈ 7 real
   projects, 13/21 the same project; live again 2026-07-16: cmux workspaces 4 and 5 both sit on
   ACOS 3.0).
3. Parked (not-open) projects appear in no sidebar and no live-session listing — there is no
   index of them at all.
4. The existing durable handoff archive is a graveyard: all 17 top-level `.resume.md` files have
   lost their sibling handoff; ~10/17 show atime==mtime (written, never read); unnoticed for
   five weeks. The durable half of the current system is demonstrably unused.
5. The Mac slows/freezes under RAM-resident session pile-up.

## 4. Success Metrics
- **DR-1 ship gate:** one full recorded close→resume round-trip on a real project with
  user-confirmed continuity, receipts archived to `.acos/evidence/`. Until it exists, the skill
  is not shipped.
- Registry rebuildable from disk alone: `rebuild-registry.py` reproduces at least the proven
  16/16-row baseline from handoff artifacts, reading no registry file.
- Zero writes to the daemon state dir (`~/Library/Application Support/acos-token-monitor/state/`)
  except the single documented `state/stop-<SESSION_ID>` marker at close step 0;
  `pending-resume-*.txt` / `RESCUED-resume-*.txt` never deleted, moved, or rewritten.
- Focus-never-launch acceptance test: picking an already-open project changes focus and the
  workspace count stays constant.
- Receipt honesty: every safe-close receipt line is read back from disk; every list prints
  `listed N of M` with M == `git status --porcelain | wc -l`; `SAFE TO CLOSE THIS TAB` is
  printed only by the script on full pass.
- Adoption: menu used ≥1×/week at day 60 (report baseline expectation ~30%), measured from the
  append-only audit JSONL (close/resume events), never by a nagger.

## 5. Constraints (technical / policy)
- macOS, APFS case-insensitive; system `/usr/bin/python3` is 3.9.6 with **no yaml module**;
  no `timeout(1)`/`gtimeout` on PATH.
- **Storage:** one JSON file per project at `~/.acos/registry.d/<project_uuid>.json`; append-only
  `~/.acos/registry-audit.jsonl`. Atomic write path: `mkstemp` in target's own dir → `fsync(tmp)`
  → `os.replace` → `fsync(dir)`. Never a shared mutable master file (measured: 3/25 unlocked
  concurrent writes survive while remaining VALID JSON — silently wrong), never YAML (truncated
  YAML parses silently: 19/30 records), never SQLite (opaque to git diff/hand-repair), never cmux
  workspace state (closing a workspace deletes its record; closing is the whole point).
- **Identity:** `project_uuid` = uuid4 minted once at enrollment, stored at
  `<root>/.acos/project-id` (git-ignored); lookup index `realpath(root).casefold()`; re-link key
  `(st_dev, st_ino)`. BANNED as identity: `sanitize(cwd)` (proven non-injective), git remote,
  cmux workspace UUID (reopen mints a new one), session UUID, tab title (Claude rewrites titles;
  a sampled title was a spinner frame). Git branch/commit/dirty-count are captured attributes,
  never identity.
- **SPINE rules 1–7 are binding** (see `digest-read-spine-conflicts.md`): focus-not-launch;
  every field derived/generated, none hand-maintained; assume silent failure is the base rate —
  fail loudly, show facts never verdicts (red/amber only, no green badges); load-bearing logic
  lives in scripts, not prose (measured: script-implemented logic ran 8/8; prose-specified 8/18);
  cmux is UI, never the database; never select artifacts by recency (`ls -t | head -1` is not a
  selector — re-resolve at open time); never write the daemon state dir.
- **DO NOT BUILD list:** registry rows created by closing; a green "verified resumable" badge;
  any hand-maintained field; a notifier/nagger; a second handoff/resume writer touching the
  daemon state dir; cmux-state-backed registry.
- All scripts call binaries absolutely: `/Users/zee/.claude/local/claude` and
  `/Applications/cmux.app/Contents/Resources/bin/cmux` (both names are shadowed on PATH: a broken
  `_acos_cli` zsh function at `~/.zshrc:215` and a cmux CLI shim).
- Task() subagents are policy-blocked from the Write tool — agent-executed file writes use Bash.
- Never modify: `review-rules/` (standing rule), `.claude/agents/` (no new agent files — the
  round-trip verifier uses a general-purpose Task), top-level `memory/handoffs/*.{md,yaml}` and
  `memory/handoffs/archive/` (Eternity's live namespace — two fresh 2026-07-16 emergency
  handoffs sit there right now). New close artifacts live under `memory/handoffs/closed/<slug>/`
  where Eternity's glob cannot see them.
- Subscription-only Claude ($200/mo Max) — never suggest or require ANTHROPIC_API_KEY.
- User ritual economics: 147 hand-run `/acos-complete` invocations prove deliberate rituals
  survive when payoff is immediate; deliberate-with-deferred-payoff is dead. The menu is the
  way IN; closing is the safe byproduct.

## 6. Dependencies
- cmux 0.64.19 installed (report's "upgrade first" prerequisite is MOOT). CLI + Unix-socket RPC,
  ~230 methods today incl. `workspace.select`, `surface.resume.get/set/clear`,
  `session.restore_previous`, `workspace.env`, `surface.health` — presence verified 2026-07-16,
  **behavior UNVERIFIED** (Phase-0 probe battery required). `cmux list-workspaces` is now a
  legacy alias of `cmux workspace list`; `workspace list --json` returns real JSON on 0.64.19;
  prefer `rpc workspace.list`, never parse the text form.
- Claude Code 2.1.212; flags re-verified present today: `--resume`, `--continue`, `--session-id`,
  `--fork-session`, `-n/--name`, `--no-session-persistence`; `claude project purge` exists.
- Native persistence (the adopt-side anchor): 643 non-subagent transcripts / 1.2 GB;
  `~/.claude.json` `projects{}` 42 rows, 32 with `lastSessionId` (lossy path-mangled keys —
  hint only, glob-disambiguation required, never a decoder).
- Enrollment ground truth: 18 `memory/handoffs` dirs across TWO parents (17 under
  `~/Documents/Vibe Coding/` incl. one anomalous row on the parent folder itself; 1 under
  `~/Documents/OKOA/`) — enrollment cannot be scoped to one parent.
- Daemon state dir: 963 entries today; session-UUID-keyed; off-limits (read-only, except the
  documented stop marker).
- Phase-0 fixes to existing scripts (pre-build prerequisites): `eternity-resume-prepend.sh`
  lines 158–169 pane-blind tier-3 resume; `eternity-protocol-core.sh:139` `head -40` silent
  truncation (repo copy + byte-identical Application Support bin twin + bin-manifest regen);
  `token-watcher.py:1113` fail-open orphan-surface branch.

## 7. Known Risks
- **Adoption decay** — ~30% odds of routine use at day 60 (report agent 12, unsoftened); decay
  mode is "stopped closing", not "it broke". Mitigations: menu-first economics, DR-1 gate,
  audit-log measurement. Phase 0 must also check provenance of the 147 `/acos-complete` runs
  (hand vs hook) — if hook-fired, expectation drops ~30%→~15%.
- **`next_action` generation quality** — the single highest-risk design dependency: real
  next-step fields run 400–800 chars; the ≤90-char headline must be GENERATED at close, never
  truncated (truncation yields noise).
- **cmux 0.64.x doc-claims** — hibernation, auto-resume, `customDescription` restart survival:
  all UNVERIFIED; sacrificial tests cost a throwaway session + one controlled restart (DP2/DP4).
- **Eternity cross-contamination** — documented 2026-06-26 incident class; registry-root vs cwd
  assertion (`realpath(cwd) == registry.root`, loud on mismatch) required at SessionStart
  (risk #7 — protects the f639310 project-scoping fix).
- **In-pane hook regression on cmux upgrades** (#5427 class) — the in-pane hook is the live
  resume carrier; verify hook firing on 0.64.19 before anything ships.
- **Confidentiality** — `automation.autoNamingAgent: "auto"` endpoint/model undocumented; cmux
  tabs carry OKOA deal content; keep auto-naming OFF (DP3).
- **Silent failure is this machine's base rate** — 10+ documented instances (ALL-GREEN doctor
  over 2,000+ failures; `head -40` hiding 34 of 74 files inside an "inspect FIRST" block —
  confirmed live today). Receipts are verified reads; the model never composes them.

## 8. Existing docs / research / related work (local reads permitted for detail)
- `planning/preeng/005-resurrection-protocol/_preseed/design.md` — reconciled design v1 (vision
  point → concrete mechanism; today-wins corrections).
- `_preseed/build-plan.md` — ordered phases 0–5 with per-step verification.
- `_preseed/vision-deltas.md` — 8 deltas D1–D8: vision said / report says / resolution.
- `_preseed/decision-points.json` — DP1–DP5 user decisions (defaults adopted as Assumptions, below).
- `_preseed/digest-read-spine-conflicts.md`, `_preseed/digest-read-recommended-design.md`,
  `_preseed/digest-read-risks-prereqs.md`, `_preseed/digest-inventory-live-machine.md`.
- Source report: `.acos/swarm/swarm-20260714-084532/synthesis/report.md` (1,535 lines) + `plan.md`
  (constraints C1–C6) + `agent-03/findings.md` (the exact 7-check close verification gate list).

## Pre-seeded research (T-tagged)
- T3 (empirical, this machine): concurrency measurements (3/25 unlocked survival; mkstemp 0/360
  torn), 16/16 registry rebuild, graveyard forensics (17/17 dangling; 63/64 hot-path reads,
  median 190 s), duplicate census (21 sessions ≈ 7 projects), verified cmux CLI battery results,
  2026-07-16 live inventory (cmux 0.64.19, Claude 2.1.212, 643 transcripts/1.2 GB, 963 daemon
  entries, 18 handoff dirs).
- T4 (vendor docs, UNVERIFIED on this machine): cmux Agent Hibernation,
  `terminal.autoResumeAgentSessions`, `automation.workspaceAutoNaming`, `customDescription`
  restart survival, `sidebar.showWorkspaceDescription`.
- T5 (internal priors): Eternity Protocol incident history (2026-06-26 cross-pane contamination;
  f639310 project-scoping fix; self-expiring dead-surface marker lesson 2026-07-13), ACOS memory
  feedback rules (preserve pending-resumes; subagent Write block; absolute binary paths).
- Assumption: RAG index unavailable (venv missing) — internal priors drawn from the swarm report
  and project memory files instead.

## Decision-point defaults adopted for planning (each is an Assumption to surface)
- DP1 menu surface → **A**: in-Claude terminal menu first; browser dashboard is optional Phase 5.
- DP2 sacrificial cmux tests → **A** (sequenced): full battery on throwaway workspaces + one
  user-scheduled controlled cmux restart, before the close skill ships.
- DP3 AI auto-naming → **OFF** (A/B): never enable before the endpoint is identified; registry
  writes titles anyway.
- DP4 hibernation → **A**: opt in only after the in-pane-hook firing test passes on a
  hibernated-then-resumed throwaway.
- DP5 seeding → **A**: seed via scanner day one; one ~10-minute human curation pass; junk rows
  tombstoned by hand.
