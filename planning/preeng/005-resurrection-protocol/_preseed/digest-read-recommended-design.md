# Digest: report.md lines 734–1110 (Design Changes, Adopt List, Recommended Design)

Source: `/Users/zee/Documents/Vibe Coding/ACOS 3.0/.acos/swarm/swarm-20260714-084532/synthesis/report.md` (§"Where The User's Stated Design Must Change", §"What Already Exists", §"The Recommended Design"). Original constraints from `/Users/zee/Documents/Vibe Coding/ACOS 3.0/.acos/swarm/swarm-20260714-084532/plan.md`.

## Original constraints (plan.md, for reference)
- **C1** — Close is user-initiated via a skill, not automatic at a token threshold.
- **C2** — Close skill writes handoff + resume prompt, THEN writes/updates registry. Registry write is downstream of, and gated on, a successful save.
- **C3** — "Existing project" case: if previously resumed via resume protocol, close must UPDATE its registry row, not append a duplicate.
- **C4** — Existing resume-prompt generation serves a different purpose; reuse of `/acos-resume-prompt`/Eternity artifacts must be argued, not assumed.
- **C5** — Browser window is view + launch only. Not an editor.
- **C6** — Goal is to stop accumulating tabs; closing must feel *safe* or user keeps hoarding and the skill fails.
- (The report also references a "C7" — post-upgrade, launching a project with no tab is the window's entire unique job.)

---

## 1. The Five "Where The User's Stated Design Must Change" Items

### Change 1: The close skill must NOT create the registry row — it may only enrich it
- **User asked:** close skill "writes a handoff + a resume prompt, then **adds or updates** the project in a registry" (C2: registry write downstream of, gated on, successful save).
- **Report says instead:** **Enroll on first sight (marker-gated); the close skill enriches.** The row exists whether or not any ritual ever ran.
- **Why:** In a force-quit — the user's own stated failure mode — the close skill never runs, so a close-populated registry is **empty at exactly the moment it exists to serve** (agent 12, DR-8). Agent 04: close fires when context is nearly exhausted, so the moment fidelity matters most is when the session can least deliver it (Risk #3, High). Agent 02 **proved** the rebuild works (16/16).

### Change 2: "Existing project → update the row" needs no memory of a prior resume
- **User asked:** "if the project was resumed using resume protocol before" — parenthetical implies add-vs-update detection depends on remembering a prior resume.
- **Report says instead:** Add-vs-update is `project_uuid ∈ registry ? UPDATE : ADD` — a pure function of the filesystem. **Identity lives in `<root>/.acos/project-id`, not in session state.**
- **Why:** Agent 03: *"A breadcrumb-based key would fail exactly when it's needed most (tab force-killed, breadcrumb never written — the user's stated status quo)."*

### Change 3: The description cannot be a description
- **User asked:** a registry "with each project's **description**, handoff location, and resume-prompt location."
- **Report says instead:** Honour the word, rebind the field. The rendered payload is a **generated `next_action` headline, <=90 chars, imperative verb first**. The static blurb survives only as **search fodder**, never as rendered pixels on a hot row.
- **Why:** Three agents converge. Agent 11 (census): `lastSessionFirstPrompt` populated **3/42**, `customDescription` **2/6** — *"Humans do not fill in description fields."* Agent 10: *"He knows what FruitSync is; he does not know what he was doing. A static blurb is written once and never read again."* Agent 12: populate automatically or it decays. Flagged: *"This is the single highest-risk dependency in the design — see the Adoption section."*

### Change 4: Launching is the wrong verb; focusing is the right one
- **User asked:** a browser window "for **viewing and launching**".
- **Report says instead:** The window's primary verb is **FOCUS**. A click on an open project must focus the existing workspace and must **never** create a second. Launch happens only when the project has **no** tab — which, post-upgrade, is the window's entire unique job (C7).
- **Why:** **SPINE 1 — six agents.** The problem is 13 tabs of one project. Agent 05 proved cmux does **no dedup**. Agent 06: focus-not-duplicate is a **correctness** requirement — two panes on one project is the exact input that makes Eternity's last-resort tier hand pane A's resume to pane B (residual #10, still open in live code). Agent 08: the stated design converts that rare accident into the default workflow. Agent 10: *"This single rule is worth more than every other feature in the window."*

### Change 5: Do not reuse `/acos-resume-prompt` — user was right, and it's sharper than stated
- **User said:** the existing resume-prompt generation "serves a different purpose" (C4).
- **Report says instead:** Correct, and **the break is definitional, not stylistic.** Agent 03: the artifact is written to `pending-resume-<session_id>.txt` **outside the repo**, keyed by session ID, **consumed-on-use** — live count right now: **0**, all moved to `consumed/`. Its content literally asserts *"This prompt was auto-injected after /clear ran. The user has not typed anything since."* Agent 07: Eternity's durable path is **keyed to a live OS PID** with a `claude_lstart` guard that deliberately refuses the pointer once the process dies — *"Closing the cmux tab kills the claude process, which invalidates the pointer, which severs eternity's resume path by design."*
- **The sharpening:** Eternity's docs do claim days-later durability — but the qualifier is *"in this same pane."* **Eternity is pane-durable; the new skill must be pane-independent.** Opposite invariants, not a configuration difference. Agent 07: *"This single fact justifies a separate addressing scheme and is the cleanest one-sentence answer to 'why can't we just use Eternity?'"*

---

## 2. The Recommended Design (complete)

### Identity
```
identity      = project_uuid (uuid4), minted ONCE at enrollment
marker        = <root>/.acos/project-id      # one line, the UUID, nothing else
lookup index  = realpath(root).casefold()    # APFS is case-insensitive; realpath does NOT casefold
re-link key   = (st_dev, st_ino)             # inode survives rename/move -> heal, don't tombstone
git           = {branch, commit, dirty, remote} -- NULLABLE captured attribute, NEVER identity
BANNED        = sanitize(cwd) as identity; git remote/repo as identity; workspace UUID as identity;
                session UUID as identity; title as any kind of key
```
`.acos/project-id` is git-ignored (`.acos/` is globally ignored) and agent 01 argues this is **right**: identity is local, and a fresh `git clone` legitimately deserves a *new* id — exactly the Backup/Clone case that refuted git-based identity.

### Storage
```
~/.acos/registry.d/<project_uuid>.json     # ONE FILE PER PROJECT. One writer per file.
~/.acos/registry-audit.jsonl               # append-only, one os.write() per line, no buffering
```
- **Write path:** `tempfile.mkstemp(dir=<target's own dir>)` → write → `fsync(tmp)` → `os.replace(tmp, target)` → `fsync(dir)`. **Never** a fixed `.tmp` name (agent 02 measured **180/360 crashes** from the house pattern). Same directory ⇒ no `EXDEV`.
- **No lock on the write path** (one writer per file makes it unnecessary). If a lock is ever needed for compaction/GC: `fcntl.flock` with `LOCK_NB` + bounded retry, **never** blocking `LOCK_EX` (macOS has no `timeout(1)`).
- **Not YAML.** Two agents killed it independently — tooling (no `yq`, no system PyYAML, Artifact CSP blocks `js-yaml`) and failure mode (truncated YAML silently returns 19/30).
- **`rebuild-registry.py` ships in v1**, not later. Agent 02 proved it: **16/16 from handoffs alone**. "An unproven rebuild path is not a mitigation."
- **GC: tombstone, never delete.** Inode re-link first; no match ⇒ `status: tombstoned`, row and pointers survive; UI hides, never destroys; resurrect on contact; **deletion is a human act only.** No age-based auto-purge — the 60s-reaper precedent shows automated reapers steal live state. A handoff is ~10 KB; 1,000 closed projects ≈ 10 MB. **"There is no storage argument for reaping, so don't."**
- **Every row carries `last_verified_at` and decays to "unverified", never to "wedged"** (agent 08's C4 — the self-expiring-marker lesson from 2026-07-13, "the single most transferable design pattern in this codebase").

### Membership / enrollment
```
ENROLL on first sight, gated by a marker: <root>/.acos/  OR  CLAUDE.md  OR  memory/handoffs/
NOT on close (12/DR-8).  NOT by naive scan (01/F4, 10/F8).
The close skill only ENRICHES.
```

### Namespace contract (mechanically checkable)
```
memory/handoffs/closed/<slug>/handoff.yaml       # type: close-project, status: parked
memory/handoffs/closed/<slug>/<slug>.reentry.md  # CO-LOCATED -> no cross-directory pointer
~/.acos/registry.d/<project_uuid>.json

FORBIDDEN, absolutely:
  memory/handoffs/*.{md,yaml} at top level   -> Eternity's ls -t binds it within 300s
  *.resume.md anywhere                        -> addressable by Eternity's pointer path
  ~/Library/Application Support/acos-token-monitor/state/**  -> Eternity's private namespace

PERMITTED, exactly one, write-only:
  state/stop-<SESSION_ID>   -> written FIRST, so Eternity cannot fire mid-close
```
Both artifacts co-located in one subdirectory is the fix for C6: **no cross-directory pointer exists, so none can dangle.**

### Close protocol (ORDERED; every load-bearing step is a script, not prose)
```
 0. Write state/stop-<sid>.                          # disarm Eternity FIRST (06 rule 3, 08 N6)
 1. PARENT writes the intent core.                   # decisions / rejected alternatives / traps /
                                                     # open questions / next_action headline <=90ch
                                                     # NEVER delegate this (03 F7, 04 F5)
                                                     # Stub-first: a thin handoff beats no handoff
 2. Enrich from disk (git, files, ports, subagents). # delegate to handoff-agent if context-starved
                                                     # (04 #3) -- via Bash heredoc, NOT Write
 3. Write handoff + .reentry.md, co-located.         # + git-state snapshot & drift block
 4. VERIFICATION GATE -- 7 checks, all must pass.    # 03's spec; fail -> STOP, tab stays open
 5. ROUND-TRIP: blind fresh agent, handoff only.     # Wigum cap 5, then DEGRADE, never halt
 6. Upsert the row (atomic, per-project file).
 7. Read back; assert sha256(handoff) == row.
 8. Cleanup INLINE.                                  # SessionEnd will not survive the kill (03 F8)
 9. Print the receipt -- BY THE SCRIPT, from verified return values.
10. cmux rpc workspace.close '{"workspace_id":"<validated>"}'   # LITERAL LAST STATEMENT
```
**Four non-negotiable guards (agent 03):** (a) close is the literal last statement; (b) close is gated on the verification gate **and** the read-back; (c) target is the **validated** `CMUX_WORKSPACE_ID` — fail **closed** if it can't be validated, and **never** fall back to `identify`'s *focused* (user may have focused a different tab by the time saving finishes → you'd close the wrong project); (d) cleanup runs inline.

**Deliberate fail-safe (agent 03's best insight):** *"the tab vanishing IS the success signal; the tab remaining open with an error IS the failure signal."* Every failure branch's action is simply **don't close**. The dangerous outcome — data lost, tab gone — is unreachable by construction.

**The receipt (agent 04's spec) — every line read back from disk after writing:**
- `SAFE TO CLOSE THIS TAB` prints **only** when every check passes. *"The receipt is worthless the first time it says SAFE and is wrong."*
- **`listed N of M`** on every list. *(Fix `head -40` first — it is silently dropping 34 of 74 files right now, inside the block whose header says "these are in NO handoff — inspect FIRST".)*
- `sha256` + `re-read OK` = artifact reopened after writing. `pointer RESOLVES` = the path was `stat`'d, not merely written.
- **`NOT stashed — working tree untouched, survives close`** — states the true safety property, pre-empts the actual fear. **Do not auto-stash** (agent 04, Risk #10 — closing a tab does not touch the tree; stashing is a mutation creating new loss modes). Agent 03 suggested `git stash create` as safe (mutates nothing) but agent 04's fail-open principle is the better guide: record state, don't mutate.
- **The round-trip quotes the fresh agent's reconstructed next step** — the only line answering "will I get my head back?", auditable in one glance.
- If the model composes the receipt, **the receipt is fiction**.

**Round-trip verifier's one non-negotiable property (agent 04):** it must be **blind** — handoff only, no repo access. *"If it can read the repo it will reconstruct context the handoff lacks and pass a bad handoff. This is the single most likely way this feature silently fails."*

### Launch (all numbered rules)
```bash
CMUX=/Applications/cmux.app/Contents/Resources/bin/cmux     # ABSOLUTE. Never bare `cmux`.
CLAUDE=/Users/zee/.claude/local/claude                      # ABSOLUTE. `claude` is a zsh fn.

[ -d "$CWD" ] || fatal    # new-workspace --cwd does NOT validate; it silently succeeds (05 F6)

# 1. Is it already open?  -> FOCUS, never launch a second.   (SPINE 1)
# 2. Re-resolve the newest .reentry.md at OPEN time.         (06 rule 5 -- never cache a filename)
# 3. Launch, prompt via ARGV = ONE auto-submitted message.   (05 -- verified 5/6)
$CMUX new-workspace --name "$TITLE" \
                    --description "$NEXT_ACTION [key:$UUID]" \
                    --cwd "$CWD" \
                    --command "$CLAUDE \"\$(cat '$REENTRY')\""
# 4. Verify delivery (read-screen for a marker) -- do NOT assume.  (05 F12: 1/6 silent drop)
```
- **Why argv and not `cmux send` (agent 05's most important negative result):** `cmux send` submits at **every** `\n` — a multi-line resume fragments into separate messages, the first with no context and the rest **queued** (`Press up to edit queued messages`). *"A 40-line resume prompt becomes 40 messages."* `cmux send` and `surface.send_text` are **disqualified** for prompt delivery. **Argv is the only route that preserves the prompt.**
- **Agents 05 vs 06 payload difference — trade-off, not dispute.** Agent 06: inject a single-line trigger (`/acos-project-resume <slug>`). Agent 05: verified the full multi-line body lands as one message. **Resolution: both routes are argv via `--command`** — agent 06's cited fix was derived for the *keystroke-injection* path, which neither route uses. **Take agent 05's mechanism (verified end-to-end) + agent 06's rule 5** (re-resolve at open time, never cache a handoff filename — Eternity writes newer handoffs continuously, so a cached filename is stale the moment Eternity fires). Add agent 05's delivery verification because of the unexplained 1/6 drop.
- **Launch hazard 1 — the trust gate (agent 05, F11):** launching into a directory Claude has not previously trusted halts at *"Quick safety check: Is this a project you created or one you trust?"* — the workspace looks launched but the resume prompt is **never delivered**. Only launch previously-trusted dirs, or detect the gate via `read-screen`.
- **Launch hazard 2 — `--command` shell-parsing (agent 09's flagged gap):** agent 09 **verified** list-form `subprocess.run` defeats injection (launched a workspace named `AGENT09-TEST; touch /tmp/pwned_agent09; echo $(whoami)` — file never created, cmux stored the string verbatim). **But agent 09 did NOT verify how cmux itself handles `--command` internally:** *"If cmux internally passes `--command` to a shell, that is the one place a registry string could still reach a shell."* **Probe this before implementing** — the launch design's whole security argument routes through it.

### Browser window (scoped role: view + FOCUS/launch; launch only when no tab exists)
- **stdlib `ThreadingHTTPServer`, `("127.0.0.1", 8820)`, fixed port** — continuing house sequence 8800 (type-forge) → 8810 (image-builder). Verified free. Started by the skill, **not launchd** (agent 06: bare launchd PATH cannot find `cmux` — root cause of the 2026-07-05 outage; a launchd-hosted UI server reproduces it in a new component).
- **NO idle reaper — put this in a comment so nobody "helpfully" adds one.** Agent 09: *"For a project switcher, idle IS the steady state... A reaper would guarantee the tool is dead exactly when wanted."* An idle stdlib server holds no pool and no model.
- **Singleton reuse, not port-hunting.** On `EADDRINUSE`, `GET /api/whoami`; if it's ours, open Chrome at it and exit 0. **Never silently hop to 8821** — silent port-hopping is the root of the "restart = new port" gotcha gr-server already paid for.
- **`POST /api/launch` accepts an OPAQUE ID only** — never a path, name, or command. Server resolves the path from its own registry copy. Worst case for a successful CSRF: "an unwanted project tab opens" — annoying, not a compromise. That asymmetry is why the ID indirection is the load-bearing control.
- **Defense depth, ~10 lines:** validate `Origin` (only `127.0.0.1:8820`/`localhost:8820`), validate `Host` (standard DNS-rebinding fix), require `Content-Type: application/json`. **Do NOT copy `typeforge_serve.py:86`'s `Access-Control-Allow-Origin: *`** — harmless for fonts, actively dangerous on a server that spawns processes. Explicitly break the house pattern here.
- **Render every registry-derived string with `textContent`, never `innerHTML`.** Agent 09 proved the real injection surface is **XSS, not shell** — cmux round-trips hostile strings faithfully.
- **`open -a "Google Chrome"`, never bare `open`** — cmux claims `LSHandlerRank: Default` for `http`/`https`, so bare `open` may hand the URL **to cmux**. Correctness requirement, not style.
- **Liveness computed fresh per request, never a stored flag** (force-quit leaves a stale flag). Use agent 06's process join (`claude PID -> lsof cwd -> tty -> tree --json`) and agent 09's `cmux rpc workspace.list` (**never** `list-workspaces`; `--json` is silently ignored).
- **Poll `/api/projects` every 5s while visible; stop when `document.hidden`.** Liveness changes are driven by events outside the browser; polling is the only honest mechanism. Skip SSE.

**The row (agent 10's spec, from measured data):**
```
[glyph] **Name** .......................... 6d
        next action sentence (<=90 chars, generated, never truncated)
        [● 74 uncommitted] [⚠ code moved 2d after handoff] [handoff link]
```
- Tiers: **OPEN NOW / RECENT / COLD (>30d) / NO HANDOFF / ARCHIVED** — last three collapsed. The 30d threshold is **measured, not chosen**: recency distribution is bimodal with an empty chasm between 28d and 90d.
- **Cut from the row, with evidence:** git branch (ACOS 3.0 has sat on `acos-deficiency-fixes-2026-06-04` for **40 days** — "a field that reads the same every time you look is invisible"); last action ("the past is precisely what's expensive to re-read"); project health score (*"nothing on disk computes it. Any number here is fabricated"*); the static description (search fodder only).
- **Dirty is a COUNT, not a dot** — tree is chronically dirty (70 files now, 74 at last handoff, 5+ days running), so a boolean dot is permanently lit and therefore invisible. "A number that moves carries information; a dot that is always on does not."
- **NEVER a green badge.** A naive verifier would stamp ✓ on ACOS 3.0 today while 74 uncommitted files sat outside every handoff, and ✓ on a handoff that itself admits it "arrived 3 commits + 1 uncommitted method stale." Asymmetry: a missing warning costs one confused re-entry; **a false green badge costs trust in the entire registry, permanently, and sends him back to hoarding forever.** **Show facts, never verdicts. Only red/amber. Silence means fine.** The one positive artifact is a clickable `file://` link to the handoff: *"the proof is one click away" beats "a badge says trust me."*
- **Elegant consequence (agent 10):** because `--description` is settable at launch, **the registry writes the cmux tab's own title and description** — the tab bar stops saying `⠐ Claude Code` and starts saying `Fix keychain access and handoff protocol`. *"The window doesn't just replace the tab bar — it repairs it."*

---

## 3. The ADOPT List (what already exists — do not rebuild)

> **CAVEAT (repeated in report):** everything in the cmux 0.64.x column is a **DOCUMENTATION CLAIM**. Agent 11 is on 0.63.2 and could not test any of it (verifying restore would require quitting cmux and killing live sessions). Treat as a to-be-verified upgrade plan, not findings.

### cmux (installed 0.63.2 → latest 0.64.18)
| Version | Feature | Replaces | Status |
|---|---|---|---|
| 0.64.11 | **Agent Hibernation** — kills idle background agent processes to free RAM/CPU, resumes from saved session on tab visit. Opt-in: `terminal.agentHibernation` | The entire "my Mac slows down" problem | **DOC-CLAIMED, UNTESTED** |
| 0.64.13 | Fix: native Claude resume dropping cmux hooks | Protects the live in-pane carrier | DOC-CLAIMED |
| 0.64.15 | `terminal.autoResumeAgentSessions` (default **true**) + corrupt-snapshot rolling backup | Auto-relaunch; snapshot durability | DOC-CLAIMED |
| 0.64.16 | `automation.workspaceAutoNaming` — AI titles from conversation content | Row line 1, for free | DOC-CLAIMED. **Verify what model `automation.autoNamingAgent: "auto"` calls before enabling — undocumented; OKOA confidentiality question** |
| — | `sidebar.showWorkspaceDescription` (default true) | The browser window, for live workspaces only | DOC-CLAIMED |
| 0.63.2 | `new-workspace --name --description --cwd --command`; `workspace-action --action set-description`; `rpc workspace.list` | The launch bridge | **VERIFIED by agents 01/03/05/09/10** |

### Claude Code 2.1.209 (all VERIFIED locally by agent 11)
| Capability | Evidence |
|---|---|
| **781 persisted transcripts, 1.1 GB** (512 in ACOS 3.0 alone), oldest Jun 14 — vs ~3 live processes | The dead-process case is already solved and unused |
| `claude --resume <uuid>` | Replays a real transcript, not a re-narration |
| `--no-session-persistence` exists only to disable it | ⇒ persistence is already the default |
| `--session-id <uuid>` | Caller **assigns** identity — mintable in advance |
| `-n, --name` | The description field, natively (shown in `/resume` picker) |
| `claude agents --json --cwd <path>` | Scriptable, no TTY needed. **⚠ `--all` returns LIVE sessions only — does not enumerate parked projects. This is the gap.** |
| `~/.claude.json` `projects{}` — 42 entries, 32 with `lastSessionId`, survives process death | Durable `{path -> session UUID}` row exists natively. But `lastSessionFirstPrompt` populated **3/42** — the description field is effectively empty |
| `--fork-session` | Resume without mutating the original transcript |
| `claude project purge [path]` | ⇒ a per-project state registry exists |

### The one thing no vendor ships
**A semantic handoff.** Agent 11: cmux auto-naming produces a short **title**; `lastBody` is the last message; neither is "what I was doing / what's next / what's half-broken." This is the one genuinely missing artifact — **and Zee has already built it** (21 active + 151 archived handoffs). The handoff producer is the asset. Agent 07 independently: *"every retirement in this stack was caused by a targeting/addressing failure, never by the handoff content model. The handoff producer has survived every rewrite; the injection mechanism has been rebuilt three times."*

### Prior art worth stealing (agent 11)
- **`cmux-resurrect` / `crex`** — third-party, built for cmux; named layout library, 16 templates, 15 AI tools detected, visibly runs `claude --resume <uuid>`, TOML storage, Alfred as launcher. **Closest single artifact to the spec.** Maturity unknown, single-vendor.
- **"Snapshot the inert; replay the live — and gate the replay."** Every mature tool converged independently. tmux-resurrect: hard whitelist (`vi vim nvim emacs man less more tail top htop irssi weechat mutt`); rationale: a `sudo mkfs.vfat /dev/sdb` that was formatting a USB stick could wipe a backup disk after reboot. zellij: human gate (`start_suspended`, "Press ENTER to run"). cmux: narrow allowlist of known-safe native resume commands. **This design's replay allowlist has exactly one entry — `claude --resume <uuid>` — the safest possible case: no arg guessing, idempotent, an on-disk read.**
- **Exclusion lists — what mature tools refuse to persist:** arbitrary live process state (universally refused); **secrets** (cmux "drops tokens, passwords, secrets, and API keys before a resume binding is stored" — **store the cwd and the command, never the environment**); shell history (tmux-resurrect removed the feature, PR #308); scrollback (opt-in everywhere, never default — and none is needed; the JSONL transcript is strictly better).
- **Anti-pattern, disqualified: screen / abduco / dtach** — they solve reattach by never letting the process die — precisely the RAM-resident behavior making the Mac slow. abduco marks `+` when "process exited, only exit status retrievable." *"That is the disease, not the cure."*
- **Cautionary: Aider's lossy replay.** `--restore-chat-history` is off by default; re-sends markdown and recursively summarizes to fit context (#2979: "Restoring chat history leads to error"). *"Your handoff should point at the session ID, not try to be the transcript."*
- **The #1 killer (two mature tools independently): autosave-at-shutdown silently destroying the registry.** cmux #2895 — reboot ⇒ workspaces gone, "empty/partial window state overwriting a previously valid snapshot", "last write wins with incomplete workspace state." tmux-continuum #162/#166 — save timestamp **advances even when the save failed**; autosave "can overwrite `last` with an empty file, destroying the saved session." **Mitigation: never blind-overwrite; write-temp → atomic-rename; keep N rolling backups; refuse to write a snapshot with fewer entries than the previous one without an explicit flag; never trust a 'saved OK' timestamp you didn't verify by re-reading.** (That last clause = **SPINE 3** arriving from an external evidence base.)
