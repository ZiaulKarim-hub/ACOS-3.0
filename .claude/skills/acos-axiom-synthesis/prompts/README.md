# Agent prompts (the model-dependent glue)

Self-contained prompts for the non-deterministic pipeline stages. **Built 2026-07.**
Each is fully self-contained (subagents inherit no conversation context) and preserves
blind independence — no agent sees another's output or the running tally.

- `elicitor.md` — blind, isolated atomic-claim elicitation (Stage 1). Cross-family;
  divergence between blind elicitors is signal, not error.
- `grader.md` — the blind checklist judge (Stage 3). Answers the **semantic** confidence
  questions (`V1`,`V2`,`V3`,`N4`,`N6`,`N7`,`N8`,`N10`) plus the grading flags that feed the
  code-computed questions. Output maps directly into `checklist.py`'s `checklist_answers`.
- `refuter.md` — the independent, **different-family** adversarial refuter (Stage 5), with
  the oscillation-guard `settled_objections` injected. Its verdict sets the
  `V4-SURVIVES-REFUTER` veto and feeds the falsification gate.
- `synthesizer.md` — the **defended** synthesizer (Stage 7): merge-never-author, every
  output sentence cited to a ledger claim and entailment-checked.

## How the wizard assembles a `fact` from these

For each claim, the orchestrating skill (main Claude, at runtime) builds the `fact` dict
that `orchestrate.run()` consumes:

1. **elicit** (3–4 blind, cross-family) → `candidates[]` + provenance (`origin`, `family`,
   `context_id`, `locator`).
2. **grade** (blind, not the author) → `checklist_answers` (semantic subset) +
   `grading.has_primary_citation` / `grading.freshness_ok` / `falsifiable`.
3. **refute** (different family, settled-objections injected) → `refuter{objection,
   credible, rebutted}` and `fatal`. The wizard sets
   `checklist_answers["V4-SURVIVES-REFUTER"] = not (fatal and credible and not rebutted)`.
4. The deterministic questions (`N1`,`N2`,`N3`,`N5`,`N9`) are computed by `checklist.py`
   from the de-circularization counts, fusion divergence, and grading flags — never asked
   of a model.

The assembled `fact` (now carrying `checklist_answers`) flows through the deterministic
engine, which sets the tier via the checklist and writes the ledger.

## Model dispatch (cross-family diversity)

- **Claude** families → `Task()` (subscription; never `ANTHROPIC_API_KEY`).
- **Gemini / z.ai-GLM / OpenAI-API** → `run-external-agent.py` with the provider registry
  (`.acos/config/providers.yaml`).
- **ChatGPT (Plus, no API)** → Claude-in-Chrome browser voice — see SKILL.md "The ChatGPT
  browser voice". Fragile and terms-of-service-sensitive; optional 4th family.
