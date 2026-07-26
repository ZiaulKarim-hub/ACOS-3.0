## 16. Architecture

### 16.1 Shape: thin router skill + TS scripts + one Bun server + a browser editor

**Not** a phase-orchestrator agent pipeline. The loan-doc phase-agent architecture the prior swarm recommended exists to run an autonomous multi-hour generation loop; **this product's expensive loop is a human sitting in a browser**, which the local-server pattern already serves.

The in-repo template is `~/.claude/skills/acos-image-builder/`: 4 files — `SKILL.md` (6.9KB), `app/server.py` (105 lines, stdlib `ThreadingHTTPServer` on 127.0.0.1:8810), `app/index.html` (1,636 lines / 102KB, inline CSS + vanilla JS, no build step), `scripts/imagebuilder.sh`. Five routes: `GET /api/library`, `GET|POST /api/project`, `POST /api/export`, `POST /api/upload`, plus static serving. One global `state = {doc, layers, sel, tool, brush, color}` with `serialize()`/`restore()`, a 40-step undo stack, localStorage autosave, ⌘S → POST. **[V — full read]**

**Every structural element the Website Builder editor needs already exists there in working form.** The one thing that does not transfer is the substrate: image-builder composites raster pixels on a `<canvas>`; a website editor manipulates real DOM nodes with CSS anchors. **Reuse the shell and the server contract; do not reuse the canvas compositor.**

`acos-type-forge` proves the full loop this product needs: one server fronts a hub linking three browser tools; browser edits persist as plain JSON on disk (`glyph-edits.json`, `spacing.json`); a deterministic non-browser script (`vectorize.py`) compiles those edits into the real shipping artifact (a TTF); a separate `rename_export.py` finalizer enforces the licence rule; and a *"review IN THE BROWSER before finalizing"* gate is marked ⚠️ do-not-skip. **[V — full read of SKILL.md, 196 lines]** Map directly: `layout.json` ← browser editor; `build.ts` = `vectorize.py`; LOCK = `rename_export.py`; the licence step is precedent for Step 8.

Its SKILL.md also states the one-origin rule's reason explicitly: *"Web fonts can't load over `file://` in Chrome → always serve over localhost."*

### 16.2 Language: TypeScript on Bun

`/Users/zee/CLAUDE.md` lines 25–46 make TS/Rust the mandatory default for **all** new code; Python is allowed only for (1) editing existing Python, (2) a Python-only library, (3) extending an existing Python hook chain. **None covers a new skill's own server or editor.**

Compliance precedent: `.claude/skills/acos-reverse-cleanroom/scripts/` — 16 `.ts` files with `#!/usr/bin/env bun` shebangs, a `scripts/package.json` (`"type": "module"`, `"Run with bun (no build step)"`, one dependency: `playwright@^1.48.0`), pure decision-logic split into `lib/*.ts` so ~90% is unit-testable, and a `bun selftest.ts` harness reporting 67/67 pass. `acos-research-riffs` has 13 more `.ts`. **[V — `ls`, `head`]**

Against that: **122 `.py` files across project skills, 66 across global skills.** The estate is Python-first; **this skill must not be.** Toolchain verified present: bun 1.3.9 at `/Users/zee/.bun/bin/bun`, node v20.19.3, rustc 1.88.0. **Rust is unnecessary** — nothing here is perf-critical or needs a single binary.

**Python-gravity is a real risk** (§17-R12): the path of least resistance is copying `server.py` and violating the rule. **Mitigation: port `server.py` → `server.ts` first, before any other code, so the TS spine exists from day one.** It is ~105 lines mapping 1:1 onto `Bun.serve()`, which gives native static serving, `Bun.file`, WebSocket upgrade, and streaming with zero dependencies. **A one-hour port, not a rewrite.**

### 16.3 Skill files

```
.claude/skills/acos-website-builder/          ← git-tracked, authored here
  SKILL.md                                     ← thin router, 9 phases
  scripts/
    package.json                               ← type: module, bun, no build
    server.ts                                  ← Bun.serve, fixed port 8820
    lock.ts                                    ← build → scrub → assert → snapshot
    import-system.ts                           ← Step-3 tolerant parser + validator
    variants.ts                                ← deterministic variant generator
    gates.ts                                   ← structured verdicts, never throws on a normal fail
    capture.ts                                 ← Chrome --headless=new wrapper
    evidence.ts                                ← Step-8 bundler
    registry.ts                                ← v2, cross-site component/direction registry
    verify.ts                                  ← regenerate-to-temp + diff -r
    doctor.ts                                  ← hash mismatches, orphaned overrides, stale locks
    extract-override.ts                        ← the sanctioned escape hatch
    install.sh                                 ← SYMLINK to ~/.claude/skills/
    selftest.ts                                ← bun selftest.ts, cleanroom's 67/67 is the bar
    lib/
      site-model.ts, render.ts, anchors.ts, cascade.ts, snap.ts, tokens.ts,
      slots.ts, coherence.ts, security.ts
  app/
    index.html                                 ← editor shell (3-pane)
    editor/
      anchors.ts, text-edit.ts, component-bar.ts, containers.ts,
      history.ts, request-more.ts, lock-preview.ts, overlay.ts, navigator.ts
  references/
    interview-bank.md                          ← §5, as a reference file not inline prose
    prompt-template.md                         ← §6
    item-inventory.md                          ← §7–§8
    gotchas.md                                 ← §16.6
  prompts/
    interview-synthesizer.md
    custom-component-author.md
```

**Installed globally via symlink**, not a copy. `acos-type-forge` exists in both the ACOS repo and `~/.claude/skills/` with byte-identical SKILL.md — **copies, not symlinks** (`ls -la` shows no symlinks anywhere in `.claude/skills/`) **[V]**. Website Builder must be usable from any project but is real code that must be version-controlled. `install.sh` creates the symlink, breaking the drift pattern rather than repeating it.

### 16.4 Invocation contract

```yaml
disable-model-invocation: true
user-invocable: true
argument-hint: "[--project <path>] [--resume] [--system <name>] [--port 8820] [--content] [--local-gen]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
```

Precedent: `acos-reverse-cleanroom` and `acos-design-variants` both set `disable-model-invocation: true` + `user-invocable: true` + an `argument-hint` **[V — frontmatter reads]**. `Bash` is needed to launch the bun server; `AskUserQuestion` for the interview (`acos-interview` runs its Q&A in the main context precisely because it is interactive).

**Do NOT list `Task` in `allowed-tools`.** `acos-skill-maker/SKILL.md` (~line 109) states: *"Sub-agent spawning is NOT a skill-frontmatter tool. Never add `Agent` or `Task` to `allowed-tools` — the framework ignores it… set `context: fork` and `agent: architect`."* The estate contradicts itself here — `acos-reverse-cleanroom/SKILL.md` line 6 lists `Task` — **treat skill-maker as the authority and do not copy that line.** **[V — both reads]**

**Phase 0 is a mandatory Confirmation Gate.** Both `/Users/zee/CLAUDE.md` and `ACOS 3.0/CLAUDE.md` mandate it. Bake the restatement into SKILL.md rather than relying on the ambient rule, and make the interview itself the confirmation artifact: restate the brief, get an explicit yes, then write anything.

Per-project config at `.acos/config/website-builder.yaml`, mirroring `.acos/config/cleanroom.yaml`: version, default port, breakpoints, direction count (10), variants-per-component (10), artwork count (20), gate thresholds, licence policy tier, publish target — snapshotted to `audit/config-snapshot.yaml` at init.

### 16.5 Agents

**Zero new files in `.claude/agents/`.** `ACOS 3.0/CLAUDE.md` Restricted Files: *"`.claude/agents/` — Agent definitions are infrastructure. Modification requires human approval."* The estate shows agents **are** added in approval batches (12 `rc-*`, 17 `dr2-*`, 9 `ic-*`), but `acos-synthesis-protocol` explicitly avoids it by spawning `Task(general-purpose)` with role prompts in the skill's own `prompts/` dir. **[V]**

Website Builder's agentic surface is small and human-paced (interview synthesis, prompt authoring, custom-component generation), so the general-purpose route is right: zero approval events, zero roster churn.

| Prompt | Purpose | Constraint |
|---|---|---|
| `interview-synthesizer` | Raw answers → structured brief for the prompt template | Returns text; main thread writes |
| `custom-component-author` | Step-6 novel components against the direction's tokens | Returns code as text; main thread writes (Write is blocked in subagents) |

### 16.6 Local server and the harness

**FIRST-PARTY VERIFIED: long-running local servers die in this harness** — and the editor's entire premise is a long-running local server.

`acos-guided-reader-server-gotcha.md` documents this being hit and diagnosed on 2026-07-09:

| Attempt | Result |
|---|---|
| Script spawns a detached child and exits | **Orphan reaped instantly.** `server.log` 0 bytes, nothing in `lsof -iTCP -sTCP:LISTEN` |
| Bash `run_in_background: true` | Binds, curls HTTP 200, then **SIGTERM (exit 143) AT THE TURN BOUNDARY** because the harness reaps tracked background tasks |
| `setsid nohup … &` | `setsid: command not found` on macOS |
| **Python double-fork daemon** (fork → setsid → fork → exec) | **WORKS** |

**[V — first-party, four attempts with exit codes]**

**Failure scenario for this product:** the user says "open the design surface," Claude starts the server, replies, the turn ends, the server is SIGTERM'd, and the browser shows `ERR_CONNECTION_REFUSED` — **every single time, appearing intermittent because it depends on turn timing.**

**Mitigation (recipe already proven in-repo):**

1. Double-fork daemon pattern.
2. **FIXED port** (8820) so the URL is known up front — **not** gr-server's random-port design, which orphans the user's open browser tab after an eternity `/clear`.
3. Write `{port, pid, url, sessionId}` into `state.json` at boot.
4. `curl --retry 20 --retry-connrefused` to confirm bind.
5. **A SECOND curl in a SEPARATE tool call** to prove it survived the turn boundary before telling the user to open it.
6. Regenerate-if-stale on startup (gr-server served a frozen `page.html` with no freshness check and showed an old UI after the template changed).

**Language conflict to resolve:** the proven launcher is Python; the standing rule mandates TypeScript. The TS equivalent is `child_process.spawn(cmd, args, {detached: true, stdio: 'ignore'}).unref()`, which is **not proven in this harness and must be re-proven with the same curl-across-turn-boundary test** before the PRD assumes it works. See §17-O5.

**Alternative worth spiking:** the single-origin variant — one Bun server proxying `astro dev` — collapses the CORS/postMessage surface to zero at the cost of proxy complexity. Spike both before locking the architecture.

**Two-process arrangement (the shape Onlook, Stackbit and Tina all converged on):** Process 1 is `astro dev` on 127.0.0.1 rendering the site with the editor integration (doc write → generator rewrites `src/generated/**` → HMR reloads, ~100–300ms). Process 2 is `wb-server` (Bun) on 127.0.0.1, the single doc writer, exposing `GET /doc` (ETag), `POST /ops`, `GET /events` (SSE), `POST /variants`, `POST /lock`. The editor chrome is a parent page served by `wb-server`; the site renders in an `<iframe>`; the two talk over `postMessage` with an explicit `targetOrigin`. Onlook's published flow is the same shape: load code into a container, container serves it, *"our editor receives the preview link and displays it in an iFrame,"* then instruments the code to map elements to their place in code **[V — quoted]**.

Three concrete wins: the site page stays pristine so **a screenshot of the iframe is a screenshot of the real site with no toolbar in it**; the editor survives an Astro restart without losing unsaved state; and LOCK preview is literally "point the same iframe at `dist/published`."

**The SSE + JSONL inbox pattern is house doctrine.** `gr-server.py` (2,000+ lines) and its validated port `ic-server.py` implement stdlib `ThreadingHTTPServer`, port written into `state.json`, `GET /state` (ETag/304), `GET /events` SSE with ~15s keepalive, browser commands appended to `commands.jsonl`, `POST /internal/*` for Claude to write back. The guided-reader SKILL.md is explicit: *"Each `tail -f` blocks the bash thread; Claude does not consume tokens while waiting."* **[V — quoted]** The division of labour is settled: **the server is a dumb byte-mover that NEVER calls `Task()`; the Claude session is the only engine.** `riff-server.ts` documents its own rule: *"Read-only by construction: there is no route that writes to the session."*

This is exactly how Step 5 ("10 more variants of this button") and Step 6 ("add a chart") happen without the user leaving the browser, **at zero token cost while they design.**

### 16.7 Screenshots

**Plain Chrome CLI, zero npm dependencies.** `website-design-okoa/_build/screenshot.sh`:

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --window-size=1440,3000 --virtual-time-budget=4000 \
  --screenshot=<out> <url>
```

then `[ -s "$out" ]`. **[V — read]**

By contrast, the ACOS Puppeteer path is only reachable via `NODE_PATH=/Users/zee/.npm/_npx/7d92d9a2d2ccc630/node_modules` — an npx cache that can be evicted; ACOS 3.0's root `package.json` declares `puppeteer@^24.39.1` but **`node_modules/` is EMPTY (0 entries)** **[V]**.

**Inherit the capture waits from `.claude/scripts/html-to-pdf.js`** — each encodes a real production bug: `page.goto(fileURL)` not `setContent()`; `networkidle0` with fallback to `load`; **strip `loading="lazy"` before capture** (headless IntersectionObserver never fires below the fold); `await document.fonts.ready` **plus per-image `decode()`**; then a 500ms deferred-CSS settle. Re-express in TS; do not re-derive.

If scripted interaction/hover capture is later needed, follow the cleanroom precedent: `cd <skill>/scripts && bun add playwright && bunx playwright install chromium` — **the dependency lives inside the skill, not in an npx cache.**

### 16.8 Hooks

A skill **can** register its own hook dynamically: `acos-reverse-cleanroom` Phase −1 step 4 says *"Arm the egress guard: add the PreToolUse hook to `.claude/settings.local.json`… Verify with a probe call"*, and Phase 7 removes it at close. The guard is `scripts/egress-guard.ts` — **a TypeScript PreToolUse hook**, so TS hooks are already accepted. **[V — quoted]**

The existing PreToolUse chain has 5 entries, four ending in `|| printf '{"hookSpecificOutput"…allow'` (fail-open); the one hard gate is `block-review-rules-read.sh`. **Any Website Builder hook must be cheap and fail-open.**

| Hook | Purpose | Priority |
|---|---|---|
| **PreToolUse: editor-file-ownership guard** | Blocks Claude's `Write`/`Edit` on `pages/*.doc.json`, `content.json`, `history.jsonl` while the editor lock is held | v1 |
| **PostToolUse: evidence mirror** | One-line verdicts into `.acos/evidence/<date>/website-<session>/` so `/acos-status` sees the build | v3 |

**"No LOCK without gates passing" is better implemented as a script exit code than a hook.**

### 16.9 Reuse-versus-build table

| Item | Decision | Path / source |
|---|---|---|
| One-origin server contract, 5 routes | **Port Python→TS** | `~/.claude/skills/acos-image-builder/app/server.py` (105 lines) |
| Browser-edits-as-JSON → deterministic compiler | **Adopt pattern** | `~/.claude/skills/acos-type-forge/scripts/vectorize.py` flow |
| SSE + `commands.jsonl` + zero-token `tail -f` | **Adopt pattern** | `~/.claude/skills/acos-guided-reader/scripts/gr-server.py`; `.claude/skills/acos-investment-committee/scripts/committee-room/ic-server.py`; `.claude/skills/acos-research-riffs/scripts/riff-server.ts` (already TS) |
| Chrome headless capture recipe | **Adopt as-is** | `/Users/zee/Documents/Vibe Coding/website-design-okoa/_build/screenshot.sh` |
| Capture waits (lazy-strip, fonts.ready, decode, settle) | **Re-express in TS** | `.claude/scripts/html-to-pdf.js` |
| Design-system schema + QA framework | **Adopt** | `~/.claude/skills/acos-design-system-forge/references/01-template.yaml` + `07-qa-framework.md` + extension modules (`motion-interaction.md` is the right source for D4's animation item) |
| Warm-start store | **Adopt as-is** | `.acos/design-library/<name>/` |
| Per-variant licence register format | **Adopt as-is** | `website-design-okoa/okoa-design/*/v1/README.md` |
| Session dir + ACTIVE marker + config snapshot | **Adopt pattern** | `.claude/skills/acos-reverse-cleanroom/SKILL.md` Phase −1 |
| Frontier-recomputed-from-disk principle | **Adopt** | `.claude/skills/acos-axiom-synthesis/STATE-MACHINE.md` line 66 |
| 3-variant side-by-side comparison | **Adopt** | `~/.claude/skills/acos-design-variants/SKILL.md` Phase 2 |
| Chart form heuristic, colour formula, validator, palette | **Adopt** | local `dataviz` skill + `references/palette.md` |
| Puck Data/Render split, viewports config, slot `allow`/`disallow` | **Adopt patterns, not code** | puckeditor.com docs |
| Figma constraint + "Ignore auto layout" model | **Adopt pattern** | help.figma.com |
| Stackbit annotation scheme + descent scoping | **Adopt pattern** | docs.netlify.com |
| Plasmic owned/managed file split | **Adopt pattern** | docs.plasmic.app |
| dnd-kit (MIT, 17,437★, pushed 2026-07-13) | **Adopt as code** | Pointer + keyboard sensors and collision layer **ONLY** — never as the layout model |
| ProseMirror / TipTap (MIT) | **Adopt as code** | One long-form block only |
| Wigum fix-loop exit-code contract | **Port to structured verdicts** | `.claude/skills/acos-ultimate-designer/scripts/wigum-loop.py` → `gates.ts` (cleanroom `lib/gates.ts` is the model: return verdicts, never throw on a normal fail) |
| Genesis registry | **Port Python→TS** | `registry.py` → `registry.ts` over the same `registry.json` (v2) |
| **The VLM judge loop** | **DO NOT PORT** | The human replaced it; porting re-imports the rejected architecture |
| **Autonomous Wigum aesthetic iteration** | **DO NOT PORT** | Same |
| **`.claude/agents/` additions** | **DO NOT ADD** | Human-approval-restricted; `Task(general-purpose)` suffices |
| **`site.json` model + renderer** | **BUILD NEW** | Nothing in ACOS does DOM-level layout editing |
| **Editor runtime** (anchors, snap, contenteditable, component bar, containers) | **BUILD NEW** | " |
| **Design-system importer + repair-prompt emitter** | **BUILD NEW** | " |
| **Deterministic variant generator** | **BUILD NEW** | " |
| **LOCK/export compiler** | **BUILD NEW** | " |
| **Evidence + licence bundler** | **BUILD NEW** | " |
| **`install.sh` symlink installer** | **BUILD NEW** | Breaks the copy-drift pattern |

### 16.10 Frameworks explicitly rejected

| Candidate | Licence / health | Why rejected |
|---|---|---|
| **GrapesJS** | BSD-3-Clause (npm), 26,067★, pushed 2026-07-24 — healthy | Backbone + underscore era architecture; core `dragMode: 'absolute'` is coordinate dragging with no responsive story; **its own docs scope Absolute Mode to *"fixed-layout designs … where responsiveness isn't required"***; the polished version lives in the commercial Studio SDK, not the open core. **[V — registry.npmjs.org, GitHub API, app.grapesjs.com]** Also note GitHub's API reports NOASSERTION while npm reports BSD-3-Clause — **re-verify against the actual LICENSE file at pin time** |
| **Craft.js** | MIT, 8,700★, **last push 2025-02-14** — ~17 months stale as of 2026-07, 225 open issues | Unacceptable as a foundation for a system that must run for years **[V — GitHub API]** |
| **Plasmic** | SDKs and code components open; **core editor and studio proprietary** | Self-hosting exists, forking the editor does not **[V — forum.plasmic.app]** |
| **Builder.io** | Only Mitosis (the compiler) is open | The visual editor is SaaS |
| **TeleportHQ** | Open component/codegen layer around a hosted editor | Same shape |
| **Puck** | **MIT, 13,018★, pushed 2026-07-24, actively developed** — genuinely the right philosophy and licence, now positioning as *"the agentic visual editor for your design system"* | **Three gaps, each fatal here:** (1) **no grid-cell placement model** — Puck composes flow lists via slots and *"multi-column layouts using nested components,"* so D2's snap-to-gridlines and Step-4(a) gridlines have no home; (2) **no per-breakpoint override cascade** — viewports resize the iframe but the Data document has no breakpoint dimension; (3) **it is React**, whereas the settled build target is Astro static with zero shipped JS, so components would exist twice. **Mine it for API shapes and possibly vendor individual utilities; do not build the product inside it** **[V — GitHub API + docs read; the three gaps are inference from the docs]** |

**Figma Sites** (open beta, Config 2025) confirms the direction is mainstream and supplies two transferable ideas — name-matched responsive variant binding (breakpoints named Desktop/Tablet/Mobile bind to variant property values with those names), and the fact that Figma treats custom cursors, marquee and parallax as **first-class site primitives**, corroborating the user's Step-2 item list. Nothing else is reusable: closed, hosted, exports no ownable editor. **[V — figma.com/blog, help.figma.com]**

### 16.11 macOS / harness gotchas to encode in `references/gotchas.md`

| # | Gotcha |
|---|---|
| 1 | **No `timeout`/`gtimeout` binary** on this Mac — `timeout 25 cmd` silently yields **EMPTY output**, not an error. Guard long runs with `run_in_background: true` + poll |
| 2 | **Agent-thread cwd resets between Bash calls** — absolute paths everywhere |
| 3 | House rule: open previews with `open -a "Google Chrome" <url>` |
| 4 | Opus subagents stream-idle-timeout on heavy binary reads — keep rendering/screenshotting in the main thread or background Bash |
| 5 | **macOS APFS is case-insensitive** — sibling direction names must not differ only by case |
| 6 | Autosave must be a small JSON diff POSTed to the server, **never a base64 blob in localStorage** (image-builder's own logged gotcha) |
| 7 | The Oracle scores Bash/Write/Edit/Task at threshold 9 fail-open, so ordinary bun/chrome commands auto-approve; **destructive steps score +5 and will prompt** — implement export as **write-to-new-dir-then-swap**, never `rm -rf` |
| 8 | Eternity `/clear` at 400k (project config) / 500k (daemon config — **the daemon's own config wins; hardcode neither**) kills the `tail -f` loop. Fixed port + `state.json` + a resume prompt that says **re-attach, do NOT relaunch** |
| 9 | `session-cleanup.sh` runs at SessionEnd on `.acos/state/` only, so `.acos/website-builder/` artifacts are safe |
| 10 | Astro HMR does not reliably hot-reload when files are **added or removed** under `src/pages/` — a variant swap that changes the import graph may need a full reload. Budget a measured fast path and a hard-reload fallback |
| 11 | `claude-in-chrome` MCP availability inside spawned agents is **unverified** — do not design any capture path that depends on it |

---

