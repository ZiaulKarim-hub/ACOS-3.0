# SLICE-DIAG-01 — Diagnostic + walking-skeleton harness (vendored engine + autopilot stub)

**Parent story:** STORY-B0 · **Epic:** EPIC-B · **Effort:** S · **Demo:** pre-Demo-1
**slice.yaml mapping:** Objective->`objective`/`description`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Validate the diagnosed problem (symptoms D1-D6 -> derived
requirements); stand up a deterministic session-directory scaffold with the FULL canonical
subtree; VENDOR the synthesis engine into the skill's own tree and prove the VENDORED copy is
reachable on a fixture; and stub the autopilot pre-flight assertion — all before any expert
logic exists.

**In-scope:** a diagnostics note tracing each symptom to a requirement + a validation hook; a
`session_scaffold` routine that creates `.acos/investment-committee/<session-id>/` with the
canonical subtree (`manifest.yaml`, `transcript.md`, `rounds/`, `sidebars/`, `ledger/`,
`evidence/`); a ONE-TIME vendoring copy of the `acos-axiom-synthesis` substrate + pipeline
scripts + tests into `.claude/skills/acos-investment-committee/scripts/synthesis/` with a
`VENDORED_FROM.md` provenance record (source path + git commit hash at copy time); a
reachability smoke test that runs the VENDORED copy's `test_pipeline.py` in-tree plus a fixture
`orchestrate.run()` invocation FROM THE VENDORED COPY (NOT the original `acos-axiom-synthesis`
skill directory), capturing exit status + ledger head; and a minimal autopilot pre-flight
assertion stub (`test -f .acos/state/autopilot-active` -> ABORT with a clear message, no
fallback branch).

**Out-of-scope:** any seat agent; any real deal parsing; Axis S; Mode B; verdict logic; the
full guardrail suite (F1 hardens the autopilot stub into the enforced guardrail).

**Allowed files/contexts:** new `SKILL.md` skeleton (`.claude/skills/acos-investment-committee/`);
new `scripts/session_scaffold.py`; new `scripts/synthesis/` (vendored copy + `VENDORED_FROM.md`);
a `diagnostics.md` under the skill; READ-ONLY: `acos-axiom-synthesis/` scripts + tests (as the
one-time vendoring SOURCE only), this feature's `spec.md`/`plan.md`.

**Step-by-step:**
1. Author `diagnostics.md`: table of D1-D6 (symptom -> affected role -> current -> desired ->
   owning requirement FR-*), mirroring spec §Diagnostics; attach validation pointer.
2. Implement `session_scaffold.py` creating `manifest.yaml` (`status: open`, `mode:
   deliberation`, `current_round: 0`), `rounds/`, `sidebars/`, `ledger/`, `evidence/`, and an
   empty `transcript.md`, deterministically from a `--deal` arg (stub Deal).
3. Vendor: copy the `acos-axiom-synthesis` substrate + pipeline scripts and its
   `test_pipeline.py`/`test_substrate.py` into `scripts/synthesis/`; write `VENDORED_FROM.md`
   recording the source path and the git commit hash at copy time. Treat the copy as a black
   box once made — no logic edits.
4. Smoke-run: run the VENDORED `test_pipeline.py` in-tree, and run `orchestrate.run()` from the
   vendored copy on its shipped fixture; record exit code + ledger head into
   `smoke-report.txt` and the evidence bundle. Do NOT modify any vendored (or original) engine
   script.
5. Stub the autopilot pre-flight assertion: `test -f .acos/state/autopilot-active` at the
   skill's entry point -> ABORT with a clear message; no fallback branch (F1 later hardens this
   into the fully-enforced guardrail).

**Definition of Done:**
- Artifacts: `diagnostics.md`, `scripts/session_scaffold.py`, `scripts/synthesis/` (vendored
  copy) + `VENDORED_FROM.md`, a scaffolded sample session dir (full canonical subtree),
  `smoke-report.txt`, an autopilot pre-flight assertion stub + its abort-message fixture.
- Validation: scaffold is idempotent (re-run same session-id -> no diff) and produces the FULL
  canonical subtree; the vendored `test_pipeline.py` passes in-tree; the vendored fixture
  `orchestrate.run()` exits 0 with a non-empty ledger head; `VENDORED_FROM.md` correctly records
  source path + git commit; the autopilot pre-flight assertion aborts (takes no fallback action)
  when `.acos/state/autopilot-active` exists.
- Evidence bundle expectations: all 7 sections below, incl. the smoke-report transcript, a
  `tree` of the scaffolded dir, `VENDORED_FROM.md` contents, and the autopilot-abort fixture
  transcript.

## Dev (Executor)

**Execution notes:** subscription-only; no `ANTHROPIC_API_KEY`. Keep `session_scaffold.py`
Python-3 stdlib only. Treat the vendored engine as a black box POST-copy — reachability only,
no logic edits. The vendoring copy itself is a one-time file operation, not a fork: document
provenance in `VENDORED_FROM.md`, don't reinterpret the code.

**Evidence Bundle (required):** 1) Implementation Summary; 2) Requirements Traceability
(D1-D6 -> FR-*); 3) Structural Quality Evidence (idempotency diff); 4) Functional Testing
(scaffold run + vendored `test_pipeline.py` pass + fixture smoke transcript, exit codes +
autopilot-abort fixture); 5) Compliance notes (no `acos-axiom-synthesis/` engine files touched;
vendored copy unmodified from its recorded source); 6) Operational (session-dir layout matches
tech_prd §2, incl. `sidebars/` and `evidence/`); 7) Self-assessment (confidence + limitations).

## QA (Zero-Trust Verifier)

Assume Dev did NOT do it correctly. Verify: (a) `diagnostics.md` covers all six symptoms with
a named requirement each; (b) re-run `session_scaffold.py` and diff — must be byte-identical
(no fake "idempotent" claim), and the scaffolded dir must include the FULL canonical subtree
(`rounds/`, `sidebars/`, `ledger/`, `evidence/`, `transcript.md`, `manifest.yaml` with
`status`/`mode`/`current_round`); (c) re-run the VENDORED `test_pipeline.py` yourself in-tree
and confirm it passes; re-run the vendored fixture `orchestrate.run()` yourself and confirm
exit 0 + ledger head matches the bundle (recompute, do not trust the log); (d) confirm zero
`acos-axiom-synthesis/` engine scripts changed (`git diff --stat` on `acos-axiom-synthesis/`)
AND confirm the vendored copy in `scripts/synthesis/` is byte-identical to the commit recorded
in `VENDORED_FROM.md`; (e) confirm `VENDORED_FROM.md` records a real source path + git commit
hash; (f) create `.acos/state/autopilot-active` and confirm the pre-flight assertion ABORTS
with a clear message and takes NO fallback action. Reject if any gate fails.

**Evidence gates:** idempotency diff empty; full canonical subtree present; vendored
`test_pipeline.py` passes in-tree; fixture exit 0; original engine untouched; vendored copy
matches recorded provenance; autopilot pre-flight abort with zero fallback; all 6 symptoms
traced.

## Dev Learnings
_(fill on execution: scaffold idempotency gotchas; vendoring-copy mechanics; axiom-synthesis
invocation quirks from within the vendored path.)_

## QA Learnings
_(fill on execution: which reachability claims needed recomputation; any faked-log risks;
provenance-drift checks; autopilot-abort fixture result.)_
