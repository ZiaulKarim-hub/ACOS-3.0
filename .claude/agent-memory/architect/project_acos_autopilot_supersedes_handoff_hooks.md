---
name: project-acos-autopilot-supersedes-handoff-hooks
description: ACOS handoff/continuation is now autopilot-based; the legacy context-monitor/context-watchdog/token-gate hooks are unregistered and superseded
metadata:
  type: project
---

As of the 2026-06-11 framework-wide robust review (Subsystem 5), the ACOS handoff
system is the **autopilot architecture**, NOT the old hook-based handoff trio.

**Live (registered in project `.claude/settings.local.json`):**
- Stop → `autopilot-stop-handler.py` (continuation loop: goal marker / iteration cap / idle window)
- UserPromptSubmit → `autopilot-context-injector.py` + `eternity-resume-prepend.sh`
- SessionStart → `register-session-pid.sh` (Eternity Protocol; lives at `~/Library/Application Support/acos-token-monitor/bin/`, spawns token-watcher daemon)
- PreToolUse (5, in order): oracle-evaluate.py, check-scope.sh, autopilot-askuserquestion-handler.py, block-review-rules-read.sh, autopilot-allow-extra-tools.py

**Legacy / UNREGISTERED everywhere (on disk with banners, never fire):**
`context-monitor.sh` (was Stop), `context-watchdog.sh` (was PreCompact), `token-gate.sh`
(was PreToolUse). There is NO PreCompact hook. `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=69` is
NOT set anywhere — old CLAUDE.md claims of 69%/130k-ceiling/PreCompact were stale and were fixed.

**Why:** the autopilot system replaced the hook-based handoff after the eternity-protocol
work; the in-repo handoff hooks were left orphaned and the docs lagged.

**How to apply:** Do NOT re-register the legacy trio anywhere (double-fires Stop + PreToolUse).
`token-gate.sh --health-check` is autopilot-aware (legacy trio = optional). When auditing hooks,
read all THREE settings layers — see [[feedback-acos-three-settings-layers]]. CLAUDE.md "Handoff
& Continuation System" + Oracle hook-ordering sections are now authoritative.
