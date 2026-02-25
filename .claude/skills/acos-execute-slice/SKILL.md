---
name: acos-execute-slice
description: Executes a single slice from assignment through implementation, evidence, review, and completion. The fundamental work unit. Use with $ARGUMENTS for the slice ID.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
context: fork
agent: architect
---

# Slice Execution

## Overview

This skill orchestrates the complete execution of a single slice: reading the spec, delegating to the developer, running programmatic reviewer assignment, spawning parallel reviewers, and handling pass/reject outcomes. This is the fundamental work unit of ACOS.

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

This is idempotent — it exits immediately if ACOS is already initialized. If not, it runs the full bootstrap (symlinks, directories, config, gitignore).

## Protocol

### Step 1: Read Slice Specification

Read the slice spec from `planning/slices/$ARGUMENTS.yaml`. Extract:
- Objective
- Acceptance criteria
- Files allowed to modify
- Dependencies (verify all are complete)
- Recommended skills

### Step 2: Set Active Slice (Scope Enforcement)

Write the scope configuration to `.acos/config/active-slice.yaml`:

```yaml
slice_id: "$ARGUMENTS"
files_allowed:
  - [list from slice spec]
activated_at: "[timestamp]"
```

This enables the `check-scope.sh` PreToolUse hook to mechanically block writes outside the allowed files list.

### Step 3: Create Evidence Bundle Structure

Run `.claude/scripts/create-evidence-bundle.sh $ARGUMENTS` to create the evidence directory structure.

### Step 4: Delegate to Developer

**Model Resolution:** Before spawning the developer, resolve its model:
```bash
bash .claude/scripts/resolve-agent-model.sh developer
```
Then pass: `Task(developer, model: $RESOLVED_MODEL)`. If resolution fails, use the agent's default model.

Use `Task(developer)` to delegate implementation. Pass in the prompt:
- Slice ID and objective
- All acceptance criteria
- Files allowed to modify
- Relevant source of truth excerpts (read from `memory/source-of-truth/vision-document.md`)
- Recommended skills to apply
- Evidence bundle path

The developer works in an isolated context and returns a structured result with:
- Files modified
- Acceptance criteria addressed
- Evidence bundle path
- Any issues encountered

### Step 5: Run Quality Gates (Pre-Review)

Run `.claude/scripts/run-quality-gates.sh pre-review` to execute project-defined quality checks.

Parse the JSON output:
- If `"passed": true` (or `"skipped": true`): proceed to Step 6 (reviewer assignment)
- If `"passed": false`: return the failing gate results to the Developer via `Task(developer)` with fix instructions. After the Developer resubmits, re-run quality gates. Maximum 3 quality gate iterations before escalating to human.

Quality gates are optional — if no `.acos/config/quality-gates.yaml` exists, the script outputs `{"passed": true, "skipped": true}` and execution continues normally.

### Step 6: Run Reviewer Assignment

Programmatically assign reviewers by piping a JSON manifest to `.claude/scripts/assign-reviewers.sh`:

```json
{
  "slice_id": "$ARGUMENTS",
  "files_modified": ["list from developer result"],
  "code_snippets": ["key patterns found in modified files"],
  "review_level": "slice"
}
```

The script reads per-reviewer files from `review-rules/` (which the Architect cannot read directly — the script does it mechanically) and outputs a JSON array of reviewer names.

### Step 7: Spawn Reviewers in Parallel

**Model Resolution & Dispatch:** Before spawning each reviewer, resolve its model:
```bash
RESOLVED=$(bash .claude/scripts/resolve-agent-model.sh [reviewer-name])
```

**If the resolved model is a bare Claude name** (`opus`, `sonnet`, `haiku` — no `:` in string):
Use `Task([reviewer-name])` with `model: $RESOLVED`, `run_in_background: true`, `isolation: worktree`.

**If the resolved model contains `:`** (e.g., `openai:gpt-4o`, `openrouter:google/gemini-2.5-pro`):
Use `Bash(run_in_background: true)` to call the external agent runner:
```bash
python3 .claude/scripts/run-external-agent.py \
  --agent [reviewer-name] \
  --model "$RESOLVED" \
  --task "[review prompt with evidence content]" \
  --context [modified files from evidence bundle]
```
For external models, pass all modified files (from `after/modified-files.txt`) as `--context` arguments since external models cannot access the file system.

If resolution fails for any reviewer, fall back to `model: opus` via Task().

For each assigned reviewer, spawn simultaneously. Pass to each:
- Evidence bundle path: `.acos/evidence/[DATE]/$ARGUMENTS/`
- Source of truth path: `memory/source-of-truth/vision-document.md`
- Slice spec path: `planning/slices/$ARGUMENTS.yaml`

Each reviewer returns a structured verdict:
- verdict: PASS or REJECT
- scores per category
- issues list (if any)
- required fixes (if REJECT)

### Step 8: Aggregate Verdicts

Collect all reviewer verdicts:
- If **ALL PASS**: proceed to Step 10 (Completion)
- If **ANY REJECT**: proceed to Step 9 (Feedback Resolution)

### Step 9: Feedback Resolution (on REJECT)

Invoke the `acos-feedback-resolution` skill with:
- All reviewer feedback consolidated
- Slice spec
- Evidence bundle path
- Max 3 resolution iterations

If feedback resolution succeeds (all reviewers pass on re-review), proceed to Step 10.
If feedback resolution fails after 3 iterations, escalate to human.

### Step 10: Completion

1. Update slice status in `planning/slices/$ARGUMENTS.yaml` to `status: completed`
2. Clear `.acos/config/active-slice.yaml` (remove scope restrictions)
3. Write summary log to `memory/handoffs/` for audit trail
4. Report completion

## Error Handling

| Stage | Error | Response |
|-------|-------|----------|
| Slice spec not found | Missing file | Report error, abort |
| Developer Task fails | Implementation error | Retry once, then escalate |
| Quality gates fail | Required gate returns non-zero | Return to Developer (max 3x) |
| Reviewer assignment | Script error | Default to ["qa-reviewer"] |
| Reviewer Task fails | Review error | Retry once |
| Max feedback iterations | Still failing | Escalate to human |

---

*Slice Execution - The fundamental unit of ACOS work.*
