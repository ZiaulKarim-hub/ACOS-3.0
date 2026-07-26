## 12. Document model, persistence, and the LOCK/UNLOCK contract

### 12.1 Two-tier truth (the highest-leverage architectural decision in the PRD)

| Tier | What | Owner | Notes |
|---|---|---|---|
| **Composition** | Which component, which variant, order, slot, anchor, prop values, text | `pages/<id>.doc.json` (+ `content.json`) — **the only thing the editor mutates** | A scene graph |
| **Implementation** | `.astro` component sources, `tokens.json` (DTCG) + compiled `tokens.css`/Tailwind `@theme`, art assets | Real files on disk, versioned, arriving from the Step-3 hand-carry | Claude edits these |
| **Rendered site** | `.astro` page files under `src/generated/**` | Produced by a pure function `render(doc, systemLock, library) -> files` | **Never parsed back into JSON** |

**Rejecting HTML→JSON round-tripping is what makes drift structurally impossible rather than merely managed.** Every product that reconstructs a doc from rendered markup is lossy at exactly the places that matter — anchors, variants, intent. This is also the canonical WYSIWYG failure (Dreamweaver design view, FrontPage, Muse): the editor parses source into a DOM, the user edits, the editor re-serialises, and comments vanish, formatting normalises, hand-tuned CSS is rewritten. **Worse here, because Claude is also writing this source** — the next read sees reformatted markup it did not write, with its own comments gone, and diffs become unreviewable.

It also makes D1 cheap: swapping a variant is a single JSON field change, and "10 more variants" is a library operation, not a page rewrite.

**`render` is total, not partial.** Declaring the doc the only truth and the renderer a pure function creates an obligation the original draft left unstated: **every `component` / `variant` / `motion` / `asset` / token id in the doc must resolve against the library, and the PRD must say what happens when one does not.** This is not a corner case — it is the *normal* consequence of the user's own Step 5 ("if nothing looks good, generate a brand-new design-system prompt"), of restoring an older lock, and of the v2 cross-direction swap in §18. The full resolution and migration policy is **§12.16**, and it is normative: a renderer that silently emits a hole, or an editor that hard-crashes on open, are both failures.

**Prior art split.** Family A (JSON doc + pure render): Puck `{content[], root, zones}`, Craft.js, Builder.io. Family B (files-as-truth + annotation mapping): TinaCMS, Netlify/Stackbit Visual Editor, Onlook. **Anti-patterns:** Webflow export drops CMS collections, forms, site search, password protection and localisation — collection lists render empty, template pages don't generate. Framer ships no HTML export at all. Both are one-way doors, and D3 requires reversibility. **[V — puckeditor.com, builder.io, docs.netlify.com, tina.io, github.com/onlook-dev/onlook; Webflow gaps from brixtemplates/memberstack/thecssagency analyses, consistent across sources]**

### 12.2 The file set

| File | Purpose | Writer |
|---|---|---|
| `site.json` | Project record: formatVersion, projectId (ULID), breakpoints (the key vocabulary of §12.3), grid, page list, per-page SEO/meta, and `systemLock {directionId, systemVersion, tokensSha256, librarySha256, source, importedAt}`. **The systemLock is what makes a re-run of Step 3 unable to silently change what a page renders** | Editor process, via typed ops only (§12.13) |
| `pages/<id>.doc.json` | The scene graph. Node: `{id, component, variant, region, layout, props, slots, text, override, locked, notes, variantMigrated?, orphaned?}`. **Serialised in the canonical form of §12.9** — that formatting decision alone determines whether the git history is useful | Editor process |
| `content.json` | Copy, separated so a content-only edit path exists (§15's "90% of month-six edits are copy changes" path) | Editor process; also the content-only CLI |
| `history.jsonl` | Append-only op log: `{seq, ts, actor: 'user'\|'agent', op, target, patch: [RFC6902], inverse: [RFC6902], label}` | Editor process |
| `system.lock.json` | Pins the imported direction like a package-lock: id, version, per-file hashes of tokens and every component | Importer (Step 3) and `wb migrate` only |
| `assets/manifest.json` | Per-asset provenance and licence. **Also the allowlist the generator validates every asset reference against**, closing the hallucinated-URL class. Records the exact encoder + settings used for each derived asset (§12.8 hazard 5) | Editor process (asset/media manager) and the importer |
| `provenance.json` | Per component instance: direction id, variant id, generation timestamp, prompt hash | Editor process |
| `inbound/import-report.json` | Per-item accept/reject/quarantine with reason and offending snippet | Importer process only |
| `migration-report.json` | Written by `wb migrate` (§12.16): every reference that changed, its old and new value, and the rule that decided it | `wb migrate` only |
| `.wb/inbox.jsonl` | Append-only agent intent channel | Any agent (append-only) |
| `.wb/editor.lock` | Single-writer pid + mtime heartbeat | Editor process |
| `.wb/editor.token` | Per-session bearer token, mode 0600 | Editor process |
| `.wb/doc-hashes.json` | Journal of `{path, sha256, mtimeMs, seq}` for every doc-owned file **as the editor last wrote it**. The reconciliation input that turns an out-of-band write into a visible conflict rather than a silent clobber (§12.10) | Editor process |
| `.wb/session-ui.json` | Selection, scroll position, open panels, active breakpoint key | Editor process |
| `.wb/locks/<iso>/` | Immutable per-LOCK snapshot: every `*.doc.json`, `site.json`, `content.json`, `system.lock.json`, `assets/manifest.json`, the dist hash manifest, the scrub output, `lock-manifest.json`, `gate-report.json` | `wb lock` only |
| `lock-manifest.json` | Written at LOCK; records the layout hash **and a SHA-256 per emitted file in `dist/published/`** so unlock can diff against hand-edits (§12.6 row 6) | `wb lock` only |
| `package.publish.json` + `package-lock.publish.json` | The editor-free dependency set used by purity gate 2, generated by `wb lock` and **committed**, so gate 2 is not itself a network-variable step (§12.5) | `wb lock --refresh-publish-manifest`, reviewed by a human |

### 12.3 The layout node — where D2 lives

**Breakpoint key vocabulary (normative, and shared by §10.1's switcher, §11.3's cascade, §11.4's free-position rules, this schema, and the §13 gates).** The original draft of this section carried an `lg` key that narrowed a 12-column default to 10 — a *mobile-first* base with a *larger*-breakpoint override, which is the exact inverse of §11.3's normative verdict ("desktop-down cascade with sparse per-breakpoint overrides"). §11.3 wins; §12.3 is corrected here, because §12.3 is the save format and an inverted save format inverts every page.

| Key | Compiles to | Grid tracks (§11.1) | Switcher label (§10.1) | Preview width | Notes |
|---|---|---|---|---|---|
| `base` | No media query — emitted unconditionally | 12 | `1280` and `full` | 1280×800 pinned when the page has any `vh`/`svh`/`dvh` rule; `full` previews the same `base` rules at the browser's own width | **The authored default is the desktop layout.** There is no key above `base` in v1 |
| `md` | `@media (max-width: 991px)` | 6 | `768` | 768×1024 | Boundary taken from the Webflow tablet breakpoint cited in §11.3's table; 768 sits inside it |
| `sm` | `@media (max-width: 479px)` | 4 | `390` | 390×844 | Boundary taken from the Webflow mobile-portrait breakpoint cited in §11.3; **identical to the ≤479px auto-demote boundary in §11.4 rule 4**, which is why they are one number and not two |

Emission order is `base`, then `md`, then `sm`, so the narrower rule always wins by source order without `!important` and without specificity games. **A node with no `sm` entry compiles to `grid-column: 1 / -1` at `sm`** — §11.3's single most load-bearing rule, and the one that prevents the documented Squarespace overlap epidemic. That rule is only reachable because overrides attach *downward*.

> **[I — inference, flagged]** The pairing of *boundary* (991/479, from §11.3's cited Webflow row) with *preview width* (768/390, from §10.1's switcher) is a reconciliation this PRD is making, not a figure quoted from a source. It is chosen because it makes both existing statements true simultaneously. If the user prefers the boundaries to equal the preview widths (768/390), that is a one-line change here and in §11.4 rule 4 — but it must be changed in **all four** places at once, and it is **O31** below.

> **Deviation requiring user sign-off.** v1 ships **no wide/`xl` tier** (no override band above 1280). §10.1's switcher has a `full` entry, which previews `base` at the browser width but cannot carry its own overrides. If the user expects to art-direct a distinct ≥1440 layout, that is an added key (`wide`, `@media (min-width: 1440px)`) and the *only* upward override in the system — an explicit exception to the desktop-down rule that would need its own cascade note. **Not assumed. Requires user decision (O32).**

```json
{
  "id": "n_hero_art",
  "component": "ArtContainer",
  "variant": "background-scene@07",
  "layout": {
    "base": { "mode": "flow", "col": { "start": 2, "span": 10 },
              "align": "stretch", "spaceBefore": "space-l", "spaceAfter": "space-xl" },
    "md":   { "col": { "start": 1, "span": 6 } }
  },
  "props": { "motion": "entrance.mask-wipe@03", "aspect": "16:9",
             "focalPoint": { "x": 0.5, "y": 0.4 } },
  "text": {}, "slots": {}, "locked": false
}
```

Read it as: on desktop the art sits in columns 2–11 of a 12-track grid; at ≤991px it takes all 6 tracks; at ≤479px it has **no entry at all**, so it compiles to `grid-column: 1 / -1` on the 4-track grid. Sparse, downward, and the mobile default is the safe one.

`base` is mandatory on every node. `md`/`sm` are optional and are written **only** when the user actually overrides at that size — which is what makes "every overridden property shows an *overridden here* dot and a one-click reset" (§10.1) implementable as a key-presence test rather than a value comparison.

Free-position escape hatch (§11.4, v2): `{ "mode": "free", "anchor": { "to": "parent"|nodeId, "edge": "top-left" }, "offset": { "x": "12%", "y": "clamp(1rem, 4vw, 3rem)" }, "z": 2 }`. It is a per-key value like any other, so a node may be `free` at `base` and absent at `sm` — which is exactly how §11.4 rule 4's auto-demote is represented: **absence at `sm` means flow at `sm`.**

Per D4, **motion is not a separate structure** — an animated piece is an `ArtContainer` node whose `props.motion` is a token/preset id, manipulated identically to a static art container.

Borrow Puck's proven conventions: a `root` node with its own props, **named slots rather than the deprecated `zones` string-key hack** (`"HeadingBlock-1234:my-content"` — Puck deprecated exactly this in favour of slot fields, so start where they ended up), and ids that encode component type for debuggability.

### 12.4 DOM ↔ doc mapping

Copy Stackbit's annotation scheme **including its scoping rule**. Netlify Visual Editor's annotations are *"HTML data attributes … so that the visual editor can map content in the preview to the correct document and field"*; `data-sb-object-id` identifies the document *"along with all descendants of that element in the DOM tree"*; `data-sb-field-path` gives the path to the field. **Scoping-by-descent is the important detail** — annotate once at the node boundary and inherit. **[V — docs.netlify.com, quotes verbatim]**

Our attributes: `data-wb-node` (scopes descendants), `data-wb-field` (marks inline-editable), `data-wb-slot` (drop region), `data-wb-variant` (what the component bar reads), `data-wb-layout` / `data-wb-anchor` (what the drag handler reads), `data-wb-bp` (which breakpoint key produced the resolved placement, so the "overridden here" dot has a DOM-side source). **All emitted only under `import.meta.env.WB_DESIGN`; all asserted absent from `dist/published`.**

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

**The gate is an executable assertion, not a claim.** `wb lock` = build → scrub → assert → snapshot. **Gates 1–5 keep their existing numbers** (they are cross-referenced from §13.4 row 27 and from §10.1's "Lock verification gates" row); gates 6–8 are additions.

| Gate | Check |
|---|---|
| 1 | Grep `dist/published/**` for `data-wb-`, `wb-editor`, `astro-dev-toolbar`, `data-astro-source-file`, `data-astro-source-loc`, `/@vite/client`, `import.meta.hot`, the editor token filename. **Any hit fails the build** |
| 2 | **Byte-equality**: build the same doc twice — once with the editor integration installed, once with it removed from `package.json` entirely — and require the two trees to be byte-identical. **This converts "the editor doesn't ship" from an intention into a CI fact.** Mechanism, preconditions and budget are specified below; without them this gate is unbuildable |
| 3 | `dist` JS byte-size assertion (an accidental editor import shows up as a step change) |
| 4 | Screenshot diff between editor-preview-at-1280 (chrome hidden) and built-page-at-1280 — proves LOCK changed nothing visual, and catches the residual case where a `data-wb-*` attribute participated in a CSS selector or affected intrinsic size |
| 5 | **Interaction-manifest check**: walk every declared motion/interaction behaviour against `dist/published` to prove it exists in shipped code. This is the Webflow-export lesson applied to a static target — no behaviour may exist only as editor state |
| 6 | **Zero unresolved references** (§12.16): every `component`, `variant`, `motion`, asset and token id in every doc resolves against `system.lock.json` + the library, and **zero nodes carry an unacknowledged `variantMigrated` or `orphaned` flag**. Fails with the node list, not a count |
| 7 | **Zero design-time origins**: grep `dist/published/**` (including `srcset`, `<meta>` content, inline `style`, CSS `url()` and `@import`, JSON-LD, and sourcemap comments) for `localhost`, `127.0.0.1`, `0.0.0.0`, `file://`, the session port, and the session root path. **A hardcoded `http://localhost:4321/img/hero.png` passes gates 1–5 and 404s for every visitor** — this closes that. Also the enforcement point for §12.6 row 9 |
| 8 | **`wb verify` clean at lock time**: regenerate `src/generated/**` into a temp dir and `diff -r` the text files; hash-compare binary assets separately (§12.8 hazard 5); and re-serialise every doc into canonical form (§12.9) and require a zero diff, so a hand-edited or foreign-serialiser doc cannot be locked |

> **Cross-section amendments this creates** (they belong to §13 and §19, recorded here so they are not lost): §13.4 row 27 becomes "LOCK purity gates 1–8 (§12.5)". §10.1's "Four automated gates (§12.5)" note becomes "Eight automated gates (§12.5)". §18's v1 bullet "all five purity gates" becomes "all eight purity gates". §19 A49 gains the gate-7 origins grep, and new criteria **A91–A99** below are appended.

**Gate 2, mechanically.** The original text asserted the gate without saying how the second build is produced, whether `wb lock` mutates `package.json`, what happens to a running design server sharing `node_modules`, or how long it takes. Normative procedure:

1. **Clean tree, never the working tree.** `git worktree add --detach .wb/tmp/gate2 HEAD` (fallback when the project is not yet committed: `rsync -a --exclude node_modules --exclude dist --exclude .wb`). `wb lock` **never** edits the live `package.json` or the live lockfile, and never touches the live `node_modules`, so a design server running in another terminal is unaffected.
2. **A committed editor-free dependency set.** `package.publish.json` / `package-lock.publish.json` (§12.2) are the live files minus the editor integration and minus design-only devDependencies. They are generated by `wb lock --refresh-publish-manifest`, **human-reviewed and committed** — regenerating them inside every lock run would make the gate depend on the registry and on the day.
3. **Install deterministically.** `npm ci --prefix .wb/tmp/gate2 --ignore-scripts` against that lockfile. Build A uses the live tree's install; build B uses this one.
4. **Pin the environment for both builds.** `SOURCE_DATE_EPOCH` = the HEAD commit timestamp, `TZ=UTC`, `LC_ALL=C`, a fixed `NODE_ENV`, an explicitly pinned Node version (recorded in `gate-report.json`), and `vite.define` supplying `WB_DESIGN=false` in both.
5. **Compare by manifest, not by `diff -r`.** Emit `manifest-a.json` / `manifest-b.json` = sorted relative path list + SHA-256 per file, and require them identical. A manifest diff names the offending file; a raw tree diff on minified bundles does not.

**Preconditions this gate depends on, stated rather than assumed:** no build timestamps in output; deterministic chunk and asset content hashing; no absolute paths in emitted sourcemaps or CSS; stable module graph ordering; and the asset-encoder pinning of §12.8 hazard 5.

> **O33 — open, no verified answer.** *Is an Astro/Vite production build byte-reproducible across two installs of the same lockfile on the same machine?* §12.8 constrains the determinism of **our generator**; it says nothing about the bundler, and **no source consulted for this PRD establishes bundler-level byte reproducibility.** This must be a Phase-0 spike, because §18 makes "a passing two-build byte-equality check" the v1 exit criterion. If the spike fails, the **fallback** is a *normalised* comparison: identical file lists, identical SHA-256 for every file except a named, enumerated exception set recorded in `gate-report.json`, with each exception justified. **That fallback weakens D3's proof from "byte-identical" to "identical except for N declared files" and therefore requires user sign-off before it is adopted.** Do not pretend otherwise. A gate that fails spuriously will be disabled by whoever is trying to ship.

**Budget.** Target ≤3 minutes wall-clock for gate 2 on the reference machine. If it exceeds 5 minutes, gate 2 demotes to pre-release/CI-only and local `wb lock` runs gates 1, 3, 4, 5, 6, 7, 8 with an explicit `gate2: waived-local` entry in `gate-report.json` — a recorded waiver, never a silent skip.

**LOCK is non-mutating.** It writes only `dist/published/` and `.wb/locks/<iso>/` (the snapshot set listed in §12.2), then `git tag wb-lock/<n>`. **The editable project is untouched, so UNLOCK is nothing more than restarting the design server — there is no unlock transformation to get wrong.**

**The one thing that claim does not cover** is hand-edits made *inside* `dist/published/`. LOCK regenerates that tree wholesale, so those edits are overwritten by the next lock no matter what unlock displays. That is handled explicitly in §12.6 row 6 rather than hidden behind the "nothing to get wrong" headline — because a reader who trusts the headline is exactly the reader who loses work.

**Going back to an older lock** is `git checkout wb-lock/<n> -- pages/ site.json system.lock.json content.json` (documents **and the system lock**, never `dist/`). Restoring the docs without the system lock is what manufactures the skew case in §12.16, so the lock file travels with them. If the library files on disk no longer hash-match the restored `system.lock.json`, the restore stops and prints the `wb migrate` command instead of opening a half-resolved project. **§19 A56 is amended accordingly** (it currently names only `pages/ site.json`).

### 12.6 State-loss ledger (what LOCK/UNLOCK must explicitly handle)

The job of this ledger is to make every loss either impossible or **explicitly named**. A row that names a loss and then claims a handling which does not actually preserve anything is worse than no row, so row 6 is rewritten below.

| # | Lost / breaks | Handling |
|---|---|---|
| 1 | Undo/redo history (in-memory) | Persist as `history.jsonl`, the capped append-only op log (§12.9a). **This, not git, is the cross-session undo answer** — see the commit-cadence reconciliation in §12.9c |
| 2 | Selection and scroll position | Persist in `.wb/session-ui.json` (also the active breakpoint key, so reopening does not silently drop the user back to `base`) |
| 3 | Per-breakpoint override provenance if flattened into final CSS | LOCK is a re-render from the doc, so provenance lives in the doc (key presence per §12.3) and is never flattened away |
| 4 | Free-position pixel baselines (the viewport they were authored at) | Anchored-offset stores percentages/`clamp()`, so there is no pixel baseline to lose |
| 5 | Placeholder flags on unfilled slots | Placeholders are a **typed state that blocks LOCK** |
| 6 | Hand-edits to files inside the exported tree `dist/published/` | **Unrecoverable by design, and now said plainly.** `dist/published/` is regenerated wholesale by every LOCK; the restore path is documents-only; `wb extract-override` lifts fragments from `src/generated/**`, not from `dist/`. Three mitigations, none of which is "we keep the edit automatically": (a) every emitted file carries the §15 banner *"generated — do not hand-edit; run /website-builder unlock"*; (b) `lock-manifest.json` records a SHA-256 per emitted file, and both **unlock and the next LOCK** diff the tree — at LOCK it is a **blocking prompt** (*"N files in dist/published were hand-edited and will be overwritten — review / discard / abort"*), not a passive display; (c) `wb extract-override --from-dist <file> [nodeId]` best-effort re-homes a dist-side fragment into `src/overrides/<nodeId>.astro` so the edit becomes legal and permanent. **(c) is best-effort and explicitly fallible** — a dist file is post-bundle output, so the mapping back to a node can be ambiguous or absent, in which case the tool refuses rather than guessing, and the honest answer is "re-make the edit in design mode" |
| 7 | Editor scaffolding leaking into the shipped site | Killed by re-render + purity gates 1–8 (§12.5) |
| 8 | Rich text pasted with `<span style=…>` and `<b>` from the source app | `contenteditable="plaintext-only"`; content stored as plain strings |
| 9 | Absolute `http://localhost:4321/...` URLs baked at design time | Post-ingest and pre-lint pass strips absolute local URLs; **enforced at lock by gate 7**, which is where it actually becomes non-optional |
| 10 | Variant/component references invalidated by a Step-5 regeneration or a new direction | **Not silently dropped.** §12.16's resolution policy: unknown component = hard fail with a named report; unknown variant = canonical-variant fallback carrying a per-node `variantMigrated` flag that is visible in the editor and **blocks LOCK until acknowledged** (gate 6) |
| 11 | Slot content orphaned when a new variant removes a slot | Moved to `node.orphaned` and surfaced in the editor. **Never deleted by a migration** — a migration may relocate content, never destroy it (§12.16) |
| 12 | Prop values orphaned when a prop is renamed or removed between system versions | Applied through the imported system's migration map if it ships one; otherwise reset to the variant default and flagged per node, same acknowledgement path as row 10 |
| 13 | Overrides (`src/overrides/<nodeId>.astro`) whose node no longer exists, or whose component changed shape | `wb doctor` reports orphan overrides; the file is **never auto-deleted** (it is human-owned per §12.7). LOCK warns; it does not block, because a stale override that nothing references cannot ship |
| 14 | Assets referenced by a doc but absent from `assets/manifest.json` | Hard fail at generate time (the manifest is the allowlist, §12.2) — the failure is loud at design time rather than a 404 at publish time |
| 15 | Doc changes made by an out-of-band writer (Claude via Bash, a text editor) after the editor loaded the file | Detected by the `.wb/doc-hashes.json` reconciliation of §12.10 and surfaced as a conflict with both versions retained; **never silently overwritten in either direction** |

### 12.7 Ownership zones and conflict handling

Copy Plasmic's owned/managed split verbatim. Plasmic emits two files per component: `plasmic/PlasmicButton.tsx` is *"owned by Plasmic, and shouldn't be edited by you. As you iterate … these files will be updated when you run plasmic sync"*; `Button.tsx` is the wrapper, for which Plasmic *"generates an initial scaffold"* and *"never touches it again."* **[V — docs.plasmic.app/learn/codegen-components, direct quotes]** This is the mechanism that makes a codegen product a tool rather than a toy.

| Zone | Paths | Writer |
|---|---|---|
| **Machine-owned** (regenerated wholesale) | `src/generated/**`, `src/styles/tokens.css` | The generator only |
| **Human/agent-owned** (never written after scaffold) | `src/pages/*.astro` thin wrappers, `src/overrides/**`, `src/lib/**` | Claude and the user |
| **Doc-owned** | `pages/*.doc.json`, `content.json`, `site.json`, `assets/manifest.json`, `provenance.json`, `history.jsonl` | The editor process only — **and Claude reaches them through `wb op`, never through a file write** |
| **Snapshot / build output** (never hand-edited, never restored from) | `dist/published/**`, `.wb/locks/**` | `wb lock` only |
| **Import record** (append/replace by the importer) | `inbound/**`, `system.lock.json`, `migration-report.json` | The Step-3 importer and `wb migrate` only |

**Claude needs a legal write path, or the guard will be routed around.** The doc-owned row above forbids Claude from writing those files directly, which is correct — but forbidding without providing is how guards get bypassed. `wb op '<typed op JSON>'` is the sanctioned CLI: it posts the same typed semantic op the browser posts (§12.13), through the same server, so it inherits validation, the op log, optimistic concurrency and the SSE push. **The skill's own instructions must state this in the imperative** ("to change a page, run `wb op`; never write `pages/*.doc.json`"), because an instruction the agent follows is cheaper and more reliable than a guard it can accidentally evade.

**Enforcement, in order of how much it is actually worth:**

1. **Reconciliation (authoritative).** `.wb/doc-hashes.json` + an `fs.watch` on the doc-owned set. Any doc-owned file whose on-disk hash differs from the journal without a corresponding server-issued write is treated as an out-of-band mutation: the editor refuses to save over it, shows both versions, and offers reload / keep-mine / merge-by-hand. **This is the only mechanism that holds regardless of *how* the write happened** — Write, Edit, Bash heredoc, `sed -i`, another editor, a script — and it is therefore the normative guarantee. Everything below is defence in depth.
2. **PreToolUse hook, extended to Bash.** Blocks `Write`/`Edit` on doc-owned paths, **and additionally scans `Bash` command text** for those paths (redirection targets, heredoc targets, `cp`/`mv`/`install` destinations, `sed -i`, `tee`, `python -c`/`node -e` payloads). **Stated honestly: a command-text scan is a heuristic and is defeatable** by variable indirection, `cd` plus a relative path, base64, or any interpreter one-liner that constructs the path at runtime. §14.1 already records that "Bash heredoc writes are not blocked" for subagents, and Bash is in the skill's own allowed-tools list — so this hook narrows the hole, it does not close it. Mechanism 1 is what closes it.
3. **File mode while the editor holds the lock.** `chmod 0444` on doc-owned files whenever `.wb/editor.lock` is live, restored on release. This makes a casual `>` redirection fail immediately with a clear error. **Also stated honestly: the Claude process and the editor process run as the same uid, so the owner can `chmod` back.** This is a speed bump against accidents, not a security boundary; a separate uid or a container would be required for that, and neither is in scope for a local ACOS skill (**O34**).
4. **`.gitattributes`** marks `src/generated/** linguist-generated=true -diff` (GitHub collapses those diffs; `-diff` also hides them from the CLI) **[V — github/linguist behaviour]**, so generated churn cannot drown the human-owned changes a reviewer needs to see.
5. **Pre-commit hook** rejects a commit touching `src/generated/**` without a corresponding doc change, and rejects any doc-owned file that is not in the canonical serialisation of §12.9.
6. **The generated banner** names the file to edit instead.

**When an illegal edit happens anyway, do not attempt a three-way merge.** Run `wb extract-override <nodeId>`, which lifts the current generated fragment into `src/overrides/<nodeId>.astro`, sets `node.override` in the doc, and re-points the generator to emit `<Override/>`. That turns an illegal edit into a legal, permanently-surviving one. This is Plasmic's split applied at node granularity. The `--from-dist` form (§12.6 row 6) is the same idea applied to the exported tree, with the ambiguity caveat stated there.

**Overrides accumulate, and that is a real cost.** Each `src/overrides/<nodeId>.astro` is a piece of the page that no longer responds to variant swaps or token changes, so a heavily-overridden page quietly stops being a design-system site. The editor shows a visible override count, and `wb doctor` uses **stated starting numbers, tunable in `site.json`**:

| Signal | Threshold (v1 default) | Behaviour |
|---|---|---|
| Overrides per page | **≥5** | `wb doctor` warns; the editor's override counter turns amber |
| Overrides per page | **≥15** | `wb doctor` escalates to a red finding; LOCK still proceeds but `gate-report.json` records the count so it is visible in the evidence bundle |
| Overrides per site | **≥40** | `wb doctor` prints the "this is no longer a design-system site" finding naming the top offending pages |
| Overridden share of a page's nodes | **≥25%** | Same escalation as ≥15, whichever fires first |

**[I — these numbers are a stated starting point, not a measured or cited figure. They exist so the rule is implementable and testable; expect to tune them after the first real site.]**

### 12.8 Determinism and drift control

Generation must be a **pure function of `(doc, system.lock.json, generator version)`**. Every generated file carries a header banner with `@generated`, `doc-sha256`, `system-lock-sha256`, `generator-version` — and **no timestamp** (a timestamp in the file body destroys determinism and pollutes every diff; put run metadata in a sidecar).

Two checks fall out:

- `wb verify` regenerates into a temp dir and `diff -r`s the **text** files against `src/generated/**`, and **hash-compares binary assets separately** (see hazard 5). **Empty diff proves both determinism and that nobody hand-edited machine-owned files.** Run on editor start, before LOCK (gate 8), and in CI.
- On editor start, a hash mismatch means someone hand-edited generated output.

**Determinism hazards to design out up front:**

| # | Hazard | Design-out |
|---|---|---|
| 1 | Map/object iteration order | Sort keys with a fixed comparator before emission |
| 2 | Absolute paths in output | Relative only — enforced at lock by gate 7 |
| 3 | Locale-dependent sorting | Fixed collator (`Intl.Collator('en', {sensitivity:'variant'})`) or raw code-unit sort; `LC_ALL=C` in build environments |
| 4 | Random ids | Derive node ids from a ULID stored in the doc, never regenerate |
| 5 | **Binary asset pipeline** — the auto-recompression on drop (§13.3, §19 A35) and any generated sprite/derivative | **Pin the exact encoder and its settings**, recorded per asset in `assets/manifest.json` as `{encoder, encoderVersion, settingsHash, outputSha256}`. `wb verify` does **not** re-encode on every run: it hash-compares the on-disk derivative against `outputSha256`, and only re-encodes when the settings hash or the source hash changed. **This is deliberate** — image encoders are not guaranteed bit-stable across versions or platforms, so re-encoding-and-diffing would produce exactly the false positives this subsection warns about. An encoder-version change is surfaced as an explicit "assets need re-derivation" action, not as a mystery diff |
| 6 | **Non-deterministic content sources** — anything that reads the clock, the network, `Math.random`, `process.env`, or the filesystem outside the doc + library at generate time | Forbidden in generated components; the §12.14 AST walk flags them at import time, and the generator runs with a frozen clock (`SOURCE_DATE_EPOCH`) so an accidental one is caught rather than absorbed |

**This is the load-bearing assumption of the whole drift story.** Any nondeterminism makes `wb verify` produce false positives, users learn to ignore it, and the guarantee silently dies. Note that hazards 1–4 and 6 are properties of **our generator**, which we control. Bundler-level reproducibility — which purity gate 2 depends on — is **not** in our control and is the open question **O33** in §12.5.

### 12.9 History: op log + snapshots + git, and NOT a CRDT

Three layers with distinct jobs:

| Layer | Mechanism | Job |
|---|---|---|
| **a** | `history.jsonl`, append-only, one line per user action with `patch` and `inverse` as RFC 6902 JSON Patch | Undo = apply `inverse`; redo = apply `patch`. Plain diffable text; doubles as the agent-vs-human audit trail. **This is the cross-session undo answer** — it survives a browser reload and a machine restart, because it is on disk |
| **b** | Atomic doc writes — write temp then `fs.rename`, debounced ~300ms, followed by a `.wb/doc-hashes.json` journal update in the same critical section | A `kill -9` leaves either the pre-op or post-op file, never a truncated one. The journal update is what makes §12.10's reconciliation trustworthy |
| **c** | Git commits at **milestones only** (LOCK, variant-set import, `wb migrate`, named checkpoint, session end), `git tag wb-lock/<n>` per lock | Durability at meaningful boundaries, and history stays readable |

**Commit-cadence reconciliation (the two policies are now one).** An earlier draft stated milestone-only commits here and "every save is a commit … auto-commit on save to a `design/` branch, squash on lock" in §12.10 — two incompatible policies for the same file, given that §13.1 fires save on every drop/mouseup. **Milestone-only wins**, for three reasons: a commit per drag produces thousands of commits per session and makes `git log` useless exactly when a user needs it; the durability job is already done by layers (a) and (b), which are cheaper and survive a crash mid-drag; and squash-on-lock would rewrite a branch that the `wb-lock/<n>` tags point into. §12.10's table row is rewritten accordingly.

**If per-save git durability is still wanted**, it is an **opt-in** `wb autosave --git` that updates a detached ref `refs/wb/autosave` (not a branch, never merged, dropped at LOCK), coalesced to at most one write every 30 s. Off by default. **[I — inference; no source establishes a required cadence. The reconciliation is a design decision made here to remove a contradiction, and §17's R6 mitigation line, which currently reads "every-save-is-a-commit", must be updated to "op log + atomic writes + reconciliation" so the two sections agree.]**

**The doc serialisation contract (normative, and asserted).** Because layer (c) only commits at milestones, a milestone diff is large — which makes readability *more* important, not less.

- UTF-8, LF line endings, trailing newline, no BOM.
- **Stable key order**: a fixed key sequence per node type (`id, component, variant, region, layout, props, slots, text, override, locked, notes, variantMigrated, orphaned`), then any unknown keys sorted lexicographically so a forward-compatible field never reorders the file.
- **2-space indent, one array element per line** — never a collapsed array, so a reordered section shows as moved lines rather than one rewritten line.
- Numbers emitted in their shortest round-trip form; no `-0`; no exponent notation.
- Booleans and `null` explicit; **omit absent optional keys entirely** rather than writing `null`, so §12.3's key-presence test for "overridden here" stays valid.
- Non-ASCII characters written literally, not `\u`-escaped.

`wb verify` re-serialises every doc-owned JSON file and requires a zero diff (purity gate 8, and the pre-commit hook of §12.7). This is what stops a hand-edit, a different formatter, or a future library upgrade from silently reformatting the file and producing a 4000-line diff that hides the one real change.

**Reject CRDTs (Yjs, Automerge, Loro).** There is one human plus a sequential agent; concurrent multi-writer merge buys nothing and costs an opaque binary doc git cannot diff. Use a single-writer `.wb/editor.lock` (pid + mtime heartbeat) and route agent writes through the inbox instead.

### 12.10 Two writers, one lock

**Failure scenario, near-certain (this is §17's R6):** the editor is open with unsaved drags in memory. The user, in the terminal, asks Claude "make the features section tighter." Claude rewrites the section and, if it touches layout, writes the doc. The browser holds stale state; the user hits Save; the browser clobbers Claude's change — or Claude clobbers the drags on the next reload. **Either way the loser's work vanishes silently.**

| Mitigation | Mechanism |
|---|---|
| **Single writer by file ownership** | §12.7, with `wb op` as Claude's sanctioned path so the ownership rule is followed rather than routed around |
| **Out-of-band-write reconciliation (the authoritative one)** | `.wb/doc-hashes.json` + `fs.watch`. Any doc-owned file whose hash diverges from the journal without a server-issued write raises a conflict in the editor before the next save is accepted, and the divergent on-disk version is copied to `.wb/conflicts/<iso>/` first. **This holds against Bash heredocs, `sed -i`, a second editor, and anything else** — which matters because the PreToolUse hook demonstrably cannot (§12.7 item 2, §14.1) |
| **Optimistic concurrency** | Every save carries the mtime/hash the client loaded; the server rejects a stale write with **409** and the editor shows "the file changed on disk — reload, force, or open the conflict copy" |
| **Durability across sessions** | The `history.jsonl` op log plus atomic writes (§12.9 a, b). **Not a commit per save** — see the cadence reconciliation in §12.9c. Git commits happen at milestones, and `wb autosave --git` is available opt-in |
| **Agent inbox** | Agents append intents to `.wb/inbox.jsonl`; the editor process is the single writer that validates, applies, appends to `history.jsonl` with `actor: 'agent'`, and pushes over SSE. Same typed ops as the UI, so **one code path for both**. When no editor process is running, `wb op` starts a headless one, applies, and exits — so the agent path is never blocked on a browser being open |
| **Loud degradation** | If `fs.watch` is unavailable or unreliable on the platform, the editor falls back to a hash re-check immediately before every save and on window focus, and says so in the status bar. **A silently-degraded conflict detector is the failure this whole subsection exists to prevent** |

The FruitSync precedent gives no help here: that site tree is not under version control at all (`fatal: not a git repository`) **[V]**, so there is no rollback of any kind today. **`git init` at Step 0, no exceptions.**

### 12.11 Session state on disk

```
.acos/website-builder/sessions/WB-<ts>-<slug>/
  00-interview/{answers.json, concept.md}
  01-prompt/{stage-a.md, stage-b-<id>.md, artwork.md}
  02-system/{<directionId>/…, manifest.json, import-report.json, system.lock.json}
  03-selection/{tournament-log.json, picks.json}
  04-site/{site.json, pages/*.doc.json, content.json, provenance.json,
           assets/manifest.json, migration-report.json, direction-tour-log.json}
  05-variants/
  06-custom/
  07-lock/{dist/, lock-manifest.json, gate-report.json, screenshots/,
           manifest-a.json, manifest-b.json}
  evidence/
  audit/config-snapshot.yaml
  .wb/{editor.lock, editor.token, inbox.jsonl, doc-hashes.json, session-ui.json,
       locks/<iso>/…, conflicts/<iso>/…, tmp/gate2/}
  state.json      ← {phase, step, awaiting, nextAction, port, pid, url, sessionId}
  events.jsonl
  ACTIVE          ← marker written at init, removed at close
.acos/website-builder/systems/<name>/{system.json, tokens.css, compliance-report.json, provenance}
.acos/website-builder/sessions/*/site/   ← in ACOS .gitignore, its own nested git repo
```

`.wb/tmp/**` and `.wb/conflicts/**` are in the site repo's own `.gitignore`; `.wb/locks/**` is **not** — the lock snapshots are the durability story and must be committed.

**The phase frontier is recomputed from which directories are populated and which gates passed — never from conversation memory.** The principle is stated best in the in-repo `acos-axiom-synthesis/STATE-MACHINE.md`: frontier is *"Computed purely from on-disk state, so the run is resumable by re-reading the ledger."* **[V — in-repo, line 66]** The `.current-session` pointer convention already exists at `.acos/sessions/loan-doc-finder/.current-session` **[V — verified by `ls`]**.

**`site/` must be its own git repo (or worktree), and the path must be in the ACOS `.gitignore`** — otherwise every milestone commit pollutes ACOS history and every LOCK tag collides with ACOS tags, making the version-history layer unusable within a single session.

### 12.12 Local server security — localhost is NOT a trust boundary

This is the single most under-rated risk in the product.

**CVE-2025-24010 (Vite):** *"Vite allowed any websites to send any requests to the development server and read the response due to default CORS settings and lack of validation on the Origin header for WebSocket connections,"* and the advisory states explicitly that it *"applies to users that only run the Vite dev server on the local machine and does not expose the dev server to the network."* Fixed in 6.0.9 / 5.4.12 / 4.5.6. Separately, **CVE-2025-30208** let `?raw??` bypass `server.fs.deny` for arbitrary file read (that one only affected `--host`-exposed servers — which is why ours never is). Vite's own docs warn that `server.allowedHosts: true` *"allows any website to send requests to your dev server through DNS rebinding attacks, allowing them to download your source code and content."* **[V — GHSA-vg6x-rcgg-rjx6, GHSA-x574-m823-4x7w, vite.dev/config/server-options, quotes verbatim]**

**Required posture:**

| # | Control |
|---|---|
| 1 | Bind `127.0.0.1` explicitly, **never** `0.0.0.0` |
| 2 | Validate `Origin` on **every non-GET and on the SSE/WS upgrade** against a two-entry allowlist |
| 3 | `Access-Control-Allow-Origin` set to the exact editor origin, **never `*`** |
| 4 | **A per-session bearer token** — 32 random bytes, `.wb/editor.token` mode 0600, injected into the editor page at render, sent as `Authorization` on every non-navigation request. **This is what defeats drive-by CSRF from any origin that has never seen the token** |
| 5 | Pin `vite.server.allowedHosts` to the explicit host; pin Vite ≥ 6.2.3 |
| 6 | Heartbeat from the editor page; exit after N idle minutes — **a forgotten dev server left running for days is the realistic exposure, not a targeted attack** |
| 7 | **`Host`-header validation on EVERY request, including the plain `GET /` that bootstraps the editor page.** Reject unless `Host` is exactly `127.0.0.1:<port>` or `localhost:<port>`. **This, not the bearer token, is the anti-DNS-rebinding control** — see the argument below |
| 8 | `Cross-Origin-Resource-Policy: same-origin`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store` on the bootstrap response, and a strict `Content-Security-Policy` on the editor page. Never reflect a request header into the response |

**Why the token alone does not defeat DNS rebinding, and what does.** The original text claimed the bearer token "is what actually defeats DNS rebinding," while also exempting `GET /` — the very response that carries the token — from validation. That reasoning does not hold, so it is replaced with an auditable one:

1. A **cross-origin** attacker page at `https://evil.example` can *send* a request to `http://127.0.0.1:<port>/` but **cannot read the response body** — the same-origin policy blocks the read, and control 3 (never `*`) prevents CORS from granting it. So the token is not exposed to a plain cross-origin attacker, and control 4 correctly stops drive-by CSRF: the attacker can send but cannot authenticate.
2. **DNS rebinding defeats step 1 by construction.** The attacker serves `evil.example` with a short TTL, then re-resolves it to `127.0.0.1`. The victim's browser now believes `http://evil.example:<port>/` is same-origin with the attacker's page, so **the SOP argument evaporates and the attacker can read the response** — including the token embedded in the bootstrap HTML. An `Origin` check does not help either, because the attacker's origin *is* `evil.example` on both sides.
3. **The header that does not lie is `Host`.** A rebound request still arrives with `Host: evil.example:<port>`, because that is what the browser was navigated to. Rejecting any `Host` that is not literally `127.0.0.1:<port>` or `localhost:<port>` refuses the rebound request **before** any response body exists to be read. This is the same mechanism Vite's `allowedHosts` implements, and the reason its docs name DNS rebinding explicitly.
4. Therefore the correct statement of the layered claim is: **control 7 (Host validation) defeats DNS rebinding; control 4 (bearer token) defeats drive-by CSRF and any residual same-site confusion; control 2 (Origin) defeats cross-origin state-changing requests.** Each has one job, and the bootstrap `GET /` is inside the validated surface rather than outside it.

The cost of extending validation to `GET /` is one header comparison, so there is no bootstrap complexity to trade away. **[I — the reasoning in points 1–4 is inference from the cited Vite advisory and the documented rebinding mechanism; it is not itself a quotation from a source. It is written out so it can be audited or refuted rather than trusted.]**

**In-repo gap to not copy:** `ic-server.py` binds `127.0.0.1` correctly but performs **no Origin check on `do_POST`** **[V — grep, lines 107/156/187]**, and no `Host` check anywhere.

### 12.13 The write endpoint is an arbitrary-file-write primitive unless constrained

Two rules make it safe by construction:

1. **The client never sends a file path or a file body.** It sends a **typed semantic op** (`{op: 'swap-variant', node: 'n_hero', variant: 'hero-split@3'}`) and the server derives the JSON Patch. **Raw-JSON-Patch-over-HTTP is nearly as dangerous as raw paths** because `add`/`replace` on an arbitrary pointer can rewrite `systemLock` or inject an `override` path. Validate every op against a schema **and** against the component library before applying.
2. **The server may write exactly the doc-owned set, and nothing else** — resolved with `realpath`, asserted `startsWith(sessionRoot)`, symlinks rejected, `..` segments rejected, and the resolved path re-checked *after* resolution rather than before. Generated files and `dist/` are written by the generator and `wb lock` from the doc, **never** by an HTTP handler.

**The allowlist, corrected.** The earlier three-shape list (`pages/*.doc.json`, `history.jsonl`, `.wb/**`) contradicted §12.7's zone table and §12.1, and left four **v1** features with no legal write path: per-page SEO/meta fields and the multi-page manager (page list lives in `site.json`), the asset/media manager and image auto-optimisation on drop (`assets/manifest.json`), provenance recording on every variant placement (`provenance.json`), and inline text editing when copy lives in `content.json`. A rule that v1 must violate is not an allowlist.

| Path shape | Which ops may write it | Constraints |
|---|---|---|
| `pages/*.doc.json` | All node/layout/text/slot/variant ops | Canonical serialisation (§12.9); one file per op batch |
| `content.json` | `set-text`, `set-richtext`, content-mode ops | Never touched by layout ops |
| `site.json` | `add-page`, `remove-page`, `rename-page`, `reorder-pages`, `set-page-meta`, `set-breakpoints`, `set-grid`, `set-doctor-thresholds` | **`systemLock` is not writable by any op, ever.** It is written only by the Step-3 importer and by `wb migrate`, and the op validator rejects any patch whose pointer starts `/systemLock` regardless of which op produced it |
| `assets/manifest.json` | `register-asset`, `set-asset-meta`, `set-alt-text`, `record-derivative` | Entries are append-or-update; a delete requires no live doc reference |
| `provenance.json` | `record-placement`, `record-variant-swap` | Append-only in practice |
| `history.jsonl` | Written by the server itself for every applied op | Append-only, never rewritten |
| `.wb/**` | Session/runtime state: `editor.lock`, `session-ui.json`, `doc-hashes.json`, `inbox.jsonl` (read + truncate-after-apply), `conflicts/**` | `.wb/locks/**` is **read-only** to the server; only `wb lock` writes it |

Everything not in that table is rejected. **§19 A78 is amended** from the three-shape assertion to this table, and gains two sub-assertions: (a) an op whose derived patch targets `/systemLock` is rejected with 400; (b) a request naming any path outside the table — including via symlink or `..` — is rejected with 400 and logged.

### 12.14 The Step-3 importer is an unauthenticated code-import channel

Pasting component code and tokens back from claude.ai means arbitrary code lands in `src/`, is evaluated by `astro dev`, and is bundled into the published site. Treat it as untrusted input.

A forgiving parser (fenced-block extraction, per-item) feeds a validator. **The validator is AST-based, not substring-based** — the earlier draft specified a denylist of literal tokens (`fetch(`, `eval(`, `new Function`, `process.`, …) and called it strict, which overstates what a token filter achieves. Bracket-notation property access, string concatenation, unicode escapes, template literals, and indirect eval via `[]["constructor"]["constructor"](…)()` all walk straight through a literal match.

**Validator design:**

| Layer | Mechanism |
|---|---|
| **Parse** | Astro files split with `@astrojs/compiler` into frontmatter, template and style; JS/TS parsed with a real ESTree-producing parser; CSS parsed with PostCSS. **A parse failure is a quarantine, never a pass-through** |
| **Resolve** | Walk the AST with scope tracking. Flag `CallExpression`/`NewExpression` whose callee **resolves** to a denied binding (`eval`, `Function`, `fetch`, `XMLHttpRequest`, `WebSocket`, `import()` of a non-local specifier, `require`, `process`, `child_process`, `fs`, `Worker`, `importScripts`, `navigator.sendBeacon`) — resolution, not spelling |
| **Fail closed on the undecidable** | Any computed member access on a global (`window[x]`), any dynamic import specifier, any `constructor` chain, any string that is assembled and then called, any `with`, any non-literal `srcset`/`href`/`url()` — **quarantine, do not reject-silently and do not pass.** Static analysis of adversarial JavaScript is undecidable in general; the honest posture is "anything I cannot resolve, a human looks at" |
| **Template & CSS** | Remote `<script src>`, remote `<link>`, remote `@import`, remote `url()`, inline event-handler attributes, `javascript:` URLs, `<iframe>`, `<object>`, `<embed>`, `srcdoc` — all quarantined. **Every remote origin is also a determinism and licence-evidence violation** (§12.8, Step 8), so this rule earns its keep twice |
| **Tokens** | Schema check that `tokens.json` is valid DTCG; reject unknown token types; reject values that are not literals |
| **Containment (defence in depth)** | Quarantined and newly-accepted items are first previewed in a **sandboxed iframe** (`sandbox` without `allow-same-origin`) under a strict `Content-Security-Policy` with no `connect-src`, so a first render cannot exfiltrate. The design server ships a CSP; the published site ships one too |
| **Human gate** | The quarantine list is shown as a rendered diff with the offending node highlighted, and nothing leaves quarantine without an explicit per-item accept recorded in `inbound/import-report.json` |

**Honest limit, stated rather than implied.** The paste's author is the user's own claude.ai session, so the realistic threat is a *mistake* (a copied snippet with a CDN font, a component that calls an analytics endpoint) or a *prompt-injection-induced* insertion — not a determined attacker with full control of the input. The validator is sized for that: it is a mistake-catcher and a supply-chain-tamper detector with a fail-closed quarantine, **not a sandbox escape-proof boundary.** If the threat model ever changes, the answer is process isolation, not a longer denylist.

Two secondary reasons this matters beyond security: **(a)** partial or malformed paste-backs will happen on most runs, and a hard-failing importer stalls the pipeline at paste #1, so per-item accept/reject with a "retry just these three" prompt is a **functional requirement**; **(b)** remote font/asset URLs sneaking in breaks offline determinism and the Step-8 licence evidence bundle.

### 12.15 The File System Access API is not a viable persistence path

`showDirectoryPicker()` requires a secure context (localhost qualifies) and a user gesture, but **Safari ships only the Origin Private File System (no directory picker) and Mozilla published a "harmful" position**; the documented Firefox fallback is `<input type="file">` for reads and `<a download>` for writes. A browser-writes-to-disk design would silently be Chrome-only and would still need a server fallback. **[V — MDN showDirectoryPicker, developer.chrome.com, WICG spec]** Keep it as an optional convenience (e.g. "export lock bundle to a folder"); the local server is the single persistence path.

### 12.16 Reference resolution and migration when the design system changes

`render(doc, systemLock, library)` is declared pure and total (§12.1). This subsection says what it does when a reference does not resolve — the case the rest of the PRD makes **routine**, not exceptional:

- **Step 5**, a user-named step in the authoritative vision: *"if nothing looks good, generate more variants, or a brand-new design-system prompt."* A brand-new direction invalidates **every** variant reference on **every** page.
- **Restoring an older lock** whose docs predate a library change (§12.5).
- **Cross-direction swap** (v2, §18).
- A Step-3 re-import that adds, renames or removes a variant.

`system.lock.json` guarantees the imported system cannot change *silently*. It says nothing about what happens when it changes *deliberately*, which is the whole of Step 5.

**Resolution policy (normative).** Applied at editor open, at generate, and at lock (gate 6):

| Case | Detection | Policy |
|---|---|---|
| Unknown **component** id | Not in the library index | **Hard fail.** The editor opens in a read-only "migration required" state listing every affected node and page; generate and LOCK both refuse. A missing component has no honest substitute — a placeholder here is a hole that ships |
| Known component, unknown **variant** id | Component resolves, variant does not | **Fall back to the direction's declared canonical variant**, and write `node.variantMigrated = {from, to, reason, at, auto: true}`. The editor shows a per-node badge and a review queue; **gate 6 blocks LOCK until every flag is acknowledged** (per node, or bulk-acknowledged with one confirmation that names the count) |
| Variant resolves but its **slot contract** changed (a slot was removed or renamed) | Schema diff between old and new variant | Slot content moves to `node.orphaned.<slotName>`, is surfaced in the editor, and is **never deleted by a migration**. A migration may relocate content; it may not destroy it |
| Prop removed or renamed | Schema diff, plus the imported system's optional migration map | Apply the map if present; otherwise reset to the variant default and flag per node, same acknowledgement path as the variant case |
| Unknown **motion** preset id | Not in the motion catalogue | Fall back to `motion.none`, flag, acknowledge before LOCK. Per D4 this is the same code path as a variant fallback, because motion is a prop on an art container, not a parallel subsystem |
| Unknown **token** name | Not in `tokens.json` | **Hard fail at generate time**, naming the token — a missing custom property otherwise degrades to an invalid CSS value and a silently wrong colour |
| Asset id absent from `assets/manifest.json` | Manifest lookup | **Hard fail** (the manifest is the allowlist, §12.2) |
| Doc `formatVersion` newer than the tool | `site.json` | Refuse to open, name the versions. Never best-effort-parse a future format |
| Doc `formatVersion` older than the tool | `site.json` | `wb migrate --format` applies the ordered format migrations, writes a `.wb/locks/pre-migrate-<iso>/` snapshot first |

**`wb migrate [--to <systemLockSha>] [--format]`** is the sanctioned operation:

1. Snapshot the current docs into `.wb/locks/pre-migrate-<iso>/` before touching anything.
2. Diff old vs new `system.lock.json`: components added/removed/renamed, variants added/removed/renamed, slot and prop schema changes, token additions/removals.
3. Produce a **plan** and show it before applying — counts per rule, and the full node list on request.
4. Apply as **typed ops through the same server path** (§12.13), so every change lands in `history.jsonl` with `actor: 'agent'` and is individually undoable. A migration is not a special bypass.
5. Write `migration-report.json` (§12.2) and update `systemLock` in `site.json` — the one write that no HTTP op may perform.
6. Leave the acknowledgement flags in place. **Migration proposes; the human accepts.**

> **Deviation requiring user sign-off.** The v1 policy makes a brand-new-direction regeneration (Step 5) a **reviewed** operation: every node gets a canonical-variant fallback and LOCK is blocked until the user acknowledges. If the user expects "generate a new direction and it just applies," that is a different product — it would mean accepting silent, unreviewed substitution across every page — and it is **not** what this PRD specifies. Bulk-acknowledge exists to make the review cheap (one confirmation naming the count), but the flag-and-block behaviour is deliberate. **Confirm this is what the user wants.**

> **O35 — open, requires user decision.** Whether `wb migrate` should attempt **semantic** variant matching across directions (map `hero-split@3` in direction A to the nearest `hero-split`-shaped variant in direction B by slot signature) rather than always falling back to the canonical variant. Semantic matching preserves more intent and is what makes the v2 cross-direction swap pleasant; it is also a heuristic that can confidently produce a wrong answer. **No known mitigation that removes the risk** — the honest options are (a) canonical fallback only, always reviewed (the v1 choice), or (b) slot-signature matching with the same mandatory review. Not decidable without the user.

### 12.17 Consistency register for this section

Recorded so downstream sections are updated together rather than drifting. Each item is an amendment this section's revision **creates elsewhere**, or a question it cannot close.

| Id | Item | Status |
|---|---|---|
| — | §13.4 row 27: "LOCK purity gates 1–5" → **1–8** | Amendment, mechanical |
| — | §10.1 lock-gates row: "Four automated gates" → **Eight** | Amendment, mechanical |
| — | §18 v1 bullet: "all five purity gates" → **all eight** | Amendment, mechanical |
| — | §19 A49: add the gate-7 design-time-origins grep | Amendment |
| — | §19 A56: restore command gains `system.lock.json` and `content.json` | Amendment |
| — | §19 A78: three-path rule → the §12.13 allowlist table, plus the `/systemLock` and symlink sub-assertions | Amendment |
| — | §17 R6 mitigation line: "every-save-is-a-commit" → "op log + atomic writes + hash reconciliation" | Amendment (§12.9c reconciliation) |
| **O31** | Breakpoint boundaries 991/479 paired with preview widths 768/390 — reconciliation, not a cited figure. Alternative is boundaries = preview widths. Must change in §10.1, §11.3, §11.4 and §12.3 together | Open, inference flagged |
| **O32** | No wide/`xl` override tier in v1. Adding one introduces the only upward override in the cascade | Open, requires user decision |
| **O33** | Astro/Vite build byte-reproducibility across two installs is **not established by any source consulted**. Phase-0 spike; documented fallback weakens D3's proof and needs sign-off | Open, no verified answer |
| **O34** | Same-uid processes mean file-mode enforcement is a speed bump, not a boundary. A separate uid or container is out of scope for a local ACOS skill | Open, no known mitigation in scope |
| **O35** | Semantic cross-direction variant matching vs canonical fallback in `wb migrate` | Open, requires user decision |

**New acceptance criteria created by this section** (append to §19, continuing from A90):

| Id | Criterion |
|---|---|
| A91 | A doc node with a `base` entry and no `sm` entry compiles to `grid-column: 1 / -1` inside `@media (max-width: 479px)`, and the emitted rule order is `base`, `md`, `sm` |
| A92 | A doc containing an `lg`-style upward override key is **rejected** by the doc schema validator with a message naming the desktop-down rule |
| A93 | `grep -rE 'localhost\|127\.0\.0\.1\|0\.0\.0\.0\|file://' dist/published/` returns zero matches, including inside `srcset`, inline `style`, CSS `url()` and JSON-LD (gate 7) |
| A94 | Purity gate 2 runs from a clean `git worktree` with its own `node_modules`; the live `package.json`, lockfile and `node_modules` are unmodified afterwards, and a design server running concurrently is unaffected |
| A95 | A doc-owned file written out-of-band via a Bash heredoc while the editor holds the lock is detected before the next save, the divergent version is preserved under `.wb/conflicts/`, and neither version is silently overwritten |
| A96 | A typed op whose derived JSON Patch targets `/systemLock` is rejected with 400, whichever op produced it |
| A97 | The editor's asset manager, page manager, per-page SEO fields and inline text editing each complete successfully against the §12.13 allowlist with no path outside the table written |
| A98 | Re-serialising every doc-owned JSON file produces a zero diff (canonical form, §12.9); a file with collapsed arrays or reordered keys fails the pre-commit hook and purity gate 8 |
| A99 | After importing a new direction, every node carries a `variantMigrated` flag, the editor lists them, LOCK is refused until they are acknowledged, and `migration-report.json` names every changed reference |
| A100 | A `GET /` carrying `Host: evil.example:<port>` is rejected before any response body is produced; a `GET /` with `Host: 127.0.0.1:<port>` succeeds |
| A101 | An imported component using `window["fe"+"tch"]("…")` is **quarantined** by the AST validator (it is not caught by a literal-substring filter), and a parse failure quarantines rather than passes |

---

