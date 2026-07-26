# D3 — LOCK exports clean code; it does not hide a toolbar

**Status:** SETTLED · **Date:** 2026-07-25 · **Decided by:** Zee, in conversation
**Do not reopen.** A later session may implement this; it may not re-litigate it.

## Context

Brief step 7: the user says LOCK, and all design toolbars and gridlines are removed so the site
appears as a visitor would see it — reversibly.

Read naively, "removed" could mean *hidden*. If LOCK only hides the editor, the finished site
still ships the entire editing engine to every visitor. That is slow, and it would fail the
performance gates the project inherits from the prior swarm research.

## Decision

**LOCK EXPORTS.** It produces a clean static site with **no editor runtime shipped to
visitors**, while keeping the editable project beside it so design mode can be re-entered.

## Consequences

- §12 specifies five LOCK purity gates and a **re-render, not copy-strip** approach — the clean
  build is generated afresh rather than produced by deleting things from the editable build.
- Proof of purity was specified as **two-build byte-equality**. ⚠ **No source consulted
  established that Astro/Vite builds are byte-reproducible across two installs.** §12.8 only
  constrains our own generator's determinism. A Phase-0 spike is required, with a documented
  normalised-comparison fallback that explicitly **weakens D3's proof** — see `DECISIONS.md` #5.
- UNLOCK must be lossless, or its losses must be named. §12 covers the return trip.
- v1 note: because v1 currently ships no gridlines, the "gridlines disappear" part of the LOCK
  experience is vacuous until that deviation is resolved (DECISIONS.md #1).

## Rejected alternative

**Hide the editor chrome and serve the same bundle.** Rejected: it ships editing code to
visitors, breaks the performance budget, and makes "the site as a visitor sees it" a lie.
