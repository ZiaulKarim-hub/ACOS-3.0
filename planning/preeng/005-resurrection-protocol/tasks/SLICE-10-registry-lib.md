# SLICE-10-registry-lib — registry_lib.py: atomic write, schema, casefold index, inode re-link, tombstone, audit
**Epic EPIC-1 / Story STORY-1.1 — Demo: Demo 1 (enrollment)**
_Vertical value:_ The durable substrate: a per-project write that a crash or a second writer can never corrupt silently.

## PM (Planner / Specifier) — Lean Context Engineering
**Single objective:** registry_lib.py: atomic write, schema, casefold index, inode re-link, tombstone, audit

**In scope:**
- Atomic write: mkstemp(dir=target's own dir) -> write -> fsync(tmp) -> os.replace -> fsync(dir); never a fixed .tmp
- Row schema (data-model E1); realpath().casefold() lookup index; (st_dev,st_ino) re-link
- tombstone-never-delete; audit append (one os.write per JSONL line) to ~/.acos/registry-audit.jsonl
- Loud failure on truncated/invalid JSON load

**Out of scope (guardrails):**
- Any lock that blocks (LOCK_EX) or survives SIGKILL (mkdir-lock)
- YAML/SQLite; a shared master file
- Deleting rows (deletion is a human act only)

**Allowed files / contexts:** .claude/scripts/resurrection/registry_lib.py; a scratch dir for the contention crash-test. No cmux, no skills yet.

**Definition of Done:** all acceptance criteria below pass; required artifacts written under the repo path; the evidence bundle at `.acos/evidence/[DATE]/SLICE-10-registry-lib/` is populated; `## Dev Learnings` and `## QA Learnings` are updated (a slice is not Done until they are — §0.7).

## Dev (Executor) — steps + 7-part Evidence Bundle
**Steps (execute EXACTLY; no scope expansion, only allowed files):**
- Implement the atomic write helper and the row read/upsert API using stdlib only (py 3.9.6).
- Implement casefold index lookup and (st_dev,st_ino) re-link/heal.
- Implement audit append and tombstone.
- Write and run the contention crash-test: 6 processes x 60 writes.

**Evidence Bundle to produce:** 1) Implementation Summary; 2) Requirements Traceability (to spec FR-* / tech_prd TR-*); 3) Structural Quality Evidence; 4) Functional/structural checks (the verification method below); 5) Security/Compliance notes; 6) Operational/Runtime considerations; 7) Self-assessment (confidence + known limitations).

## QA (Zero-Trust Verifier)
Assume the Dev did **not** do the work correctly. Verify scope respect, evidence authenticity (no fabricated logs — spot-check and recompute), and that every acceptance criterion + evidence gate is satisfied. QA may **REJECT** and require rework until the gates pass (a reject blocks the slice like an INCONCLUSIVE reviewer).

**QA checks:**
- Independently re-run the crash-test and recompute torn/errored counts (do not trust the Dev's log)
- Truncate a row file by hand and confirm the loader raises, not returns partial
- Confirm no blocking lock and no mkdir-lock anywhere
- Confirm every field is derived/generated per data-model E1

## Definition of Done (maps to ACOS `slice.yaml`)
**acceptance_criteria:**
- Contention crash-test 6x60 -> 0 errors, 0 torn (mirrors the measured 180/360 -> 0)
- A truncated file load fails LOUDLY (JSON), never a silent partial
- Re-link by (st_dev,st_ino) heals a moved root instead of tombstoning it
- Audit append is one os.write per line; ordering preserved

**verification_method:** Crash-test output archived; unit checks for casefold lookup, inode re-link, and loud-truncation; stdlib-only import audit.

**evidence bundle:** `.acos/evidence/[DATE]/SLICE-10-registry-lib/`

## Dev Learnings
_(fill at execution — the slice is NOT Done until this is updated: what worked, what surprised, what to reuse.)_

**2026-07-18 (SLICE-RES-10 build):**
- **What worked:** making `upsert_row` a whitelist (`project_uuid, root, status, last_close, git, last_session_id_hint`) and recomputing every index field from the filesystem on every write made "no hand-typed fields" a structural property instead of a review item — unknown keys raise. Reuse this pattern for close-project.sh's row enrichment.
- **What surprised:** the contention storm needed no lock at all to hit 0 torn across ~2k concurrent reads of 360 writes — mkstemp's unique temp name plus `os.replace` is the entire mechanism. The fixed-`.tmp` failure mode (writer A truncating writer B's in-flight temp) simply cannot occur. Also: `FileNotFoundError` in the reader loop is only possible before the seed write; after the first `os.replace` the path is never absent, which simplifies reader accounting.
- **What to reuse:** the `home=None` override threading through every public function is what made the "never touch real ~/.acos" guarantee testable — plus a hard refusal in `_selftest` when `home == realpath(~)`. Every future Resurrection slice that touches `~/.acos` should copy this override + refusal pair. The hidden `--contend-worker` self-spawn (`sys.executable` + `abspath(__file__)`) is a clean way to get real multi-process contention without any test framework.

## QA Learnings
_(fill at execution — the slice is NOT Done until this is updated: what nearly slipped through, which check caught it, what to harden.)_

**2026-07-18 (SLICE-RES-10 verification):**
- **What nearly slipped through:** the first draft of the enroll check contained a vacuous assertion (`== list(...)[0:0] or True` — always true); caught by re-reading the test body before the first run, replaced with a real `dev_ino == [st_dev, st_ino]` comparison. Harden: any selftest line ending in `or True` is a fabricated pass — grep for it.
- **Which checks caught real properties:** the independent second run (fresh `--home`) reproduced 8/8 with a different read count (2124 vs 1954), confirming the storm result is not a one-off; the audit re-parse (364/364 lines valid JSON after 6 concurrent appenders) is the actual proof of the one-`os.write`-per-line rule — a multi-write implementation would have torn lines here.
- **What to harden later:** the casefold check's swapped-case branch only truly exercises on APFS case-insensitive volumes (on case-sensitive filesystems it falls back to the true-case path); if a future CI runs on a case-sensitive volume, add an explicit on-disk-case fixture. Audit ordering is kernel O_APPEND order — if strict cross-process sequencing is ever needed, add a per-process monotonic counter field rather than a lock.
