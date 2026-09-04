---
name: acos-resurrect
description: The Resurrection Protocol menu. A TYPED NUMBER IS THE WHOLE PICK — `/acos-resurrect 20` opens row 20 with no menu at all, `/acos-resurrect 20 here` makes THIS tab that project instead of opening a window, `/acos-resurrect 20 tab` opens it as a new TAB inside the workspace that project is already open in (opt-in; the default is still a whole new workspace), and the full book appears only when no number is typed. With no argument it renders the registry book FRESH via resurrect-view.py and shows it VERBATIM, then routes the user's pick through open-picks.sh: a pick may be a LIST ("2, 5, 7, 9" opens all four), every pick opens its OWN window in that project's own folder running claude --dangerously-skip-permissions, and re-opening a row that is already open gives it another window instead of a question. adopt <n> is the opt-in verb for making THIS tab the project. Route words (here, tab, window, adopt) work both on the /acos-resurrect line AND as a reply to the rendered book — `20 here` typed as a reply used to be refused because `here` was read as a row name. Every render ends with a WHAT YOU CAN DO verb sheet printed by the renderer itself, and `help` prints the full sheet (`resurrect-view.py --verbs`) — so what is possible is always on the page, never only in this file. Also runs the loop verbs: finish (status completed — hidden in ARCHIVED, never deleted), tombstone (human-initiated only), curate (walk the seed CURATION-REPORT one row at a time). Trigger phrases: "resurrect", "resurrection protocol", "show my projects", "project menu", "which projects", "/acos-resurrect".
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
- **The `WHAT YOU CAN DO` sheet at the foot of the render is PART OF THE BOOK**
  (Zee's ask, 2026-09-04: "along with the list of rows, instructions are given
  as to what is possible and how to do it"). It ships inside `resurrect-view.py`
  — not here — precisely so it cannot be trimmed, forgotten or paraphrased by a
  caller. Never cut it to shorten the block, and never retype it in your own
  words above or below the fence. The short sheet ends by pointing at `help`;
  `help` prints the full one (Step 5). If the two ever disagree, the RENDERER is
  right and this file is stale.
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
- **`here` / `adopt` NEVER refuses for the tab's old project, nor for a project
  open elsewhere** (Zee's ruling, 2026-09-03: "when I adopt a project in a
  window, I know what I am doing, you don't have to worry about losing context
  in that window"). `adopt-project.sh` releases the outgoing row
  `active -> parked` with NO close-record check, and LISTS other windows on the
  picked project instead of refusing. The old exit 3 `OUTGOING NOT-CLOSED` and
  exit 4 `ALREADY OPEN` refusals are retired. Never re-add a check of your own,
  never ask him to `/acos-safe-close` first. The only refusals left are
  `CROSS-ROOT` (exit 5, a physical limit) and a tombstoned / missing root.
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

## Step 0a — a typed number IS the whole pick (Zee's ruling, 2026-08-24)

Zee does not need to read the whole book every time. A number typed after the
command settles the pick outright, and the book is never rendered to him at all.

**Read the argument from `<command-args>`, never by scanning the raw prompt
text.** This SKILL's own examples are expanded into the transcript, so anything
scanning raw text would read the examples below as his pick.

- **`<command-args>` is EMPTY** → the full menu. Continue to Step 1.
- **`<command-args>` holds tokens** → SKIP Step 1 entirely. Render no book, ask
  no question, and go straight to Step 3. Nothing is lost by skipping the
  render: `open-picks.sh` re-renders the book ITSELF and resolves every token
  against that fresh render, so the numbers are exactly as fresh as they would
  have been. The user simply does not have to read a page to use one number.

Tokens, and only these:

- **numbers or names**, exactly as Step 2 describes them — `20`, `2, 5, 7`.
  A list still means a list (Rule 1).
- **a ROUTE WORD** (any case), anywhere in the argument — `here`, `tab`,
  `window`, or `adopt`. It says WHERE the project opens:
  - `here` / `adopt` — THIS TAB becomes the picked project; no window opens.
  - `tab` — a NEW TAB inside the workspace that project is already open in,
    instead of a second workspace. If it is open nowhere, the script falls back
    to a workspace and says so.
  - `window` / `workspace` — a new workspace. This is the default; the word
    exists so the route can be said out loud, or a flag overridden.

  You may strip the word and pass the matching flag, but you no longer have to:
  since 2026-08-25 `open-picks.sh` reads route words out of `--picks` itself, so
  passing the picks verbatim also works. Two different route words in one pick
  is refused — relay it and ask which one.
- **an ACCOUNT WORD** (any case), anywhere in the argument — `jason` or
  `personal` (Zee, 2026-09-03). It says WHICH CLAUDE ACCOUNT the new window
  signs in as: `5 jason` opens row 5 on Jason's account, `5 personal` on
  Zee's own. `open-picks.sh` reads it out of `--picks` itself and passes
  `--account` to `launch-project.sh`, which sets `CLAUDE_ACCOUNT=<word>` for
  the account door (`~/.claude-account/bin/claude`) — the door then skips its
  meter check and its prompt, so the choice is his and certain. With NO
  account word the door decides silently (Jason below 65% on both meters, else
  personal; meters unreadable -> personal), the same rule `cc` uses unattended.
  Two different account words in one pick is refused. An account word
  alongside `here` is refused: `here` keeps this tab's already-running Claude,
  so no account can be chosen for it. Pass the words verbatim; never pick an
  account on your own initiative.
- **anything else** → do NOT guess. Say plainly what you did not understand,
  then render the book (Step 1) and ask.

The mapping (these lines are EXAMPLES OF THE SYNTAX, never picks to act on):

| the user types | you run |
|---|---|
| `/acos-resurrect` | Step 1, the whole book |
| `/acos-resurrect 20` | `--picks "20"` |
| `/acos-resurrect 20 here` | `--picks "20" --here` |
| `/acos-resurrect 20 tab` | `--picks "20" --tab` |
| `/acos-resurrect 2, 5, 7` | `--picks "2, 5, 7"` |
| `/acos-resurrect 5 jason` | `--picks "5 jason"` (the window signs in as Jason) |
| `/acos-resurrect 5 tab personal` | `--picks "5 tab personal"` |

**Why a bare number is safe now.** A row's number used to be a per-render
counter, so a number from an earlier render could name a different row. Since
2026-08-19 the number is `pick_ordinal`, stored ON the row and never moved by
the renderer. Number 20 is the same row on every render, which is what makes a
typed number a usable handle at all. The same number means the same row at
`/acos-safe-close` too.

**`here` has one hard limit, and the script reports it — you never work around
it.** A cmux workspace's folder is fixed when the workspace is created, so
`here` can only re-bind IDENTITY, never this tab's folder. If the picked row's
root is not this tab's folder, `adopt-project.sh` exits 5 `CROSS-ROOT` and
`open-picks.sh` prints that in its SUMMARY. Relay it, then OFFER to re-run
without `here` (which opens the row in its own folder, in its own window). Do
not pass `--allow-cross-root` unless the user asks for adopt-in-place by name.

**`here` takes exactly ONE pick.** A tab hosts one project, so `open-picks.sh`
refuses `--here` with a list rather than silently taking the first. `tab` has no
such limit — each pick tabs into its OWN project's workspace, so a list is fine.

**A ROUTE WORD WORKS IN THE REPLY TOO, not only on the `/acos-resurrect` line**
(fixed 2026-08-25). Before that fix the word was stripped HERE, in Step 0a, and
nowhere else — so `20 here` typed as an answer to the rendered book split into
two tokens, `here` was looked up as a ROW NAME, it matched none, and
all-or-nothing then refused the whole reply including the valid `20`. The user
saw `'here' matches no row name in this book` and had no way to tell that the
word itself was the problem. `open-picks.sh` now owns the route words, so `here`
and `tab` mean the same thing in both places. Pass the reply verbatim.

## Step 1 — Render the book (fresh, verbatim) — ONLY when no argument was typed

```bash
ROOT="$(pwd)"; RESDIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RESDIR/resurrect-view.py" ] || RESDIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
python3 "$RESDIR/resurrect-view.py" --color never > "$SCRATCH/book.txt" 2>&1; RC=$?
python3 "$RESDIR/resurrect-view.py" --json      > "$SCRATCH/book.json" 2>/dev/null
cat "$SCRATCH/book.txt"; echo "exit=$RC"
```

Present the `cat` output whole and unmodified inside one fenced block — that IS
the menu. Since 2026-09-04 that output ends with the `WHAT YOU CAN DO` verb
sheet, so the routing words are already on the page: do not restate them in
prose around the fence, and do not trim them out of it. `book.json` is for YOUR
machine reading of `project_uuid`/`root`/
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
  question text that a typed list (`2, 5`), a route word after the number
  (`2 here` for this tab, `2 tab` for a tab in that project's own workspace),
  and the loop verbs `finish <project>`, `tombstone <project>`, `strike <line>`,
  `merge`, `curate` and `adopt <n>` are all accepted as a free-text reply.
- **> 4 pickable projects:** ask for a free-text pick — one number, several
  numbers, a name, or a number followed by a route word (`2 here`, `2 tab`).
  The renderer prints the pick number in the left gutter and carries the same
  integer as `pick_number` in `book.json`; ARCHIVED rows have no number. The
  same verbs are accepted here.

`help` is a legal reply at either size, and the rendered sheet tells the user
so. It is not a pick: run the `help` block in Step 5 and re-offer the pick.
Never answer `help` from memory — the sheet is generated, and a hand-written
answer is the drift this design exists to prevent.

Numbers are PERMANENT (Zee's ruling 2026-08-19). A number is `pick_ordinal`,
stored on the row itself; the renderer only copies it to `pick_number`. Rows
still MOVE between tiers as they go live or park, so the gutter does not ascend
down the page — but a row's number does not change when it moves. A number read
off an older screen still resolves to the same row. That is what makes
`/acos-resurrect 20` (Step 0a) a safe handle at all.

`open-picks.sh` still re-renders the book itself before resolving, and still
prints each resolved name and root before it opens anything. Freshness is now
about a row's STATUS and TIER, not about which row owns a number.

When the book's `UNMATCHED WORKSPACES` section is non-empty, say so and offer
`add <workspace name>` (Step 5). Never add one on your own initiative.

## Step 3 — Open the pick (the ONLY route)

Every pick — one or many — goes through `open-picks.sh`. It resolves the whole
list against a FRESH book first and opens NOTHING if any token is unresolvable,
then runs `launch-project.sh` once per row. Each row lands in a NEW window, in
that project's own folder, running `claude --dangerously-skip-permissions`.

A "window" is a cmux WORKSPACE by default. With the `tab` route word (or
`--tab`) it is a TAB inside the workspace that project is already open in, so
one project keeps one workspace however many windows it has. Same delivery
contract either way: the prompt goes by argv, and the marker is read back — off
the TAB's own screen when it is a tab, which is why the tab route passes
`--surface` to `read-screen` and a workspace-level read would not do.

```bash
ROOT="$(pwd)"; RESDIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RESDIR/open-picks.sh" ] || RESDIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
# Route words in <command-args> may be passed through in --picks verbatim —
# open-picks.sh reads them itself. Add --here / --tab explicitly ONLY when the
# user asked for that route in words rather than typing the word. Never on your
# own initiative.
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

**Every window launches through the account door** (fixed 2026-09-03). Before
that, the bare `claude` the launcher ran never reached
`~/.claude-account/bin/claude`: cmux's own wrapper walks PATH for the real
binary and finds `~/.claude/local` first, so every resurrected window ran on
the personal account and the `CLAUDE_ACCOUNT_NO_PROMPT=1` it set was read by
nobody. The launch command now sets `CMUX_CUSTOM_CLAUDE_PATH` to the door —
exactly what `cc` does — AND calls cmux's wrapper by its absolute path
(`/Applications/cmux.app/Contents/Resources/bin/cmux-claude-wrapper`) instead
of the bare word, because under `zsh -lic` (the tab route, any respawn-pane)
the login files put `~/.claude/local` at PATH position 1 and cmux's shim at 18,
so the bare word never reached the wrapper either (measured live 2026-09-03:
the first Route-B restart landed on personal that way). The receipt prints an
`account:` line saying which account the window signs in as, and via what.
Relay that line. If it says the door is MISSING, the window is on the personal
account; say so.

Seven flags exist, and NONE of them is ever your own initiative:

- `--account jason|personal` — which Claude account the NEW window signs in
  as. Pass it when Step 0a found an account word, or the user named the
  account in words (`open 5 on Jason's account`). Never on your own
  initiative: with no word the door decides silently, and that is the
  default. Refused alongside `here` (this tab's Claude is already running).
- `--tab` — the new window opens as a TAB inside the workspace that project is
  ALREADY open in, instead of as a second workspace. Pass it when Step 0a found
  the word `tab`, or the user asked for a tab in words. OPT-IN: without it a
  repeat open still makes a second workspace, which is unchanged Rule 3
  behaviour. It takes a LIST (unlike `here`) because each pick tabs into its own
  project's workspace. A pick whose project is open NOWHERE falls back to the
  workspace route and says so in its own output — relay that line, do not
  present it as a failure. Read the SUMMARY for `opened a TAB + delivery
  VERIFIED`. Refuses alongside `--focus-existing` and alongside `here`.
- `--here` — THIS TAB becomes the picked project; no window opens. Pass it when
  Step 0a found the word `here`, or the user asked for this tab in words. It
  routes to `adopt-project.sh` instead of `launch-project.sh`. It takes exactly
  ONE pick and refuses a list, and it refuses alongside `--focus-existing`
  (they mean opposite things). Read the SUMMARY line for its outcome:
  `THIS TAB is now the project`, or a REFUSAL naming `CROSS-ROOT` (the only
  refusal left since 2026-09-03). On `CROSS-ROOT`, relay it and OFFER to re-run
  without `here` — never pass `--allow-cross-root` unasked.
- `--focus-existing` — jump to a window already open on that project instead of
  making another. Use ONLY when the user asks to go to the existing one.
- `--label <text>` — name the new window `<project> <text>` (D12). Offer it when
  a second window on one project is being opened for a distinct piece of work;
  without it the script auto-numbers and says so.
- `--dry-run` — resolve and print the decisions, open nothing. Use it when the
  user wants to see what a list would do before it does it.
- `--include-archived` — allow a `completed` row to be reopened. Every row now
  carries a permanent number, ARCHIVED ones included, so an archived row CAN be
  named by number. `open-picks.sh` refuses one by default in its pre-check, so a
  mistyped number can no longer quietly revive a finished project. Pass this
  ONLY when the user is deliberately reopening a finished project — that is the
  loop, and it is his call. A `tombstoned` row is refused with no opt-in at all.

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
owns every gate and every write: the outgoing `active -> parked` release (no
close-record check since 2026-09-03), the sidebar rename, the `[key:<uuid>]` tag
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
- **already open elsewhere** → NOT a refusal (Zee, 2026-09-03). The receipt lists
  the other windows under `also open elsewhere` and adoption proceeds; several
  windows on one project is normal (Rule 3). Exit 3 and exit 4 are retired.
- **exit 5 / `CROSS-ROOT`** → the row's root is not this tab's folder. Relay the
  block and route it through Step 3, which opens it in its own folder. Do NOT
  re-run with `--allow-cross-root` unless the user asked for adopt-in-place in
  this conversation.
- **`REFUSED — ...` (exit 1/2)** → that line is the outcome; STOP, no workaround.
  A `SET-BUT-DEAD` refusal means cmux restarted under this session: the tab this
  process thinks it is in no longer exists.

## Step 5 — Loop verbs

### help — print the full verb sheet (Zee's ask, 2026-09-04)

The render carries a SHORT sheet; `help` prints the full one. Both live in
`resurrect-view.py`, so this skill relays and composes nothing. The flag reads
no registry and joins no cmux, so it is instant and safe at any time.

```bash
ROOT="$(pwd)"; RESDIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RESDIR/resurrect-view.py" ] || RESDIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
python3 "$RESDIR/resurrect-view.py" --verbs
```

Relay it whole in one fenced block, then re-offer the pick. Answer a `help`,
"what can I do here", or "what are my options" the same way — by RUNNING it.
The sheet is the single source of truth for what this skill accepts; anything
you add from memory can only drift out of date.

### numbers — see, set and swap the pick numbers yourself (Zee's ask, 2026-08-24)

Zee sets his own numbers. The machinery already existed in
`.claude/scripts/resurrection/manage-ordinals.py`, but NO skill mentioned that
file, so there was no way in short of knowing the path. These are the plain
words that reach it. Every one of them is **HUMAN-INITIATED ONLY** — never run
one on your own initiative, never batch them, never "tidy up" with them.

| the user says | you run |
|---|---|
| `numbers` | `manage-ordinals.py status` |
| `number 44 to 7` / `renumber 44 to 7` | `manage-ordinals.py renumber 44 7` |
| `swap 4 9` | `manage-ordinals.py swap 4 9` |
| `compact` | `manage-ordinals.py compact` |

```bash
ROOT="$(pwd)"; RES_DIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RES_DIR/manage-ordinals.py" ] || RES_DIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
# WITHOUT --apply every verb is a DRY RUN that prints what it would do.
# Show that output, get the user's yes, then re-run the SAME line with --apply.
python3 "$RES_DIR/manage-ordinals.py" <verb> <args>
```

Relay the output verbatim, same as every other block here. What the script
already handles, so you never re-implement or work around it:

- **`renumber` refuses to displace a live row.** It names the holder and points
  at `swap`. Relay that; do not pick a different number for him.
- **A previously-held number can be reused, and needs no flag** (Zee's ruling
  2026-08-24, reversing the earlier never-reuse rule). `renumber` still PRINTS
  what that number used to hold and when — anything still referring to it now
  points at a different row — but it no longer blocks. `--reuse-retired` is
  still accepted and does nothing.
- **`compact` needs `--confirm compact`, the word typed in full.** It renumbers
  every row to 1..N and **invalidates every number he has memorised**. It is
  opt-in for that reason. Say the cost out loud before running it, every time.
- **A new row fills the lowest free number** (same 2026-08-24 ruling). Gaps
  close on their own as projects are added, so `compact` is for tidying an
  existing spread, not for reclaiming holes one at a time. A row sitting in
  `deleted/` still HOLDS its number, so `restore` keeps working; only `purge`
  truly frees one. `delete`, `restore` and `purge` also live in this script;
  all are human-initiated and documented in its own header.
- **The cost of reuse, so it is never a surprise.** A number is no longer unique
  across time: 7 may be one project today and another after the first is purged.
  The ledger still records every number's history, so `numbers` can still say
  what 7 has been.

### delete / restore / purge — what each one really moves (Zee, 2026-08-24)

`finish` and `tombstone` only HIDE a row: it stays on disk, keeps its number
forever, and sits under ARCHIVED. `delete` is the other case — a row that should
not be in the book at all. Zee's rulings settled exactly what it moves:

| | the NUMBER | close bundles | knowledge facts |
|---|---|---|---|
| `delete` | **freed at once** | archived | untouched |
| `restore` | original if free, else the lowest free one | moved back | untouched |
| `purge` | already free; nothing changes | **kept** in the archive | **untouched** |

- **delete frees the number immediately.** He overruled the first cut, which
  held the number so `restore` could always have it back. His reason: delete
  must actually clear the book. That fits the reuse rule he set the same day.
- **"Treat it as `/acos-complete`"** — his words for the handoffs. Each handoff
  inside the row's close bundles is stamped `status: completed`, the same stamp
  that skill writes, and the bundle moves to `memory/handoffs/archive/closed/`.
  `.resume.md` files are never relabelled; the eternity protocol needs them.
- **Only PROVEN ownership moves.** A bundle is proven by its `.project-uuid`
  marker file — the file itself, never the wording of an evidence string. An
  unproven bundle is REPORTED and left where it is. Moving a project's history
  on a resemblance is the failure this exists to prevent: 22 rows share the
  ACOS 3.0 folder. Run `stamp-bundle-owners.py` to convert guesses into proof.
- **Knowledge facts survive both verbs.** Nothing else on this machine backs
  them up. `purge` ends the row's undo window; it is not a content eraser.
- **restore never displaces a live row.** If the original number was taken, the
  returning row takes the lowest free one and the receipt says which, and who
  holds the old one.

```bash
ROOT="$(pwd)"; RES_DIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RES_DIR/manage-ordinals.py" ] || RES_DIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
# Ownership first — a delete only archives what it can PROVE it owns.
python3 "$RES_DIR/stamp-bundle-owners.py"            # dry run: what would be stamped
python3 "$RES_DIR/stamp-bundle-owners.py" --apply
# Then the row verbs. Without --apply each is a dry run.
python3 "$RES_DIR/manage-ordinals.py" delete <n> --confirm-name "<exact name>" --apply
python3 "$RES_DIR/manage-ordinals.py" restore <uuid> --apply
python3 "$RES_DIR/manage-ordinals.py" purge <uuid> --confirm-name "<exact name>" --apply
```

**NEVER pass `--no-cmux` to `delete` from this skill.** It skips the open-window
check, which is the guard that stops a row being deleted out from under a live
window. An assistant is exactly the caller that cannot know whether one is open.

`stamp-bundle-owners.py` leaves two kinds alone and says so: a bundle claimed by
two rows at ONE folder, and a bundle no row claims. Both are duplicate-row cases
— merge the rows, then re-run, and the survivor owns the bundle.

### renumber in BULK, from a spreadsheet (Zee's ask, 2026-08-24)

One verb at a time does not scale, and it cannot express a reshuffle at all: to
swap 5 and 7 you must move one row onto a number the other still holds, and
`renumber` refuses that. So Zee asked for a sheet. He fills one column; the
script does the rest in a single planned pass.

| the user says | you run |
|---|---|
| `numbers sheet` / "give me the file" | `plan-ordinals.py export` |
| "I've filled it in" | `plan-ordinals.py apply --file <path>` |

```bash
ROOT="$(pwd)"; RES_DIR="$ROOT/.claude/scripts/resurrection"; [ -f "$RES_DIR/plan-ordinals.py" ] || RES_DIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
# 1. write the sheet (default: ~/Documents/OKOA/acos-row-numbers.xlsx)
python3 "$RES_DIR/plan-ordinals.py" export
# 2. Zee fills the `new_number` column and saves. WAIT for him to say he has.
# 3. dry run — prints the plan, writes nothing
python3 "$RES_DIR/plan-ordinals.py" apply --file "<path>"
# 4. only after he approves the printed plan
python3 "$RES_DIR/plan-ordinals.py" apply --file "<path>" --apply
# --survivor NUMBER=UUID names the surviving row of a merged number, and beats
# a green fill. Repeat it once per number. Example, 2026-08-25:
#   --survivor 26=cae643cb-6ad8-472e-9390-be40c1283578
```

The `new_number` column takes three kinds of value:

| cell | meaning |
|---|---|
| blank | leave that row exactly where it is |
| a number | move the row to that number |
| `0` | **DELETE that row** (Zee, 2026-08-25) |
| the SAME number typed on 2+ rows | **MERGE them into one row** (Zee, 2026-08-25) |

`0` can carry that meaning because it is the one value no row can hold — the
renderer never issues it. (`/acos-safe-close` also uses `0`, for "new project",
but that is a different question asked in a different place; nothing reads both.)

Relay every block verbatim. What the script owns, so you never re-implement it:

- **A blank cell means LEAVE THAT ROW ALONE.** It never clears a number.
- **`0` runs the real `delete` verb**, not a copy of it — so the number is
  freed, the close bundles are archived, and the knowledge facts are kept,
  exactly as they are for a single delete.
- **Deletes run BEFORE the moves.** A delete frees a number, and another row in
  the same sheet may be moving into it. Put `0` on row 5 and `5` on row 9, and
  row 9 lands on 5. The other order would collide.
- **A delete that cannot be safe refuses the WHOLE sheet, before anything is
  written.** Two blockers: a window is open on that row, or it owns a close
  bundle only by a guess. Per row the guess is a printed note; in a bulk run
  nobody reads per-row notes, so it is promoted to a refusal naming
  `stamp-bundle-owners.py` as the fix.
- **If a delete fails, the moves are NOT attempted.** The receipt names which
  row and its exit code, and tells you to re-export rather than re-run.
- **The stale-plan guard.** Each line's `current_number` must still match the
  row on disk. If anything renumbered, enrolled or closed since the export, the
  sheet describes a book that is gone and the whole apply REFUSES. Re-export.
  This is also what stops the same sheet being applied twice.
- **`project_uuid` is the identity.** Names repeat on this machine, so a name
  could never be the key. If he deletes that column, re-export rather than
  guessing which row he meant.
- **The same number TYPED on two or more rows is a MERGE, not a refusal**
  (Zee, 2026-08-25: "Found a lot of duplicates, I will put in the same number
  for the duplicates"). See the merge block below.
- **A typed number landing on a row whose cell is BLANK is still refused.** A
  blank cell was never typed, so it is a collision he did not ask for. The
  refusal names both rows and the four ways out: give the blank row a number,
  type the same number on it to merge them, mark it `0`, or pick another
  number. Measured 2026-08-25: five of these in his own sheet, one of which
  would have deleted the `zee` row.
- **Still refused:** a negative, and a fraction. A fraction is refused rather
  than rounded, because rounding would pick a row he never named.
- **The move is two passes.** Every mover is parked above everything in use,
  then placed. No intermediate state ever has two rows on one number.
- **A partial write is reported, never retried.** There is no lock on the
  registry. The script re-reads every row afterwards and, if anything did not
  land, prints what and stops — pointing at `manage-ordinals.py status` and
  `conflict-scan.py`. Do not re-run it to "fix" that; read the state first.
- **`registry.d/.ordinal-plan-in-progress.json`** exists only while writes are
  in flight. Finding one means a run died mid-rearrangement; it names exactly
  what was moving. Relay it, do not delete it on your own initiative.
- **XLSX needs openpyxl.** It is importable under `python3` (3.14.6) here but
  NOT under `/usr/bin/python3` (3.9.6). The export falls back to CSV and says so
  rather than failing at the last step. Excel opens either.
- **Exporting NEVER blanks a column he has already filled.** An export rewrites
  the whole file, and on 2026-08-25 that would have wiped 50 typed cells. The
  fresh sheet now copies the earlier one's `new_number` column across, matching
  by `project_uuid` (three rows are called FruitSync, so a name match would
  shuffle them), and keeps a dated copy of the file it replaces. `--carry-from
  PATH` reads a different sheet; `--blank` opts out. A typed number whose row no
  longer exists is REPORTED by name, never dropped in silence.

### merging duplicate rows (Zee, 2026-08-25)

> "Found a lot of duplicates, I will put in the same number for the duplicates,
> in case they have different names, go with the name for which I mark the
> number with green color."

The same number typed on two or more rows says those rows are **one project
wearing several rows**. They are folded into one.

**Which name survives**, in order — the first that applies wins:

| rung | how |
|---|---|
| 1 | `--survivor NUMBER=UUID` on the apply command, when he names one out loud |
| 2 | a **GREEN fill** on that row's `new_number` cell |
| 3 | whichever row holds the most (facts + 3 × close bundles) |

Rung 3 is reported as **WEAK** and listed separately above the dry run, because
nothing was marked and the script chose. Never apply past a WEAK list without
showing it to him first. Two green marks on one number, or a dead heat on rung
3, **refuse the sheet** — guessing between two deliberate marks is worse than
stopping.

**What a merge moves, before the losing row is deleted:**

- **knowledge facts** → through `merge-knowledge.py`, which de-duplicates by
  content hash and carries the `struck` / `supersedes` edges, so the survivor
  keeps the same view of what is still true.
- **close bundles** → re-stamped to the survivor. Where the roots differ the
  DIRECTORY moves too, because `owned_bundles()` only ever looks under a row's
  own root; a re-stamp alone would leave the history unreachable. A name clash
  at the destination gets a `--2` suffix, never an overwrite.
- **window claims** → re-pointed, so a tab open on the losing row keeps working.
- then the loser runs the real `delete` verb: number freed, remaining bundles
  archived, facts kept.

**Order matters.** Content moves FIRST. A bundle archived by the delete would
then be handed over from inside an archive folder, where nothing looks for it.

**Why absorb rather than just delete.** Delete already keeps a row's facts —
they live in a store addressed by `project_uuid`, not by the row. But nothing
would ever open that store again, because the row that named it is gone.
Absorbing is what makes the kept facts reachable. Live case: the two Logo
Builder rows hold 18 and 16 facts, both real.

**A merge dissolves its own bundle ambiguity.** A bundle two same-named rows
could both claim normally refuses everything — `bundle_owner` will not award
one project another's history on a resemblance. But if EVERY row that could
claim it is inside this merge group, the survivor owns it whichever way it
went. That is how `2026-07-18-ACOS-3.0-close`, the last unresolved bundle on
this machine, gets settled. A bundle some row OUTSIDE the group could claim
stays doubtful and still refuses, naming `stamp-bundle-owners.py`.

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
