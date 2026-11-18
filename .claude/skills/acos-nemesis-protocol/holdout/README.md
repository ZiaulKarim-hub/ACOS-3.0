# Holdout for acos-nemesis-protocol

The pack (`pack/`) is authored by a SEPARATE agent from `prd/PRD.md` §6 and is gitignored. Only
`manifest.json` is committed. The builder never reads the pack. Reveal runs exactly once, in a QA
context (`HOLDOUT_QA_CONTEXT=1`), by a non-builder:

```bash
HOLDOUT_QA_CONTEXT=1 bun ~/.claude/skills/acos-holdout-test/scripts/holdout.ts reveal holdout/manifest.json --pack holdout/pack --candidate . --evidence holdout/evidence
bun ../acos-skill-maker/scripts/trace.ts check prd/TRACE.json --reveal
```
