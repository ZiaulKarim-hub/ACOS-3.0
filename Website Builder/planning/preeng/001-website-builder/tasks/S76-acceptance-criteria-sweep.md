# S76-acceptance-criteria-sweep — Acceptance-criteria sweep with the collision handled

| Field | Value |
|---|---|
| Epic / Story | E19 / ST-26 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 6 / — |
| Depends on | S68-lock-time-checklist-32-checks, S72-demo-4-locked-published-evidence |
| Requirements | FR-250 |
| Acceptance criteria | SL-S76-1 · SL-S76-2 · SL-S76-3 |
| CQ / evidence | CQ1 · EL-069 · EL-070 |
| Note | **NA-20 / NA-B05.** §19 as written contains **A1–A90** `[V — read in full]`; the "96 criteria" figure carried into the normalized inputs is **not supported by the section text**. Above A90 the ids **collide**: §12.17 appends A91–A101 and §18 appends a **disjoint** A91–A101 |

## PM — slice definition

**Objective.** Map **all 90** criteria to a gate, a script or an observable behaviour, and cite the unstable ones **section-qualified**.

**In scope.** A machine-checkable sweep table — one row per criterion A1…A90 with `{id, statement source, owning slice, gate or script, verification_method, status}`; a mechanical cross-check of that table **against `stories.json`** so every criterion is claimed by at least one slice and every slice's claimed criteria exist; section-qualified citation for every id above A90 (`§12.17-A91`…`§12.17-A101` and `§18-A91`…`§18-A101`, **never bare**) plus the recorded recommendation to renumber §18's set to **A102–A112**, with A91+ treated as **unstable until that lands**; and an explicit **amendments-owed** list for the three criteria recorded as inconsistent with their own canonical statements — the answered-question cap (A3, unachievable as written against a 90-question bank with ~45–55 asked in fast mode `[I]`) and the two performance rows (A66 omitting the interaction metric, A67 stating a flat pre-load cap; NA-16).

**Out of scope.** Amending the source's criteria — this slice **reports** the amendments owed; only the human amends. Silently picking one side of the A91+ collision. Marking a criterion satisfied on the strength of a slice's own claim rather than a run.

**Allowed files / contexts.**
- `acceptance-sweep.json` (new, at the feature root), `scripts/acceptance-sweep.ts` (the checker), `acceptance-sweep.md` (the human-readable render).
- **Read-only against `stories.json`** — this slice checks it and never edits it.

**Steps.**
1. Enumerate A1…A90 into the sweep table; **90 is the figure of record**, and the sweep states plainly that the 96 figure is unsupported (EL-070).
2. For each row, record the owning slice, the gate or script that demonstrates it, and one **named** verification method from the set `grep-assert · exit-code · hash-compare · recompute · screenshot-diff · structured-gate-verdict · manual-observation · probe`.
3. Write `acceptance-sweep.ts` to cross-check the table against `stories.json` mechanically: unclaimed criteria, criteria claimed by no gate, and criteria cited by a slice but absent from the table are three separate error classes.
4. Record every id above A90 twice — once as `§12.17-A<n>` and once as `§18-A<n>` — and mark the id space **unstable**. Bare `A91`+ anywhere in any artifact is an error the checker reports.
5. Record the renumbering recommendation (§18's set → A102–A112) as the fix that makes the id space trustworthy, and note it is a prerequisite for traceability, not a cosmetic tidy.
6. Record the three amendments owed (A3, A66, A67) as **owed**, naming what the gate actually implements versus what the criterion text says (S68 implements the canonical performance statement; S13 records the measured fast-mode count against A3).
7. Render the human-readable sweep with the same data — one source, two outputs.

**Definition of Done.**
- Artifacts: `acceptance-sweep.json`, `acceptance-sweep.ts`, `acceptance-sweep.md`.
- Validation: the table has exactly 90 rows; the checker exits non-zero on a seeded unclaimed criterion; a seeded bare `A93` in an artifact is reported; the amendments-owed list has three entries.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S76-1, SL-S76-2, SL-S76-3]`, `verification_method: exit-code` (SL-S76-2: `grep-assert`; SL-S76-3: `manual-observation`).

**Assumption.** `[I]` Full criterion **statement text** for A1–A90 is not reproduced inside this feature directory; the sweep table carries each id, its owning slice and its verification method, and cites §19 as the statement source rather than restating it. If a criterion's text is needed to settle a dispute, it is read from §19 at that moment — the sweep never paraphrases a criterion into the table.

## Dev — execution contract

Every id above A90 is ambiguous **two ways** and every bare `O31`/`O32`/`O33`/`O34` is ambiguous **four ways** (NA-08, EL-069) — cite both families section-qualified everywhere, including in comments. Evidence bundle: (1) summary — 90 rows, N mapped to gates, N to scripts, N to observable behaviour; (2) traceability FR-250 → the table; (3) structural quality — one data file, one checker, one renderer; (4) functional testing — the checker's output on the real table plus three seeded error classes; (5) security/compliance — n/a, note it; (6) operational — how to re-run the sweep after a slice lands; (7) self-assessment, stating explicitly that the sweep records status from **runs**, not from slice claims.

## QA — zero-trust verification

- **Count the rows yourself.** 96 rows is a rejection; 90 rows where several are placeholders is also a rejection.
- **Run the checker yourself** against `stories.json` and confirm its error classes fire — seed an unclaimed criterion of your own.
- **Grep every artifact in the feature directory** for a bare `A9[1-9]` or `A10[0-9]` and require zero unqualified hits.
- **Confirm the collision is recorded, not resolved** — a sweep that quietly adopted §12.17's numbering and dropped §18's is a rejection, because it hides an unstable id space behind a tidy table.
- **Confirm the three amendments-owed entries** exist and say what the gate implements versus what the text says.
- **Reject** any row marked satisfied on a slice's claim rather than a recorded run.
- **Reject** if `stories.json` was modified by this slice.

## Dev Learnings

_Not Done until filled. Required: how many criteria had no owning gate on first pass, and which were satisfiable only by manual observation._

## QA Learnings

_Not Done until filled. Required: whether the id collision was tempting to resolve unilaterally, and which criterion text most needed amendment before it could be tested at all._
