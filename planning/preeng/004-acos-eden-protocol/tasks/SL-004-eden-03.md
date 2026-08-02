# SL-004-eden-03 — Injector hook (per-turn re-injection)

**Story:** ST-004-eden-2 · **Epic:** EP-004-eden-2 · **Demo:** 1 · **Effort:** M · **Priority:** P0
**Depends on:** SL-004-eden-02 (U1 verdict)

## PM (Planner / LCE)
- **Objective (single):** Implement `eden-level-injector.py` (UserPromptSubmit) that reads
  `.acos/state/eden-level` and injects the per-turn directive as additionalContext.
- **In-scope:** file-presence check (absent→passthrough), read digit, `build_directive(level)` per
  tech_prd §2.2, fail-open fallback; register LAST in the UserPromptSubmit chain.
- **Out-of-scope:** simplification logic itself (behavioral, in the directive text), reading-level tuning.
- **Allowed files:** `.claude/scripts/eden-level-injector.py`, `.claude/settings.local.json`.
- **Definition of Done:** with a level set, the directive (naming the active level + scope + fidelity
  floor compact) is injected every turn; with no file, zero overhead; autopilot + eternity still fire;
  contract matches the SL-02 verdict.

## Dev — Evidence Bundle
1. Injector implementation. 2. Traceability (M2, M4-partial, M5 scope statement, M6 compact floor).
3. Directive content matches tech_prd §2.2 fields. 4. Smoke test: autopilot + eternity injectors still
emit. 5. Off = passthrough. 6. Fail-open verified (simulate error → turn not blocked). 7. Limitations.

## QA (Zero-Trust)
- Confirm registration order (LAST). Confirm the directive text names the scope boundary (M5) and the
  fidelity-floor compact (M6). Confirm fail-open. Confirm no regression to autopilot/eternity.
- **Evidence gate:** reject if the directive omits the scope statement or fidelity compact, or if it
  was finalized before the SL-02 verdict.

## Dev Learnings
_(to be filled)_

## QA Learnings
_(to be filled)_
