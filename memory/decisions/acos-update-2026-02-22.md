# ACOS Update Report — 2026-02-22

## What We Found

The AI coding world has moved fast since ACOS was last updated. Claude Code itself
now has 17 hook events (we only use 6), a new way to run background scripts without
slowing things down, and a way to give each reviewer agent its own isolated copy of
the codebase. The broader industry is moving toward "context engineering" — deliberately
designing what the AI sees — and mechanically enforced quality gates rather than
optional checklists. ACOS is ahead of most tools on adversarial review and planning
structure, but behind on adopting new Claude Code primitives that would make the
system stronger.

## What ACOS Already Does Well

- Adversarial review with independence wall (ahead of all commercial tools)
- Structured planning hierarchy (Vision > Epic > Story > Slice)
- Evidence-based verification with audit trails
- Multi-agent orchestration with parallel reviewers
- Session handoff system with three-layer defense
- Permission governance via The Oracle
- Cross-project learning infrastructure

## Proposed Changes

### SAFE & QUICK

See Change Cards #1–#3 below.

### WORTHWHILE

See Change Cards #4–#6 below.

### BIG MOVES

See Change Cards #7–#8 below.

### Things We Looked At But Decided Against

1. **Agent Teams** — A new experimental feature where AI agents can talk directly
   to each other. We decided against it because it's still in beta, has known
   limitations (can't resume sessions, only one team at a time), and would require
   rethinking our entire orchestration model. We'll revisit when it's stable.

2. **Claude Agent SDK (Python/TypeScript)** — A programming library for building
   custom agents. Powerful but would mean rewriting our shell-script infrastructure
   in Python/TypeScript. Not worth it right now — our shell scripts work and are
   easier to debug.

3. **Plugin System for Distribution** — Packaging ACOS as a Claude Code plugin for
   easy installation. Good idea but significant packaging work with no immediate
   benefit since we deploy via bootstrap/embed-skills.

4. **1M Context Window** — Claude now supports 1M tokens, which would reduce handoff
   needs. However, it requires different pricing and our current 200K thresholds are
   well-tested. We can revisit when 1M becomes the default.

5. **MCP Tool Search (lazy loading)** — Reduces memory usage when many MCP tools are
   configured. ACOS doesn't currently use MCP heavily, so the benefit is minimal.

## Rollback Safety Net

Each change below can be undone by reverting the specific file(s) listed.
Since we run health checks before and after, any regression is caught immediately.
Git history preserves the pre-change state of every file.
