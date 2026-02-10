# DEPRECATED

These agent definitions have been migrated to native Claude Code agents at `.claude/agents/`.

The native agents provide mechanical enforcement of:
- Tool restrictions (`disallowedTools`)
- Permission modes (`permissionMode: plan` for read-only reviewers)
- Context isolation (via `Task()` delegation)
- Independence wall (via PreToolUse hooks)

**These files will be removed after 2 weeks of successful operation.**

## Migration Map

| Old Location | New Location |
|-------------|-------------|
| `agents/super/the-architect.md` | `.claude/agents/architect.md` |
| `agents/execution/ACOS-developer.md` | `.claude/agents/developer.md` |
| `agents/reviewers/ACOS-qa-reviewer.md` | `.claude/agents/qa-reviewer.md` |
| `agents/reviewers/ACOS-security-reviewer.md` | `.claude/agents/security-reviewer.md` |
| `agents/reviewers/ACOS-performance-reviewer.md` | `.claude/agents/performance-reviewer.md` |
| `agents/reviewers/ACOS-integration-reviewer.md` | `.claude/agents/integration-reviewer.md` |
| `agents/support/ACOS-memory-agent.md` | `.claude/agents/memory-agent.md` |
| `agents/support/ACOS-learning-curve-agent.md` | `.claude/agents/learning-agent.md` |
