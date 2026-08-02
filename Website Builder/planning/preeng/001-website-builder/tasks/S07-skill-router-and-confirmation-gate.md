# S07-skill-router-and-confirmation-gate — Thin router SKILL.md with the mandatory Confirmation Gate

| Field | Value |
|---|---|
| Epic / Story | E1 — Skill scaffold and the TypeScript spine / ST-02 |
| Type · MoSCoW · Size | build · MUST · S `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S01-gate-16a-and-launcher-rung |
| Requirements | FR-010, FR-011 |
| Acceptance criteria | A90 · A87 · A86 |
| CQ / evidence | — |

## PM — slice definition

**Objective.** Ship a thin router skill whose frontmatter is exactly as specified and whose Phase 0 refuses to write anything before an explicit human confirmation.

**In scope.** `SKILL.md` with the nine-phase router structure; the exact frontmatter (`disable-model-invocation: true`, `user-invocable: true`, the argument hint, and `allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion`); the Phase-0 restate-and-confirm gate; an inline main-session execution path for every named feature.

**Out of scope.** Any orchestration logic beyond routing. Declaring `Task` in `allowed-tools`. Creating anything under `.claude/agents/`. Implementing the phases themselves.

**Allowed files / contexts.**
- `SKILL.md` (new), `prompts/*.md` (new role rubrics, executed inline)
- **Forbidden:** `.claude/agents/**` (human-approval-restricted infrastructure), any `Task(` call anywhere in the skill.

**Steps.**
1. Write the frontmatter exactly; verify by grep that `Task` does not appear in `allowed-tools`.
2. Write the nine-phase router: each phase names its script entry point and its exit condition, and nothing else.
3. Implement Phase 0 as a hard gate: restate the understood brief, wait for an explicit confirmation, and only then permit any write or server launch.
4. Add both role rubrics under `prompts/` with an explicit note that they are executed **inline by the main session** using only already-declared tools.
5. Assert with a script: zero files under `.claude/agents/`, zero `Task(` occurrences in the skill tree.

**Definition of Done.**
- Artifacts: `SKILL.md`, both role prompts, the assertion script.
- Validation: `grep -c 'Task' SKILL.md` on the `allowed-tools` line returns 0; a dry run halts at Phase 0 with no file written.
- `slice.yaml` mapping — `acceptance_criteria: [A90, A87, A86]`, `verification_method: grep-assert` (A90: `manual-observation`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-010, FR-011 → `SKILL.md` lines; (3) structural quality — the router contains no business logic; (4) functional testing — a transcript showing Phase 0 halting before any write, and a directory listing proving nothing was created; (5) security/compliance — no new agent files, no undeclared tool; (6) operational — how a user resumes mid-phase; (7) self-assessment.

## QA — zero-trust verification

- **Run your own** `grep -n 'allowed-tools' SKILL.md` and read the line; do not accept a claim.
- **Run your own** `find .claude/agents -type f | wc -l` and require 0.
- **Run your own** `grep -rn 'Task(' <skill tree>` and require zero matches.
- **Reject** if a dry run wrote any file before the confirmation was given — check with a directory hash before and after.
- **Reject** if any named feature has no inline main-session path (the mid-skill subagent question is unresolved and nothing may depend on it).

## Dev Learnings

_Not Done until filled. Required: anything the router made awkward that a phase would have made easy._

## QA Learnings

_Not Done until filled. Required: whether the Phase-0 halt was genuinely enforced or merely documented._
