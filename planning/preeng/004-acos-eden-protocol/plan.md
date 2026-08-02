# Implementation Plan — acos-eden-protocol

## Architecture (one picture)

```
/acos-eden-protocol <arg>            ~/.claude/skills/acos-eden-protocol/SKILL.md
        │                                      (front door: parse, confirm, write state, report)
        ▼
   .acos/state/eden-level  ◀─────────────┐   (single digit; absent = off)
        │                                │
        ▼                                │ (toggle writes/deletes)
  eden-level-injector.py  (UserPromptSubmit hook, LAST in chain)
        │  reads state → emits per-turn directive as additionalContext
        ▼
   Claude composes the chat turn, then applies:
     • Level-spec table (surface: FK/FRE + max sentence)   ← reading-level engine
     • Vocabulary/jargon gate (semantic: L2 defines, L1 not)
     • Fidelity Floor (8 invariants) + exempt-content passthrough
     • Precision appendix ("Exact figures & terms")  [default-on when exempt spans present]
        ▲
   eden-rearm (SessionStart matcher 'clear') re-injects after /clear
   session-cleanup.sh  ── excludes eden-level from purge (persist across sessions)
```

Scope boundary (structural): the directive applies to **top-level human-facing chat only** — never
Task() sub-agent I/O, evidence bundles, QA JSON, code, tool output, or generated artifact files.

## Modules
1. **Skill front door** (`SKILL.md`) — grammar parse, Confirmation-Gate on ambiguity, state write, status report.
2. **State** (`.acos/state/eden-level`) — the single source of truth.
3. **Injector hook** (`eden-level-injector.py`) — per-turn directive re-injection; fail-open; last in chain.
4. **Re-arm hook** (`eden-rearm`, bash or py) — SessionStart matcher `clear`.
5. **Reading-level engine** (rules embedded in the injected directive + SKILL.md) — level-spec table + jargon gate.
6. **Fidelity Floor + exempt classifier** (rules in directive; optional stdlib helper for detection) — the guarantee.
7. **Precision appendix** (rule in directive) — default-on "Exact figures & terms".
8. **Cleanup exclusion** — a one-line change to `session-cleanup.sh`.

## Vertical slices → demos (per §0.8)
- **Demo 1 (MVP mechanism):** SL-004-eden-01 (grammar+state), SL-004-eden-02 (**spike U1**),
  SL-004-eden-03 (injector re-injection), SL-004-eden-04 (re-arm across /clear). Result: the dial
  toggles and the active level is re-injected every turn and survives /clear — no simplification yet.
- **Demo 2 (fidelity):** SL-004-eden-05 (Fidelity Floor + exempt classifier), SL-004-eden-06
  (precision appendix). Result: nothing gets corrupted; exact figures preserved and surfaced.
- **Demo 3 (the dial works):** SL-004-eden-07 (two-axis reading-level engine + kb language rules),
  SL-004-eden-08 (self-verification heuristic w/ caveat). Result: output actually reads at the level.
- **Harden:** SL-004-eden-09 (per-message override), SL-004-eden-10 (cleanup exclusion + docs + status UX).

## Sequencing rationale
- The **spike (SL-02)** precedes finalizing the injector (SL-03): if multi-hook additionalContext does
  NOT concatenate, the injector design changes. Do not build SL-03's final contract before SL-02.
- Fidelity (Demo 2) precedes the reading-level engine (Demo 3): the guarantee must exist before the
  transform that could violate it is switched on.

## Dependencies & cross-cutting changes
- **Modifies a shared script:** `session-cleanup.sh` (exclude `eden-level`). Flagged; requires care —
  it's outside eden's own files (see Restricted Files note; this is a hook script, human-reviewable).
- **Hook registration:** add eden's two hooks to `.claude/settings.local.json` (UserPromptSubmit last;
  SessionStart matcher `clear`).
- Reuses: autopilot injector pattern, `.acos/state/` conventions, Oracle path modifiers, kb language rules.

## Risks (plan-level)
- U1 unverified → SL-02 spike gates SL-03. | Fidelity loss → Demo 2 before Demo 3.
- Modifying `session-cleanup.sh` could affect other cleanup → change is additive (an exclusion), reviewed.
- Hook-chain ordering regressions → register last, fail-open, and a smoke test that autopilot/eternity still fire.

## Definition of Done (feature)
All 10 slices pass their QA gates; verify-artifacts equivalents green; Demo 1–3 demonstrated;
fidelity-violation count = 0 in a test battery of finance-flavored prompts; U1 resolved or the injector
redesigned accordingly.
