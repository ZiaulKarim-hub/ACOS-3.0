# SLICE-12-rebuild — rebuild-registry.py: reproduce the 16/16 baseline reading no registry file (+ DP5 seeder)
**Epic EPIC-1 / Story STORY-1.1 — Demo: Demo 1 (enrollment)**
_Vertical value:_ A derived index cannot dangle: rebuild DELETES the 55%-dangling-pointer class instead of mitigating it.

## PM (Planner / Specifier) — Lean Context Engineering
**Single objective:** rebuild-registry.py: reproduce the 16/16 baseline reading no registry file (+ DP5 seeder)

**In scope:**
- Enumerate find */memory/handoffs (authoritative) + */CLAUDE.md + */.acos across BOTH parents (Vibe Coding, OKOA)
- Use ~/.claude.json project paths as a lossy hint (glob-disambiguation only, never a decoder)
- Reproduce the proven 16/16 baseline; flag (never auto-enroll) the Vibe Coding-root anomaly

**Out of scope (guardrails):**
- Auto-enrolling the parent-folder anomaly without confirmation
- Treating ~/.claude.json path-mangled keys as authoritative

**Allowed files / contexts:** .claude/scripts/resurrection/rebuild-registry.py; read-only enumeration of both parents + ~/.claude.json. Writes only via registry_lib.py.

**Definition of Done:** all acceptance criteria below pass; required artifacts written under the repo path; the evidence bundle at `.acos/evidence/[DATE]/SLICE-12-rebuild/` is populated; `## Dev Learnings` and `## QA Learnings` are updated (a slice is not Done until they are — §0.7).

## Dev (Executor) — steps + 7-part Evidence Bundle
**Steps (execute EXACTLY; no scope expansion, only allowed files):**
- Implement enumeration across both parents + ~/.claude.json.
- Reconcile candidates; reproduce 16/16 from handoff artifacts alone.
- Flag the Vibe Coding-root anomaly in the dry-run output.

**Evidence Bundle to produce:** 1) Implementation Summary; 2) Requirements Traceability (to spec FR-* / tech_prd TR-*); 3) Structural Quality Evidence; 4) Functional/structural checks (the verification method below); 5) Security/Compliance notes; 6) Operational/Runtime considerations; 7) Self-assessment (confidence + known limitations).

## QA (Zero-Trust Verifier)
Assume the Dev did **not** do the work correctly. Verify scope respect, evidence authenticity (no fabricated logs — spot-check and recompute), and that every acceptance criterion + evidence gate is satisfied. QA may **REJECT** and require rework until the gates pass (a reject blocks the slice like an INCONCLUSIVE reviewer).

**QA checks:**
- Delete the registry.d contents and confirm rebuild reconstructs 16/16 from disk alone
- Confirm the Vibe Coding-root anomaly is flagged, never silently enrolled
- Confirm ~/.claude.json is used as a hint only (a mangled key never becomes identity)

## Definition of Done (maps to ACOS `slice.yaml`)
**acceptance_criteria:**
- Dry-run lists >=18 candidates across both parents including the Vibe Coding-root anomaly (flagged, not auto-enrolled)
- Reproduces the 16/16-row baseline reading no registry file
- Output reconciles with the rows enrollment creates later

**verification_method:** Dry-run output archived; 16/16 reconstruction diffed against enrollment-created rows; anomaly flag shown.

**evidence bundle:** `.acos/evidence/[DATE]/SLICE-12-rebuild/`

## Dev Learnings
**2026-07-18 (execution):**
- **The identity anchor makes rebuild trivial.** Because `<root>/.acos/project-id` is the durable identity (not the registry), a full `registry.d` wipe reconstructs byte-identical uuid-per-root rows — the registry really is a pure derived index. The 40-line-proof pattern scaled cleanly once id-reuse was absolute (reuse ALWAYS; mint only under `--apply`; dry-run mints nothing).
- **Depth-1 `os.scandir` beats `find` here:** the parent-root anomaly falls out naturally by putting each parent itself in the candidate list before its children, and `.claude/worktrees`-style nested paths are excluded by construction rather than by filter.
- **Real disk drifted from research and floors saved us:** 22 candidates vs the researched ~18 (4 new corroborating-marker-only roots), and `website-design-okoa` has handoffs but NO `~/.claude.json` row — live proof hints are lossy in both directions. Assert floors (≥15/≥16), never exact counts.
- **Reuse:** `_write_text_atomic` (mkstemp pattern for non-JSON files) belongs in registry_lib if a third script ever needs it; the fixture harness pattern (`--parents/--home/--claude-json` overrides) keeps every destructive test off the real home and should be copied by SLICE-13.
- Surprise: dedup by `realpath().casefold()` — the registry's own index key — is also the right candidate-dedup key; using anything else would let a case-twin enroll twice.

## QA Learnings
**2026-07-18 (zero-trust verification, 20/20 fixture checks + real-disk assertions):**
- **What nearly slipped through:** a malformed `<root>/.acos/project-id` (non-UUID content). The naive path would silently re-mint and orphan the old identity; T4a/T4b now pin the required behavior — `skipped-issues`, file untouched, human review. Harden any future writer the same way.
- **Which check caught the most:** the wipe-then-rebuild diff (T3b, `before == after` on root→uuid). It is the only check that proves the "derived index cannot dangle" claim rather than asserting it; keep it as the permanent regression gate for SLICE-13 seeding.
- **Hint discipline verified mechanically:** a `~/.claude.json`-only path with zero disk markers never became a candidate (T1h), and mangled worktree keys surfaced only in the informational hint-only list on the real run — a hint never minted anything.
- **Audit as tripwire:** asserting the audit event set is exactly `{"upsert"}` (T5b) is a cheap, durable way to prove rebuild never tombstones/deletes — recommend the same assertion in every future registry-writing slice.
- Real-run evidence was re-generated fresh in this session (not trusted from the prior draft bundle); `~/.acos/registry.d` confirmed absent after the real dry-run — dry-run wrote nothing to the real home.
