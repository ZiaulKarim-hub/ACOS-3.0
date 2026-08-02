# SL-004-eden-01 — Command grammar & state file

**Story:** ST-004-eden-1 · **Epic:** EP-004-eden-1 · **Demo:** 1 · **Effort:** M · **Priority:** P0

## PM (Planner / LCE)
- **Objective (single):** Implement the skill front door: parse the first-token grammar and read/write
  `.acos/state/eden-level`.
- **In-scope:** grammar `off | on | 1-5 | level N | status | (bare)`; write digit / delete file; status report.
- **Out-of-scope:** the injector hook, any simplification behavior, the reading-level engine.
- **Allowed files:** `~/.claude/skills/acos-eden-protocol/SKILL.md`, `.acos/state/eden-level` (runtime).
- **Definition of Done:** each grammar input produces the correct state transition (data-model E7);
  `on`→`5`, `off`→delete, `N`→write, invalid→error naming the range, ambiguous→Confirmation-Gate
  clarification; bare/`status`→report. Evidence bundle produced.

## Dev (Executor) — Evidence Bundle expectations
1. Implementation summary of the parser. 2. Requirements traceability (M1, M3, M7, M8).
3. Structural quality: grammar table matches data-model E7 exactly. 4. Functional check: a transition
matrix test (each input → expected file state). 5. Confirmation-Gate honored for ambiguous input.
6. Runtime: off = file absent = zero overhead. 7. Self-assessment + limitations.

## QA (Zero-Trust)
- Verify every E7 row by inspecting the resulting `.acos/state/eden-level` (or its absence).
- **Evidence gates:** invalid input never silently clamps (M8); ambiguous never silently defaults (M7);
  `on` = 5 documented as the assumed default. Reject if any transition is wrong or a default is silent.

## Dev Learnings
_(to be filled during execution)_

## QA Learnings
_(to be filled during execution)_
