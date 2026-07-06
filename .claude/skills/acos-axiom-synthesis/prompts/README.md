# Agent prompts (Phase 2+)

Self-contained prompts for the model-dependent pipeline stages. Not yet built —
these arrive as the later build phases land (PLAN.md §11):

- `elicitor.md` — blind, isolated atomic-claim elicitation (Phase 2).
- `grader.md` — two-axis grading, where an LLM judgment is needed (Phase 3).
- `refuter.md` — the independent, different-family adversarial refuter (Phase 4),
  with the oscillation-guard `settled-objections.md` injected.
- `synthesizer.md` — the *defended* synthesizer: merge-never-author, every output
  claim cited + entailment-verified (Phase 3/6).

Each must be fully self-contained (subagents don't inherit conversation context) and
must preserve blind independence — no agent sees another's output or the running tally.
