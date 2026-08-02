# Competency Questions — acos-eden-protocol

15 questions a practitioner must answer to build eden correctly. Each maps to lattice node(s) and an
evidence-ledger entry. Coverage target ≥95% (see `research_qa_report.json`).

| # | Competency Question | Answer (short) | Coverage |
|---|---|---|---|
| CQ1 | Which CC primitive persistently governs output register? | Hook re-injection, NOT output style (exclusive+deprecated). | ✅ |
| CQ2 | How is the level re-applied every turn without model memory? | `UserPromptSubmit` hook reads state → injects directive each turn. | ✅ |
| CQ3 | What content is exempt from simplification, detected how? | 13 exempt types; stdlib regex/heuristic classifier. | ✅ |
| CQ4 | How does the skill self-verify the target level? | Two-gate heuristic (FK/FRE + jargon scan); NOT certified numeric. | ✅ |
| CQ5 | Exact two-axis per-level spec; how L1 vs L2 split? | Level-spec table; L2 defines every term, L1 allows undefined jargon. | ✅ |
| CQ6 | How does the injector coexist with the hook chain? | Registered LAST after autopilot + eternity; fail-open. | ✅ |
| CQ7 | Does CC concatenate additionalContext across same-event hooks? | **Unverified (U1)** — spike slice before finalizing. | ⚠️ partial |
| CQ8 | Exact state format/location; cleanup adjustment? | `.acos/state/eden-level` digit; exclude from session-cleanup purge. | ✅ |
| CQ9 | How re-arm persistence across /clear? | `SessionStart` matcher `clear` hook re-injects directive. | ✅ |
| CQ10 | Command grammar; invalid-input handling? | First-token router; error on invalid; confirm on ambiguous. | ✅ |
| CQ11 | Exact scope boundary; how enforced? | Top-level chat only; directive names exclusions (Task/evidence/code/files). | ✅ |
| CQ12 | Which fidelity invariants; checked how? | 8 invariants; checklist referenced by directive + QA. | ✅ |
| CQ13 | How does the precision appendix work; when included? | Default-on collapsible block; included when exempt spans present. | ✅ |
| CQ14 | Which kb rules to adopt vs reject? | Adopt language rules (scaled); reject tutor-loop mechanics. | ✅ |
| CQ15 | Per-message override syntax; state impact? | `raw:`/`L1:` prefix; one response; no state mutation. | ✅ |

**Coverage:** 14 of 15 fully answered; CQ7 partially answered (design known, empirical confirmation
pending a spike). Weighted coverage = 14.5/15 = **96.7% ≥ 95%** → research QA can APPROVE, with U1
logged as the single open item carrying a validation slice.
