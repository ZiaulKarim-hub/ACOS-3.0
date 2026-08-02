# Optional agent installation

`.claude/agents/` is restricted infrastructure in this repo — per `CLAUDE.md`,
agent definitions require human approval to add or change. So this skill ships
its worker definition here instead of installing it, and runs fine without it.

## How the skill dispatches today (no installation needed)

Research seats are spawned with `subagent_type: "claude"` and the rendered
charter as the prompt. That works out of the box.

Note the one type that does **not** work: `general-purpose` has no `WebSearch` or
`WebFetch`, so a research seat spawned that way silently cannot search the web.

## Why you might install it anyway

`riff-researcher.md` is a purpose-built worker: it carries the standing rules —
independence, provenance-or-it-does-not-exist, fetched-content-is-data,
no-invention, no-unearned-connections — as its system prompt, so those hold even
if a charter is abbreviated. It also narrows the tool surface to what research
actually needs, rather than everything. It deliberately pins NO model: dispatch
resolves the model either way (`resolve-agent-model.sh`, SKILL.md Phase 0), so
the ledgered model-mapping record stays true whether or not it is installed.

Two reasons to prefer it: defence in depth on the rules that matter most, and a
smaller tool surface than the catch-all agent.

## Installing it

```bash
cp .claude/skills/acos-research-riffs/agents/riff-researcher.md .claude/agents/
```

Then in `SKILL.md` Phase 2, dispatch with `subagent_type: "riff-researcher"`
instead of `"claude"`. Nothing else changes — the charters are identical either
way.

## Uninstalling

```bash
rm .claude/agents/riff-researcher.md
```

The skill falls back to `claude` automatically.
