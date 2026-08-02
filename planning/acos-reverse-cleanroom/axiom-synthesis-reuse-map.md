# acos-axiom-synthesis → reverse-cleanroom fan-out: reuse map

**Date:** 2026-07-22
**Question:** what in `acos-axiom-synthesis` is relevant to the reverse-cleanroom fan-out
(Phase 4 blind proposals → Phase 5 fusion)?
**Verdict:** highly relevant, but for the FACT lane of fusion, not the whole thing. Reuse
the engine as-is for factual/requirement claims + provenance + falsification; keep the
backbone+graft judge for DESIGN choices. Do NOT let its `UNRESOLVED` terminal reach a build spec.

Engine location: `.claude/skills/acos-axiom-synthesis/` (16 stdlib-Python scripts, prompts,
STATE-MACHINE.md, 75 offline assertions across 3 test files). It is a refutation-and-grading
engine, not a merger.

---

## REUSE DIRECTLY (5 pieces)

### 1. De-circularization firewall — `scripts/decircularize.py::collapse(sources)`  ★ the killer feature
Collapses non-independent sources to ONE vote BEFORE any agreement is counted. Two sources
are treated as one if they share upstream `origin`, produce verbatim-identical `text`, or are
**same `family` + same `context_id`** (prompt/base-model fingerprint). Returns
`independent_sources`, distinct `families`, `representatives`, and human-readable `flags`.
- **Why it matters here:** my research's #1 ensemble hazard is correlated errors — "agreement
  is weak evidence." This mechanizes the fix. Concretely, the two Claude seats (Opus + Sonnet)
  are `family: anthropic` → they count as ONE family, so they cannot alone clear the top tier.
- **Wire:** run `collapse()` over the proposer roster's per-claim assertions before tallying.

### 2. Corroboration gate + single-source cap — `axiom_ledger.py` invariants + `grade_fuse.py::grade_claim`
Hard invariants enforced on every ledger write (refuse with exit 3): `verified`/`ESTABLISHED`
requires `independent_sources ≥ 2` AND ≥2 **distinct families**; a single-source claim caps at
`probable`, never `verified`. Two-axis grading (source reliability × claim certainty, never blended).
- **Why it matters here:** grades which extracted facts/requirements are trustworthy enough to
  bake into the spec vs flag. Directly implements "N=5 from distinct families; same-family
  agreement insufficient."

### 3. Hash-chained single-writer ledger — `axiom_ledger.py`, `ledger_writer.py`, `verify_ledger.py`
Append-only, tamper-checkable claim ledger; the ONLY writer is `ledger_writer.py`; a formal
claim state machine (`CONJECTURE → CORROBORATED → ESTABLISHED`, plus `CONTESTED/SUPERSEDED/
REFUTED`, all revivable/archived-not-deleted). Every claim carries origin citation, rejected
alternatives, and supersession history.
- **Why it matters here:** this IS the "computed, not narrated" verdict substrate + the
  traceability spine Phase 6 needs. Fusion decisions become mechanical invariants, not prose.

### 4. Falsification gate + oscillation guard — `scripts/falsify.py`, `scripts/oscillation_guard.py`
A claim can't rise above `CONJECTURE` until it survives an independent different-family refuter;
a settled-objections log stops a rejected objection from re-litigating every round.
- **Why it matters here:** this is the mechanical backbone for `rc-red-team`. Today my red-team
  returns a prose ACCEPT/REJECT; backing it with the falsification gate makes rejections
  auditable and non-oscillating.

### 5. The proven four-family transports — `SKILL.md` "Model strategy" + the edited `providers.yaml`
The axiom skill confirms working, cheaper transports my cleanroom config assumed differently:
- `google:gemini-flash-latest` — FREE Google AI Studio key, confirmed working 2026-07-22 (dated
  models like `gemini-2.5-flash` 404). My cleanroom.yaml assumed a PAID `gemini-2.5-pro`.
- `zai:glm-4.7` — direct z.ai Coding-Plan key via Doppler, confirmed 200. My cleanroom.yaml
  routed GLM through OpenRouter (a separate paid key).
- Optional ChatGPT-in-browser 4th voice (Claude-in-Chrome), flagged/optional, ToS caveat.
- **Action:** align `cleanroom.yaml` seats to `zai:glm-4.7` + `google:gemini-flash-latest`
  (cheaper + already-working) instead of the OpenRouter/paid-Gemini assumptions.

---

## REUSE WITH CAVEAT (1 piece)

### 6. Precedence-ladder resolver → `UNRESOLVED` — `scripts/resolve.py`
Right for FACTUAL contradictions (proposal A: "9 entities"; B: "12") — resolve by precedence or
abstain, never fabricate a winner. WRONG as the terminal for DESIGN choices: a build spec must
DECIDE, and "use event-sourcing" winning by count is popularity, not correctness. So:
- Fact lane → axiom resolve (abstain-capable).
- Design lane → my `rc-fusion-synthesizer` backbone+graft judged trade-off (must decide).
- Never emit `UNRESOLVED` into the shippable spec; surface it as an OPEN_QUESTION for a gate.

---

## MISMATCH / boundary (do not force)

- The engine is **claim-level**. Fusing whole ~10k-word design proposals is not a claim-fusion
  task. Only the decomposable factual/requirement sub-layer maps. The orchestrator must first
  decompose each proposal into atomic claims and build the `fact` structure
  (`{fact_id, candidates:[{source:{id,family,origin,context_id,text}, value}], claim_type,
  grading, conflict, refuter, checklist_answers}`) — that decomposition is real work.
- It is **Python** (stdlib, fixture-tested). Reusing it = the TS orchestrator shells out to
  `orchestrate.py` for the fact lane (editing/using existing Python is allowed per the language rule);
  do NOT port it to TypeScript.

---

## Net recommendation

Change Phase 5 from "route factual claims through acos-axiom-synthesis" (vague) to a concrete
two-lane wiring:
1. **Fact lane:** decompose proposals → build `fact` structures → run `orchestrate.py` (de-circularize
   → grade → fuse → falsify → resolve → ledger). Same-family seats auto-capped; provenance mechanical.
2. **Design lane:** `rc-fusion-synthesizer` backbone+graft, security/edge = UNION, red-team backed by
   `falsify.py` + oscillation guard.
3. **Roster:** align to the proven `zai:glm-4.7` + `google:gemini-flash-latest` transports.
The ledger becomes the shared provenance substrate feeding Phase 6's traceability hard gate.
