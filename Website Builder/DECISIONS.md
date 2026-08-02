# Open decisions — Website Builder

16 decisions the PRD deliberately did **not** make, because making them would have meant
fabricating an answer. Each has my recommendation. A recommendation is an opinion, not a
finding — the PRD's own evidence is cited where it exists.

Ordered by how much downstream work each one blocks. **D1–D4 are settled and not listed here**
(see `memory/decisions/`).

Status legend: ☐ open · ☑ decided (record the answer and the date inline)

---

## 1. ☑ v1 scope sign-off — gridlines and dragging  ⚠ BLOCKS EVERYTHING

**Where:** §18 "Vision deviations requiring sign-off" (first table in the section).

**The situation.** v1 as drafted delivers **no gridlines** (Step 4a) and dragging only as
*section reorder* (Step 4b) — no pointer-drag placement, no snapping, no free-position, no
zoom/pan. Both are named features in the brief. The direct consequence: **D2 (constraint
dragging) is inert in v1**, the only version that ships first. §18 also notes that LOCK's
"gridlines disappear" moment is vacuous in v1, since there are no gridlines to remove.

**Options.**
- **A — Accept.** v1 is "editor-lite"; the canvas arrives in v2. Fastest to something real.
- **B — Pull the canvas into v1.** Honours the brief, but §18 estimates this roughly doubles
  editor scope (~16–24 days, ~25–35 days against the revised baseline — figures tagged as
  inference, not measured).
- **C — Split v1a / v1b.** v1a editor-lite ships and proves the pipeline; v1b adds the canvas
  before anything is called done.

**My recommendation: C.** A risks you never seeing the thing you actually asked for, because
"v2" is where features go to wait. B front-loads the highest-risk unproven mechanic before the
pipeline around it works. C keeps the honest sequencing of A while making the canvas a
committed deliverable rather than a deferral.

**☑ Decided 2026-07-26: B — pull the canvas into v1.** Zee rejected the editor-lite scope
(against the recommendation above): v1 must ship gridlines (step 4a) and full constraint
dragging (step 4b), making D2 active in the first shipping version and giving LOCK's
"gridlines disappear" moment real content. Accepted consequence: editor scope roughly
doubles — §18's estimate of ~16–24 days (~25–35 days against the revised baseline), tagged
as inference, not measured. Follow-on: §18's timeline, its v1 scope-in list, and the §13
gate budgets need re-baselining against this choice; decision 2's "pairs with option C"
note is now moot.

---

## 2. ☐ v1 component set — 87 items / 674 variants, or cut back?

**Where:** §8.8-X3, marked "⚠ REQUIRES USER SIGN-OFF".

The corrected v1 component set is **87 items / 674 variants**. §18's timeline and §13's gate
budgets were both sized against **~50 items / ~430 variants**. The PRD refuses to pick between:
accept and re-baseline the schedule; demote specific rows to v2; or split v1a/v1b. Radio group
and Toggle switch are named as **non-demotable**.

**My recommendation: re-baseline, then demote only what the interview says this project does
not need.** A fixed 87 for every site is the wrong shape — per-project demotion is cheaper than
arguing about the global list. Pairs naturally with decision 1's option C.

---

## 3. ☐ "20 artworks" — 20 pieces total, or 20 per style family?

**Where:** §7-O31 and §17-O15. §7 currently adopts the **20-total** reading as the v1
hand-carry quota, and flags it against the FruitSync exemplar (**231 sprites**) as a
"requires user sign-off" deviation.

**My recommendation: 20 total for v1, per direction.** 231 is not reachable through a manual
paste boundary. But say plainly that a game-style site needs a different artwork path, which is
what decision 13 is about.

---

## 4. ☐ Multi-page in v1, or a single page?

**Where:** §17.4-O10 vs §18's v1 scope-in list, which already promises "multi-page manager,
global regions, per-page SEO fields". The two contradict each other. §18's patcher costed three
branches and recommended **Branch A+** as inference; it declined to choose.

**My recommendation: Branch A+ (multi-page in v1).** Global regions — edit the navigation once,
everywhere follows — is what makes a multi-page site maintainable. Retrofitting it later is
worse than building it in.

---

## 5. ☐ Build byte-reproducibility — is D3's proof achievable?

**Where:** §12.8, §12-O33. **No source consulted established that Astro/Vite builds are
byte-reproducible across two installs.** §12.8 only constrains *our generator's* determinism.
The PRD requires a Phase-0 spike, states explicit reproducibility preconditions, and documents
a normalised-comparison fallback — flagged as **weakening D3's proof**, hence needing sign-off.

**My recommendation: run the Phase-0 spike before committing to two-build byte-equality.** If
it fails, accept normalised comparison and say so in the PRD rather than claiming a guarantee
the toolchain cannot give. This is the item most likely to quietly become untrue.

---

## 6. ☐ Does sibling-anchored free-positioning ship at all?

**Where:** §11.4 rule 1. The original language allowed anchoring to "parent edge, sibling, or
grid cell". The subgrid-promotion compile strategy behind it is **unprototyped**, with "no known
mitigation beyond the idea stated".

**My recommendation: parent and grid-cell anchoring only in v1; sibling anchoring behind the
prototype.** Sibling anchors are where constraint systems usually break, and this one has never
been built.

---

## 7. ☐ Step 5 regeneration — silent apply, or reviewed?

**Where:** §12.16. v1 makes applying a brand-new direction a **reviewed** operation: per-node
flag, LOCK blocked until acknowledged, bulk-acknowledge available. The PRD flags that your
vision step 5 may have assumed a new direction simply *applies*.

**My recommendation: keep the review, keep bulk-acknowledge.** Silently restyling every node
after hours of manual placement is the kind of surprise that makes people stop trusting a tool.

---

## 8. ☐ Is there a wide/xl breakpoint override tier in v1?

**Where:** §12-O32. Currently **no** — §10.1's "full" preview shows base rules and carries no
overrides. Adding one would introduce the **only upward override** in an otherwise
desktop-down cascade.

**My recommendation: no xl tier in v1.** One exception to a cascade direction costs more in
confusion than it buys in layout control.

---

## 9. ☐ Should 1440 be a fifth live-switcher option?

**Where:** §10.1. Related to decision 8 but separate: this is about *previewing*, not
overriding.

**My recommendation: yes, as preview-only.** 1440 is the reference desktop width the capture
profile already uses. Previewing it without allowing overrides is cheap and keeps decision 8
intact.

---

## 10. ☐ How many typefaces seed `font-catalog.json`?

**Where:** §6. An OFL-licensed shortlist (OFL = SIL Open Font License, a licence that permits
embedding and redistribution). The PRD would not invent a count.

**My recommendation: 24–32 families, curated by role.** Enough for ~10 directions to differ
genuinely; small enough to audit every licence by hand once. Treat as a starting number to
revise after the first real run.

---

## 11. ☐ Motion-concurrency caps — carry over, or benchmark?

**Where:** §13.4 gate 4a, §13.11. The cap numbers come from prior research, **not benchmarked
against this product's own render stack**.

**My recommendation: ship the carried-over caps as provisional, benchmark during v1.** They are
labelled provisional in two places already; the honest fix is measurement, not a new guess.

---

## 12. ☐ Who authors the variant axis schema?

**Where:** §8.6, new O33 / risk R46. Three candidates were costed. The PRD's inference is
**hand-authored in the skill**, for determinism — but that is an **unbudgeted effort line**
that §18's timeline does not carry.

**My recommendation: hand-authored, and add the effort line to §18.** Determinism matters more
here than authoring convenience, but the schedule must admit the cost.

---

## 13. ☐ Raster artwork when the project has no asset library

**Where:** §18-O32 (narrowed from O7). Lane A (code-drawn, token-referencing) and Lane B
(asset-library ingestion) are in for v1. Lane C (external raster) is **out**, with a runbook.
The residual case — a project with no asset library whose direction genuinely needs
photographic or painterly raster — has **no solution that preserves the paste-only path**, and
no known mitigation.

**My recommendation: accept it as a per-project limitation and say so at interview time.** If
the interview reveals a raster-dependent direction, the skill should warn before generating a
design system it cannot fully deliver — better than discovering it at step 4.

---

## 14. ☐ Confirm the reconstruction of §7 categories K and M

**Where:** §7.14 / §7.15, O35. The original contents were **unrecoverable** from the surviving
text after the truncation. These two subsections are labelled **a reconstruction, not a
recovery**, and need your confirmation that they say what you want.

**My recommendation: read those two subsections and confirm or correct.** Everything else in
the PRD is original or audited; these two are the only rebuilt passages.

---

## 15. ☐ How is success criterion S9 measured?

**Where:** §2.3. S9 is a retention proxy — is the tool used more than twice? But **NG3 says the
product has no backend**, and no section specifies any usage tracking. Marked "no known
mitigation".

**My recommendation: measure it from local session files, not telemetry.** Count sessions
recorded against the same ACOS project inside a 90-day window. No backend needed, no data
leaves the machine.

---

## 16. ☐ Should the interview ask about the audience's access needs?

**Where:** §3.2. Whether Step 1 should ask about a project's *tertiary* audience — the people
who will actually visit the site — and whether their known access needs should tighten the §13
gate thresholds for that project. The PRD proposes no mechanism and did not invent one.

**My recommendation: ask the question, but do not let the answer *loosen* any gate.** Learning
that an audience skews older or uses screen readers should be able to raise a threshold, never
lower one. Accessibility floors should not be negotiable per project.

---

## Not listed here

51 further deferred items are recorded in `prd/OPEN-ITEMS.md` section B. Those are unmeasured
numbers, unsourced inferences, and edits that belong to a section other than the one that found
them. They need work, not a decision from you.
