# Domain Brief — acos-eden-protocol

**Domain:** Claude Code skill/hook engineering × readability science × fidelity-preserving text
simplification for a finance/legal professional.

## Entities
- **EdenLevel** — the active reading level (`off`, `1`–`5`), persisted in `.acos/state/eden-level`.
- **Injector hook** (`eden-level-injector.py`) — `UserPromptSubmit` hook, re-injects the per-turn directive.
- **Re-arm hook** (`eden-rearm`) — `SessionStart` (matcher `clear`) hook.
- **Level-spec table** — level → {reader, FK band, FRE band, max sentence, vocabulary rule}.
- **Exempt-content classifier** — detector of spans that must pass through verbatim.
- **Fidelity Floor** — the 8 hard invariants.
- **Precision appendix** — the "Exact figures & terms" block.
- **Command parser** — first-token grammar router.
- **Per-message override** — ephemeral one-off level (`raw:`/`L1:`).

## Processes
- **Toggle** — set/clear/report the level via the command grammar.
- **Per-turn re-injection** — hook reads state → emits directive → model applies it to the chat turn.
- **Simplify-with-fidelity** — rewrite surface register while holding the 8 invariants + exempt passthrough.
- **Self-verify (heuristic)** — two-gate estimate (FK/FRE + jargon scan) before output; non-certified.
- **Re-arm on /clear** — SessionStart hook re-establishes the directive.

## Methods / Standards
- **Flesch-Kincaid Grade Level**, **Flesch Reading Ease** — surface readability formulas. [T1]
- **Dale-Chall familiar-word list (~3000)** — vocabulary constraint for L4(-5). [T1]
- **ACOS hook conventions** — fail-open `|| printf ...`; state under `.acos/state/`. [T1]
- **autopilot-context-injector.py pattern** — file-presence check → additionalContext injection. [T1]
- **Confirmation Gate** (global CLAUDE.md) — never act on ambiguous interpretive input without confirming. [T1]

## Metrics
- **Fidelity-violation count** (target 0 — release blocker).
- **Level-adherence rate** (heuristic self-check in target band).
- **Toggle-to-effect latency** (≤1 turn).

## Risks
- Fidelity loss (CRITICAL); mis-scoping to machine output (HIGH); salience decay (MEDIUM);
  U1 unverified (MEDIUM); over-simplification false confidence (HIGH).

## Key Terms
- **Fidelity Floor** — invariants guaranteeing accuracy survives simplification.
- **Exempt content** — spans copied byte-for-byte (numbers, code, paths, citations, legal terms…).
- **Two-axis** — surface (FK/FRE) + semantic (jargon-definition) level control.
- **Precision appendix** — verbatim "Exact figures & terms" footer.
- **Tutor loop** — knowledge-builder's chunk/advance-signal mechanics (explicitly NOT adopted).
- **Re-injection** — re-applying the directive each turn via a hook, not model memory.
