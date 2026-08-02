# Resurrection Protocol — Reconciled Design v1 (2026-07-16)

Synthesis of: the user's confirmed 5-point vision (2026-07-16), swarm report `swarm-20260714-084532` (Digests A–C), and the live machine inventory of 2026-07-16 (Digest D). Rule applied throughout: **where today's live inventory contradicts the report, TODAY WINS** — each such case is flagged. Anything resting only on vendor documentation is marked **UNVERIFIED**.

---

## 0. Today-wins corrections to the report

1. **cmux is already 0.64.19** (report assumed installed 0.63.2, latest 0.64.18, and made "upgrade first" a prerequisite). The upgrade decision is **MOOT**. What survives from that prerequisite: (a) verify the in-pane hook still fires post-upgrade (#5427-class regression risk — the in-pane hook is the live resume carrier); (b) actually test the 0.64.x features, which remain **UNVERIFIED doc-claims** (Agent Hibernation, `terminal.autoResumeAgentSessions`, `automation.workspaceAutoNaming`, `sidebar.showWorkspaceDescription`).
2. **`cmux list-workspaces` is now a legacy alias** for `cmux workspace list`, and on 0.64.19 `workspace list --json` returned real JSON (on 0.63.2 the `--json` flag was silently ignored). The report's belt-and-braces rule stands: prefer `cmux rpc workspace.list`; never parse the text form.
3. **Live capabilities now list ~230 methods** (report: 154), including `surface.resume.get/set/clear`, `session.restore_previous`, `workspace.select`, `workspace.env`, `surface.health`. Presence verified today; **behavior UNVERIFIED** — candidates to simplify focus/launch, to be probed in the Phase-0 battery.
4. **Claude Code 2.1.212** (report: 2.1.209). All six resume-relevant flags re-verified present today (`--resume`, `--continue`, `--session-id`, `--fork-session`, `-n/--name`, `--no-session-persistence`), plus `claude project purge` exists.
5. **Transcripts: 643 non-subagent JSONL / 1.2 GB today** (report: 781 / 1.1 GB). Native persistence remains the adopt-side anchor; counts drift.
6. **Daemon state dir: 963 entries** (report ~1500). Still session-UUID-keyed, still off-limits.
7. **Nothing is built yet** (`~/.acos/registry.d/` absent; no resurrection/close/registry/switcher skill anywhere) — but a cmux workspace titled "Resurrection Protocol" exists at the ACOS 3.0 cwd, and **workspaces 4 and 5 both sit on ACOS 3.0 right now** — SPINE 1's duplicate problem is live today, not hypothetical.
8. **Binary-path gotcha for every script:** `claude` is shadowed twice (broken `_acos_cli` zsh function at `~/.zshrc:215` + a cmux CLI shim on PATH). Scripts must call `/Users/zee/.claude/local/claude` and `/Applications/cmux.app/Contents/Resources/bin/cmux` — absolute, always.
9. **Enrollment ground truth:** 18 `memory/handoffs` dirs across TWO parents (17 under `Vibe Coding/` — including one directly on the `Vibe Coding` root itself, a known anomaly — plus 1 under `Documents/OKOA/`), and 42 known cwds in `~/.claude.json` including Desktop paths. Enrollment cannot be scoped to one parent directory.
10. Two fresh top-level Eternity handoffs (`2026-07-16-emergency-handoff*.yaml`) sit in ACOS 3.0's `memory/handoffs/` — live confirmation that the top-level namespace is Eternity's active territory and must never be written by this system.

---

## 1. Vision point → concrete mechanism

### Vision 1 — ONE MASTER DOCUMENT ("the book")
**The book the user sees is ONE view; storage is sharded.** A single shared file is disqualified by measurement (without a lock, 3/25 concurrent writes survive *while producing valid JSON* — valid-but-silently-wrong is the worst index failure), and per-project files dissolve locking entirely (C1 verdict; agent 08 derived it blind).

- **Store:** `~/.acos/registry.d/<project_uuid>.json` — one file per project, one writer per file. Plus `~/.acos/registry-audit.jsonl` (append-only, one `os.write()` per line).
- **Format: JSON, never YAML** (system `/usr/bin/python3` 3.9.6 has no `yaml`; `yq` not installed; truncated YAML parses silently returning 19/30 records; JSON fails loudly). Never SQLite (opaque binary kills `git diff` + hand-repair; its winning scenario — a mass-close write storm — has zero writers in a force-quit).
- **Write path (every writer):** `tempfile.mkstemp(dir=<target's own dir>)` → write → `fsync(tmp)` → `os.replace(tmp, target)` → `fsync(dir)`. Never a fixed `.tmp` name (house pattern measured 180/360 crashes under contention; unique mkstemp: 0). If a lock is ever needed (compaction only): `fcntl.flock` with `LOCK_NB` + bounded retry, never blocking `LOCK_EX` (macOS has no `timeout(1)`), never the mkdir-lock (survives SIGKILL; flock auto-releases in 0.000s).
- **Identity model (C2, four agents, no remaining disagreement):**
  - `project_uuid` (uuid4), minted **once at enrollment**, stored at `<root>/.acos/project-id` (git-ignored — correct: a fresh clone deserves a new id; that is exactly the Backup/Clone case that refuted git identity live: one upstream repo, 3 toplevels, 3 HEADs, 2 URL schemes; only 14/31 candidate dirs are repos).
  - Lookup index: `realpath(root).casefold()` (APFS is case-insensitive; `realpath` does not casefold; `os.path.normcase` is a no-op on POSIX).
  - Re-link key: `(st_dev, st_ino)` — inode survives rename/move; a dead path usually means relocated → heal, don't tombstone.
  - Git `{branch, commit, dirty_count, remote-normalized}` — nullable captured attribute, **never identity**.
  - **BANNED as identity:** `sanitize(cwd)` (proven non-injective: 5 paths → 1 key; 4+ keys for one project), git remote, workspace UUID (reopen mints a new one), session UUID, title (Claude rewrites titles live — sampled value was a spinner frame).
- **Row fields — every one derived or generated, none hand-typed (SPINE 2):** name = basename(root); status ∈ active | parked | completed | tombstoned (`parked` is a clean unused sentinel — census of 172 handoffs shows only completed/active in use); enrolled_at; `last_verified_at` that decays to "unverified", never to "wedged" (the 2026-07-13 self-expiring-marker lesson); last_close {at, handoff_path, reentry_path, sha256, next_action ≤90 chars}; `lastSessionId` from `~/.claude.json` as an optional hint (42 rows, 32 populated — verified today; the path-mangled keys are a lossy hint requiring glob-disambiguation, never a decoder).
- **"Stays in the book until finished for good":** rows are **tombstoned, never deleted**; deletion is a human act only; no age-based reaper (a handoff is ~10 KB; 1,000 closed ≈ 10 MB — "there is no storage argument for reaping, so don't").
- **The rendered book is generated FRESH at every view** — no persisted master markdown that could go stale ("a stale registry is a lying registry"). Rows failing a link check render **BROKEN in red — never hidden** (C6).
- **`rebuild-registry.py` ships in v1** — the proven pattern (a ~40-line script reconstructed 16/16 project rows from handoff artifacts alone, reading no registry file). "An unproven rebuild path is not a mitigation." A derived index cannot dangle — this deletes the measured 55%-dangling-pointer failure class rather than mitigating it.

### Vision 2 — SAFE CLOSE
**Skill `/acos-safe-close` = a thin router over `close-project.sh`** (SPINE 4: same author, same repo — script-implemented logic ran 8/8 = 100%; prose-specified logic ran 8/18 = 44%). The receipt is printed **by the script from verified return values** — "if the model composes the receipt, the receipt is fiction."

Ordered protocol (report steps 0–10):
```
 0. Write state/stop-<SESSION_ID> in the daemon dir FIRST — the ONLY permitted
    daemon-state write, ever (SPINE 7) — so Eternity cannot fire mid-close.
 1. PARENT writes the intent core: decisions, rejected alternatives, traps,
    open questions, next_action headline <=90 chars. NEVER delegated (a Sonnet
    agent reading git log will confabulate the why — documented failure).
    Stub-first: a thin handoff beats no handoff.
 2. Enrich from disk (git, files, ports, subagents); delegate to handoff-agent
    only if context-starved — via Bash heredoc, NOT Write (Task() subagents are
    policy-blocked from Write).
 3. Write BOTH artifacts CO-LOCATED:
      memory/handoffs/closed/<slug>/handoff.yaml        (type: close-project, status: parked)
      memory/handoffs/closed/<slug>/<slug>.reentry.md
    + git-state snapshot & drift block.
 4. VERIFICATION GATE — agent 03's 7-check gate, all must pass; fail -> STOP,
    tab stays open. (Exact check list to be pulled from agent-03/findings.md at
    build time — not restated here to avoid inventing.)
 5. BLIND ROUND-TRIP: fresh agent, handoff ONLY, no repo access ("if it can
    read the repo it will pass a bad handoff" — the single most likely silent
    failure). Wigum cap 5, then DEGRADE, never halt.
 6. Upsert the registry row (atomic, per-project file). The row ALREADY EXISTS
    (enrollment) — close ENRICHES, never creates (C8 / DR-8).
 7. Read back; assert sha256(handoff) == row.
 8. Cleanup INLINE (SessionEnd will not survive the kill).
 9. Receipt — every line read back from disk after writing (SPINE 3):
    `listed N of M` on every list; `sha256 + re-read OK`; `pointer RESOLVES`
    (stat'd, not merely written); `NOT stashed — working tree untouched,
    survives close` (NO auto-stash — record state, never mutate); a quote of
    the fresh agent's reconstructed next step; `SAFE TO CLOSE THIS TAB` only
    when every check passes.
10. cmux rpc workspace.close '{"workspace_id":"<validated>"}'  — LITERAL LAST
    statement. (Param is workspace_id, not workspace — verified.)
```
Four non-negotiable guards (agent 03): (a) close is the literal last statement; (b) close is gated on the verification gate AND the read-back; (c) target is the **validated** `CMUX_WORKSPACE_ID` (checked `grep -qx` against `rpc workspace.list`) — fail **closed**; never fall back to `identify`'s focused surface (`cmux identify --surface` **fails open** — live, bogus, and known-dead surfaces all return exit 0 with byte-identical output); (d) cleanup runs inline. Added guard from risk #20: count live workspaces first and refuse the auto-close if this is the last workspace in the window (behavior untested).

Fail-safe frame: "the tab vanishing IS the success signal; the tab remaining open with an error IS the failure signal." Every failure branch's action is simply *don't close* — the dangerous quadrant (data lost + tab gone) is unreachable by construction.

**Honest zero-loss accounting:** what actually dies at close is the *reasoning* — files, git tree, `memory/`, `planning/` survive regardless. Safe close exists to capture reasoning; crash protection comes from Vision 5's enrollment + native transcripts, not from this ritual.

### Vision 3 — MENU ON RETURN
The vision says: open Claude Code anywhere, run the Resurrection Protocol, see the book as a menu, pick, continue. The report designed a localhost **browser** window instead. **Menu surface = DECISION POINT DP1** — the evidence settles the row *content* and the focus/launch *mechanics*, not the surface; the report never evaluated an in-terminal menu.

Common engine either way:
- **`resurrect-view.py`** computes the book fresh per request. Liveness is computed live, never a stored flag (a force-quit leaves stale flags): "is project P open?" via claude `PID → cwd` (`lsof -a -d cwd -p <pid> -Fn` — un-lie-able: force-quit removes the process, nothing left to lie); "where is its pane?" via `PID → tty` (`ps -o tty=`) → `cmux tree --all --json`; "which row is this workspace?" via the `[key:<uuid>]` tag appended at the END of `--description` (`<next action> [key:uuid]`, ~45 chars overhead — resolves the 05-vs-10 tension over one ~280-char field); workspace state via `cmux rpc workspace.list` only. Hand-opened untagged workspaces fall back to the process join, **never** cwd string match (`current_directory` tracks the live shell cwd — in-session `cd` breaks it; 2 workspaces share one cwd today) and **NEVER title** (unanimous).
- **Row spec** (agent 10, matching the schema the user hand-built under duress on 2026-07-14 — `| SID | What it's working on | Status | Resume anchor |`): project name; the generated `next_action` line (≤90 chars, imperative verb first, **generated at close, never truncated from a long field** — real Next-step fields run 400–800 chars and "twelve options is zero options"); facts, never verdicts: dirty **count** not a dot (tree chronically dirty — 70 files, 40 days on one branch — an always-on dot is invisible), amber staleness note, clickable `file://` handoff link ("the proof is one click away" beats "a badge says trust me"). Tiers: **OPEN NOW / RECENT / COLD (>30d — measured bimodal, empty chasm 28d–90d) / NO HANDOFF / ARCHIVED** (last three collapsed). **CUT:** git branch, last action, health score, static description (search fodder only). **NEVER a green badge** — a false green costs trust in the entire registry permanently; red/amber only; silence means fine.
- **Pick routing** (every path obeys SPINE 1 — focus, never duplicate — and risk #7 — never continue project X inside a session whose cwd is project Y):
  - (a) picked root == current session's `realpath(cwd)` → re-resolve the newest `.reentry.md` **at open time** (never a cached filename — Eternity writes newer handoffs continuously) and continue inline. This is the vision's literal flow.
  - (b) project open elsewhere → **FOCUS** its workspace (`cmux rpc workspace.select` — method present in live capabilities today, behavior UNVERIFIED, probed in Phase 0). Never create a second (cmux does NO dedup — verified: bare open created a 5th ACOS 3.0 workspace while 4 were open).
  - (c) not open anywhere → **launch**:
    ```bash
    CMUX=/Applications/cmux.app/Contents/Resources/bin/cmux   # ABSOLUTE, always
    CLAUDE=/Users/zee/.claude/local/claude                    # ABSOLUTE, always
    [ -d "$CWD" ] || fatal   # new-workspace --cwd silently accepts bad paths (exit 0)
    "$CMUX" new-workspace --name "$TITLE" \
        --description "$NEXT_ACTION [key:$UUID]" \
        --cwd "$CWD" \
        --command "$CLAUDE \"\$(cat '$REENTRY')\""
    ```
    **Argv is the only prompt route** — a multi-line reentry lands as ONE auto-submitted message (verified 5/6); `cmux send` and `surface.send_text` submit at every `\n`, shredding a 40-line prompt into 40 messages — disqualified. Then **verify delivery** via `read-screen` for a marker + one retry (unexplained 1-in-6 silent drop, cause unknown, leading hypothesis disproved). Detect the trust gate via `read-screen` for "Quick safety check" — untrusted dirs look launched but never deliver the prompt. **No registry-derived string ever enters `--command`** — only the skill-controlled reentry file PATH; names/next_action go in `--name`/`--description`, where the attack surface is XSS-not-shell (verified: hostile strings round-trip verbatim; list-form subprocess defeats shell injection).
  - Side effect everywhere: **the registry writes the tab's own title and description** — the tab bar stops saying `⠐ Claude Code` and starts saying the actual next action. "The window doesn't just replace the tab bar — it repairs it."
- **Optional browser surface** (only if DP1 selects it): `resurrection-server.py` — stdlib `ThreadingHTTPServer`, `127.0.0.1:8820` FIXED (house sequence 8800 type-forge → 8810 image-builder; 8820 verified free); started by the skill, **never launchd** (bare launchd PATH cannot find cmux — the 2026-07-05 outage class); **NO idle reaper, with a code comment saying so** (idle IS the steady state); singleton reuse via `GET /api/whoami` on EADDRINUSE — never silently port-hop; `POST /api/launch` accepts an **opaque ID only** (server resolves the path — caps CSRF at "an unwanted tab opens"); validate `Origin` + `Host` + `Content-Type: application/json`; **do not copy `typeforge_serve.py`'s `Access-Control-Allow-Origin: *`**; render every registry-derived string with `textContent`, never `innerHTML`; open with `open -a "Google Chrome"`, never bare `open` (cmux claims `http`/`https` at `LSHandlerRank: Default` — bare `open` may hand the URL to cmux); poll `/api/projects` every 5s while visible, stop on `document.hidden`; no SSE.

### Vision 4 — THE LOOP REPEATS
- Re-close any time: `close-project.sh` upserts by `project_uuid` — add-vs-update is a **pure function of the filesystem** (`project_uuid ∈ registry.d ? UPDATE : ADD`), needing no memory of a prior resume (Change 2; a breadcrumb key fails exactly when the tab was force-killed).
- Resume flips `status: parked → active`; `last_verified_at` refreshes on every render contact.
- **Finish for good:** a finish verb in `/acos-resurrect` sets `status: completed` — the row is hidden in the collapsed ARCHIVED tier, never deleted. Existing `/acos-complete` is left untouched (it is the true prior art — 80% of the close mechanics — but its archive/ pointer-rewrite flow is exactly the mechanism that produced the 17/17 dangle; our co-located `closed/<slug>/` namespace never re-enters it).
- **Eternity boundary:** Eternity keeps owning SAME-PANE continuation (auto /clear at the live 500k threshold — the docs' "400k" is drift item #2); Resurrection owns CROSS-WINDOW, days-later park+resume. Eternity is **pane-durable** (per-PID pointer with a `claude_lstart` guard that refuses the pointer once the process dies — by design); Resurrection is **pane-independent**. Opposite invariants, not a configuration difference — the user's original instinct not to reuse `/acos-resume-prompt` was right and is sharper than stated (Change 5). Namespaces are fully disjoint (C5): the co-located `closed/` subdirectory is invisible to Eternity's non-recursive `ls -t memory/handoffs/*.md *.yaml` glob (confirmed live today at `core.sh:87`); `.reentry.md` never `.resume.md` (`.resume.md` is addressable by Eternity's pointer path); the one contact point is `state/stop-<sid>` at close step 0.

### Vision 5 — PURPOSE: never lose work; closing must FEEL safe
- **Force-quit safety WITHOUT ritual:** enrollment-on-first-sight means the book is populated before any close ever runs — the acceptance test is agent 12's: `kill -9` every cmux tab, reopen, nothing is missing that a graceful close would have provided *for the registry*. Plus ADOPTED native persistence: 643 transcripts on disk today; `claude --resume <uuid>` replays a real transcript; persistence is the default. Plus Eternity's emergency handoffs, untouched. (Honest caveat: a true force-quit still loses reasoning not yet captured anywhere — safe close is what brings that to zero, which is why it must be cheap.)
- **Closing FEELS safe because it IS verified:** script-printed receipt read back from disk; blind round-trip quote of the reconstructed next step; `SAFE TO CLOSE THIS TAB` only on full pass; the tab staying open is itself the failure signal; and the **DR-1 gate — prove ONE full restore on a real project and keep the recording before asking for the habit.** "Until it exists, the skill is not shipped." Permission-to-close is the real product and it must be a demonstration, not a promise.
- **Adoption shape (agent 12):** "Deliberate is not dead. Deliberate-with-deferred-payoff is dead." The menu is the WAY IN (immediate payoff on every open — the 147 hand-run `/acos-complete` invocations prove the user performs rituals whose payoff is immediate); closing becomes the safe byproduct. No nagger, no notifier.
- **Fewer freezes:** closing cures tab COUNT and the 13-tabs-of-one-project confusion (SPINE 1 — one row per project: 21 live sessions → ~7 rows; 508 recorded ACOS 3.0 sessions → 1 row); cmux Agent Hibernation (**UNVERIFIED** doc-claim, opt-in, DP4) attacks RAM/CPU independently.

---

## 2. ADOPTED (exists — do not rebuild)
- **Claude Code native persistence** (verified today on 2.1.212): transcripts, `claude --resume <uuid>`, `--session-id` (mint identity in advance), `-n/--name`, `--fork-session`, `claude project purge`.
- **`~/.claude.json` `projects{}`** — 42 rows / 32 `lastSessionId`, survives process death (exact match today). Used as a lossy hint only.
- **cmux 0.64.19, already installed:** the CLI/RPC launch+focus surface (`new-workspace --name --description --cwd --command`, `rpc workspace.list/close`, `read-screen`, `tree --all --json` — verified on 0.63.2; re-verified via Phase-0 battery on .19). Feature adopts pending verification (**all UNVERIFIED doc-claims**): Agent Hibernation (DP4), `terminal.autoResumeAgentSessions`, `automation.workspaceAutoNaming` (DP3 — confidentiality gate: what model does `autoNamingAgent: "auto"` call?), `sidebar.showWorkspaceDescription`.
- **The existing handoff CONTENT model + handoff-agent** — the one artifact no vendor ships is the semantic handoff, and it is already built (21 active + 151 archived). Every past retirement was an addressing failure, never the content model.
- **Eternity Protocol, unchanged** — except the two prerequisite fixes it needs regardless.
- **Prior-art lessons, not vendored:** cmux-resurrect/crex (closest artifact; maturity unknown); replay allowlist of exactly one entry (`claude --resume <uuid>` / the argv reentry) — never arbitrary commands; never persist environment, secrets, shell history, or scrollback (the JSONL transcript is strictly better); never blind-overwrite a snapshot — refuse to write one with fewer entries than the previous without an explicit flag (the tmux-continuum/cmux #2895 killer, i.e., SPINE 3 arriving from external evidence).

## 3. BUILT (new; all version-controlled in the ACOS 3.0 repo, where it executes)
- `.claude/scripts/resurrection/registry_lib.py` — atomic write path, schema, casefold index, inode re-link, tombstone.
- `.claude/scripts/resurrection/enroll-project.sh` — SessionStart enrollment (marker-gated) + cwd==root assertion.
- `.claude/scripts/resurrection/rebuild-registry.py` — v1 requirement; also the DP5 seeder.
- `.claude/scripts/resurrection/close-project.sh` — steps 0–10 + receipt.
- `.claude/scripts/resurrection/resurrect-view.py` — the book, computed fresh (liveness joins, tiers, BROKEN flags).
- `.claude/scripts/resurrection/launch-project.sh` — focus-or-launch + argv delivery + read-screen verification.
- `.claude/skills/acos-safe-close/SKILL.md` — thin router (parent writes intent core, script does everything else).
- `.claude/skills/acos-resurrect/SKILL.md` — the menu + finish verb.
- (DP1-conditional) `.claude/scripts/resurrection/resurrection-server.py` — the 8820 browser view.
- Data: `~/.acos/registry.d/`, `~/.acos/registry-audit.jsonl`, `<root>/.acos/project-id` per project, `memory/handoffs/closed/<slug>/` per project.

## 4. NOT BUILT (explicit, with the evidence that kills each)
- **Registry rows created by closing** (empty at the force-quit — its only moment; DR-8).
- **Any hand-maintained/hand-typed field, or prompting the user to fill descriptions** (native description fields measured 3/42 and 2/6 populated — "humans do not fill in description fields").
- **Green badges, health scores, verdicts of any kind** (a naive verifier would stamp ✓ today over 74 uncommitted files; false green = permanent trust death → hoarding forever).
- **A notifier/nagger** (agents 10, 12).
- **Any write to the daemon state dir except `state/stop-<sid>`**; any second handoff/resume writer in Eternity's namespaces; any `*.resume.md`; any top-level `memory/handoffs/*.{md,yaml}` (SPINE 7, C5).
- **cmux as the registry substrate** (closing a workspace DELETES its record from disk — verified; no closed-workspace store in any RPC method; upstream snapshot fragility #2387/#2895/#2125).
- **YAML or SQLite storage**; a single shared registry file; the house fixed-`.tmp` atomic-write helper.
- **Recency as a selector** (`ls -t` may only order candidates that already passed exact identity match — SPINE 6).
- **Auto-stash at close** (closing a tab does not touch the tree; stashing is a mutation creating new loss modes).
- **Naive filesystem-scan membership** (enrolls `memory/`, `planning/`, `learning-curve/` strays; `~/.claude/projects/` is polluted AND misses real work).
- **Idle reaper or port-hopping on the server; launchd hosting; `ACAO: *`; `innerHTML`.**
- **Per-session rows; title-based matching; keep-alive daemons (screen/abduco/dtach pattern — "the disease, not the cure").**
- **Auto-close at a token threshold** — close stays user-initiated (original constraint C1); Eternity keeps owning in-pane continuation.

## 5. Open verification items (UNVERIFIED / doc-claimed / unknown)
- All cmux 0.64.x features (hibernation, auto-resume, auto-naming incl. what model it calls, sidebar descriptions) — doc-claimed only, now testable locally since 0.64.19 is installed.
- `customDescription` survival across a cmux app restart (the `[key:uuid]` join across restarts depends on it; docs' restore list conspicuously omits it).
- `workspace.close` behavior with a live foreground Claude Code session ("the single highest-value remaining test").
- Closing the LAST workspace in a window (may close the window or quit cmux).
- How cmux handles `--command` internally (shell-parsed vs exec'd) — the launch security argument routes through it.
- `workspace.select` / `surface.resume.*` / `session.restore_previous` behavior (methods present today; untested).
- The 1-in-6 silent prompt drop (cause unknown; mitigated by delivery verification + retry).
- `~/.acos/` TCC-exemption from launchd context (probable, untested — moot unless the server is ever launchd-hosted, which it must not be).
- fsync-before-rename crash durability (docs-based: POSIX/LWN/SQLite).