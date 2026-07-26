## 13. Quality gates

### 13.1 The dividing line

Not "a11y vs performance" but **scoped arithmetic/DOM-read vs whole-document render pass**.

- **LIVE** (sub-100ms, fires on drop/mouseup — **never mid-drag, never per-frame** — scoped to the touched subtree)
- **LOCK-TIME** (seconds to tens of seconds, whole-document, batch)

`axe.run(context)` supports scoped runs natively **[V]**; Lighthouse's throttled multi-second run cannot happen per-frame **[V]**.

**LOCK wall-clock budget (new, closes a recorded gap).** "Seconds to tens of seconds" describes each individual gate, not the full 28(+)-gate LOCK run end to end, and no total budget was previously stated even though LOCK is a synchronous human-waiting moment. Stated target: **p50 ≤ 90s and p95 ≤ 180s for a representative 5-page site** on the reference hardware/network profile used elsewhere in this section (§13.5's throttling profile). This number is an **inference, not a measured or sourced figure** — no vendor benchmark was run to derive it, and it should be validated against a real prototype before being treated as a hard SLA. If the budget can't be met once gate 20 (Lighthouse, median-of-3, per page) is included at real page counts, the mitigation is: run gate 20's full median-of-3 sweep against a **representative sample** of pages (one per distinct template/layout, capped at N pages) rather than every literal page, and re-run the full per-page sweep only for pages the sample flags as different in shape. This sampling fallback is itself unverified against real multi-page sites and should be treated as a design intent, not a proven-sufficient mitigation.

### 13.2 Two WCAG criteria apply to the EDITOR ITSELF — the most product-specific accessibility fact in this PRD

**WCAG 2.2 SC 2.5.7 Dragging Movements (AA, new in 2.2):** *"All functionality that uses a dragging movement for operation can be achieved by a single pointer without dragging, unless dragging is essential."* **[V — w3.org/WAI/WCAG22/Understanding/dragging-movements.html]**

The entire Step-4 design surface **is** a dragging interface. If the only way to move a component, resize it, or reorder it is a mouse drag, **the editor itself fails AA.** The fix is concrete and cheap, and it's already in the v1 feature list: select-then-click-destination, arrow-key nudge over grid cells, `+`/`−` span steppers, and — per D2's anchor model — a "move to: left of X / above Y" menu. This is a requirement for the editor's **own** UI, separate from what the published site does.

**WCAG 2.2 SC 2.5.8 Target Size (AA):** 24×24 CSS px minimum, with four exceptions (Spacing, Equivalent, Inline, Essential). Award-style editor chrome — thin drag handles, tiny corner resize grips, dense component-bar icon rows — violates this by default. **Every editor-chrome element needs a live bounding-rect check on render, not just at lock.**

### 13.3 Live checks (in-browser, scoped)

| Check | What |
|---|---|
| Contrast recompute | WCAG 2 relative-luminance ratio (4.5:1 normal, 3:1 large, 3:1 UI) **and** APCA Lc on every touched pair. Pure arithmetic on two colours — no DOM walk, no network |
| Target size | `getBoundingClientRect()` on every interactive element touched by a drag/resize; flag <24×24 unless an exception applies |
| Scoped axe-core | color-contrast, image-alt, label, button-name, aria-required-attr, duplicate-id on the touched subtree only |
| Overflow / clipping | ResizeObserver + `scrollWidth > clientWidth` |
| Focus-not-obscured | Bounding-box intersect newly-placed sticky/fixed elements against all focusables (SC 2.4.11) |
| Reading-order vs visual-order | Walk the tabbable list, flag non-monotonic DOM-vs-rect pairs (heuristic proxy for SC 2.4.3) |
| Reduced-motion sibling presence | Confirm the item's catalog has a tagged reduced variant; auto-apply a generated fallback and flag |
| Alt-text / decorative gate | **Blocks the placement**, not just the lock |
| Motion-property lint | Non-compositor properties, out-of-band durations, missing reduced-motion query (v2) |
| Text-spacing stress clone | WCAG 1.4.12 override stylesheet on a scoped off-screen clone (v2) |
| Image auto-optimisation | On drop, with a visible undoable confirmation |
| Budget HUD | Page weight vs budget; projected LCP from `PerformanceObserver`'s live LCP-candidate entry |
| **Motion-concurrency running counter (new, closes a recorded gap)** | On every placement/removal of a motion-bearing container, recompute the live count of heavy-cost-class instances (WebGL/canvas scenes, particle/ambient layers, autoplay video loops, pinned/scrubbed sequences) and feed it into the Design Health pill so the human sees the count accumulate turn-by-turn — **not** discovers it for the first time at LOCK. Ambient/Tier-3 while under the caps in §13.4 gate 4a; escalates to a Tier-2 Design Health warning as the count approaches the cap, per §13.7's severity model |

### 13.4 The ordered lock-time checklist

Ordering follows cheapest-and-most-foundational-first: the build must succeed before anything downstream is meaningful; deterministic gates before anything requiring a render pass. The base 28 gates keep their original numbers for cross-reference stability; four gates recorded as missing by the critics are inserted as lettered sub-steps (**4a, 11a, 13a, 23a**) at the ordering position their cost class and dependency actually require, rather than renumbering the table.

| # | Gate | Threshold / pass condition |
|---|---|---|
| 1 | Build/export succeeds | Zero errors |
| 2 | `wb verify` — regenerate to temp, `diff -r` | Empty diff |
| 3 | Token/CSS lint (`stylelint-declaration-strict-value` + raw hex/px grep) | Zero raw values outside the token system |
| 4 | Six coherence lints (§7.12) | All pass; lint 6 (border-only ⇒ zero shadow tokens) is the one that catches human-visible incoherence |
| **4a** | **Motion-concurrency cap check (new, closes a recorded MAJOR gap)** | Purely structural — a count over the container inventory, no render pass needed, so it belongs this early. Caps, carried over from the prior swarm report's Lens 8 finding as an **inference pending user validation**: **max 1 WebGL/canvas scene, max 1 particle/ambient layer, max 2 autoplay video loops, max 2–3 pinned/scrubbed sequences, per page.** Rationale: motion costs are additive (draw calls, texture memory, JS tick overhead compound), so the whole-page `lhci` budget at gate 20 fails late and gives no attribution back to which container caused it. This gate fails the build with a per-container attribution list if any cap is exceeded. **Open question: the exact cap numbers are inherited from research, not independently benchmarked against this product's own render stack — treat as a starting default, not a validated ceiling, until measured against a real prototype.** |
| 5 | Full-page axe-core sweep (adds landmark-unique, region, heading-order, doc-wide duplicate-id) | **Zero critical/serious** |
| 6 | Pa11y cross-check (HTML_CodeSniffer WCAG2AA) | Second ruleset; raises coverage without claiming completeness |
| 7 | WCAG 2 + APCA contrast sweep, text **and** non-text (1.4.3, 1.4.11) | 4.5:1 / 3:1 / 3:1; APCA Lc75 body, Lc60 large-bold, Lc45 large-non-text ⁵ |
| 8 | Target-size sweep on published-site controls (2.5.8) | 24×24 CSS px, exceptions applied |
| 9 | Dragging-alternative audit for widgets built via Step 6 (2.5.7) | Every drag affordance has a documented single-pointer alternative |
| 10 | Reflow at 320 CSS px (1.4.10) + text-spacing stress (1.4.12) | No 2D scroll except exempted content (data tables, images, toolbars, maps). **Free-positioned elements get mandatory extra scrutiny** |
| 11 | Free-position breakpoint audit | Re-project at 320/390/768/1440; auto-demote anything with no narrow-viewport position; **refuse to lock on document `overflow-x` or parent-box escape** |
| **11a** | **Skip-link presence and tab-order (new, closes a recorded BLOCKING gap — WCAG 2.4.1 Bypass Blocks, Level A)** | Every published page has a working "skip to main content" link, present in the DOM and **first in tab order**, that jumps focus past repeated navigation/ribbon chrome into the main content region. Pass condition: skip link exists, is keyboard-reachable as the very first `Tab` stop, and moving focus through it lands inside `<main>` (or the equivalent landmark). **This requires the skip link to exist as a real, selectable v1 component** — it was previously absent from both the gate list and the component inventory. Recommended default: **2 variants** (visible-on-focus text link; icon+text compact variant for dense ribbon designs), consistent with this PRD's general pattern of offering a small number of comparable variants rather than one fixed implementation. **Cross-reference note (requires coordination outside this section):** the v1 component inventory (§8/§18) needs an explicit skip-link entry with this variant count; this section defines the gate that enforces it, but does not itself own the component catalog. Also requires the editor-chrome z-index ladder (§11/§12) to reserve a band **above** skip-link so the purity claim in §12.5 stays provable — flagged here, owned there. |
| 12 | Playwright keyboard tab-walk (2.4.3, 2.4.7, 2.4.11) | Focus order matches visual order; no traps; ring visible at every stop (≥3:1 against adjacent, non-zero outline); nothing obscured. **Runs after 11a so a missing skip link is caught by its own dedicated gate rather than silently passing this walk** — a missing skip link is not a keyboard trap and this gate alone will not flag its absence |
| 13 | Reduced-motion render diff | **Must differ where motion exists AND still look designed** |
| **13a** | **Pause/Stop/Hide affordance audit (new, closes a recorded BLOCKING gap — WCAG 2.2.2, Level A)** | Every marquee, ticker, ambient background-motion layer, or particle layer that moves continuously for more than 5 seconds and runs alongside other content must have a working pause/stop/hide control. Pass condition: every container tagged with a continuous-motion cost class (the same tagging used by gate 4a) resolves a non-null **pause-affordance reference**, and that control is keyboard-operable and does what it claims. **This is a Level A criterion, not stylistic** — unlike 2.3.1 (photosensitivity, gate 14) and 2.5.4 (motion actuation, gate 15) which are conditional on specific triggers, this gate is unconditional wherever qualifying continuous motion exists, because marquee/ticker and decorative-background-layer containers are already in the v1 component set. axe-core does not reliably catch this criterion, so it cannot be folded into gate 5. **Cross-reference note (requires coordination outside this section):** the container contract (§9 motion spec) needs a required `pauseAffordanceRef` field, parallel to its existing trigger and reduced-motion-variant-ref fields, so an unpausable marquee is **structurally unbuildable** rather than merely caught late at LOCK. This section defines the enforcing gate; the schema change is owned by §9 and is flagged here as an open coordination item, not fabricated as already done. |
| 14 | Photosensitivity scan (2.3.1) — **conditional** on strobe/glitch-tagged assets | ≤3 flashes/sec above the size/contrast threshold. Trace Center PEAT-equivalent frame analysis |
| 15 | Motion-actuation check (2.5.4) — **conditional** on device-orientation-driven assets | UI alternative exists and motion-triggering is disableable |
| 16 | Responsive preflight (overlap, overflow, fixed heights, free-position counts, no-mobile-plan blocks) at 320/390/768/1280/1440 | Zero blocking findings. **320 is added below the prior report's capture matrix because that is where text-reflow blowouts actually appear** |
| 17 | Long-string reflow fuzz (40-char unbroken token at 320px) | No overflow |
| 18 | 200% zoom reflow | No horizontal scroll, no content loss |
| 19 | Pseudolocalisation (+35% string expansion) | No overflow or truncation |
| 20 | `lhci` performance budget — median-of-3, mobile, simulated Slow-4G (1.6 Mbps down / 750 Kbps up / 150ms RTT, Lighthouse's documented default) + 4× CPU | **LCP ≤2.5s, CLS ≤0.1** (internal stretch 0.05), **INP ≤200ms** (or TBT ≤600ms floor / 300ms aspirational as proxy), **pre-LCP transfer ≤1.5–2MB** (not total page weight). **This is the canonical threshold statement for this product; §19's acceptance criteria A66/A67 must be read as subordinate to it.** A recorded gap found A66 omitting INP entirely and A67 stating a flat ≤2MB instead of the ≤1.5–2MB range used here — that is a **cross-section inconsistency this subagent cannot fix directly** (A66/A67 live outside §13's file). Flagged as an **open item requiring a §19 edit**: add INP (or the TBT proxy) to A66, and reconcile A67's flat 2MB against this gate's 1.5–2MB range so only one number survives. |
| 21 | Font-loading audit | `font-display: swap` on every `@font-face`; preload only the committed 2–3 families; **blocks a 4th family sneaking in via a late component swap**. **Extended (closes a recorded MAJOR gap): every `@font-face` must also ship a metric-matched local fallback** — `size-adjust`, `ascent-override`, `descent-override`, and `line-gap-override` computed from the real, selected font binary's own metrics, not guessed or copied from a generic system-font table. This computation can only happen **after** the human's typeface pick is final, because it needs the actual font file — the claude.ai design-system generation step cannot produce it. Framed against D1: this is a **derived value**, computed from the chosen direction/typeface rather than picked independently, so it belongs in the same "computed, not picked" family as spacing/radius/shadow scales — not a new kind of decision. Gate 21 fails if any committed `@font-face` lacks a matching local-fallback declaration, or if CLS attributable to font-swap (measured via a layout-shift-source breakdown, not just the aggregate CLS number in gate 20) is not ~0. **Cross-reference note (requires coordination outside this section):** §7/§8's token taxonomy should list "font fallback metrics" explicitly as a derived, non-pickable token family; this section only defines the gate that enforces it once §7/§8 names it. |
| 22 | SEO / structured-data validation | §13.6 |
| 23 | Broken-link + console-error sweep, HTTPS/mixed-content check | Zero |
| **23a** | **Asset-reference resolution (new, closes a recorded MAJOR gap)** | Walk every `url()`, `font-family`, SVG `id` reference, and asset path in the **built output** and assert each one resolves to (a) an entry in `assets/manifest.json` and (b) an actual file on disk. Pass condition: **zero dangling references, zero references to a remote host** (the whole point of the exported, self-contained static site in D3). This closes a distinct failure class from gate 26: licence-manifest completeness (gate 26) confirms every *recorded* asset carries a licence; it does not confirm every *referenced* asset actually exists. Without this gate, a hallucinated or stale asset path (the class of failure documented elsewhere in this research as the "Scale AI lesson") ships as a silently broken image or missing font with no error anywhere in the pipeline. Placed here, between the link/console sweep (23) and the no-JS check (24), because it is deterministic and file-system-local — cheaper than gate 24's rendered crawler view, and logically a precondition for it (no point checking the no-JS render if assets it depends on are already known to be missing). |
| 24 | No-JS render check | Content visible, nav usable, forms submittable. **Also the crawler's view** |
| 25 | Anti-slop advisory pass | **Non-blocking, logged** — see §13.7, §13.8 |
| 26 | Asset licence-manifest completeness | Every font and image has a recorded licence class; commercial foundry faces emit a **pre-launch blocker** |
| 27 | LOCK purity gates 1–5 (§12.5) | All pass |
| 28 | Evidence bundle assembled | §15.6 |

**Total gate count note:** the checklist is now 28 base gates plus 4 lettered insertions (4a, 11a, 13a, 23a) — 32 checks in total. This is reflected in the LOCK wall-clock budget in §13.1, which was sized with these additions in mind rather than against the original 28.

### 13.5 Core Web Vitals as of 2026

| Metric | Good | Poor | Note |
|---|---|---|---|
| LCP | ≤2.5s | >4.0s | |
| CLS | ≤0.1 | >0.25 | Internal stretch target 0.05 ⁶ |
| INP | ≤200ms | >500ms | **Replaced FID in March 2024.** Now the most commonly failed vital (~43% of sites) — meaning main-thread cost from motion is a live risk, not theoretical |

Only ~43% of mobile origins and ~54% of desktop origins pass all three. **[V — web.dev/corewebvitals, 75th-percentile methodology; HTTP Archive Web Almanac 2024 pass rates]**

**A dragged-in unoptimised photo blows LCP single-handedly.** A modern phone shoots 4032×3024 at 2–5MB. Under Lighthouse's documented Slow-4G profile that is roughly **10–25 seconds of transfer alone** — instantly "poor." Since the product is explicitly about a human freely swapping in artwork, this is the **expected common path, not a corner case**. The fix belongs at **drop time**, not lock time. **[V — thresholds and throttling profile; file-size arithmetic is inference]**

### 13.6 SEO / structured-data gate (all mechanically verifiable)

Unique `<title>` per page; meta description 50–160 chars; canonical URL; Open Graph + Twitter Card including an image; `<html lang>` matching the interview language; **single `<h1>` with no skipped heading levels** (an accessibility overlap — screen-reader navigation depends on it); 100% image alt coverage; `robots.txt` + `sitemap.xml` generated from the page tree; **JSON-LD matched to the site-type answer** (Organization/WebSite for marketing, VideoGame for game promo, WebApplication for app shell, FAQPage/BreadcrumbList where those sections exist) validated against schema.org.

### 13.7 Severity tiers — what blocks what

| Tier | Blocks | Examples | Surfacing |
|---|---|---|---|
| **0** | The individual placement/edit from completing | Contrast <3:1 on placed text; target <24px with no valid exception; missing alt/decorative choice on a new image; duplicate ARIA id | Inline, immediate |
| **1** | LOCK only — never interrupts live editing | Full-page axe critical/serious; `lhci` budget miss beyond the floor; 320px reflow breakage; missing required structured-data fields; unresolved asset-licence gap; **missing skip link (11a); missing pause/stop/hide affordance on qualifying motion (13a); dangling asset reference (23a); motion-concurrency cap exceeded (4a)** | The gate report |
| **2** | Nothing — advisory, dismissible | APCA good-but-not-great; non-optimal image format; duration slightly out of band; **the anti-slop advisory**; **motion-variant homogeneity signal (§13.8) — using many distinct motion "kinds" from the catalog on one site**; **motion-concurrency count approaching (but not yet exceeding) a 4a cap, surfaced early via the live counter in §13.3** | Batched into the Design Health pill, **never a toast stream** |
| **3** | Nothing — silent telemetry | Minor spacing deviations under free-position; motion-library usage stats | End-of-session digest |

**Mechanics:** debounce live checks to fire on drop/mouseup (never mid-drag, never per-frame); collapse repeated violations of the same rule into one counted badge; gate all Tier-2 surfacing through the single Design Health pill.

**Ambient badges beat blocking dialogs during editing; hard gates belong only at LOCK.** Most problems are cheaply detectable without a model in the loop, and a non-designer will not tolerate hard blocks mid-edit.

### 13.8 The anti-slop lint changes role (argued both ways, resolved)

**For keeping it strict:** the human only chooses a *direction* among ~10; the editor still auto-places components from that direction before the human touches anything, and the claude.ai-side generation is itself subject to the same distributional-median pressure the prior report documented (Tailwind's 2019 indigo-500 default propagating into "every AI interface is purple"). An unlinted generation can hand the human a pre-homogenised menu where every "direction" still routes through the same three icon-card layouts.

**Against:** a human who saw 10 directions and deliberately picked the purple gradient one is exercising the exact taste-agency this product exists to enable. Mechanically blocking `bg-indigo-500` after a real choice contradicts the premise, and several "tells" (icon-topped 3-col grids, rounded cards) are legitimate patterns for specific content.

**Resolution:** demote to a **Tier-2 advisory at the human-edit layer** with a permanent per-element dismiss, and keep it as a **hard gate only upstream** — linting the claude.ai-generated design-system JSON **before the human ever sees the menu of choices**. The upstream gate is load-bearing, not optional, once the downstream gate is softened.

The 16 machine-detectable tells: purple-to-blue gradients (Tailwind blue-600/purple-500 defaults), Inter everywhere, uniform 16px radii + 24px padding, three-card layouts with tiny icons, badge-above-H1 heroes, serif-italic accents, generic stat banners, low-contrast dark mode, glassmorphism. Analysis of 1,590 Show HN pages: 22% heavy slop, 32% mild, 46% clean; ~75% of commercial pages launched Q1 2026 carry at least one strong signature. **[V — 925studios analysis, Hallmark's 57 detection gates, Developers Digest cataloguing]**

**Motion-consistency signal (new, closes a recorded MAJOR gap).** The static-visual anti-slop lint above has a motion-side blind spot the upstream gate structurally cannot see: it lints the claude.ai-generated design-system JSON *before* the human sees the menu, but the catalog is deliberately broad (D1's "10 variants per swappable component on demand" extends to motion — a component may offer, say, 6–10 scroll-reveal variants). Catalog **breadth** is intentional and good; deployment **restraint** is a separate concern the upstream gate never touches, because mixing many distinct motion "kinds" happens downstream, at the moment a human freely swaps components via the component bar — exactly the frictionless action this product is built around. A site that uses four different section-reveal styles, two different hover-treatment families, and a bespoke cursor animation can pass every static anti-slop tell and still read as visually undisciplined. Resolution, consistent with §13.7's existing severity model: a **Tier-2 Design Health entry**, non-blocking, one-click dismiss, that counts distinct motion "kinds" in active use per site and surfaces a soft warning at **3 or more distinct variants of the same kind** (e.g., 3+ different scroll-reveal treatments) with the framing "sites read as more designed with 1–2." The threshold of 3 is carried over from the prior research as a **reasonable-sounding default, not independently validated against user testing** — treat it as a starting point subject to revision once real usage data exists.

### 13.9 Never claim certification

Deque's own Accessibility Coverage Report (13,000+ pages/page-states, ~300,000 issues) found axe-based automated testing catches **57.38%** of real accessibility issues **[V]**. Running axe + Pa11y + Lighthouse + all the live checks raises the floor meaningfully but does not close the gap. Since this product replaces the AI *aesthetic* judge with a human but does **not** add a human *accessibility* judge, the honest claim is **"passed N automated + structural gates,"** never "WCAG 2.2 AA certified." The evidence bundle carries an explicit named gap for manual/screen-reader review.

### 13.10 APCA posture

APCA models perceived contrast more accurately for the dark, cinematic, large-type palettes award sites favour, but it is a candidate for WCAG 3.0 (still draft as of 2026) and **has no independent legal standing today**. The defensible posture is a **dual gate**: pass WCAG 2 (4.5:1 / 3:1) **and** compute APCA as a stricter internal target. Both are pure two-colour arithmetic, so both run live for free. **[V — APCA draft status, git.apcacontrast.com; the Lc75/60/45 bands are inherited from the prior swarm report and not independently re-verified — see §20.3]**

### 13.11 Open items recorded by this revision (no known mitigation beyond what's stated above, or requiring a decision/edit outside this section)

These are named explicitly rather than silently resolved, per this revision's instructions:

- **LOCK wall-clock budget (§13.1):** the p50 ≤90s / p95 ≤180s figures are an inference sized against the newly-expanded 32-gate list, not a measured result from a working prototype. **Requires validation** once a real multi-page build can be timed end to end; the sampling fallback for gate 20 (representative pages instead of every page) is likewise unproven at scale.
- **Motion-concurrency caps (gate 4a):** the specific numbers (1 WebGL scene / 1 particle layer / 2 autoplay videos / 2–3 pinned sequences) are carried over from prior research, not benchmarked against this product's actual render stack. **Requires a user decision or a benchmarking pass** before being treated as a hard ceiling rather than a working default.
- **Skip-link component ownership (gate 11a):** this section defines the enforcing gate and a recommended 2-variant default, but adding the actual component entry to the v1 inventory is owned by §8/§18, not this section. **Requires a cross-section edit** to close fully.
- **Pause/Stop/Hide schema field (gate 13a):** this section defines the enforcing gate, but the underlying `pauseAffordanceRef` field on the container contract is owned by §9's motion spec. **Requires a cross-section edit** to close fully — without it, gate 13a can only be a post-hoc catch rather than a structurally-unbuildable-otherwise guarantee.
- **Font-metric-override token family (gate 21):** this section defines the enforcing gate and grounds the requirement in D1's "derived, not picked" principle, but §7/§8's token taxonomy does not yet name "font fallback metrics" as an explicit derived family. **Requires a cross-section edit** to close fully.
- **A66/A67 reconciliation (gate 20):** this section states the canonical INP + pre-LCP-transfer thresholds, but §19's acceptance criteria A66 (missing INP) and A67 (flat ≤2MB vs. this gate's ≤1.5–2MB range) were recorded as inconsistent with it. **Requires a §19 edit**, which is out of this subagent's scope; flagged here so it is not silently lost.
- **Motion-consistency threshold (§13.8):** the "3 or more distinct variants of the same kind" trigger is a carried-over default, not independently validated. **No known mitigation beyond stating it as provisional** until real usage data exists.

---
