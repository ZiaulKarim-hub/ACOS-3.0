# S36-page-ops-seo-preview-and-health-hud — Page-scoped ops (Branch A+), per-page SEO, preview mode and the Design Health HUD

| Field | Value |
|---|---|
| Epic / Story | E8 / ST-11 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 2 / — |
| Depends on | S31-typed-ops-autosave-history-undo |
| Requirements | FR-091, FR-092, FR-093, FR-094 |
| Acceptance criteria | A37 · §12.17-A97 · SL-S36-1 · SL-S36-2 |
| CQ / evidence | CQ11 |
| Note | **NA-B01** — FR-091 reads as a v1 multi-page manager; **Branch A+ is binding**. Page-scoped ops, `pages[]` and per-page SEO ship now so multi-page is a v2 **feature addition, not a data migration**; the manager UI and global regions are v2 (ADR-07) |

## PM — slice definition

**Objective.** Ship page-scoped operations and per-page metadata now so multi-page is a later feature rather than a later migration, plus one honest health surface.

**In scope.** Every op carrying a page scope and resolving its target through `pages[]`; `site.json.pages` of **length one** carrying `{id, path, title, order, seo}`; the page ops validated against the **write allowlist**, with any derived patch touching `/systemLock` rejected 400; per-page SEO fields — unique title, 50–160-character description, canonical URL, OG and Twitter with image, `<html lang>` from the interview language answer; **preview mode** ("preview as visitor") suppressing every editor affordance in the same shell; the **Design Health pill** — always visible, non-modal, bottom-corner, three dots (A11y / Perf / SEO), a page-weight bar and a projected LCP read from the live `PerformanceObserver` LCP-candidate entry, expanding on click to a grouped issue list; **Tier-2 findings surface only here — never as a toast stream** (A37).

**Out of scope.** The multi-page manager UI and site-wide global regions — v2 by NA-B01. `gates.ts` and the Tier 0/1/2/3 engine (S63) — this slice is the surface, not the producer. `robots.txt`, `sitemap.xml` and JSON-LD emission and gating (S68), which read the fields shipped here.

**Assumption.** The amber/red thresholds for the page-weight bar and the projected LCP are not published; they ship as configured starting numbers beside `site.json.doctorThresholds`, tagged `[I]`, low confidence, tunable without a code change.

**Allowed files / contexts.**
- `scripts/lib/ops/page-ops.ts`, `scripts/lib/seo-fields.ts`, `app/editor/preview-mode.ts`, `app/editor/health-pill.ts`, `04-site/site.json` (through the op path only).

**Steps.**
1. Add the page scope to the op envelope and resolve targets through `pages[]`; a page-less op is rejected, not defaulted.
2. Implement the page ops against the allowlist; assert the `/systemLock` pointer rejection with its own test.
3. Implement the SEO fields with their validation — title uniqueness, description length band, canonical URL shape, `lang` sourced from the interview answer.
4. Implement preview mode by suppressing the overlay and the panes in one place — same renderer, no second output path.
5. Build the pill and route every Tier-2 finding to it and **nowhere else**.
6. Prove the asset manager, page manager, SEO fields and inline text editing each complete with **no path outside the allowlist written**.

**Definition of Done.**
- Artifacts: the page-scoped op envelope, the page ops, the SEO field set, preview mode, the health pill.
- Validation: `pages[]` has length one and every op is page-scoped; a `/systemLock` patch is rejected 400; the four write paths complete inside the allowlist; the pill shows a real observer-derived LCP, not a computed guess; a grep finds zero toast calls on the Tier-2 path.
- `slice.yaml` mapping — `acceptance_criteria: [A37, "§12.17-A97", SL-S36-1, SL-S36-2]`, `verification_method: exit-code` (A37: `grep-assert`; SL-S36-2: `manual-observation`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-091…FR-094 → file:line, **including an explicit line naming which parts of FR-091 are deferred to v2 under Branch A+**; (3) structural quality — one page-resolution path; (4) functional testing — the allowlist run for all four write paths, the SEO validation matrix, and the pill screenshot with the observed LCP beside a manual measurement; (5) security/compliance — the `/systemLock` rejection and the post-resolution path re-check; (6) operational — what the pill shows when a gate is inconclusive rather than failing; (7) self-assessment.

## QA — zero-trust verification

- **Post an op with no page scope** and require rejection; a silent default to page zero is the migration debt this slice exists to prevent.
- **Post a patch touching `/systemLock`** yourself and require 400.
- **Re-run all four write paths** with a filesystem watch and confirm no path outside the allowlist table was written — watch it, do not read the log.
- **Read the LCP value from the observer yourself** and compare it to what the pill displays; a computed or estimated number is a rejection.
- **Grep for toast and snackbar calls** on the Tier-2 path and require zero.
- **Check the SEO validation band yourself**; a 200-character description that saved is a rejection.
- **Enter preview mode and capture it** — any editor affordance visible is a rejection.

## Dev Learnings

_Not Done until filled. Required: what page-scoping cost while there is only one page, and whether the observer LCP-candidate entry was stable enough to display._

## QA Learnings

_Not Done until filled. Required: which Tier-2 finding tried to reach the user outside the pill, and whether the health dots were honest at a glance._
