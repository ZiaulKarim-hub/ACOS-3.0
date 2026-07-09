# acos-token-monitor bin/ — reference copies (NOT live)

These are **version-controlled reference copies** of two hooks from the Eternity
Protocol's token-monitor daemon suite. They are **not loaded from here** — nothing
in the repo sources this directory.

**Source of truth (live, machine-local, untracked by git):**

```
~/Library/Application Support/acos-token-monitor/bin/
```

The `bin/` suite is per-machine runtime infrastructure spawned by launchd, which is
why it lives outside the repo. That means fixes to it have **no git backup** — these
copies exist so the two in-pane hooks below survive a machine reset and are reviewable
in PRs. If you edit the live files, refresh these copies (and remember the launcher
fail-CLOSES on a `bin-manifest.sha256` mismatch, so regenerate that manifest too).

## Files

| File | Role |
|------|------|
| `eternity-cmux-inpane.sh` | In-pane **Stop** hook. Injects `/exit` (P0), `/clear` (P1), and the `/acos-eternity-protocol` fire (P2). Contains the 2026-07-06 hardening: arm-after-verify, verified `/clear`, consume-all-flags + fresh-`.failed`, and the guard-age-only stale-guard reaper (2h window). |
| `eternity-cmux-resume-inpane.sh` | In-pane **SessionStart(clear)** hook. Injects the resume trigger prompt after a `/clear`. Contains the 2026-07-06 arm-after-verify + `cmux ping` gate and the separate-Enter submit fix. |
| `register-session-pid.sh` | **SessionStart** hook (registered globally in `~/.claude/settings.json`). Registers the session PID, self-spawns the token-watcher, and captures the cmux surface binding. Contains the 2026-07-09 stale-surface-invalidation fix. |

## 2026-07-09 fixes captured here

- **Stale cmux-surface binding → silent `/clear` stall** (root cause of the Investment-
  Committee session `6e82feac` failure). `register-session-pid.sh` wrote `cmux-surface-<sid>`
  when `CMUX_SURFACE_ID` was set but **never invalidated it when unset**. After a cmux
  restart (which kills all surface ids) or a resume outside cmux, the dead binding
  persisted; `is_cmux_session()` trusts the file's mere existence, so the session stayed
  misclassified as cmux and armed a `/clear` at a **dead surface** — the in-pane send
  failed silently, no clear, no resume. Fix: SessionStart now **removes** a stale
  `cmux-surface-<sid>` when `CMUX_SURFACE_ID` is unset, so the session correctly falls
  back to warp (manual-only), which works.
- **Louder failure** (`eternity-cmux-inpane.sh` Priority-1): when cmux is up (`ping` OK)
  but the `/clear` **send** fails (surface unreachable), escalate via the daemon's shared
  channel — append to `.eternity-ALERT` + a one-shot macOS notification (`.alerted-<sid>`
  marker, reset on a successful clear) — so a dead-surface stall is never silent again.

## 2026-07-06 fixes captured here

- **Submit-Enter fix** (both files): `cmux send "text\n"` delivers text+Enter as one
  burst that Claude Code's TUI can absorb as a bracketed paste (newline → soft-newline,
  never submitted). Fix: send the Enter as a **separate, delayed** `cmux send -- '\n'`
  (twice, with gaps).
- **Stall-class fixes** (`eternity-cmux-inpane.sh`): see the inline comments — every
  send is now ping-gated and verified, guard bookkeeping commits only on a verified
  send, and the reaper self-heals a silently-dead fire without a marker gate (which
  would re-open the permanent stall it exists to cure).

Reviewed by two rounds of adversarial multi-agent review before landing.
