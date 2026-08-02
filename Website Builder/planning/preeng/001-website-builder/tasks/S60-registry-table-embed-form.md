# S60-registry-table-embed-form — Whitelisted registry components: table, embed and form

| Field | Value |
|---|---|
| Epic / Story | E13 / ST-20 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 4 / — |
| Depends on | S51-slot-contracts-and-swap-safety · S23-versioned-coherence-lint-set |
| Requirements | FR-190, FR-191, FR-194 |
| Acceptance criteria | SL-S60-1 · SL-S60-2 · SL-S60-3 |
| CQ / evidence | CQ1 · EL-084 |
| Note | **E13 carries unsigned sign-off rows 5 and 6.** The minimal placement path and the minimal chart-data field are deviations from §18's literal cut and require the user's sign-off |

## PM — slice definition

**Objective.** Ship the narrow custom-component registry against the direction's tokens, with a real placement path.

**In scope.** The whitelisted registry — **table, chart, embed, form** — generated deterministically against the direction's tokens plus dataviz sub-tokens; **anything else refused** with a message naming the v1 scope; a **working insertion path in the editor for each kind**, because shipping a capability with no insertion path silently cuts it; the **minimal chart-data field** (paste a table of numbers bound to the chart node's data prop — no formulas, no multi-sheet, no cell formatting); registration through the `component.custom-slot` contract that enforces token usage; the full **versioned coherence lint set** (S23) run before acceptance on the inline-authored path.

**Out of scope.** Chart rendering itself (S61 — this slice ships the table, embed and form kinds plus the chart node's registration, data field and placement). The opaque custom-code-block container (v2). Any non-whitelisted kind.

**Allowed files / contexts.**
- `scripts/lib/registry/{table,embed,form,index}.ts`, `scripts/lib/custom-slot.ts`, `06-custom/**` (write), the insertion path in the component bar, `04-site/pages/<id>.doc.json` through typed ops only.
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.**

**Steps.**
1. Define the registry as a closed set of four kinds; the insertion API rejects any other kind with a message naming the v1 scope.
2. Generate table, embed and form deterministically from the direction's tokens — every colour, spacing and type value is a token reference.
3. Build the insertion path for all four kinds in the editor; a kind with no way to place it counts as not shipped.
4. Implement the minimal chart-data field with the three explicit exclusions stated in the UI.
5. Route every inline-authored registration through `component.custom-slot`, running the full coherence lint set before acceptance.
6. Carry the sign-off note on the placement-path row and the chart-data-field row; both are recorded as unsigned deviations.

**Definition of Done.**
- Artifacts: the three generated kinds, the chart node registration + data field, the custom-slot contract, the insertion paths, the sign-off note.
- Validation: inserting a fifth kind is refused with the scope message; each of the four kinds is placeable in the editor; an off-token value in an inline-authored component is caught by the lint set before acceptance.
- Demo-able increment: insert a table, an embed and a form onto a page and see them read as part of the direction.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S60-1, SL-S60-2, SL-S60-3]`, `verification_method: exit-code` (SL-S60-2: `manual-observation`).

## Dev — execution contract

Evidence bundle: (1) summary listing each kind with its insertion entry point; (2) traceability FR-190, FR-191, FR-194 → file:line; (3) structural quality — one registry table, no per-kind special cases in the insertion path; (4) functional testing — the refused-kind fixture, one placement per kind, an off-token fixture rejected by the lint set; (5) security/compliance — the embed kind is a deterministic embed used as supplied and never redrawn; (6) operational — how a registry kind is added in v2 without reopening the whitelist mechanism; (7) self-assessment naming the two unsigned sign-off rows explicitly.

## QA — zero-trust verification

- **Attempt to insert a non-whitelisted kind yourself** and require refusal with the scope-naming message.
- **Place each of the four kinds through the editor** — a kind you cannot place is a rejection regardless of code coverage.
- **Grep the generated output** for a raw colour or spacing literal where a token exists; one hit is a rejection.
- **Author an off-system inline component** and confirm the lint set blocks acceptance **before** registration, not after.
- **Reject** if the sign-off rows are presented as signed, or omitted from the evidence bundle.

## Dev Learnings

_Not Done until filled. Required: which of the three kinds fought hardest against token-only styling, and what the chart-data field's exclusions cost in practice._

## QA Learnings

_Not Done until filled. Required: whether an insertion path existed for every kind or only for the ones with tests._
