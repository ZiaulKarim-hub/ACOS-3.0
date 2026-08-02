# Deep-Drill Chat Mode — Design (2026-08-01)

**Status: confirmed scope (user, 2026-08-01) — build after fix-pass-2 is green.**

User intent (restated + confirmed): a chat-native mode of /acos-research-riffs —
usable entirely in the context window, no browser needed — replicating the user's
Insightia-style drill-down workflow, but with genuinely deeper research at every
level of questioning. Accepted upgrades: depth ladder, per-answer depth stamp,
recency policy (the recency policy ships in fix-pass-2 as CONTRACT-7).

Accepted defaults from the restate:
- Generic drill-down Q&A pattern (topic → findings → drill any finding → richer
  detail), any subject domain; finance-first examples in docs.
- Deliver-then-deepen timing: instant grounded answer first, deeper results
  follow in-thread when probes land.
- Chat mode is the default register when the user doesn't ask for the room;
  `riff room` remains available and unchanged (the browser is a viewer).
- Built on the post-fix trust chain (fix-pass-2 must be green first).

## The mechanic

### 1. Drill threads
A root question opens a thread; follow-ups on the same subject stay in it.
Ledger entries gain optional `thread` (id) and `depth` (integer) fields —
additive, append-only discipline unchanged. The orchestrator (the Claude session
running the skill) assigns thread ids; the engine only records them.

### 2. Depth ladder (per thread)
- **L0 — dossier answer**: instant, from the existing corpus (`riff ask`).
- **L1 — fresh sweep**: 1-3 targeted probes on the specific sub-question
  (new searches → ingest → re-ask). Dispatched automatically when the L0 label
  is below `verified`, when the answer abstained, or when the user drills.
- **L2 — primary-source verification**: fetch the primary documents themselves,
  verify exact figures/dates, capture `as_of`/`published` (recency policy).
- Escalation rule: a follow-up inside a thread auto-escalates one level above
  the thread's last answered depth. The user can jump levels ("go deep on X").
  L2 is the ceiling; beyond it, more L2 probes widen rather than deepen.

### 3. Deliver-then-deepen
Every question gets an immediate answer from the current corpus, honestly
labeled (including `primary-new` once the recency policy lands). If the ladder
triggers, the probes run and the enriched answer follows in the same thread,
explicitly marked as the deepened result. No silent waiting; no unlabeled
improvisation (I2/I9 unchanged).

### 4. Depth stamp (accepted upgrade)
One line on every answer:
`[thread T3 · depth L1 · 4 probes · 9 sources · verified]`
Fields come from `riff ask` output + thread bookkeeping — no new math.

## What actually changes where (small engine surface, protocol-heavy)

| Piece | Change |
|---|---|
| `scripts/lib/ledger.ts` | optional `thread`/`depth` fields on entries (additive) |
| `scripts/riff.ts` | `ask --thread <id> --depth <n>` recorded into the question/answer ledger entries; `riff thread <id>` prints a thread's drill history |
| `scripts/lib/claims.ts` | none beyond fix-pass-2 (CONTRACT-6/7 fields feed the stamp) |
| `SKILL.md` | Phase 4 rewritten around the drill protocol: thread assignment, ladder triggers, deliver-then-deepen register, depth stamp format, worked example |
| `templates/probe-charter.md` | depth-tier framing: L1 sweep probes vs L2 primary-verification probes (recency probe kind already added by fix-pass-2) |
| `scripts/test-riff.ts` | thread/depth recording, thread listing, stamp fields present |

Explicitly NOT in scope: no new daemon, no room changes, no background
auto-research loop — probes are dispatched by the orchestrator per the protocol,
so cost stays visible and user-paced.
