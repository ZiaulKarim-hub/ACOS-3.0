# Recency-Aware Evidence Policy — Design Proposal (2026-07-26)

**Status: PROPOSAL ONLY — nothing here is implemented.**

## The problem

The skill's trust machinery systematically punishes new information:

1. The `verified` label requires 2+ independent sources. A model released last week
   structurally cannot have them. It is capped to `provisional`, and the register
   treats `provisional` as "hedge hard or abstain."
2. Retrieval and the moderator can prefer an older, corroborated claim over a newer,
   single-source one — even when the newer one is the vendor's own release note.
3. Nothing forces researchers to LOOK for the newest releases. A dimension can
   saturate on established literature while a 3-week-old alternative goes unfound.
   This is the bigger risk: recall, not grading.
4. Claims carry no dates the router can reason with. "Single-sourced because it is
   9 days old" and "single-sourced because nobody could corroborate it in 3 years"
   are indistinguishable states today.

The epistemic error being encoded: **treating corroboration count as a proxy for
truth.** Low corroboration on a young claim is an expected property of youth, not
evidence of falsity. Absence of literature is information about *time*, not about
*truth*. (The converse also holds: freshness is not evidence of truth — the fix is
honest labeling, never a lower bar.)

## Proposed design (7 parts)

### 1. Two-axis confidence instead of a single ladder

Replace `verified > corroborated > provisional` (one axis) with two orthogonal
fields, from which a delivery label is *computed*:

- `source_quality`: primary | secondary | tertiary — who is speaking
  (vendor release notes / model card / repo = primary; reporting = secondary;
  aggregators = tertiary). The tier system already approximates this.
- `corroboration`: count of independent sources **for the answering claim**
  (per review fix M5 — never pooled across the hit set).

| | primary | secondary only |
|---|---|---|
| **2+ independent** | verified | corroborated |
| **1 source, young** | **primary-new (deliverable, dated)** | provisional |
| **1 source, aged** | primary-unconfirmed (flag for re-probe) | provisional |

The critical new cell: `primary-new`. A week-old vendor model card is not the same
epistemic state as a lone 2-year-old blog post, and it stops being labeled the same.

### 2. Claim dating as first-class metadata

Every claim gains optional `as_of` (date of the information) and `published`
(source publication date), captured at ingest by the researcher charter. Uses:

- The router prefers newer primary claims on version-sensitive facts.
- Age drives the label decay in (4) mechanically.
- The Phase-4 "latest-version check" becomes computable instead of habit.

### 3. A recency floor in coverage (the recall fix)

Per-dimension flag `fast_moving: true` (set at scope time; default true for any
technology/product dimension). A fast-moving dimension **cannot saturate** until a
`recency probe` has run: a search restricted to a recent window (default 90 days,
configurable). "Nothing new found in the window" is itself a dated claim and
counts as the probe's result. This forces the newest releases to be *looked for*,
which no grading rule can substitute for.

### 4. Corroboration expectations that age with the claim

For a claim younger than a window (default 60 days):

- `primary-new` is fully deliverable with the dated framing in (5).
- When the claim ages past the window and corroboration never arrived, the label
  decays to `primary-unconfirmed` and the auditor queues a re-probe. This encodes:
  *new-and-single-sourced is normal now; still-single-sourced forever is a signal.*

### 5. Register wording: label, never suppress

Phase-4 delivery of a `primary-new` claim:

> "Per Liquid AI's release notes of 2026-07-14 — too new for independent
> corroboration yet."

And the symmetric guard for stale corroborated claims on fast-moving facts:

> "As of 2025-11 (3 sources); a newer release may have changed this — recency
> probe queued."

Honest dating replaces both suppression of the new and false confidence in the old.

### 6. Contradiction handling: dated primary beats source-count

When a newer primary claim contradicts an older corroborated one on a
version-sensitive fact, the router prefers the newer primary and files a conflict
ledger entry — corroboration count never outvotes a newer primary source. (The
live Liquid-AI cloning case already demonstrated this shape: four primary sources
correctly overrode a secondary summary; this rule generalizes it to n=1 primary
when the fact is versioned.)

### 7. The unchanged floor

- Figures still require a primary source (I9). Freshness never waives it.
- A rumor/leak with no primary stays `provisional` no matter how fresh.
- Labels never claim more certainty than exists — this proposal adds honesty
  states; it does not lower any bar. The fidelity moves into the label.

## Where it lands in code (sketch)

| Piece | File | Change |
|---|---|---|
| Two-axis label + age rule | `scripts/lib/claims.ts` (`assess`) | compute label from (source_quality, per-claim corroboration, age) |
| `as_of`/`published` fields | `scripts/lib/claims.ts` ingest + researcher charter | optional, additive |
| Recency probe requirement | `scripts/lib/coverage.ts` | `fast_moving` flag; saturation blocked until dated recency probe |
| Date-aware conflict pref | `scripts/lib/claims.ts` moderator/router | newer-primary-wins on versioned facts + conflict ledger entry |
| Eval check `recency-swept` | `scripts/lib/report.ts` | fail if a fast-moving dimension has no dated recency probe |
| Invariant I11 | `SKILL.md` | "A claim is never downgraded for being new; it is labeled. Youth explains low corroboration; it does not disqualify. Labels decay if corroboration never arrives." |
| Dated delivery framing | Phase-4 register + `riff-live.ts` seat prompt | deliver `primary-new` with source+date, never abstain on youth alone |

## Cost estimate

Additive fields and one new probe type; no schema breaks (all optional fields).
Est. ~200-350 lines across 5 files + charter/SKILL.md text + ~10 regression tests.
