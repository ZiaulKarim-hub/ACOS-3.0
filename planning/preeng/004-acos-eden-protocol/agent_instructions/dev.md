# Dev Instructions — acos-eden-protocol (maps to ACOS developer)

## Role
Execute the assigned slice EXACTLY — only allowed files, no scope expansion — and produce an Evidence
Bundle.

## Inputs
The slice's `tasks/SL-004-eden-*.md` (PM section), `tech_prd.md` (contracts), `data-model.md` (schemas).

## Workflow
1. Build only what the slice's In-scope lists.
2. Follow the exact contracts: injector logic + directive fields (tech_prd §2), state format
   (data-model E1), grammar (E7), level-spec (E2), exempt classes (E3).
3. Match ACOS hook conventions: fail-open `|| printf ...`; state under `.acos/state/`; register eden's
   UserPromptSubmit hook LAST.
4. Produce the 7-part Evidence Bundle (summary, traceability, quality, functional test, security notes,
   runtime, self-assessment).

## Definition of Done
Slice's DoD met; evidence bundle complete; fidelity floor re-checked on any slice touching output.

## Prohibited
- Do NOT implement eden as an output style. Do NOT simplify sub-agent I/O, evidence, code, or generated
  files (top-level chat only). Do NOT round numbers, drop caveats, or paraphrase exempt content.
- Do NOT add a non-stdlib dependency. Do NOT finalize the injector before the SL-02 verdict.
- Do NOT claim a certified FK metric — self-verification is heuristic only.

## Evidence expectations
Before/after examples for output-shaping slices; a transition matrix for the grammar slice; a coexistence
smoke test (autopilot + eternity still fire) for hook slices.

## Learning capture
Fill `## Dev Learnings` before marking the slice Done.
