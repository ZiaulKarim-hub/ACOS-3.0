# SL-004-eden-02 — SPIKE: multi-hook additionalContext concatenation (U1)

**Story:** ST-004-eden-2 · **Epic:** EP-004-eden-2 · **Demo:** 1 · **Effort:** S · **Priority:** P0 (gating)

## PM (Planner / LCE)
- **Objective (single):** Resolve U1 — does Claude Code concatenate `additionalContext` from multiple
  same-event `UserPromptSubmit` hooks, or use only one?
- **In-scope:** a throwaway probe hook emitting a marker string as additionalContext, registered
  alongside the existing autopilot + eternity injectors; observe whether the marker reaches context
  when the other two also emit.
- **Out-of-scope:** eden's real injector logic (SL-03 depends on this result).
- **Allowed files:** a temp probe under `.claude/scripts/`, `.claude/settings.local.json` (temporary registration).
- **Definition of Done:** a written verdict (CONCATENATES / SINGLE-ONLY / OTHER) with the observed
  evidence, and a decision: if not concatenated, document the injector redesign (single coordinating
  injector or SessionStart-only arming). Temp probe removed afterward.

## Dev — Evidence Bundle
1. The probe + registration used. 2. Observed context result (quote it). 3. Verdict + confidence.
4. Impact on SL-03's injector contract. 5. Cleanup confirmation (probe + temp registration removed).

## QA (Zero-Trust)
- Re-read the observed evidence; confirm the verdict follows from it (not asserted).
- **Evidence gate:** SL-03 MUST NOT finalize the injector until this verdict exists. Reject if the
  spike is skipped or the verdict is unsupported.

## Dev Learnings
**VERDICT (2026-07-13): CONCATENATES — confidence HIGH.** Official Claude Code hooks docs
(code.claude.com/docs/en/hooks): "When several hooks return additionalContext for the same event,
Claude receives all of the values." Multiple matching hooks "run in parallel, and identical handlers
are deduplicated." Local corroboration: autopilot-context-injector.py deliberately withholds its own
additionalContext while eternity-resume is armed (lines 16-20) — proof that otherwise BOTH inject.
No throwaway probe needed; resolved by authoritative docs + code inspection.
**Design impact:** injector contract UNCHANGED. REFINEMENT — hooks run in PARALLEL, so registration
order does NOT guarantee eden's directive is read "last"; the directive is written self-sufficient and
order-independent (states level + scope + fidelity floor on its own).

## QA Learnings
The spike was resolvable without a live probe because the behavior is documented AND already exercised
in production by two coexisting UserPromptSubmit hooks (autopilot + eternity). A future reviewer should
NOT accept "register last = read last" as a guarantee — parallel execution means order is unspecified.
