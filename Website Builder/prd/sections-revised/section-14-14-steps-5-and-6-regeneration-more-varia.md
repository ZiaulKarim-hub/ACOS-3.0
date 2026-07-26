## 14. Steps 5 and 6 — regeneration, more variants, redesign, custom components

### 14.1 More variants (deterministic, no model call)

"Generate 10 variants of this component on demand" must **not** be implemented as parallel subagents writing files. **Subagents are policy-blocked from the `Write` tool in this environment — verified twice** (MEMORY.md `reference_subagent_write_blocked`, 2026-07-07, and a live re-confirmation on 2026-07-18 whose Write call was rejected with *"Subagents should return findings as text, not write report files"*). Bash heredoc writes are not blocked. **[V — first-party]**

**Correct design:** `variants.ts` — a deterministic generator that reads the chosen direction's tokens and emits parameterised component markup. No model call, no Write block, instant, and **it guarantees the variants stay inside the direction, which is D1's whole point**.

| Operation | Behaviour |
|---|---|
| **More variants** | Next N for the slot, using the skill-supplied current highest index so numbering is **append-only** and cannot collide with previously-ingested variants |
| **More like this** | 5 deterministic neighbours of the selected (already-approved) variant, appended to the bar. **Satisfies "ask for more variants" without ever presenting a 30-item wall, and keeps new options anchored to something the user already liked** |
| **Lazy generation** | Generate on first open of a family's swap panel; cache per direction; **never pre-generate families the site does not use**. Ten variants × ~12 families is ~120 component variants per direction — eager generation stalls Step 4 |

### 14.2 Redesign the system, or part of it

| Scope | Behaviour |
|---|---|
| **Partial** (e.g. "new colour, keep the type") | Re-enter Step 2 with the current direction vector, marking which of the 26 slots are frozen and which are open. Because ≥60% of artwork is token-referencing, most art re-skins for free |
| **Full** | A new Step-2 cycle with prior identity as **negative constraint** |

**Migration is mandatory and must never silently drop a node.** A new `system.lock.json` invalidates every variant reference. The migration report: map old variant ids to new; list unmappable nodes explicitly; the user resolves each. This is logged as an explicit operation, not an implicit side effect.

**Layout survives a direction swap** — placement is stored as grid integers and token indices, so a direction change can keep placement and re-resolve tokens, *provided both directions share the same grid spec*. That is why `layout.breakpoints` and `type.viewport-endpoints` are marked `n/a` (identical across all directions) in §7.

### 14.3 Cross-direction component swaps — the unresolvable tension, made visible

The user is in Direction 3 (warm paper, editorial serif, 600ms fades, 2px radius). They see Direction 7's neon pill button in the bar and want it. **Two implementations, both bad:**

| Option | What happens | Why it fails |
|---|---|---|
| **A — Re-skin** (button references roles) | The pill inherits Direction 3's terracotta, 2px radius, slow easing | It is no longer neon, no longer a pill, no longer the thing they pointed at. The swap "worked" and produced something they didn't want; they conclude the bar is broken |
| **B — Transplant** (button carries literal values) | The site now has two accent hues, two radius scales, two motion languages | The token lint fires; and every future direction-level change leaves this button behind, permanently |

**Resolution — make the tension visible rather than pretending it is solved:**

1. The swap UI shows **both renderings side by side**, labelled *"Fitted to your direction"* and *"Kept as designed (adds 6 off-system values)."* The user picks explicitly.
2. Transplants are recorded in a visible **coherence-debt ledger** with a count.
3. A soft cap (≈3 transplants) triggers the genuinely useful move: **"You have transplanted 4 components from Direction 7 — switch the whole site to Direction 7 and transplant these 4 back the other way?"** No existing tool offers this.
4. **Do not block cross-direction swaps.** Blocking is what makes the user abandon the direction model entirely.

### 14.4 Typed slot contracts and the content orphanage

**Failure scenario:** hero variant A has `{headline, subhead, cta}`. The user swaps to variant B with `{eyebrow, headline, subhead, cta_primary, cta_secondary, stat_row[3]}`. Where does their carefully-written CTA label go? What fills the eyebrow and the three stats? **If the tool auto-fills with lorem or an AI guess, the user now has fake statistics on a live page and may not notice.** Swap back to A and the eyebrow and stats are gone permanently. Do it twice and original copy is lost with no undo path across the swaps.

**Contract:**

1. Every component declares a typed slot contract: `{name, type, cardinality, required}`.
2. The component bar **only offers variants whose contract is a superset or exact match**, and states **before** the swap: *"this variant adds 4 slots"* / *"this variant has no place for: [stat_row]"*.
3. **Content orphanage:** anything the target cannot hold moves to a visible parked panel, **never deleted**, and is auto-restored if a later swap re-introduces the slot.
4. Newly-created empty slots render as **visibly-flagged placeholders that BLOCK LOCK** until filled or deleted. **This is what prevents fake stats shipping.**
5. Slot names are part of the component contract and validated on swap.

### 14.5 Custom components (Step 6)

Three paths:

| Path | When | Mechanism |
|---|---|---|
| **Registry** | Whitelisted families: table, chart, embed, form | Deterministic generator against the direction's tokens + the dataviz sub-token set. **v1 caps custom components to this whitelist; everything else is explicitly out of scope** |
| **Agent-authored** | A genuinely novel component | `Task(general-purpose)` with a role prompt from the skill's `prompts/` dir. **Returns code as TEXT; the main thread writes it** (subagent Write is blocked). Runs the six coherence lints before acceptance |
| **Custom code block** | The signature moment, or anything the system shouldn't own | An **opaque draggable container** holding hand-written HTML/CSS/JS. The editor positions it but **never introspects** it. **This is where the quality ceiling actually lives** |

**The `component.custom-slot` registration contract is the gate that makes this safe:** a custom component enters through a door that enforces token usage, or every custom addition is an incoherence vector.

### 14.6 Charts, specifically

A chart is not one component. It decomposes into four parts:

| Part | Content |
|---|---|
| **Marks** | 12 types: line, area, bar/column, pie/donut, gauge, scatter/bubble, heatmap, funnel, radar, waterfall, treemap, map |
| **Chrome kit** | axes, gridlines, ticks, labels, legend, tooltip, annotation/reference line, zero-line — **4 treatments applied across all 12 marks, which is what makes a site's charts read as one system** |
| **Colour ramps** | categorical / sequential / diverging, **derived from the direction's OKLCH anchors, never picked**, validated colourblind-safe in both schemes |
| **Data states** | empty, loading, partial (filter returned nothing), error, single-data-point — **required in the editor** (see scope note immediately below), because charts fail more often here than in the happy path |

**Scope of "required" data states, reconciled with the static build target (closes a recorded gap):** §16.2 commits v1 to a static export that ships **zero runtime JS** to visitors, and §14.6 above commits v1 chart rendering to **build-time SVG** — i.e. charts are pre-rendered once, at publish time, from whatever data was present then. On that architecture there is no live client-side data fetch in the published site, so "loading" and "error" are not states a visitor's browser can ever actually enter — there is nothing to load and nothing to fail at runtime.

These four data states are therefore **editor-only design-time previews, not shipped runtime behaviour, in v1**:

- In design mode, the component bar lets the user preview a chart in each of the five states (empty, loading, partial, error, single-data-point) purely as **static mockup renderings**, so the direction's chart chrome is verified to hold up under bad data before it ever meets real data. This is a design-QA tool, not a live capability.
- **Only two of the five are ever shipped to the static output**, because only two can be true facts about a snapshot of data at publish time: **empty** (the dataset genuinely had zero rows) and **single-data-point** (the dataset genuinely had exactly one row). Both render as ordinary pre-rendered SVG, no different in kind from the happy-path chart.
- **"Loading" and "error" are never shipped in v1.** They exist solely as editor previews so the designer can see and approve the chart chrome's failure-state treatment in advance. If a future version (see below) adds a live data mode, these two states become real, functional, and shipped at that point — not before.
- **"Partial" (filter returned nothing) is v1-shippable only for a build-time, statically-evaluated filter** (e.g. a published page that pre-computes one fixed filtered view) — it is not the same as a visitor interactively filtering client-side, which is out of scope for v1's zero-shipped-JS static architecture and belongs with the "interactive/dashboard-grade" charts explicitly deferred to v3 below.
- This distinction — editor-preview vs shipped-runtime — must be visible in the tool itself: the state-preview control in the swap/preview bar is labelled *"Preview only — not shown to visitors"* for loading and error, so the user does not mistake a design QA aid for a live feature and is not surprised when it is absent from the published site.

shadcn/ui ships "Chart" as a single registry entry; Untitled UI splits Line & bar (8), Pie (3), Radar (3), Gauges (3), Progress circles (1) — **both under-model the chrome. [V — fetched]** The local `dataviz` skill already encodes a form heuristic, a colour formula with a runnable validator, mark specs, interaction rules, and a palette reference at `references/palette.md`. **Reuse it as the chart sub-system spec rather than reinventing.**

**Decide early: build-time SVG or a client library.** A charting library is real client JavaScript on a static marketing page, and 12 marks at v2 may require a runtime that undermines the performance gate. **v1 default: build-time SVG.** Interactive/dashboard-grade charts are v3 and pull in tooltips, brushing, legends-as-filters, and a dependency the performance budget must absorb — this is also where "loading," "error," and interactive "partial" (client-side filtering) become real, shipped, functional states rather than editor previews.

### 14.7 The signature moment is not a variant set

The prior report's Findings 2 and 6 are explicit that award-tier winners have exactly **one** bespoke signature moment, and that treating identity-carrying choices as generic catalogue picks is **the root mechanism of AI-design homogenisation** (Finding 5). If the component bar offers "10 signature-moment variants" the way it offers 10 button styles, **it mechanically reproduces the sameness problem the whole prior research effort diagnosed.**

Correct treatment: 2–3 bespoke **concept** candidates generated at Step 2 tied to the specific brand narrative, chosen and refined at Step 4, and handled thereafter through the custom code block. **A lint flags a second signature moment.** A system that lets the user pick five produces a worse site than one that lets them pick none.

---
