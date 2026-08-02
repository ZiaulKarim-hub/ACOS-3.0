# SLICE-20-close — close-project.sh steps 0-10 + four guards + last-workspace guard + agent-03 7-check gate
**Epic EPIC-2 / Story STORY-2.1 — Demo: Demo 2 (safe close)**
_Vertical value:_ Closing is verified zero-loss: the tab vanishing IS the success signal; the tab staying open IS the failure signal.

## PM (Planner / Specifier) — Lean Context Engineering
**Single objective:** close-project.sh steps 0-10 + four guards + last-workspace guard + agent-03 7-check gate

**In scope:**
- Step 0 state/stop-<sid> FIRST (only daemon write)
- Step 1 parent writes the intent core (never delegated)
- Enrich from disk; delegate to handoff-agent only if context-starved, via Bash heredoc not Write
- Write co-located handoff.yaml + <slug>.reentry.md + git-state/drift
- 7-check verification gate (agent-03); blind round-trip (step 5, separate slice)
- Atomic row upsert (enrich, never create); read-back sha256 assert; inline cleanup
- Validated workspace.close as the literal last statement; four guards + last-workspace guard

**Out of scope (guardrails):**
- Any identify --surface fallback (fails open)
- Auto-stash (record state, never mutate the tree)
- Creating a registry row at close (enrollment already did)
- Writing .resume.md or top-level memory/handoffs/*

**Allowed files / contexts:** .claude/scripts/resurrection/close-project.sh; memory/handoffs/closed/<slug>/; the single daemon write state/stop-<sid>. Pull agent-03's 7-check list from agent-03/findings.md at build time.

**Definition of Done:** all acceptance criteria below pass; required artifacts written under the repo path; the evidence bundle at `.acos/evidence/[DATE]/SLICE-20-close/` is populated; `## Dev Learnings` and `## QA Learnings` are updated (a slice is not Done until they are — §0.7).

## Dev (Executor) — steps + 7-part Evidence Bundle
**Steps (execute EXACTLY; no scope expansion, only allowed files):**
- Implement steps 0-10 in order; make close the literal last statement.
- Validate CMUX_WORKSPACE_ID via grep -qx against rpc workspace.list; fail CLOSED.
- Add the last-workspace guard (parameterized by SLICE-00 DP2 result).
- Wire the 7-check gate; wire read-back + sha256 assert; inline cleanup.
- Run the tamper tests.

**Evidence Bundle to produce:** 1) Implementation Summary; 2) Requirements Traceability (to spec FR-* / tech_prd TR-*); 3) Structural Quality Evidence; 4) Functional/structural checks (the verification method below); 5) Security/Compliance notes; 6) Operational/Runtime considerations; 7) Self-assessment (confidence + known limitations).

## QA (Zero-Trust Verifier)
Assume the Dev did **not** do the work correctly. Verify scope respect, evidence authenticity (no fabricated logs — spot-check and recompute), and that every acceptance criterion + evidence gate is satisfied. QA may **REJECT** and require rework until the gates pass (a reject blocks the slice like an INCONCLUSIVE reviewer).

**QA checks:**
- Independently run all tamper tests; recompute listed N of M
- Confirm the ONLY daemon write is state/stop-<sid> (diff the whole dir)
- Confirm no identify fallback path exists in the code
- Confirm close is literally the last statement (read the script tail)

## Definition of Done (maps to ACOS `slice.yaml`)
**acceptance_criteria:**
- Delete the handoff between write and read-back -> receipt refuses SAFE, tab stays open
- Unvalidatable CMUX_WORKSPACE_ID -> fail closed, no close, no identify fallback
- Last-workspace case -> close skipped with an explicit message
- state/stop-<sid> exists BEFORE step 1 (directory diff); it is the only daemon-dir write
- Receipt listed N of M == git status --porcelain | wc -l
- Artifacts co-located under closed/<slug>/, status: parked, type: close-project, glob-invisible to Eternity
- pending-resume-*.txt population unchanged before/after

**verification_method:** Each tamper test archived; directory diff of the daemon dir; Eternity glob (ls -t memory/handoffs/*.md *.yaml) unchanged; sha256 read-back shown.

**evidence bundle:** `.acos/evidence/[DATE]/SLICE-20-close/`

## Dev Learnings
**2026-07-18 (SLICE-RES-20 build):**
- Quoting agent-03's verification spec as `#`-prefixed comment lines killed two birds: verbatim traceability AND immunity from nested-heredoc collision (their spec contains a bare `PY` delimiter line that would have terminated a `<<'PY'` wrapper heredoc — renamed ours `PYEOF` and prefixed the quote).
- Agent-03's checks 3/4 assume `import yaml`; system python 3.9.6 has none. The same assertions run cleanly against a ~30-line line-prefix parser over a stable handoff format — design the format for the parser, not the parser for the format.
- Check 7's `basename` needle degenerates in the `closed/<slug>/handoff.yaml` layout (basename is always `handoff.yaml`); the slug-qualified path `closed/<slug>/handoff.yaml` contains the basename and is strictly stronger — same intent, no invented check.
- `refuse()` that flushes the partial receipt before `NOT SAFE — <reason>` gives failure transcripts for free: every refusal test showed exactly which steps completed (e.g. stop marker written BEFORE the step-1 intent refusal, proving step-0-first ordering).
- Reuse: `registry_lib.upsert_row` genuinely enriches in place — pre-enrolled row kept its uuid/enrolled_at; the absent-row path needed only find_by_root + a receipt NOTE.

## QA Learnings
**2026-07-18 (SLICE-RES-20 sandbox verification):**
- What nearly slipped through: the receipt's `listed 2 of 2` vs later `3 of 3` looked like a counting bug — it was the first run's own untracked `closed/` dir joining the dirty list. Recomputing `git status --porcelain | wc -l` at the SAME instant as the run is the only fair comparison; QA should never compare counts across runs.
- Which check caught what: the real-daemon-dir before/after `ls` diff (not just "did stop-<sid> land in the override dir") is what proves the ONLY-one-write contract — the override dir alone can't prove absence of leakage.
- The fail-closed workspace test is safely runnable against LIVE cmux: `workspace.list` is read-only, so a bogus `CMUX_WORKSPACE_ID` exercises the exact set-but-dead branch (exit 1, zero close-instruction lines) with no destructive risk.
- To harden later: race a genuine external tamper (delete/replace handoff between write and gate) rather than relying on the structural read-back chain; and version same-day re-closes instead of overwriting the slug.
