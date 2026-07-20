---
name: acos-resurrect
description: The Resurrection Protocol menu — renders the registry book FRESH via resurrect-view.py and shows it VERBATIM, routes the user's pick (same-root reentry read inline; otherwise launch-project.sh focus-or-launch relayed verbatim), and runs the loop verbs: finish (status completed — hidden in ARCHIVED, never deleted), tombstone (human-initiated only), curate (walk the seed CURATION-REPORT one row at a time). Trigger phrases: "resurrect", "resurrection protocol", "show my projects", "project menu", "which projects", "/acos-resurrect".
disable-model-invocation: false
user-invocable: true
---

# ACOS Resurrect — the menu over the book (Resurrection Protocol proper)

Resurrect = see every project honestly, pick one, land in it with its reentry in
front of you. ALL computation lives in the scripts:
`.claude/scripts/resurrection/resurrect-view.py` (the book — computed fresh,
read-only, BROKEN rows shown) and `.claude/scripts/resurrection/launch-project.sh`
(focus-or-launch, SPINE 1, delivery verification). Status transitions go through
`.claude/scripts/resurrection/registry_lib.py` ONLY. This skill routes and
relays; it computes nothing and decorates nothing.

This skill is GLOBAL (installed in `~/.claude/skills/`), but the scripts live
ONCE — in the ACOS 3.0 install. Every block resolves `RESDIR` to this project's
own `.claude/scripts/resurrection` when present, else falls back to the
canonical path `/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection`
(the same absolute path the SessionStart enroll hook uses). The registry itself
is already global (`~/.acos/registry.d/`), so the book is identical from any
project. `ROOT` always stays `$(pwd)` — the project you are operating in.

Loop economics (what the verbs mean): **resume flips parked->active** — the
launcher does that flip itself on every focus/create, and Step 3 does it for a
same-root pick; every `registry_lib` upsert refreshes `last_verified_at`.
**finish sets completed** — the row moves to ARCHIVED on the next render, hidden
from the active tiers, never deleted. The book render itself is read-only and
refreshes nothing.

Identity is SIDEBAR-NAME FIRST (user decision 2026-07-18): a row is keyed by
(folder root, cmux sidebar name `custom_title`) — several projects share one
folder, each with its own row, close, and launch target. Rows with no sidebar
name are FOLDER-LEVEL (non-cmux sessions fall back there). The book may render
two extra fact classes: `NAME DRIFT` (a row's saved sidebar name no longer
matches the live workspace — relay verbatim, never "fix" silently) and
`UNMATCHED WORKSPACES` (live cmux workspaces matching no row — candidates the
user may add via the `add` verb below).

## Hard rules (violating any one is a defect)

- The book is computed FRESH on every invocation: run `resurrect-view.py` again
  every time the menu is shown — never reuse a prior render, never cache a
  render to a file a later invocation reads. The `$SCRATCH` capture below is a
  same-turn relay buffer, nothing more.
- Show the rendered book VERBATIM — the whole `cat` output in one fenced block.
  NEVER re-compose, retype, reorder, trim, summarize, or decorate rows. BROKEN
  rows are always shown with their reason — never hidden, never dropped. No
  green badges, no checkmarks, no "verified" stamps: the renderer prints facts
  only (red/amber only) and you add NOTHING to them.
- Focus-never-launch is the LAUNCHER'S job. This skill NEVER calls
  `cmux workspace create` (nor `select` / `close`) directly — the only route to
  a workspace is `launch-project.sh`. SPINE 1 (focus, never a second workspace)
  lives there, not here.
- Registry mutations go through `registry_lib` ONLY — the transition blocks
  below. Never hand-edit a row file. NOTHING here deletes a row: `finish` and
  `tombstone` both HIDE the row in ARCHIVED; the row file stays on disk.
  Deletion is a human act performed by the human, outside this skill.
- `tombstone` is HUMAN-initiated only: the user must have named that row
  themselves in this conversation (directly, or as their per-row answer in
  curation mode). Never tombstone on your own initiative; never batch-tombstone.
- No nagger, no notifier, no reminder, no scheduled anything, and no auto-close
  at any token threshold. This skill acts only when invoked, only on what was
  picked.
- NEVER write the daemon state dir
  (`~/Library/Application Support/acos-token-monitor/state/`), NEVER touch
  `pending-resume-*.txt` / `RESCUED-resume-*.txt`, and NEVER modify or invoke
  `/acos-complete` (a separate skill, deliberately untouched — `finish` is a
  registry status transition, not a handoff archive).

## Step 0 — Preflight

Run from the root of the project hosting this session.

```bash
ROOT="$(pwd)"
# Script location: prefer this project's own copy; else fall back to the
# canonical ACOS 3.0 install (this skill is global — the scripts live once).
RESDIR="$ROOT/.claude/scripts/resurrection"
[ -f "$RESDIR/resurrect-view.py" ] || RESDIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
[ -f "$RESDIR/resurrect-view.py" ]  || { echo "STOP: resurrect-view.py not found at $RESDIR"; exit 1; }
[ -f "$RESDIR/launch-project.sh" ]  || { echo "STOP: launch-project.sh not found at $RESDIR"; exit 1; }
[ -f "$RESDIR/registry_lib.py" ]    || { echo "STOP: registry_lib.py not found at $RESDIR"; exit 1; }
echo "resurrection scripts: present (RESDIR=$RESDIR)"
```

`SCRATCH` = the session scratchpad directory named in your system prompt
(fallback: `mktemp -d`). Each fenced block runs in its own shell — re-derive
`ROOT`/`RESDIR`/`SCRATCH` at the top of every block you run, ALWAYS carrying the
same `|| RESDIR=<canonical ACOS 3.0 path>` fallback shown in Step 0 (this skill
is global; the scripts live in ACOS 3.0 only). `ROOT` is always `$(pwd)`.

## Step 1 — Render the book (fresh, verbatim)

```bash
ROOT="$(pwd)"; RESDIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RESDIR/resurrect-view.py" ] || RESDIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
python3 "$RESDIR/resurrect-view.py" --color never > "$SCRATCH/book.txt" 2>&1; RC=$?
python3 "$RESDIR/resurrect-view.py" --json      > "$SCRATCH/book.json" 2>/dev/null
cat "$SCRATCH/book.txt"; echo "exit=$RC"
```

Present the `cat` output whole and unmodified inside one fenced block — that IS
the menu. `book.json` is for YOUR machine reading of `project_uuid`/`root`/
`next_action`/`tier` in the steps below (same facts, a second fresh
computation); it is never shown as the book and never reused in a later
invocation. `exit != 0` → relay the output verbatim and STOP.

## Step 2 — The pick

Non-ARCHIVED projects (tiers OPEN NOW / RECENT / COLD / NO HANDOFF) are the
pickable set. ARCHIVED rows stay visible in the book but are not offered as
options; the user may still name one explicitly by free text (the launcher
accepts a `completed` row — that is the loop — and REFUSES a `tombstoned` one;
relay its refusal).

- **<= 4 pickable projects:** AskUserQuestion with ONE option per project.
  Option label = the project name. Option description must be SELF-CONTAINED:
  tier, age, dirty count, and the row's `next_action` verbatim — the user
  decides from the description alone. Mention in the question text that the
  loop verbs `finish <project>`, `tombstone <project>`, and `curate` are also
  accepted as a typed reply.
- **> 4 pickable projects:** ask for a free-text pick — by name, or by number
  counting top-to-bottom through the book as printed (1-based). The verbs
  `finish <project>`, `tombstone <project>`, and `curate` are accepted here too.

When the book's `UNMATCHED WORKSPACES` section is non-empty, say so in the
question text and offer `add <workspace name>` as an accepted reply — that is
the user's door for adding a live-but-unregistered workspace to the book (the
`add` verb in Step 5). Never add one on your own initiative.

Resolve the pick against `book.json` by casefolded name match. Ambiguous →
list the exact candidates and ask again. NEVER guess between two plausible rows.

## Step 3 — Same-root pick (the user is already in that project)

If `realpath` of the picked row's `root` equals `realpath` of this session's
cwd, do NOT launch anything — the reentry is read inline and work continues in
THIS conversation.

```bash
ROOT="$(pwd)"
find "$ROOT/memory/handoffs/closed" -name '*.reentry.md' -exec stat -f '%m %N' {} + 2>/dev/null | sort -n | tail -1
```

Newest `.reentry.md` by mtime, resolved NOW — the row's recorded `reentry_path`
is only a loud fallback when the scan finds nothing. Read that file with the
Read tool, tell the user you are continuing from it, and pick up its next step.

If the row's status is `parked`, flip it active (the resume flip — refreshes
`last_verified_at` too):

```bash
ROOT="$(pwd)"
RES_DIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RES_DIR/registry_lib.py" ] || RES_DIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
RES_UUID="<project_uuid from book.json>" RES_DIR="$RES_DIR" python3 - <<'PY'
import os, sys
sys.path.insert(0, os.environ["RES_DIR"])
import registry_lib
home = os.environ.get("ACOS_REGISTRY_HOME") or None
u = os.environ["RES_UUID"]
row = registry_lib.load_row(u, home)
assert row is not None, "REFUSED: no registry row for %s" % u
assert row["status"] != "tombstoned", "REFUSED: tombstoned row — un-tombstoning is a human act"
if row["status"] == "parked":
    registry_lib.upsert_row({"project_uuid": u, "root": row["root"], "status": "active"}, home)
    registry_lib.audit_append({"event": "resume", "project_uuid": u, "mode": "same-root"}, home)
print("status read-back:", registry_lib.load_row(u, home)["status"])
PY
```

## Step 4 — Different-root pick → the launcher (relay verbatim)

```bash
ROOT="$(pwd)"; RESDIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RESDIR/launch-project.sh" ] || RESDIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
bash "$RESDIR/launch-project.sh" --project "<project_uuid>" > "$SCRATCH/launch-out.txt" 2>&1; RC=$?
cat "$SCRATCH/launch-out.txt"; echo "exit=$RC"
```

Relay the `cat` output whole and unmodified inside one fenced block. The
launcher owns focus-or-launch (SPINE 1), delivery verification, the
parked->active flip, the durable `[key:<uuid>]` tag, and the launch audit
event — repeat none of it here.

- `REFUSED — ...` anywhere → that line is the outcome; STOP, no workaround.
- exit 3 / `DELIVERY NOT-VERIFIED` / `TRUST GATE DETECTED` → quote it loudly;
  never claim delivery the script did not verify.
- exit 0 → the focused/created workspace is where the user continues; this
  conversation's job for that pick is done.

## Step 5 — Loop verbs

### finish <project>

Meaning: this project is DONE. Sets `status: completed` via `registry_lib` — on
the next render the row sits under ARCHIVED (hidden from the active tiers),
and the row file is NEVER deleted. `/acos-complete` (handoff archiving) is a
different skill and is not invoked. Resolve name → uuid via `book.json`
(ambiguous → ask), then:

```bash
ROOT="$(pwd)"
RES_DIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RES_DIR/registry_lib.py" ] || RES_DIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
RES_UUID="<project_uuid>" RES_DIR="$RES_DIR" python3 - <<'PY'
import os, sys
sys.path.insert(0, os.environ["RES_DIR"])
import registry_lib
home = os.environ.get("ACOS_REGISTRY_HOME") or None
u = os.environ["RES_UUID"]
row = registry_lib.load_row(u, home)
assert row is not None, "REFUSED: no registry row for %s" % u
assert row["status"] != "tombstoned", "REFUSED: tombstoned row — un-tombstoning is a human act"
if row["status"] != "completed":
    registry_lib.upsert_row({"project_uuid": u, "root": row["root"], "status": "completed"}, home)
    registry_lib.audit_append({"event": "finish", "project_uuid": u}, home)
print("status read-back:", registry_lib.load_row(u, home)["status"])
PY
```

Confirm to the user with the block's printed read-back line only — no badge, no
stamp. A `finish`ed project remains resurrectable: picking it later relaunches
it and the launcher flips it back to `active`.

### tombstone <project> (HUMAN-initiated ONLY)

Only when the user themselves named this row. Tombstone hides the row in
ARCHIVED and makes the launcher refuse it; the file is never deleted and
un-tombstoning is a human act outside this skill.

```bash
ROOT="$(pwd)"
RES_DIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RES_DIR/registry_lib.py" ] || RES_DIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
RES_UUID="<project_uuid>" RES_DIR="$RES_DIR" python3 - <<'PY'
import os, sys
sys.path.insert(0, os.environ["RES_DIR"])
import registry_lib
home = os.environ.get("ACOS_REGISTRY_HOME") or None
u = os.environ["RES_UUID"]
row = registry_lib.tombstone_row(u, home)  # appends its own audit event; idempotent; NEVER unlinks
print("status read-back:", row["status"], "tombstoned_at:", row["tombstoned_at"])
PY
```

### add <workspace> (HUMAN-initiated, from UNMATCHED WORKSPACES only)

Only for a workspace the FRESH book lists under `UNMATCHED WORKSPACES`, and
only when the user asked for it by name. Mints a new row keyed by the
workspace's cwd + sidebar name, via `registry_lib` only. Take `<cwd>` and
`<custom_title>` verbatim from `book.json`'s `unmatched_workspaces`.

```bash
ROOT="$(pwd)"
RES_DIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RES_DIR/registry_lib.py" ] || RES_DIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
RES_WSROOT="<cwd from book.json>" RES_WSNAME="<custom_title from book.json>" \
RES_DIR="$RES_DIR" python3 - <<'PY'
import os, sys, uuid
sys.path.insert(0, os.environ["RES_DIR"])
import registry_lib
home = os.environ.get("ACOS_REGISTRY_HOME") or None
root = os.environ["RES_WSROOT"]
name = os.environ["RES_WSNAME"]
existing = registry_lib.find_row(root, name, home)
assert existing is None, "REFUSED: a row already exists for (%s, %r): %s %s" % (
    root, name, existing["project_uuid"], existing["status"])
u = str(uuid.uuid4())
registry_lib.upsert_row({"project_uuid": u, "root": root,
                         "workspace_name": name, "status": "active"}, home)
registry_lib.audit_append({"event": "enroll-from-book", "project_uuid": u,
                           "root": root, "workspace_name": name}, home)
row = registry_lib.load_row(u, home)
print("status read-back:", row["status"], row["project_uuid"], repr(row["workspace_name"]))
PY
```

After the add, re-render the book (Step 1) so the user sees the new row fresh.

### curate

When the user says "curate": walk the seed curation list ONE row at a time.

1. Locate the report (an ACOS 3.0 seed artifact — check this project first,
   then the canonical ACOS 3.0 install):
   `CR="$(ls -t "$ROOT"/.acos/evidence/*/SLICE-RES-13-seed/CURATION-REPORT.md "/Users/zee/Documents/Vibe Coding/ACOS 3.0"/.acos/evidence/*/SLICE-RES-13-seed/CURATION-REPORT.md 2>/dev/null | head -1)"` —
   if empty, say so and stop (nothing to curate).
2. Cross-check every listed row against the FRESH `book.json`: rows already
   ARCHIVED (tombstoned/completed) or no longer present are skipped — say which.
3. For each remaining row, one at a time: present name + root + status + tier +
   age (facts from the book, verbatim values) and ask keep / tombstone / stop
   walking (AskUserQuestion, self-contained description). Tombstone ONLY on
   that row's explicit "tombstone" answer — that answer is the human
   initiation — using the tombstone block above.
4. After the walk, re-render the book (Step 1) so the user sees the result
   fresh.

## Relay discipline

Every script output reaches the user as unmodified `cat` output. Status
confirmations are the transition block's own printed read-back line. The book
is the renderer's output, whole. You add routing words around the blocks —
never inside them.

---

*ACOS Resurrect — the book is the truth; the scripts decide; the skill relays.*
