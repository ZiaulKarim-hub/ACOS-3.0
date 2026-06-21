# Resume Prompt — Design Mechanics Discussion

**Paste this into the new session after `/clear`.**

---

We just finished the Ascent Park City Lender Memorandum rebuild — both FINAL PDFs are shipped (ridgeline variant, 24 pages each, at `/Users/zee/Documents/OKOA/Ascent LK Cap preso/rebuild/ascent-park-city.{A-verbatim,B-corrected}.FINAL.pdf`). **Don't touch the PDFs or the renderer; the build is done.**

The conversation has pivoted to a **meta-discussion about reusable design patterns** extracted from that work. Full context is in `memory/handoffs/2026-05-26-design-mechanics-discussion.yaml` — read it before responding.

## Where we left off

I (the prior session) walked Zee through three "renderer mechanics that aren't visible but matter" patterns in simple language with analogies. He really liked them — said they "make auto-generated designs look more natural" — and wants to continue from there. Keep these three patterns fresh in mind:

### Pattern 6a — Inter-table breathing via CSS `+` selector
- **Rule**: `.t + .t { margin-top: 6mm; }` and `.t-note + .t { margin-top: 6mm; }`
- **What it does**: targets only tables that come AFTER another table (or after a table-footnote). First table on the page doesn't match → no orphaned margin. Subsequent tables get automatic 6mm breathing room.
- **Analogy used**: "like handing out coasters at a party — only people who arrive second-or-later get one, because there's nothing before them to protect from."
- **Generalizes to**: any stack of repeated elements.

### Pattern 6b — Flex-column page-body with `margin-top: auto` for bottom-pinning
- **Rule**: `.page-body { display: flex; flex-direction: column; }` plus `.bottom-treatment { margin-top: auto; }` on the child you want pinned.
- **What it does**: `margin-top: auto` in flex column converts ALL empty space above the element into margin. If content above is short → element pins to bottom. If content above is tall → no empty space → element sits inline.
- **Analogy used**: "like a heavy book on a shelf with other books on top — if there are 2 books above, the heavy one falls until it touches the shelf; if there are 20 books above, no room left to fall through."
- **Generalizes to**: footers, copyright notices, key-takeaway panels, anything "pin-to-bottom-when-possible."

### Pattern 6c — Eyebrow folding for continuation pages
- **Rule**: when a section spans 2 pages, fold the second page's identity INTO the eyebrow ("§07 PROPERTY DESCRIPTION — Floor Plans") and DROP the big section-title element on that page.
- **What it does**: reclaims ~25mm of expensive vertical real estate (32pt italic display title) by trading it for cheap eyebrow real estate (12pt all-caps). Reader still knows the section context.
- **Analogy used**: "like chapter headers in a book — first page of Chapter 7 has the big CHAPTER SEVEN banner; pages 2/3/4 just have a small running header 'Chapter 7 · Title' at the top."
- **Generalizes to**: any multi-page section (long appendices, dense data, multi-page TOCs).

## What Zee likely wants to dig into next

In order of likelihood:

1. **Deeper dive into category 5 (page architecture conventions)** — he said both 5 AND 6 were intriguing but only got the 6 walkthrough. Category 5 covers: page chrome triad (eyebrow + title + body), coral accent rule between body and chrome, sage chrome footer band, `.narrative` 2-col body via CSS `column-count`, italic gray captions at 7pt.

2. **Whether these patterns deserve a dedicated skill** — could be `acos-editorial-variant-system` (covering variant architecture + compositional layouts + page conventions) or `acos-deck-refactor` (multi-page sections, reorder/merge primitives, photo-budget discipline).

3. **Other categories he hasn't gotten a deep-dive on yet** — variant architecture (token-set inheritance, italic-override CSS, V1 minimal-weights), compositional layout system (per-page layout flags, raw_html escape hatch, named layouts), multi-page section primitives.

4. **Codifying patterns into something he can apply outside the Ascent rebuild** — practical templates, a starter renderer, or a personal pattern library.

## How to interact with him

- He's a PE associate at Okoa Capital — sharp but appreciates simple language and concrete analogies over jargon.
- He liked the analogies (party coasters, books on a shelf, book chapter headers) — keep using that style when explaining new patterns.
- He's direct: when he doesn't like something, he says so. When he likes something, he says that too.
- Don't re-summarize the full 19-pattern list — he's already seen it twice. Pick up from where the conversation paused, not from the start.
- Don't pitch a skill creation unless he asks.

## What to do FIRST in the new session

1. Read `memory/handoffs/2026-05-26-design-mechanics-discussion.yaml` for the full discussion arc.
2. Briefly acknowledge the handoff was received (one sentence — don't re-explain what we already discussed).
3. **Ask him**: which direction does he want to go next? Offer the 4 options above (or his own). Don't assume.

Do NOT regenerate the PDFs, edit the YAMLs, or touch the renderer unless he explicitly asks for a build-side change. The deliverable for this thread is the discussion itself.
