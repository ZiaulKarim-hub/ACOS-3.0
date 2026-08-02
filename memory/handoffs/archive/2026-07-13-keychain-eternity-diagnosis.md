---
timestamp: "2026-07-13"
status: "completed"
type: "diagnosis"
topic: "Repeating macOS keychain-unlock prompts — suspected Eternity Protocol involvement"
origin_session: "49f72902-6b7a-43f3-92a1-72303f0a0c3c"
eden_note: "The eden output-filter was ON (Level 3) in the origin session. It affects human-facing chat ONLY — this file is written in full technical register."
---

# Diagnosis Handoff — repeating "security wants to use the 'login' keychain" prompts

## Problem statement
macOS repeatedly shows the keychain-unlock dialog:
> **security wants to use the "login" keychain.** Please enter the keychain password.

It re-appears continuously. Clicking **Cancel** does not stop it. Entering the login password did
**not** stop it (prompts returned). The requester is `/usr/bin/security find-generic-password`
reading two services:
- `Claude Code-credentials` (account `zee`) — read by the `claude` binary (Claude Code auth).
- `gh:github.com` (account `ZiaulKarim-hub`, and blank) — read by the git/gh credential helper.

## User's hypothesis (investigate FIRST)
The ACOS **Eternity Protocol** is involved. Evidence below supports an *indirect* role.

## Environment snapshot (2026-07-13, origin session 49f72902)
- Tracked Claude sessions (token-watcher `.last-total-*`): **84**
- Sessions AT/OVER the `500000`-token eternity fire threshold: **33**
- Eternity fire/continue markers in `~/Library/Application Support/acos-token-monitor/state/`:
  - `.clear-requested-*`: **22**
  - `.compact-fired-*`: **6** — incl. `.compact-fired-49f72902…` @ **2026-07-13 21:30** (the origin session itself)
  - several `.cmux-surface-*` markers (14:08–14:39)
- Eternity config `~/Library/Application Support/acos-token-monitor/config.yaml`:
  `threshold: 500000`, `fire_command: "/acos-eternity-protocol"`.
- Backfill launch agent `com.acos.token-watcher-backfill` runs `backfill-watchers.sh 240` every
  `StartInterval` 120s; last run: spawned 0, skipped-alive 14, skipped-dead 8.

## Ruled OUT
- No cron jobs (`crontab -l` empty).
- No custom git-mirror / push launchd agent (only `com.acos.token-watcher-backfill` + surfshark VPN).
- **Eternity / token-monitor scripts do NOT call `security`, `gh`, or `git` directly.** grep of
  `~/Library/Application Support/acos-token-monitor/bin/` for
  `find-generic-password|gh auth|gh api|git push|git fetch|git clone` → **zero** matches.
  So the keychain reads are NOT issued by eternity code itself.

## Leading hypothesis — indirect eternity amplification (CONFIDENCE: moderate, NOT directly proven)
Eternity does not read the keychain, but it repeatedly **cycles sessions**:
33 sessions over threshold → daemon keystroke-injects `/acos-eternity-protocol` → compact + `/clear`
+ resume (22 `.clear-requested` observed). Each `/clear` / resume / new cmux surface makes the
`claude` binary **re-authenticate**, which reads `Claude Code-credentials` from the login keychain.
With the keychain **locked**, every such read raises the unlock dialog. 84 sessions + active eternity
cycling = a self-refreshing storm that a single unlock or a single kill cannot clear.
This fits: eternity is very active, and the reads are issued by `claude`, not by eternity code.
**Gap:** not yet confirmed by correlating a specific eternity fire with a specific read burst.

## Alternative / contributing hypotheses
1. **Locked keychain, independent of eternity.** Auto-lock timer or sleep locked `login`; 84 sessions
   each periodically read `Claude Code-credentials` → mass prompts regardless of eternity.
2. **Keychain password ≠ macOS login password** → dialog unlock does not persist. Test in Keychain Access.
3. **Origin session's GLOBAL settings edit.** This session added acos-eden-protocol `UserPromptSubmit`
   + `SessionStart` hooks to `~/.claude/settings.json` (to make eden global). That file is read by ALL
   sessions and MAY have triggered a mass reload/re-auth. Eden hooks themselves do NOT read the
   keychain. Reverting the global eden registration is a cheap way to remove this variable.
4. **`gh:github.com` reads** (account `ZiaulKarim-hub` = personal GitHub mirror target) imply a separate
   git/gh trigger; the source was not caught running (no active `git`/`gh` process observed).

## Already tried
- Killed all stuck `security find-generic-password` procs: **68 → 0**. They **returned** → an active
  driver, not a static backlog.
- User entered login password in the dialog → prompts **returned**.
- Confirmed eternity/token-monitor scripts issue no `security`/`gh`/`git` calls.

## Recommended next steps (for the picking-up session)
1. **Correlate eternity ↔ reads.** `tail -f` the active session's daemon log and watch for
   `/acos-eternity-protocol` fires / new `.clear-requested-*`; simultaneously sample
   `ps -Ao pid,comm,command | awk '$2=="security"'` ~1×/s. If read bursts line up with eternity fires,
   the amplification hypothesis is confirmed.
2. **Test by pausing eternity.** Raise the threshold above current totals
   (`/acos-eternity-protocol-threshold 2000000`) or stop the daemon; `/acos-eternity-protocol-stop` on
   noisy sessions. Watch whether the storm subsides.
3. **Test the keychain.** Keychain Access → `login` → Unlock. If it rejects the login password →
   keychain password ≠ login password (reset it). If it accepts → Change Settings → disable
   "Lock after…" / "Lock when sleeping" and see if reads go silent.
4. **Remove the eden variable.** Revert the global eden hook registration in `~/.claude/settings.json`
   (back to project-only, or remove) and observe.
5. **Reduce load.** 84 tracked / 33 over threshold is extreme; closing idle sessions cuts both the
   re-auth load and eternity's fire pressure.

## Key files / paths
- Daemon + state: `~/Library/Application Support/acos-token-monitor/` (`bin/`, `state/`, `logs/`, `config.yaml`)
- `bin/token-watcher.py`, `bin/backfill-watchers.sh`, `bin/eternity-cmux-inpane.sh`, `bin/eternity-cmux-resume-inpane.sh`, `bin/inject-via-cmux.py`
- Launch agent: `~/Library/LaunchAgents/com.acos.token-watcher-backfill.plist`
- Global CC settings (eden hooks added here): `~/.claude/settings.json`
- Eden skill (global): `~/.claude/skills/acos-eden-protocol/`; state `~/.claude/state/eden-level`
- Keychain DB: `~/Library/Keychains/login.keychain-db`

## Safety notes
- The reads are legitimate (`/usr/bin/security` reading the user's OWN saved GitHub + Claude Code
  logins) — not malware.
- Do NOT run `security` subcommands blindly while diagnosing — `security show-keychain-info` HUNG once
  and had to be killed; some `security` subcommands can themselves raise the dialog.
- Killing `security find-generic-password` procs is safe (equivalent to Cancel) but only clears the
  current batch; the driver refills it.
