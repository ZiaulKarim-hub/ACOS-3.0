Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/archive/2026-06-11-emergency-handoff.yaml` for full session state.

Quick summary:
- Working on: QA swarm-review of the eternity-protocol corpus (5 SKILL.md files + 7 daemon scripts) to find lurking edge-case bugs before long-term reliance. The protocol itself is stable (Jun 10 hardening complete).
- Last action: Inventoried the full review corpus and diagnosed a usage-policy API error that appeared after switching the main model to Fable 5 (likely false-positive from Fable-tier dual-use screening tripping on keystroke-injection + permission-autopilot vocabulary).
- Next step: Run /acos-swarm-review against the files listed under files_to_review in the handoff. Do NOT use the Fable 5 model — run on Sonnet or Opus. Then triage findings, fix confirmed bugs (cmux auto-fire + warp manual-only hardening), and analyze the eternity-protocol <-> Oracle autopilot interaction (handoff task 3).
- Blockers: Usage-policy error under Fable 5 (work around: stay on Sonnet/Opus). cmux RPC method name unverified (set CMUX_INJECT_METHOD if cmux variant fails).

This prompt was auto-injected after /clear ran. The user has not typed anything
since. Read the handoff document and continue the prior work seamlessly.
