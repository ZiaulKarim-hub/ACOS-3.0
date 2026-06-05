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

### Step 1.5: Retrieve Prior Learnings (RAG)

Before implementing, query the memory index for lessons relevant to this slice so the developer benefits from past experience rather than re-discovering known gotchas:

```bash
bash .claude/scripts/rag-query.sh --query "<slice objective + key files/domain>" --top-k 6
```

- Build the query from the slice objective and the domain of its `files_allowed`.
- Scan `results[]` for `category: learning` (patterns/anti-patterns), `category: decision` (constraints to honor), and `category: handoff` (prior gotchas in this area).
- Carry the relevant findings into the developer prompt in Step 4 (see the "Relevant prior learnings" bullet).
- **Fallback:** if the JSON has `"fallback": true`, grep `memory/` and `learning-curve/` instead. Do **not** skip silently.

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
- Relevant prior learnings retrieved in Step 1.5 (patterns to reuse, anti-patterns/gotchas to avoid — include the source `path` for each)
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
- **Evidence-authority directive (do NOT rely on developer self-report):** the mechanical quality-gate output from Step 5 (`run-quality-gates.sh`) is the authoritative functional check. The developer-authored `verify.log` / `Summary.md` are claims, not proof — independently derive at least one verification from the slice's acceptance criteria and run it yourself rather than only re-running the commands the developer chose to record.

Each reviewer returns a structured verdict:
- verdict: PASS or REJECT
- scores per category
- issues list (if any)
- required fixes (if REJECT)
- `checks_performed`: a list of what the reviewer actually verified (**required** — the gate flags a PASS with no issues *and* no `checks_performed` as a possible rubber-stamp; see Step 8 warnings)

### Step 8: Aggregate Verdicts (Mechanical Gate)

Verdict aggregation is **mechanical** — the Architect records raw verdicts but does **not** decide the gate. This prevents the orchestrator (the entity the Independence Wall guards against) from rationalizing a borderline REJECT into a PASS.

1. Write the assigned reviewer list (from Step 6) to `.acos/state/review-verdicts/$ARGUMENTS/expected.json` — a JSON array of reviewer names.
2. For each reviewer that returned, write its verdict verbatim to `.acos/state/review-verdicts/$ARGUMENTS/<reviewer>.json`:
   ```json
   {"reviewer": "<name>", "verdict": "PASS|REJECT|INCONCLUSIVE", "issues": [...], "checks_performed": [...]}
   ```
   Record faithfully. A crashed/failed reviewer that returned nothing gets **no file** — the gate treats a missing expected reviewer as INCONCLUSIVE (blocking). The script's `warnings[]` flags any PASS lacking both issues and `checks_performed` (possible rubber-stamp) — surface these to the human; do not silently accept.
3. Run the authoritative gate:
   ```bash
   bash .claude/scripts/aggregate-verdicts.sh $ARGUMENTS
   ```
4. **Obey the exit code — you MUST NOT override it:**
   - exit 0 (`decision: PASS`, every expected reviewer PASS) → proceed to Step 10 (Completion).
   - exit 2 (any REJECT / INCONCLUSIVE / missing reviewer) → proceed to Step 9 (Feedback Resolution); the JSON `failures[]` lists which reviewers blocked and why.

   Do not proceed to completion on a non-zero exit, regardless of your own read of the reviews.

### Step 9: Feedback Resolution (on REJECT)

Invoke the `acos-feedback-resolution` skill with:
- All reviewer feedback consolidated
- Slice spec
- Evidence bundle path
- Max 3 resolution iterations

If feedback resolution succeeds (all reviewers pass on re-review), proceed to Step 10.
If feedback resolution fails after 3 iterations, escalate to human.

### Step 10: Completion

1. **Advisory review (non-gating).** Read `.acos/state/review-advisors/$ARGUMENTS.json` (written by `assign-reviewers.sh`). For each advisor listed (e.g. `legal-analyst`), spawn it via `Task()` (model-resolved like a reviewer) with the same evidence-bundle / slice-spec / source-of-truth context. Advisor output is **diligence findings, NOT a gate** — record it in the completion summary and surface it to the user, but do **NOT** block completion on it. (This is how legal-analyst is consulted on legal-touching slices without forcing it to emit PASS/REJECT — finding 4.8.)
2. Update slice status in `planning/slices/$ARGUMENTS.yaml` to `status: completed`
3. Clear `.acos/config/active-slice.yaml` (remove scope restrictions)
4. Write summary log to `memory/handoffs/` for audit trail (include advisor findings)
5. Report completion

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
