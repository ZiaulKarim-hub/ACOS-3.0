## 19. Acceptance criteria

Testable statements. Each maps to a gate, a script, or an observable behaviour.

### Pipeline

| # | Criterion |
|---|---|
| A1 | Running the skill in a project with an existing `.acos/design-library/*/design-system-spec.yaml` offers it as a warm start within the first three exchanges |
| A2 | Step 0 detects an asset library when one exists at a path the user names, and records `assetLibraryPath` in `session.json` |
| A3 | The interview completes with ≤45 answered questions for a single-language, single-surface, no-forms marketing site |
| A4 | Every emitted design directive in the Step-2 prompt cites the interview question ID that produced it |
| A5 | The concept document names at least one thing the site refuses to do, and the pipeline refuses to advance to Step 2 without it |
| A6 | The generated Stage-A prompt contains: the DTCG worked example, the OKLCH-hue warning, the pinned font shortlist with base64 display cuts, the frozen token manifest, the CSP constraint, the 390px preview requirement, and the self-audit instruction |
| A7 | Pasting a **complete** chunk ingests with zero manual file operations beyond one `pbpaste` command |
| A8 | Pasting a **truncated** chunk fails with a message naming the missing files, and does not write a partial system |
| A9 | Pasting a chunk containing `fetch(` in a component quarantines that item, ingests the rest, and reports it in `import-report.json` |
| A10 | A contrast pair claimed as passing but actually failing is detected, auto-nudged, and logged in the substitution log |
| A11 | A font not on the pinned shortlist is substituted with the nearest OFL match in the same classification and logged |
| A12 | Local Regeneration Mode produces a bundle that passes the identical validator with zero pastes |
| A13 | `--resume` after a context reset reconstructs the phase from disk alone, with no reliance on conversation memory |

### Design system

| # | Criterion |
|---|---|
| A14 | Every token in a direction carries `com.acos.llm`, `com.acos.pick`, and `com.acos.direction` extension blocks |
| A15 | The editor renders **no control** for any token with `com.acos.pick.pickable: false` |
| A16 | A token whose `com.acos.direction.vectorHash` differs from the active direction is rejected by the builder |
| A17 | A direction with `elevation.model: border-only` that references any shadow token fails coherence lint 6 |
| A18 | The contrast proof table is all-pass by construction; any failure is reported as evidence of a hand-edited value |
| A19 | Both light and dark schemes are independently solved, and the proof table covers both |
| A20 | ≥60% of the 20 artworks in a generated set are token-referencing (`currentColor` / `var(--*)`) |
| A21 | Changing a direction's hue anchors re-skins all token-referencing artwork with no regeneration |
| A22 | Every motion item has a paired reduced-motion sibling, and the reduced-motion render diff shows a **difference** where motion exists |
| A23 | No custom cursor exceeds 128×128, and every `cursor: url()` declaration has a native keyword fallback |
| A24 | Spacing, type steps, radius scale, shadow scale, and semantic colour roles are all marked `derived` and have no editor control |

### Editor

| # | Criterion |
|---|---|
| A25 | A component can be selected via canvas click, via the breadcrumb, and via the Navigator tree — including a zero-height wrapper and an element fully covered by a background art container |
| A26 | Every drag operation has a single-pointer equivalent (select + click destination, or arrow-key nudge), satisfying WCAG 2.5.7 for the editor itself |
| A27 | Every editor-chrome control measures ≥24×24 CSS px, or satisfies a documented WCAG 2.5.8 exception |
| A28 | A padding drag commits to a named spacing token and displays the token name, never a raw pixel value |
| A29 | A component swap that removes a slot parks the orphaned content in a visible panel; swapping back restores it |
| A30 | A component swap that adds a slot creates a flagged placeholder that **blocks LOCK** until filled or deleted |
| A31 | A component swap is a **single** undo step; one Cmd+Z restores the prior variant completely with no hybrid state |
| A32 | A "regenerate this section" action is a single undo step |
| A33 | Hovering a variant in the component bar previews it live in the real slot with the current copy and neighbours |
| A34 | No two variants offered in the same bar are indistinguishable at 200×120px |
| A35 | Dropping a 4MB photo triggers auto-recompression with a visible, undoable confirmation |
| A36 | Placing an image without alt text or a decorative toggle **blocks the placement** |
| A37 | The Design Health HUD is the only surfacing channel for Tier-2 findings; no Tier-2 finding produces a toast |
| A38 | A component swap replaces the node **in place** in the DOM tree; the tab order before and after the swap is identical for equivalent content |

### Layout

| # | Criterion |
|---|---|
| A39 | The gridline overlay's track positions match `getComputedStyle(section).gridTemplateColumns` exactly |
| A40 | A drag commits an integer `grid-column` / `grid-row`, and the same block occupies 50% width at both 768px and 1440px when spanning 6 of 12 |
| A41 | A block with no small-breakpoint override compiles to `grid-column: 1 / -1` in source order |
| A42 | An edit made at 390px shows a pre-commit chip naming exactly which sizes it will affect |
| A43 | A free-positioned block auto-demotes to normal flow at ≤479px unless explicitly opted in |
| A44 | A free-positioned block that produces document `overflow-x` at any of 320/390/768/1280/1440 **fails LOCK** |
| A45 | A free-positioned block's parent does not collapse (reserved `min-block-size` applied at drop) |
| A46 | Component internals use `@container`, not `@media`; moving a card from a 6-col to a 3-col slot requires no manual fix |
| A47 | Snap tolerance divided by zoom keeps snapping usable at 25% and 200% |
| A48 | Free-position is unavailable by default on a scroll-driven pinned/scrubbed container, and forcing it requires an explicit confirmation |

### Lock and export

| # | Criterion |
|---|---|
| A49 | `grep -r 'data-wb-' dist/published/` returns zero matches |
| A50 | `grep -rE 'astro-dev-toolbar\|/@vite/client\|import.meta.hot\|data-astro-source' dist/published/` returns zero matches |
| A51 | A build with the editor integration installed and a build with it removed from `package.json` produce **byte-identical** `dist/published/` trees |
| A52 | A screenshot of the editor preview at 1280 with chrome hidden and a screenshot of the built page at 1280 differ by zero pixels |
| A53 | `wb verify` produces an empty diff on a freshly generated project, and on the same project after ten drag operations |
| A54 | LOCK writes only to `dist/published/` and `.wb/locks/<iso>/`; `pages/*.doc.json` mtimes are unchanged |
| A55 | UNLOCK is restarting the design server; no transformation is applied to the design project |
| A56 | `git checkout wb-lock/<n> -- pages/ site.json` restores a prior lock's documents without touching `src/overrides/**` |
| A57 | Every declared motion/interaction behaviour is present in `dist/published` (interaction-manifest check) |
| A58 | Unlocking after a hand-edit to the exported tree **shows the diff** rather than silently overwriting |
| A59 | LOCK produces `dist/` via write-to-new-dir-then-swap; no `rm -rf` is executed |

### Quality

| # | Criterion |
|---|---|
| A60 | The locked site renders at 320 CSS px with no two-dimensional scroll except exempted content |
| A61 | A 40-char unbroken token injected into any text block at 320px produces no overflow |
| A62 | +35% pseudolocalised strings produce no overflow or truncation on any page |
| A63 | 200% zoom produces no horizontal scroll and no content loss |
| A64 | A Playwright tab-walk reaches every interactive element, in visual order, with a visible focus ring at ≥3:1 against adjacent colours, and no trap |
| A65 | Full-page axe-core reports zero critical and zero serious findings |
| A66 | LCP ≤2.5s, CLS ≤0.1, and TBT ≤600ms on a median-of-3 mobile Lighthouse run under the documented Slow-4G profile |
| A67 | Pre-LCP transfer is ≤2MB |
| A68 | Every `@font-face` declares `font-display: swap`; exactly the committed families are preloaded; a fourth family introduced by a late swap **fails the gate** |
| A69 | Every page has a unique title, a 50–160-char description, a canonical URL, OG + Twitter tags with an image, a matching `lang`, a single H1 with no skipped levels, and 100% alt coverage |
| A70 | `robots.txt` and `sitemap.xml` are generated from the page tree, and JSON-LD validates against schema.org for the interview's site type |
| A71 | The site renders usably with JavaScript disabled: content visible, nav operable, forms submittable |
| A72 | The evidence bundle contains a licence class for every font and every asset, and says "passed N automated gates" — **never "WCAG AA compliant"** |
| A73 | The evidence bundle contains an explicit "manual and screen-reader review not performed" line |
| A74 | Any commercial-foundry font emits a pre-launch blocker rather than being embedded |
| A75 | No third-party mark (platform badge, social icon, trust badge, map tile) has been redrawn; all are used as supplied |

### Architecture and safety

| # | Criterion |
|---|---|
| A76 | The server binds `127.0.0.1` only; a request from a non-allowlisted `Origin` is rejected on every non-GET and on the SSE upgrade |
| A77 | A request without the session bearer token is rejected |
| A78 | The server writes only to `pages/*.doc.json`, `history.jsonl`, and `.wb/**`, verified by `realpath` + prefix assertion; a symlinked path is rejected |
| A79 | The wire format carries typed semantic ops; a raw JSON Patch or a file path in a request body is rejected |
| A80 | A `curl` to the server's health endpoint in a **separate tool call after the turn boundary** returns HTTP 200 |
| A81 | Claude's `Write` on `pages/*.doc.json` while the editor lock is held is blocked by the PreToolUse hook |
| A82 | A stale save (mtime/hash mismatch) is rejected with 409 and surfaces "reload or force" in the editor |
| A83 | `site/` is its own git repo, and `.acos/website-builder/sessions/*/site/` is in the ACOS `.gitignore` |
| A84 | All new code is TypeScript run by bun; `find` over the skill's `scripts/` and `app/` returns zero `.py` files |
| A85 | `bun selftest.ts` passes with 100% of assertions |
| A86 | Zero files are added to `.claude/agents/` |
| A87 | `Task` does not appear in the skill's `allowed-tools` |
| A88 | The skill is installed globally as a symlink to the git-tracked repo copy, verified by `ls -la ~/.claude/skills/ | grep acos-website-builder` showing `->` |
| A89 | No subagent calls `Write`; all agent-produced code returns as text and is written by the main thread |
| A90 | Phase 0 restates the understood brief and waits for an explicit confirmation before any file write or server launch |

---

