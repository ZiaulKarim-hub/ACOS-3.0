# git-manager

Scripts behind the global `/acos-git-manager` skill (`~/.claude/skills/acos-git-manager/SKILL.md`).

Answers two questions and stops:

1. **Where does everything live?** Which git repo hosts which skill, sub-project, or
   piece of software — and which GitHub account each of that repo's remotes belongs to.
2. **What is not stored anywhere safely yet?** Split into the five states that have
   different fixes, not lumped into one "unsynced" flag.

```
bun git-manager.ts scan [--fetch] [--all] [--loose] [--json] [--html <path>]
                        [--open] [--root <path>]... [--config <path>]
                        [--color never] [--width <cols>]
bun git-manager.ts plan-push --repo <path> --to <remote|personal|work>
                             [--acknowledge-secrets] [--config <path>]
```

Exit codes for `plan-push`: `0` ok · `2` bad input or unknown remote ·
`3` destination forbidden by a `neverPush` rule · `4` suspected secret in the
outgoing diff.

## Browser view

`--html <path>` writes a self-contained page: no external stylesheet, no script
from the network, works offline, styled for light and dark.

`--open` implies `--html` (writing to a temp file when no path is given) and then
opens the page in **Google Chrome** specifically — `open -a "Google Chrome"` — not
the default handler. If Chrome is unavailable it falls back to the default browser
and says so. A failed open is never fatal: the `file://` path is printed either
way, and the exit code is unaffected.

The `/acos-git-manager` skill passes `--open` on every run. The flag stays opt-in
at the command line, because a script should not take over the browser unasked.

## Layout

`render-terminal.ts` draws two box-ruled tables sharing ONE column grid (computed
across every row, so both line up), then a detail card per row — top 5 by risk by
default, all rows with `--all`.

Two invariants the tests enforce at widths 96 / 100 / 110 / 118 / 120 / 140 / 160,
with colour on and off:

- every border line is exactly `--width` characters
- no line overflows `--width`

They hold because the two flexible columns (`PROJECT`, `WHERE IT CAN GO`) consume
the leftover space *exactly* — `PROJECT` shrinks toward 10 when space is tight
rather than either column being floored — and because `trunc()` counts VISIBLE
characters, stepping over ANSI escape codes instead of counting them.

`--width` defaults to the live terminal width, clamped to 96–160. Pass it
explicitly when the output will be read somewhere other than this terminal.

## Recommendations

`recommend.ts` adds two derived columns. Both come from what the scanner already
found; neither re-reads the disk.

- **`KIND`** — `config` / `skills` / `agents` / `code` / `docs`. `code` fires on a
  build file, a package name, 3+ scripts, or a conventional source sub-folder
  (`src`, `app`, `tests`, `convex`, …), so a project that keeps its code one level
  down is not mislabelled `docs`.
- **`DO THIS`** — the single next step, naming the destination account. A trailing
  `?` marks the WORK account (user's call under the personal-default rule).
  `·dup#N` marks a possible duplicate.

Three honesty rules it keeps:

1. A duplicate is always "possible". Same name after stripping `Backup `,
   `Clone-`, `copy`, and trailing counters is evidence, not proof — deleting the
   wrong copy is unrecoverable, so the wording is always "check vs".
2. A duplicate becomes the HEADLINE action only when the row is `NOT_A_REPO` or
   `NO_REMOTE`. On a live repo with commits waiting, the push stays the action and
   the duplicate is appended — replacing it would hide real pending work.
3. The personal account is the default destination; the work account is only ever
   suggested with a `?`.
4. **A recorded human ruling outranks every derived suggestion**, including the
   duplicate check. See below.

## Decisions — the only part of this tool with memory

Everything else recomputes from disk on every run, which is why the report kept
asking `docs — track?` about folders the human had already ruled out. A scan can
see what git knows; it cannot see what was decided. `decisions.ts` is that memory.

```bash
bun git-manager.ts decide --repo <path> --not-tracked --why "<reason>" [--date YYYY-MM-DD]
bun git-manager.ts decide --repo <path> --undo
bun git-manager.ts decide --list
```

Rulings live in `decisions.json` beside the config — separate on purpose, because
config is settings you hand-edit while rulings accumulate over time. Four rules:

1. **Recorded, not hidden.** A ruling moves the row into its own `DECIDED — NOT
   TRACKED` table. It never removes the row. `ignorePaths` already hides things,
   and a hidden row is a decision nobody can review or reverse.
2. **The state stays true.** A decided folder that is not a repo still reports
   `NOT_A_REPO`, and keeps its severity, so `--undo` restores its exact former
   position. The ruling changes what to DO about the fact, never the fact.
3. **Exact path, fails loud.** Matching is on the absolute path. Rename or move
   the folder and the ruling stops applying, so the row returns to needs-attention
   and any ruling left behind is printed under `RULINGS THAT MATCHED NOTHING`.
   Loose matching would quietly carry a ruling onto a path never ruled on.
4. **A reason is mandatory.** `decide` exits 2 without `--why`. A ruling nobody can
   review later is indistinguishable from the tool having simply forgotten.

`do-not-track` is the only verdict. "Track it later" is not a ruling; it is an item
still on the list. `totals.decided` counts these rows, and they are excluded from
`totals.needAttention` AND from `totals.clean` — decided is not the same as safe.

A `decisions.json` that exists but will not parse is a REFUSAL (exit 2), never a
silent fall back to "nothing was decided". Losing every ruling without saying so
would send the report straight back to asking settled questions.

## The live page (`serve`)

```bash
bun git-manager.ts serve [--port 8787] [--no-open] [--loose]
```

A saved file cannot update itself. Reloading one just re-reads the same frozen
text, so an auto-reloading `--html` file would look live while being wrong —
worse than a file, which at least admits it is a snapshot. `serve` is the honest
version: a local server on `127.0.0.1` (this machine only, never the network)
that re-scans when something actually changes and pushes the new table to any
open page over Server-Sent Events.

**Strictly read-only.** It scans, renders and serves. It never commits, never
pushes, never writes to a repo. The one network action is the page's *refresh
from GitHub* button, which runs `git fetch` — read-only, and only on a click.
Fetching 31 repos every few seconds would be slow and rude; stale-but-labelled
beats fast-and-rude.

**How it knows.** Not polling. `watch.ts` asks macOS to report changes under the
roots (`fs.watch` recursive), debounces a burst into one re-scan, and re-scans
only then. Measured: 1 scan in a 40-second idle window while Claude Code was
actively writing session transcripts; a real change reaches the page in ~2s.

Two filters make that work, and BOTH were found by testing, not by reading:

1. **`.git` must NOT be skipped by the watcher**, even though the scanner skips
   it. A commit, a branch move and a push change nothing outside `.git` — reusing
   the scanner's `skipDirs` made a pure `git commit` produce no update at all.
   Inside `.git`, only `objects/` and `lfs/` are dropped (hundreds of writes per
   operation, each accompanied by a ref or index write we do see).
2. **`config.watchIgnore`** — high-churn folders not worth WAKING UP for.
   `~/.claude/projects` holds session transcripts rewritten every few seconds;
   each one triggered a full 1.7s rescan that changed nothing. These folders are
   still scanned and still counted; they just appear on the periodic re-check
   (60s) rather than instantly. That trade is explicit, not silent.

**The page tells the truth about its own age.** A bar shows `live`, what caused
the last update, and how long ago it scanned. If the server dies the bar turns
red and says *"connection lost — everything below is a FROZEN SNAPSHOT, not the
current state"*, then reconnects by itself when the server returns. A live page
that quietly keeps showing old numbers is the failure mode this must never have.

Updates swap `<main id="gm-root">` in place, so scroll position and open
`details` panels survive. `renderHtml(scan, {live:true})` adds the connection
script and nothing else — served markup is byte-identical to `--html` output.

A scan that throws does not kill the server: the page keeps the last good table
and is told the refresh failed. Ports in use are stepped over, not fought over.

## Ordering

Rows sort worst state first. Within a state they sort by how much work sits there
(`inventory.weight`: skills ×4, agents ×3, sub-projects ×2, scripts ×1, capped),
then by raw volume. Content weight orders rows INSIDE a band and can never lift a
row out of it, so "holds a lot" never outranks "exists nowhere else". A
`neverPush` breach adds 100000 and floats to the top.

## It never pushes

`plan-push` stops at printing the literal command:

```
git -C "<path>" push <remote> <branch>
```

That command must be run directly by the session. Wrapping the push inside this
script would hide it from `~/.claude/hooks/github-repo-guard.ts`, which is exactly
the failure the guard exists to prevent. Naming the remote in the command is what
keeps the destination visible in the transcript.

`plan-push` exits 3 and prints no command when a `neverPush` rule in the config
forbids that repo/account pair.

## Files

| File | Role |
|---|---|
| `git-manager.ts` | CLI entry: `scan`, `plan-push`, `decide`, `serve` |
| `scan.ts` | depth-limited walk, per-repo state, the five-state classifier |
| `decisions.ts` | the human's rulings — the only stateful part; read/record/withdraw |
| `serve.ts` | the live page: local server, live connection, read-only |
| `watch.ts` | change detection — event-driven, debounced, noise-filtered |
| `git.ts` | read-only git wrappers (only `fetchAll` touches the network) |
| `accounts.ts` | remote URL → GitHub account, plus the `neverPush` rule check |
| `inventory.ts` | what lives in a repo; resolves symlinked-in skills to their host repo |
| `recommend.ts` | derives `KIND` (what it is) and `DO THIS` (the one next step) |
| `secrets.ts` | pre-push credential scan; findings are always masked |
| `render-terminal.ts` | the table |
| `render-html.ts` | self-contained browser page, light and dark |
| `config.default.json` | roots, skip list, account matchers, `neverPush` rules |
| `decisions.json` | written by `decide`; the rulings themselves (created on first use) |

Copy `config.default.json` to `config.json` to override without touching the default.
`ignorePaths` is empty on purpose: prune a row only after you have seen it and judged
it noise.

## Known limits

- Remote counts come from each repo's last fetch unless `--fetch` is passed.
- `.gitignore`d files are invisible to the unsaved count.
- The headline state describes the current branch. Other local branches are
  checked and surface as `SIDE BRANCH`, but only the 60 most recently committed
  branches per repo are examined.
- Folders with just a script or two beside documents are counted, not listed,
  unless `--loose` is passed. Folders named in `ignoreNames` are hidden entirely,
  but that rule never hides a repo. Both counts are printed.
- The walk stops at `maxDepth` below each root and does not follow symlinked
  directories (following them invents "untracked" projects that are tracked at
  the link target).
- The secret scan matches shaped credentials and skips lock files and binary
  assets. A password that looks like an ordinary word will pass. It reads at most
  1000 commits or 5 MB of diff and reports when it was cut short — a clean result
  on a truncated scan is not a clean result. `git log -p` is used rather than
  `git diff` because `git diff HEAD` is empty once everything is committed, which
  would silently scan nothing on a never-pushed branch.
