# Clean-room enforcement & session lifecycle

The pipeline IS a clean room. Three zones, mechanically separated:

- **Dirty room** (`00-capture/`, `01-intent/`) — sees the ORIGINAL. On-machine only.
- **Spec wall** (`02-wall/`) — strips expression/secrets/PII/tech-nouns; hashes what crosses.
- **Clean room** (`04-rebuild/` onward) — external models; see ONLY `02-wall/spec-clean.md`.

## Session lifecycle

1. **Init.** Orchestrator creates `.acos/cleanroom/<session-id>/` with sub-dirs
   `00-capture 01-intent 02-wall 03-prioritize 04-rebuild 05-synthesis 06-emit audit`.
   It writes `ACTIVE` (marker the egress guard keys off) and copies `.acos/config/cleanroom.yaml`
   into `audit/config-snapshot.yaml`.

2. **Arm the guard.** While `ACTIVE` exists, register the PreToolUse egress hook (below).
   Outside an active session the hook is a pure no-op, so registration can be persistent —
   but the safe default is session-scoped registration via `.claude/settings.local.json`
   added at init and removed at close.

3. **Fingerprint.** After Phase 0 and again after Phase 1, run
   `bun .claude/skills/acos-reverse-cleanroom/scripts/fingerprint-build.ts .acos/cleanroom/<sid>`.
   After the spec-wall writes `02-wall/spec-clean.md` (+ `forbidden-tokens.txt`), run it once more
   so the clean spec's hash lands in `allow_hashes` and the forbidden tokens are armed.

4. **Egress only after the wall.** Phase 4 sends `02-wall/spec-clean.md` to external models.
   Any external call whose payload leaks dirty-room content is DENIED (fail-closed).

5. **Close.** Remove `ACTIVE`, de-register the hook, finalize `audit/wall-manifest.json`.

## Hook registration (session-scoped)

Add to `.claude/settings.local.json` `hooks.PreToolUse` at init (matcher covers egress-capable tools):

```json
{
  "matcher": "Bash|WebFetch|WebSearch|mcp__.*",
  "hooks": [{ "type": "command", "command": "bun .claude/skills/acos-reverse-cleanroom/scripts/egress-guard.ts" }]
}
```

The guard returns `allow` (exit 0) or `deny: <reason>` (exit 2). It is fail-CLOSED
inside an active session and a no-op otherwise. It does NOT replace the Oracle —
it runs alongside it and is strictly additive.

## Audit trail (`audit/`)

- `dirty-fingerprint.json` — what the guard checks against.
- `wall-manifest.json` — every artifact that crossed the wall: sha256, provider, key tier
  (proof a ZDR/paid/self-hosted endpoint was used for a proprietary target), and an
  attestation the original never crossed. This is the evidence bundle if independence
  is ever challenged (mirrors `.acos/evidence/`).
- `egress-log.jsonl` — one line per external send: timestamp (from orchestrator), provider,
  payload hash, decision.

## Provider posture (enforced for `target.class: own`)

| Provider | Default posture | Rule |
|---|---|---|
| OpenAI API | no-train since 2023-03-01; ZDR for eligible enterprise | require ZDR for proprietary |
| Gemini | no-train ONLY on paid tier | force billing-linked PAID key; never AI Studio/free |
| Z.ai GLM | API effectively zero-retention (Singapore) | OK; prefer self-hosted open weights |
| Moonshot Kimi | trains by default, no documented opt-out | EXCLUDED from proprietary path |

"30-day deletion" is not a floor — a court preservation order can freeze logs; only ZDR
customers were exempted in *NYT v. OpenAI*. Sending proprietary logic to a default endpoint
can waive trade-secret status. For proprietary targets, prefer self-hosted open weights
(GLM/DeepSeek) to remove egress entirely.
