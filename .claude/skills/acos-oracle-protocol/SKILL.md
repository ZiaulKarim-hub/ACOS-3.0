---
name: acos-oracle-protocol
description: Configures The Oracle permission governance system. Manage threshold, hard blocks, modifiers, learned patterns, view audit log, and toggle on/off.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# ACOS Oracle Protocol

## Overview

The Oracle is ACOS's permission governance system — a temperature-scoring PreToolUse hook that auto-approves low-risk tool calls and escalates high-risk ones to the user. This skill manages its configuration.

Configuration file: `.acos/config/oracle.yaml`
Audit log: `.acos/state/oracle-audit.log`
Session override: `.acos/state/oracle-session-threshold`

## Skill Protocol

### Phase 1: Display Current Configuration

1. Read `.acos/config/oracle.yaml`
   - If missing, inform user The Oracle is not configured and offer to create from defaults
2. Display a summary:
   - Enabled status
   - Current threshold (and session override if present)
   - Number of hard blocks
   - Number of custom modifiers
   - Number of learned patterns
   - Whether learning is enabled

### Phase 2: Present Options

Present the user with these options:

1. **Set threshold** — Change the decision threshold (0-10)
   - 0 = ask about everything
   - 5 = balanced (default)
   - 8 = aggressive autonomy
   - 10 = approve everything except hard blocks
2. **Session override** — Set a temporary threshold for the current session only
   - Writes to `.acos/state/oracle-session-threshold`
   - Does not modify oracle.yaml
   - Cleared on next session start
3. **Manage hard blocks** — Add or remove hard-block patterns
   - Show current list, let user add/remove
   - Warn: hard blocks ALWAYS deny, regardless of threshold
4. **Manage custom modifiers** — Add or remove custom modifier rules
   - Each rule: tool (optional), pattern (regex), modifier (integer)
   - Positive modifier = riskier, negative = safer
5. **Manage learned patterns** — Add or remove learned patterns
   - Each pattern: tool, pattern (regex), modifier, confidence (0.0-1.0)
   - Toggle learning enabled/disabled
6. **View audit log** — Show recent escalations and denials
   - Read `.acos/state/oracle-audit.log`
   - Show last 20 entries by default
7. **Reset to defaults** — Restore oracle.yaml from the default template
   - Copy from `.claude/skills/acos-oracle-protocol/templates/oracle-default.yaml`
   - Requires explicit user confirmation
8. **Enable/Disable** — Toggle The Oracle on or off
   - Sets `enabled: true` or `enabled: false` in oracle.yaml

### Phase 3: Apply Changes

Based on user selection:
- Edit `.acos/config/oracle.yaml` with the requested changes
- For session overrides, write to `.acos/state/oracle-session-threshold`
- For resets, copy the default template

### Phase 4: Validate

After making changes:
1. Run a quick test to verify the config is parseable:
   ```bash
   echo '{"tool_name":"Read","tool_input":{"file_path":"test.ts"},"cwd":"."}' | python3 .claude/scripts/oracle-evaluate.py
   ```
2. Confirm the expected output (`{"permissionDecision": "allow"}` for a Read)
3. Report success or any issues

## Temperature Reference

| Tool | Base | Rationale |
|------|------|-----------|
| Read, Glob, Grep, LSP | 0 | Pure read-only, always safe |
| WebSearch, WebFetch | 2 | External but read-only |
| Task | 2 | Subagent spawning, isolated |
| Edit, NotebookEdit | 3 | Modifies existing files |
| Write | 4 | Creates new files |
| Bash | 5 | Shell execution, wide risk range |

**Built-in modifiers:**
- Sensitive paths (.env, credentials, .pem, .key): +4
- Restricted paths (node_modules, .git/): +3
- Destructive bash (rm -r, git checkout .): +3
- Install operations (npm install, pip install): +2
- Framework paths (.acos/, memory/): -2
- In-scope files (active slice): -2
- Test commands (npm test, pytest): -2
- Lint commands (eslint, biome, ruff): -2
- Info commands (git status, ls, pwd): -3

---

*ACOS Oracle Protocol — Tune your permission governance.*
