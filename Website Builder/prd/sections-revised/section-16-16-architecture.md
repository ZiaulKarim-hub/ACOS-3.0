## 16. Architecture

### 16.1 Shape: thin router skill + TS scripts + one Bun server + a browser editor

**Not** a phase-orchestrator agent pipeline. The loan-doc phase-agent architecture the prior swarm recommended exists to run an autonomous multi-hour generation loop; **this product's expensive loop is a human sitting in a browser**, which the local-server pattern already serves.

The in-repo template is `~/.claude/skills/acos-image-builder/`: 4 files — `SKILL.md` (6.9KB), `app/server.py` (105 lines, stdlib `ThreadingHTTPServer` on 127.0.0.1:8810), `app/index.html` (1,636 lines / 102KB, inline CSS + vanilla JS, no build step), `scripts/imagebuilder.sh`. Five routes: `GET /api/library`, `GET|POST /api/project`, `POST /api/export`, `POST /api/upload`, plus static serving. One global `state = {doc, layers, sel, tool, brush, color}` with `serialize()`/`restore()`, a 40-step undo stack, localStorage autosave, ⌘S → POST. **[V — full read]**

**Every structural element the Website Builder editor needs already exists there in working form.** The one thing that does not transfer is the substrate: image-builder composites raster pixels on a `<canvas>`; a website editor manipulates real DOM nodes with CSS anchors. **Reuse the shell and the server contract; do not reuse the canvas compositor.**

`acos-type-forge` proves the full loop this product needs: one server fronts a hub linking three browser tools; browser edits persist as plain JSON on disk (`glyph-edits.json`, `spacing.json`); a deterministic non-browser script (`vectorize.py`) compiles those edits into the real shipping artifact (a TTF); a separate `rename_export.py` finalizer enforces the licence rule; and a *"review IN THE BROWSER before finalizing"* gate is marked ⚠️ do-not-skip. **[V — full read of SKILL.md, 196 lines]** Map directly: `layout.json` ← browser editor; `build.ts` = `vectorize.py`; LOCK = `rename_export.py`; the licence step is precedent for Step 8.

Its SKILL.md also states the one-origin rule's reason explicitly: *"Web fonts can't load over `file://` in Chrome → always serve over localhost."*

**Status of the process topology (added in revision).** The *skill shape* above — thin router + TS scripts + a local server + a browser editor — is **settled**. The *process topology* underneath it (one origin with a proxy, versus two origins with an iframe + `postMessage`) is **NOT settled**; it is §17-O4 and is resolved by the spike described in §16.6.1. Everything §16.6 says about the two-process arrangement is therefore written as **candidate architecture**, not architecture of record. See §16.6.2 for the invariants that hold under either outcome — those are the parts an engineer may start building today.

### 16.2 Language: TypeScript on Bun

`/Users/zee/CLAUDE.md` lines 25–46 make TS/Rust the mandatory default for **all** new code; Python is allowed only for (1) editing existing Python, (2) a Python-only library, (3) extending an existing Python hook chain. **None covers a new skill's own server or editor.**

Compliance precedent: `.claude/skills/acos-reverse-cleanroom/scripts/` — 16 `.ts` files with `#!/usr/bin/env bun` shebangs, a `scripts/package.json` (`"type": "module"`, `"Run with bun (no build step)"`, one dependency: `playwright@^1.48.0`), pure decision-logic split into `lib/*.ts` so ~90% is unit-testable, and a `bun selftest.ts` harness reporting 67/67 pass. `acos-research-riffs` has 13 more `.ts`. **[V — `ls`, `head`]**

Against that: **122 `.py` files across project skills, 66 across global skills.** The estate is Python-first; **this skill must not be.** Toolchain verified present: bun 1.3.9 at `/Users/zee/.bun/bin/bun`, node v20.19.3, rustc 1.88.0. **Rust is unnecessary** — nothing here is perf-critical or needs a single binary.

**Python-gravity is a real risk** (§17-R12): the path of least resistance is copying `server.py` and violating the rule. **Mitigation: port `server.py` → `server.ts` first, before any other code, so the TS spine exists from day one.** It is ~105 lines mapping 1:1 onto `Bun.serve()`, which gives native static serving, `Bun.file`, WebSocket upgrade, and streaming with zero dependencies. **A one-hour port, not a rewrite.**

**Scope boundary of the language rule as it applies here (added in revision).** The rule governs the code *this skill authors and ships*. Two things are deliberately distinguished, because §16.6.3's fallback ladder turns on the distinction:

- **The server itself** (routes, doc model, ops, SSE, LOCK compiler, gates) — TypeScript on Bun, non-negotiable, no fallback contemplated.
- **The process-launch shim** (the ~20-line wrapper whose only job is to detach a child so it survives the harness's turn boundary) — TypeScript *by default*, but this is the one place where the only **first-party-proven** recipe is Python (§16.6). If the TS path fails re-proof, §16.6.3 defines an escalation ladder that keeps the server in TS even in the worst case. **The worst case still requires explicit user sign-off** because it invokes a language-rule exception that none of the three written exceptions cleanly covers.

### 16.3 Skill files

```
.claude/skills/acos-website-builder/          ← git-tracked, authored here
  SKILL.md                                     ← thin router, 9 phases
  scripts/
    package.json                               ← type: module, bun, no build
    server.ts                                  ← Bun.serve, fixed port 8820
    launch.ts                                  ← detached-daemon launcher (see §16.6.3 ladder)
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
    probes/
      probe-turn-boundary.ts                   ← §16.6.3 O5 re-proof harness (run BEFORE v1 build)
      probe-task-availability.md               ← §16.5.1 O31 probe recipe (10 min, manual)
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
    gotchas.md                                 ← §16.11
  prompts/
    interview-synthesizer.md
    custom-component-author.md
```

**Installed globally via symlink**, not a copy. `acos-type-forge` exists in both the ACOS repo and `~/.claude/skills/` with byte-identical SKILL.md — **copies, not symlinks** (`ls -la` shows no symlinks anywhere in `.claude/skills/`) **[V]**. Website Builder must be usable from any project but is real code that must be version-controlled. `install.sh` creates the symlink, breaking the drift pattern rather than repeating it.

*(Revision note: `launch.ts` and `scripts/probes/` are new entries; the `gotchas.md` cross-reference was corrected from §16.6 to §16.11, which is where the gotcha table actually lives. `install.sh` remains a `.sh` because it is a two-line symlink installer that must run before any bun-based tooling is assumed present — that is an intentional, stated exception, not drift.)*

### 16.4 Invocation contract

```yaml
disable-model-invocation: true
user-invocable: true
argument-hint: "[--project <path>] [--resume] [--system <name>] [--port 8820] [--content] [--local-gen]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
```

Precedent: `acos-reverse-cleanroom` and `acos-design-variants` both set `disable-model-invocation: true` + `user-invocable: true` + an `argument-hint` **[V — frontmatter reads]**. `Bash` is needed to launch the bun server; `AskUserQuestion` for the interview (`acos-interview` runs its Q&A in the main context precisely because it is interactive).

**Do NOT list `Task` in `allowed-tools`.** `acos-skill-maker/SKILL.md` (~line 109) states: *"Sub-agent spawning is NOT a skill-frontmatter tool. Never add `Agent` or `Task` to `allowed-tools` — the framework ignores it… set `context: fork` and `agent: architect`."* The estate contradicts itself here — `acos-reverse-cleanroom/SKILL.md` line 6 lists `Task` — **treat skill-maker as the authority and do not copy that line.** **[V — both reads]**

**Unresolved consequence of that rule — see §16.5.1.** §14.5 and §16.5 both describe `Task(general-purpose)` being invoked *mid-session, on demand*, hours into a live browser-driven editing session (e.g. the user clicks "add a custom chart"). The frontmatter rule above governs what the skill declares; it does **not**, on its own, explain whether a running session can still issue a `Task` call at an arbitrary later point. §16.5.1 states what is actually known, what is inference, and what the v1 design does so that no named feature depends on the unknown.

**Phase 0 is a mandatory Confirmation Gate.** Both `/Users/zee/CLAUDE.md` and `ACOS 3.0/CLAUDE.md` mandate it. Bake the restatement into SKILL.md rather than relying on the ambient rule, and make the interview itself the confirmation artifact: restate the brief, get an explicit yes, then write anything.

Per-project config at `.acos/config/website-builder.yaml`, mirroring `.acos/config/cleanroom.yaml`: version, default port, breakpoints, direction count (10), variants-per-component (10), artwork count (20), gate thresholds, licence policy tier, publish target — snapshotted to `audit/config-snapshot.yaml` at init.

### 16.5 Agents

**Zero new files in `.claude/agents/`.** `ACOS 3.0/CLAUDE.md` Restricted Files: *"`.claude/agents/` — Agent definitions are infrastructure. Modification requires human approval."* The estate shows agents **are** added in approval batches (12 `rc-*`, 17 `dr2-*`, 9 `ic-*`), but `acos-synthesis-protocol` explicitly avoids it by spawning `Task(general-purpose)` with role prompts in the skill's own `prompts/` dir. **[V]**

Website Builder's agentic surface is small and human-paced (interview synthesis, prompt authoring, custom-component generation), so the general-purpose route is right: zero approval events, zero roster churn.

| Prompt | Purpose | Constraint | Execution mode (v1) |
|---|---|---|---|
| `interview-synthesizer` | Raw answers → structured brief for the prompt template | Returns text; main thread writes | **Inline in the main session** by default; `Task(general-purpose)` only as a context-relief optimisation (§16.5.1) |
| `custom-component-author` | Step-6 novel components against the direction's tokens | Returns code as text; main thread writes (Write is blocked in subagents) | **Inline in the main session** by default; `Task(general-purpose)` only as a context-relief optimisation (§16.5.1) |

#### 16.5.1 How the running session actually produces agent-authored work (resolves the §16.4 / §14.5 contradiction)

**The contradiction, stated plainly.** §16.4 forbids `Task` in `allowed-tools`. §14.5 lists "Agent-authored" as the generation path for a genuinely novel component and specifies `Task(general-purpose)` with a role prompt. §16.5's own table names the same mechanism for interview synthesis. Custom components (Step 6) and interview synthesis are **named, in-scope features**, so the PRD must not leave their execution path undefined.

**What is actually known, and what is inference:**

- **Known [V — quoted]:** skill-maker states the framework *ignores* `Task` in `allowed-tools`; sub-agent spawning is configured with `context: fork` / `agent:`, which describes how a skill is *entered*, not how it spawns work later.
- **Known [V]:** `acos-synthesis-protocol` and §14.5's cited precedent both call `Task(general-purpose)` from skill prose without declaring `Task` in frontmatter — i.e. the estate's working pattern is "call it, don't declare it."
- **Inference (NOT verified):** that `allowed-tools` acts as a *ceiling* on the session's tool surface for the duration of the skill, such that declaring a list without `Task` could suppress a later `Task` call. **This is inference. The PRD does not know whether an `allowed-tools` list suppresses `Task`, and no first-party test of this exists in the estate.** Marked as **§17-O31** (new; mirror into §17.4).

**v1 design decision — remove the dependency rather than bet on the unknown.** In v1, both prompt files are used as **rubrics executed inline by the main Claude session**, not as subagent role prompts:

1. The editor appends the request to `commands.jsonl` (custom-component request, or interview-synthesis request).
2. The main session's `tail -f` loop picks it up (§16.6, zero-token wait).
3. The main session reads `prompts/custom-component-author.md`, produces the component, runs the six coherence lints (§14.5), and writes the file itself with `Write` — which it already has.

This path uses **only tools already declared** in §16.4's `allowed-tools`, so it works regardless of how O31 resolves. It costs main-session context; it does not cost a capability.

**Optimisation, gated on O31.** If the O31 probe shows a running skill session *can* issue `Task(general-purpose)`, the same two jobs may be forked to a subagent purely to protect main-session context — the subagent still returns **text**, and the main thread still writes (subagent `Write` is blocked). This is a performance change, not a functional one, so no feature depends on it.

**O31 probe (cheap, ~10 minutes, `scripts/probes/probe-task-availability.md`):** invoke a throwaway skill with an `allowed-tools` list that omits `Task`, then, after the skill has begun executing, attempt one trivial `Task(general-purpose)` call ("return the string OK"). Record whether the call is available, refused, or silently unavailable. Run before v2 planning; **not** a v1 blocker under the design above.

**Deviation flag — requires user sign-off.** If the user wants agent-authored components to *always* run as a subagent (for context economy or parallelism), the only known way to make that explicit is to add `Task` to this skill's `allowed-tools`, which **contradicts the skill-maker authority quoted in §16.4**. That is a deliberate departure from a house rule and **requires user sign-off**; it is not taken unilaterally by this PRD.

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

**Language conflict to resolve:** the proven launcher is Python; the standing rule mandates TypeScript. The TS equivalent is `child_process.spawn(cmd, args, {detached: true, stdio: 'ignore'}).unref()`, which is **not proven in this harness and must be re-proven with the same curl-across-turn-boundary test** before the PRD assumes it works. See §17-O5 and §16.6.3.

#### 16.6.1 O4 is OPEN: the process topology is a candidate, not a decision

**Explicit status correction (added in revision).** Everything in §16.6.2's "two-process arrangement" was previously written in the register of a settled design — named processes, exact routes, exact responsibilities — while §17-O4 simultaneously lists *"single-origin proxy vs two-origin iframe + postMessage"* as unresolved, to be settled by *"spike both before locking the architecture."* Both cannot be true. **The correction is: O4 stands. §16.6.2 is the leading candidate, documented in detail so the spike has something concrete to test — it is not the architecture of record.**

**The two candidates:**

| | **Candidate A — two origins** | **Candidate B — single origin** |
|---|---|---|
| Shape | `astro dev` on one port renders the site; `wb-server` (Bun) on another serves the editor chrome; site in an `<iframe>`; `postMessage` with explicit `targetOrigin` | One Bun server on 8820 **proxies** `astro dev`; editor chrome and site preview are same-origin |
| Precedent | Onlook / Stackbit / Tina converged on this **[V — Onlook flow quoted below]** | The proxy is a standard pattern but **no first-party in-estate precedent was verified for this product's exact combination** (proxy + SSE + HMR passthrough) |
| Cost | CORS surface, `postMessage` protocol, `targetOrigin` discipline, two lifecycles to supervise | Proxy complexity: must pass through Astro HMR's websocket and not collide with `wb-server`'s own SSE |
| Benefit | Isolation: the site page stays pristine; editor survives an Astro restart | Zero cross-origin surface: no `postMessage` protocol at all; direct DOM access from editor chrome to preview document |
| Risk if wrong | Protocol churn between chrome and preview | HMR websocket breakage inside the proxy; harder to keep the preview DOM free of editor artifacts |

**Spike definition (must run before locking the architecture — this is the O4 answer procedure):** build the *same* two-page vertical slice on both topologies — load a page, select a node, change one text string, swap one component variant, observe HMR, take a headless screenshot of the preview only. Measure: (i) lines of code in the chrome↔preview channel; (ii) whether a preview-only screenshot is achievable without editor chrome in the frame; (iii) HMR round-trip latency; (iv) behaviour after killing and restarting `astro dev`. **Timebox: one working session per topology.** Record the result as an ADR and update this section and §17-O4 together.

**Until the spike lands, an engineer should build only the invariants in §16.6.2 — those are topology-independent.**

#### 16.6.2 Candidate architecture (Candidate A, described in full) and the topology-independent invariants

**Alternative worth spiking:** the single-origin variant — one Bun server proxying `astro dev` — collapses the CORS/postMessage surface to zero at the cost of proxy complexity. Spike both before locking the architecture (procedure in §16.6.1).

**Two-process arrangement — CANDIDATE A, pending §17-O4 (the shape Onlook, Stackbit and Tina all converged on):** Process 1 is `astro dev` on 127.0.0.1 rendering the site with the editor integration (doc write → generator rewrites `src/generated/**` → HMR reloads, ~100–300ms). Process 2 is `wb-server` (Bun) on 127.0.0.1, the single doc writer, exposing `GET /doc` (ETag), `POST /ops`, `GET /events` (SSE), `POST /variants`, `POST /lock`. The editor chrome is a parent page served by `wb-server`; the site renders in an `<iframe>`; the two talk over `postMessage` with an explicit `targetOrigin`. Onlook's published flow is the same shape: load code into a container, container serves it, *"our editor receives the preview link and displays it in an iFrame,"* then instruments the code to map elements to their place in code **[V — quoted]**.

Three concrete wins **(these are the arguments FOR Candidate A, not a statement that A has won)**: the site page stays pristine so **a screenshot of the iframe is a screenshot of the real site with no toolbar in it**; the editor survives an Astro restart without losing unsaved state; and LOCK preview is literally "point the same iframe at `dist/published`."

**Topology-independent invariants — SETTLED, safe to build now regardless of how O4 resolves:**

| Inv. | Invariant | Why it survives either topology |
|---|---|---|
| **I1** | **One writer.** `wb-server` is the only process that writes `layout.json` / `content.json` / `history.jsonl`. Everything else proposes ops. | True whether the preview is proxied or framed |
| **I2** | **The route contract**: `GET /doc` (ETag), `POST /ops`, `GET /events` (SSE), `POST /variants`, `POST /lock`, plus static serving. | Same routes; only the *origin* they are called from changes |
| **I3** | **Semantic ops, never raw file writes** from the browser. | Security posture is origin-independent |
| **I4** | **Preview isolation as a requirement, not a mechanism**: a capture of the preview must contain zero editor chrome. Candidate A gets this from the iframe; Candidate B must achieve it by rendering the preview in its own document/route. | Stated as an acceptance criterion so the spike can score it |
| **I5** | **The editor must survive a preview-process restart** without losing unsaved state (state lives in `wb-server`, not in the preview document). | Independent of topology |
| **I6** | **The dev-preview substrate is itself open (§17-O8: Astro vs plain generated HTML).** Nothing above names Astro except as the current candidate; if O8 resolves to plain HTML, "Process 1" becomes "a static file watcher + reload" and I1–I5 are unchanged. | Explicit so O8 and O4 do not get silently coupled |

**The SSE + JSONL inbox pattern is house doctrine.** `gr-server.py` (2,000+ lines) and its validated port `ic-server.py` implement stdlib `ThreadingHTTPServer`, port written into `state.json`, `GET /state` (ETag/304), `GET /events` SSE with ~15s keepalive, browser commands appended to `commands.jsonl`, `POST /internal/*` for Claude to write back. The guided-reader SKILL.md is explicit: *"Each `tail -f` blocks the bash thread; Claude does not consume tokens while waiting."* **[V — quoted]** The division of labour is settled: **the server is a dumb byte-mover that NEVER calls `Task()`; the Claude session is the only engine.** `riff-server.ts` documents its own rule: *"Read-only by construction: there is no route that writes to the session."*

This is exactly how Step 5 ("10 more variants of this button") and Step 6 ("add a chart") happen without the user leaving the browser, **at zero token cost while they design.**

#### 16.6.3 O5 is a v1 BLOCKER with a defined fallback ladder (added in revision)

**The dependency, stated plainly.** Every editor feature in v1 — the design surface, autosave, SSE, the agent inbox, the zero-token `tail -f` loop — requires a local server that survives Claude's turn boundary. The **only first-party-proven** way to survive it is the **Python double-fork daemon**. The TS equivalent is unproven (§17-O5). §18's v1 "Scope in" list currently states *"Double-fork server + fixed port + curl-across-turn-boundary verification"* as delivered functionality **without conditioning it on O5**. That is corrected here.

**Gate 16-A (new gate; blocking, run before v1 implementation begins).** `scripts/probes/probe-turn-boundary.ts` must be executed and its result recorded in the evidence bundle **before any server-dependent v1 scope is treated as committed.**

*Procedure (identical to the 2026-07-09 first-party test, so the results are comparable):*
1. Launch `server.ts` via the candidate detached-spawn mechanism.
2. `curl --retry 20 --retry-connrefused` → expect HTTP 200 **in the same turn**.
3. **End the turn.**
4. In a **separate, later tool call**, `curl` again → expect HTTP 200, and confirm the pid in `state.json` is still in `ps`.
5. Repeat 3–4 across at least two further turn boundaries, and once across an eternity-protocol `/clear` if one occurs.
*Pass = HTTP 200 at every post-boundary check with the original pid alive. Anything else is a fail.*

**Fallback ladder — take the first rung that passes Gate 16-A.** Each rung is tested with the exact same procedure. Rungs F1–F3 keep 100% of the shipped server in TypeScript; only the *launch shim* differs.

| Rung | Mechanism | Language impact | Status |
|---|---|---|---|
| **F1** | Node/Bun `child_process.spawn(cmd, args, {detached: true, stdio: 'ignore'}).unref()` | Pure TS | **UNPROVEN in this harness** — the thing O5 asks about. Note the 2026-07-09 log line *"Script spawns a detached child and exits → orphan reaped instantly"* is evidence that a naive detach is insufficient; whether `detached:true` + `unref()` differs materially is exactly what the probe answers |
| **F2** | Bun/Node spawn of a **`setsid`-equivalent double-fork implemented in TS** (fork → new session → fork → exec `bun server.ts`) | Pure TS | Unproven. Note gotcha 3 of the original log: **`setsid` does not exist on this Mac**, so the session-leader step must be achieved another way (e.g. a POSIX call through a TS FFI binding, or F3) — **this may not be reachable in pure TS; no known mitigation if the required syscall is not exposed** |
| **F3** | A ~15-line **POSIX `sh` launcher** that performs the double-fork and `exec`s `bun server.ts` | Server is 100% TS; the launcher is shell. **`install.sh` already establishes shell as acceptable glue in this skill** | Unproven but low-risk; **preferred fallback** because it preserves the language rule's intent (no new Python, all product logic in TS) while using the harness-proven *shape* |
| **F4** | Reuse the **proven Python double-fork daemon** purely as a launcher that `exec`s `bun server.ts` | ~20 lines of Python exist in the repo; **all product logic stays TS** | **PROVEN shape** (this is literally the recipe that worked). **Requires user sign-off** — it is a deliberate deviation from the standing TypeScript-only rule, and none of the three written exceptions (existing-Python edit / Python-only library / Python hook chain) cleanly covers a brand-new launcher file. Naming the deviation is mandatory, per the PRD's own rule |
| **F5** | **Redesign the lifecycle so cross-turn survival is not required**: the user runs `bun scripts/server.ts` in **their own terminal** (outside the harness), and the skill only ever *connects* to it — detecting it via `state.json`, and printing a copy-pasteable start command if absent | Pure TS, zero harness dependency | Always available. **Cost: the "one command and a browser opens" experience degrades to a two-step start**, and any resume after `/clear` depends on the user's terminal still running. This is a **UX regression that requires user sign-off** if it becomes the shipped path |

**v1 scope is explicitly conditional (correction to §18).** Read §18's v1 line *"Double-fork server + fixed port + curl-across-turn-boundary verification"* as: **"a launcher that passes Gate 16-A, selected by the §16.6.3 ladder, plus fixed port and cross-turn verification."** If the selected rung is F4 or F5, the deviation must be signed off before v1 build starts, and §18 should be amended to name the chosen rung. **This is the single sequencing rule of the whole plan: run Gate 16-A first; it costs under an hour and it decides whether v1 is buildable as written.**

**Open question tracked (new; mirror into §17.4):**
- **O32 — If every TS rung (F1–F3) fails Gate 16-A, does the user prefer F4 (a ~20-line Python launcher, language-rule deviation) or F5 (manual terminal start, UX deviation)?** **Requires user decision.** The PRD does not choose on the user's behalf; both are deviations from something the user asked for.

**Honest residual:** if F1–F3 all fail *and* the user rejects both F4 and F5, there is **no known mitigation** — the browser-editor premise is incompatible with the harness under those constraints, and the product would have to be rescoped to a non-live-server form (e.g. generate-then-open-a-static-file, losing autosave, SSE and the inbox). This is stated so the risk is visible, not because it is expected.

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

**Device-height pinning applies to capture too (added in revision, ties to gotcha 12).** `--window-size=1440,3000` is a tall capture window chosen to grab a full page in one shot. **Any capture used to judge a viewport-height layout must instead use the pinned device size** (`390×844`, `768×1024`, `1280×800`, `1440×900`), because a 3000px-tall window makes `100vh`/`svh`/`dvh` resolve to 3000px and the hero is judged at a height no device has. Full-page captures remain valid for content review; they are **not** valid evidence for hero framing.

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
| **Detached-daemon launcher (`launch.ts` / rung-dependent)** | **PROVE FIRST, then choose the rung** | Proven shape is the Python double-fork in `acos-guided-reader-server-gotcha.md`; ladder F1→F5 in §16.6.3; **Gate 16-A decides. F4/F5 require user sign-off** |
| **Preview-iframe device-height pinning** | **BUILD NEW (adopt the constraint from Puck's documented default)** | Puck ships all four default viewports at `height: 'auto'` — §11 and gotcha 12; the pinned sizes are 390×844, 768×1024, 1280×800, 1440×900 |
| **Chrome-CLI capture at pinned device sizes** | **Extend the adopted recipe** | §16.7 — `--window-size` must match the pinned device height for any page containing a `vh`/`svh`/`dvh` rule |
| **The VLM judge loop** | **DO NOT PORT** | The human replaced it; porting re-imports the rejected architecture |
| **Autonomous Wigum aesthetic iteration** | **DO NOT PORT** | Same |
| **`.claude/agents/` additions** | **DO NOT ADD** | Human-approval-restricted; `Task(general-purpose)` suffices **where available — v1 does not depend on it, see §16.5.1** |
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
| **Puck** | **MIT, 13,018★, pushed 2026-07-24, actively developed** — genuinely the right philosophy and licence, now positioning as *"the agentic visual editor for your design system"* | **Three gaps, each fatal here:** (1) **no grid-cell placement model** — Puck composes flow lists via slots and *"multi-column layouts using nested components,"* so D2's snap-to-gridlines and Step-4(a) gridlines have no home; (2) **no per-breakpoint override cascade** — viewports resize the iframe but the Data document has no breakpoint dimension; (3) **it is React**, whereas the settled build target is Astro static with zero shipped JS, so components would exist twice. **Mine it for API shapes and possibly vendor individual utilities; do not build the product inside it** **[V — GitHub API + docs read; the three gaps are inference from the docs]**. **Fourth, non-fatal but load-bearing:** all four of Puck's default viewports use `height: 'auto'` **[V — Lens 4]**, which is the source of gotcha 12; adopting Puck's viewport *config shape* without pinning heights would import the bug |

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
| 12 | **The viewport-height trap.** An auto-height preview iframe makes `100vh`/`svh`/`dvh` measure **the iframe's expanded height, not a device's** — so a hero using viewport units is framed and approved in the editor and is wrong on a real phone. Puck ships all four default viewports with `height: 'auto'` **[V — Lens 4]**, and hero is this product's highest-value swap (12 variants, §20.2). **Rule: whenever a page contains any `vh`/`svh`/`dvh` rule, pin the preview iframe to a real device height — 390×844, 768×1024, 1280×800, 1440×900 — and pin the headless capture window to the same size (§16.7).** **Acceptance criterion (feeds §19): for any page containing a viewport-height rule, the measured preview iframe height at each breakpoint equals the pinned device height, and a device-height capture exists in the evidence bundle.** Related: when Puck's compositional `<Puck.Preview />` is used directly the viewports API has no effect at all (§11) — do not assume a viewport config is being honoured; **assert the measured height** |
| 13 | **Do not assume `Task` is callable mid-skill.** Whether an `allowed-tools` list suppresses a later `Task(general-purpose)` call is **unverified** (§17-O31). Any feature that would depend on it must have an inline main-session path (§16.5.1); run `scripts/probes/probe-task-availability.md` before designing around subagents |
| 14 | **A `run_in_background: true` server is not a server.** It binds, curls 200, and is SIGTERM'd (exit 143) at the turn boundary. Anything that must outlive a turn goes through the §16.6.3 launcher; **always prove survival with a second curl in a separate tool call**, never with a same-turn 200 |

**Cross-reference additions made in this revision (must be mirrored into §17 so the ids stay consistent):**

| New id | Where defined | One-line statement |
|---|---|---|
| **O31** | §16.5.1 | Does an `allowed-tools` declaration that omits `Task` suppress a later `Task(general-purpose)` call from a running skill session? **Unverified; probe defined; v1 designed not to depend on it** |
| **O32** | §16.6.3 | If every pure-TS launcher rung (F1–F3) fails Gate 16-A, does the user choose F4 (small Python launcher, language-rule deviation) or F5 (manual terminal start, UX deviation)? **Requires user decision** |
| **Gate 16-A** | §16.6.3 | Cross-turn-boundary server survival proof; **blocking; must run before v1 server-dependent scope is treated as committed** |

**Sign-off items surfaced by this revision (none may be taken silently):**

1. **§16.6.3 F4** — reusing a ~20-line Python double-fork launcher would deviate from the standing TypeScript-only rule. **Requires user sign-off.**
2. **§16.6.3 F5** — a manual, user-terminal server start would deviate from the "one command and the browser opens" experience. **Requires user sign-off.**
3. **§16.5.1 deviation flag** — mandating subagent execution for custom components would require adding `Task` to `allowed-tools` against the skill-maker authority. **Requires user sign-off.**
4. **§16.6.1** — locking either topology (Candidate A or B) before the spike runs would be a decision the PRD has not earned. **Requires the spike, then an ADR.**

---

