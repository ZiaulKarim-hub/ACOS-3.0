# SLICE-11-enroll — enroll-project.sh + additive SessionStart hook + cwd==root assertion
**Epic EPIC-1 / Story STORY-1.1 — Demo: Demo 1 (enrollment)**
_Vertical value:_ Membership on first sight: the book is populated before any close ever runs (survives force-quit, DR-8).

## PM (Planner / Specifier) — Lean Context Engineering
**Single objective:** enroll-project.sh + additive SessionStart hook + cwd==root assertion

**In scope:**
- Marker gate (<root>/.acos/ OR CLAUDE.md OR memory/handoffs/)
- Mint uuid4 once -> <root>/.acos/project-id (git-ignored)
- Upsert row with derived fields via registry_lib.py
- assert realpath(cwd)==registry.root; log loudly on mismatch (risk #7)
- O(1), fail-open, never blocks session start; register as ADDITIVE SessionStart hook, name distinct from autopilot-enroll-project.sh

**Out of scope (guardrails):**
- Naive filesystem scan
- Close-time row creation
- Touching the existing hook chain or the daemon dir

**Allowed files / contexts:** .claude/scripts/resurrection/enroll-project.sh; ~/.claude/settings.json (one additive user-level SessionStart entry). Never register-session-pid.sh or the existing hook chain.

**Definition of Done:** all acceptance criteria below pass; required artifacts written under the repo path; the evidence bundle at `.acos/evidence/[DATE]/SLICE-11-enroll/` is populated; `## Dev Learnings` and `## QA Learnings` are updated (a slice is not Done until they are — §0.7).

## Dev (Executor) — steps + 7-part Evidence Bundle
**Steps (execute EXACTLY; no scope expansion, only allowed files):**
- Implement the marker gate and the uuid4 mint-once.
- Call registry_lib upsert with derived fields.
- Add the realpath(cwd)==root assertion with a loud log on mismatch.
- Register the additive user-level SessionStart hook at the absolute repo path.

**Evidence Bundle to produce:** 1) Implementation Summary; 2) Requirements Traceability (to spec FR-* / tech_prd TR-*); 3) Structural Quality Evidence; 4) Functional/structural checks (the verification method below); 5) Security/Compliance notes; 6) Operational/Runtime considerations; 7) Self-assessment (confidence + known limitations).

## QA (Zero-Trust Verifier)
Assume the Dev did **not** do the work correctly. Verify scope respect, evidence authenticity (no fabricated logs — spot-check and recompute), and that every acceptance criterion + evidence gate is satisfied. QA may **REJECT** and require rework until the gates pass (a reject blocks the slice like an INCONCLUSIVE reviewer).

**QA checks:**
- Confirm the hook is additive and does not touch register-session-pid.sh or the existing chain
- Force a cwd!=root case and confirm the loud log fires (protects the f639310 fix)
- Confirm the marker gate rejects a naive-scan candidate (memory/ stray)
- Confirm .acos/project-id is written exactly once (re-run enrollment)

## Definition of Done (maps to ACOS `slice.yaml`)
**acceptance_criteria:**
- New session in a marker dir -> a row file appears in ~/.acos/registry.d/ with all fields derived
- Session in a scratchpad/non-marker dir -> no row
- Second session in the same project -> same uuid, no duplicate row; .acos/project-id written exactly once
- cwd!=root logs loudly and does not silently continue

**verification_method:** Archived transcripts of the four cases; the SessionStart hook shown additive (diff of settings.json); enrollment timed O(1).

**evidence bundle:** `.acos/evidence/[DATE]/SLICE-11-enroll/`

## Dev Learnings
_2026-07-18 (developer subagent, SLICE-RES-11):_
- **Heredoc-vs-stdin trap:** a `python3 - <<'PY'` heredoc consumes stdin, so the hook JSON must be captured FIRST (`payload="$(cat)"`) and passed via an env var. Reusable pattern for every future hook-shaped bash+python script in this repo.
- **Mint-once needs `os.link`, not `os.replace`:** the house atomic pattern (`mkstemp -> fsync -> os.replace`) is last-writer-wins — correct for rows, WRONG for a mint-once file. `os.link(tmp, target)` fails EEXIST for the race loser, who then adopts the winner's uuid. Verified with 6 concurrent first-enrollments → 1 project-id, 1 row, zero residue.
- **Deleted-project-id edge:** re-adopt the existing row's uuid via `find_by_root` before minting, or a hand-deleted `.acos/project-id` silently forks a duplicate row for the same root. A fresh clone (different root) still correctly mints new identity.
- **Symlinked cwd is the natural forced-mismatch fixture:** `realpath(cwd) != row.root` is trivially forced with `ln -s projA linkA` — no monkeypatching needed to test the loud log.
- Reused registry_lib's `home=` sandbox contract as an `ACOS_REGISTRY_HOME` env override — tests never touch the real `~/.acos`.

## QA Learnings
_2026-07-18 (developer subagent self-QA, zero-trust re-run of all gates):_
- **What nearly slipped through:** the first draft passed `git=None` for non-repos, which would have CLOBBERED previously captured git facts on every non-repo upsert (upsert_row treats a present key as authoritative). Caught by reading upsert_row's `fields.get(...)` fallback chain; fix = omit the key entirely when the value is absent. Same discipline applied to `last_session_id_hint`.
- **Which check caught the naive-scan guardrail:** the `memory/` stray fixture (memory/ WITHOUT memory/handoffs/) — the gate must probe `memory/handoffs` specifically, not `memory`. Rejection transcript archived (case 2b).
- **project-id written exactly once** proven by inode identity (`stat -f %i`) across re-runs, not just content equality — content-only comparison would miss a rewrite-with-same-value.
- **Harden next:** the hook is unregistered until the parent session applies `hook-registration-block.json`; integration QA must diff `~/.claude/settings.json` to confirm additivity (existing register-session-pid.sh + two matcher:"clear" entries untouched). Also worth a follow-up: a permanently symlinked project root will log ROOT MISMATCH every session (spec-literal, loud-by-design) — watch for noise.
