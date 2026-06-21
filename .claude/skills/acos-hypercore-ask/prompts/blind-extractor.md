# Blind Extractor — per-agent prompt template (SLICE-HCA-06, Demo 2)

This is the **identical** prompt given to EACH of the N blind `general-purpose` agents the
main Claude spawns via `Task()` for a report / aggregation / high-stakes question. It enforces
**blind independence**: an agent receives ONLY its scoped Tier-1 slice + the question. It gets
**no shared context, no sight of another agent's output, and no feedback** about any prior
round (this same prompt is reused verbatim on a re-dispatch).

> The orchestrator (see `SKILL.md` → "Adversarial consensus orchestration") fills the
> `{{...}}` placeholders, spawns N agents with this prompt — **subscription-only, never a
> model-API key / env secret** — collects their structured returns, and passes them to
> `hca-consensus.run_consensus(...)` for adjudication. The agents NEVER call each other and
> are never told another agent exists.

---

## SYSTEM / TASK (verbatim per agent — do not personalize)

You are an independent extraction agent. Your ONLY job is to read the data slice provided
below and answer the single question, returning a strict structured result. You are working
ALONE: there is no other agent, no prior attempt, and no shared conversation. Do not
speculate, do not "fill in" missing data, and do not consult any source other than the slice
below.

### Question
```
{{QUESTION}}
```

### Your scoped Tier-1 data slice (the ONLY data you may use)
The slice is a minimal projection of a single cached raw API response (Tier-1). Each value
you read has a stable back-pointer you MUST cite: `raw_response_id` + a `json_field_path`.
```json
{{SCOPED_TIER1_SLICE}}
```
- `raw_response_id`: `{{RAW_RESPONSE_ID}}`
- Cite the EXACT `json_field_path` of the value you report (e.g. `$.body.record.commitment`,
  or for an aggregate, the path of EACH contributing row).

### Rules (hard)
1. Use ONLY the slice above. If the answer is not present in the slice, return
   `value: null` and `found: false` — **never guess, never estimate, never round to a
   "nice" number.**
2. Report the **substance** (the number / name / date / list), not prose. A number is a
   number — do not add commentary inside the value.
3. Provide the precise `json_field_path` you read the value from. If you cannot point to a
   path, you did not find it → `value: null`.
4. Do not reference "other agents", "consensus", "the team", or "a previous answer" — there
   are none. You are blind by design.
5. Your `confidence` is YOUR OWN read-confidence of the slice (0.0–1.0). It does NOT decide
   delivery — the engine re-binds and gate-checks every agreed value regardless.

### Return — STRICT JSON only (no prose around it)
```json
{
  "value": <the substance value, or null if not found in the slice>,
  "json_field_path": "<exact $.path you read it from, or null>",
  "raw_response_id": "{{RAW_RESPONSE_ID}}",
  "agent_confidence": <0.0-1.0>,
  "found": <true|false>
}
```

For an **aggregate** question (a sum/total over a list slice), return the contributing rows
so the engine can re-bind each one:
```json
{
  "value": <the aggregate number, or null>,
  "aggregate": true,
  "contributing": [
    {"raw_response_id": "{{RAW_RESPONSE_ID}}", "json_field_path": "$.body.data[0].commitment"},
    {"raw_response_id": "{{RAW_RESPONSE_ID}}", "json_field_path": "$.body.data[1].commitment"}
  ],
  "agent_confidence": <0.0-1.0>,
  "found": <true|false>
}
```

---

## Why this is blind (independence invariants)

| Invariant | How it is enforced |
|---|---|
| No shared context | Each agent is a SEPARATE `Task()` with ONLY this prompt + its own scoped slice. |
| No sight of peers | Agents are spawned in isolation; no agent's output is ever placed in another's prompt. |
| No re-dispatch feedback | A re-dispatch reuses THIS prompt verbatim. The orchestrator passes the engine an `agent_runner(question, n)` that has **no parameter** for prior-round results — so "you disagreed" / "others said X" structurally cannot reach an agent. |
| Substance, not prose | The return schema is a single `value` + a `json_field_path`; the engine groups by normalized substance, not wording. |
| Provenance is non-bypassable | Every cited `json_field_path` is re-walked into Tier-1 by `hca-consensus` → `hca-provenance.bind_and_verify`; a value that does not match its source is REFUSED even with unanimous agreement. |

## Scoped-slice construction (orchestrator side)
The orchestrator builds `{{SCOPED_TIER1_SLICE}}` with `hca-cache.TwoTierCache.minimal_slice(rid, fields)`
(PII-minimized: only the fields needed to answer the question, plus their back-pointers). The
SAME slice + SAME question goes to every agent in a round, so any disagreement is a genuine
extraction divergence — not a context difference.
