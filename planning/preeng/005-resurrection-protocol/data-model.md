# Data Model — 005-resurrection-protocol
*(`/preeng.plan` output. Schemas for every persisted entity. JSON everywhere; stdlib-only.)*

## 1. Project registry row — `~/.acos/registry.d/<project_uuid>.json`
One file per project; one writer per file; every field DERIVED or GENERATED (SPINE 2 — none hand-typed).
```json
{
  "project_uuid": "uuid4 (identity; minted once at enrollment)",
  "name": "basename(root)  (derived)",
  "status": "active | parked | completed | tombstoned",
  "enrolled_at": "ISO-8601",
  "last_verified_at": "ISO-8601  (decays to 'unverified', NEVER to 'wedged')",
  "root": "realpath(root)",
  "lookup_key": "realpath(root).casefold()  (APFS index)",
  "st_dev": 0,
  "st_ino": 0,
  "git": { "branch": "str|null", "commit": "str|null", "dirty_count": 0, "remote": "normalized|null" },
  "last_close": {
    "at": "ISO-8601",
    "handoff_path": "memory/handoffs/closed/<slug>/handoff.yaml",
    "reentry_path": "memory/handoffs/closed/<slug>/<slug>.reentry.md",
    "sha256": "sha256(handoff.yaml)",
    "next_action": "GENERATED imperative headline, <=90 chars"
  },
  "lastSessionId": "optional hint from ~/.claude.json (lossy; never a decoder)"
}
```
- Identity = `project_uuid`. Lookup index = `lookup_key`. Re-link key = `(st_dev, st_ino)` (inode survives
  rename/move -> heal, don't tombstone). Git fields are captured attributes, NEVER identity.
- Rows are tombstoned, never deleted (deletion is a human act; no age-based reaper; ~10 KB/handoff).

## 2. Audit event — append-only `~/.acos/registry-audit.jsonl` (one `os.write` per line)
```json
{ "ts": "ISO-8601", "event": "enroll | close | resume | finish | tombstone",
  "project_uuid": "uuid4", "details": { } }
```
The sole adoption measurement (menu used >=1x/week at day 60). Append-only; never rewritten. No nagger.

## 3. project-id file — `<root>/.acos/project-id` (git-ignored)
Plain text: the `uuid4` minted once at enrollment. Git-ignored on purpose — a fresh clone deserves a new id
(the Backup/Clone case that refuted git identity: one upstream, 3 toplevels, 3 HEADs).

## 4. Close handoff — `memory/handoffs/closed/<slug>/handoff.yaml`
```yaml
type: close-project          # distinct from Eternity's handoff types
status: parked               # parked | (resume -> active) | (finish -> completed)
project_uuid: <uuid4>
intent_core:                 # PARENT-written, never delegated
  decisions: [ ]
  rejected_alternatives: [ ]
  traps: [ ]
  open_questions: [ ]
  next_action: "<=90 char generated headline"
git_state: { branch, commit, dirty_count, drift_block }
```
Co-located under `closed/<slug>/` — invisible to Eternity's non-recursive
`ls -t memory/handoffs/*.md memory/handoffs/*.yaml` glob (namespace disjointness, C5).

## 5. Reentry doc — `memory/handoffs/closed/<slug>/<slug>.reentry.md`
The multi-line resume prompt delivered via argv at launch. **Extension is `.reentry.md`, NEVER `.resume.md`**
(`.resume.md` is addressable by Eternity's pointer path). Re-resolved at open time (SPINE 6), never cached.

## 6. cmux workspace description tag
`"<next_action> [key:<project_uuid>]"` — the `[key:...]` tag at the END (~45-char overhead) is the
workspace-to-row join; process-join is the fallback for untagged/hand-opened workspaces; cwd-string and title
are NEVER used to join.

## 7. Daemon stop marker — `state/stop-<SESSION_ID>`
The ONLY permitted write into the daemon state dir, at close step 0 (so Eternity cannot fire mid-close).
`pending-resume-*.txt` / `RESCUED-resume-*.txt` are never deleted, moved, or rewritten.

## 8. Evidence bundle — `.acos/evidence/[DATE]/[SLICE-ID]/`
Per-slice: Phase-0 probe outputs, tamper-test transcripts, the DR-1 close->resume recording + receipts.

## 9. Entity relationships (see `domain-lattice.json`)
`ENT-registry-row` part_of `PROC-enrollment`; `ENT-close-handoff`/`ENT-reentry-doc`/`ENT-stop-marker` part_of
`PROC-safe-close`; `ENT-desc-tag` part_of `PROC-launch-focus`; `ENT-the-book` part_of `PROC-resurrect-menu`;
`ENT-evidence-bundle` part_of `PROC-dr1`. `ENT-registry-row` uses `M-tombstone`; `ENT-audit-event` uses
`M-audit-append` and is `measured_by` `MET-adoption-day60`.

## 10. Invariants
- Every field derived/generated (no hand-typed field). A stale persisted master cannot exist (book rendered
  fresh). A derived index cannot dangle (deletes the 55%-dangling class). Truncated registry JSON fails LOUDLY.
- Membership never depends on a clean close (enrollment-on-first-sight; rebuildable from disk).
