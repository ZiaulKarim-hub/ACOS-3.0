# SLICE-22-blind-roundtrip — Blind round-trip verifier (close step 5)
**Epic EPIC-2 / Story STORY-2.1 — Demo: Demo 2 (safe close)**
_Vertical value:_ The single most likely silent failure is a repo-reading verifier passing a bad handoff; deny it the repo.

## PM (Planner / Specifier) — Lean Context Engineering
**Single objective:** Blind round-trip verifier (close step 5)

**In scope:**
- Fresh general-purpose Task, handoff text ONLY; must state the next step
- Wigum cap 5 then DEGRADE (close still allowed, receipt marks DEGRADED)
- Test the tester: a gutted handoff must FAIL; the real one must yield a next-step quote that appears in the receipt

**Out of scope (guardrails):**
- Any repo/cwd access for the verifier
- New .claude/agents/ files
- Halting the close on cap (DEGRADE instead)

**Allowed files / contexts:** A fresh general-purpose Task given the handoff text ONLY (no repo, no cwd). No new agent definition files.

**Definition of Done:** all acceptance criteria below pass; required artifacts written under the repo path; the evidence bundle at `.acos/evidence/[DATE]/SLICE-22-blind-roundtrip/` is populated; `## Dev Learnings` and `## QA Learnings` are updated (a slice is not Done until they are — §0.7).

## Dev (Executor) — steps + 7-part Evidence Bundle
**Steps (execute EXACTLY; no scope expansion, only allowed files):**
- Wire step 5 to dispatch a general-purpose Task with the handoff text only.
- Implement Wigum cap 5 -> DEGRADE.
- Run the test-the-tester cases.

**Evidence Bundle to produce:** 1) Implementation Summary; 2) Requirements Traceability (to spec FR-* / tech_prd TR-*); 3) Structural Quality Evidence; 4) Functional/structural checks (the verification method below); 5) Security/Compliance notes; 6) Operational/Runtime considerations; 7) Self-assessment (confidence + known limitations).

## QA (Zero-Trust Verifier)
Assume the Dev did **not** do the work correctly. Verify scope respect, evidence authenticity (no fabricated logs — spot-check and recompute), and that every acceptance criterion + evidence gate is satisfied. QA may **REJECT** and require rework until the gates pass (a reject blocks the slice like an INCONCLUSIVE reviewer).

**QA checks:**
- Confirm the verifier truly had no repo/cwd access (inspect the dispatch)
- Confirm a gutted handoff fails (do not trust a single pass)
- Confirm DEGRADE, never halt, on cap

## Definition of Done (maps to ACOS `slice.yaml`)
**acceptance_criteria:**
- A deliberately gutted handoff FAILS the verifier
- The real handoff yields a next-step quote that appears in the receipt
- Cap reached -> DEGRADE, receipt marks DEGRADED, close still allowed; no new agent files

**verification_method:** Both test-the-tester transcripts archived; the receipt's quoted next step shown to match the verifier output.

**evidence bundle:** `.acos/evidence/[DATE]/SLICE-22-blind-roundtrip/`

## Dev Learnings
**2026-07-18 (SLICE-RES-22 build):**
- **Split the harness from the dispatch.** Scripts cannot Task(); building `roundtrip-verify.sh` as assemble-mode (blind prompt file + printed dispatch instruction) / validate-mode (`--answer` → verdict) keeps the blind wall structural: the script has no spawn capability, so repo leakage can only come from a skill that ignores the printed, transcript-inspectable instruction. Reuse this shape for any future "script prepares, skill dispatches" step.
- **The result file's real spec was already in the repo.** `close-project.sh`'s `parse_roundtrip` (line 192) line-prefix parses `verdict:` + `next_step:` and accepts ONLY PASS|DEGRADED — so `--out` is the plain-text line format carrying {verdict, attempt, quoted_next_step} (+ `next_step` alias), not strict JSON, which `startswith("verdict:")` could never match. Free interlock discovered: a FAIL result is structurally refused by the close, so mis-wiring FAIL into `--roundtrip-result` fails closed.
- **The reentry leaks the answer.** close-project.sh's reentry embeds `NEXT ACTION: <line>`; a gutted-HANDOFF-only fixture would still hand the verifier the answer through the reentry (and through `session_summary`'s `next: ...` tail). Gutting must strip every leak site. This is now a documented trap line in the real fixture's intent core.
- **Put the question's own vocabulary in the stopword list.** "State, in one sentence, the next concrete step..." otherwise donates next/step/state/... as free overlap credit to any parroted answer. Threshold 0.40 ratio + 3 distinct matches: correct paraphrase scored 9/9 (1.00), ungrounded-vs-gutted scored 0/8 (0.00) — a wide, comfortable gap; errors land on the safe side (false-FAIL → Wigum retry, never false-PASS).
- **DEGRADED must still satisfy the consumer.** parse_roundtrip refuses an empty `next_step`, so the DEGRADED quote is always non-empty: `UNVERIFIED (Wigum cap 5 reached): <sentence|(no answer produced)>` — loud, honest, parseable (verified at attempt 5 with an EMPTY answer).

## QA Learnings
**2026-07-18 (SLICE-RES-22 test-the-tester):**
- **What nearly slipped through:** the daemon-state before/after diff showed 3 changed rows mid-suite — a naive read screams "the tests wrote the daemon dir." Recomputing on file NAMES (1669 before == 1669 after, zero added/removed) proved the changes were the LIVE session's own token-watcher heartbeat/counters ticking mtimes; the script contains 0 references to the daemon path and has exactly 2 write sites (prompt + `--out`). Harden: always diff the file SET separately from metadata when asserting "dir untouched" next to a live daemon.
- **Which check caught the big one:** the gutted-fixture prompt was grepped for the real next-action phrase (0 matches) BEFORE trusting the FAIL verdict — proving the prompt truly lacked the answer, so the FAIL exercised the heuristic rather than an accident. Zero-overlap was caught exactly as designed: `matched 0 of 8 (ratio 0.00) against 0 reference lines`.
- **Contract verified against the real consumer, not the spec prose:** T6 ran a byte-faithful mirror of close-project.sh's `parse_roundtrip` over all three verdict files — PASS/DEGRADED ACCEPTED, FAIL REFUSED — and the extracted `next_step` string matched the receipt quote byte-for-byte.
- **Glob-invisibility re-verified for this slice's fixtures** (non-recursive `memory/handoffs/*.md|*.yaml` → 0 matches with 4 files present under `closed/<slug>/`) — do not inherit SLICE-20's result, re-prove per slice.
- **Exit-code capture gotcha:** `${PIPESTATUS[0]}` after `| tee` silently returned empty under the zsh test shell — exit codes were re-captured pipe-free. Harden: never assert on PIPESTATUS in mixed-shell transcripts.
