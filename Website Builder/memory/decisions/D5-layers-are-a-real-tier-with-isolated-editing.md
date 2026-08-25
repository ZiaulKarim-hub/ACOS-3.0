# D5 — Layers are a real document tier, and editing one never disturbs the layers below

**Status:** SETTLED · **Date:** 2026-08-20 · **Decided by:** Zee, in conversation
**Do not reopen.** A later session may implement this; it may not re-litigate it.

## Context

The user's instruction: *"The background and foreground of the website work should be
separate, first do the background work, and then add the foreground stuff to it."* Offered two
readings — (a) an authoring-ORDER rule with the model unchanged, or (b) a structural layer
split — the user chose **(b)**, and added the governing requirement in the same breath:
*"being able to work on separate layers without changing the bottom layer/layers would allow
for a lot of flexibility."*

**What the PRD had before this decision.** Background was a *component you place*, not a tier
the page sits on. Three pieces carried it and none of them constituted a layer system:

- `Decorative background layer` — a container kind, 10 structural variants, v1, Tier A,
  user-named. §9.2 notes it "covers the largest pixel area of any component."
- `Background ambient motion` — an animation kind, 8 variants, v1; its heaviest sub-variant
  (particle field) is v3-gated and inherits `costClass: gpu`.
- `layout.z-index-scale` — Primer's ladder adopted verbatim: behind (−1), default,
  sticky (100), dropdown (200), overlay (300), modal (400), popover, skipLink. A `behind`
  rung existed; nothing organised the page into authorable tiers.

§11.1's four-level layout contract had no depth axis at all:

1. **Page** = a vertical list of sections. Reorder-only.
2. **Section** = a real CSS Grid — 12/6/4 tracks with `fr` units.
3. **Block** = integer `grid-column` / `grid-row` placement, per breakpoint.
4. **Inside a block** = flow only (hug / fill / fixed). Never coordinates.

## Decision

### 1. A layer is a new tier, inserted between Section and Block

Levels 1–4 above are a *containment* axis. A layer is a *depth* axis, so it does not append as
a fifth level — it splits the old level 2. The revised contract is **five levels**:

1. **Page** = a vertical list of sections, plus at most one optional **page backdrop layer**.
   Reorder-only.
2. **Section** = an ordered **stack of layers**, bottom to top.
3. **Layer** = a real CSS Grid — 12/6/4 tracks with `fr` units. Every layer in a section shares
   that section's track definition, without exception.
4. **Block** = integer `grid-column` / `grid-row` placement **on exactly one layer**, per
   breakpoint.
5. **Inside a block** = flow only (hug / fill / fixed). Never coordinates.

### 2. Sections own layer stacks. The page owns at most one backdrop, and it carries no content

This follows from level 1 being reorder-only, and the derivation is the reason for the rule
rather than a preference: if layers were page-wide and blocks lived on them, reordering a
section would slide its blocks out from under the artwork they were composed against. Section-
owned stacks make reorder safe by construction.

The **page backdrop layer** is the deliberate exception, for the case of one continuous wash or
scene behind the whole page. To keep reorder safe it is **art and motion only — no component
blocks may be placed on it.** A page backdrop holding content would reintroduce exactly the
breakage the section-owned rule exists to prevent.

### 3. Layer isolation is enforced structurally, not by UI convention

The user's requirement — work on a layer without changing the ones below — is delivered as two
distinct guarantees, because a UI-only version of this promise is not checkable.

**Edit isolation (the surface).** Exactly one layer is **active** at a time. Clicks, drags,
the grid overlay, and the component bar target only the active layer. Lower and upper layers
render normally but are **inert**: they cannot be selected, moved, or swapped by accident.

**Write isolation (the invariant).** §12.1 already makes `pages/<id>.doc.json` the only thing
the editor mutates, and §12.9 already models history as an op log with inverse patches. That
makes the guarantee mechanical rather than aspirational:

> **Layer-scoped writes.** Every op the editor emits carries a `layerId`. An op whose target
> node's `layerId` differs from the op's own `layerId` is **rejected**, not applied.

This is the checkable form of "without changing the bottom layers." It is an assertable
invariant over the op log, and it belongs in §12.9 as a validity rule on op application.

### 4. Overlay-class content never lives on a layer

§7.5 already carries the sharpest trap in the document: because D4 puts animations inside
draggable containers, a transformed art container **silently traps every dropdown inside it**,
presenting to the user as "the menu is behind the picture" with no obvious cause. A formal
stack of independently-animatable layers makes that failure *more* likely, not less.

**Rule:** every overlay-class node — dropdown (200), overlay (300), modal (400), popover,
skipLink — renders into a **page-level overlay root outside the layer stack entirely.**
`layout.z-index-scale` is preserved exactly as adopted; what changes is that the trap becomes
structurally impossible rather than lint-detectable after the fact.

### 5. Existing background pieces are re-homed, not re-invented

`Decorative background layer` (10 variants) and `Background ambient motion` (8 variants) stop
being components placed *inside* a section and become the default occupants of a section's
**bottom layer**. Their variant counts, priorities and Tier-A status are unchanged. No new
inventory rows are created by this decision.

### 6. The user's build-order request is delivered as a consequence, not instead

Step 4 gains an explicit **layer-ordered build**: the bottom layer of a section is composed and
approved before work moves up the stack. The user asked for background-first authoring and for
a structural split; the structure makes the ordering natural rather than a separate rule.

### 7. No cross-layer anchoring in v1

A block anchors within its own layer's grid. Because every layer in a section shares one track
definition, a block on layer 2 aligns with a block on layer 1 **by landing on the same grid
columns** — which covers the common case without a new mechanism.

Anchoring a block to a *specific node on a different layer* is deliberately **out of v1**. It
is the same risk family as sibling anchoring, which `DECISIONS.md` decision 6 already flags as
unprototyped with "no known mitigation beyond the idea stated."

## Consequences

**Sections this decision obliges to change** (none of these edits are made by this decision
itself; they are owed):

| Section | Edit owed |
|---|---|
| §11.1 | Four-level contract becomes five. Level 2 splits into Section-owns-stack and Layer-is-the-grid |
| §11.2 | "The grid overlay must BE the grid" now reads `getComputedStyle` on the **active layer**, not the section |
| §11.4 | Free-position escape hatch is scoped to the active layer; state that cross-layer anchoring is out of v1 |
| §12.1 | Two-tier truth unchanged in shape; the scene graph gains the layer tier |
| §12.3 | The layout node gains `layerId`; the section node gains `layers[]` |
| §12.9 | Add the layer-scoped-writes validity rule to op application |
| §7.5 | `layout.stacking-context-rules` gains the overlay-root rule; the existing trap note is strengthened, not replaced |
| §9.2 | `Decorative background layer` re-homed as a bottom-layer default rather than a placed component |
| §4 Step 4 | Layer-ordered build: bottom layer composed and approved first |
| §18 | New unbudgeted effort line; **LOCK also strips** list gains layer editor-state |
| §13 | A LOCK gate asserting no layer editor-state survives into `dist/published/**` |

**LOCK (D3) is unaffected in principle and gains work in practice.** Layers are an authoring
concept; at export each layer compiles to a grid-area-stacked child carrying a z-index derived
from its stack index. Nothing editor-specific ships. But `layerId`, the active-layer flag, and
per-layer names, visibility and lock state **are editor-only state**, so LOCK must strip them
and be gated on stripping them — the same treatment §18 already gives the recovery bin,
`node.locked` freeze flags, per-section notes and `assets/manifest.json`.

**Per-breakpoint layer visibility ships with it.** Per-breakpoint visibility is already a v1
feature, compiled to a `display` rule rather than duplicate markup. Extending it from blocks to
whole layers — hide the decorative layer at 390 — is cheap and is the obvious use of it.

**No new concurrency cap is invented.** §9.5's `costClass` validator already sums across
*placed instances* and blocks placement past the cap. Layers do not change what is placed, so
the existing caps (max 1 WebGL slot, max 1 particle layer, max 2 autoplay video loops, max 2–3
pinned sequences) continue to apply unchanged across the whole stack. A layer count cap is
deliberately **not** introduced, because the cost that matters is already measured where it
occurs.

**Effort is a new unbudgeted line.** Structurally this is the same shape as the multi-page
manager: a new tier in the document model, a new panel in the editor, new LOCK strip rules, and
a new gate. §18 costs that shape at **16–24 days [I]** for Branch B. Treat layers as a
comparable line **until measured — this is an inference from structural similarity, not an
estimate of this work.** It stacks on top of decision 1's already-accepted "~16–24 days,
~25–35 days against the revised baseline," both of which are themselves tagged inference.

**Open follow-ups this decision spawns:**

- **Does the page backdrop scroll with the page, or stay fixed?** Both are legitimate and they
  look completely different. Parallax (§9.3, 5 variants, v2) is the case that needs the answer.
  Not decided here; no default is assumed.
- **Cross-layer anchoring** — out of v1 above, but genuinely open for v2, and it should be
  answered together with `DECISIONS.md` decision 6 (sibling anchoring) rather than separately,
  since they share a compile strategy.
- **Whether the layer panel is a new surface or an extension of the navigator tree.** The
  navigator tree is already mandatory in v1 with its own effort line (§20.2 disagreement 10).
  Extending it is likely cheaper than a second panel, but this has not been costed.

## Rejected alternative

**Reading (a) — an authoring-order rule with the document model unchanged.** The pipeline would
build and get approval for background work before foreground work began, but background would
remain a component placed inside a section. Rejected by the user in favour of the structural
split. Note the ordering behaviour is **not lost** — consequence 6 delivers it as a property of
the structure.

**Page-owned layer stacks with blocks on them.** Rejected on the derivation in decision 2:
level 1 is reorder-only, so page-wide content layers would let a section reorder slide blocks
out from under the artwork they were composed against.

**A layer-count cap.** Rejected as a fabricated number. The real cost is GPU and main-thread
load from placed instances, which §9.5's `costClass` validator already caps at the point where
that cost is incurred.
