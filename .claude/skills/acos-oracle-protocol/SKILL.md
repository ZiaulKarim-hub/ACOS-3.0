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

### Phase 1: Health Check (Always Runs First)

1. Run the diagnostic:
   ```bash
   python3 .claude/scripts/oracle-evaluate.py --diagnose
   ```
2. Report results to the user:
   - Is Oracle enabled?
   - Is the config parseable?
   - Do sample tool calls produce expected decisions?
   - Are there permission conflicts in `settings.local.json`?
3. If issues are detected, explain them and offer to auto-fix before proceeding.

### Phase 2: Smart Options

Present the user with these options using AskUserQuestion:

1. **Quick Presets** — One-word profiles that set the threshold:
   - `strict` (threshold 3): Asks about edits, writes, and most bash commands. Only reads and info commands are auto-approved.
   - `balanced` (threshold 5): Approves reads, basic edits, tests, lints. Asks about installs, destructive ops, sensitive files.
   - `autonomous` (threshold 8): Minimal prompts. Only sensitive writes and destructive bash escalate.
   - `default` (threshold 9): Default. Auto-approves everything except destructive bash and hard blocks.
   - `permissive` (threshold 10): Approves everything except hard blocks.
   - `YOLO` (threshold 11): No guardrails. Even hard blocks are bypassed. Use with extreme caution.

2. **Tune threshold** — Set a specific threshold value (0-11). Show what each level means:
   - 0 = ask about everything
   - 3 = strict (preset equivalent)
   - 5 = balanced (preset equivalent)
   - 8 = autonomous (preset equivalent)
   - 9 = default
   - 10 = permissive (everything except hard blocks)
   - 11 = YOLO (everything, hard blocks bypassed)

3. **Audit analysis** — Read the audit log, show:
   - Top 5 most-escalated tool patterns
   - Breakdown by tool type (Bash, Write, Edit, etc.)
   - Suggested learned rules based on frequency (e.g., "npm run build was asked 12 times → suggest -3 modifier")

4. **Advanced** — Granular configuration:
   - Manage hard blocks (add/remove patterns)
   - Manage custom modifiers (add/remove rules)
   - Manage learned patterns (add/remove, toggle learning)
   - Enable/Disable Oracle entirely
   - Reset to defaults (copy from template)

### Phase 3: Apply + Validate + Test

After making any changes:
1. **If YOLO (threshold 11) was selected**, display this warning and require explicit confirmation before applying:
   > **WARNING: YOLO mode disables ALL safety guardrails.**
   > Hard-blocked commands (git push, rm -rf /, DROP TABLE, git reset --hard main)
   > will be auto-approved without any prompt. This is irreversible once executed.
   > Are you sure you want to enable YOLO mode?
   - Do NOT apply threshold 11 without the user typing explicit confirmation.
2. Apply changes to `.acos/config/oracle.yaml`
3. For session overrides, write to `.acos/state/oracle-session-threshold`
4. For resets, copy from `.claude/skills/acos-oracle-protocol/templates/oracle-default.yaml`
5. Run `python3 .claude/scripts/oracle-evaluate.py --diagnose` to verify
6. Show before/after comparison of the affected setting

## Quick Preset Details

When a preset is selected, set the threshold AND inform the user what it means:

| Preset | Threshold | Auto-approved (examples) | Escalated (examples) |
|--------|-----------|--------------------------|----------------------|
| strict | 3 | Read, Glob, Grep, LSP, WebSearch, Task | Edit, Write, Bash (all) |
| balanced | 5 | + Edit, Write (normal), Bash (tests, lints, info) | Bash (install, destructive), Write/Edit (sensitive) |
| autonomous | 8 | + installs, Edit sensitive, restricted paths | Write sensitive (.env, creds), Bash destructive (rm -r) |
| permissive | 10 | + Write sensitive, Bash destructive | Nothing (only hard blocks deny) |
| YOLO | 11 | Everything including hard blocks | Nothing at all |

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
- Sensitive paths (.env, credentials, .pem, .key): +5
- Destructive bash (rm -r, git checkout .): +5
- Restricted paths (node_modules, .git/): +3
- Install operations (npm install, pip install): +3
- Framework paths (.acos/, memory/): -2
- In-scope files (active slice): -2
- Test commands (npm test, pytest): -2
- Lint commands (eslint, biome, ruff): -2
- Info commands (git status, ls, pwd): -3

## Diagnostic Command

Run anytime to check Oracle health:
```bash
python3 .claude/scripts/oracle-evaluate.py --diagnose
```

With a custom config path:
```bash
python3 .claude/scripts/oracle-evaluate.py --diagnose --config path/to/oracle.yaml
```

---

*ACOS Oracle Protocol — Tune your permission governance.*
