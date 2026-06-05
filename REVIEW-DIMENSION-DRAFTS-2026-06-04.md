# Review-Dimension Additions — DRAFTS for findings 4.7 & 4.8

**Status:** drafts for you to apply. `review-rules/` is human-editable-only **and** the
Independence Wall (fixed 2026-06-04) now blocks the architect/assistant from reading or
writing it; `.claude/agents/` is human-approval-only. So these are paste-ready — I cannot
apply them myself.

**Matcher note (important):** `assign-reviewers.sh` was hardened on 2026-06-04 (finding 4.6).
Trigger matching now is:
- `trigger_file_paths` / `trigger_code_patterns` entries containing `* ? [ ]` → glob (fnmatch)
- entries containing `/` → substring (path fragment)
- bare words → **word boundary** (so `key` no longer matches `monkey.ts`)

➡️ Write code-pattern triggers as **clean alphanumeric tokens** (`aria`, `role`, `button`)
or **file globs** (`*.tsx`). Avoid punctuation-laden patterns like `aria-`, `<button`,
`role=` — they won't match under the word-boundary rule.

Each new reviewer needs **two** files:
1. `review-rules/<name>-reviewer.yaml` — the trigger rule (you paste; filename MUST end
   `-reviewer.yaml` so `assign-reviewers.sh`'s `*-reviewer.yaml` glob picks it up).
2. `.claude/agents/<name>-reviewer.md` — the agent definition (human-approval-only).

---

## Finding 4.7 — Missing review dimensions

Priority recommendation: **accessibility** and **license** are the highest-value, most
concretely-triggerable for your current work (visual-composer UI + dependency hygiene).
`observability` is valuable for services; `data-integrity` and `cost` are situational —
add when relevant.

### 4.7.a — `review-rules/accessibility-reviewer.yaml`

```yaml
# Accessibility (WCAG) reviewer — triggers on UI/frontend work.
name: accessibility-reviewer
always_required: false
trigger_file_paths:
  - "*.tsx"
  - "*.jsx"
  - "*.vue"
  - "*.svelte"
  - "*.html"
  - "*.css"
  - "*.scss"
  - "components"
trigger_code_patterns:
  - "aria"
  - "role"
  - "tabindex"
  - "alt"
  - "button"
  - "onKeyDown"
  - "focus"
  - "contrast"
# Escalate at higher planning levels only if UI files are in scope (inherits slice triggers).
```

### 4.7.b — `review-rules/license-reviewer.yaml`

```yaml
# Open-source license / dependency-compliance reviewer — triggers on dependency manifests.
name: license-reviewer
always_required: false
trigger_file_paths:
  - "package.json"
  - "pnpm-lock.yaml"
  - "yarn.lock"
  - "package-lock.json"
  - "requirements.txt"
  - "pyproject.toml"
  - "Cargo.toml"
  - "go.mod"
  - "Gemfile"
trigger_code_patterns: []
```

### 4.7.c — `review-rules/observability-reviewer.yaml`

```yaml
# Observability reviewer — triggers on logging/tracing/metrics + service code.
name: observability-reviewer
always_required: false
trigger_file_paths:
  - "*.ts"
  - "*.py"
  - "*.go"
  - "services"
  - "server"
  - "api"
trigger_code_patterns:
  - "logger"
  - "console"
  - "trace"
  - "span"
  - "metric"
  - "telemetry"
  - "OpenTelemetry"
  - "Sentry"
trigger_file_count_gt: 10
```

### 4.7.d / 4.7.e — templates for `data-integrity-reviewer` and `cost-reviewer`

```yaml
# review-rules/data-integrity-reviewer.yaml
name: data-integrity-reviewer
always_required: false
trigger_file_paths:
  - "migrations"
  - "schema"
  - "*.sql"
  - "models"
trigger_code_patterns:
  - "migrate"
  - "ALTER"
  - "DELETE"
  - "UPDATE"
  - "transaction"
  - "rollback"
```

```yaml
# review-rules/cost-reviewer.yaml
name: cost-reviewer
always_required: false
trigger_file_paths:
  - "*.tf"
  - "Dockerfile"
  - "docker-compose*"
  - "*.k8s.yaml"
  - "infra"
  - "terraform"
trigger_code_patterns:
  - "instance_type"
  - "replicas"
  - "autoscaling"
  - "gpu"
```

### Companion agent definition (one per new reviewer) — e.g. `.claude/agents/accessibility-reviewer.md`

Mirror the existing reviewer agents' isolation contract (verified from `qa-reviewer.md`).
Swap `<DIMENSION>` / `<name>` per reviewer.

```markdown
---
name: accessibility-reviewer
description: Adversarial accessibility (WCAG 2.1 AA) reviewer. Read-only, isolated. Verifies keyboard nav, semantic markup, ARIA correctness, contrast, focus management. Assumes UI is inaccessible until proven otherwise.
tools: Read, Glob, Grep, Bash
disallowedTools: Write, Edit, Task, WebSearch, WebFetch
model: opus
permissionMode: plan
maxTurns: 30
isolation: worktree
---

# Accessibility Reviewer

## CRITICAL ADVERSARIAL DIRECTIVE
You are the accessibility line of defense. **Assume the UI is inaccessible until proven otherwise.**

## What you verify
- Keyboard operability (every interactive element reachable + operable without a mouse; focus order logical; no traps)
- Semantic HTML + correct ARIA roles/states (no role misuse; name/role/value present)
- Text alternatives (alt text, labels for inputs, accessible names for icon buttons)
- Color contrast ≥ WCAG AA; information not conveyed by color alone
- Focus management for dynamic content (modals, route changes, live regions)
- Motion/animation respects prefers-reduced-motion

## Output (structured verdict — recorded by the orchestrator)
- verdict: PASS or REJECT
- scores per category
- issues list (WCAG criterion + location)
- required fixes (if REJECT)
- checks_performed: list of what you actually verified (REQUIRED — a PASS with no
  checks_performed is flagged as a rubber-stamp by aggregate-verdicts.sh)
```

> After adding each agent file, also update `MEMORY.md`'s agent count and the project
> `CLAUDE.md` "Agent Roster" if you want it listed.

---

## Finding 4.8 — `legal-analyst` can never be auto-assigned

Two root causes (verified):
1. `assign-reviewers.sh` globs `*-reviewer.yaml` → `legal-analyst.yaml` (ends `-analyst.yaml`) is excluded.
2. `legal-analyst.yaml` self-declares **non-gating** (advisory findings, not PASS/REJECT).

So it can't just be renamed into the gating reviewer set — that would force it to return
PASS/REJECT it isn't designed to. The right shape is an **advisor** path.

### Your part (review-rules): keep `legal-analyst.yaml` advisory, ensure its triggers are good

No new file needed. Just confirm `legal-analyst.yaml` has `trigger_file_paths` covering
your legal surface, e.g.:

```yaml
# (additions to the existing review-rules/legal-analyst.yaml trigger_file_paths)
trigger_file_paths:
  - "loan"
  - "promissory"
  - "guaranty"
  - "deed"
  - "SNDA"
  - "title"
  - "covenant"
  - "legal"
# keep the existing "advisory / non-gating" declaration as-is
```

### My part (non-restricted, on your go): advisor mechanism in `assign-reviewers.sh` + surfacing

I can implement this without touching `review-rules/`:
- `assign-reviewers.sh`: additionally scan advisory rule files (e.g. `*-analyst.yaml` or files
  with an `advisory: true` key), evaluate their triggers with the same `_matches()` logic, and
  write any matches to a side file `.acos/state/review-advisors/<slice>.json` (keeping the
  stdout reviewer array unchanged so nothing breaks).
- `acos-execute-slice`: after the mechanical gate, read that advisor file and **surface** the
  advisor's findings to the human as non-gating diligence notes (they don't block, but they're
  no longer silently dropped).

This closes 4.8 (legal-analyst is consulted on legal-touching slices) without making it a
hard gate. Say the word and I'll implement + verify the script half.

---

*Drafts generated 2026-06-04. Apply the YAML/agent files yourself (walled paths); ping me to
do the `assign-reviewers.sh` advisor half for 4.8.*
