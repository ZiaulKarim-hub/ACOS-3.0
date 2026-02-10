---
name: ci-cd-generation
description: Generates parameterized CI/CD workflow files based on the project's quality gates and toolchain preferences. Supports GitHub Actions with room for other providers.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# CI/CD Generation Skill

## Purpose

This skill generates CI/CD workflow files that mirror the project's quality gates configuration. Instead of hardcoding a specific toolchain, it reads the project's own definitions and produces matching CI steps.

## When to Use

Apply this skill when:
- Setting up CI/CD for a new ACOS project
- Updating CI workflows after changing quality gates
- Migrating CI between providers (GitHub Actions, GitLab CI, etc.)

## Skill Protocol

### Phase 1: Read Project Configuration

1. Read `.acos/config/quality-gates.yaml` — each gate becomes a CI step
2. Read the project's `CLAUDE.md` for toolchain preferences (runtime, package manager)
3. Read `package.json` / `pyproject.toml` / `Cargo.toml` for dependency info
4. Identify the CI provider (default: GitHub Actions)

### Phase 2: Generate Workflow

For **GitHub Actions** (primary):

1. Create `.github/workflows/ci.yml`
2. Map each quality gate to a workflow step:
   - Gate `command` → step `run`
   - Gate `required: true` → step must pass for workflow to succeed
   - Gate `required: false` → step uses `continue-on-error: true`
   - Gate `stage: pre-review` → runs in the main job
   - Gate `stage: post-review` → runs in a separate job (can be triggered manually or on merge)
3. Add setup steps based on detected toolchain:
   - Node.js projects: `actions/setup-node` + install step
   - Python projects: `actions/setup-python` + install step
   - Rust projects: `actions-rs/toolchain` + cargo build
   - Other: minimal setup, user customizes
4. Configure triggers (push to main, pull requests)

### Phase 3: Validate

1. Verify the generated workflow is valid YAML
2. Confirm all quality gate commands are represented
3. Check that setup steps match the project toolchain

## Output Structure

```yaml
# .github/workflows/ci.yml (generated)
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # ... setup steps (toolchain-specific)
      # ... one step per pre-review quality gate
      # ... required gates fail the workflow
      # ... optional gates use continue-on-error

  # post-review gates (if any) in a separate job
```

## Handling Missing Configuration

- No `quality-gates.yaml` → generate a minimal CI with checkout + build only
- No `CLAUDE.md` toolchain info → infer from project files (package.json, etc.)
- Unknown toolchain → generate skeleton with TODO comments

## Template

See `templates/github-actions.example.yaml` for an annotated reference workflow.

## Supported Providers

| Provider | Status | Output File |
|----------|--------|-------------|
| GitHub Actions | Supported | `.github/workflows/ci.yml` |
| GitLab CI | Skeleton only | `.gitlab-ci.yml` |
| Other | Not yet | — |

---

*CI/CD Generation Skill - Your quality gates, automated in CI.*
