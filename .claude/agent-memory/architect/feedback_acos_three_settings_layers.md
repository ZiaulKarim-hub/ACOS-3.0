---
name: feedback-acos-three-settings-layers
description: Claude Code merges THREE settings files; auditing hook registration must check all three or you get false conclusions
metadata:
  type: feedback
---

When auditing which hooks are actually registered, you MUST check all THREE Claude Code
settings layers — checking fewer leads to a factually wrong conclusion.

1. Project: `<repo>/.claude/settings.local.json`
2. User-global: `~/.claude/settings.json`
3. User-global local: `~/.claude/settings.local.json`  ← the one most easily forgotten

**Why:** During the 2026-06-11 robust review (Subsystem 5), Round 1 concluded the legacy
handoff trio was "registered in NO settings file" after checking only layers 1 and 2.
Round 2 caught that layer 3 (`~/.claude/settings.local.json`, a stale 2026-04-25 pre-autopilot
snapshot) still registered all three legacy hooks LIVE — using the removed `git rev-parse`
pattern — causing duplicate Stop + PreToolUse firing across every project. The miss became a
documented-as-fact falsehood until corrected.

**How to apply:** Before asserting any hook is/ isn't registered, `grep` the script name across
all three files. Stale global-local settings can silently re-introduce superseded behavior
project-wide. Related: [[project-acos-autopilot-supersedes-handoff-hooks]].
