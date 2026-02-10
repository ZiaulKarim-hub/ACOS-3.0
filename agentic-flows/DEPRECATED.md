# DEPRECATED

These YAML flow definitions have been converted to native Claude Code orchestration skills at `.claude/skills/`.

Orchestration skills use `context: fork` + `agent: architect` to execute flows with real `Task()` delegation to sub-agents, replacing the old "read YAML and follow it" approach.

**These files will be removed after 2 weeks of successful operation.**

## Migration Map

| Old Flow | New Skill |
|----------|-----------|
| `vision-interview-flow.yaml` | `.claude/skills/acos-interview/SKILL.md` |
| `slice-execution-flow.yaml` | `.claude/skills/acos-execute-slice/SKILL.md` |
| `story-completion-flow.yaml` | `.claude/skills/acos-execute-story/SKILL.md` |
| `epic-completion-flow.yaml` | `.claude/skills/acos-execute-epic/SKILL.md` |
| `vision-completion-flow.yaml` | `.claude/skills/acos-complete-vision/SKILL.md` |
| `feedback-resolution-flow.yaml` | `.claude/skills/acos-feedback-resolution/SKILL.md` |
| `learning-extraction-flow.yaml` | `.claude/skills/acos-learn/SKILL.md` |
