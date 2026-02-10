---
name: quality-gates
description: Structured guidance for setting up automated quality gates (lint, typecheck, tests) in a project. Quality gates run as part of slice execution before review.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Quality Gates Skill

## Purpose

This skill helps projects define automated quality checks that ACOS runs as part of the slice execution workflow. Quality gates are toolchain-agnostic — projects define their own commands.

## When to Use

Apply this skill when:
- Setting up a new project that needs automated checks
- Adding or modifying quality gates for an existing project
- Debugging why a quality gate is failing during slice execution

## How Quality Gates Work in ACOS

1. Projects define gates in `.acos/config/quality-gates.yaml`
2. During slice execution, after the Developer finishes implementation, `run-quality-gates.sh` runs all gates for the configured stage
3. If any **required** gate fails, the slice goes back to the Developer for fixes
4. If all required gates pass, the slice proceeds to review
5. If no config file exists, ACOS skips quality gates entirely (fail-open)

## Skill Protocol

### Phase 1: Discover Project Toolchain

1. Read the project's `CLAUDE.md` or `package.json` / `pyproject.toml` / `Cargo.toml` to identify:
   - Language and runtime
   - Package manager
   - Linter / formatter
   - Type checker (if applicable)
   - Test runner
2. Check for existing config at `.acos/config/quality-gates.yaml`

### Phase 2: Define Gates

Create or update `.acos/config/quality-gates.yaml` with gates matching the project's toolchain.

Each gate needs:
- **command**: The shell command to run (must exit 0 on success)
- **required**: Whether failure blocks the workflow (`true` = must pass, `false` = advisory)
- **stage**: When the gate runs (`pre-review` = before reviewers, `post-review` = after approval)

### Phase 3: Validate

1. Run `.claude/scripts/run-quality-gates.sh` to verify all gates execute correctly
2. Check that commands exist and are runnable
3. Confirm required vs optional classification makes sense

## Configuration Reference

```yaml
# .acos/config/quality-gates.yaml
gates:
  <gate-name>:
    command: "<shell command>"    # Must exit 0 on success
    required: true|false          # true = blocks workflow on failure
    stage: "pre-review|post-review"
```

### Stage Definitions

| Stage | When it runs | Use for |
|-------|-------------|---------|
| `pre-review` | After developer, before reviewers | Lint, typecheck, unit tests |
| `post-review` | After reviewers approve | Integration tests, E2E tests |

### Gate Runner Output

`run-quality-gates.sh [stage]` outputs JSON:

```json
{
  "passed": true,
  "results": [
    {
      "name": "lint",
      "command": "npm run lint",
      "required": true,
      "stage": "pre-review",
      "passed": true,
      "output": "...",
      "error": ""
    }
  ]
}
```

## Template

See `templates/quality-gates.example.yaml` for an annotated example configuration.

---

*Quality Gates Skill - Automated checks, project-defined.*
