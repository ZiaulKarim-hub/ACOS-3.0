# Overview

**Feature:** `acos-eden-protocol` — a session-persistent **output simplicity filter** for Claude Code / ACOS.

Once invoked, eden-protocol renders the **top-level assistant chat response** at a user-calibrated
reading level and keeps doing so, every turn, for the rest of the session — until turned off or
changed. The dial:

| Level | Target reader |
|---|---|
| `off` | Normal — no filter |
| `1` | University student |
| `2` | High-school senior with **no** prior knowledge of the subject |
| `3` | High-school junior |
| `4` | 5th grader |
| `5` (a.k.a. `on`) | 1st grader — everything explained the way a 6-year-old would understand |

The distinguishing constraint versus a naive "explain it simply": eden is built for a
finance / PE-real-estate-lending professional, so simplification is bounded by a **Fidelity Floor** —
exact numbers, caveats, legal terms of art, and executable code/commands survive **verbatim** at every
level. Simplification changes *how plainly* something is said, never *what is true*.

This PRD is grounded in swarm-research session `swarm-20260707-eden-protocol` (7 isolated agents +
synthesis); pre-seeded findings are tagged R1–R7 and carried into `research.md` / `evidence-ledger.json`.

---

## Diagnostics
*(Problem before solution — §0.3. Symptoms, affected roles, current vs. desired, hypotheses.)*

**Symptoms ("what's going wrong today"):**
- Claude's default chat register is often too dense/jargon-heavy for a fast read or for forwarding to a
  non-expert (a broker, an LP, a borrower).
- The only lever today is asking "explain this simply" **every single turn** — it does not persist.
- Ad-hoc simplification is *lossy in the wrong direction*: it rounds `$3,412,905` to "about $3M",
  drops a "net of a pending $410k lien" caveat, or paraphrases `git filter-repo --path` into prose —
  each of which is data corruption for this user's work product.

**Affected roles / personas:**
- **P1 — Direct operator** (PE RE-lending associate): toggles the dial mid-session to grasp dense
  output quickly. Primary.
- **P2 — Indirect stakeholder** (non-expert recipient of pasted output): never touches the system;
  consumes the simplified text second-hand. Secondary.

**Current vs. desired behavior:**
- *Current:* one-shot, per-turn, unbounded simplification with no fidelity guarantees.
- *Desired:* one persistent, calibrated, **fidelity-bounded** dial, scoped to human-facing chat only,
  discoverable every turn, reversible with zero residue.

**Hypotheses & unknowns:**
- **H1** — A `UserPromptSubmit` hook re-injecting the active level every turn (the autopilot pattern)
  reliably holds the register across long sessions and `/clear`, where model-memory alone drifts. [T2]
- **U1 (must-verify)** — Whether Claude Code **concatenates** `additionalContext` from multiple
  same-event `UserPromptSubmit` hooks (eden would be the 3rd). Gates the injector contract. [T3]
- **H2** — A stdlib-only regex/heuristic exempt-content classifier is sufficient to protect the
  Fidelity Floor in practice (flagged for extra QA). [T2/Assumption]

There is a dedicated **diagnostic/spike slice** (see `tasks/` SL-004-eden-02) that resolves U1 before
any injector code is finalized. Until U1 is resolved, the injector contract is marked `Assumption`.

---

## Users & Use Cases

**U-1 (P1).** *Set a level and keep it:* "`/acos-eden-protocol 3`" → every later chat answer this
session reads at a high-school-junior level, exact figures intact, until changed.

**U-2 (P1).** *Quick grasp of a dense answer:* mid-diligence, operator flips to `4` to skim a complex
waterfall explanation in plain English, then back to `off` for precise work.

**U-3 (P1).** *Share-ready output:* operator sets `5` to paste an explanation to a non-expert borrower
(P2), trusting numbers/terms are still exact.

**U-4 (P1).** *One-off exception:* while at `4`, operator prefixes a single message `raw:` to get one
unfiltered, precise answer without disturbing the session default.

**U-5 (P1).** *Discoverability:* operator forgets the current setting → `/acos-eden-protocol status`
(or bare invocation) reports the active level.

---

## Requirements

### 4.1 Functional Requirements (MoSCoW)

**MUST**
- M1 — Provide a first-token command grammar: bare→status; `on`→level 5; `off`→clear; `1`–`5` and
  `level N`→set level; `status`→report. [CQ10]
- M2 — Persist the active level across turns via a `UserPromptSubmit` hook re-injecting the directive
  every turn (not model memory). [CQ1, CQ2, CQ6]
- M3 — Store state at `.acos/state/eden-level` (single digit; **file absent = off**). [CQ8]
- M4 — Survive `/clear` via a `SessionStart` (matcher `clear`) re-arm hook. [CQ9]
- M5 — Apply **only** to top-level human-facing chat; never Task() sub-agent I/O, evidence bundles,
  QA JSON, code, tool output, or generated artifact files. [CQ11] **(P0)**
- M6 — Enforce the **Fidelity Floor** (8 invariants) at every level: numbers verbatim; no
  caveat/hedge/warning dropped; exempt content byte-for-byte; simplified confidence ≤ source; no added
  claims; always re-derive from original; adult tone; legal terms preserved w/ optional gloss.
  [CQ3, CQ12]
- M7 — Never silently default an ambiguous invocation to a level — route through a Confirmation-Gate
  clarification. [CQ10] **(P0)**
- M8 — Invalid input (`7`, `banana`) → explicit error stating the valid range; never silent clamp.
  [CQ10]

**SHOULD**
- S1 — Two-axis level engine: Flesch-Kincaid grade + Flesch Reading Ease (surface) **and** a
  vocabulary/jargon-definition gate (semantic) that separates L1 from L2. [CQ5]
- S2 — Default-on collapsible **"Exact figures & terms"** precision appendix on simplified responses
  that contain exempt spans. [CQ13]
- S3 — Adopt knowledge-builder language rules; reject its tutor-loop mechanics. [CQ14]
- S4 — Per-message override (`raw:` / `L1:`-style prefix) applying a one-off level without mutating
  session state. [CQ15]
- S5 — Silent by default; emit a one-time banner only when the level **changes**; `status` on demand.

**COULD**
- C1 — Optional L4–L5 chunk-then-pause delivery for genuinely hard topics (opt-in, not default).
- C2 — `off` retains a non-auto "last used level" suggestion for a faster re-enable.
- C3 — Lightweight self-verification heuristic (syllable/sentence-length/acronym scan) with an
  explicit non-guarantee caveat. [CQ4]

**WON'T (this version)**
- W1 — A certified numeric Flesch-Kincaid calculator at inference time (no non-stdlib NLP dep). [CQ4]
- W2 — Simplifying the user's *own* messages, generated artifact files, or any machine-readable output.
- W3 — A native Claude Code output style (exclusive slot + deprecated + would evict "Explanatory"). [T1]

### 4.2 APIs, Data & States

- **State:** `.acos/state/eden-level` — plain text, one char in `{1,2,3,4,5}`; absence = off.
- **Grammar (state transitions):**
  `off ──on/5──▶ L5`, `Lx ──n──▶ Ln`, `Lx ──off──▶ off`, `* ──status/bare──▶ (report, no change)`,
  `* ──invalid──▶ (error, no change)`, `* ──ambiguous──▶ (confirm, no change)`.
- **Hook I/O contract (subject to U1):** `eden-level-injector.py` emits
  `hookSpecificOutput.additionalContext` = the per-turn directive when the state file exists; emits an
  empty passthrough otherwise. Fail-open fallback (`|| printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit"}}'`).
- **Per-turn directive (content):** active level + target reader; the scope boundary (top-level chat
  only); a compact reference to the Fidelity Floor; the exempt-content reminder.

### 4.3 Non-Functional Requirements (NFRs)

- **Reliability:** fail-open — any hook error must not block the turn (matches every ACOS hook). [T1]
- **Performance:** off = zero overhead (file-absence check only); on = one small file read + one
  injected block per turn.
- **Security/permissions:** eden's `.acos/state/` writes score ~2 under the Oracle (< threshold 9) —
  no elevated approval for normal toggling. Filenames avoid `SENSITIVE_PATH_PATTERNS`. [T1]
- **Compatibility:** registered **last** in the `UserPromptSubmit` chain (after autopilot + eternity);
  must not disturb autopilot/eternity/Oracle. [T1]
- **Portability:** Python 3 stdlib + bash only.

---

## Prioritization & Scope Cut
Ship order = P0 (M5, M2/M4, M7) → P1 (S1–S5) → P2 (C1–C3). The spike (U1) precedes finalizing M2.
If forced to cut: keep M1–M8 + S1 + S2 (the fidelity-critical core); defer S4, C1–C3. The precision
appendix (S2) is **not** cut despite being a SHOULD — it is the user-facing guarantee that fidelity
survived, and its marginal cost is low (reuses already-extracted exempt spans).

## Metrics & Analytics
See §0.5 formula definitions carried into `analysis-report.md`. Instrumentation target:
`.acos/metrics/agent-completions.log` (existing). Product metrics:
- **Level-adherence rate** — % of filtered responses whose heuristic self-check lands in the target
  band (goal: high; measured by the self-verification heuristic, non-certified).
- **Fidelity-violation count** — must be **0** (any dropped number/caveat or altered exempt span is a
  release blocker). Primary quality gate.
- **Toggle-to-effect latency** — the next turn after a level change reflects it (should be 1 turn).

## UX & Content
- **Invocation:** `/acos-eden-protocol [off|on|1..5|level N|status]`.
- **Feedback:** silent per turn; one-line banner on change ("Eden: Level 4 — 5th grader. Numbers & code
  stay exact."); `status` prints the active level + grammar table on first use.
- **Tone:** adult and respectful at every level — simplicity scales sentence length/jargon/structure,
  never register. No baby-talk, no condescension. [R5]

## Rollout Plan
- **Demo 1 — Toggle + persistence (MVP):** `on/off/1-5/status` works; the injector re-injects the
  active level every turn and survives `/clear`. No simplification logic yet — proves the *mechanism*.
- **Demo 2 — Fidelity Floor + precision appendix:** exempt-content classifier + the 8 invariants +
  default-on "Exact figures & terms" appendix. Proves *nothing gets corrupted*.
- **Demo 3 — Two-axis reading-level engine:** per-level FK/FRE bands + jargon-definition gate wired to
  actual response shaping, knowledge-builder language rules applied. Proves the *dial actually works*.

## Risks & Mitigations
| Risk | Severity | Mitigation |
|---|---|---|
| Fidelity loss (numbers/caveats/terms) | CRITICAL | Fidelity Floor (8 invariants) + exempt passthrough + precision appendix [R3] |
| Mis-scoping into sub-agent/machine output | HIGH | M5 structural scope boundary in the directive [R2] |
| Directive salience decay over long sessions | MEDIUM | Per-turn hook re-injection, not model memory [R1] |
| U1 unverified (multi-hook additionalContext) | MEDIUM | Spike slice before finalizing injector [R1] |
| Over-simplification → false confidence | HIGH | Invariant #4 (confidence ≤ source) + retained hedges [R3] |

## Dependencies & Stakeholders
- **Depends on:** acos-knowledge-builder (language donor), autopilot-context-injector.py (pattern),
  `.acos/state/` + `session-cleanup.sh` conventions, Oracle path modifiers, readability formulas. [R1,R6]
- **Cross-cutting change:** `session-cleanup.sh` must be modified to **exclude** `.acos/state/eden-level`
  from SessionEnd purge (change to a shared script — flagged). [R6]
- **Stakeholder:** the user (sole operator + owner).

## Open Questions
1. **U1 (must-verify):** does Claude Code concatenate `additionalContext` across multiple same-event
   `UserPromptSubmit` hooks? → spike SL-004-eden-02. [T3]
2. Exact per-turn directive wording (how much Fidelity Floor is restated vs referenced each turn). [Assumption]
3. Persist across brand-new sessions? Defaulted **yes** (passive preference), mitigated by always-visible
   level line. [Assumption T5]
4. `on` → level 5 default. Defaulted from the user's phrasing "on and level 5 would mean…". [Assumption T5]

## Appendix
- Swarm report: `.acos/swarm/swarm-20260707-eden-protocol/synthesis/report.md`
- Per-level spec table: `research.md` §Reading-Level Engine and `data-model.md`.
- Fidelity Floor (8 invariants): `research.md` §Fidelity Floor and `agent_instructions/qa.md`.

## PRD Summary (One-Page Digest)
`acos-eden-protocol` is a session-persistent, fidelity-bounded output-simplicity dial (off / 1–5) for
top-level Claude chat, built as **skill + `.acos/state/eden-level` + a `UserPromptSubmit` re-injection
hook + a `SessionStart` re-arm hook** — never an output style. It scales *how plainly* answers are
written (university → first grader) while an 8-invariant **Fidelity Floor** guarantees exact numbers,
caveats, legal terms, and code survive verbatim. It applies to human-facing chat only (never sub-agent
or machine output), never silently guesses a level, and ships in three demos: toggle+persistence →
fidelity floor → reading-level engine. One P0 unknown (multi-hook `additionalContext` concatenation)
is resolved by a spike before the injector is finalized.
