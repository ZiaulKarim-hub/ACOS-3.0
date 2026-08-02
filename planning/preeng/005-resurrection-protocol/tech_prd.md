# Technical PRD — 005-resurrection-protocol
*(`/preeng.plan` output. Companion to `spec.md` (product) and `data-model.md` (schemas).)*

## 1. System components (all version-controlled where they execute)
- `.claude/scripts/resurrection/registry_lib.py` — row schema; atomic write path
  (`mkstemp(dir=target dir)` -> `fsync(tmp)` -> `os.replace` -> `fsync(dir)`); `realpath().casefold()` lookup
  index; `(st_dev,st_ino)` re-link; tombstone-never-delete; audit append (one `os.write` per JSONL line).
  stdlib-only, `/usr/bin/python3` 3.9.6.
- `.claude/scripts/resurrection/enroll-project.sh` — marker gate (`<root>/.acos/` | `CLAUDE.md` |
  `memory/handoffs/`); mint uuid4 once -> `<root>/.acos/project-id`; upsert derived fields; assert
  `realpath(cwd)==registry.root` (log loudly on mismatch — risk #7); O(1), fail-open, never blocks session start.
- `.claude/scripts/resurrection/rebuild-registry.py` — v1 requirement + DP5 seeder; enumerate
  `find */memory/handoffs` (authoritative) + `*/CLAUDE.md` + `*/.acos` across BOTH parents +
  `~/.claude.json` paths (lossy hint, glob-disambiguation only); reproduce 16/16; flag the Vibe Coding-root anomaly.
- `.claude/scripts/resurrection/close-project.sh` — steps 0-10; four guards + last-workspace guard; pull
  agent-03's exact 7-check list from `agent-03/findings.md` at build time; validated `workspace.close` (fail closed).
- `.claude/scripts/resurrection/resurrect-view.py` — book computed FRESH per request; liveness via `lsof`
  PID->cwd + `ps` tty -> `cmux tree --all --json`; workspace join via `[key:<uuid>]` tag, process-join fallback,
  never cwd-string, never title; tiers OPEN NOW / RECENT / COLD(>30d) / NO HANDOFF / ARCHIVED; dirty as a COUNT;
  BROKEN rows red, never hidden; no green anything.
- `.claude/scripts/resurrection/launch-project.sh` — focus-or-launch: (a) same-root -> newest `.reentry.md`
  re-resolved at open time, inline; (b) open elsewhere -> `cmux rpc workspace.select` focus, never a second
  workspace; (c) not open -> new-workspace with argv reentry + `read-screen` delivery verification + one retry
  + trust-gate detection + `[ -d "$CWD" ]` precheck; write `--name`/`--description` from the registry.
- `.claude/skills/acos-safe-close/SKILL.md` — thin router (parent writes the intent core, never delegated,
  calls the script, prints the receipt verbatim).
- `.claude/skills/acos-resurrect/SKILL.md` — the menu (surface per DP1, terminal-first) + finish verb.
- (DP1-conditional) `.claude/scripts/resurrection/resurrection-server.py` — the 8820 browser view.

## 2. Technical requirements (traceable to spec FRs)
- **TR-1 (FR-M2/M1):** atomic write path exactly as above; per-project files dissolve locking; if compaction
  ever needs a lock use `flock LOCK_NB` + bounded retry, never blocking `LOCK_EX`, never mkdir-lock.
- **TR-2 (FR-M3):** identity = uuid4 minted once; lookup `realpath.casefold`; re-link `(st_dev,st_ino)`;
  `sanitize(cwd)`/git-remote/workspace-UUID/session-UUID/title BANNED as identity.
- **TR-3 (FR-M4/FR-S4):** enroll-project.sh marker gate + assertion + O(1) fail-open; additive user-level
  SessionStart hook; never touches the existing hook chain.
- **TR-4 (FR-M5):** rebuild reproduces 16/16 from handoffs alone across both parents; `~/.claude.json` is a
  hint only (glob-disambiguation, never a decoder).
- **TR-5 (FR-M6/M7/M8/M9):** close steps 0-10; `next_action` generated ≤90 chars; receipt read-back with
  `listed N of M`; validated `workspace.close`, fail closed, no `identify` fallback; refuse last-workspace close.
- **TR-6 (FR-M10):** blind round-trip verifier — fresh general-purpose Task, handoff text ONLY; Wigum cap 5
  then DEGRADE; no new agent definition files.
- **TR-7 (FR-M11/M12):** fresh book render; live liveness joins; `[key:<uuid>]` join; SPINE 1 focus-not-launch;
  argv delivery verified via read-screen + retry.
- **TR-8 (FR-M13):** artifacts under `memory/handoffs/closed/<slug>/`; `.reentry.md` never `.resume.md`; single
  daemon contact `state/stop-<sid>`.
- **TR-9 (FR-M14):** Phase-0 fixes — `eternity-resume-prepend.sh:158-169` pane-scope/remove tier-3;
  `eternity-protocol-core.sh:139` `head -40` fix in repo copy + byte-identical Application Support bin twin +
  bin-manifest regen; `token-watcher.py:1113` fail-CLOSED + bin-manifest regen.
- **TR-10 (FR-M15):** DR-1 gate — full cycle on a real project; recording/receipts to `.acos/evidence/`.
- **TR-11 (FR-C1):** optional server — stdlib ThreadingHTTPServer at `127.0.0.1:8820` fixed; never launchd; NO
  idle reaper (comment in code); singleton via `/api/whoami`; opaque-ID launch; Origin+Host+Content-Type
  validation; no `ACAO:*`; `textContent` only; `open -a "Google Chrome"`; 5s visible-only polling.
- **TR-12 (NFR-Security):** no registry-derived string enters `--command` (only the skill-controlled reentry
  file PATH); names/next_action go in `--name`/`--description` via list-form subprocess (XSS-not-shell).

## 3. Orchestration, durability & edge constraints (§0.9)
- Orchestration stack = ACOS skills+agents+hooks; executor `/acos-execute-slice`.
- **Durable execution:** state survives `kill -9` by construction (enrollment + atomic writes + rebuild-from-disk
  + native transcripts + untouched Eternity handoffs). No keep-alive daemon (that is "the disease, not the cure").
- **HITL nodes:** DP1-DP5 defaults (Assumptions to confirm); the DP5 curation pass; DP2's scheduled cmux
  restart; the DR-1 user continuity confirmation. Each is a mandatory approval pause.
- **Observability:** append-only audit JSONL; per-slice evidence bundles; agent identity log.
- **Role->state mapping:** PM(architect) authors slice -> Dev(developer) executes in allowed files + Evidence
  Bundle -> QA(reviewers) zero-trust verify -> pass/reject-to-rework; a slice is not Done until learnings update.

## 4. Failure model (fail-safe by construction)
The dangerous quadrant (data lost + tab gone) is unreachable: every close failure branch's action is simply
*don't close* — the tab remaining open with an error IS the failure signal; the tab vanishing IS success. Close
is the literal last statement, gated on the 7-check verification gate AND the read-back; the target is the
validated `CMUX_WORKSPACE_ID` (fail closed); `identify --surface` is never a fallback (fails open). Registry
reads fail loudly (JSON), never silently (the YAML/valid-but-wrong failure class is designed out).

## 5. Assumptions carried (UNVERIFIED — resolved in Phase-0)
cmux `workspace.select`/`workspace.close`/`surface.resume.*`/`session.restore_previous` behavior; last-workspace
close; `customDescription` restart survival; hibernation/auto-resume; the 1-in-6 silent prompt drop;
`--command` shell-parse-vs-exec. All are T4 in `evidence-ledger.json`, gated behind the Phase-0 diagnostic slice.
