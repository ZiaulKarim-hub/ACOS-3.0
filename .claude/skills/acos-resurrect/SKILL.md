---
name: acos-resurrect
description: The Resurrection Protocol menu — renders the registry book FRESH via resurrect-view.py and shows it VERBATIM, then routes the user's pick through open-picks.sh: a pick may be a LIST ("2, 5, 7, 9" opens all four), every pick opens its OWN window in that project's own folder running claude --dangerously-skip-permissions, and re-opening a row that is already open gives it another window instead of a question. adopt <n> is the opt-in verb for making THIS tab the project. Also runs the loop verbs: finish (status completed — hidden in ARCHIVED, never deleted), tombstone (human-initiated only), curate (walk the seed CURATION-REPORT one row at a time). Trigger phrases: "resurrect", "resurrection protocol", "show my projects", "project menu", "which projects", "/acos-resurrect".
disable-model-invocation: false
user-invocable: true
---

# ACOS Resurrect — the menu over the book (Resurrection Protocol proper)

Resurrect = see every project honestly, pick one or several, and land each in a
window of its own, in its own folder, already working. ALL computation lives in
the scripts: `.claude/scripts/resurrection/resurrect-view.py` (the book —
computed fresh, read-only, BROKEN rows shown),
`.claude/scripts/resurrection/open-picks.sh` (the pick LIST — resolves every
token against a fresh book, all-or-nothing, then opens each row),
`.claude/scripts/resurrection/launch-project.sh` (one window: create in
`--cwd <root>`, launch `claude --dangerously-skip-permissions`, verify delivery),
and `.claude/scripts/resurrection/adopt-project.sh` (ADOPT-IN-PLACE — now the
opt-in `adopt <n>` verb, not the default route). Status transitions go through
`.claude/scripts/resurrection/registry_lib.py` ONLY. This skill routes and
relays; it computes nothing and decorates nothing.

**Why a pick opens its own window** (Zee's Rules 1-4, 2026-08-19). A cmux
workspace's FOLDER cannot be changed after the workspace is created (`--cwd`
exists only on `workspace create`; there is no re-point verb), and a Claude
session's cwd is fixed at launch. Adoption can only re-bind IDENTITY — sidebar
name, the durable `[key:<uuid>]` tag, the registry row — never the tab's shell
folder. So a pick creates a window in the right folder instead of re-labelling
one in the wrong folder:

- **Rule 1** — a pick may be a LIST: `2, 5, 7, 9` opens all four.
- **Rule 2** (2026-08-18) — every pick lands in the project's OWN folder.
- **Rule 3** — re-opening a row that is already open gives it ANOTHER window on
  the same project. Never a question, never a jump. `--focus-existing` is how
  the user asks to jump instead.
- **Rule 4** — every opened window runs `claude --dangerously-skip-permissions`.
  Delivery is still PROVEN: the shell prints the reentry note between BEGIN/END
  markers before exec'ing claude, and read-screen looks for the marker
  (MEASURED 2026-08-19 — Claude Code renders inline, so the markers survive).

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

On EVERY pick the window is named for the project (user request 2026-07-20), so
the sidebar name always matches the row you landed in. Since Rule 3 makes several
windows on one project normal, the name is the project name PLUS a distinguisher:
`--label <text>` gives `<project> <text>`, and with no label the second and later
windows are AUTO-NUMBERED (`To Do Tree 2`) and the script says the number was
auto-assigned (D12). `launch-project.sh` names the window it creates and leaves a
focused window's existing name alone when that name already starts with the
project's; `adopt-project.sh` renames THIS tab under the `adopt <n>` verb. All are
fail-open — a rename miss is cosmetic, never a gate. The rename is identity-safe
because every named row already stores `workspace_name == name`, and because the
`[key:<uuid>]` tag is written alongside it — the tag is what keeps a window bound
to its real row when names repeat.
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
  directly — the only routes are `open-picks.sh` (every pick, one or many),
  `launch-project.sh` (the single-window primitive it calls), and
  `adopt-project.sh` (only for the opt-in `adopt <n>` verb).
- **A pick lands in the project's OWN folder, in its own window** (Rules 1-4,
  2026-08-19; Rule 2 dates from 2026-08-18). Earlier rules made adoption the
  default route, which left projects running from the wrong folder permanently —
  how tab workspace:20 came to run FruitSync from `ACOS 3.0`, and how the
  Research to Portfolio session minted a row called `FruitSync (duplicate)`
  rooted at ACOS 3.0 on 2026-08-18. `adopt-project.sh` still exits 5 with
  `CROSS-ROOT` rather than adopting across roots; the escape hatch
  `--allow-cross-root` exists and is never the default. The user is always told
  which sidebar name to look at, so nobody is stranded.
- **All-or-nothing on a list.** `open-picks.sh` resolves every token against a
  FRESH book before it opens anything. One unknown number or ambiguous name and
  NOTHING opens. Never open the resolvable subset — half a list is worse than a
  refusal, because the user then has to work out which windows exist.
- **Never claim a delivery the script did not verify.** exit 3 means the marker
  was not seen; quote the line. A `TRUST GATE DETECTED` line means claude is
  sitting on the folder-trust prompt and has NOT received the reentry.
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

## Step 2 — The pick (ONE row, or a LIST)

Non-ARCHIVED projects (tiers OPEN NOW / RECENT / COLD / NO HANDOFF) are the
pickable set. ARCHIVED rows stay visible in the book but are not offered as
options; the user may still name one explicitly by free text (a `completed` row
opens — that is the loop — and a `tombstoned` one is REFUSED; relay the refusal).

**A pick may be a LIST** (Zee's Rule 1, 2026-08-19). `2, 5, 7, 9` means open all
four. Say so when you ask. Repeats are legal and meaningful: `5, 5` opens two
windows on row 5 (Rule 3).

- **<= 4 pickable projects:** AskUserQuestion with ONE option per project.
  Option label = the project name. Option description must be SELF-CONTAINED:
  tier, age, dirty count, and the row's `next_action` verbatim. Say in the
  question text that a typed list (`2, 5`) and the loop verbs
  `finish <project>`, `tombstone <project>`, `strike <line>`, `merge`, `curate`,
  and `adopt <n>` are also accepted as a free-text reply.
- **> 4 pickable projects:** ask for a free-text pick — one number, several
  numbers, or a name. The renderer prints the pick number in the left gutter and
  carries the same integer as `pick_number` in `book.json`; ARCHIVED rows have no
  number. The same verbs are accepted here.

Numbers are per-render. The book is recomputed every invocation and rows move
between tiers, so a number from an EARLIER render is not the same row now. Never
resolve a pick against a stale render — `open-picks.sh` re-renders the book
itself for exactly this reason, and prints each resolved name and root before it
opens anything.

When the book's `UNMATCHED WORKSPACES` section is non-empty, say so and offer
`add <workspace name>` (Step 5). Never add one on your own initiative.

## Step 3 — Open the pick (the ONLY route)

Every pick — one or many — goes through `open-picks.sh`. It resolves the whole
list against a FRESH book first and opens NOTHING if any token is unresolvable,
then runs `launch-project.sh` once per row. Each row lands in a NEW window, in
that project's own folder, running `claude --dangerously-skip-permissions`.

```bash
ROOT="$(pwd)"; RESDIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RESDIR/open-picks.sh" ] || RESDIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
bash "$RESDIR/open-picks.sh" --picks "<the user's picks verbatim>" > "$SCRATCH/open-out.txt" 2>&1; RC=$?
cat "$SCRATCH/open-out.txt"; echo "exit=$RC"
```

Relay the `cat` output whole and unmodified inside one fenced block. The scripts
own every decision and every write: list resolution, the all-or-nothing refusal,
window creation with `--cwd <root>`, the claude launch, the delivery marker
check, the sidebar name, the `parked/completed -> active` flip, the durable
`[key:<uuid>]` tag, and the audit event. Repeat none of it, and never perform
any step the script declined to.

Read the exit code, then act:

- **exit 0** → every pick opened and every delivery was verified. Tell the user
  which sidebar names to look at, by name. Those windows are where the work
  continues; this conversation's job for those picks is done.
- **exit 3** → at least one row opened but its delivery was NOT verified. Quote
  the `DELIVERY NOT-VERIFIED` line and the `TRUST GATE DETECTED` line if present.
  Never claim a delivery the script did not verify.
- **exit 2 / `REFUSED — ...`** → nothing opened at all. Relay it verbatim, ask
  for a corrected list, and STOP. Do not open the resolvable subset "to save a
  step" — all-or-nothing is the contract.

Three flags exist, and NONE of them is ever your own initiative:

- `--focus-existing` — jump to a window already open on that project instead of
  making another. Use ONLY when the user asks to go to the existing one.
- `--label <text>` — name the new window `<project> <text>` (D12). Offer it when
  a second window on one project is being opened for a distinct piece of work;
  without it the script auto-numbers and says so.
- `--dry-run` — resolve and print the decisions, open nothing. Use it when the
  user wants to see what a list would do before it does it.

## Step 4 — `adopt <n>` (opt-in only, when THIS tab should become the project)

Rule 3 made a new window the default, so adoption is now something the user asks
for by name: `adopt 7` means "make THIS tab project 7". It still cannot cross
roots — a tab's folder is fixed at creation — so it works only when the picked
row's root IS this tab's folder.

```bash
ROOT="$(pwd)"; RESDIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RESDIR/adopt-project.sh" ] || RESDIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
bash "$RESDIR/adopt-project.sh" --project "<project_uuid>" > "$SCRATCH/adopt-out.txt" 2>&1; RC=$?
cat "$SCRATCH/adopt-out.txt"; echo "exit=$RC"
```

Relay the `cat` output whole and unmodified inside one fenced block. The script
owns every gate and every write: the outgoing-close check, the outgoing
`active -> parked` release, the sidebar rename, the `[key:<uuid>]` tag
round-trip, the picked row's status flip, the reentry resolution, and the audit
event.

The receipt carries four blocks that are part of the pick — read them, do not
summarise them away: **`owned reentry notes`** (every UNREAD note owned by THIS
project — read every one, and a line saying `HEURISTIC` was matched by name, not
proof), **`knowledge:`** (the index plus "learned since you were last here" —
offer the `strike` verb), **`STALE`** (stored facts that no longer match the
disk — nothing is auto-corrected; ask before rewriting any), and **`OTHER
WINDOWS ON THIS PROJECT`** (what other live windows are doing).

- **exit 0** → this tab IS the picked project now. Read the printed `reentry:`
  path with the Read tool, say you are continuing from it, and pick up its next
  step IN THIS CONVERSATION.
- **exit 3 / `OUTGOING NOT-CLOSED`** → STOP. The project currently in this tab
  has no close record, and adopting would release it with unsaved reentry state.
  Relay the line, then offer exactly two options: run `/acos-safe-close` on that
  project first, or pick that project instead. Never override the gate.
- **exit 4 / `ALREADY OPEN`** → the row is live in another workspace. Under
  Rule 3 the answer is a new window, so route it through Step 3 instead.
- **exit 5 / `CROSS-ROOT`** → the row's root is not this tab's folder. Relay the
  block and route it through Step 3, which opens it in its own folder. Do NOT
  re-run with `--allow-cross-root` unless the user asked for adopt-in-place in
  this conversation.
- **`REFUSED — ...` (exit 1/2)** → that line is the outcome; STOP, no workaround.
  A `SET-BUT-DEAD` refusal means cmux restarted under this session: the tab this
  process thinks it is in no longer exists.

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

### strike <the line he objects to>

D5d, the review-AFTER rule: Zee is an EDITOR of the knowledge store, not a
gatekeeper of it. When he objects to a line in the `learned since you were last
here` digest, strike it. A strike is an edge, never a delete — the row stays on
disk and the strike is auditable, so a wrong strike is undoable.

```bash
ROOT="$(pwd)"; RES_DIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RES_DIR/knowledge_lib.py" ] || RES_DIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
RES_DIR="$RES_DIR" RES_UUID="<project_uuid>" RES_FACT="<fact id from the digest>" python3 - <<'PY'
import os, sys
sys.path.insert(0, os.environ["RES_DIR"])
import knowledge_lib
u, f = os.environ["RES_UUID"], os.environ["RES_FACT"]
home = os.environ.get("ACOS_REGISTRY_HOME") or None
knowledge_lib.strike_fact(u, f, reason="struck by Zee on resurrect", home=home)
print("struck:", f, "— still on disk:",
      any(x["id"] == f for x in knowledge_lib.load_facts(u, home)),
      "— now hidden:", f not in {x["id"] for x in knowledge_lib.live_facts(u, home)})
PY
```

Strike ONLY the line he named. Never strike on your own initiative, and never
batch-strike — the store's value is that it accumulates.

### merge <window> into <window>

MW-D. Two windows of one project that converged onto the same work. Folds the
source window's thread into the target and releases the source's claim. Knowledge
is NOT touched: both windows already write into the same per-project store with
their label as provenance (D13), so there is nothing to move.

```bash
ROOT="$(pwd)"; RES_DIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RES_DIR/windows_lib.py" ] || RES_DIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
python3 "$RES_DIR/windows_lib.py" --project "<project_uuid>" \
  --workspace "<target workspace id>" --merge-from "<source workspace id>"
```

`REFUSED` means one of them never claimed the project — relay it and stop.

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

### conflicts (Zee's Rule 3 — the system tells you, and names the fix)

Run the scanner whenever a pick behaves oddly, and after any adopt that printed
a warning. It is READ-ONLY and repairs nothing:

```bash
ROOT="$(pwd)"; RES_DIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RES_DIR/conflict-scan.py" ] || RES_DIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
python3 "$RES_DIR/conflict-scan.py"
```

It names five classes and the fix for each: `BLEED` (two projects claiming one
cmux surface), `NAME-CLASH` (two live rows with one name), `ROOT-GONE`,
`ROOT-UNREACHABLE` (a tab bound to a row it can never sit in), and
`SESSION-SHARED` (one session recorded as the hint of two rows). Several windows
on ONE project is NOT a conflict and the scanner stays silent about it.

Relay its output verbatim. Never act on a finding without the user's ruling —
each fix line is addressed to them, not to you.

## Relay discipline

Every script output reaches the user as unmodified `cat` output. Status
confirmations are the transition block's own printed read-back line. The book
is the renderer's output, whole. You add routing words around the blocks —
never inside them.

---

*ACOS Resurrect — the book is the truth; the scripts decide; the skill relays.*
