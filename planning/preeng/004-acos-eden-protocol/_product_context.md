# Product Context — 004-acos-eden-protocol

## 1. Product / Feature Name
`acos-eden-protocol` — a session-persistent **output simplicity filter** for Claude Code / ACOS.
Once invoked, it renders the top-level assistant chat response at a user-calibrated reading level
(off = normal; 1 = university student → 5 = first grader) and keeps doing so for the rest of the
session until turned off or changed.

## 2. Business Objectives
- Give the user a single calibrated dial over how simply Claude explains things in chat.
- Make dense technical / financial explanations comprehensible on demand — for the user's own quick
  grasp and for pasting to non-expert stakeholders — WITHOUT corrupting the underlying facts.
- Reuse across all ACOS work (planning, review, diligence, teaching) as an orthogonal, always-available
  layer that composes with every other skill.

## 3. User Problems (ranked)
1. AI chat output is frequently too dense / jargon-heavy for fast comprehension or for sharing with
   non-experts, and there is no per-session control over its reading level.
2. Naive "simplify this" corrupts exactly the things a PE real-estate lending professional cannot lose:
   precise figures (principal, XIRR, dates, LTV/DSCR), caveats, legal terms of art, and executable
   code/commands.
3. A one-shot "explain simply" doesn't persist — the user must re-ask every turn.

## 4. Success Metrics
- Selected level's reading target is hit (Flesch-Kincaid grade within the level's band; jargon-
  definition gate satisfied for L2-5).
- **Zero fidelity-floor violations**: every exact number, caveat, and exempt span (code, paths,
  citations, legal terms) survives verbatim.
- Filter persists across turns and across `/clear`; toggling `off` returns to normal with zero overhead.
- Level is always discoverable (per-turn directive states the active level; `status` subcommand).

## 5. Constraints (technical / timeline / resource)
- **Claude Code primitives only**: skill (`SKILL.md`) + hooks + `.acos/state/` files. Python 3 stdlib
  + bash, matching existing ACOS hook conventions (fail-open `|| printf ...` fallback).
- **MUST NOT be a native output style** — output styles are a single exclusive slot, the project
  already sets `"outputStyle": "Explanatory"`, and that mechanism is deprecated; an eden output-style
  would silently evict Explanatory. [T1]
- **Subagent Write is policy-blocked** in this environment ("return findings as text"); artifact
  authoring uses the main thread or Bash writes. [T3]
- **Scope = top-level human-facing chat only** — never Task() sub-agent I/O, evidence bundles, QA JSON,
  code, tool output, or generated artifact files. [T2]
- Must coexist with the existing UserPromptSubmit hook chain (autopilot-context-injector.py →
  eternity-resume-prepend.sh) and not disturb autopilot/eternity/Oracle. [T1]

## 6. Dependencies
- `acos-knowledge-builder` — donor of the plain-language ruleset (adopt language rules, reject the
  chunked tutor loop). [T1]
- `autopilot-context-injector.py` — the proven `UserPromptSubmit` state-file + additionalContext
  re-injection pattern eden copies. [T1]
- `.acos/state/` conventions (`oracle-session-threshold`, `model-session.yaml`), `session-cleanup.sh`
  (SessionEnd), Oracle path modifiers. [T1]
- Reading-level science: Flesch-Kincaid, Flesch Reading Ease, Dale-Chall familiar-word list. [T1/T2]

## 7. Known Risks
- **Fidelity loss** (rounded numbers, dropped caveats, paraphrased legal/technical terms) — CRITICAL
  for finance/diligence work. Mitigated by the Fidelity Floor + exempt-content passthrough. [T2]
- **Mis-scoping** to sub-agent / machine-readable output would break orchestration. [T2]
- **Context salience decay** of the injected directive over 50+ turns — mitigated by per-turn
  re-injection (hook), not model memory. [T2]
- **Unverified**: whether Claude Code concatenates additionalContext from multiple same-event
  UserPromptSubmit hooks — must verify before wiring eden's hook. [T3, must-verify]
- Over-simplification producing **false confidence** (a hedged answer sounding certain at L5). [T2]

## 8. Existing docs / research (pre-seeded below)

---

## Pre-seeded research (T-tagged)
_Source: swarm-research session `swarm-20260707-eden-protocol` — 7 isolated agents + synthesis.
Full report: `.acos/swarm/swarm-20260707-eden-protocol/synthesis/report.md`. Evidence tiers:
T1 Authoritative (official docs / verified live repo files), T2 Expert reasoning, T3 Empirical/
observed, T4 Community/tool, T5 Internal assumption._

### R1 — Mechanism [T1, Verified by 3 agents incl. Claude Code expert + 2 repo-grounded]
Build as **skill + `.acos/state/eden-level` (plain digit; file absent = off) + `eden-level-injector.py`
(`UserPromptSubmit` hook, registered LAST after autopilot + eternity injectors, fail-open) +
`eden-rearm` (`SessionStart` matcher `clear`)**. NOT a native output style (exclusive + deprecated +
would evict active "Explanatory"). Hook `additionalContext` is additive — the exact autopilot/eternity
pattern. Oracle impact of eden's `.acos/state/` writes = negligible (score 2 << threshold 9).

### R2 — Scope [T2, Verified — P0]
Eden applies to **top-level human-facing chat only**. Never Task() sub-agent prompts/outputs, evidence
JSON, QA verdicts, code/diffs, tool output, or generated files (PDF/DOCX/XLSX). The re-injected
directive must state this scope.

### R3 — Fidelity Floor [T2, Verified — 8 hard invariants]
(1) numbers verbatim; (2) no caveat/hedge/warning dropped; (3) exempt content byte-for-byte; (4)
simplified confidence ≤ source; (5) no added claims (subset of source facts); (6) always re-derive
from original, never re-simplify; (7) adult tone every level; (8) legal terms preserved with optional
gloss. **Exempt content types:** code/inline-code, shell commands, file paths, API/function names,
config keys/values, URLs, citations, exact quotes, math/financial formulas, ALL numbers-with-units,
defined entities ("Borrower"), warning/regulatory language. Recommend a **default-on collapsible
"Exact figures & terms" appendix**.

### R4 — Two-axis reading-level spec [T1 surface bands / T2 L1-L2 split]
Enforce BOTH: (a) Flesch-Kincaid grade + Flesch Reading Ease (sentence/syllable surface), (b) a
vocabulary/jargon-definition gate (semantic). FK alone can't split L2 from L1.

| Level | Reader | FK grade | FRE | Max sentence | Vocabulary rule |
|---|---|---|---|---|---|
| 5 | 1st grader | 0.5–1.5 | 90–100 | 6–8 (one idea) | ~300-500 sight words; physical analogies only |
| 4 | 5th grader | 4.0–5.5 | 80–90 | 10–12 | Dale-Chall ~3000 list; define outside words in-sentence |
| 3 | HS junior | 9.5–11.5 | 55–65 | 15–18 | general HS vocab; specialized jargon gets brief gloss |
| 2 | HS senior, ZERO domain knowledge | 10–13 | 40–55 | 20–25 | adult grammar OK but define EVERY domain term on first use |
| 1 | University student | 13–16+ | 10–40 | 25–35 | full academic vocab; jargon allowed undefined |
| off | Normal | — | — | — | no rewrite pass |

### R5 — knowledge-builder: adopt vs reject [T1, full line-cited read]
ADOPT (scaled per level): jargon-defined-on-first-use, spelled-out abbreviations, jargon-free
definitions, short sentences, mandatory concrete examples at L4-5 (finance analogies first, don't
force), honest-uncertainty + source-caveat markers (ALL levels — accuracy not clarity), misconception
callouts, "what this is NOT" scoping, tables for 3+, small ASCII diagrams, anti-condescension tone.
REJECT (tutor-loop mechanics): chunked one-concept-per-turn delivery, F/B/S/K/Q/D advance signals,
diagnostic openers, cross-turn glossary, end-of-topic recaps, cross-session learned-memory, quiz/
deep-dive modes. NUANCE: at L4-5 for genuinely hard topics, optional chunk-then-pause delivery is the
least-bad way to reconcile "simple words" with "explain everything" — an opt-in mode, not the default.

### R6 — State / toggle / grammar [T1, repo-grounded]
Grammar (first-token routed, per acos-oracle-protocol Phase 0): bare → status; `on` → level 5 (matches
user's "on and level 5" wording); `off` → delete state file; `1`..`5` and `level N` → same path;
`status` → alias. Invalid input → error with valid range, never silently clamp. Storage:
`.acos/state/eden-level` (digit; absent = off). Re-injection: hook-based (not model memory).
Lifecycle: survive `/clear` (SessionStart re-arm) AND persist across sessions (exclude from
session-cleanup); per-turn directive always states the active level so a later session is never
surprised.

### R7 — Open decisions (from completeness critic) [T2]
P0: (a) top-level-chat-only scope [→R2]; (b) hook-based persistence [→R1]; (c) never silently default
level — confirm on ambiguous invocation (honors the global Confirmation Gate). P1: per-message override
(`raw:` / `L1:` prefix, doesn't touch session state); optional L4-5 chunking; silent-by-default badge
(banner only on level change); self-verification via lightweight internal heuristic (NOT a guaranteed
numeric FK — state the caveat). P2: off = clear flag but may retain "last used" as a non-auto
suggestion; simplify-Confirmation-Gate-wording-but-preserve-precision; defensive integer-gate parse.

### Assumptions / must-verify
- [must-verify, T3] Multi-hook `additionalContext` concatenation on UserPromptSubmit — confirm before shipping the hook.
- [assumption, T5] "on" defaults to level 5 (first grader) per the user's phrasing "on and level 5 would mean…".
- [assumption, T5] Level persists across brand-new sessions (passive preference); mitigated by always-visible active-level line.
