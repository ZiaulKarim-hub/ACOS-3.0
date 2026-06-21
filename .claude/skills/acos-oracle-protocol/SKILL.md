---
name: acos-oracle-protocol
description: Configures The Oracle permission governance system. Manage threshold, hard blocks, modifiers, learned patterns, view audit log, toggle on/off, and activate session autopilot.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# ACOS Oracle Protocol

## Overview

The Oracle is ACOS's permission governance system — a temperature-scoring PreToolUse hook that auto-approves low-risk tool calls and escalates high-risk ones to the user. This skill manages its configuration **and** controls session-scoped Autopilot mode (auto-accept all prompts including AskUserQuestion / ExitPlanMode, with destructive-delete escalation preserved).

Configuration file: `.acos/config/oracle.yaml`
Audit log: `.acos/state/oracle-audit.log`
Session override: `.acos/state/oracle-session-threshold`
Autopilot sentinel: `.acos/state/autopilot-active` (JSON; presence = autopilot ON)
Autopilot loop state: `.acos/state/autopilot-loop-state.json`

## Phase 0: Subcommand Routing (runs before everything else)

Inspect skill invocation arguments (`$ARGUMENTS`). Match the first token, then **delegate to `autopilot-activate.py` for deterministic behavior** — do not re-implement the logic interpretively.

| First token in $ARGUMENTS | Bash command to run | Then |
|---|---|---|
| `autopilot-on` | `python3 .claude/scripts/autopilot-activate.py on "<rest of $ARGUMENTS as goal>" [--max-iter N]` | Show script output verbatim to user. **Do NOT** re-ask the user to confirm the goal — the script handles pre-flight, sentinel write, audit log, and reports termination conditions. Do show the safety contract block below ONCE before running, so the user sees what they're agreeing to. If script exits non-zero, surface the error and stop. |
| `autopilot-off` | `python3 .claude/scripts/autopilot-activate.py off` | Show output. Exit. |
| `autopilot-status` | `python3 .claude/scripts/autopilot-activate.py status` | Show output. Exit. |
| `autopilot-preflight` | `python3 .claude/scripts/autopilot-activate.py preflight` | Show output. Exit. |
| (no argument or other token) | proceed to Phase 1 (legacy Oracle configuration flow) | — |

### Argument parsing for `autopilot-on`

Extract `--max-iter N` from `$ARGUMENTS` if present; pass it through to the script. Everything else is the goal text, passed as positional arguments to the script.

**If $ARGUMENTS contains explicit goal text (the existing path):**

- `/acos-oracle-protocol autopilot-on Build the dataroom for Vaughn-Mora`
  → `python3 .claude/scripts/autopilot-activate.py on "Build" "the" "dataroom" "for" "Vaughn-Mora"`
- `/acos-oracle-protocol autopilot-on --max-iter 200 Refactor the test suite to vitest`
  → `python3 .claude/scripts/autopilot-activate.py on --max-iter 200 "Refactor" "the" "test" "suite" "to" "vitest"`

**If $ARGUMENTS is empty or contains only `--max-iter N` (no goal text — implicit-goal mode):**

This mode is intended for after running a pre-engineering skill (like acos-genesis-protocol) that produces a vision artifact. Follow these steps:

1. **Check `memory/source-of-truth/vision-document.md`** (the ACOS convention vision path).
   - If the file exists and is non-empty: read it. Identify the core goal / success criteria. Compose a **1–3 sentence summary** that captures what "done" looks like. The summary will be injected on every iteration so keep it tight.
   - If the file does NOT exist: proceed to step 2.

2. **Decipher the goal from the current conversation context.** Look at the most recent skill outputs (the user has likely just run acos-genesis-protocol or a similar pre-engineering skill). Identify:
   - The vision statement
   - The acceptance criteria / definition of done
   - Any explicit deliverables mentioned
   Compose a 1–3 sentence summary capturing those.

3. **Confirm with the user via AskUserQuestion** — single question, one option labeled `(Recommended)` containing your composed summary, plus an `Other` path so the user can revise. Example header: "Confirm goal." This is the one-and-only confirmation step before autopilot starts the loop.

4. **Run the activate command** with the confirmed summary:
   - If step 1 found the vision file:
     `python3 .claude/scripts/autopilot-activate.py on --goal-file memory/source-of-truth/vision-document.md "<confirmed summary>" [--max-iter N]`
   - If step 1 found nothing (context fallback):
     `python3 .claude/scripts/autopilot-activate.py on "<confirmed summary>" [--max-iter N]`

The `--goal-file` flag stores the absolute path in the sentinel so the Stop hook's continuation directive includes `GOAL_FILE: <path>  (re-read this anytime for the full vision)` on every iteration. This means Claude can always go back to the source of truth even after eternity-protocol `/clear` cycles — the file path persists, even when the conversation context resets.

### Safety contract (show ONCE before running `on`)
   > **Autopilot will auto-approve:**
   > - All tool permission prompts (Bash, Edit, Write, Task)
   > - `(Recommended)` options on AskUserQuestion (else first option)
   > - ExitPlanMode confirmations
   > - WebFetch / WebSearch (any domain)
   > - MCP server tools (`mcp__*`) — note: MCP server `deny` is broken in
   >   Claude Code (#33106), so blocking destructive MCP actions is impossible
   >
   > **Autopilot will LOG-AND-ALLOW these destructive patterns** (entries
   > written to `.acos/state/requested-destructive.log` for your morning review;
   > the action still proceeds — no denial):
   > - `rm -rf` against $HOME, /, ., .., project root  (INCLUDING `rm -rf /`)
   > - `xargs rm`
   > - `shred`
   > - `dd` to `/dev/{zero,null,random,urandom,sd*,nvme*,disk*}`
   >
   > **The following are now ENTIRELY UNBLOCKED under autopilot** (no log, no
   > escalation — trusted to Claude's judgment per user spec 2026-06-05):
   > - `find ... -delete` (mass deletion by pattern)
   > - SQL destructive ops (DROP TABLE/DATABASE/SCHEMA, TRUNCATE, DELETE without WHERE)
   >
   > **Autopilot CANNOT prevent these (no hook layer exists for them):**
   > - OS-level dialogs (macOS Accessibility, Screen Recording, network consent)
   > - Subprocess password prompts (sudo, GPG signing, ssh keys, npm 2FA, git credentials)
   > - Claude's own safety refusals
   > - Anthropic rate-limit / quota exhaustion errors
   >
   > **Behavior with eternity-protocol (cmux variant):**
   > - Autopilot SURVIVES /clear cycles. The UserPromptSubmit hook detects
   >   pending-resume markers and exempts them from panic-stop.
   > - Iteration count, goal text, and tool-call history persist in the sentinel
   >   across context wraps.
   > - Combined with eternity-protocol-cmux, autopilot can run indefinitely
   >   (subject to the 50-iter / idle / goal-complete brakes).
   >
   > **Continuation loop will TERMINATE on:**
   > - `AUTOPILOT_GOAL_COMPLETE` marker phrase from Claude (graceful exit)
   > - Iteration count >= max_iterations (default 150, overridable with `--max-iter`)
   > - Five consecutive iterations with zero tool calls (idle exit)
   > - Explicit deactivation: `/acos-oracle-protocol autopilot-off` (inside Claude)
   >   or `python3 .claude/scripts/autopilot-activate.py off` (any shell)
   >
   > **User messages during autopilot are treated as MID-COURSE GUIDANCE**,
   > not stop signals. Claude reads them, responds, and continues. The only
   > way to stop autopilot is via the explicit deactivation paths above or
   > the natural exit conditions.
   >
   > **Autopilot does NOT persist across sessions** — SessionEnd cleans it up.
   >
   > **Cmux + eternity-protocol-cmux dependency** — For autopilot runs that
   > may cross 400k tokens, eternity-protocol-cmux MUST be active in your
   > cmux session for autopilot to survive `/clear` cycles. Without it,
   > autopilot dies at 400k like any session. Verify with `cat ~/Library/Application\ Support/acos-token-monitor/config.yaml`.

After showing the safety contract, **run the activate-script command** and surface its output. The script does everything else: pre-flight, sentinel write, audit log, termination-condition summary. Do NOT add additional confirmation prompts after the safety contract.

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
