# Generate: Handoff Skill

Copy this entire prompt into Claude. Fill in the blanks in the YOUR PROJECT section. Claude will generate a /handoff skill you can use to save your session state when the context window gets long.

---

**PROMPT — copy everything below this line:**

I need you to create a Claude Code skill definition for a Handoff protocol. Save it to `.claude/skills/handoff/SKILL.md`.

## MY PROJECT

- **Project name:** [your project name]
- **Tech stack:** [language, framework, database, etc.]
- **Test runner:** [vitest/jest/pytest/cargo test/etc. — or "none"]
- **Build command:** [npm run build / cargo build / etc. — or "none"]

## WHAT THIS SKILL MUST DO

Create a `/handoff` skill that, when invoked, generates a complete session handoff file so the next Claude session can continue without losing any context.

The skill must:

1. **Gather current state automatically:**
   - Read `project-state.md` for task breakdown and status
   - Run `git status` to capture uncommitted changes
   - Run `git log --oneline -10` for recent commits
   - Run the test suite to record pass/fail counts
   - Run the build to confirm it's passing or capture the error

2. **Generate a handoff file** saved to `handoffs/handoff-[YYYY-MM-DD]-[HHMM].md` (create the directory if needed) containing:
   - Session summary (2-3 sentences of what was accomplished)
   - Completed items with file names (checkboxes)
   - Current task status table (every task, its status, notes)
   - What's working (verified and tested)
   - What's broken or blocked (with what would unblock it)
   - Decisions made this session with reasoning and rejected alternatives
   - Git state (branch, last commit, uncommitted files)
   - Build and test status
   - Performance baselines (test suite time, build time, response times if applicable)
   - Technical debt introduced honestly (shortcuts taken, why, how to fix properly)
   - Next steps in exact priority order with reasoning
   - Warnings and gotchas the next session needs to know

3. **Update `project-state.md`** with a session log entry noting the handoff.

4. **Tell the user how to continue** — print instructions:
   > Start a new Claude session, paste the contents of `handoffs/handoff-[file].md`, and say "Continue from this handoff."

5. **Self-check before saving** — verify the handoff answers:
   - Can someone continue from this alone with zero questions?
   - Is the exact next task identified?
   - Are all decisions documented with reasoning?
   - Is the build/test state recorded?
   - Are known issues and fragile areas called out?

## SKILL DEFINITION FORMAT

Use this frontmatter:

```yaml
---
name: handoff
description: Creates a handoff package capturing full project state for session continuity. Run /handoff when context is getting long or when done for the day.
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---
```

Then write the full skill instructions below. The skill should be thorough but fast — gathering state and writing the file shouldn't take more than a couple of minutes.
