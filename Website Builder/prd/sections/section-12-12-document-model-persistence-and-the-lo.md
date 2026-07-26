## 12. Document model, persistence, and the LOCK/UNLOCK contract

### 12.1 Two-tier truth (the highest-leverage architectural decision in the PRD)

| Tier | What | Owner | Notes |
|---|---|---|---|
| **Composition** | Which component, which variant, order, slot, anchor, prop values, text | `pages/<id>.doc.json` (+ `content.json`) — **the only thing the editor mutates** | A scene graph |
| **Implementation** | `.astro` component sources, `tokens.json` (DTCG) + compiled `tokens.css`/Tailwind `@theme`, art assets | Real files on disk, versioned, arriving from the Step-3 hand-carry | Claude edits these |
| **Rendered site** | `.astro` page files under `src/generated/**` | Produced by a pure function `render(doc, systemLock, library) -> files` | **Never parsed back into JSON** |

**Rejecting HTML→JSON round-tripping is what makes drift structurally impossible rather than merely managed.** Every product that reconstructs a doc from rendered markup is lossy at exactly the places that matter — anchors, variants, intent. This is also the canonical WYSIWYG failure (Dreamweaver design view, FrontPage, Muse): the editor parses source into a DOM, the user edits, the editor re-serialises, and comments vanish, formatting normalises, hand-tuned CSS is rewritten. **Worse here, because Claude is also writing this source** — the next read sees reformatted markup it did not write, with its own comments gone, and diffs become unreviewable.

It also makes D1 cheap: swapping a variant is a single JSON field change, and "10 more variants" is a library operation, not a page rewrite.

**Prior art split.** Family A (JSON doc + pure render): Puck `{content[], root, zones}`, Craft.js, Builder.io. Family B (files-as-truth + annotation mapping): TinaCMS, Netlify/Stackbit Visual Editor, Onlook. **Anti-patterns:** Webflow export drops CMS collections, forms, site search, password protection and localisation — collection lists render empty, template pages don't generate. Framer ships no HTML export at all. Both are one-way doors, and D3 requires reversibility. **[V — puckeditor.com, builder.io, docs.netlify.com, tina.io, github.com/onlook-dev/onlook; Webflow gaps from brixtemplates/memberstack/thecssagency analyses, consistent across sources]**

### 12.2 The file set

| File | Purpose |
|---|---|
| `site.json` | Project record: formatVersion, projectId (ULID), breakpoints, grid, page list, and `systemLock {directionId, systemVersion, tokensSha256, librarySha256, source, importedAt}`. **The systemLock is what makes a re-run of Step 3 unable to silently change what a page renders** |
| `pages/<id>.doc.json` | The scene graph. Node: `{id, component, variant, region, layout, props, slots, text, override, locked, notes}`. **Serialised with stable key order, 2-space indent, one array element per line** — that formatting decision alone determines whether the git history is useful |
| `content.json` | Copy, separated so a content-only edit path exists |
| `history.jsonl` | Append-only op log: `{seq, ts, actor: 'user'\|'agent', op, target, patch: [RFC6902], inverse: [RFC6902], label}` |
| `system.lock.json` | Pins the imported direction like a package-lock: id, version, per-file hashes of tokens and every component |
| `assets/manifest.json` | Per-asset provenance and licence. **Also the allowlist the generator validates every asset reference against**, closing the hallucinated-URL class |
| `provenance.json` | Per component instance: direction id, variant id, generation timestamp, prompt hash |
| `inbound/import-report.json` | Per-item accept/reject/quarantine with reason and offending snippet |
| `.wb/inbox.jsonl` | Append-only agent intent channel |
| `.wb/editor.lock` | Single-writer pid + mtime heartbeat |
| `.wb/editor.token` | Per-session bearer token, mode 0600 |
| `lock-manifest.json` | Written at LOCK; records the layout hash so unlock can diff against hand-edits |

### 12.3 The layout node — where D2 lives

```json
{
  "id": "n_hero_art",
  "component": "ArtContainer",
  "variant": "background-scene@07",
  "layout": {
    "default": { "mode": "flow", "col": { "start": 1, "span": 12 },
                 "align": "stretch", "spaceBefore": "space-l", "spaceAfter": "space-xl" },
    "lg":      { "col": { "start": 2, "span": 10 } }
  },
  "props": { "motion": "entrance.mask-wipe@03", "aspect": "16:9",
             "focalPoint": { "x": 0.5, "y": 0.4 } },
  "text": {}, "slots": {}, "locked": false
}
```

Free-position escape hatch: `{ "mode": "free", "anchor": { "to": "parent"|nodeId, "edge": "top-left" }, "offset": { "x": "12%", "y": "clamp(1rem, 4vw, 3rem)" }, "z": 2 }`.

Per D4, **motion is not a separate structure** — an animated piece is an `ArtContainer` node whose `props.motion` is a token/preset id, manipulated identically to a static art container.

Borrow Puck's proven conventions: a `root` node with its own props, **named slots rather than the deprecated `zones` string-key hack** (`"HeadingBlock-1234:my-content"` — Puck deprecated exactly this in favour of slot fields, so start where they ended up), and ids that encode component type for debuggability.

### 12.4 DOM ↔ doc mapping

Copy Stackbit's annotation scheme **including its scoping rule**. Netlify Visual Editor's annotations are *"HTML data attributes … so that the visual editor can map content in the preview to the correct document and field"*; `data-sb-object-id` identifies the document *"along with all descendants of that element in the DOM tree"*; `data-sb-field-path` gives the path to the field. **Scoping-by-descent is the important detail** — annotate once at the node boundary and inherit. **[V — docs.netlify.com, quotes verbatim]**

Our attributes: `data-wb-node` (scopes descendants), `data-wb-field` (marks inline-editable), `data-wb-slot` (drop region), `data-wb-variant` (what the component bar reads), `data-wb-layout` / `data-wb-anchor` (what the drag handler reads). **All emitted only under `import.meta.env.WB_DESIGN`; all asserted absent from `dist/published`.**

Astro gives DOM→source-file mapping for free: it injects `data-astro-source-file` and `data-astro-source-loc` in development only (a filed issue confirms they appear in dev even when `devToolbar` is disabled — gated on dev, not on the toolbar). **[V — withastro/astro issue #9324; astro-click-to-source integration]** So no Babel instrumentation is needed.

### 12.5 The LOCK/UNLOCK contract (D3, settled)

**LOCK is a re-render, never a copy-and-strip.** Same renderer, `editor: false`. The FruitSync precedent proves what copy-and-strip costs: the release required rewriting every `/a01/` link to `/` and manually excluding the dev variant-chooser and four dev mockup pages from the shipped folder **[V — DEPLOY-STEPS.md]** — which is exactly the leakage D3 exists to prevent.

**Five layered enforcement mechanisms, four of them documented Astro/Vite features:**

1. **Two configs, two commands, two outDirs.** `astro dev --config astro.design.mjs` vs `astro build --config astro.publish.mjs --outDir dist/published`. **Only the design config registers the editor integration**, so the editor is not in the publish build graph at all.
2. **`astro:config:setup` receives `command: 'dev'|'build'|'preview'|'sync'` and `injectScript(stage, content)`.** Gating on `command === 'dev'` is the documented dev-only injection pattern.
3. **`addDevToolbarApp(entrypoint)`** for editor chrome. Astro's docs state the toolbar *"is a development tool only and will not appear on your published site"* — which makes the component bar, grid toggle and save button a class of UI that **physically cannot leak**.
4. **`import.meta.env.WB_DESIGN` guards** for anything inside a component. Vite statically replaces `import.meta.env.*` at build time so the dead branch is eliminated — **but the gotcha is real and filed (vite#15256): if the variable is undefined the branch may NOT be shaken.** `WB_DESIGN` must be explicitly defined as `false` in the publish config's `vite.define`.
5. **`astro:build:done`** receives `dir` (URL), `pages` (`{pathname}[]`) and `assets` (`Map<string, URL[]>`) — enough to post-scrub every emitted HTML file and then assert.

**[V — docs.astro.build integrations reference + dev-toolbar guide, direct quote; vite.dev env-and-mode; vitejs/vite #15256]**

**The gate is an executable assertion, not a claim.** `wb lock` = build → scrub → assert → snapshot:

| Gate | Check |
|---|---|
| 1 | Grep `dist/published/**` for `data-wb-`, `wb-editor`, `astro-dev-toolbar`, `data-astro-source-file`, `data-astro-source-loc`, `/@vite/client`, `import.meta.hot`, the editor token filename. **Any hit fails the build** |
| 2 | **Byte-equality**: build the same doc twice — once with the editor integration installed, once with it removed from `package.json` entirely — and require the two trees to be byte-identical. **This converts "the editor doesn't ship" from an intention into a CI fact** |
| 3 | `dist` JS byte-size assertion (an accidental editor import shows up as a step change) |
| 4 | Screenshot diff between editor-preview-at-1280 (chrome hidden) and built-page-at-1280 — proves LOCK changed nothing visual, and catches the residual case where a `data-wb-*` attribute participated in a CSS selector or affected intrinsic size |
| 5 | **Interaction-manifest check**: walk every declared motion/interaction behaviour against `dist/published` to prove it exists in shipped code. This is the Webflow-export lesson applied to a static target — no behaviour may exist only as editor state |

**LOCK is non-mutating.** It writes only `dist/published/` and `.wb/locks/<iso>/` (an immutable snapshot: every `*.doc.json`, `system.lock.json`, the dist hash, the scrub output, `lock-manifest.json`), then `git tag wb-lock/<n>`. **The editable project is untouched, so UNLOCK is nothing more than restarting the design server — there is no unlock transformation to get wrong.**

Going back to an older lock is `git checkout wb-lock/<n> -- pages/ site.json` (documents only, never `dist/`), which cannot lose manual code because manual code lives in human-owned zones the checkout does not target.

### 12.6 State-loss ledger (what LOCK/UNLOCK must explicitly handle)

| # | Lost / breaks | Handling |
|---|---|---|
| 1 | Undo/redo history (in-memory) | Persist as a capped operation log alongside `layout.json`; every save is a git commit so cross-session undo has an answer |
| 2 | Selection and scroll position | Persist in `.wb/session-ui.json` |
| 3 | Per-breakpoint override provenance if flattened into final CSS | LOCK is a re-render from the doc, so provenance lives in the doc and is never flattened away |
| 4 | Free-position pixel baselines (the viewport they were authored at) | Anchored-offset stores percentages, so there is no pixel baseline to lose |
| 5 | Placeholder flags on unfilled slots | Placeholders are a **typed state that blocks LOCK** |
| 6 | Hand-edits to the exported tree, silently overwritten on unlock | `lock-manifest.json` records the layout hash; unlock **diffs the exported tree and shows hand-edits** instead of discarding them |
| 7 | Editor scaffolding leaking into the shipped site | Killed by re-render + the five gates |
| 8 | Rich text pasted with `<span style=…>` and `<b>` from the source app | `contenteditable="plaintext-only"`; content stored as plain strings |
| 9 | Absolute `http://localhost:4321/...` URLs baked at design time | Post-ingest and pre-lint pass strips absolute local URLs |

### 12.7 Ownership zones and conflict handling

Copy Plasmic's owned/managed split verbatim. Plasmic emits two files per component: `plasmic/PlasmicButton.tsx` is *"owned by Plasmic, and shouldn't be edited by you. As you iterate … these files will be updated when you run plasmic sync"*; `Button.tsx` is the wrapper, for which Plasmic *"generates an initial scaffold"* and *"never touches it again."* **[V — docs.plasmic.app/learn/codegen-components, direct quotes]** This is the mechanism that makes a codegen product a tool rather than a toy.

| Zone | Paths | Writer |
|---|---|---|
| **Machine-owned** (regenerated wholesale) | `src/generated/**`, `src/styles/tokens.css` | The generator only |
| **Human/agent-owned** (never written after scaffold) | `src/pages/*.astro` thin wrappers, `src/overrides/**`, `src/lib/**` | Claude and the user |
| **Doc-owned** | `pages/*.doc.json`, `content.json`, `history.jsonl`, `site.json` | The editor process only |

**Enforcement:** `.gitattributes` marks `src/generated/** linguist-generated=true -diff` (GitHub collapses those diffs; `-diff` also hides them from the CLI) **[V — github/linguist behaviour]**; a pre-commit hook rejects a commit touching `src/generated/**` without a corresponding doc change; the generated banner names the file to edit instead; **a PreToolUse hook blocks Claude's `Write`/`Edit` on editor-owned files.

**When an illegal edit happens anyway, do not attempt a three-way merge.** Run `wb extract-override <nodeId>`, which lifts the current generated fragment into `src/overrides/<nodeId>.astro`, sets `node.override` in the doc, and re-points the generator to emit `<Override/>`. That turns an illegal edit into a legal, permanently-surviving one. This is Plasmic's split applied at node granularity.

**Overrides accumulate, and that is a real cost.** Each `src/overrides/<nodeId>.astro` is a piece of the page that no longer responds to variant swaps or token changes, so a heavily-overridden page quietly stops being a design-system site. The editor shows a visible override count and `wb doctor` warns above a threshold.

### 12.8 Determinism and drift control

Generation must be a **pure function of `(doc, system.lock.json, generator version)`**. Every generated file carries a header banner with `@generated`, `doc-sha256`, `system-lock-sha256`, `generator-version` — and **no timestamp** (a timestamp in the file body destroys determinism and pollutes every diff; put run metadata in a sidecar).

Two checks fall out:

- `wb verify` regenerates into a temp dir and `diff -r`s against `src/generated/**`. **Empty diff proves both determinism and that nobody hand-edited machine-owned files.** Run on editor start, before LOCK, and in CI.
- On editor start, a hash mismatch means someone hand-edited generated output.

**Determinism hazards to design out up front:** map/object iteration order (sort keys), absolute paths in output (relative only), locale-dependent sorting (fixed collator), random ids (derive node ids from a ULID stored in the doc, never regenerate).

**This is the load-bearing assumption of the whole drift story.** Any nondeterminism makes `wb verify` produce false positives, users learn to ignore it, and the guarantee silently dies.

### 12.9 History: op log + snapshots + git, and NOT a CRDT

Three layers with distinct jobs:

| Layer | Mechanism | Job |
|---|---|---|
| **a** | `history.jsonl`, append-only, one line per user action with `patch` and `inverse` as RFC 6902 JSON Patch | Undo = apply `inverse`; redo = apply `patch`. Plain diffable text; doubles as the agent-vs-human audit trail |
| **b** | Atomic doc writes — write temp then `fs.rename`, debounced ~300ms | A `kill -9` leaves either the pre-op or post-op file, never a truncated one |
| **c** | Git commits at **milestones only** (LOCK, variant-set import, named checkpoint, session end), `git tag wb-lock/<n>` per lock | Durability, and history stays readable |

**Reject CRDTs (Yjs, Automerge, Loro).** There is one human plus a sequential agent; concurrent multi-writer merge buys nothing and costs an opaque binary doc git cannot diff. Use a single-writer `.wb/editor.lock` (pid + mtime heartbeat) and route agent writes through the inbox instead.

### 12.10 Two writers, one lock

**Failure scenario, near-certain:** the editor is open with unsaved drags in memory. The user, in the terminal, asks Claude "make the features section tighter." Claude rewrites the section and, if it touches layout, writes `layout.json`. The browser holds stale state; the user hits Save; the browser clobbers Claude's change — or Claude clobbers the drags on the next reload. **Either way the loser's work vanishes silently.**

| Mitigation | Mechanism |
|---|---|
| **Single writer by file ownership** | §12.7, enforced by a PreToolUse hook |
| **Optimistic concurrency** | Every save carries the mtime/hash the client loaded; the server rejects a stale write with **409** and the editor shows "the file changed on disk — reload or force" |
| **Every save is a commit** | Auto-commit `layout.json` on save to a `design/` branch, squash on lock, so "undo the last thing" has a real answer across sessions |
| **Agent inbox** | Agents append intents to `.wb/inbox.jsonl`; the editor process is the single writer that validates, applies, appends to `history.jsonl` with `actor: 'agent'`, and pushes over SSE. Same typed ops as the UI, so **one code path for both** |

The FruitSync precedent gives no help here: that site tree is not under version control at all (`fatal: not a git repository`) **[V]**, so there is no rollback of any kind today. **`git init` at Step 0, no exceptions.**

### 12.11 Session state on disk

```
.acos/website-builder/sessions/WB-<ts>-<slug>/
  00-interview/{answers.json, concept.md}
  01-prompt/{stage-a.md, stage-b-<id>.md, artwork.md}
  02-system/{<directionId>/…, manifest.json, import-report.json, system.lock.json}
  03-selection/{tournament-log.json, picks.json}
  04-site/{site.json, pages/*.doc.json, content.json, provenance.json, assets/manifest.json}
  05-variants/
  06-custom/
  07-lock/{dist/, lock-manifest.json, gate-report.json, screenshots/}
  evidence/
  audit/config-snapshot.yaml
  state.json      ← {phase, step, awaiting, nextAction, port, pid, url, sessionId}
  events.jsonl
  ACTIVE          ← marker written at init, removed at close
.acos/website-builder/systems/<name>/{system.json, tokens.css, compliance-report.json, provenance}
.acos/website-builder/sessions/*/site/   ← in ACOS .gitignore, its own nested git repo
```

**The phase frontier is recomputed from which directories are populated and which gates passed — never from conversation memory.** The principle is stated best in the in-repo `acos-axiom-synthesis/STATE-MACHINE.md`: frontier is *"Computed purely from on-disk state, so the run is resumable by re-reading the ledger."* **[V — in-repo, line 66]** The `.current-session` pointer convention already exists at `.acos/sessions/loan-doc-finder/.current-session` **[V — verified by `ls`]**.

**`site/` must be its own git repo (or worktree), and the path must be in the ACOS `.gitignore`** — otherwise every drag operation pollutes ACOS history and every LOCK tag collides with ACOS tags, making the version-history layer unusable within a single session.

### 12.12 Local server security — localhost is NOT a trust boundary

This is the single most under-rated risk in the product.

**CVE-2025-24010 (Vite):** *"Vite allowed any websites to send any requests to the development server and read the response due to default CORS settings and lack of validation on the Origin header for WebSocket connections,"* and the advisory states explicitly that it *"applies to users that only run the Vite dev server on the local machine and does not expose the dev server to the network."* Fixed in 6.0.9 / 5.4.12 / 4.5.6. Separately, **CVE-2025-30208** let `?raw??` bypass `server.fs.deny` for arbitrary file read (that one only affected `--host`-exposed servers — which is why ours never is). Vite's own docs warn that `server.allowedHosts: true` *"allows any website to send requests to your dev server through DNS rebinding attacks, allowing them to download your source code and content."* **[V — GHSA-vg6x-rcgg-rjx6, GHSA-x574-m823-4x7w, vite.dev/config/server-options, quotes verbatim]**

**Required posture:**

| # | Control |
|---|---|
| 1 | Bind `127.0.0.1` explicitly, **never** `0.0.0.0` |
| 2 | Validate `Origin` on **every non-GET and on the SSE/WS upgrade** against a two-entry allowlist |
| 3 | `Access-Control-Allow-Origin` set to the exact editor origin, **never `*`** |
| 4 | **A per-session bearer token** — 32 random bytes, `.wb/editor.token` mode 0600, injected into the editor page at render, sent as `Authorization`. **This is what actually defeats DNS rebinding and drive-by CSRF** |
| 5 | Pin `vite.server.allowedHosts` to the explicit host; pin Vite ≥ 6.2.3 |
| 6 | Heartbeat from the editor page; exit after N idle minutes — **a forgotten dev server left running for days is the realistic exposure, not a targeted attack** |

**In-repo gap to not copy:** `ic-server.py` binds `127.0.0.1` correctly but performs **no Origin check on `do_POST`** **[V — grep, lines 107/156/187]**.

### 12.13 The write endpoint is an arbitrary-file-write primitive unless constrained

Two rules make it safe by construction:

1. **The client never sends a file path or a file body.** It sends a **typed semantic op** (`{op: 'swap-variant', node: 'n_hero', variant: 'hero-split@3'}`) and the server derives the JSON Patch. **Raw-JSON-Patch-over-HTTP is nearly as dangerous as raw paths** because `add`/`replace` on an arbitrary pointer can rewrite `systemLock` or inject an `override` path. Validate every op against a schema **and** against the component library before applying.
2. **The server may write exactly three path shapes** — `pages/*.doc.json`, `history.jsonl`, `.wb/**` — resolved with `realpath`, asserted `startsWith(sessionRoot)`, symlinks rejected. Everything else (generated files, dist) is written by the generator process from the doc, not by an HTTP handler.

### 12.14 The Step-3 importer is an unauthenticated code-import channel

Pasting component code and tokens back from claude.ai means arbitrary code lands in `src/`, is evaluated by `astro dev`, and is bundled into the published site. Treat it as untrusted input.

A forgiving parser (fenced-block extraction, per-item) feeds a strict validator that **rejects or quarantines** any item containing `fetch(`, `eval(`, `new Function`, `import(` of non-local specifiers, `process.`, `child_process`, remote `<script src>`, remote `@import`/`url()` in CSS, or inline event handlers; plus a schema check that `tokens.json` is valid DTCG.

Two secondary reasons this matters beyond security: **(a)** partial or malformed paste-backs will happen on most runs, and a hard-failing importer stalls the pipeline at paste #1, so per-item accept/reject with a "retry just these three" prompt is a **functional requirement**; **(b)** remote font/asset URLs sneaking in breaks offline determinism and the Step-8 licence evidence bundle.

### 12.15 The File System Access API is not a viable persistence path

`showDirectoryPicker()` requires a secure context (localhost qualifies) and a user gesture, but **Safari ships only the Origin Private File System (no directory picker) and Mozilla published a "harmful" position**; the documented Firefox fallback is `<input type="file">` for reads and `<a download>` for writes. A browser-writes-to-disk design would silently be Chrome-only and would still need a server fallback. **[V — MDN showDirectoryPicker, developer.chrome.com, WICG spec]** Keep it as an optional convenience (e.g. "export lock bundle to a folder"); the local server is the single persistence path.

---

