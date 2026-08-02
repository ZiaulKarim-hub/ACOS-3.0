# Live Machine Inventory — 2026-07-16 (verification vs 2026-07-14 report)

All commands read-only. `claude` shell function in `~/.zshrc:215` (`claude() { _acos_cli claude "$@"; }`) is broken in non-interactive shells (`command not found: _acos_cli`); real binary resolved via `which -a claude` → used `/Users/zee/.claude/local/claude` directly. A cmux CLI shim also shadows PATH: `/var/folders/.../cmux-cli-shims/.../claude`.

## 1. cmux

`"/Applications/cmux.app/Contents/Resources/bin/cmux" version`
```
cmux 0.64.19 (99) [1c22c5564]
```
Installed is now **0.64.19** — newer than both the report's "installed 0.63.2" and its "latest 0.64.18". cmux was upgraded since the report.

`... capabilities` → JSON: `protocol: cmux-socket`, `version: 2`, `access_mode: cmuxOnly`, `socket_path: /Users/zee/.local/state/cmux/cmux.sock`, ~230 methods. Notable for Resurrection Protocol: `surface.send_text`, `surface.send_key`, `surface.resume.get/set/clear`, `surface.list`, `surface.health`, `workspace.list/create/select/rename`, `workspace.env`, `session.restore_previous`, `pane.list`, `terminal.input`.

`... list-workspaces` (legacy alias notice printed; alias for `cmux workspace list`, still works). Live list via `workspace list --json`:
| ref | title | cwd | selected |
|---|---|---|---|
| workspace:5 | Resurrection Protocol | /Users/zee/Documents/Vibe Coding/ACOS 3.0 | no |
| workspace:4 | OKOA Works | /Users/zee/Documents/Vibe Coding/ACOS 3.0 | no |
| workspace:1 | ✳ Resume Fruit Sync cover image generation | /Users/zee/Documents/Vibe Coding/FruitSync | yes |

Duplicates: workspaces 5 and 4 share the same cwd (`ACOS 3.0`); only distinguishable by custom title. Both have custom titles (`has_custom_title: true`). A "Resurrection Protocol" workspace already exists (work on this project has begun in cmux).

## 2. ~/.config/cmux/cmux.json

`ls -la ~/.config/cmux/` → **EXISTS NOW**: `cmux.json` (6111 B, mtime **Jul 16 18:33** — created/touched today), plus `settings.json` (6120 B, May 6).
Content: JSONC template — `"$schema": .../cmux.schema.json`, `"schemaVersion": 1`, and **every setting commented out** (app, notifications, sidebar, workspaceColors, sidebarAppearance, automation incl. `claudeBinaryPath`/`socketControlMode: cmuxOnly`/`portBase: 9100`, customCommands.trustedDirectories, browser, shortcuts). Header comment: "cmux creates this template on launch when both settings file locations are missing. ~/.config/cmux/settings.json takes precedence over the Application Support fallback." Net: file exists but is a no-op template; no file-managed settings active.

## 3. Claude Code

`/Users/zee/.claude/local/claude --version` → `2.1.212 (Claude Code)` (report claimed 2.1.209 — auto-updated).

`--help` flag confirmation:
- `-r, --resume [value]` — EXISTS (session ID or interactive picker w/ optional search term)
- `-c, --continue` — EXISTS (most recent conversation in current directory)
- `--session-id <uuid>` — EXISTS
- `--fork-session` — EXISTS (with --resume/--continue)
- `-n, --name <name>` — EXISTS (display name in prompt box, /resume picker, terminal title)
- `--no-session-persistence` — EXISTS (only works with --print)

`claude project` subcommand — **EXISTS**: "Manage Claude Code project state"; sole subcommand is `purge [options] [path]` — "Delete all Claude Code state for a project (transcripts, tasks, file history, config entry)". No list/register/rename verbs.

## 4. ~/.claude.json (python3 json parse)

```
projects keys: 42
with lastSessionId: 32
```
Matches report exactly (42 / 32). Example project paths: `/Users/zee`, `/Users/zee/Desktop/loan-intake-platform`, `/Users/zee/Desktop/okoa-loan-intake-system`.

## 5. Transcript inventory

`find ~/.claude/projects -name "*.jsonl" -not -path "*subagents*" | wc -l` → **643** (report claimed 781 — 138 fewer; transcripts were deleted/purged/rotated since 07-14).
`du -sh ~/.claude/projects` → **1.2G** (report claimed 1.1 GB — grew slightly despite fewer files).

## 6. Registry / Resurrection artifacts

- `ls ~/.acos/registry.d/` → **No such file or directory**. `find ~/.acos -iname "*registry*"` → empty. `~/.acos/` contains only: `config`, `evidence`, `metrics`, `paste`, `state`.
- `ls ~/.claude/skills/ | grep -iE "resurrect|close-project|registry|switch"` → no match.
- `ls "/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/skills/" | grep -iE "resurrect|close-project|registry|switch"` → no match.
Nothing of the proposed system is built yet.

## 7. Daemon state dir

`ls "$HOME/Library/Application Support/acos-token-monitor/state" | wc -l` → **963** (report claimed ~1500 — roughly 500+ fewer entries; state dir shrank, likely GC/cleanup). Nothing modified.

## 8. Handoff dirs

ACOS 3.0 `memory/handoffs` top-level: **18 `*.resume.md`** + **2 `*.yaml`** (`2026-07-16-emergency-handoff.yaml`, `2026-07-16-emergency-handoff-2.yaml` — both created 07-16, i.e., new since the report) + `archive/` subdir.

Other project roots with `memory/handoffs` (find maxdepth 3):
Under `/Users/zee/Documents/Vibe Coding/`: **Fastest Decision tree**, **(Vibe Coding root itself — `Vibe Coding/memory/handoffs` exists directly)**, **HearMeTalk**, **website-design-okoa**, **Font-Forge**, **FruitSync**, **ACOS 3.0**, **BrandSync**, **private-equity-hedge-fund-strategy**, **email-obot**, **okoa-wiki**, **Auto-Blogger**, **Jobsync**, **Codesync**, **Xyntax**, **SLOPE-Structured_Life_Organization_and_Planning_Engine**, **okoa-loan-intake-system** — 17 dirs (16 projects + the Vibe Coding root anomaly).
Under `/Users/zee/Documents/OKOA/`: **Find payments made to XL** (1).
Total: 18 handoff dirs the registry must cover (plus `.claude.json` shows 42 known project cwds incl. Desktop paths).

## 9. Live Claude processes

`ps aux | grep -i "claude" | grep -v grep | wc -l` → **23** — noisy. Breakdown: 3 interactive CLI sessions (`--session-id b6a737e4…`, `7d50c4ce…`, `54600feb…` [this one]), 2 headless `-p --input-format stream-json` subagents, 6 python3.14 processes (token-monitor daemons match count), 1 `cmux hooks claude pre-tool-use`, and ~10 Claude Desktop app processes (Claude.app + helpers/renderer/GPU/crashpad/ShipIt/chrome-native-host) inflating the grep. Real Claude Code CLI count: **5** (3 interactive + 2 subagent).

---

# CHANGED SINCE 2026-07-14

1. **cmux version: DRIFT.** Installed 0.64.19 now, not 0.63.2; also exceeds the report's "latest 0.64.18". Any report logic keyed to 0.63.x behavior (e.g., missing RPC methods) needs re-check; `surface.resume.get/set/clear` and `session.restore_previous` are present in the live capabilities list.
2. **~/.config/cmux/cmux.json: DRIFT (if report said absent).** File exists as of Jul 16 18:33 — but it is an all-commented-out auto-generated JSONC template with zero active settings.
3. **Claude Code version: DRIFT.** 2.1.212 vs claimed 2.1.209. All six claimed flags verified present; additionally `claude project purge` subcommand confirmed to exist.
4. **~/.claude.json 42 projects / 32 lastSessionId: NO DRIFT.** Exact match.
5. **Transcripts: DRIFT.** 643 non-subagent .jsonl (was 781, −138); disk 1.2G (was 1.1 GB, +~0.1G).
6. **Registry/skills: NO DRIFT.** Still nothing built — no `~/.acos/registry.d/`, no registry files, no resurrection/close-project/registry/switcher skills in either skills dir. (But note: a cmux workspace titled "Resurrection Protocol" now exists at the ACOS 3.0 cwd.)
7. **Daemon state dir: DRIFT.** 963 entries vs claimed ~1500.
8. **Handoffs: MINOR DRIFT.** Two new top-level YAML handoffs dated 2026-07-16 in ACOS 3.0; 18 .resume.md persist. 18 total memory/handoffs dirs across Vibe Coding (17, incl. one directly under the Vibe Coding root) + OKOA (1).
9. **Live processes: expected churn**, count 23 (noisy; 5 real CLI processes). Not a stable claim to diff.

Load-bearing environment gotcha for the Resurrection build: the `claude` command is shadowed twice (broken `_acos_cli` zsh function at `~/.zshrc:215`, and a cmux CLI shim on PATH); scripts must call `/Users/zee/.claude/local/claude` or `$HOME/.claude/local/claude` explicitly.