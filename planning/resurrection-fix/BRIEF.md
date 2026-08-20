# Resurrection Protocol — fix brief

Written 2026-08-19. Scope: `/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection/`
and `/Users/zee/.claude/skills/acos-resurrect/SKILL.md`.

Every finding below is cited and was established on 2026-08-19 by a 5-reader
internal investigation (189 claims, engine label `[3 sources · verified]`) plus a
5-seat web research panel (172 claims). Do not re-derive them. Verify only where
you change behaviour.

---

## 0. STATE OF THE TREE — do this first

- `open-picks.sh` and `conflict-scan.py` are **UNTRACKED** — never committed.
- `launch-project.sh` (+217/-66), `adopt-project.sh`, `close-project.sh`,
  `enroll-project.sh`, `rename-workspace.sh` and `acos-resurrect/SKILL.md` are
  modified-uncommitted. `HEAD` is `66b7b71` (2026-08-17).
- The **committed** `launch-project.sh` does the OPPOSITE of what runs today. Its
  header reads `SPINE 1: focus, never a second workspace`, and it printed
  `focused existing workspace %s — no second workspace created`.
- There is **no commit message anywhere** for Rule 3, Rule 4, or `open-picks.sh`.
  The only provenance is the files' own self-dated comments.

**ACTION:** commit the current working tree to a branch FIRST, with a message
explaining Rule 3 and Rule 4, before changing anything.

---

## 1. "tab" means three different things (naming only — the mechanism is correct)

- `launch-project.sh:11-17` and its runtime print at `:393-397` say "a new tab".
- `launch-project.sh:445-446` calls `cmux workspace create`. That is a WORKSPACE.
- `SKILL.md:33-39` says "ANOTHER window" for the same thing.

**The mechanism survived adversarial refutation and must NOT change by default.**
`cmux new-surface` has no `--command` and no `--description`. Only
`workspace create` takes name + description + cwd + command atomically. The argv
route is required and stated at `launch-project.sh:19-20`:

> "the prompt route is argv (--command), never cmux send / surface.send_text
> (they shred multi-line prompts at every \n)"

Identity is the `[key:<uuid>]` tag, which lives in a workspace DESCRIPTION. A
surface has no description slot. The whole resurrection folder has **zero** uses
of `--surface` and **zero** of `CMUX_SURFACE_ID`.

**FIX:** pick ONE word (recommend "workspace", matching cmux) and use it in all
three places. Do not silently keep three.

---

## 2. OPTIONAL new capability — a real tab-in-workspace route

Zee asked for a second TAB inside an existing project's workspace, not a second
workspace. Possible, but it is NOT the current design. This is the largest item
in the brief. **If it is out of scope, say so explicitly and ship item 1's naming
fix alone.**

Three viable routes, in order of preference:

- (a) `new-workspace --layout <json>` — layout surfaces define their own commands;
  create-time only.
- (b) `cmux new-surface --workspace <id> --working-directory <path>` then
  `respawn-pane --surface <id> --command <cmd>`.
- (c) `new-surface` then `cmux send` + `send-key Enter`. **PROVEN to work on
  2026-08-19 for a SINGLE-LINE command**, but `launch-project.sh:19-20`
  explicitly forbids it for multi-line prompts. Do not use for multi-line.

**HARD BLOCKERS to solve before shipping any of these:**

- `launch-project.sh:440-464` joins back to the new workspace by diffing which
  workspaces carry the `[key:<uuid>]` tag. Under one-workspace-many-surfaces that
  diff finds nothing and refuses at `:461-463`.
- A workspace-scoped `read-screen` returns ONLY the selected surface. MEASURED on
  workspace `0B30D6A1` with 2 surfaces: the workspace-level read md5-matched
  `surface:15` exactly and did NOT match `surface:13`. Pass `--surface`.
- `windows_lib.py:54-60` keys its manifest file by workspace id, so two surfaces
  collapse into one file; `:86-105` overwrites `label`/`session_id`; `:181-186`
  `other_windows` always returns `[]`; `:203-213` `is_last_window` parks the row
  while a sibling is still working; `:165-178` a closed surface reads live
  forever; `:328-366` `merge_window` with src==dst deletes the target.
- `adopt-project.sh:495-496` self-excludes siblings, so its D11 prompt never
  fires. `enroll-project.sh:106-137` enrolls every surface as the same project.
- `conflict-scan.py` ROOT-UNREACHABLE (`:144-173`) breaks both ways: one
  description per workspace hides N-1 projects, and `current_directory` is a
  workspace property so surfaces get judged against the wrong folder.
- `knowledge_lib.py:22-26,89-94` and `prune-state-bindings.ts:48-89,107-130` are
  UNAFFECTED (pure `project_uuid` / pid+lstart). Do not touch them.

---

## 3. The delivery proof is a race the script always loses

**ROOT CAUSE:** an uncommitted Rule 4 change to `build_command`
(`launch-project.sh:190-214`). `HEAD` ended `exec /bin/zsh -i`; the working tree
ends `exec claude --dangerously-skip-permissions`. The BEGIN-marker check was
sound while the window stayed in a shell. A full-screen TUI was layered on top,
and the proof was only RE-ASSERTED in prose (`:24-25`), never redesigned.

- `--scrollback` IS passed (`:248-255`). That hypothesis is dead. The buffer is
  EMPTY, not truncated: `--lines 5000` returns the SAME 46 lines as the default.
  `read_screen` omits `--surface` and `--lines` entirely.
- **TIMING:** join-back sleeps 1s (`:453-460`), then each attempt sleeps 2s
  BEFORE reading (`:466-482`) — samples at ~T+3s and ~T+5s, both after the
  marker's lifetime. Audit arithmetic in `~/.acos/registry-audit.jsonl:1068-1082`:
  `delivered:true` ≈ 3.22s, `delivered:false` ≈ 5.23s, a 2.0s delta equal to one
  extra `sleep(2)`. **Attempt 2 converted ZERO failures.** Waiting longer cannot
  fix this; it samples further into the erasure.
- **PROOF THE NOTES ARRIVED:** `cmux rpc workspace.list` carries
  `latest_submitted_message` == the exact prompt from `:209-210`.
  Logo Builder: `latest_submitted_at` `17:01:10.311Z` = **1.37s AFTER** its
  `delivered:false` audit line 1072. Insightia: `17:01:14.375Z` = **0.20s AFTER**
  line 1076. The script gave up, then the prompt landed.
- **RE-CONFIRMED LIVE 2026-08-19:** workspace `721DD59A-BD50-4588-8C4F-FC66A221716D`
  (Skill Workshop) printed `DELIVERY NOT-VERIFIED`, yet
  `latest_submitted_at` = `2026-08-19T20:37:03.835Z` with the full reentry path
  in `latest_submitted_message`. The replacement key works.
- The marker proves the WRONG THING anyway: it only shows the shell `cat`'d the
  note, never that Claude received the argv prompt (`:211-213`).

**FIX:** key the proof on `latest_submitted_message` / `latest_submitted_at` from
`workspace.list`. It is structured (repaint-proof), identity-bound (it contains
the reentry path the script itself resolved at `:335`), and `list_workspaces()`
is ALREADY called in the post-create join loop at `:453-460` — no new cmux verb
needed. **CAVEAT:** these fields are undocumented in-repo and were observed only
in live output. Treat as volatile; keep a loud fallback.

**ALSO FIX** the inverted diagnostic at `:496-497`, which appends "trust gate
present (likely cause)". In the 2026-08-19 batch the correlation ran the other
way: `delivered=true ⟺ trust_gate=true` (2/2), `delivered=false ⟺
trust_gate=false` (3/3). The gate appears to PAUSE the repaint and preserve the
marker. n=5, correlation only — do not state it as causal, but stop asserting the
opposite.

---

## 4. All-or-nothing does not cover tombstoned or completed rows

- `open-picks.sh:15-16` promises the pre-check catches "one tombstoned row". The
  pre-check at `:91-116` has **NO status test**.
- A uniquely-named tombstoned row passes the pre-check and is refused later,
  inside the sequential loop, at `launch-project.sh:315-317` — AFTER earlier picks
  already opened windows. That breaks the all-or-nothing contract.
- **WORSE:** `completed` rows are ARCHIVED (`resurrect-view.py:371`) but are NOT
  refused by launch at all. One would open and be flipped back to `active`.

**FIX:** test status in the pre-check, before anything opens.

---

## 5. An unrunnable fix line

`conflict-scan.py:175-202` (BLEED) prints a fix naming `prune-state-bindings.sh`.
The file is `prune-state-bindings.ts`. As printed, the fix cannot be run.

---

## 6. Four scripts disagree on what "already open" means

- `launch-project.sh:148-180` `workspace_matches()` → `:393-400` creates another
  workspace anyway (Rule 3).
- `adopt-project.sh:166-184` `binds_row()` → `:495-506` exits 4 and ASKS (D11).
- `close-project.sh:633-644` counts workspaces per window (`last_ws`).
- `close-project.sh:742-762` + `windows_lib.py:203-213` `is_last_window()` (D14).

**FIX:** one shared predicate, or a documented reason each differs.

---

## 7. Pick numbers become STATIC (Zee's ruling, 2026-08-19)

**DECISION.** Numbers are assigned once per row and never change on their own.
This supersedes any earlier "keep positional numbers + book-token gate"
recommendation. **Do NOT build the book-token gate** — static ordinals remove the
staleness hazard at its root, because a number read off a stale screen still
resolves to the same row.

### Facts established 2026-08-19 (do not re-derive)

- `pick_number` is currently a per-render counter assigned at
  `resurrect-view.py:513`, over a sort that is tier-index-asc then ref_time-desc
  (`:496-499`). ARCHIVED rows get `None` and consume no number.
- The tier ladder (`:370-380`) does NOT read `active`/`parked`. A row changes tier
  because a tagged cmux workspace makes it `live` (`:281-307`, `:484`). So a
  number moves when a human closes a tab BY HAND, with **no registry write at all**.
- `ROW_KEYS` (`registry_lib.py:49-63`) is a closed 13-key tuple; `_validate_row`
  (`:144-151`) and `upsert_row` (`:200-204`) reject unknown keys. No stable
  human-scale id exists today — only `project_uuid`.
- `enrolled_at` IS already a `ROW_KEY`. It supplies the backfill ordering.
- `open-picks.sh` has **NO range syntax**: `tokens()` at `:79-81` splits on commas
  and whitespace only, so a token like `2-5` fails `t.isdigit()` and is refused.
  Dense contiguous numbering is therefore NOT required.
- Counter growth is negligible. Git's 7→9-12 hexdigit growth was hash-collision
  driven (birthday paradox); that does not apply to a sequential counter.
  53 rows today; 4 digits covers thousands.

### Implement

1. Add `pick_ordinal` (positive int) to `ROW_KEYS` and to `_validate_row`.
2. **Backfill once:** sort all rows in `~/.acos/registry.d/` by `enrolled_at`
   ascending and assign 1..N (53 rows as of 2026-08-19). Deterministic and
   re-runnable. Write a one-shot script; do not hand-edit row files.
3. New rows get `max(pick_ordinal ever issued) + 1` — see the ledger in item 8.
   Minting sites: `enroll-project.sh`, and the `add <workspace>` verb in
   `acos-resurrect/SKILL.md`. Start at 1 — reserve `0`, because
   `acos-safe-close/SKILL.md:235-241` uses `0` for "new project".
4. **NEVER auto-reuse an ordinal**, including after tombstone or delete. A
   tombstoned row keeps its number forever and stays visible under ARCHIVED.
5. `resurrect-view.py`: stop computing `pick_number` at `:513`. Read
   `pick_ordinal` from the row and emit it as `pick_number` in BOTH the gutter and
   `book.json`, so the invariant at `:501-506` (gutter integer ≡ book.json
   pick_number) is preserved — in fact strengthened, since one persisted value
   cannot drift.
6. Assign a number to EVERY row including ARCHIVED ones. Today they get `None`
   and cannot be referred to at all. This MUST ship together with item 4 — with
   archived rows numbered, the missing status test becomes easier to trip.
7. Add an `ORDINAL-CLASH` class to `conflict-scan.py`, alongside `NAME-CLASH`:
   two live rows carrying the same `pick_ordinal`. This is the detector for the
   `max+1` race, since `registry_lib.py:10-13` documents no blocking lock and none
   surviving SIGKILL. At one human and a few opens a day the race is very
   unlikely, but it must be diagnosable if it happens.
8. **Display.** The gutter will no longer ascend down the page, because rows stay
   sorted by tier then recency. That is ACCEPTED — the number is a label read
   beside the name, not a position counted to. Precedent: tmux ships
   `renumber-windows off` as its default (verified live on this machine
   2026-08-19, together with `base-index 0`). Render the ordinal in its own
   right-aligned gutter column so it stays scannable. Do NOT re-sort tiers by
   ordinal unless Zee asks — that would raise the oldest projects to the top of
   every tier and defeat the tiers.
9. The echo in `open-picks.sh:126-129` can stay a PRINT, not a gate. It only had
   to become a gate because the number could lie; it no longer can.

---

## 8. NEW — row management verbs: delete, swap, renumber (Zee's request 2026-08-19)

All four verbs below are **HUMAN-INITIATED ONLY**. Never invoke on your own
initiative, never batch. The user must name the row themselves in the
conversation, exactly as the existing `tombstone` verb requires.

### The ordinal ledger (build this first — the other verbs depend on it)

`~/.acos/registry.d/ordinal-ledger.jsonl` — append-only, one JSON object per
line. Record every ordinal event: `issue`, `swap`, `renumber`, `retire`,
`restore`. Each entry carries the ordinal, the `project_uuid`, the row name at
the time, an ISO timestamp, and the verb.

This is the source of truth for **"ever issued"**. Auto-assignment reads it and
takes `max + 1`, so a number freed by delete or renumber is never handed back out
automatically. Precedent for the rule: Atlassian documents that reusing Jira keys
means *"old issue links… will stop redirecting"*; Linux's fix for recycled
process ids was `ESRCH` — fail loudly rather than act on the wrong target
(`pidfd_send_signal(2)`).

### `delete <n>` — soft delete, recoverable

- Moves `~/.acos/registry.d/<uuid>.json` to
  `~/.acos/registry.d/deleted/<uuid>.json`. Does NOT unlink.
- Move `~/.acos/windows/<project_uuid>/` alongside it, so a restore brings the
  window manifests back too. Leave the knowledge store keyed on `project_uuid`
  (`knowledge_lib.py:22-26,89-94`) in place — it is addressed by uuid and
  survives independently. State in the receipt that it was left behind.
- **CONFIRMATION MUST BE ACTIVE, NOT PASSIVE.** Require the user to type the
  project's NAME. Do not accept `y`/Enter. Evidence: Akhawe & Felt, USENIX
  Security 2013 (>25M impressions) found extra clicks do not deter — **84% of
  Firefox users who did the first two clicks did the third**. Habituation work
  (Vance et al., MIS Quarterly 42(2) 2018; Anderson et al., CHI 2015) shows
  attention drops sharply after the SECOND exposure. Bravo-Lillo et al., SOUPS
  2014 found prompts that *"forced the user to interact with the text field
  containing the change"* resisted habituation — flagged MEDIUM confidence, since
  the paper sites returned 403 and it came via a search index. Precedent: GitHub
  makes you *"type the name of the repository you want to delete"* despite having
  a stable id.
- The deleted row's ordinal is RETIRED in the ledger. Never auto-reissued.
- Refuse if the row is currently `live` (a workspace is open on it). Say so and
  name the workspace.

### `restore <uuid>` — bring a deleted row back

- Moves the row file and its window manifests back from `deleted/`.
- Restores its ORIGINAL `pick_ordinal`. If that ordinal is now held by another
  live row, REFUSE and name the holder; tell the user to `renumber` or `swap`
  first. Never silently displace.

### `purge <uuid>` — true unlink, from `deleted/` only

- Separate verb. Only operates on rows already in `deleted/`.
- Requires the name typed again. Irreversible; say so plainly in the prompt.
- The ordinal stays retired in the ledger even after purge.

### `swap <a> <b>` — exchange two rows' ordinals

- Both rows must exist and be non-deleted. Refuse otherwise, naming which.
- There is no lock (`registry_lib.py:10-13`), so this cannot be atomic. Write
  both, then RE-READ both and verify. On a partial write, report loudly and name
  `ORDINAL-CLASH` as the diagnostic. Do not retry silently.
- Append one `swap` entry to the ledger recording both sides.

### `renumber <n> to <m>` — set one row's ordinal

- Refuse `m <= 0`. `0` is reserved (`acos-safe-close/SKILL.md:235-241`).
- If `m` is held by a LIVE row: REFUSE, name the holder, and suggest `swap`.
  Never silently displace.
- If `m` is RETIRED in the ledger: warn, name what previously held it and when,
  and require an explicit confirmation. Manual assignment MAY reuse a retired
  ordinal; automatic assignment never may.
- If `m` is free and never issued: assign it. Note in the receipt that the
  auto-assign high-water mark has moved, so the next new row will take `m + 1`
  if `m` is now the maximum.
- The vacated ordinal `n` is RETIRED, not freed.

### `compact` — close all gaps (LOUD, opt-in, never automatic)

- Reassigns every non-deleted row to 1..N in current ordinal order.
- **This invalidates every number the user has memorised.** Say that in the
  confirmation, and require the word `compact` typed in full.
- This is exactly tmux's `renumber-windows`, which ships **off** by default and
  was reintroduced in tmux 1.7 (13 Oct 2012) only as an opt-in, after the 19 Sep
  2007 changelog entry *"Don't renumber windows on close."*
- Known cost, on record: in tmux issue #3214, renumbering silently cleared a
  stored reference to a window. The maintainer replied *"Yes, this is not
  ideal..."* and fixed it. Assume the same class of breakage here.
- Append one ledger entry per row moved.

### Gaps are now real — say so in the book

Once delete and renumber exist, the gutter genuinely goes sparse. That is the
accepted cost of the user's ruling. On record as a real complaint: in tmux issue
#3096, a user filed gaps AS a bug — *"you always have to read the indices."* The
mitigation is item 7's right-aligned gutter column, so the number is read beside
the name rather than counted to.

---

## 9. Name-based picking is broken for almost every row

Two independent defects, both in `open-picks.sh`:

- **Whitespace split.** `tokens()` at `:79-81` splits on `[,\s]+`, so a
  multi-word name becomes several tokens. MEASURED 2026-08-19:
  `--picks "Skill Workshop"` returned
  `REFUSED — 'Skill' matches no row name in this book` and
  `'Workshop' matches no row name in this book`. This breaks the name route for
  nearly every project on this machine — `To Do Tree`, `OKOA Works`,
  `Logo Builder`, `Research to Portfolio`, `Guided Reader`, `Reverse Cleanroom`,
  `Eden Protocol`, `Git Management`, `Axiom Synthesis`, and more.
- **Duplicate names.** `Website-builder`, `To Do Tree`, `Research to Portfolio`,
  `FruitSync` and `ACOS 3.0` each sit on TWO rows (captured 2026-08-19).
  `:108-116` refuses an ambiguous name and enumerates the colliding uuids.
  `registry_lib.py:229` recomputes `name` on every write and does NOT enforce
  uniqueness.

**Consequence:** between these two, the pick NUMBER is the only working handle
for most rows. That is the strongest argument for item 7.

**FIX:** support quoted multi-word names (e.g. `"Skill Workshop"`) or an explicit
`name:` prefix, and make ambiguous names resolvable — e.g. `FruitSync @ /path`,
or a disambiguating suffix in the row's stored name.

---

## 10. Stale docstrings

`launch-project.sh:2` says "open-a-window" while the embedded docstring at
`:63-76` still says "focus-or-launch (SPINE 1)" and documents a reentry resolver
that has since been replaced.

---

## Tests — there is currently ZERO coverage of numbering

`test_resurrection_book.py:22-98` has 14 test methods that all either test
`window_label()` or call `render_human()` with `pick_number` hardcoded to `1`.
`build_book` is never called by any test.

Add tests for:

- backfill is deterministic and idempotent over a fixture registry
- a new row gets `max+1` from the ledger, counting tombstoned AND deleted rows
- an ordinal survives park→active→park, `finish`, and `tombstone` unchanged
- a tombstoned or deleted ordinal is never auto-reissued
- ARCHIVED rows carry a number AND are still refused by the pre-check
- gutter integer == `book.json` `pick_number` for every row
- `ORDINAL-CLASH` fires on two live rows sharing an ordinal
- `delete` refuses a live row; `restore` refuses when the ordinal is taken
- `swap` leaves no clash; a simulated partial write is detected on re-read
- `renumber` refuses `0`, refuses a live-held target, warns on a retired target
- `compact` renumbers 1..N and writes one ledger entry per moved row
- a quoted multi-word name resolves to exactly one row
- the new delivery proof passes on a real launch and fails on a dead workspace

---

## Constraints

- Do not change the argv delivery contract (`launch-project.sh:19-20`).
- Do not build the book-token staleness gate (superseded by item 7).
- `finish` and `tombstone` still only HIDE. Only the new `delete`/`purge` verbs
  remove anything, and only on explicit human instruction with the name typed.
- Preserve the gutter-integer ≡ `book.json` `pick_number` invariant
  (`resurrect-view.py:501-506`).
- Reserve `0`: `acos-safe-close/SKILL.md:235-241` uses it for "new project".
- Never write the daemon state dir
  (`~/Library/Application Support/acos-token-monitor/state/`), never touch
  `pending-resume-*.txt` / `RESCUED-resume-*.txt`, and never modify or invoke
  `/acos-complete`.
