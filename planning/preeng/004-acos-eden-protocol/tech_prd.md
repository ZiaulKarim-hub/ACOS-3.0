# Technical PRD — acos-eden-protocol

## 1. File layout (deliverables)
```
~/.claude/skills/acos-eden-protocol/SKILL.md        # front door + rules (global skill)
.claude/scripts/eden-level-injector.py              # UserPromptSubmit hook
.claude/scripts/eden-rearm.sh                        # SessionStart (matcher 'clear') hook
.acos/state/eden-level                               # runtime state (digit; absent=off) [gitignored]
.claude/settings.local.json                          # + 2 hook registrations
.claude/scripts/session-cleanup.sh                   # MODIFIED: exclude eden-level from purge
```

## 2. Hook contracts

### 2.1 eden-level-injector.py (UserPromptSubmit)
- **Trigger:** every user prompt. **Placement:** LAST entry in the UserPromptSubmit array (after
  autopilot-context-injector.py and eternity-resume-prepend.sh) so eden's directive is the most-recent
  context Claude reads.
- **Logic:**
  ```
  level_file = project_root/".acos/state/eden-level"
  if not level_file.is_file():  emit_passthrough(); exit 0        # OFF = zero overhead
  level = read_digit(level_file)
  emit(additionalContext = build_directive(level))
  ```
- **Fail-open fallback (shell):** `... || printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit"}}'`
- **U1 dependency:** contract assumes additionalContext from multiple same-event hooks is concatenated.
  **Verified by SL-004-eden-02 before this is finalized.** If not concatenated: fall back to a single
  coordinating injector or SessionStart-only arming (documented alternative).

### 2.2 build_directive(level) → the per-turn directive (content contract)
Every directive states, compactly:
1. `EDEN PROTOCOL ACTIVE — Level {N} ({reader}).` (discoverability, always visible to the model)
2. **Scope:** "Apply ONLY to your top-level chat reply to the user. Do NOT alter Task() sub-agent
   prompts/outputs, evidence bundles, QA JSON, code, tool output, or generated files."
3. **Reading target:** the level's row (max sentence length, vocabulary rule, FK/FRE band).
4. **Fidelity Floor (compact):** numbers verbatim · keep every caveat · exempt content byte-for-byte ·
   confidence ≤ source · subset-only · never re-simplify · adult tone · legal terms glossed not replaced.
5. **Precision appendix:** "If the reply contains exempt spans, append a collapsible 'Exact figures &
   terms' block reproducing them verbatim from the original."

### 2.3 eden-rearm.sh (SessionStart, matcher 'clear')
Re-establishes nothing stateful itself (state is on disk); its purpose is to guarantee the directive
is present immediately after `/clear` even before the first post-clear prompt, mirroring eternity's
cross-`/clear` arming. Fail-open.

## 3. Orchestration & edge constraints (§0.9)
- **Eventual executor:** `/acos-execute-slice` runs each SL-004-eden-* slice under hook enforcement.
- **Durable execution:** state lives on disk (`.acos/state/eden-level`) → survives interruption,
  `/clear`, and (by cleanup exclusion) session end. No in-memory dependency.
- **Human-in-the-loop:** ambiguous invocation → Confirmation-Gate clarification (AskUserQuestion). Level
  changes emit a one-time banner (HITL awareness without a blocking pause).
- **Observability:** the per-turn directive names the active level in-band; `status` subcommand; agent
  completions logged to `.acos/metrics/agent-completions.log` (existing).

## 4. Reading-level engine (§technical)
Two gates enforced by the directive + SKILL.md rules:
- **Surface gate:** target FK grade + FRE band + max sentence length per level (see data-model.md table).
- **Semantic gate:** vocabulary/jargon rule — L5 sight-words + physical analogies; L4 Dale-Chall +
  in-sentence defs; L3 gloss specialized jargon; L2 define EVERY domain term (zero-knowledge reader);
  L1 jargon allowed undefined.
- **Self-verification:** lightweight internal heuristic (syllable/sentence-length/undefined-acronym
  scan). **Explicitly NOT a certified numeric FK** (WON'T W1) — the non-guarantee is stated in SKILL.md.

## 5. Fidelity Floor & exempt classifier (§technical)
- 8 invariants (research.md §3) referenced by the directive every turn and enforced by QA.
- Exempt-content detection: stdlib regex/heuristics — fenced/inline code, path-like tokens, URL regex,
  number-with-unit regex, ALL-CAPS/quoted defined entities, citation markers, formula tokens. Detection
  is advisory to the model (the guarantee is behavioral, reinforced by the directive), with an optional
  helper script for a QA-time check. Flagged for extra QA (its correctness underwrites the 0-violation metric).

## 6. Security / permissions
- Oracle: `.acos/state/` writes score ~2 (< threshold 9) → auto-approved; filenames avoid SENSITIVE
  patterns. Hooks are read-only w.r.t. user content (they only inject context). No secrets touched.

## 7. Non-guarantees (state them in docs)
- Self-verification is heuristic, not a certified metric. U1 is an assumption until the spike resolves it.
- L1/L2 numeric bands are interpolations; the enforced 2-vs-1 split is the jargon gate.
