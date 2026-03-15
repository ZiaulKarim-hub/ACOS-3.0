# ACOS v3.0 — Agentic Coding Orchestration System

## System Overview
ACOS is a multi-agent orchestration system for software development. It implements
a planning hierarchy (Vision > Epic > Story > Slice), an independence-walled
review system, and cross-project learning.

## Key Principles
- The Architect plans and orchestrates. Reviewers verify independently.
- The Independence Wall: Reviewers NEVER see Architect decisions. The Architect
  NEVER sees review rules (review-rules/ directory). This is mechanically enforced
  by agent tool restrictions and hook guards.
- All work produces evidence bundles in .acos/evidence/
- Planning artifacts live in planning/ (vision, epics, stories, slices)
- Memory artifacts live in memory/ (source-of-truth, decisions, reviews, handoffs)

## Auto-Handoff System
- Stop hook estimates token usage from transcript content (~3 chars/token + 30k
  system overhead), fires once per session at ~100k tokens (~50%). Creates a
  semantic handoff via /acos-handoff-protocol.
- Token-gate (PreToolUse) enforces handoff with staleness detection: if tokens grew
  >20k since the last handoff was created, it demands a FRESH handoff. Hard ceiling at 130k.
- Context compaction triggers at 69% (~138k tokens) via CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=69.
  This fires ~8k tokens after the Stop hook, just after the handoff is saved.
- SessionEnd hook (session-cleanup.sh) removes ephemeral state files (.token-gate-cache,
  .handoff-enforcement, .stop-retry-count, continue markers) to prevent stale state.
- PreCompact hook creates a mechanical handoff (`status: mechanical`) before compaction.
- SessionStart hook auto-loads ALL **active** handoffs (newest first) + accepted ADRs
  from memory/decisions/, within a 25k token budget. Falls back to mechanical handoffs
  if no active ones exist. Skips `status: completed`.
- Handoff lifecycle: handoffs stay `status: active` until user runs `/acos-complete`.
  `/acos-complete` marks all active handoffs as completed and moves them to
  `memory/handoffs/archive/`. Next session starts with clean context.
- No time-based expiry — status lifecycle handles staleness.
- Handoff files: memory/handoffs/ | Archive: memory/handoffs/archive/ | Runtime: .acos/state/

## The Oracle (Permission Governance)
- PreToolUse hook that scores every tool call on a temperature scale (0=safe, 10=dangerous).
- Actions at or below the threshold are auto-approved silently. Above threshold → user prompt.
- No hard blocks — all operations go through temperature scoring. Destructive commands
  (rm -rf, git reset --hard) score high (+5) and escalate to user at most thresholds.
- Config: `.acos/config/oracle.yaml` (per-project, user-editable).
- Session override: `.acos/state/oracle-session-threshold` file.
- Audit trail: `.acos/state/oracle-audit.log` (escalations and denials only).
- Default threshold: 9. Range: 0 (ask everything) to 10 (permissive) to 11 (YOLO — bypasses hard blocks).
- Fail-open: missing config or errors default to allow. The Oracle is a convenience layer.
- Configure with `/acos-oracle-protocol`. Supports custom modifiers and learned patterns.
- Risk-tiered: Oracle only evaluates Bash, Write, Edit, NotebookEdit, Task. Read-only tools exempt.
- Fail-safe: shell-level `|| printf 'allow'` fallback prevents tool lockout if script errors.
- No git dependency: hooks resolve paths via CWD and `__file__`, not `git rev-parse`.
- Health check: `python3 .claude/scripts/oracle-evaluate.py --health` verifies all dependencies.
- Hook ordering: Oracle (Bash|Write|Edit|NotebookEdit|Task) → check-scope.sh (Write|Edit only) → execute.

## Model Profile System
- Controls which model each agent uses when spawned — supports Claude AND external models.
- Claude-only presets: Budget (haiku-heavy), Standard (sonnet), Premium (opus, default), Auto (smart mix).
- Multi-provider presets: Hybrid-Review, Free-Tier, OpenAI-Review, Gemini-Review.
- Config: `.acos/config/model-profile.yaml` (per-project, persistent defaults).
- Provider registry: `.acos/config/providers.yaml` (OpenAI, Google, OpenRouter, Custom endpoints).
- Session state: `.acos/state/model-session.yaml` (ephemeral, cleaned by SessionEnd).
- Resolution: `resolve-agent-model.sh <agent-name>` → outputs model spec.
  - Claude models: bare name (`opus`, `sonnet`, `haiku`) → dispatched via Task().
  - External models: `provider:model` (e.g., `openai:gpt-4o`) → dispatched via run-external-agent.py.
- Safety gate: architect and developer MUST use Claude (tool access required). External models
  silently fall back to Claude defaults.
- External agent runner: `.claude/scripts/run-external-agent.py` — calls OpenAI-compatible APIs
  with agent system prompts and pre-bundled code context. Python 3 stdlib only.
- Resolution order: session custom override → session profile → config default profile → hardcoded fallback.
- Main conversation model is advisory only — requires user to run `/model` to change.
- Configure with `/acos-model-change`. Profile selection also offered during `/acos-start`.
- Orchestration skills call `resolve-agent-model.sh` before every agent spawn, then dispatch
  to Task() (Claude) or Bash+run-external-agent.py (external) based on the result.

## Planning Hierarchy
Vision (source of truth) > Epic (capability) > Story (user value) > Slice (atomic work)

## Agent Roster
- **architect** — Strategic orchestrator. Spawns all other agents via Task().
- **developer** — Implements code within scope boundaries.
- **qa-reviewer** — Adversarial quality verification (read-only, isolated).
- **security-reviewer** — OWASP-focused security analysis (read-only, isolated).
- **performance-reviewer** — Algorithmic and resource efficiency (read-only, isolated).
- **integration-reviewer** — Cross-component coherence (read-only, isolated).
- **memory-agent** — RAG retrieval and memory organization.
- **learning-agent** — Cross-project knowledge extraction and application.
- **loan-doc-phase1** — Phase 1 orchestrator for loan document generator (design extraction).
- **loan-doc-phase2** — Phase 2 orchestrator for loan document generator (loan folder analysis).
- **loan-doc-phase34** — Phase 3+4 orchestrator for loan document generator (design + validation + Wigum loop).

## Review Process
Reviews are assigned programmatically by .claude/scripts/assign-reviewers.sh
based on per-reviewer trigger files in review-rules/ (file paths, code patterns).
Each reviewer has its own YAML file declaring when it should be included.
ALL assigned reviewers must PASS for work to proceed. Reviewers are spawned
simultaneously via background Task() calls in isolated worktrees, and cannot
see each other's output. Failed or crashed reviewers are marked INCONCLUSIVE
(blocks approval like a REJECT).

## File Conventions
- Planning templates: .claude/skills/acos-plan/templates/
- Review templates: .claude/skills/acos-review/templates/
- Evidence: .acos/evidence/[DATE]/[SLICE-ID]/
- Decisions: memory/decisions/
- Learning curve: learning-curve/
- RAG infrastructure: .claude/scripts/rag/ (Python) + .claude/scripts/rag-*.sh (wrappers)
- RAG vector data: .acos/vectordb/ (local LanceDB, git-ignored)

## Project-Level Configuration
Projects using ACOS define their own toolchain and domain preferences in their
project's `CLAUDE.md`. ACOS agents read project context at runtime — do NOT
hardcode toolchain preferences into agent definitions or framework-level skills.

Preference categories projects should define:
- Package manager (npm/pnpm/bun/yarn for JS; pip/uv/poetry for Python; cargo for Rust)
- Linter/formatter (Biome/ESLint+Prettier/Ruff/clippy)
- Test runner (Vitest/Jest/Bun test/pytest/cargo test)
- CI/CD provider (GitHub Actions/GitLab CI/CircleCI)
- Quality gates: `.acos/config/quality-gates.yaml` (see `/quality-gates` skill)
- Domain security profile: `.acos/config/security-profile.md` (see `/domain-security-profile` skill)
- Permission governance: `.acos/config/oracle.yaml` (see `/acos-oracle-protocol` skill)
- Model profiles: `.acos/config/model-profile.yaml` (see `/acos-model-change` skill)
- Provider registry: `.acos/config/providers.yaml` (external model API endpoints and keys)
- MCP servers: `.claude/settings.local.json` under `mcpServers` (see `/mcp-setup` skill)

## Restricted Files
- review-rules/ — Per-reviewer trigger rules. HUMAN EDITABLE ONLY. No agent may read or modify.
- review-rules.yaml — Legacy pointer to review-rules/ directory (kept for reference).
- .claude/agents/ — Agent definitions are infrastructure. Modification requires human approval.
