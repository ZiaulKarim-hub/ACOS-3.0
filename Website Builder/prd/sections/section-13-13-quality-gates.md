## 13. Quality gates

### 13.1 The dividing line

Not "a11y vs performance" but **scoped arithmetic/DOM-read vs whole-document render pass**.

- **LIVE** (sub-100ms, fires on drop/mouseup — **never mid-drag, never per-frame** — scoped to the touched subtree)
- **LOCK-TIME** (seconds to tens of seconds, whole-document, batch)

`axe.run(context)` supports scoped runs natively **[V]**; Lighthouse's throttled multi-second run cannot happen per-frame **[V]**.

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

### 13.4 The ordered lock-time checklist

Ordering follows cheapest-and-most-foundational-first: the build must succeed before anything downstream is meaningful; deterministic gates before anything requiring a render pass.

| # | Gate | Threshold / pass condition |
|---|---|---|
| 1 | Build/export succeeds | Zero errors |
| 2 | `wb verify` — regenerate to temp, `diff -r` | Empty diff |
| 3 | Token/CSS lint (`stylelint-declaration-strict-value` + raw hex/px grep) | Zero raw values outside the token system |
| 4 | Six coherence lints (§7.12) | All pass; lint 6 (border-only ⇒ zero shadow tokens) is the one that catches human-visible incoherence |
| 5 | Full-page axe-core sweep (adds landmark-unique, region, heading-order, doc-wide duplicate-id) | **Zero critical/serious** |
| 6 | Pa11y cross-check (HTML_CodeSniffer WCAG2AA) | Second ruleset; raises coverage without claiming completeness |
| 7 | WCAG 2 + APCA contrast sweep, text **and** non-text (1.4.3, 1.4.11) | 4.5:1 / 3:1 / 3:1; APCA Lc75 body, Lc60 large-bold, Lc45 large-non-text ⁵ |
| 8 | Target-size sweep on published-site controls (2.5.8) | 24×24 CSS px, exceptions applied |
| 9 | Dragging-alternative audit for widgets built via Step 6 (2.5.7) | Every drag affordance has a documented single-pointer alternative |
| 10 | Reflow at 320 CSS px (1.4.10) + text-spacing stress (1.4.12) | No 2D scroll except exempted content (data tables, images, toolbars, maps). **Free-positioned elements get mandatory extra scrutiny** |
| 11 | Free-position breakpoint audit | Re-project at 320/390/768/1440; auto-demote anything with no narrow-viewport position; **refuse to lock on document `overflow-x` or parent-box escape** |
| 12 | Playwright keyboard tab-walk (2.4.3, 2.4.7, 2.4.11) | Focus order matches visual order; no traps; ring visible at every stop (≥3:1 against adjacent, non-zero outline); nothing obscured |
| 13 | Reduced-motion render diff | **Must differ where motion exists AND still look designed** |
| 14 | Photosensitivity scan (2.3.1) — **conditional** on strobe/glitch-tagged assets | ≤3 flashes/sec above the size/contrast threshold. Trace Center PEAT-equivalent frame analysis |
| 15 | Motion-actuation check (2.5.4) — **conditional** on device-orientation-driven assets | UI alternative exists and motion-triggering is disableable |
| 16 | Responsive preflight (overlap, overflow, fixed heights, free-position counts, no-mobile-plan blocks) at 320/390/768/1280/1440 | Zero blocking findings. **320 is added below the prior report's capture matrix because that is where text-reflow blowouts actually appear** |
| 17 | Long-string reflow fuzz (40-char unbroken token at 320px) | No overflow |
| 18 | 200% zoom reflow | No horizontal scroll, no content loss |
| 19 | Pseudolocalisation (+35% string expansion) | No overflow or truncation |
| 20 | `lhci` performance budget — median-of-3, mobile, simulated Slow-4G (1.6 Mbps down / 750 Kbps up / 150ms RTT, Lighthouse's documented default) + 4× CPU | **LCP ≤2.5s, CLS ≤0.1** (internal stretch 0.05), **INP ≤200ms** (or TBT ≤600ms floor / 300ms aspirational as proxy), **pre-LCP transfer ≤1.5–2MB** (not total page weight) |
| 21 | Font-loading audit | `font-display: swap` on every `@font-face`; preload only the committed 2–3 families; **blocks a 4th family sneaking in via a late component swap** |
| 22 | SEO / structured-data validation | §13.6 |
| 23 | Broken-link + console-error sweep, HTTPS/mixed-content check | Zero |
| 24 | No-JS render check | Content visible, nav usable, forms submittable. **Also the crawler's view** |
| 25 | Anti-slop advisory pass | **Non-blocking, logged** — see §13.7 |
| 26 | Asset licence-manifest completeness | Every font and image has a recorded licence class; commercial foundry faces emit a **pre-launch blocker** |
| 27 | LOCK purity gates 1–5 (§12.5) | All pass |
| 28 | Evidence bundle assembled | §15.6 |

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
| **1** | LOCK only — never interrupts live editing | Full-page axe critical/serious; `lhci` budget miss beyond the floor; 320px reflow breakage; missing required structured-data fields; unresolved asset-licence gap | The gate report |
| **2** | Nothing — advisory, dismissible | APCA good-but-not-great; non-optimal image format; duration slightly out of band; **the anti-slop advisory** | Batched into the Design Health pill, **never a toast stream** |
| **3** | Nothing — silent telemetry | Minor spacing deviations under free-position; motion-library usage stats | End-of-session digest |

**Mechanics:** debounce live checks to fire on drop/mouseup (never mid-drag, never per-frame); collapse repeated violations of the same rule into one counted badge; gate all Tier-2 surfacing through the single Design Health pill.

**Ambient badges beat blocking dialogs during editing; hard gates belong only at LOCK.** Most problems are cheaply detectable without a model in the loop, and a non-designer will not tolerate hard blocks mid-edit.

### 13.8 The anti-slop lint changes role (argued both ways, resolved)

**For keeping it strict:** the human only chooses a *direction* among ~10; the editor still auto-places components from that direction before the human touches anything, and the claude.ai-side generation is itself subject to the same distributional-median pressure the prior report documented (Tailwind's 2019 indigo-500 default propagating into "every AI interface is purple"). An unlinted generation can hand the human a pre-homogenised menu where every "direction" still routes through the same three icon-card layouts.

**Against:** a human who saw 10 directions and deliberately picked the purple gradient one is exercising the exact taste-agency this product exists to enable. Mechanically blocking `bg-indigo-500` after a real choice contradicts the premise, and several "tells" (icon-topped 3-col grids, rounded cards) are legitimate patterns for specific content.

**Resolution:** demote to a **Tier-2 advisory at the human-edit layer** with a permanent per-element dismiss, and keep it as a **hard gate only upstream** — linting the claude.ai-generated design-system JSON **before the human ever sees the menu of choices**. The upstream gate is load-bearing, not optional, once the downstream gate is softened.

The 16 machine-detectable tells: purple-to-blue gradients (Tailwind blue-600/purple-500 defaults), Inter everywhere, uniform 16px radii + 24px padding, three-card layouts with tiny icons, badge-above-H1 heroes, serif-italic accents, generic stat banners, low-contrast dark mode, glassmorphism. Analysis of 1,590 Show HN pages: 22% heavy slop, 32% mild, 46% clean; ~75% of commercial pages launched Q1 2026 carry at least one strong signature. **[V — 925studios analysis, Hallmark's 57 detection gates, Developers Digest cataloguing]**

### 13.9 Never claim certification

Deque's own Accessibility Coverage Report (13,000+ pages/page-states, ~300,000 issues) found axe-based automated testing catches **57.38%** of real accessibility issues **[V]**. Running axe + Pa11y + Lighthouse + all the live checks raises the floor meaningfully but does not close the gap. Since this product replaces the AI *aesthetic* judge with a human but does **not** add a human *accessibility* judge, the honest claim is **"passed N automated + structural gates,"** never "WCAG 2.2 AA certified." The evidence bundle carries an explicit named gap for manual/screen-reader review.

### 13.10 APCA posture

APCA models perceived contrast more accurately for the dark, cinematic, large-type palettes award sites favour, but it is a candidate for WCAG 3.0 (still draft as of 2026) and **has no independent legal standing today**. The defensible posture is a **dual gate**: pass WCAG 2 (4.5:1 / 3:1) **and** compute APCA as a stricter internal target. Both are pure two-colour arithmetic, so both run live for free. **[V — APCA draft status, git.apcacontrast.com; the Lc75/60/45 bands are inherited from the prior swarm report and not independently re-verified — see §20.3]**

---

