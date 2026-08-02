# Research Dossier — acos-eden-protocol

*Sources are structured from swarm-research `swarm-20260707-eden-protocol` (7 isolated agents +
synthesis) plus direct repo inspection. This worker cannot fetch external sources; external facts
below were pre-seeded into the product context by the swarm and are tiered in `evidence-ledger.json`.*

## 1. The mechanism question (CQ1, CQ2, CQ6) — RESOLVED

Three candidate primitives for a persistent output-register transform:

| Primitive | Persistence | Verdict |
|---|---|---|
| **Skill instructions** (in-context) | Advisory; decays over long sessions / `/clear` | Necessary as the front door, insufficient alone |
| **Output style** | Structural, but a **single exclusive slot**; the project already sets `"outputStyle":"Explanatory"`; mechanism **deprecated** | **REJECTED** — would silently evict Explanatory [R1/T1] |
| **`UserPromptSubmit` hook** re-injecting `additionalContext` every turn | Mechanically re-armed each turn from disk state; proven by autopilot to survive `/clear` + long sessions | **CHOSEN** [R1/T1] |

**Resolution:** eden = skill + `.acos/state/eden-level` + `eden-level-injector.py` (`UserPromptSubmit`,
registered LAST) + `eden-rearm` (`SessionStart` matcher `clear`). This mirrors
`autopilot-context-injector.py`, which checks a sentinel file each turn and injects a fresh directive —
the only pattern in this repo proven to hold a standing instruction across many turns without
model-memory drift. Two isolated agents (mechanism-expert + repo-state) converged on it independently.

**U1 (CQ7) — the one open dependency:** whether Claude Code concatenates `additionalContext` across
multiple same-event `UserPromptSubmit` hooks (eden would be #3, after autopilot + eternity). Inference
that it does (autopilot + eternity already coexist) is strong but **not doc-confirmed** — so a spike
slice resolves it before the injector is finalized. If concatenation is NOT how it works, the injector
must be redesigned (e.g., a single coordinating injector, or a different event).

## 2. The scope boundary (CQ11) — P0

ACOS is a multi-agent orchestrator (architect → developer/reviewers via `Task()`). "Every message"
**must** mean top-level human-facing chat only. A first-grade-language QA report is unparseable by the
architect that consumes it; a simplified evidence bundle breaks traceability. Eden's directive must
name the boundary explicitly and exclude: Task() sub-agent prompts/outputs, evidence bundles, QA JSON,
code/diffs, tool output, and generated artifact files (PDF/DOCX/XLSX). [R2]

## 3. The Fidelity Floor (CQ3, CQ12) — the finance-grade guarantee

Simplification is a lossy transform; for a PE-lending user, lossy in the wrong place = corrupted work
product. Eight hard invariants hold at **every** level:

1. Every number survives **verbatim** (digits, precision, units) — framing may be added, never substituted.
2. No caveat / hedge / exception / warning is dropped — each becomes an explicit clause.
3. **Exempt content** passes through byte-for-byte.
4. Simplified confidence never exceeds source confidence.
5. No added claims — the simplified fact set is a **subset** of the source facts.
6. Always re-derive from the original; **never re-simplify** an already-simplified output.
7. Tone stays adult/professional at every level.
8. Legal terms of art are preserved (optional appended gloss), never substituted.

**Exempt content types:** code/inline-code, shell commands, file paths, API/function names, config
keys/values, URLs, citations, exact quotes, math/financial formulas, all numbers-with-units, defined
entities ("Borrower", "Event of Default"), warning/regulatory language.

**Precision appendix (CQ13):** a default-on collapsible "Exact figures & terms" block reproducing every
exempt span verbatim, sourced from the **original** (never re-derived from simplified text). Default-on
globally for this user because the cost of an omission reaching a real memo/loan-doc is high and the
marginal cost is low (it reuses the already-extracted exempt spans). [R3]

## 4. The reading-level engine (CQ5) — two axes

Flesch-Kincaid grade + Flesch Reading Ease measure the **surface** axis (sentence length, syllables).
A separate **vocabulary/jargon-definition** gate measures the **semantic** axis. FK alone **cannot**
separate L2 from L1 — both sit near the college band. The differentiator is domain-knowledge assumption:

| Level | Reader | FK grade | FRE | Max sentence | Vocabulary rule |
|---|---|---|---|---|---|
| 5 | 1st grader | 0.5–1.5 | 90–100 | 6–8 (one idea) | ~300–500 sight words; physical analogies; ≤2 syllables |
| 4 | 5th grader | 4.0–5.5 | 80–90 | 10–12 | Dale-Chall ~3000 familiar list; define outside words in-sentence |
| 3 | HS junior | 9.5–11.5 | 55–65 | 15–18 | general HS vocab; specialized jargon gets a brief gloss |
| 2 | HS senior, **zero domain knowledge** | 10–13 | 40–55 | 20–25 | adult grammar OK, but **define every domain term on first use** |
| 1 | University student | 13–16+ | 10–40 | 25–35 | full academic vocab; **jargon allowed undefined** |
| off | Normal | — | — | — | no rewrite pass |

**Self-check (CQ4)** is two-gate — (a) FK/FRE surface estimate, (b) jargon-definition scan — and is a
**lightweight internal heuristic, NOT a certified numeric FK** (no non-stdlib NLP dep; WON'T W1). This
non-guarantee must be stated wherever self-verification is described. [R4]

## 5. Language rules: adopt vs reject (CQ14)

**ADOPT (scaled per level)** from acos-knowledge-builder: jargon-defined-on-first-use, spelled-out
abbreviations, jargon-free definitions, short sentences, mandatory concrete examples at L4–5 (finance
analogies first, don't force), honest-uncertainty + source-caveat markers (**ALL levels** — accuracy,
not clarity), misconception callouts, "what this is NOT" scoping, tables for 3+, small ASCII diagrams,
anti-condescension tone.

**REJECT (tutor-loop mechanics):** chunked one-concept-per-turn delivery, F/B/S/K/Q/D advance signals,
diagnostic openers, cross-turn glossary, end-of-topic recaps, cross-session learned-memory, quiz /
deep-dive modes. Eden filters one already-composed response; it is **not** a turn-by-turn tutor.
**Nuance:** at L4–5 for genuinely hard topics, optional chunk-then-pause delivery is the least-bad way
to reconcile "simple words" with "explain everything" — an opt-in mode (COULD C1), not the default. [R5]

## 6. State, grammar, lifecycle (CQ8, CQ9, CQ10, CQ15)

- **Grammar (first-token routed):** bare→status; `on`→L5; `off`→delete file; `1`–`5` / `level N`→set;
  `status`→report; invalid→error naming the range; ambiguous→Confirmation-Gate clarification (P0).
- **State:** `.acos/state/eden-level` (one digit; absent = off).
- **Persistence:** survive `/clear` (SessionStart re-arm) AND persist across sessions (exclude from
  `session-cleanup.sh` purge). Per-turn directive always states the active level so a later session is
  never surprised.
- **Per-message override (CQ15):** `raw:` / `L1:` prefix parsed at message time; one response only;
  never mutates the state file. [R6, R7]

## Data Gaps
- **U1** multi-hook `additionalContext` concatenation — unverified (spike). [T3]
- Reading-level bands not live-verified (WebSearch was unavailable to research agents); standard
  formulas are high-confidence from training knowledge; **L1/L2 numeric bands are interpolations** —
  the real 2-vs-1 enforcement is the jargon gate, not the FK number. [T2]
- No sample eden conversation exists to measure real FK adherence or salience decay over 50+ turns.
