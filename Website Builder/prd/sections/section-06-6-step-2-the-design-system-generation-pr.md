## 6. Step 2 — the design-system generation prompt

### 6.1 What the prompt must demand

| # | Demand | Why |
|---|---|---|
| 1 | **DTCG 2025.10 format verbatim**, with a literal worked example, not a description | The spec changed the colour token shape to an object with `colorSpace`/`components`/`alpha`/`hex`; any model working from pre-2025 examples emits a hex string and the pipeline breaks **[V — designtokens.org/TR/drafts/format/, version 2025.10, dated 17 June 2026]** |
| 2 | **OKLCH hue anchors, chroma ceiling, neutral temperature, scheme strategy — never hex swatches** | The colour solver (Leonardo model: declare target contrast ratios, solve for colours) runs locally. Asking for swatches gets swatches that fail contrast **[V — adobe/leonardo contrast-colors README]** |
| 3 | **An explicit statement that OKLCH hue ≠ HSL hue** — 0° is magenta, red is ≈41° | A prompt that says "hue 0 for red" silently produces a magenta-based palette across every direction **[V — MDN oklch(), Baseline May 2023]** |
| 4 | **Font pairings chosen from an embedded, pinned OFL shortlist** — never open-ended naming | Closes the hallucinated-foundry-licence failure and the off-shortlist-licence failure in one move, and makes the output trivially cross-checkable |
| 5 | **A base64 `data:font/woff2` @font-face for each direction's display face**, subset to the preview glyph set | The artifact CSP permits `fonts.googleapis.com` under `style-src` but restricts `font-src` to `data:` and `claudeusercontent.com` — the CSS loads and the WOFF2 is blocked, so a Google-Fonts direction previews in a system face. **You would pick a look you never saw.** A Latin-subset display WOFF2 is typically 8–20KB, ~11–27KB base64 **[V — content-security-policy.com + claude-artifacts-guide CSP list; size figures are inference]** ¹ |
| 6 | **Vanilla HTML + inline CSS + optional vanilla JS for every component variant — never React** | Sidesteps the unpublished, unstable React-artifact import allowlist, and vanilla fragments are what the editor's anchored DOM actually needs |
| 7 | **Everything self-contained** — inline `<style>`, data-URI images, no CDN links, no `@import` | The artifact CSP blocks all outbound requests; a `<link>` to Google Fonts silently fails |
| 8 | **A frozen token-name manifest, re-pasted verbatim in every chunk** | Across chunks/conversations the model re-invents names (`--color-accent` in chunk 1, `--accent` in chunk 3). Component swaps then resolve to nothing and render unstyled with no error. The ingest **hard-rejects** any key not on the manifest — no fuzzy remapping, which would be a new bug factory |
| 9 | **Prior-direction parameters as negative constraints in every subsequent chunk** | Divergence must be enforced by the skill, not hoped for from the model. "Do not produce a direction whose hue anchor is within 30° of any of these, or that reuses any of these type pairings" |
| 10 | **A per-item `com.acos.llm` extension block** — `{usage: string[], rules: string, antipatterns: string[]}` on every semantic token | Copied from GitHub Primer's shipped `org.primer.llm` pattern. This is what lets the building agent select the right token without guessing **[V — primer/primitives functional/*/\*.json5, quoted verbatim]** |
| 11 | **A `com.acos.pick` block** — `{pickable, slot, directionId, variantIndex, derivedFrom[]}` | The editor renders a control **only** where `pickable: true`. This is how D1's "derived values are never picked" becomes structurally enforced rather than documented |
| 12 | **A `com.acos.direction` block** — `{id, vectorHash}` | The builder rejects any token whose hash ≠ the active direction. Stops cross-contamination during component swaps |
| 13 | **A root capability manifest declaring expected counts per group** | Makes truncation detectable: the skill compares declared to actual on ingest |
| 14 | **A paired reduced-motion variant for every motion item**, art-directed with WCAG-exempt vocabulary (opacity/colour/blur), never `animation: none` | The editor cannot invent a good reduced variant for an animation it never saw the internals of. If this isn't demanded upstream, every animated element degrades to a generic freeze |
| 15 | **A 390px-wide preview frame inside every direction artifact**, alongside the desktop frame | Directions are otherwise judged only at desktop width; art tied to a 16:9 hero doesn't crop to 390×844 portrait, and the user selects a direction they've never seen at the viewport most visitors use |
| 16 | **A self-audit closing step**: recount the manifest against what was actually emitted and list any gaps | Cheap; reduces how often the ingest validator has work to do |

¹ **Verify before shipping the prompt spec.** Open a claude.ai artifact with a Google Fonts `<link>` and check computed `font-family` in devtools. This is a 60-second test that determines whether typography can be judged on the web side at all. See §17-O1.

### 6.2 The exact return-format schema

**Envelope (mandatory, per chunk):**

````
```json
FILE: manifest.json
{
  "templateVersion": "1.0.0",
  "chunk": { "index": 2, "of": 6, "kind": "direction-deep-dive", "directionIds": ["d03"] },
  "files": [
    { "path": "tokens/d03.tokens.json", "lines": 412, "sha256Prefix": "a91f0c" },
    { "path": "components/d03/button-primary/01.html", "lines": 38, "sha256Prefix": "77bd21" }
  ],
  "countsDeclared": { "directions": 1, "components": 22, "artwork": 0 },
  "terminator": "<<<ACOS-END-a7f3>>>"
}
```
````

Then every subsequent fenced block opens with a `FILE:` comment in that block's own comment syntax:

````
```json
// FILE: tokens/d03.tokens.json
{ ... }
```

```html
<!-- FILE: components/d03/button-primary/01.html -->
<!-- ACOS-COMPONENT id=d03.button-primary.01 item=button-primary direction=d03
     tokens-used=--color-accent,--radius-md,--motion-fast slots=label,icon? -->
<button class="btn-primary">…</button>
<style>…</style>
```
````

And the very last line of the response is the terminator token verbatim.

**Ingest contract.** The skill splits on triple-backtick fences, reads each block's `FILE:` line, writes to that path, then validates:

| Check | On failure |
|---|---|
| Manifest present and parseable | **Hard fail.** Name exactly what's missing; offer re-paste or Local Regeneration |
| Terminator line present as the final line | **Hard fail** — this is a truncation, and a truncated CSS block is still *valid CSS* that renders. This is the corruption-without-symptom class and the single most expensive failure at this boundary |
| Per-file line counts match declared | **Hard fail** on the mismatching file only; auto-draft a repair prompt naming it |
| `countsDeclared` == counts actual | Mark missing ids MISSING, ingest everything else, draft a targeted repair prompt |
| JSON parses strictly | Attempt a **tolerant repair pass** (trailing commas, obvious syntax slips) before declaring failure; log what was auto-fixed |
| Every token key ∈ frozen manifest | **Hard reject** the offending key. No fuzzy remapping |
| DTCG schema valid | Reject with the specific path that failed |
| No `fetch(`, `eval(`, `new Function`, non-local `import(`, `process.`, `child_process`, remote `<script src>`, remote `@import`/`url()`, inline event handlers | Quarantine that item; continue |
| Every contrast pair recomputed locally (WCAG 2 + APCA) | Auto-nudge OKLCH lightness deterministically; if the fix exceeds a delta threshold, flag for human confirm. Never trust a stated pass |
| Every font ∈ pinned OFL shortlist | Auto-substitute nearest OFL match in the same classification, log a licensing note, continue non-blocking |
| Every asset reference resolves inside the bundle | Mark that one variant DEGRADED, exclude it from the swap bar, don't block the rest |

Files are emitted **smallest-first** so a truncation loses the least.

### 6.3 Chunking strategy

Hard numbers from the user's own precedent: each FruitSync variant page is 35–43KB of self-contained HTML+CSS (~10–12K tokens); the shipped release index is 92KB **[V — `wc -c` on 6 variant files]**. A full direction at that fidelity is ~40KB minimum. Ten directions plus 20 artworks is ~400KB (~110K tokens) against a 200K claude.ai context that artifacts count against.

| Chunk | Content | Approx size |
|---|---|---|
| A | ~10 direction capsules (26-slot vector + 40–80 word manifesto each) + ONE gallery artifact previewing all 10 as hero cards at desktop AND 390px | Small; fits reliably |
| B₁…Bₙ | Full DTCG expansion + identity-carrying component instances for **one shortlisted direction** each. Run only for directions the user actually shortlists | ~40KB each |
| Art | The 20 artworks with `suitsDirections[]` tags | Variable |

**Why Stage A is thin:** it is what the user actually judges. Generating all 10 in full upfront wastes ~90% of the output because 9 expansions are discarded.

**claude.ai constraint:** the platform commits to one live-updating artifact per turn — a new reply iterates the *same* artifact in place, and separate artifacts accumulate *across* turns via a panel switcher. There is no documented mechanism for one response to open ten independently-addressable artifacts **[V — support.claude.com/en/articles/9487310 + multiple 2026 guides converging; medium confidence]**. So: at most ONE artifact per response (the gallery, for eyeballing), and the machine-readable payload in ordinary fenced code blocks, which have no such limit.

### 6.4 The one-paste protocol

Naive hand-carry is 35–60 discrete copy → switch app → paste → name → file operations at ~60–90s each: **45–90 minutes of the user's hands per generation cycle**, and Step 5 makes it a loop. This is the most likely way the product quietly dies.

The protocol: **one fenced block per chunk containing the manifest with inline file contents.** One `Cmd+A` / `Cmd+C` per chunk. The skill ingests via `pbpaste` on a one-word command. ~40 operations become ~5. **[I — sized against first-party artifact counts]**

### 6.5 Local Regeneration Mode (first-class, not a fallback of last resort)

The same prompt, the same schema, run against a Claude Code subagent. Zero pastes, deterministic filing, schema-validated at write time. The claude.ai hop becomes an opt-in "I want the web model's design sense for this one" path.

**If the PRD hard-wires the paste as mandatory, usage frequency is capped by the user's tolerance for clerical work.** Local Regeneration Mode ships in v1.

---

