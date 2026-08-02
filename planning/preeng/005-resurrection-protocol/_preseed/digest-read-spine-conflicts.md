# Extraction: report.md lines 119–733 (Cross-Agent Convergence SPINE 1–7 + Conflicts C1–C8)
Source: `/Users/zee/Documents/Vibe Coding/ACOS 3.0/.acos/swarm/swarm-20260714-084532/synthesis/report.md`
All findings machine-verified unless flagged **[DOC-CLAIMED]** or otherwise noted.

---

## SPINE RULES (blind cross-agent convergence, highest confidence)

### SPINE 1 — One project has N tabs; row must be per-PROJECT and click must FOCUS, not launch
- Strongest convergence in the swarm (6 agents, 4 sub-questions, 5 lenses); NOT on the brief's list.
- Evidence:
  - Agent 03 (SQ2 TechFeas): `workspace.list` showed **three workspaces sharing one `current_directory`**; "mapping is project 1..N workspaces."
  - Agent 05 (SQ3 TechFeas): **cmux does NO dedup** — ran `cmux "<ACOS 3.0 path>"` while already open in 4 workspaces → `OK workspace:10`, a 5th. "The bare form is a *creator*, not an *opener*."
  - Agent 06 (SQ3 Integration): focus-not-duplicate is "not a UX preference, it is a correctness requirement" — two panes on one project makes the last-resort tier hand pane A's resume to pane B.
  - Agent 08 (SQ4 Risk, N1): "The design converts a rare precondition into the default workflow." 2026-06-26 incident reproduced on the happy path.
  - Agent 09 (SQ5 TechFeas): three workspaces all `current_directory = ACOS 3.0`; "`open` is a **count**, not a boolean."
  - Agent 10 (SQ5 UserImpact): **21 live sessions = ~7 real projects; 13 were ACOS 3.0 alone.** On disk: **508 recorded sessions for ACOS 3.0, 131 for FruitSync.**
- Agent 12: "This is a **duplicate problem, not a switcher problem.**"
- **REQUIRES:** clicking a row FOCUSES the existing workspace for that project. One row per project (see also C8 end: 21 sessions → ~7 rows; 508 ACOS sessions → 1 row).
- **FORBIDS:** a switcher that launches (creates new workspaces); per-session rows.

### SPINE 2 — No field may be hand-maintained; registry is DERIVED, never a stored pointer
- 5 agents, 4 sub-questions, 5 lenses, 4 independent evidence types. Brief asked verification → **real**, with a caveat.
- Evidence:
  - Agent 01 (Finding 8): registry is "a rebuildable index, not the sole source of truth"; lost registry = inconvenience.
  - Agent 02 (Finding 6): **wrote and ran a ~40-line rebuild that reconstructed 16 project rows from handoff artifacts alone, reading no registry file** (proof, not assertion).
  - Agent 04 (Finding 2): **measured 55% dangling pointers (10/18)**. "A derived index cannot dangle." This choice *deletes* risks #2, #5, #6 rather than mitigating them.
  - Agent 10: hand-maintained field → chore → skipped → stale → "a stale registry is a *lying* registry." Named **the load-bearing constraint of the entire design.**
  - Agent 11 (census): `lastSessionFirstPrompt` populated **3 of 42** Claude projects; `customDescription` on **2 of 6** cmux workspaces — one of those written by another swarm agent that day. "Humans do not fill in description fields. Never prompt."
- **CAVEAT (live conflict inside the convergence, adjudicated in C8):** "derived from disk" conflates two claims:
  - "No field is hand-typed" — genuinely unanimous (01, 02, 04, 10, 11). This is the spine.
  - "Membership is discovered by scanning" — **contested.** Agent 12 (DR-2) wants seeding from cmux workspaces + Claude Code's 781 transcripts. Agent 01 (Finding 4): a naive scan enrolls framework-support strays `memory/`, `planning/`, `learning-curve/` — "the registry must be **explicit-enrollment**, never filesystem-scan-derived." Agent 10 (Finding 8): `~/.claude/projects/` is polluted with scratchpads/skill subdirs and *still misses real work* (Font-Forge work landed in the global skill dir) — "auto-scraped registry would be full of garbage rows and would still miss real work."
- **REQUIRES:** every registry field derived/generated; ship rebuild path; enrollment resolved per C8.
- **FORBIDS:** any hand-typed field; prompting the user to fill in descriptions; stored pointers as the source of truth.

### SPINE 3 — Silent failure is this machine's base rate
- 10+ independent instances across 6 agents (stronger than brief claimed):
  - 04: `eternity-doctor` reported **ALL-GREEN** through `rc=2 x1391, rc=1 x718, rc=5 x78, rc=3 x39` with only ~6 successful FIRED. **16 of 17 audited failure rows marked `Silent? Yes`.**
  - 04: `head -40` silently truncates — resume says `uncommitted changes: 74 file(s)` but lists exactly 40, no ellipsis; **34 files invisible** inside the block headed "these are in NO handoff — inspect FIRST".
  - 02: truncated **YAML parses successfully and silently returns 19 of 30 records**, no error.
  - 01: **3 of 25** concurrent writes survive without the lock — *while still producing valid JSON* (atomic rename keeps file VALID and silently WRONG).
  - 05: **1 of 6** launch trials silently dropped the resume prompt; cause unknown; leading hypothesis tested and **disproved**.
  - 05: `new-workspace --cwd /does/not/exist` returns **exit 0**, launches in wrong dir. Bare `cmux <path>` form validates; the flag form does not.
  - 05: `--id-format both` placed after the command = **silent no-op**.
  - 06: `cmux identify --surface X` **fails open** — valid surface, bogus UUID, and known-dead surface all return exit 0 with byte-identical output.
  - 08: pane gate **still half fail-open in live code** (`token-watcher.py:1113`), dormant only because one 90-byte marker file exists.
  - 09: `cmux list-workspaces --json` / `--format json` — **flag silently ignored**, text printed.
  - 12: **100% dangling-sibling rate went unnoticed for five weeks.**
- **REQUIRES (agent 04's design consequence, endorsed):** every line of any receipt must be **read back from disk after writing**. Never report an intention. (`eternity-doctor` was green because it checked it had *tried*, not that it had *worked*.)
- **FORBIDS:** intention-based receipts; trusting exit codes / valid-parse as success.

### SPINE 4 — Prose doesn't execute; only code does
- Agent 04 owns the measurement (genuine controlled natural experiment: same author, same repo, same period, one variable):
  - Git-state capture implemented as a **shell script** (`eternity-protocol-core.sh:132`): **8/8 = 100%** adoption.
  - Pointer-rewrite-on-archive specified as **prose + a snippet** in `acos-complete/SKILL.md:108`: **8/18 = 44%**. Ten pointers dangle now. "The rewrite logic is *correct*... **It failed because nobody ran it.**"
- Corroboration: doc-drift fingerprint from agents 05, 06, 07, 12 (Documentation Drift section, outside extracted range).
- Note: report is precise that the brief credited this MORE broadly than evidence supports — only 04 measured it; others corroborate the fingerprint.
- **REQUIRES:** close skill's SKILL.md must be a **thin router over `close-project.sh`**; the receipt must be printed **by the script from verified return values**.
- **FORBIDS:** model-composed receipts ("If the model composes the receipt, the receipt is fiction"); safety-critical logic specified as skill prose.

### SPINE 5 — cmux cannot be the registry substrate
- Agent 01 (local experiment): created throwaway workspace, confirmed flush to disk, closed it, record vanished — `GONE: closed workspace removed from session file`. Searched all **154 RPC methods**: no `list-closed-workspaces`, no undo-close store, no "recent projects". Substrate is "**structurally incapable** of holding the state."
- Agent 11 (upstream issue tracker) **[DOC-CLAIMED, issue-tracker sourced]**: cmux session persistence chronically fragile — #2387 restore regression **still open** ("critical for daily use"), #2895 snapshot silently overwritten with partial state, #2125 all workspaces reopened at `$HOME`. "**Treat cmux as the convenient UI, never the database.**"
- **FORBIDS:** storing registry state in cmux (workspaces, descriptions-as-store, session files).
- **REQUIRES:** independent on-disk store; cmux used as UI only.

### SPINE 6 — Never select by recency; `ls -t | head -1` is not a selector
- Agents 06, 08, 04 converge. Agent 06 found the mechanism: `eternity-protocol-core.sh:87` globs `ls -t memory/handoffs/*.{md,yaml}`, newest-wins, unscoped, non-recursive. Agent 08's structural invariant: "`ls -t` may only order candidates that have *already passed* an exact identity match." Agent 04 (loss lens): "Never fall back to 'newest in dir'."
- **REQUIRES:** exact identity match FIRST; recency only as tiebreaker among already-matched candidates.
- **FORBIDS:** newest-in-directory as a selection mechanism.

### SPINE 7 — Never write to the daemon state dir
- Agents 06, 07, 08 converge across two sub-questions. Agent 08 namespace verdict: every key in that **871–1498-file** directory is a **session UUID**; **not one carries a project identifier**. "A namespace with no project dimension cannot be safely shared by a project-oriented tool."
- **EXACTLY ONE write permitted** (all three agents name the same one): `state/stop-<sid>` — the documented Eternity opt-out marker, so Eternity cannot fire mid-close.
- **FORBIDS:** any other write to the daemon state dir.

---

## CONFLICTS & ADJUDICATION (C1–C8)

### C1 — Storage substrate: BOTH headlines lose; verdict = per-project sharded JSON
- **Conflict:** Agent 01: single JSON `~/.acos/registry.json` + `fcntl.flock` + atomic tmp→fsync→replace. vs Agent 02: SQLite WAL + `busy_timeout=5000` + `BEGIN IMMEDIATE` + UPSERT.
- **Both verified their own arm:** 01: 25/25 records with lock, 3/25 without (still valid JSON — valid-but-silently-wrong is the worst index failure mode). 02: 6 writers × 80 UPSERTs = **480/480 commits, 0 SQLITE_BUSY, 0 lost**; at `busy_timeout=0`: **140 BUSY but still LOST=0** (clean retryable rejection, never silent corruption).
- **Tiebreaker: agent 02's premise is FALSE.** 02's case rests on risk R1 ("Mass-close write storm: user force-closes all tabs → N close-skills write at once", rated High/Catastrophic). But a force-quit means **no close skill runs at all** (agent 12 DR-8: "`kill -9` every cmux tab... Nothing is missing that a graceful close would have provided"). The storm scenario has **zero writers**. Agent 02 itself flagged in Data Gaps: "Contention rate unmeasured." Real write rate (per 01): one tab at a time, a handful/day, across ~23–50 projects. "Agent 02 optimised the wrong axis with excellent evidence."
- **Why not 01's single JSON:** the lock is *advisory*, load-bearing, cooperative-only. 01 concedes in What-Would-Change-My-Mind ("Writers stop being cooperative... Then move to per-project files"). Agent 08 (N7) independently: "one file *per project*, never one shared file." Agent 02 measured a live house-helper bug: fixed tmp filename staging (`resolve-session-pid.py:61`, same shape at five sites in `token-watcher.py`) → under 6-way contention **180 crashes in 360 attempts**; unique `mkstemp` → **0**.
- **VERDICT:** `~/.acos/registry.d/<project_uuid>.json` — one file per project, one writer per file.
  - Dissolves the question: no shared mutable file → no lost update, no lock, no reaper, no `busy_timeout` — R1, R2, R3, N7 go to zero by construction.
  - Both combatants named it as their fallback; agent 08 derived it blind (structural invariant #9: "Directory-as-database. One file per project, atomic tmp+mv writes").
  - Matches what codebase already got right (02 Finding 9: daemon shards by session, one writer per file; registry inherits at ~23–50 files vs daemon's 1498).
  - Keeps 01's browser story: `res.json()` zero-dep, Artifact CSP blocks CDNs; local server globs `registry.d/`, joins liveness, serves one JSON array (agent 09's `GET /api/projects`). Browser never reads the raw store.
  - Keeps `git diff` + hand-repair (SQLite's opaque binary kills both).
- **Agent 02 wins nearly everything except its headline:**
  - **YAML DISQUALIFIED** (two agents, two grounds): 01 — system `/usr/bin/python3` is **3.9.6 with no `yaml`**, `yq` **not installed**, browser would need `js-yaml` (blocked by Artifact CSP). 02 — truncated YAML parses, returns 19/30; "the next write serialises those 19 rows back to disk and makes the loss permanent." Deliberately overrules ACOS house style. (Agents 07, 08 proposed YAML registries but held neither the storage lens nor ran the tests.)
  - **`mkstemp(dir=<target's own dir>)`, never a fixed `.tmp`** — measured 180/360 → 0. Do not copy the house helper.
  - **`fsync(tmp)` → `rename` → `fsync(dir)`** — atomicity is not durability.
  - **`fcntl.flock` over the house mkdir-lock** *if a lock is ever needed* (compaction/GC only): kernel **auto-releases flock on SIGKILL in 0.000s**; **mkdir lockdir survives SIGKILL** → needs 60s reaper → second-order race (reaper steals lock from slow-but-alive writer).
  - **`LOCK_NB` + bounded retry, never blocking `LOCK_EX`** — macOS has no `timeout(1)`; blocking wait on wedged holder hangs forever; a hung close skill triggers exactly the force-quit this project exists to prevent.
  - **Ship `rebuild-registry.py` in v1** (the 16/16 rebuild). "An unproven rebuild path is not a mitigation."
  - **APFS case-insensitivity:** `realpath` does not case-normalise; `os.path.normcase` is a **no-op on POSIX** (feeds C2).

### C2 — Identity key: git DISQUALIFIED as identity, refuted live three times over
- **Conflict:** Agent 03: `git rev-parse --show-toplevel` (canonicalised with `pwd -P`) as registry key. vs Agents 01/08: UUID minted at enrollment + `<root>/.acos/project-id`. 01 ran it; 03 inferred it.
- **Refutation (agent 01, live):**
```
okoa-loan-intake-system          git@github.com:okoateam/okoa-loan-intake-system.git   main  4e2846d
Backup okoa-loan-intake-system   https://github.com/okoateam/okoa-loan-intake-system.git main 31fe1dd
Clone-okoa-loan-intake-system    git@github.com:okoateam/okoa-loan-intake-system.git   main  1ec85ea
```
  One upstream repo, three distinct toplevels, three distinct HEADs, two URL schemes → git-derived identity collapses genuinely different projects and cross-contaminates handoffs. Coverage also fails: of **31 directories under `Vibe Coding/`, only 14 are git repos; 18 have `.acos/`**; the sets don't coincide.
- Agent 03's own edge-case section proposed the winning answer ("path is the lookup key, `project_uuid` is the identity"). 03's headline loses; its edge-case note wins.
- **Synthesized identity model (4 agents, no remaining disagreement):**
  | Layer | Value | Source | Why |
  |---|---|---|---|
  | Identity | `project_uuid` (uuid4), minted **once at enrollment**, stored at `<root>/.acos/project-id` | 01, 03(edge), 08 | Immutable; survives rename/move and the Backup/Clone collision |
  | Lookup index | `realpath()` **then** `.casefold()` | 02 | APFS case-insensitive; `realpath` doesn't normalise case, `normcase` no-op on macOS → `/vibe coding/...` vs `/Vibe Coding/...` = two rows for one project. Agents 01, 03, 08 all said bare "realpath" and would have shipped this bug |
  | Re-link key | `(st_dev, st_ino)` | 02 | Verified: inode survives rename/move (`16777232:83800502` unchanged). Dead path usually = relocated, not deleted → self-heals |
  | Git | `{branch, commit, dirty, remote}` — **nullable captured attribute** | 01 | Informational only; 17/31 candidates have no repo; remote must be normalised (`git@` vs `https://`) |
  | **BANNED** | `sanitize(cwd)` as identity | 08 | Verified **non-injective**: 5 distinct paths → 1 key; inverted too: `~/.claude/projects/` holds **4+ distinct keys for the same ACOS 3.0 project**. "Project identity is a function of cwd, not of project." |
- Agent 11's contribution = principle, not key: cmux's `claude` wrapper `uuidgen`s a session ID and passes `--session-id` **before** Claude starts (deterministic binding from t=0), vs ACOS Eternity's discover-and-re-bind (886 `cmux-surface-*` files + stale-binding bug history). Lesson: **mint at enrollment, never derive.** (Session identity ≠ project identity, but the principle transfers.)
- **Residual (agent 08, N3):** registry key and Eternity's `sanitize(cwd)` key **must not disagree**. Launcher must launch with cwd == exactly `realpath(registry.root)`; SessionStart should assert `realpath(cwd) == registry.root` and log loudly on mismatch. Otherwise: subdir cwd → different Eternity project key → resume silently not found (fails safe) OR merges with another project's scope (fails open — un-does the f639310 fix by construction).

### C3 — Liveness/match key: three agents answered DIFFERENT questions; layered verdict; title NEVER
- **Conflict (apparent):** 05: match on `description` not `current_directory`. 09: workspace UUID then cwd, never title. 06: neither — `PID → cwd` via `lsof`.
- **VERDICT — layered, all three verified, all three needed:**
  | Question | Answer | Agent | Evidence |
  |---|---|---|---|
  | "Is project P open at all?" | claude `PID → cwd` via `lsof -a -d cwd -p <pid> -Fn` | 06 | PID 32079 → `/Users/zee/Documents/Vibe Coding/ACOS 3.0`. **Un-lie-able: force-quit removes the process; nothing left to lie** |
  | "Where is its pane, so I can focus it?" | `PID → tty` (`ps -o tty=`) → `cmux tree --all --json` | 06 | Verified on 3 real surfaces: PID 32079 → ttys000 → surface:1 → workspace:1. Re-minted by running app every call |
  | "Which registry row is this workspace?" | `[key:<uuid>]` tag embedded in `--description` | 05 | `--description` round-trip verified exact |
  | "How do I read cmux's state at all?" | `cmux rpc workspace.list` (real JSON), **never** `cmux list-workspaces` | 09 | `--json`/`--format json` both silently ignored; `rpc` form returns `current_directory` and `id`, text form never shows them |
  | "Is this workspace the one I launched?" | workspace UUID — live-only, advisory, re-verified | 01, 09 | Reopen **mints a new UUID** → UUID identifies a *binding*, not a project; cmux leaks 9 stale workspaceIds vs 3 live |
- **Adjudication (a):** `current_directory` vs `description` — **05 wins and closes 09's own declared gap.** 09's Data Gap: "did not confirm whether `current_directory` tracks the shell's live `cd` or the launch `--cwd`." 05 tested: **it tracks the live shell cwd** (workspace created with bad `--cwd /Users/zee/nope/nope-swarm05` still reported `cwd='/Users/zee/Documents/Vibe Coding/ACOS 3.0'`). So 09's fallback `realpath(current_directory) == realpath(project.path)` is **unsafe as written** — in-session `cd` breaks it; 3–4 workspaces already share one cwd.
- **Adjudication (b):** `cmux identify --surface` is NOT a liveness probe (06, decisive) — valid surface, bogus UUID, and known-dead surface (`91B2A7DB-...`, the FruitSync one) all return exit 0, byte-identical key sets, requested surface never echoed → fail-open false positive on every dead surface (the original incident's bug class). Agent 03's close protocol validates `CMUX_WORKSPACE_ID` against `workspace.list` with `grep -qx` — correct pattern, unaffected.
- **Unanimous negative: NEVER match on `title`.** 09: Claude Code rewrites titles live; sample shows `'⠐ Claude Code'` — a spinner frame; "a title-matched switcher would flicker as the spinner animates." 10 independently: the tab title *lies*, zero information.
- **Design tension no single agent saw (both halves of one ~280-char field):** 05 wants `[key:<uuid>]` in `--description`; 10 wants the description to carry the **next-action sentence** ("the highest-leverage 20 characters in this design"; `⠐ Claude Code` → `Fix keychain access and handoff protocol`). **Resolution:** append tag at the END — `<next action> [key:3f6c1e8a-...]` (~45 chars overhead), accept minor clutter. Hand-opened workspaces (no tag) fall back to agent 06's process join, NOT cwd.

### C4 — Are `workspace:N` refs positional? NO — 05 right; 01's own output disproves 01
- **Conflict:** 01: refs are positional indices that shift. 05: refs are stable handles.
- Agent 01's own pasted JSON:
```
{"ref":"workspace:1","index":0,"id":"9392A583-...","title":"⠂ Claude Code"}
{"ref":"workspace:4","index":1,"id":"B5DB13F5-...","title":"acos-close-probe"}
{"ref":"workspace:2","index":2,"id":"0C99FE36-...","title":"✳ Fix keychain..."}
```
  `ref` and `index` are separate fields that do not track each other (`workspace:4` at `index:1`). 01 conflated `ref` with `index`.
- 05's independent proof: new workspace was `workspace:6` while displayed 2nd (order `workspace:1`, `workspace:6`, `workspace:2`); later refs reached `workspace:11` with only 3 workspaces present. **Refs are stable handles from a monotonic allocation counter; `index` is the position.** What 01 actually saw: its `workspace:3` slot disappearing after close and a sibling appearing at `workspace:4` = next counter value, not renumbering.
- **RESOLVED: agent 05.** Shared conclusion survives regardless — **persist UUIDs, never refs** — for two independently sufficient reasons: refs are per-cmux-run handles meaningless across restart (05); reopened project mints a brand-new workspace UUID and cmux deletes the closed record entirely (01).

### C5 — Close-handoff namespace: 06's directory + 07's naming/sentinel
- **Conflict:** 06: `memory/handoffs/closed/<slug>/` subdirectory. vs 07: `memory/parked/*.reentry.md`. Both verified disjointness from existing readers.
- **06 wins the directory, three grounds:**
  1. Needs no cooperation from any existing reader. Subdirectory invisible to `eternity-protocol-core.sh:87`'s non-recursive `ls -t memory/handoffs/*.md memory/handoffs/*.yaml` ("this is exactly why `archive/` is already safe"). 07's plan needs (a) handoff in `memory/handoffs/` where the glob CAN see it — 06's sharper case: if close-project writes there and Eternity fires within 300s, Eternity's `ls -t` binds close-project's handoff and pairs its resume to the wrong document; and (b) a new skip rule added to `/acos-complete`'s prose — per SPINE 4, prose-dependent safety = 44% execution rate.
  2. 07's split across two directories re-creates the exact mechanism that produced the 17/17 dangle (agent 12 E3: `.yaml` handoffs archived, `.resume.md` siblings left behind). 06's single directory co-locates both artifacts → no cross-directory pointer to break.
  3. 06's namespace is glob-invisible to all four existing readers simultaneously; 07's own enumeration of the four patterns shows its design clears only three.
- **07 wins naming + sentinel:**
  - **`.reentry.md`, never `.resume.md`** — `.resume.md` is load-bearing for Eternity: `core.sh` and three skills resolve `memory/handoffs/${BASENAME}.resume.md` via the pointer path; writing one makes close-project artifacts addressable by the Eternity resume path. Precedent burn: the doubled `...resume.resume.md` pointer to a nonexistent file, guarded at `core.sh:84-87`.
  - **`status: parked`** — census across all **172 handoffs**: `status:` takes only `completed` (147) and `active` (4); `parked` is a clean unused sentinel, semantically honest (work unfinished), and `/acos-complete`'s "no status field → treat as active" logic doesn't reach an explicit value. (06 proposed `status: completed`-at-birth for the same purpose; `parked` better.)
  - 07's `long-running-run-pause` find: user already hand-rolled a park-shaped handoff once — weak but real corroboration.
- **VERDICT:** `memory/handoffs/closed/<slug>/{handoff.yaml, <slug>.reentry.md}`, both co-located in one subdirectory, `type: close-project`, `status: parked`. Directory from 06; extension, sentinel, census from 07; belt-and-braces from both.

### C6 — Dangling pointer counts: 10/18 AND 17/17 both correct; they compose
- **Conflict (apparent):** 04: 10 of 18 dangling. 12: 17 of 17 dangling. Both verified (ran it); **different predicates on different populations.**
  - 04: "Does the path written *inside* the file resolve?" — extracted backticked `...handoffs/...` pointer from each `.resume.md`, `test -e` → **10 dangling / 8 OK of 18** (one resume carries no pointer, excluded).
  - 12: "Is the paired handoff still *next to* the file?" — for each top-level `*.resume.md`, tested sibling `<base>.yaml` or `<base>.md` in same dir (`[ -f ]`) → **17 of 17 dangling**.
- **Composed story:** `/acos-complete` moved `.yaml` handoffs to `archive/`, left `.resume.md` siblings behind. All ~17–18 lost their sibling (12's test). 8 of 18 had the embedded pointer rewritten to the archive path and still resolve; 10 did not (04's test). Mechanism = SPINE 4: rewrite is prose-specified at `acos-complete/SKILL.md:108`, 8/18 = 44% executed. 04 confirms **all 10 dangling targets survive in `archive/`** — "the bytes exist; the *link* is broken."
- Population discrepancy (17 vs 18) immaterial — likely files moving during the swarm.
- Agent 12's inference (from read patterns, which 04 lacked): a 100% dangle rate survived **five weeks, ~a dozen sessions, unnoticed** → the files are never read. Pre-empted rebuttal ("dangle is cosmetic; resume reads the per-PID pointer, not the sibling glob"): "This is correct **and it is my point.** 'Nothing broke' and 'nothing is used' are the same observation about a file nobody opens."
- **Shared fix, two lenses:** registry **derived by scanning**, not a stored pointer. 04: "A derived index cannot dangle... deletes risks #2, #5 and #6." 12 (DR-4): "entries that fail a link check are shown as BROKEN in red — never hidden."
- **REQUIRES:** link-check with visible BROKEN state, never hidden.

### C7 — Build vs. adopt: ADOPT the platform, BUILD the thin row; upgrade is a PREREQUISITE, not a substitute
- **Conflict:** 11: ADOPT — cmux 0.64.x ships it. vs 01–09: largely designed a build.
- **Agent 11's claims — ALL [DOC-CLAIMED, NOT TESTED]:** agent 11 is on 0.63.2 (latest **0.64.18**, released the day of the report); verifying restore would have required quitting cmux/killing live sessions. "All restore claims are from docs/source/snapshot inspection, not observation." Claims:
  - 0.64.11: **Agent Hibernation** (kills idle background agent processes to free RAM/CPU, resumes with saved session when tab visited).
  - 0.64.15: `terminal.autoResumeAgentSessions` (default `true`) + corrupt-snapshot rolling backup.
  - 0.64.16: `automation.workspaceAutoNaming` (AI titles from conversation content).
  - `sidebar.showWorkspaceDescription` defaults true — "the sidebar IS the project-list browser."
  - 11's synthesis: the build = thin registry row joining `{project path, session UUID, handoff path, description}` where every field but `description` is already on disk.
- **Field-by-field stress test:**
  | Field | On disk? | Verified by |
  |---|---|---|
  | project path | Yes — `~/.claude.json` `projects{}` = 42 entries, survives process death; also `~/.cmuxterm/claude-hook-sessions.json` `.cwd` | 11, 01 |
  | session UUID | Yes — `lastSessionId` populated 32 of 42 | 11 |
  | handoff path | Yes, derivably — agent 02 rebuilt 16/16 project rows from handoffs alone | 02 |
  | description | **NO** — `lastSessionFirstPrompt` 3/42; `customDescription` 2/6 (one swarm-written) | 11 |
- 3 of 4 fields survive; the 4th is the field agents 10, 11, 12 rule must never be typed (three lenses converge): **the description must be GENERATED — by the close skill from the handoff, or by cmux's auto-naming.** "This is the gap. It is the whole build."
- **What the upgrade does NOT solve (the residual = what to build):**
  1. Hibernation does not reduce tab COUNT — fixes "Mac slows down", not "which of my 13 ACOS tabs" (SPINE 1). Only **focus-not-launch** hits the real problem (12 independently: "A project switcher does not fix 13 tabs of the same project").
  2. Auto-naming produces a **title**, not a next action; `lastBody` is the last message. Neither is "what I was doing / what's next / what's half-broken". Near-miss: auto-naming plausibly delivers agent 10's row line 1 for free; **line 2 (the next-action payload) is the build.**
  3. **No native registry enumerates PARKED projects** (11 verified by running: `claude agents --json --all` returns live sessions only, 2 of them; `~/.claude/sessions/<pid>.json` is PID-keyed, evaporates on process death; cmux sidebar shows live workspaces). "A parked project appears in nothing. That is the window's entire unique job, and it is the correct scope."
  4. cmux still cannot be the store post-upgrade (SPINE 5); 0.64.15 rolling backup mitigates corruption but does not make a restore-file a history.
  5. **The upgrade may break the thing that works** — cmux #5427: native `claude --resume` drops the cmux `--settings` wrapper so hooks stop firing (fixed 0.64.13 **[DOC-CLAIMED]**). Agent 06 established the **in-pane hook IS the live carrier** (daemon injector: ~6 successful FIRED ever vs `rc=2 x1391`). **Single biggest risk in the adopt recommendation — must be verified BEFORE upgrading, not after.**
- **VERDICT:** ADOPT platform, BUILD thin row, amended: row must be (a) derivable from disk with no ritual (02, 12); (b) carry a *generated* next-action headline no vendor ships (10, 11); (c) keyed by minted `project_uuid`, NOT the session UUID agent 11 named — 08 proved path→key non-injective, 01 proved reopen mints a new session. "On the key, 01/08 win; on the scope, 11 wins."
- Agents 01–09 not wasted: build ~5x too large but mechanisms make the small build correct — 05's argv route, 06's process join + namespace defence, 03's verification gate, 04's receipt discipline, 09's opaque-ID launch bridge, 02's rebuild + atomic-write discipline. "The scope shrinks; the engineering does not."

### C8 — Close or Open? User contradicted on ordering, precisely and on one point only
- **Conflict:** User asked for a close skill (write handoff → write resume prompt → add/update registry row). Agent 12: close skill is the wrong center of gravity.
- **Agent 12's unrebutted structural argument:** the stated failure mode is force-close. **In a force-quit, the close skill does not run.** If the registry is populated by closing, the registry is empty at exactly the moment it exists to serve. DR-8: "The close skill must never be a precondition for anything. Force-quit must lose nothing the registry needed." Test: `kill -9` every cmux tab, reopen the window, nothing is missing. ("Structural, not empirical, so no experiment could rebut.")
- Independent support: 04 Risk #3 ("Close fires when context is nearly exhausted... the moment fidelity matters most is when the session can least deliver it" — High likelihood); 02 Finding 6 (rebuild proven 16/16 → auto-population demonstrated, not speculative); 12 E2+E7 (`/acos-complete` run 147 times produces artifacts never read — "a close-populated registry is modelled on the dead half of your existing system").
- **But 12's DR-2 (seed by scanning) is rejected as written** (the SPINE 2 divergence): 01 Finding 4 (naive scan enrolls `memory/`, `planning/`, `learning-curve/`, reviewer-rules dir → explicit-enrollment, never filesystem-scan-derived); 10 Finding 8 (`~/.claude/projects/` polluted AND misses real work — Font-Forge session died `[BLOCKED: not logged in]`, work happened in the global skill dir); 08 corroborates pollution: `~/.claude/projects/` holds 4+ distinct keys for the same ACOS 3.0 project including `...--claude-agents` and `...--claude-skills-acos-investment-committee`.
- **RESOLUTION (genuine synthesis):**
  > **Membership is established by ENROLLMENT ON FIRST SIGHT, gated by a project marker — never by closing, and never by a naive scan.**
  A project enrolls the first time a session starts in a directory containing `.acos/` **or** `CLAUDE.md` **or** `memory/handoffs/`.
  - 12 satisfied: row exists before any close; registry never empty at the crisis.
  - 01 satisfied: marker gate kills strays (`memory/`, `planning/`, `learning-curve/` have no `CLAUDE.md`, no `.acos/`).
  - 10 satisfied: marker gate kills scratchpads/skill subdirs; row still curated (a directory is a project because it is *marked* as one, not because a process ran there).
  - 02's rebuild works unchanged: its three enumeration sources are exactly these markers (`find */memory/handoffs` authoritative; `*/CLAUDE.md` markers; `~/.claude/projects/` as a **lossy hint requiring glob-disambiguation, not a decoder**).
- **The close skill's surviving real job — ENRICHMENT, not creation:** it adds the one thing no scan recovers. Agent 04 Finding 5: "What actually dies when the tab closes is the reasoning — not the files." Git tree, `memory/`, `planning/`, `.acos/` all survive close; what dies is negative state / hard-won traps (e.g. "the fix-agent died on an API error and wrote NOTHING; files are clean", "agent self-reports hid 2 real bugs this session") — no repo scan or `git log` reconstructs these. Agent 03 (Finding 7) independently: parent writes the intent core, `handoff-agent` enriches from disk, **never delegate the intent core** — a Sonnet agent reading `git log` will confabulate the *why* (project memory documents exactly that failure).
- **Concrete design consequences:**
  - Close skill does NOT create the row (row already exists) and does NOT gate anything (force-quit loses nothing).
  - Close skill DOES add the why, traps, rejected alternatives, `next_action` headline — and closes the tab (agent 03 verified tab-close works).
  - Degrades gracefully to optional polish (12: "If the window becomes the fastest way *in* to a project, closing tabs becomes a safe byproduct").
  - Agent 10's structural completion: **one row per PROJECT, never per session** — 21 live sessions → ~7 rows; 508 recorded ACOS 3.0 sessions → 1 row. "No tab bar can ever do this. Lead the entire design with it."

---

## Verification-status flags (rollup)
- **Machine-verified (ran on this machine):** all SPINE 1–7 evidence rows except agent 11's issue-tracker items; C1 both experiment arms + mkstemp/flock/SIGKILL tests; C2 git refutation + inode test + non-injectivity; C3 all five probe rows + bad-`--cwd` test + `identify` fail-open; C4 both JSON observations; C5 glob-invisibility + 172-handoff status census; C6 both counts; C7 field census (`~/.claude.json` 42 entries, `lastSessionId` 32/42, `lastSessionFirstPrompt` 3/42, `customDescription` 2/6), `claude agents --json --all` live-only; C8 marker-directory checks.
- **[DOC-CLAIMED, NOT TESTED]:** ALL cmux 0.64.x feature claims (Agent Hibernation 0.64.11; `terminal.autoResumeAgentSessions` + rolling backup 0.64.15; `automation.workspaceAutoNaming` 0.64.16; `sidebar.showWorkspaceDescription` default; #5427 fix in 0.64.13). Agent 11 on 0.63.2; explicit: "All restore claims are from docs/source/snapshot inspection, not observation." Upgrade hook-injection risk must be verified BEFORE upgrade.
- **Issue-tracker-sourced (upstream, not local):** cmux #2387 (open restore regression), #2895 (snapshot silently overwritten), #2125 (workspaces reopened at `$HOME`), #5427.
- **Unknown-cause anomaly:** agent 05's 1-of-6 silently dropped resume prompt — leading hypothesis tested and disproved; cause still unknown.