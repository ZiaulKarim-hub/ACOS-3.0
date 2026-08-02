# SLICE-21-safe-close-skill — acos-safe-close/SKILL.md thin router
**Epic EPIC-2 / Story STORY-2.1 — Demo: Demo 2 (safe close)**
_Vertical value:_ Safety-critical logic stays in the script (ran 8/8) not skill prose (8/18); the receipt is script-printed, never composed.

## PM (Planner / Specifier) — Lean Context Engineering
**Single objective:** acos-safe-close/SKILL.md thin router

**In scope:**
- Thin router: parent writes intent core, calls close-project.sh, prints the script's receipt verbatim
- Never composes its own receipt

**Out of scope (guardrails):**
- Any safety-critical logic in prose
- Delegating the intent core to a sub-agent by default

**Allowed files / contexts:** .claude/skills/acos-safe-close/SKILL.md. The parent writes the intent core; the script does everything else.

**Definition of Done:** all acceptance criteria below pass; required artifacts written under the repo path; the evidence bundle at `.acos/evidence/[DATE]/SLICE-21-safe-close-skill/` is populated; `## Dev Learnings` and `## QA Learnings` are updated (a slice is not Done until they are — §0.7).

## Dev (Executor) — steps + 7-part Evidence Bundle
**Steps (execute EXACTLY; no scope expansion, only allowed files):**
- Author the SKILL.md as a thin router over close-project.sh.
- End-to-end run on a THROWAWAY project.

**Evidence Bundle to produce:** 1) Implementation Summary; 2) Requirements Traceability (to spec FR-* / tech_prd TR-*); 3) Structural Quality Evidence; 4) Functional/structural checks (the verification method below); 5) Security/Compliance notes; 6) Operational/Runtime considerations; 7) Self-assessment (confidence + known limitations).

## QA (Zero-Trust Verifier)
Assume the Dev did **not** do the work correctly. Verify scope respect, evidence authenticity (no fabricated logs — spot-check and recompute), and that every acceptance criterion + evidence gate is satisfied. QA may **REJECT** and require rework until the gates pass (a reject blocks the slice like an INCONCLUSIVE reviewer).

**QA checks:**
- Confirm the SKILL.md holds no safety-critical logic (SPINE 4)
- Confirm the printed receipt is byte-identical to the script's output (not model-composed)
- If the model composed any receipt line, REJECT

## Definition of Done (maps to ACOS `slice.yaml`)
**acceptance_criteria:**
- Full end-to-end run on a throwaway: receipt says SAFE only after all checks; tab closes as the literal last act
- The skill prints the script's receipt verbatim; composes nothing

**verification_method:** End-to-end throwaway run archived; SKILL.md shown to contain no load-bearing logic.

**evidence bundle:** `.acos/evidence/[DATE]/SLICE-21-safe-close-skill/`

## Dev Learnings
**2026-07-18 (SLICE-RES-21 execution):**
- **The two-pass close resolves the chicken-and-egg.** The blind verifier needs handoff+reentry text, but close-project.sh is their only writer. Answer: a generation pass (no `--roundtrip-result`) puts them on disk, the harness round-trips them, the final pass records the verdict. Idempotent by construction (same slug/day → same paths); the skill withholds the generation receipt from "final" presentation so exactly one authoritative receipt reaches the user.
- **A parallel slice can land mid-build — write the coupling thin, then tighten.** roundtrip-verify.sh (RES-22) appeared on disk between my Step-3 and Step-5 test runs. Because the skill's first draft deferred to the harness's usage output, upgrading to the real assemble/dispatch/validate commands touched only Step 5. Reuse: when referencing a parallel-built component, write the contract first, the flags last.
- **Session-id resolution is already house-patterned** — newest JSONL in `~/.claude/projects/<encoded-cwd>/` (from acos-eternity-protocol-stop). Reuse it; do not invent a second mechanism.
- **The Independence Wall guard pattern-matches prose.** An evidence sentence merely *mentioning* the reviewer-rules directory by its literal name tripped block-review-rules-read.sh mid-heredoc. Phrase prohibitions without the guarded literal.
- **What worked:** letting the script refuse instead of pre-checking in prose (the FAIL-verdict result file → script-printed `NOT SAFE` is the router's whole error handling); env-override sandbox (`RESURRECTION_STATE_DIR`/`ACOS_REGISTRY_HOME`/`RESURRECTION_SKIP_CMUX=1`) exactly as RES-20 documented.

## QA Learnings
**2026-07-18 (SLICE-RES-21 execution):**
- **What nearly slipped through:** the first-draft Step 5 told the session to "run `--help` and follow usage" — with the harness landed, that is under-specified routing an eager session could improvise around (e.g., writing its own result file). Caught by re-reading the just-landed harness header, which names /acos-safe-close as dispatcher; hardened into exact assemble/validate commands plus a Hard rule: a self-written verdict/result file is a fabricated verification.
- **Which check caught what:** the glob-invisibility test needed a *positive control* (a pre-existing decoy top-level handoff) — an empty glob result proves nothing if the glob itself is wrong. Decoy matched 1 of 1; the 2 of 2 closed/ files matched zero.
- **Byte-identity needs a mechanism, not a promise:** the receipt is relayed as `cat` of a captured file whose sha256 is in the bundle (`d9800f91…`) — QA recomputes instead of trusting the transcript.
- **Honest-evidence boundary:** the E2E verifier reply was builder-composed from the blind prompt text (workflow subagents have no Task tool); the verdict was still harness-computed, and FAIL/DEGRADED paths were exercised with ungrounded answers. Labeled in the bundle §7 rather than dressed up as a real blind dispatch — fabricated verification claims are the exact failure class this slice guards against.
- **To harden later (post-DP2):** the "tab closes as the literal last act" criterion is untestable until the user-scheduled DP2 tests; today's correct observable is the refusal chain (`auto-close REFUSED`), which the E2E archives.
