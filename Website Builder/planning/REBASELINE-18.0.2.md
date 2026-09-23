# §18.0.2 re-baseline — RUN 2026-09-22

**Status: the counts are VERIFIED. The day-figures are re-baselined as a BAND, not a point.
A point estimate is not derivable from anything in the PRD, and §18.0.2 forbids inventing one.**

> §18.0.2: *"The re-baseline is a task, not a paragraph. It belongs to the slice set, and it
> must **read the counts** rather than restate them."* — and, on inventing a figure:
> *"inventing a corrected number would be exactly the fabrication this PRD refuses elsewhere."*

Both instructions are followed below. Every count is parsed out of §8.4's own table and
re-added; no figure is copied from the PRD's prose.

## 1. The counts, read rather than restated

§8.4's table was parsed and every family re-added independently.

| Family | Stated items | Stated variants | Listed entries | Listed variants sum | Match |
|---|---|---|---|---|---|
| Navigation | 6 | 43 | 6 | 43 | ok |
| Hero | 3 | 28 | 3 | 28 | ok |
| Content | 18 | 151 | 18 | 151 | ok |
| Social proof | 3 | 24 | 3 | 24 | ok |
| Commerce | 4 | 31 | 4 | 31 | ok |
| Form | 17 | 122 | 17 | 122 | ok |
| Feedback | 6 | 46 | 6 | 46 | ok |
| Media | 5 | 76 | 5 | 76 | ok |
| Utility | 4 | 14 | 4 | 14 | ok |
| Page templates | 4 | 18 | 4 | 18 | ok |
| §9 motion and art containers | 17 | 121 | 17 | 121 | ok |
| **Re-added total** | **87** | **674** | | | **agrees with §8.4** |

**§8.4's arithmetic is sound.** Every family's listed entries match its stated item count, every
family's listed variants sum to its stated variant total, and the families sum to exactly
87 / 674. Nothing needed correcting.

The two multipliers, computed rather than quoted:

| Quantity | Old baseline | Verified new | Multiplier | Change |
|---|---|---|---|---|
| Pickable items | ~50 | **87** | **1.7400** | **+74%** |
| Generated variants | ~430 | **674** | **1.5674** | **+57%** |

Both reproduce §8.4's stated *"~74% increase in items and ~57% in variants"* exactly.

## 2. The decomposition, validated against the PRD's own total

§18's line table gives the revised per-layer figures. Summing the Branch A+ spine:

| Line | Revised days | Count-sensitive? | Why |
|---|---|---|---|
| L1 interview + prompt generator | 2.25–4.25 | **yes** | the generated prompt must cover every pickable item, so its size tracks the item count |
| L2 ingest/validate/normalise + token compiler + font catalog + variants | 9.5–14.5 | **yes** | this line's own title ends in *"variants"*; it is the line that processes all 674 |
| L3a editor-lite (Branch A/A+, single page) | 12.5–17.5 | **yes** | the component bar presents every item and its variants (D1: 10 variants per component on demand) |
| L4 lock/export/publish/evidence | 3.5–5.5 | **no** | sized by the 32-gate LOCK list, which does not grow with the item catalogue |
| **Spine total** | **27.75–41.75** | | |

**§18 prints "≈ 28–42 days" for exactly this spine.** The decomposition reconstructs it, which
is what licenses using these four lines as the re-baseline's unit of work. Had it not
reconstructed, the line split would have been wrong and nothing below would follow.

## 3. The re-baselined figure — a band, with each model named

No per-item or per-variant day cost is measured anywhere in the PRD. A single corrected number
therefore cannot be derived, only assumed. What can be derived is what the spine becomes under
explicitly-named scaling assumptions:

| Model | Assumption | Branch A+ spine |
|---|---|---|
| **A** | nothing scales — the figure §18 prints today | **27.8–41.8 days** |
| **B** | the three build lines scale linearly with **variants** (×1.5674) | **41.5–62.3 days** |
| **C** | the three build lines scale linearly with **items** (×1.7400) | **45.7–68.6 days** |

**The re-baselined v1 spine lies between 27.8 and 68.6 days.**

- **Model A is a floor that is now known to be wrong**, because the counts genuinely changed —
  §8.4 calls it *"a real scope change, not a re-count of the same thing."*
- **Model C is a ceiling** that assumes zero economy of scale: no shared machinery, every item
  paid for at full price.
- The truth is somewhere between, and **narrowing it needs a measured per-item cost the PRD
  does not contain.** Building L2 for the first twenty items and timing it would produce that
  number; nothing short of building will.

## 4. What this re-baseline deliberately does NOT do

**It does not fold in the stacking additions.** Each carries its own figure that was never
decomposed into the L1–L4 lines, so adding them here would double-count against a spine whose
internals are unknown:

| Addition | Its own figure | Status |
|---|---|---|
| Item 1 option B (canvas into v1) | ~16–24 days, ~25–35 days against the revised baseline | **[I]** inference, accepted 2026-07-26 |
| D5 (layers as a real tier) | 16–24 days, explicitly *"stacks on top of"* item 1 | **[I]** inference, accepted 2026-08-20 |
| C1 inline links | unbudgeted | not measured |
| C2 minimal multi-select | unbudgeted | not measured |
| C3 insertion registry + chart-data field | unbudgeted | not measured |

**It does not re-baseline §13's gate budgets.** §13.1's *"p50 ≤ 90s and p95 ≤ 180s for a
representative 5-page site"* is sized against the **32-gate list**, not against the item
catalogue, and §13.1 already marks it *"an inference, not a measured or sourced figure."*
Gate runtime scales with what a page contains, not with how many items the catalogue offers.
Re-baselining it against 87/674 would be the wrong operation on the wrong variable.

**It does not choose a model.** Picking A, B or C is a scheduling judgement with real
consequences, and the spread is 27.8 to 68.6 days — a factor of about 2.5.

**It does not change any Priority cell.** Per-project demotion is the relief valve item 2 chose,
and Radio group and Toggle switch remain non-demotable in every project.

## 5. Method note

The counts were parsed mechanically from §8.4 rather than read by eye. The first parser run
reported the §9 row as **16 entries / 119 variants** against a stated 17 / 121, which looked
like a PRD defect. It was not. The parser required each entry's number to be followed by a
semicolon or end-of-cell, and the final entry reads *"signature moment 2 (concept candidates,
not a swap catalogue)"* — a parenthetical, so the entry was silently dropped. The parser was
corrected to allow a trailing aside, after which all eleven families match. **The PRD was
right and the tool was wrong**, which is recorded here because the opposite conclusion was one
unreviewed step away.

## 6. What changes in the PRD as a result

§18.0.2 currently says the re-baseline is *"NOT yet done"* and instructs the reader to
*"treat every §18 day-figure as a floor and not an estimate."* That instruction is now
**confirmed correct and quantified**: the floor is 27.8–41.8 days, and the same spine reaches
45.7–68.6 days under a linear-in-items reading.

The figures in §18's line table are left untouched. Replacing them would require choosing a
model, and that choice is not this task's to make.
