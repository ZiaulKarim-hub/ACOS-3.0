# Resurrection Protocol — Build Plan (ordered)

Ground rules carried through every step: **NEVER write to the daemon state dir** (`~/Library/Application Support/acos-token-monitor/state/`) except the single documented `state/stop-<SESSION_ID>` marker at close step 0. **NEVER delete or move `pending-resume-*.txt` / `RESCUED-resume-*.txt`.** Never write top-level `memory/handoffs/*.{md,yaml}` or any `*.resume.md`. All scripts call `/Users/zee/.claude/local/claude` and `/Applications/cmux.app/Contents/Resources/bin/cmux` absolutely (the `claude` command is shadowed twice on this machine). All new code lives in the ACOS 3.0 repo (version-controlled where it executes — the report's highest-severity doc-drift lesson).

---

## Phase 0 — Prerequisites (report §"Prerequisites Before Any Build", updated where today wins)

**0.1 — "Ask Zee why he doesn't close tabs" — ANSWERED, no action.** The 2026-07-16 confirmed vision states it directly: closing must FEEL safe or he keeps hoarding (fear-of-loss motive). Residual: if hoarding persists after DR-1 ships, revisit agent 04's alternative motives (context-switch cost / tab-as-todo-list).

**0.2 — cmux upgrade prerequisite is MOOT (already 0.64.19); run the post-upgrade verification battery instead.**
- (a) Verify in-pane hook firing on 0.64.19 — the live resume carrier (#5427-class regression risk). Open a throwaway Claude session in a new cmux pane; confirm SessionStart/UserPromptSubmit/Stop hook artifacts appear for that session (fresh pid registration in the daemon state dir — read-only check — and autopilot context injection visible in-session). *Verification: observed artifacts archived to `.acos/evidence/2026-07-16/resurrection-phase0/`.*
- (b) Re-run the cmux CLI battery on 0.64.19 using throwaway `RESURRECTION-PROBE-*` workspaces: `rpc workspace.list` JSON shape; `workspace list --json` (worked today — was silently ignored on 0.63.2); `new-workspace --name/--description/--cwd/--command` round-trip; `--description` verbatim round-trip; `read-screen`; refs-are-handles behavior; **`rpc workspace.select` focus behavior (new, untested)**. *Verification: pasted command outputs archived; each probe workspace closed after.*
- (c) DP2-gated disruptive tests: `workspace.close` against a live sacrificial Claude session (does it prompt?); last-workspace-in-window close; `customDescription` survival across one controlled cmux restart; hibernation/auto-resume on a throwaway (DP4). *Verification: written answers with pasted output; the close-skill guards in Phase 2 are parameterized by these results.*

**0.3 — Fix residual #10 (pane-blind last-resort resume tier).** File: `/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/eternity-resume-prepend.sh`, the "(3) LAST RESORT — newest pending-resume in this project (NOT pane-scoped)" block at lines 158–169 (confirmed present today, comment admits it). Pane-scope or remove path (3) — agent 08: the single most important pre-existing bug to close BEFORE the registry makes two-panes-one-project routine. *Verification: with two sessions on one project, session B is never offered session A's resume via path (3); simulate and archive the transcript. Touches this one file only.*

**0.4 — Fix the `head -40` silent truncation.** Confirmed today at `eternity-protocol-core.sh:139` (`printf '%s\n' "$GS_DIRTY" | head -40`) inside the block headed "these are in NO handoff — inspect FIRST"; repo copy and the live Application Support bin copy are byte-IDENTICAL — **fix both**, and regenerate the token-monitor bin-manifest after touching the bin copy (house rule). Fix: list all, or print an explicit `... (listed 40 of N — TRUNCATED)` line. *Verification: generate a handoff now (~70 dirty files in this repo): listed count matches `git status --porcelain | wc -l`, or the truncation line prints. Files touched: `.claude/scripts/eternity-protocol-core.sh` + `~/Library/Application Support/acos-token-monitor/bin/eternity-protocol-core.sh` + bin-manifest.*

**0.5 — Close the half-open pane gate (P1-F).** `~/Library/Application Support/acos-token-monitor/bin/token-watcher.py:1113` — make the orphan-surface-unknown branch fail CLOSED so gate safety no longer depends on one 90-byte marker file (`.cmux-inpane-inject`). Regenerate the bin-manifest after editing. *Verification: simulate a surface-less artifact → gate rejects; temporarily renaming the marker (and restoring it) no longer re-arms fail-open. Nothing deleted; pending-resume files untouched.*

**0.6 — Provenance of the 147 `/acos-complete` runs (hand vs hook).** Grep `.claude/settings*.json` and all registered hooks for any automation invoking acos-complete; spot-check archived handoff transcript context. *Verification: written answer in evidence. If hook-fired, the adoption expectation drops ~30% → ~15% and the DR-1 gate becomes even more load-bearing.*

**0.7 — Probe `--command` internal handling.** Launch a throwaway workspace passing, as a single list-form argument, a `--command` string containing `; touch /tmp/resurrection-cmd-probe;`. File appears ⇒ cmux shell-parses `--command`. *Verification: documented result. Design consequence either way: registry-derived strings never enter `--command` (already the rule); this settles where the reentry `$(cat ...)` evaluation happens.*

**0.8 (optional hardening, from risk #23):** `archive-project.sh:199` gates a `-delete` of handoffs on an interactive `read -p ... || true` that silently degrades in non-TTY. Convert to an explicit `--yes` flag. *Verification: non-TTY invocation without the flag refuses to delete.*

---

## Phase 1 — Registry core

**1.1 — `.claude/scripts/resurrection/registry_lib.py`.** Atomic write (`mkstemp` in the target's own dir → `fsync(tmp)` → `os.replace` → `fsync(dir)`); row schema (§design); `realpath().casefold()` index; `(st_dev, st_ino)` re-link; tombstone-never-delete; audit append (one `os.write()` per JSONL line) to `~/.acos/registry-audit.jsonl`. *Verification: contention crash-test 6 processes × 60 writes → 0 errors, 0 torn (mirror of the measured 180/360 → 0 result); truncated-file load fails LOUDLY (JSON), never a silent partial.*

**1.2 — `.claude/scripts/resurrection/enroll-project.sh` + hook registration.** Marker gate (`<root>/.acos/` OR `CLAUDE.md` OR `memory/handoffs/`); mint uuid4 once → `<root>/.acos/project-id`; upsert row with derived fields; assert `realpath(cwd) == registry.root`, log loudly on mismatch (risk #7 — protects the f639310 project-scoping fix); O(1) fast, fail-open, never blocks session start. Register as an **ADDITIVE** user-level SessionStart hook in `~/.claude/settings.json` pointing at the absolute repo path. Do NOT touch the Application Support `register-session-pid.sh` or the existing hook chain. Name deliberately distinct from the existing `.claude/scripts/autopilot-enroll-project.sh`. *Verification: new session in a marker dir → row file appears in `~/.acos/registry.d/` with all fields derived; session in a scratchpad/non-marker dir → no row; second session in the same project → same uuid, no duplicate row; `.acos/project-id` written exactly once.*

**1.3 — `.claude/scripts/resurrection/rebuild-registry.py` (v1 requirement + DP5 seeder).** Enumeration sources: `find */memory/handoffs` (authoritative) + `*/CLAUDE.md` + `*/.acos` across BOTH parents (`~/Documents/Vibe Coding/`, `~/Documents/OKOA/`) and any additional roots, + `~/.claude.json` project paths as a lossy hint (glob-disambiguation only — path-mangling collapses spaces/dots). *Verification: dry-run against live disk lists ≥18 candidates including the `Vibe Coding`-root anomaly (flagged, not auto-enrolled without confirmation); output reconciles with rows enrollment creates later.*

**1.4 — Seed + curation (per DP5).** Run the seeder; user does one curation pass in the menu; junk rows tombstoned by hand (deletion is a human act only). *Verification: book lists the real active projects; anomaly rows archived.*

---

## Phase 2 — Safe close

**2.1 — `.claude/scripts/resurrection/close-project.sh`** implementing steps 0–10 (§design) with the four non-negotiable guards + last-workspace guard (parameterized by 0.2c results). Pull agent 03's exact 7-check verification-gate list from `.acos/swarm/swarm-20260714-084532/agent-03/findings.md` at build time. *Verification — tamper tests, each archived: (a) delete the handoff between write and read-back → receipt refuses SAFE, tab stays open; (b) unvalidatable `CMUX_WORKSPACE_ID` → fail closed, no close, no `identify` fallback; (c) last-workspace case → close skipped with explicit message; (d) `state/stop-<sid>` exists BEFORE step 1 runs (the only daemon-dir write; assert via directory diff); (e) receipt's `listed N of M` equals `git status --porcelain | wc -l`; (f) `.reentry.md` and `handoff.yaml` co-located under `memory/handoffs/closed/<slug>/`, `status: parked`, `type: close-project`; (g) Eternity's glob cannot see them (`ls -t memory/handoffs/*.md memory/handoffs/*.yaml` output unchanged); (h) `pending-resume-*.txt` population unchanged before/after.*

**2.2 — `.claude/skills/acos-safe-close/SKILL.md`** — thin router: parent writes the intent core (never delegated), calls the script, prints the script's receipt verbatim, never composes its own. *Verification: full end-to-end run on a THROWAWAY project; receipt says SAFE only after all checks; tab actually closes as the literal last act.*

**2.3 — Blind round-trip verifier** (step 5): fresh general-purpose agent given the handoff text ONLY — no repo access, no cwd context; must state the next step; Wigum cap 5 then DEGRADE (close still allowed, receipt marks DEGRADED). No new agent definition files (`.claude/agents/` untouched). *Verification: test the tester — a deliberately gutted handoff must FAIL; the real one must yield a next-step quote that appears in the receipt.*

---

## Phase 3 — The menu (Resurrection Protocol proper)

**3.1 — `.claude/scripts/resurrection/resurrect-view.py` + `.claude/skills/acos-resurrect/SKILL.md`** (surface per DP1; menu-first recommended). Fresh-computed book: liveness via claude `PID → lsof cwd` join + `PID → tty → cmux tree --all --json`; workspace join via `[key:<uuid>]` description tag, process-join fallback for untagged, never cwd-string, never title; tiers OPEN NOW / RECENT / COLD(>30d) / NO HANDOFF / ARCHIVED; dirty as a count; BROKEN rows in red, never hidden; no green anything. *Verification: renders today's real state correctly — FruitSync + ACOS 3.0 as OPEN NOW, and ACOS 3.0's two live workspaces (4 and 5) as ONE row; a deliberately broken row renders BROKEN.*

**3.2 — `.claude/scripts/resurrection/launch-project.sh`** — focus-or-launch: (a) same-root pick → newest `.reentry.md` re-resolved at open time, loaded inline; (b) open elsewhere → `cmux rpc workspace.select` focus (as validated in 0.2b), NEVER a second workspace; (c) not open → `new-workspace` with argv reentry delivery, `read-screen` delivery verification + one retry, trust-gate detection ("Quick safety check"), `[ -d "$CWD" ]` pre-check, `--name`/`--description` written from the registry (`<next_action> [key:<uuid>]`). *Verification — the SPINE 1 acceptance test: picking ACOS 3.0 while it is open changes focus and the workspace count stays constant; launch path on a throwaway delivers the multi-line reentry as ONE message (read-screen marker found); untrusted-dir launch is detected and reported, not silently assumed delivered.*

**3.3 — Loop mechanics:** resume flips `parked → active`; finish verb sets `completed` (row hidden in ARCHIVED tier, never deleted). `/acos-complete` untouched. *Verification: status transitions visible in the row file and audit log.*

---

## Phase 4 — DR-1 gate (the ship gate)

Run the FULL cycle on a real project: `/acos-safe-close` → receipt `SAFE TO CLOSE THIS TAB` → tab gone → later, `/acos-resurrect` → pick → work demonstrably continues → **user confirms continuity**. Save the recording/receipts to `.acos/evidence/`. Per the report: **"Until it exists, the skill is not shipped."** This is the antidote to the placebo problem and to trust-death (one silent loss ends the tool permanently).

---

## Phase 5 — Optional browser window (DP1-conditional)

**`.claude/scripts/resurrection/resurrection-server.py`** — stdlib ThreadingHTTPServer at `127.0.0.1:8820` fixed; skill-started, never launchd; NO idle reaper (comment in code); singleton via `GET /api/whoami`, never port-hop; `POST /api/launch` opaque-ID only; `Origin`+`Host`+`Content-Type` validation; no `ACAO: *`; `textContent` only; `open -a "Google Chrome"`; 5s visible-only polling. *Verification: EADDRINUSE reuse works; hostile project name renders inert; cross-origin POST rejected; `/api/launch` with a path instead of an ID → 400.*

---

## Touched vs. left alone

**TOUCHED (exhaustive):** `.claude/scripts/eternity-resume-prepend.sh` (0.3); `.claude/scripts/eternity-protocol-core.sh:139` + its byte-identical Application Support bin twin + bin-manifest regen (0.4); `~/Library/Application Support/acos-token-monitor/bin/token-watcher.py:1113` + bin-manifest regen (0.5); `~/.claude/settings.json` (one additive SessionStart entry, 1.2); optionally `archive-project.sh` (0.8); plus all NEW files under `.claude/scripts/resurrection/` and the two new skills.

**LEFT ALONE (never touched):** the daemon state dir except writing `state/stop-<sid>` at close; `pending-resume-*.txt` / `RESCUED-resume-*.txt` (never deleted, never moved); top-level `memory/handoffs/` and `memory/handoffs/archive/` (Eternity's live namespace — two fresh 2026-07-16 emergency handoffs sit there right now); `register-session-pid.sh` and the rest of the token-monitor bin (beyond the two named fixes); `/acos-complete`, `/acos-handoff`, `/acos-resume-prompt`, the Eternity skills; `review-rules/` (never, by standing rule); `.claude/agents/` (no new agents; round-trip verifier uses a general-purpose Task).