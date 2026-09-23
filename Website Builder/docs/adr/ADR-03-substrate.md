# ADR-03 — Build substrate: framework versus plain generated HTML

**Status: STILL OPEN. Invariant I6 REMAINS IN FORCE — no code may hard-depend on any framework.**

**Date:** 2026-09-22 · **Slice:** `S03-o8-substrate-spike` · **Requirement:** FR-005 ·
**CQ9 · EL-085** · Acceptance: SL-S03-1, SL-S03-2

This ADR records a **non-decision**, which `S03` explicitly permits: *"Write ADR-03 with the
decision **or** an explicit 'still open, I6 remains in force'."* The measurements below are
real and one-sided. The reason they do not settle the question is stated in full, because a
decision made on this evidence would be a decision made on the wrong test.

## Context

Two candidates render the same one page from the same `tokens.json` and the same
`content.json`:

- **A — framework:** Astro `5.14.1`, `npm install`, `npx astro build`.
- **B — plain:** a 120-line TypeScript renderer run by `bun`, no package manifest at all.

## The measurements

**Equality first, because an unequal comparison is not a comparison.** After normalising
whitespace and removing one leaked attribute, the two built files are **byte-identical**.
Rendered at 1280×900 in headless Chrome, the two screenshots share the sha256
`2a97119777d5bdbb79783c061132bffa1649127ee942d54fb87db42f9aeaa5b5` — **pixel-identical, 61715
bytes each.** The comparison is fair.

| Measure | A — framework | B — plain | Method |
|---|---|---|---|
| Built files | 1 | 1 | `find dist -type f` |
| JavaScript bundles in output | **0** | **0** | `find dist -name '*.js'` |
| Distinct framework strings surviving into `dist/` | **1** — `is:global` | **0** | `grep -oiE '(is:[a-z]+\|set:[a-z]+\|client:[a-z]+\|data-astro[a-z-]*\|astro-[a-z0-9]+\|__vite[a-z_]*\|data-v-[a-z0-9]+)'`, sorted unique |
| Dependency surface | **251 top-level packages, 144M** | **0 packages, 0 bytes** | `ls node_modules \| wc -l`, `du -sh node_modules` |
| Full rebuild, 3 runs | **1008 / 835 / 796 ms** | **38 / 32 / 33 ms** | wall clock around the build command |
| Two builds, same install, byte-identical? | **yes** | **yes** | `sha256` over a sorted `sha256` of every file in `dist/`, twice, from clean |
| Package manifest implied | `package.json` + `package-lock.json`; `npm install` then `npx astro build` | **none** | — |

**The `is:global` leak is a real finding and it was nearly missed.** A first pass grepping for
`astro|vite|hmr` returned **0** for both candidates and looked like a clean tie. The attribute
that actually survives is `is:global` — a framework directive that should have been consumed at
build time, appearing in shipped markup as `<style is:global>`. It is also not valid HTML: a
colon in an attribute name is not standard. **A scrub list written from the obvious search terms
would have shipped it.** That generalises past this ADR: a LOCK scrub must be built from what is
actually in the output, never from a list of names someone expected to find.

## Why this does NOT decide the substrate

**Every measured axis favours B, and the measurement is the wrong shape to conclude from.**

1. **It is one static page.** It exercises nothing a framework exists to provide: routing,
   multi-page output, partial hydration, image handling, content collections, or a live-edit
   preview. B "wins" a race B was built for.
2. **It does not measure the live-editability score the slice asks for.** `S03` names
   live-editability as a scoring axis. Only the full-rebuild time was measured
   (**32–38 ms** for B; **796–1008 ms** for A). A framework's dev server updates a running page
   without a full rebuild, and that path was not measured here. **This is the weakest number in
   the table, and it is weak in A's favour.**
3. **The multi-page question is unsettled.** `DECISIONS.md` item 4 — multi-page in v1, or a
   single page — is **open**. A substrate chosen for a single page and then asked to serve a
   multi-page site with global regions is a choice made against the wrong requirement.
   **This slice may not decide item 4 and does not.**

## On byte-reproducibility — read this precisely

Both candidates produced **byte-identical output across two builds**. That is a real result and
it is **not** an answer to the question §12-O33 asks.

O33 asks whether a build is byte-reproducible **across two installs of the same lockfile**. What
was measured here is two builds on **one** install, on one machine, minutes apart. The harder
question — a second `npm install` resolving to a different dependency tree — is untouched.

**`S05` owns that spike, and `DECISIONS.md` item 5 owns what to do if it fails.** Neither is
decided here. §12-O33's own words stand unchanged: *"no source consulted for this PRD establishes
bundler-level byte reproducibility."*

## Decision

**None. The choice stays open and I6 remains in force: no code may hard-depend on any framework.**

Practically, that means the renderer contract (`S25`) is written so that the substrate sits
behind it, and the product tree adopts neither candidate yet.

## What would settle it

1. **`S05`** — the two-build byte-equality spike across two installs.
2. **A live-edit measurement**, not a rebuild measurement: change one token, measure time to the
   updated pixel in a running page, on both candidates.
3. **`DECISIONS.md` item 4** — multi-page in v1, or single page. **Zee's call, not this slice's.**
4. **The same comparison at multi-page scale**, once item 4 is settled.

## Note for the two-build gate procedure (NA-11 / EL-085)

The candidates imply different installer invocations, and that is the recorded toolchain
conflict. A carries `package.json` + `package-lock.json` and needs `npm install`; B carries no
manifest and is run by `bun`. **The carried two-build comparison procedure is written against a
different package manager than the skill's own runtime.** Whoever writes that gate must state
which manager the reproducibility claim is about, because "the same lockfile" means nothing until
that is named.
