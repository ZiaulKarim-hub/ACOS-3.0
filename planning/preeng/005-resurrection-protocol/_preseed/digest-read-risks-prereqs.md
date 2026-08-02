# Digest: Swarm Report — cmux Project Registry & Switcher (swarm-20260714-084532)

**Report:** `/Users/zee/Documents/Vibe Coding/ACOS 3.0/.acos/swarm/swarm-20260714-084532/synthesis/report.md` | Date 2026-07-14 | 12 agents (all delivered; 3 died to API errors after writing, 1 resumed) | 6 sub-questions, 5 lenses (Technical Feasibility, Risk, Integration, User Impact, Competitive)

---

## 1. Executive Summary (compressed, faithful)

- **Top line: "Upgrade cmux first, then build about a fifth of what you asked for."** User is on cmux **0.63.2**. **0.64.11** ships Agent Hibernation (kills idle background agent processes to free RAM/CPU, resumes from saved session on tab visit). **0.64.15** ships auto-resume of restored agent sessions. **0.64.16** ships AI auto-naming of workspaces from conversation content. Latest is **0.64.18, released today (2026-07-14)**. **CRITICAL CAVEAT: all 0.64.x claims are documentation claims — agent 11 could not test any (testing required restarting cmux, killing live sessions). Everything on the adopt side is doc-verified, not machine-verified.**
- **Strongest finding (6 agents independently): the user is solving the wrong problem — a DUPLICATE problem, not a switcher problem.** Agent 10 measured 21 live Claude sessions ≈ ~7 real projects, **13 of 21 = ACOS 3.0**. Agent 12: 2 live workspaces, both ACOS 3.0. Agents 03/09: 3 and 4 workspaces sharing one `current_directory`. Agent 05 proved **cmux does NO dedup** — bare `cmux <path>` created a 5th ACOS 3.0 workspace while 4 were open. Agent 06: focus-not-duplicate is a *correctness* requirement. Agent 08: two panes on one project is the exact precondition of the 2026-06-26 cross-pane resume-contamination incident; the design makes that rare accident the normal case. **A switcher must FOCUS, not launch.**
- **Registry must NOT be created by the close skill.** Stated failure mode is force-quit-everything; in a force-quit the close skill never runs → registry empty at precisely its moment of need (agent 12, DR-8). Agent 02 proved the alternative: a ~40-line script reconstructed **16 project rows from handoff artifacts alone, reading no registry file**. Close skill should *enrich* an existing row, never be a precondition.
- **Do not build a durable archive and trust it.** Agent 12 forensics: existing durable handoff archive — **151 files, five months, git-tracked** — shows **no filesystem evidence of ever being read to resume work on a later day**. All **17 top-level `.resume.md` files lost their sibling handoff**; **~10 of 17 have atime == mtime to the minute** (written, never read again); unnoticed for **five weeks**. Hot path (daemon `pending-resume-*.txt`) is alive: **63 of 64 read after write, median 190 seconds**. "Two systems wearing one name" — one alive and obsessively bug-fixed, the other a graveyard. **Do not model the new skill on the dead half.**
- **Agent 12's verdict, unsoftened: ~30% odds of routine use (>=1x/week) at day 60; ~60% odds of enthusiastic use for 2–3 weeks then decay.** Decay mode is not "it broke" — it is "he stops closing tabs, because closing was never the thing he wanted." Counter-evidence: user ran `/acos-complete` **147 times over five months by hand** — demonstrably will perform a closing ritual. Reconciliation: `/acos-complete` survives because its payoff is immediate and local. **"Deliberate is not dead. Deliberate-with-deferred-payoff is dead."**

---

## 2. Headline Recommendation

### ADOPT (do not build)
1. **cmux 0.64.18 Agent Hibernation** — solves "my Mac slows down"; vendor-shipped. **Doc-claimed, untested.** (agent 11)
2. **cmux 0.64.16 `automation.workspaceAutoNaming`** — AI titles from conversation content (agent 10's row line 1, for free). *Verify what model it calls before enabling — `automation.autoNamingAgent: "auto"` is undocumented; OKOA-deal confidentiality question.* (agent 11)
3. **Claude Code's native persistence** — **781 transcripts / 1.1 GB** already on disk; `claude --resume <uuid>` already works; persistence is default (only related flag exists to *disable* it). "The hard part of your system already works and you are not using it." (agent 11)
4. **`~/.claude.json` `projects{}`** — **42 entries, 32 with `lastSessionId`**, and it **survives process death**. Durable per-project row `{path -> last session UUID}` exists natively. (agent 11)

### BUILD (genuinely missing, and small)
1. **Per-project registry file** — `~/.acos/registry.d/<project_uuid>.json`, one file per project, populated by **enrollment-on-first-sight**, rebuildable from disk. Only field not already on disk: the **description/next-action**, which must be **generated, never typed**.
2. **The `next_action` headline (<=90 chars)** — the single field that replaces the scrollback. cmux auto-naming gives a *title*, not "what's next and what's half-broken". The one artifact no vendor ships. (agents 10, 11)
3. **A browser window whose ONLY unique job is showing projects that DON'T have a tab.** Post-upgrade, cmux's sidebar (`sidebar.showWorkspaceDescription`, default true) covers live ones. Parked projects appear in no sidebar and not in `claude agents --json --all` (agent 11 verified: **live sessions only**). Much smaller than what agents 01–09 designed.
4. **A close skill that enriches an existing row with intent** — decisions, rejected alternatives, traps, the "why" — the only content that dies with the tab and that no scan can recover. (agents 03, 04, 07)

### DO NOT BUILD
- **A registry whose rows are created by closing.** (agent 12, DR-8)
- **A green "verified resumable" badge.** A naive verifier would stamp ACOS 3.0 today while **70–74 uncommitted files** sit outside every handoff. False-positive cost = permanent trust loss. **Show facts, never verdicts. Only red/amber. Silence means fine.** (agent 10)
- **Any hand-maintained field.** (5 agents, 5 lenses; Convergence 1)
- **A notifier / nagger.** (agents 10, 12)
- **A second handoff/resume writer that touches the daemon state dir.** (agents 06, 07, 08)
- **cmux workspace state as the registry substrate.** Agent 01 proved by experiment that **closing a workspace deletes its record from disk entirely** — and closing is the whole point. Agent 11: cmux's own snapshot is chronically fragile upstream (**#2387 regression still open, #2895 silent partial overwrite, #2125 all cwd -> `$HOME`**). "cmux is the convenient UI, never the database."

---

## 3. Verified Mechanisms (agents actually ran and proved)

| Mechanism | Command | Result | Agent |
|---|---|---|---|
| Closing a workspace DELETES its record from disk | `cmux new-workspace ...` -> flush -> `cmux close-workspace --workspace workspace:3` | `GONE: closed workspace removed from session file at Tue Jul 14 08:49 MDT 2026`. No `list-closed-workspaces` in **154 RPC methods**. Disqualifies cmux as substrate. | 01 |
| Self-close works and is brutal | `cmux rpc workspace.close '{"workspace_id":"..."}'` vs workspace running `sleep 400` | Workspace gone; `pgrep -fl "sleep 400"` returned nothing. No confirmation dialog, no refusal; process killed. **Param is `workspace_id`, not `workspace`.** | 03 |
| The /clear constraint does NOT apply to close | `workspace.close` issued from a Bash call inside the session's own shell | Works — out-of-band Unix-socket RPC to the app; terminal never reads anything. **No daemon needed.** | 03 |
| Git identity refuted — live, 3x | `git -C <dir> remote get-url origin` / `rev-parse --short HEAD` across 3 sibling dirs | One upstream, **3 toplevels, 3 HEADs, 2 URL schemes**. Only **14 of 31** dirs are repos. | 01 |
| Registry rebuildable from disk | `rebuild.py`, reading **no registry file** | **16/16 project rows** reconstructed from handoff artifacts alone (status, last-activity, resume presence, handoff counts). | 02 |
| flock is load-bearing | 25 concurrent writers, one JSON file | With lock: **25/25**. Without: **3/25 — and still valid JSON** (silent lost update). | 01 |
| SQLite WAL handles the storm | 6 writers x 80 UPSERTs | `busy_timeout=5000` -> **480/480, 0 BUSY, 0 lost**. `busy_timeout=0` -> **140 BUSY, LOST=0**. | 02 |
| ACOS house atomic-write helper has a real bug | 6 procs x 60 writes, shared `.tmp` vs `mkstemp` | Shared: **180/360 OSError crashes**. Unique: **0**. `torn_content=False` in both arms — bug is the staging area, not rename. | 02 |
| YAML fails silently; JSON fails loudly | 30-record registry truncated to 60% | JSON **0/30** (throws). JSONL **18/30**. YAML **19/30 — parses, no error, silent loss**. | 02 |
| APFS is case-insensitive; realpath does NOT casefold | `realpath()` string-compare vs `os.path.samefile` | string-compare **False**, samefile **True**; `normcase` is a **no-op on POSIX**. | 02 |
| Inode survives rename/move | `stat -f '%d:%i'` before/after move | `16777232:83800502` unchanged. | 02 |
| flock auto-releases on death; mkdir-lock does not | Holder SIGKILLed mid-lock | `fcntl.flock`: auto-released in **0.000s**. `mkdir` lockdir: **SURVIVES SIGKILL**. | 02 |
| Argv delivers a multi-line prompt as ONE message | `--command "$CLAUDE \"\$(cat resume.txt)\""` + `read-screen --scrollback` | `❯ RESUME CONTEXT (multi-line test):` ... `⏺ ARGV_MULTILINE_ONE_MESSAGE`. Auto-submitted; session stays interactive. **5/6 trials.** | 05 |
| `cmux send` SHREDS multi-line prompts | `cmux send 'Line one.\nLine two.\nSay MULTILINE_SUBMITTED\n'` | Fragmented into **3 separate messages** + `Press up to edit queued messages`. **Disqualified for prompts.** | 05 |
| cmux does NO dedup | `cmux "<ACOS 3.0 path>"` while already open in 4 workspaces | `OK workspace:10` — a **5th** workspace on the same project. | 05 |
| `new-workspace --cwd` silently accepts a bad path | `cmux new-workspace --cwd /Users/zee/nope/nope-swarm05` | **`OK workspace:8`, exit 0.** (Bare `cmux <path>` *does* validate: `Error: Path does not exist`, exit 1.) | 05 |
| `current_directory` tracks the LIVE shell cwd | Workspace created with deliberately bad `--cwd` | Reported the **inherited** cwd, not the launch dir. Closes agent 09's stated gap. | 05 |
| `--description` round-trips exactly | `--description 'agent-05 probe; safe to delete'` | Returned verbatim; persists to disk as `customDescription`. | 05, 01 |
| External env-stripped processes CAN drive the socket | `env -i HOME=... PATH=/usr/bin:/bin cmux new-workspace ...` | `OK workspace:9`. **`access_mode: cmuxOnly` does NOT mean in-cmux-only** — real control is the **0600 socket file**. Browser launcher will work. | 05 |
| `cmux identify --surface` FAILS OPEN | Valid, bogus, and known-dead surface UUIDs | **All three exit 0 with byte-identical output**; requested surface never echoed. **Not a liveness probe.** | 06 |
| The PID->cwd->tty->surface join resolves | `lsof -a -d cwd -p 32079 -Fn`; `ps -o tty=`; `cmux tree --all --json` | PID 32079 -> `/Users/zee/.../ACOS 3.0` -> ttys000 -> surface:1 -> workspace:1. Verified on 3 surfaces. **Un-lie-able.** | 06 |
| The pane is forked by the cmux APP, not the caller | `ps -o pid,ppid,command -p 72687,72688,1593` | `cmux.app(1593) -> login -flp zee -> bash --noprofile --norc -> zsh`. **A registry launch cannot inherit a stale surface binding.** | 06 |
| `sanitize(cwd)` is non-injective | The transform run on 5 distinct paths | **5 paths -> 1 key** (`sort -u \| wc -l` = 1). Inverted: `~/.claude/projects/` holds **4+ keys for one project**. | 08 |
| List-form `subprocess.run` defeats injection | name = `AGENT09-TEST; touch /tmp/pwned_agent09; echo $(whoami)` | `returncode: 0`; `/tmp/pwned_agent09` never created; title stored **verbatim**. **The real surface is XSS, not shell.** | 09 |
| cmux has NO custom URL scheme | `plutil -p /Applications/cmux.app/Contents/Info.plist` | `CFBundleURLSchemes: ["http","https"]` only, `LSHandlerRank: Default`. Kills the `cmux://` option; explains why bare `open` must not be used. | 09 |
| `list-workspaces --json` is silently ignored | `cmux list-workspaces --json` / `--format json` | Text output both times. **Use `cmux rpc workspace.list`.** | 09 |
| `--id-format` is a GLOBAL option | `cmux list-workspaces --id-format both` vs `cmux --id-format both list-workspaces` | After the command: silently ignored. Before: works. | 05 |
| Refs are handles, not positions | `workspace:6` displayed 2nd; `workspace:11` with only 3 workspaces | Refs are a monotonic counter; `index` is the position. Settles C4. | 05 |
| Code 100% / prose 44% | `grep -c "GIT STATE SNAPSHOT"` (script-emitted) vs dangling-pointer loop (prose-specified) | **8/8 vs 8/18.** Same author, same repo, same period. | 04 |
| 55% of resume pointers dangle | Extract pointer, `test -e`, over `memory/handoffs/*.resume.md` | **10 DANGLING / 8 OK of 18**; all 10 targets recoverable in `archive/`. Loss ratio **1x–12x (up to 92%)**. | 04 |
| 100% lost their sibling handoff | Sibling-existence test per `.resume.md` | **17 of 17.** Unnoticed for ~5 weeks. | 12 |
| The fidelity mechanism silently truncates | `awk` fence count vs stated count | Resume says `uncommitted changes: 74 file(s)`; lists **exactly 40**. `head -40`, no ellipsis. **34 files invisible.** | 04 |
| Hot path ALIVE; cold path a graveyard | atime-vs-mtime on 64 `consumed/pending-resume-*.txt` vs `memory/handoffs/*.resume.md` | Hot: **63 of 64 read after write, median 190s**. Cold: **~10 of 17 atime == mtime to the minute** — never read again. | 12 |
| The tree is chronically dirty | `git status --porcelain \| wc -l` | **70 right now; 74 at last handoff. Branch unchanged 40 days.** Both git row-fields near-zero-signal. | 10 |
| 21 sessions = ~7 projects | User's own inventory + `~/.claude/projects/` jsonl counts | **13 of 21 were ACOS 3.0.** On disk: **508** recorded ACOS 3.0 sessions, **131** FruitSync. | 10 |
| `claude agents --json --all` lists LIVE sessions only | Ran it (exit 0) | Returns 2 live. **Does not enumerate parked projects — the native registry gap.** | 11 |
| The native description field is empty | `~/.claude.json` census; cmux snapshot census | `lastSessionFirstPrompt`: **3 of 42**. `customDescription`: **2 of 6** (one written by a swarm agent today). | 11 |
| cmux mints session identity at spawn | Read `/Applications/cmux.app/Contents/Resources/bin/claude` | `SESSION_ID="$(uuidgen ...)"` then `exec "$REAL_CLAUDE" --session-id "$SESSION_ID" --settings "$HOOKS_JSON" "$@"`. **Mint, don't discover.** | 11 |
| 8820 is free; the house pattern is real | `lsof -iTCP:8800-8830 -sTCP:LISTEN`; `grep -rn "shell=True"` | Empty. **Zero `shell=True` hits** across gr-server, gr-pool, type-forge. | 09 |
| System python3 has no yaml; yq/flock/timeout absent | `/usr/bin/python3 -c "import yaml"`; `which yq flock timeout` | `ModuleNotFoundError`; yq NOT FOUND; flock NOT FOUND; timeout/gtimeout NOT FOUND. **`jq` IS Apple-shipped.** | 01, 02 |

---

## 4. Risk Register (merged, ranked by likelihood x blast radius)

| # | Risk | Likelihood | Blast radius | Detectable? | Mitigation | Agents |
|---|---|---|---|---|---|---|
| 1 | **Duplicate launch -> two panes, one project -> cross-pane resume contamination.** Residual #10 (`eternity-resume-prepend.sh:158-169`) is pane-blind and **still open in live code**; the new design makes its precondition routine. | High | Catastrophic — wrong project's work resumes; discovered via "what were we working on?" | Poorly — silent | **Fix residual #10 FIRST.** Then probe liveness (06's join) and **FOCUS, never launch a second**. Fail closed if absence can't be proven. | 08 (N1), 06, 05, 03, 09, 10 |
| 2 | **Low-fidelity handoff — reasoning gone, files intact.** Reopen "works"; mental model lost; discovered weeks later. | Certain (it is the default) | Total for the irrecoverable half (the *why*) | No — reopen looks successful | Capture decisions/rejected alternatives/traps, not file state (git has that, better). **Blind** round-trip verifier. Receipt counts **reasoning fields**, not bytes. | 04 (#1), 03, 07 |
| 3 | **Registry empty at the force-quit** (populated by closing). | High | Total — tool absent at its only moment | Yes, trivially | Enroll on first sight; close only enriches. **Test: `kill -9` every tab; nothing missing.** | 12 (DR-8/DR-2) |
| 4 | **Dangling pointer — resume points at moved/absent handoff**; fresh session Reads a bad path and **proceeds on the thin summary anyway**. | Measured 55% (10/18); 100% lost sibling | ~90% of context (measured 1x–12x) | Weakly — only a failed Read; agent continues | **Derive the index by scanning**; co-locate handoff + reentry so no cross-directory pointer exists. **A derived index cannot dangle.** | 04 (#2), 12 (E3) |
| 5 | **Silent truncation inside the fidelity mechanism** — `head -40` caps the list while the count reports the truth. | Certain when >40 dirty — and it IS 70 | Medium-High — reader believes list complete | No — no ellipsis | One-line fix. **Every truncation must print its own truncation**; receipt prints `listed N of M`. | 04 (#4) |
| 6 | **Close-skill artifact is surface-less -> adopted by a sibling pane** via half-open gate (`token-watcher.py:1113`), passing mtime liveness check trivially. | High *if* it writes to `state/`; zero if it stays out | Wrong resume injected into an unrelated live pane | Poorly | **Write nothing into `state/`** except `stop-<sid>`. Close the orphan-surface-unknown half of P1-F. | 08 (N2, Incident 6) |
| 7 | **Registry key != Eternity's `sanitize(cwd)` key.** Launcher opens at root; Claude's real cwd is a subdir/symlink. | High | Silent resume loss, or cross-project scope merge un-doing the f639310 fix | No | Store `realpath(root)`; launch with exactly that cwd; **assert `realpath(cwd) == registry.root` at SessionStart** and log loudly. | 08 (N3) |
| 8 | **Registry row = permanent stale binding** (nothing expires; months-old row looks fresh). | High over months | Launch into a wrong/nonexistent dir | Yes, at render time | Rows store **durable facts only**; `last_verified_at`; realpath probe at render; any "dead" verdict must **self-expire** (the 2026-07-13 lesson). | 08 (N4), 02 (R9) |
| 9 | **Trust death: one silent loss event ends the tool permanently.** | Low per-event; certain over time given SPINE 3 | Terminal — never comes back | Only at the worst moment | **Prove one restore before asking for one save (DR-1).** Never blind-overwrite. Rolling backups. | 12 (E9), 11 |
| 10 | **Eternity fires WHILE the close skill runs** -> interleaved writes, half-written handoff. | Medium | Corrupt/merged resume; possible loss of close handoff | Partly | Write `state/stop-<sid>` **first**. Atomic writes. | 08 (N6), 06 |
| 11 | **Untrusted-directory trust gate silently blocks the resume prompt** — workspace looks launched; prompt never delivered. | Medium | Launch silently no-ops | No — looks fine | Launch only previously-trusted dirs, or `read-screen` for `"Quick safety check"`. | 05 (F11) |
| 12 | **Two writers, one namespace, mtime arbitration** — Eternity's resume and the close resume indistinguishable by shape; only mtime separates. | High if namespaces overlap | Resume at the wrong altitude | No | Disjoint namespaces + identity-match selection. **Never `ls -t` as a selector.** | 08 (N5), 06 (F4) |
| 13 | **Registry write races between two panes** -> lost update on a shared file. | Medium | Silently loses a project row — the exact failure the design exists to prevent | No | **One file per project.** No shared mutable file. | 08 (N7), 02 (R1/R3), 01 |
| 14 | **XSS from registry-derived strings** — cmux stores/returns hostile strings verbatim (verified). | Medium | Script execution in the switcher UI | Yes | `textContent`, **never** `innerHTML`. This is the real injection surface. | 09 |
| 15 | **CSRF: any open web page POSTs `/api/launch`** (no preflight for a form POST). | Yes — the main web risk | Capped at "an unwanted tab opens" by opaque-ID design | Yes | Opaque ID + `Origin` + `Host` + JSON content-type. **Do not copy `ACAO: *`.** | 09 |
| 16 | **SessionEnd cleanup will not survive the self-close.** | Probable | Ephemeral state leaks | Yes | Run cleanup **inline, before close**. Defer nothing to "after the close". | 03 (F8) |
| 17 | **GC'ing `pid-<sid>` files IMMORTALISES their watcher** (`self_terminate_if_owner_dead()` only fires when the pid file exists). | Medium if GC added | Converts a file leak into a **process** leak | Yes | Any GC must reap the matching watcher **first**. | 06 |
| 18 | **Registry accelerates the SessionStart eviction loop** — O(all pid files) with a fork each, on every session start: **450 files, 0.569s today; ~2s at 1500**. | High | Slow `/clear`; growing forever | Yes, measurable | Bounded GC (dead PID **and** mtime >14d) — but see #17. Countervailing: close skill is net load *relief*. | 06 (F7) |
| 19 | **Unexplained 1-in-6 prompt drop.** Cause unknown; leading hypothesis tested and disproved. | ~17% observed | Resume silently doesn't land | Only if you check | **Verify delivery** (`read-screen` for a marker + retry). Do not assume. | 05 (F12) |
| 20 | **Closing the LAST workspace in a window may close the window or quit cmux.** Untested. | Unknown | Could close every project in that window | Yes | Count live workspaces first; skip close if last one. **One test before shipping.** | 03 |
| 21 | **cmux snapshot silently overwritten with partial state (#2895)** — if cmux is ever trusted as store. | Medium (upstream, open) | Workspaces gone after reboot | No | Never make cmux's snapshot source of truth. Refuse to write a snapshot with fewer entries than the previous without an explicit flag. | 11 |
| 22 | **The upgrade regresses Eternity** — cmux wrapper injecting `--session-id`/`--settings` can collide with ACOS hooks (#5427 class); the in-pane hook **is** the live carrier. | Medium | The working resume path breaks | Yes, if tested | **Verify hook firing immediately after upgrading, before building anything.** | 11, 06 |
| 23 | **`archive-project.sh:199` `-delete`s handoffs**, gated on interactive `read -p ... \|\| true` that silently degrades in non-TTY. | Low (manual) | Total, irreversible | No | "Fails safe **by accident**, not by design." One inherited `REPLY=y` flips it to silent mass delete of handoffs, decisions, planning, `vision-document.md`. Never gate a destructive branch on an interactive prompt. | 04 (#11) |

---

## 5. The Adoption Problem

**Agent 12 verdict (verbatim):** "~30% that this is in routine use (>=1x/week) at day 60. ~60% that it gets enthusiastic use for 2-3 weeks and then decays. Confidence: Probable — inference from direct observation of this user's own artifacts, not from a base rate of strangers. The decay mode will not be 'it broke.' It will be: he stops closing tabs, because closing was never the thing he wanted."

### Evidence AGAINST sustained use
- **Pain is not present.** Right now 2–3 cmux workspaces, all ACOS 3.0. Crisis is episodic — spikes, purge, resolves traceless. "He is specifying for a peak he cannot feel while specifying, and at the actual peak he is in a hurry and force-quits rather than running a 30-second ritual per tab."
- **Duplicate problem, not switcher problem** (SPINE 1, six agents). "A project switcher does not fix 13 tabs of the same project."
- **Cold path already a graveyard** (the most worrying finding). Hot vs cold: hot = `state/pending-resume-<sid>.txt`, read by the machine ~3 min later, **63 of 64 read (median 190s)**, link integrity fine, ALIVE. Cold = `memory/handoffs/*.yaml` + `*.resume.md`, read by a human in theory, **~10 of 17 never read after write minute**, **17 of 17 dangling, 5 weeks unnoticed**, GRAVEYARD. **Killer inference:** three of the last four commits are eternity bug-fixes, all hot-path. "The bugs a person fixes are a map of what they actually use." A 100% dangle rate would have been a P0 within a day if those files were ever read; it survived five weeks.
- **Durability already exists unused** — 781 persisted transcripts, `claude --resume` works, persistence default.
- **The platform is about to eat it** — hibernation + auto-naming arrive automatically/invisibly, "the delivery mode that actually survives."
- **Silent failure is this machine's base rate** (SPINE 3); per HN user `dangerclose`, one silent loss kills a tool permanently: "Chrome Browser Crash, MacBook Crash — I have lost 2K+ links. After that incident I came across raindrop."
- **Closest direct user verdict on this exact spec is negative** — HN `wtcactus` on Brave/Vivaldi vs Edge/Arc: "Brave lets you check which tabs are open in another machine and open them... Edge and Arc **bypass that step**." A registry-you-pick-from called categorically inferior to invisible sync. (One articulate user, one thread — Probable, not a sample.)
- **"It turns out not to be particularly crippling"** — HN `minkles`: "After much thinking, and figuring out I'm just lazy, I just don't bother with it." Loss may not hurt enough to motivate a ritual.

### Evidence FOR sustained use (stronger than agent 12 expected)
- **147 hand-invoked `/acos-complete` runs over five months** (147 archived handoffs `status: "completed"`). "Substantially refutes the naive 'deliberate always loses' thesis. He is demonstrably a man who will perform a closing ritual."
- The registry-as-**index** is genuinely new — the archive has no index and never had one.

### The reconciliation (the whole finding)
> "`/acos-complete` survives because its payoff is immediate and local (a clean context for the next session in the same pane). It is a hot-path action wearing cold-path clothes. The proposed close skill's payoff is deferred and remote. **Deliberate is not dead. Deliberate-with-deferred-payoff is dead.**"

Every design decision follows from this. C8's resolution matters most: **make the window the way you get IN** (immediate, felt, daily) so closing becomes a safe byproduct, not a tax.

### The "just-in-case" thesis (not to be taken as comfort)
- Agent 12's sharpest idea: **the real product may be permission to close, not retrieval.** Evidence = E2/E3 split: the ritual works (147 invocations, 5 months); retrieval artifacts rot to 100% dangle unnoticed. "The archive is not a database — it is a receipt. 147 receipts, every one cashed at the instant of issue, none ever presented again." Explains 5 weeks of unnoticed rot: "you don't go back and check whether an old receipt still scans."
- Agent 12 argues against its own thesis: (1) **Permission must be earned or it is a placebo** — "A permission-to-close system that is quietly 100% broken is not a lower-risk product than a retrieval system — it is a **higher**-risk one, because the failure is discovered only at the worst possible moment." (2) The user's own standard forbids it — "final must be cold-look-proof"; a placebo survives every warm look and fails the first cold one.
- **Resolution: permission-to-close IS the real product, and it must be backed by at least one demonstrated restore — a demonstration, not a promise (DR-1).**

### Agent 10's UX findings / levers that raise adoption odds
- **The tab bar wins today and hoarding is completely rational**: "A tab does not point at the work — it **contains** the work. The scrollback is the memory. Closing it destroys the only copy." No UI polish beats that until closing genuinely stops destroying state. **The registry's job is to make hoarding irrational.**
- **But the tab bar is lying on 3 of its 4 jobs:** the title lies (`⠐ Claude Code` = zero information); the count lies (21 tabs = 7 projects); liveness lies (5 of 21 sessions were empty failed `/acos-handoff` stubs wearing a `✳` glyph). "The window doesn't have to beat a good tab bar. It has to beat a lying one." But it must win question 3 — "what was I doing in there?" — and only if the next-action line is genuinely good.
- **The highest risk in the whole project (agent 10, pointed upstream):** "If the close skill cannot reliably produce a <=90-char next-action headline, the row's payload collapses to a truncated paragraph and the window loses to the tab bar on question 3. **The entire design rests on that one sentence being good.**" Real `Next step` fields run **400–800 characters**. **The registry cannot truncate its way to a headline — it must be generated.** Truncating the 2026-06-04 example (twelve options in one field — "Twelve options is zero options") yields pure noise.
- **The user already hand-built this registry today, under duress, and chose the schema:** `OPEN-CLAUDE-SESSIONS-2026-07-14.md`, columns `| SID | What it's working on | Status | Resume anchor |`. He did NOT pick description, branch, or health. Agent 10: "The strongest artifact in the investigation... Match his choice; don't out-clever it."

---

## 6. Prerequisites Before Any Build (COMPLETE — gates everything; "Ordered. Do not skip 1 or 2.")

1. **ASK ZEE WHY HE DOESN'T CLOSE TABS.** One question, before anything is built. Agent 04: "If Zee's hoarding is not fear-of-loss but something else (context-switch cost, 'the tab IS my todo list'), the receipt treats the wrong disease... Cheapest test: ask him why he doesn't close... I inferred his motive from artifacts; I did not ask." Agent 12 independently: "My reading (2 tabs, no crisis) may be a quiet Tuesday, not the steady state." Two agents, two lenses flag the design's central premise as inferred, not verified. Five-minute check that could save weeks.
2. **Upgrade cmux 0.63.2 -> 0.64.18. Then re-scope.** Agent 12: "the most avoidable failure in this whole project... Building this against a stale platform version risks spending weeks hand-rolling what an upgrade delivers on Tuesday." Re-ask afterwards which stated pains survive hibernation + auto-naming; build only for those. **Guard: verify immediately that the upgrade has not broken in-pane hook firing** (cmux #5427 class; the in-pane hook is the live carrier — daemon injector has ~6 successful FIRED ever vs `rc=2 x1391`). **Also verify what `automation.autoNamingAgent: "auto"` actually calls before enabling auto-naming** — undocumented; OKOA confidentiality question.
3. **Fix residual #10 — pane-scope `eternity-resume-prepend.sh` path (3).** Agent 08: "the single most important pre-existing bug to close **before** building the registry." Rated MEDIUM when two-panes-one-project was rare; the new design's core premise makes it routine → **HIGH**. Agent 08: "If residual #10 is closed and path (3) is removed or pane-scoped, N1's blast radius drops sharply."
4. **Prove ONE restore before asking for one save (DR-1).** Run the close skill on a real project, close the tab, reopen from the registry, have Zee confirm the work resumed. **Ship the recording of that.** "Until it exists, the skill is not shipped." Only antidote to the placebo problem and trust death.
5. **Fix the `head -40` truncation.** One line. Silently dropping **34 of 74 files right now**, inside the block whose header says "these are in NO handoff — inspect FIRST."
6. **Close the orphan-surface-unknown half of P1-F** (`token-watcher.py:1113`). Dormant only because a **90-byte marker file** exists (`.cmux-inpane-inject`). "Deleting one 90-byte marker file re-arms it." Close-skill artifacts are surface-less by construction — the ideal payload for this hole.
7. **Check whether the 147 `/acos-complete` runs were hand-invoked or automated.** Agent 12: "That single datum is doing heavy lifting in my 'deliberate is fine' conclusion. **If a hook fires it, my verdict drops from ~30% to ~15%.**"
8. **Probe how cmux handles `--command` internally** (shell-parsed or exec'd). Agent 09: "If cmux internally passes `--command` to a shell, that is the one place a registry string could still reach a shell." The launch design's security argument routes through this.

---

## 7. Per-Agent Summaries (compressed)

| Agent | SQ / Lens | Key contribution |
|---|---|---|
| 01 | SQ1 Registry model / Tech Feasibility | Killed cmux as substrate by experiment (close DELETES record; 154 RPC methods, no closed-workspace store). Refuted git identity live (3 sibling dirs, 1 upstream, 3 HEADs; only 14/31 are repos). Killed YAML on tooling (no `yq`, no system PyYAML, CSP blocks `js-yaml`). Proved flock load-bearing (25/25 vs 3/25 still-valid JSON). Full schema. *Wrong on C4 (refs positional) — contradicted by its own pasted output.* |
| 02 | SQ1 / Risk (concurrency) | Proved 16/16 rebuild from handoffs alone — de-risks the whole feature. Killed YAML on failure mode (truncated YAML silently returns 19/30). Found real live bug in ACOS atomic-write helper (shared `.tmp`: 180/360 crashes). APFS case-insensitive + `realpath` no casefold (corrects 01/03/08). Inode survives move. flock auto-releases on SIGKILL; mkdir-lock doesn't. *Headline (SQLite) loses: its R1 mass-close storm cannot occur.* |
| 03 | SQ2 Close lifecycle / Tech Feasibility | Proved self-close works (killed live `sleep 400`, no prompt/refusal) and /clear constraint doesn't apply (out-of-band socket RPC, no daemon). WAL-commit ordering, 7-check verification gate, fail-safe framing: "the tab vanishing IS the success signal." Existing resume prompt is ephemeral/consumed-on-use (live count: 0). *Headline key (git) refuted by 01.* |
| 04 | SQ2 / Risk (data loss) | Natural experiment: code 8/8 = 100% vs prose 8/18 = 44% — most important design input. Measured 55% dangling pointers, ~90% loss. Found fidelity mechanism silently truncating (74 claimed, 40 listed). Reframed close skill: "What dies when the tab closes is the reasoning — not the files." Trust-receipt spec + blind round-trip verifier. Flagged prerequisite #1: ask him why. |
| 05 | SQ3 cmux launch / Tech Feasibility (EMPIRICAL) | Best empirical work in the swarm. Argv = one auto-submitted multi-line message (5/6); `cmux send` shreds prompts — disqualified. **Contradicted stored ACOS memory on the paste mechanism (it is inverted).** Proved no dedup, `--cwd` accepts bad paths, env-stripped external processes drive the socket, `current_directory` tracks live cwd. Found trust-gate hazard; reported unexplained 1/6 drop honestly incl. a disproved hypothesis. Settles C4. |
| 06 | SQ3 / Integration | `cmux identify --surface` FAILS OPEN — kills the obvious liveness check. The un-lie-able join PID->cwd->tty->surface. The namespace fix (`ls -t` at `core.sh:87` is non-recursive ⇒ subdir invisible ⇒ why `archive/` is already safe). 6-rule Eternity coexistence contract. Pane forked by cmux app ⇒ registry launch can't inherit stale binding. Measured SessionStart eviction loop (450 files, 0.569s, growing forever). Found the HIGH doc drift: live hook not where CLAUDE.md says. |
| 07 | SQ4 Reuse vs rebuild / Integration | Found the architectural fault line: Eternity's durable path is keyed to a live OS PID with a `claude_lstart` guard refusing it once the process dies. "Eternity is **pane-durable**; the new skill must be **pane-independent**." Confirmed cross-project gap real after adversarial search. `/acos-complete` is the true prior art (80% of the mechanics). `status: parked` is a clean unused sentinel (census of 172 handoffs). Three doc-drift instances. |
| 08 | SQ4 / Risk (contamination) | Root-cause taxonomy (C1–C7) — most durable deliverable. Proved `sanitize(cwd)` non-injective (5 paths -> 1 key; 4+ keys for one project). Found P1-F still HALF fail-open in live code, dormant only via one 90-byte marker. Named residual #10 the #1 prerequisite; re-rated MEDIUM -> HIGH. Self-expiring marker = most transferable pattern. Fencing-token discipline: validate at the consumer, not the producer. |
| 09 | SQ5 Browser UI / Tech Feasibility | Ran the injection attack; list-form `subprocess.run` defeats it — real surface is XSS, not shell. Opaque-ID launch bridge caps CSRF at "an unwanted tab opens." Killed `cmux://` (`CFBundleURLSchemes: ["http","https"]` only); explained why `open -a "Google Chrome"` is a correctness rule. House port pattern (8800/8810 -> 8820); gr-server anti-patterns to reject (ephemeral port, idle reaper). "`open` is a count, not a boolean." |
| 10 | SQ5 / User Impact | 21 sessions = ~7 projects; 13 = ACOS 3.0 — SPINE 1's sharpest datum. Found the user's own hand-built registry from this morning + its schema. Killed the green badge on an asymmetry argument. Self-corrected mid-investigation (dirty chronic at 70 -> count not dot; branch unchanged 40 days -> cut it). Named the project's highest risk: the <=90-char headline must be generated, never truncated. Read CHI 2005 in full and used it to reject a feature. |
| 11 | SQ6 Prior art / Competitive | The report's headline: ADOPT, don't build. Found 0.64.11 Hibernation / 0.64.15 auto-resume / 0.64.16 auto-naming (**doc-claimed, untested — on 0.63.2**). Verified native registry exists with empty description field (`lastSessionId` 32/42, `lastSessionFirstPrompt` 3/42; `customDescription` 2/6). `claude agents --json --all` = live only. "Mint identity at spawn, never discover it" (read cmux wrapper source). Exclusion lists; snapshot-the-inert/replay-the-gated-live rule; the autosave-at-shutdown killer hit by two mature tools. |
| 12 | SQ6 / User Impact (abandonment) | The honest verdict: ~30% at day 60. Proved hot path alive (63/64, median 190s) vs cold path graveyard (~10/17 never read; 17/17 dangling, 5 weeks unnoticed) via atime/mtime. Killer inference: bugs fixed map actual use. Reconciliation: "Deliberate is not dead. Deliberate-with-deferred-payoff is dead." Reframed the design (C8): make the window how he OPENS; close never a precondition. Argued the just-in-case thesis and against it with equal force. Died twice; wrote evidence to disk before analysis and said so. |

---

## 8. Data Gaps (must re-verify before building)

### Structural gaps (affect the recommendation)
- **NOBODY TESTED cmux 0.64.x.** Agent 11 is on **0.63.2**; verifying restore/hibernation/auto-naming required quitting cmux + killing live sessions. **Every adopt-side claim — the entire C7 headline — is a documentation claim.** The single largest gap; the reason "upgrade and re-scope" is a prerequisite rather than a conclusion.
- **Nobody tested a cmux app restart** (agents 01 and 11 both declined). **Whether `customDescription` survives a restart is unresolved** — the docs' restore list *conspicuously omits* titles/descriptions even though the snapshot file plainly contains `customTitle`/`customDescription`. Agent 01 used the session-restore file as a proxy, marked restore *Probable*. **Testable and worth testing — the description-as-registry-key idea depends on it.**
- **The design's central premise is inferred, not verified** — nobody asked Zee why he doesn't close tabs (agents 04, 12).
- **Nobody measured the actual close rate** (premise of C1's storage debate). Agent 02: "Contention rate unmeasured." Agent 04: "If close is rare, the round-trip test's cost is irrelevant... I could not determine the expected rate."
- **No telemetry correlates handoff quality with resume success.** Agent 04: "This is the measurement the system most needs and lacks — and precisely why the silent killer stayed silent. If one thing gets instrumented, make it this."

### Tooling gaps that shaped the research
- **WebSearch/WebFetch unavailable in subagent context throughout** (agents 10, 12). Working fallback: Bash `curl` -> Crossref API for DOI resolution + direct PDF fetch from author faculty pages; DuckDuckGo/Bing block scripted queries, Google hits Cloudflare, Semantic Scholar rate-limits. Agent 12 reached HN Algolia API by `curl`. Operational note for future swarms.
- **Agent 12 died twice mid-flight** to API failures; wrote raw evidence to disk before analysis (its Recommendation appears mid-file); got one substantial HN thread before the cut.
- **Agent 04's external lens returned nothing** — its delegated web-research subagent terminated without delivering; agent 04 cited zero external sources rather than smuggle in half-remembered ones, marked every general principle *Probable* (the right call).

### Unverified specifics
- **Agent 05's unexplained 1-in-6 prompt drop.** First multi-line argv launch rendered correctly but Claude replied "I don't see an actual user message... The system context shows hooks ran successfully." Wrapper hypothesis (claude zsh/doppler wrapper mangling the arg) tested and **disproved**; 3 further trials 3/3. **Total 5/6, cause unknown.** The `"hooks ran successfully"` phrasing points at the `UserPromptSubmit` chain possibly racing prompt delivery on a cold start. Not root-caused.
- **Does `workspace.close` prompt when Claude Code specifically is foreground?** Agent 03 probed with `sleep 400` only; "Testing on a live Claude requires sacrificing a session." — **the single highest-value remaining test.**
- **Closing the LAST workspace in a window** — untested; may close the window or quit cmux.
- **How cmux handles `--command` internally** (shell-parsed vs exec'd) — "the one place a registry string could still reach a shell." (agent 09)
- **A cmux-spawned pane's env could not be read directly** — `ps eww` returns no environment at all on Darwin 24.5 for any pane shell; agent 06's env-inheritance claim rests on process ancestry.
- **SessionEnd grace period on `workspace.close`** — inferred (Probable) from the instant kill; not instrumented.
- **No launchd-context TCC test** — agent 01 asserts `~/.acos/` is TCC-exempt (dotfile in `$HOME`, not `~/Documents`) but did not read it from a launchd-spawned process. Probable.
- **Crash/power-loss durability not empirically tested** — the `fsync`-before-rename requirement rests on POSIX/LWN/SQLite docs.
- **No contamination scenario executed** — agent 08 was read-only; Incident 7's end-to-end sequence is Probable (gate semantics Verified, sequence inferred).
- **147 `/acos-complete` runs: hand-invoked or hook-fired?** Nobody checked; moves the verdict ~30% -> ~15% if hook-fired.
- **17-vs-18 resume-file population discrepancy** (agents 04 vs 12) unreconciled but immaterial; both agree on direction.
- **cmux-resurrect (`crex`)** — exclusion list and storage path not in README; maturity/maintenance unknown; single-vendor.
- **`~/.claude/projects/` is a lossy hint, not a decoder** — spaces and dots both collapse to `-` (`ACOS 3.0` -> `ACOS-3-0`); needs glob-disambiguation against the filesystem.
- **Nobody enumerated projects outside `~/Documents/Vibe Coding/`** — real work also lives in `~/Documents/OKOA/`, `~/okoa-labs/`, `"OKOA Website"/{dev,stable}`. **The true project set spans multiple parents — enrollment cannot be scoped to one root.**
- **Deliberately not cited because never verified:** Chang et al. "When the Tab Comes Due" (CHI 2021, never searched); Altmann & Trafton memory-for-goals (drafted then removed); Mark, Gudith & Klocke (CHI 2008, "~23 minutes" — PDF downloaded but not read, not vouched for); JetBrains/VS Code recent-project row contents; Arc Spaces auto-archive interval; cry-wolf/warning-fatigue literature; Bergman/Whittaker keeping-vs-finding literature (agent 12 couldn't reach it — just-in-case mechanism claim is "my own inference from local evidence, not literature-backed").
- **Net:** local empirical evidence unusually strong; external evidence thin and honestly labeled. Agent 04's frame: "this machine's own 1,391-failure storm and measured 55% dangling-pointer rate are more probative than any general literature."

---

## 9. Documentation Drift ("the docs are not a trustworthy spec")

Agent 07: "the existing stack's documentation is not a trustworthy integration contract — I had to read the code to get the truth on every material point." SPINE 4's fingerprint: specs nobody executes are specs nobody updates.

| # | Claim | Reality | Severity | Found by |
|---|---|---|---|---|
| 1 | CLAUDE.md: "SessionStart runs `register-session-pid.sh`"; swarm brief points at `.claude/scripts/register-session-pid.sh` | **That file does not exist.** The hook runs `"$HOME/Library/Application Support/acos-token-monitor/bin/register-session-pid.sh"`. In-repo copy at `.claude/scripts/acos-token-monitor-bin-reference/` is byte-identical (`diff` -> IDENTICAL) and **never executed**. | **HIGH** — live hook lives outside the repo, not version-controlled with the project; a repo-only edit is a silent no-op | 06 |
| 2 | Every eternity skill: "At 400k tokens", "Default: 400k" | Live `config.yaml`: **`threshold: 500000`** (`token-watcher.py:90` `DEFAULT_THRESHOLD = 400_000` is only the fallback). | MEDIUM — docs misstate live fire point by 100k / 25% | 06, 07 |
| 3 | `acos-complete/SKILL.md:31`: `.md` is the "current format", "legacy `.yaml` also possible" | **Backwards.** `handoff-agent.md:45` writes `.yaml`; on disk `.yaml` dominant (**77** `type: "emergency-manual"`). New readers must glob both extensions. | MEDIUM | 07 |
| 4 | ACOS memory `reference_cmux_send_submit_paste_absorption`: "Enter absorbed as bracketed-paste soft-newline; send Enter as SEPARATE delayed `cmux send -- '\n'`" | **Mechanism recorded BACKWARDS.** Measured: not too few submits — **too many**: every `\n` submits immediately, fragmenting one prompt into N messages. Prescribed workaround would not have fixed multi-line prompts. **And it propagated:** agent 10 cited it as a "known gotcha" and carried the inverted mechanism into its design. | **HIGH** | 05 (measured); 10 (propagated) |
| 5 | CLAUDE.md: `.claude/skills/acos-handoff/` exists in-project | Does not (`ls` -> No such file); resolves only from `~/.claude/skills/acos-handoff/`. | LOW | 07 |
| 6 | Swarm brief's cmux ground truth: ~23 commands | Real 0.63.2 `--help` lists **~90**, incl. `send`, `read-screen`, `close-workspace`, `select-workspace`, full tmux-compat layer, browser automation subsystem. The brief asked whether `cmux send` exists because "it is NOT in the top-level --help output I saw" — it is, with its own `--help`. **The brief's own snapshot was stale.** | MEDIUM | 05 |
| 7 | Brief's guess: `~/.cmux/` | Real path **`~/.cmuxterm/`** (`claude-hook-sessions.json`). | LOW | 01 |
| 8 | 2026-07-05 audit: "cmux exists only at `/opt/homebrew/bin/cmux`" | It is a **symlink** -> `/Applications/cmux.app/Contents/Resources/bin/cmux`; bundle path canonical, survives Homebrew unlink. | LOW | 06 |
| 9 | `capabilities`: `"access_mode": "cmuxOnly"` | **Misleading** — a fully env-stripped external process drives the socket fine; real access control is the 0600 socket file. Would wrongly discourage the browser-launcher design. | MEDIUM | 05 |
| 10 | ACOS memory `feedback_eternity_cmux_rpc_method_name`: method is `surface.send_text` | **CORRECT** — confirmed present in live capabilities list. Credit where due. | — | 05 |
| 11 | CLAUDE.md: `session-cleanup.sh` (SessionEnd) removes ephemeral state in `.acos/state/` | Accurate, and explicitly an allowlist — never touches the daemon's `state/`. SessionEnd does **nothing** about the **1498-file** daemon dir. | LOW (doc correct; gap real) | 06 |
| 12 | CLAUDE.md PreToolUse chain order | Matches `settings.local.json` exactly; legacy unregistered hooks confirmed unregistered. | — (correct) | 06 |

**Meta-observations:** (a) The stale brief and the backwards memory are the same disease as the 44% prose-execution rate — written knowledge in this system decays silently and is trusted anyway (SPINE 3 + SPINE 4 applied to documentation). (b) The live hook being outside the repo (#1) is the highest-severity item and matches the known trap in `reference_eternity_inpane_hook_hardening_2026_07_06` ("untracked, no git backup"). **Anything the new skill depends on must be version-controlled where it actually executes.**

---

## 10. Audit Trail / Method

- Plan: `.acos/swarm/swarm-20260714-084532/plan.md`; Findings: `.acos/swarm/swarm-20260714-084532/agent-{01..12}/findings.md` (**12 files, ~431,721 bytes, all read in full**); Report: `.acos/swarm/swarm-20260714-084532/synthesis/report.md`.
- Method: conflicts adjudicated by evidence class, privileging agents who ran a command and pasted output over agents who reasoned. Where an agent's own pasted output contradicted its conclusion (C4), the output won. Convergences counted only when agents were blind to each other. **SPINE 2 contains a live, unresolved disagreement (scan vs. enrollment) that the brief's summary had smoothed over; SPINE 1 (six agents on duplication) was not on the brief's list and is the strongest result in the swarm.**
- Isolation held: no agent saw a sibling's output. Cross-agent environmental interference (probe workspaces `ACOS-PROBE-TMP`, `SWARM-TEST-DELETE-ME`, `acos-close-probe`; one agent set `description: ACOS-REGISTRY-PROBE-20260714` on `workspace:1`) was noticed and correctly scoped by agents 01, 03, 05; agent 11 disclosed that one of the two `customDescription` values it censused was written by another swarm agent that day.
- Casualties: 3 agents died to API errors after writing; 1 resumed; agent 12 died twice and wrote raw evidence first (file leads with E1–E9); agent 04's delegated external-research subagent died and agent 04 cited zero external sources rather than fabricating.
- **"Nothing in this report is invented."** Every material claim traces to a numbered agent finding; documentation claims (principally the entire cmux 0.64.x adopt case, C7) are labelled as such at every point of use.