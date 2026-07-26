---
name: acos-resurrect
description: The Resurrection Protocol menu — renders the registry book FRESH via resurrect-view.py and shows it VERBATIM, routes the user's pick (project already open elsewhere → launch-project.sh FOCUS; otherwise adopt-project.sh ADOPTS the pick into the CURRENT tab and the reentry is read inline — a pick never strands the user in another tab), and runs the loop verbs: finish (status completed — hidden in ARCHIVED, never deleted), tombstone (human-initiated only), curate (walk the seed CURATION-REPORT one row at a time). Trigger phrases: "resurrect", "resurrection protocol", "show my projects", "project menu", "which projects", "/acos-resurrect".
disable-model-invocation: false
user-invocable: true
---

# ACOS Resurrect — the menu over the book (Resurrection Protocol proper)

Resurrect = see every project honestly, pick one, land in it with its reentry in
front of you — **in the tab you typed the command in**. ALL computation lives in
the scripts: `.claude/scripts/resurrection/resurrect-view.py` (the book —
computed fresh, read-only, BROKEN rows shown),
`.claude/scripts/resurrection/adopt-project.sh` (ADOPT-IN-PLACE, SPINE 2 — the
default route: this tab BECOMES the picked project), and
`.claude/scripts/resurrection/launch-project.sh` (focus-or-launch, SPINE 1 —
used only to JUMP to a project that is already open in another tab). Status
transitions go through `.claude/scripts/resurrection/registry_lib.py` ONLY. This
skill routes and relays; it computes nothing and decorates nothing.

**Adopt-in-place, and its one physical limit** (user decision 2026-07-26): a
pick must land HERE, not in some other tab the user then has to hunt for. But a
cmux workspace's FOLDER cannot be changed after the workspace is created
(`--cwd` exists only on `workspace create`; there is no re-point verb), and a
Claude session's cwd is fixed at launch. So adoption re-binds IDENTITY — sidebar
name, the durable `[key:<uuid>]` tag, and the registry row — never the tab's
shell folder. When the picked root differs from the tab's folder,
`adopt-project.sh` prints a `FOLDER CAVEAT` naming the root every file operation
must use; relay it verbatim and then USE absolute paths under that root. Never
paper over it, and never claim the directory changed.

This skill is GLOBAL (installed in `~/.claude/skills/`), but the scripts live
ONCE — in the ACOS 3.0 install. Every block resolves `RESDIR` to this project's
own `.claude/scripts/resurrection` when present, else falls back to the
canonical path `/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection`
(the same absolute path the SessionStart enroll hook uses). The registry itself
is already global (`~/.acos/registry.d/`), so the book is identical from any
project. `ROOT` always stays `$(pwd)` — the project you are operating in.

Loop economics (what the verbs mean): **resume flips parked->active** — both
`adopt-project.sh` and `launch-project.sh` do that flip themselves on every
adopt/focus; every `registry_lib` upsert refreshes `last_verified_at`.
**adopt also RELEASES the outgoing project** — the row this tab previously held
goes `active -> parked`, which is what stops a released project from sitting in
the book pretending to be open (and undoes `enroll-project.sh`'s revive-on-work,
which re-actives any row the moment a session starts in its folder).
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

On EVERY pick the tab is auto-renamed to the picked project's name (user
request 2026-07-20), so the sidebar name always matches the row you landed in:
`adopt-project.sh` renames THIS tab (Step 4) and `launch-project.sh` renames the
tab it focuses (Step 3, in its `finalize()`). Both are fail-open — a rename miss
is cosmetic, never a gate. The rename is identity-safe because every named row
already stores `workspace_name == name`, and because adoption writes the
`[key:<uuid>]` tag alongside it — the tag is what keeps an adopted tab bound to
its real row when the tab's folder is not the project's root.
`rename-workspace.sh` still exists for a bare cosmetic rename, but a PICK never
uses it alone: a rename without the tag would leave the tab claiming a project
it is not bound to.

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
- Workspace actions belong to the SCRIPTS. This skill NEVER calls
  `cmux workspace create` / `select` / `close` / `rename` / `set-description`
  directly — the only routes are `adopt-project.sh` (re-bind THIS tab) and
  `launch-project.sh` (focus a tab that is already open). SPINE 1 (one project,
  one tab — focus, never a second workspace) and SPINE 2 (a pick lands in the
  tab it was typed in) live in those scripts, not here.
- **Adoption never CREATES a tab.** The old different-root behaviour — spawn a
  new workspace and leave the user behind in the tab they typed in — is a defect
  (2026-07-26). `launch-project.sh` is now called ONLY when the book shows the
  picked project already live in another workspace; its create path is not a
  route this skill takes.
- **The outgoing project is checked before it is released.** `adopt-project.sh`
  exits 3 with `OUTGOING NOT-CLOSED` when the tab's current project has no
  `last_close` record. Relay that verbatim and STOP — offer `/acos-safe-close`
  or picking that project instead. Never work around it; an unclosed project
  loses its reentry state when its tab is taken.
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
[ -f "$RESDIR/adopt-project.sh" ]   || { echo "STOP: adopt-project.sh not found at $RESDIR"; exit 1; }
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
- **> 4 pickable projects:** ask for a free-text pick — by name, or by the
  printed NUMBER next to the row. The renderer prints an explicit pick number
  (the left gutter) on every pickable row and carries the same integer as
  `pick_number` in `book.json`; ARCHIVED rows have no number. The verbs
  `finish <project>`, `tombstone <project>`, and `curate` are accepted here too.

When the book's `UNMATCHED WORKSPACES` section is non-empty, say so in the
question text and offer `add <workspace name>` as an accepted reply — that is
the user's door for adding a live-but-unregistered workspace to the book (the
`add` verb in Step 5). Never add one on your own initiative.

Resolve the pick against `book.json`: a NUMERIC reply → the project whose
`pick_number` equals it EXACTLY (never re-count the printed rows yourself — the
renderer already assigned the number the user sees). A NAME reply → casefolded
name match. Ambiguous → list the exact candidates and ask again. NEVER guess
between two plausible rows.

## Step 3 — Already open elsewhere? Jump to that tab (relay verbatim)

The ONLY thing that routes a pick away from this tab is the pick already being
live somewhere else. Read the picked row's `live.workspaces` from `book.json`
(the fresh render from Step 1). If it is non-empty AND none of those workspace
ids equals `$CMUX_WORKSPACE_ID`, the project is open in another tab — focus it
and stop:

```bash
ROOT="$(pwd)"; RESDIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RESDIR/launch-project.sh" ] || RESDIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
bash "$RESDIR/launch-project.sh" --project "<project_uuid>" > "$SCRATCH/launch-out.txt" 2>&1; RC=$?
cat "$SCRATCH/launch-out.txt"; echo "exit=$RC"
```

Relay the `cat` output whole and unmodified inside one fenced block. The
launcher owns focus (SPINE 1), the parked->active flip, the durable
`[key:<uuid>]` tag, the tab rename, and the audit event — repeat none of it here.

- `REFUSED — ...` anywhere → that line is the outcome; STOP, no workaround.
- exit 3 / `DELIVERY NOT-VERIFIED` / `TRUST GATE DETECTED` → quote it loudly;
  never claim delivery the script did not verify.
- exit 0 → the focused workspace is where the user continues; this
  conversation's job for that pick is done. Tell them WHICH tab to look at, by
  its sidebar name.

If `live.workspaces` is empty — or its only entry IS this tab — do NOT run the
launcher. Go to Step 4. Running it here would create a second workspace and
strand the user, which is the defect this routing exists to prevent.

## Step 4 — Adopt the pick into THIS tab (the default route)

```bash
ROOT="$(pwd)"; RESDIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RESDIR/adopt-project.sh" ] || RESDIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
bash "$RESDIR/adopt-project.sh" --project "<project_uuid>" > "$SCRATCH/adopt-out.txt" 2>&1; RC=$?
cat "$SCRATCH/adopt-out.txt"; echo "exit=$RC"
```

Relay the `cat` output whole and unmodified inside one fenced block. The script
owns every gate and every write: the already-open refusal, the outgoing-close
check, the outgoing `active -> parked` release, the sidebar rename, the
`[key:<uuid>]` tag round-trip, the picked row's `parked/completed -> active`
flip, the reentry resolution, and the audit event. Repeat none of it, and
NEVER perform any of those steps yourself if the script declined to.

Read the exit code, then act:

- **exit 0** → adoption done. This tab IS the picked project now. Read the
  `reentry:` path the script printed, using the Read tool, tell the user you are
  continuing from it, and pick up its next step IN THIS CONVERSATION.
  If the script printed a `FOLDER CAVEAT`, relay it and treat the printed
  `working root:` as the project's root for every file operation from here on —
  absolute paths only. Do not claim the working directory changed; it did not.
- **exit 3 / `OUTGOING NOT-CLOSED`** → STOP. The project currently in this tab
  has no close record and adopting would release it with unsaved reentry state.
  Relay the line, then offer exactly two options: run `/acos-safe-close` on that
  project first, or pick that project instead. Never override the gate.
- **exit 4 / already open** → the picked project is live in another workspace.
  Relay the refusal, then run Step 3's launcher block to focus that tab.
- **`REFUSED — ...` (exit 1/2)** → that line is the outcome; STOP, no workaround.
  A `SET-BUT-DEAD` refusal means cmux restarted under this session: the tab this
  process thinks it is in no longer exists, and nothing can be adopted into it.

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
stamp. A `finish`ed project remains resurrectable: picking it later adopts it
into the current tab (or focuses its tab if one is open) and that script flips
it back to `active`.

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
