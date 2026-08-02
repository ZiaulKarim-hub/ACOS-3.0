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
| `git-manager.ts` | CLI entry: `scan`, `plan-push` |
| `scan.ts` | depth-limited walk, per-repo state, the five-state classifier |
| `git.ts` | read-only git wrappers (only `fetchAll` touches the network) |
| `accounts.ts` | remote URL → GitHub account, plus the `neverPush` rule check |
| `inventory.ts` | what lives in a repo; resolves symlinked-in skills to their host repo |
| `secrets.ts` | pre-push credential scan; findings are always masked |
| `render-terminal.ts` | the table |
| `render-html.ts` | self-contained browser page, light and dark |
| `config.default.json` | roots, skip list, account matchers, `neverPush` rules |

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
