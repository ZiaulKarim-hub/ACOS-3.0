---
name: acos-oracle-protocol
description: Configures The Oracle permission governance system. FOUR settings, and only one is ever on - /acos-oracle-protocol 1 to 10 (the dial, how loose ordinary scoring is), autopilot (allows, logs the truly destructive, runs the goal loop), yolo (allows everything, records nothing, bypasses hard blocks), and oracle (Opus judges every gated call in context and you are never asked). autopilot, yolo and oracle each REQUIRE a goal. The numbers 11 and 12 are gone from the interface - they were never really rungs, so they became words. Also manages hard blocks, modifiers, learned patterns, the audit log, and status/follow for the Oracle daemon. The separate 'activate session autopilot' command is gone; it is the autopilot setting now.
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

**The four settings. Only one is ever on — choosing any clears the others.**

| Type | Setting | Goal? |
|---|---|---|
| `/acos-oracle-protocol 1` … `10` | the dial — how loose ordinary scoring is | no |
| `/acos-oracle-protocol autopilot "<goal>"` | allows, WRITES DOWN the truly destructive, runs the goal loop | **yes** |
| `/acos-oracle-protocol yolo "<goal>"` | allows everything, records nothing, bypasses hard blocks | **yes** |
| `/acos-oracle-protocol oracle "<goal>"` | Opus judges every gated call; you are never asked | **yes** |

Route all four through the control script — do not re-implement them here:

```bash
CTL=".claude/scripts/oracle/oracle-ctl.ts"
bun "$CTL" 7                                   # the dial
bun "$CTL" autopilot "<goal>"                  # was threshold 11
bun "$CTL" yolo "<goal>"                       # was threshold 11, then 12
bun "$CTL" oracle "<goal>"                     # Oracle mode
bun "$CTL" status                              # what is on, today's verdicts
bun "$CTL" follow                              # watch decisions live
bun "$CTL" stop                                # leave oracle, back to the old number
```

**Why words and not numbers.** 11 and 12 were never really rungs on a dial:
autopilot runs a goal loop and YOLO switches the rules off, so numbering them
implied a smooth ramp that does not exist (Zee, 2026-08-16). They survive as
numbers ONLY inside the hook, which still compares a threshold. Typing `11` or
`12` is refused, and the error names the word that replaced it.

**Offer `oracle` FIRST whenever he wants autonomy.** It is the only setting that
buys autonomy without giving up judgement. `yolo` gives up judgement entirely;
`autopilot` only writes a note afterwards.

1. **Quick Presets** (the dial only):
   - `strict` (3): Asks about edits, writes, and most bash commands.
   - `balanced` (5): Approves reads, basic edits, tests, lints.
   - `autonomous` (8): Minimal prompts. Only sensitive writes and destructive bash escalate.
   - `default` (9): Auto-approves everything except destructive bash and hard blocks.
   - `permissive` (10): Approves everything except hard blocks.

2. **Tune the dial** — any value 0-10. 0 asks about everything; 10 approves
   everything except hard blocks. Above 10 there are no numbers, only the words.

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
1. **If `yolo` was selected**, display this warning and require explicit confirmation before applying:
   > **WARNING: YOLO mode disables ALL safety guardrails.**
   > Hard-blocked commands (git push, rm -rf /, DROP TABLE, git reset --hard main)
   > will be auto-approved without any prompt. This is irreversible once executed.
   > Nothing is judged and nothing is recorded.
   > If you want autonomy WITH judgement, use Oracle mode instead: it never asks
   > you either, but Opus reads each call first.
   > Are you sure you want to enable YOLO mode?
   - Do NOT apply `yolo` without the user typing explicit confirmation.
   - `autopilot`, `yolo` and `oracle` all REFUSE without a goal — that refusal is
     by design, not a bug to work around.
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
| autopilot | (word) | Everything, but destructive ops are written to `requested-destructive.log` | Nothing (hard blocks still deny) |
| yolo | (word) | Everything including hard blocks | Nothing at all |

## Oracle Mode — the switch, not a rung

**What it is.** Opus sits at the permission door. Every call that would normally
stop and ask Zee is handed to it instead, with the command, the recent chat, and
the session's goal. It answers allow or deny. Zee is never asked.

**Why it has no number.** The 1-12 dial measures how LOOSE the rules are. The
Oracle is not looser than anything — it is a different axis entirely, where the
rules get *judged* rather than relaxed. Putting it at 12 taught the wrong thing
(Zee, 2026-08-16: "12 is actually the wrong number for this"), so it became a
switch and 12 went back to meaning YOLO.

```bash
CTL="$(git rev-parse --show-toplevel 2>/dev/null || pwd)/.claude/scripts/oracle/oracle-ctl.ts"
bun "$CTL" oracle "<the goal for this session>"  # Oracle ON
bun "$CTL" status                                 # what is on, today's verdicts
bun "$CTL" follow                                 # watch decisions live
bun "$CTL" stop                                   # OFF, back to the previous threshold
bun "$CTL" <1-10> | autopilot "<goal>" | yolo "<goal>"   # the other three
```

**The bar is HARM, not need.** Zee's standing instruction, and the charter quotes
him verbatim: *"give permission to everything unless it is truly going to cause
harm to my system"*, and *"just because an operation is outside the work directory
doesn't automatically mean it is harmful… touching keys or credentials could be
necessary too"*. Deletes, force pushes, writes outside the project and credential
reads are ordinary work. There is deliberately NO hardcoded deny-list — a rule
list would just be the old scoring Oracle wearing a new name.

**The goal is EVIDENCE, not a gate.** Off-topic and harmless is still allow;
wandering is not damage. What the goal buys is the mismatch case: a live test
caught `rm -rf ~/Documents` only because the stated task was "clean temp files in
the build folder". Never let this become an "is it on-task?" test.

**It is never unreachable** (Zee: falling back to YOLO "would be useless"). Five
layers: live socket -> auto-start the daemon -> call the judge directly with no
daemon at all -> retry with backoff -> and only then DENY, naming exactly what
broke. It never silently allows something it has not judged. The cost of that
last layer is real: a machine with no working Claude CLI and no network would
refuse gated tools rather than wave them through.

**Where it sits.** Oracle mode is checked BEFORE the hard-block list and before
autopilot, so at `start` the fixed list gets no vote and autopilot's blanket
allow never runs. That is deliberate — unattended work is when a real judge is
worth most.

**Its own session is exempt.** The Oracle judges by running Claude Code, which
loads this same hook. The child carries a secret matching a 0600 token file, so
it passes instantly instead of asking itself forever. A wrong token does not
bypass anything.

Files: daemon `~/.acos/oracle/`, verdicts `~/.acos/oracle/verdicts.log`,
mode state `.acos/state/oracle-mode.json`, keep-alive
`~/Library/LaunchAgents/com.acos.oracle.plist`.

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
