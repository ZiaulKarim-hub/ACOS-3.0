# S62-inline-authored-path-and-coherence-debt — Inline-authored components, coherence debt, the signature-moment rule and third-party marks

| Field | Value |
|---|---|
| Epic / Story | E13 / ST-20 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 4 / — |
| Depends on | S23-versioned-coherence-lint-set · S60-registry-table-embed-form |
| Requirements | FR-195, FR-196, FR-197 |
| Acceptance criteria | A75 · SL-S62-1 · SL-S62-2 · SL-S62-3 |
| CQ / evidence | CQ1 · EL-084 |
| Note | **NA-10 / EL-084** — §14.5's agent-authored path names `Task(general-purpose)`, which conflicts with the no-unverified-subagent rule. **Inline main-session execution of the role prompt is adopted instead**; subagent forking is a later context-economy optimisation only |

## PM — slice definition

**Objective.** Allow bespoke work through one audited door, record what it costs in coherence, and never redraw a third-party mark.

**In scope.** The inline-authored component path executed **inline in the main session** with already-declared tools — no `Task(general-purpose)` spawn on this path; the **versioned coherence lint set** (S23, named members, not a bare count) run in full before acceptance; the `CoherenceLedger` `{entries: [{at, nodeId?, tokenPath?, acceptedValue, systemValue, reason, kind, debtScore}]}` receiving every accepted off-system value with a reason; the **signature-moment rule** — 2–3 bespoke concept candidates per direction, generated at Step 2 and chosen/refined at Step 4, with a lint flagging a **second** signature moment; the `[3P]` rule — no third-party mark (platform badge, social icon, trust badge, map tile) may be redrawn; `[3P]` items are deterministic embeds used **as supplied** (A75, R23 — trademark exposure is legal, not aesthetic).

**Out of scope.** The **opaque custom-code-block container** — v2, and explicitly where the quality ceiling actually lives (FR-195). Cross-direction transplant debt — a v2 consumer of the same ledger. Registry generation (S60).

**Allowed files / contexts.**
- `scripts/lib/inline-authored.ts`, `scripts/lib/coherence-ledger.ts`, `scripts/lib/lints/signature-moment.ts`, `scripts/lib/third-party-marks.ts`, `04-site/coherence-ledger.json` (write), `06-custom/**`.
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.**

**Steps.**
1. Execute the role prompt inline in the main session; assert by grep that no `Task(` spawn exists on this path, and record NA-10 as the reason.
2. Run the full versioned lint set before acceptance, citing `lintSetVersion` and each member id — never a lint count.
3. On an accepted off-system value, write a ledger entry with the accepted value, the system value it departed from, the reason and a debt score; acceptance without an entry is impossible by construction.
4. Implement the signature-moment lint: 2–3 candidates per direction is the rule, and a second signature moment is flagged.
5. Implement the `[3P]` rule: a mark is embedded as supplied; any attempt to generate or redraw one is refused with the trademark reason stated.
6. Assert by grep that no opaque custom-code-block container exists in v1, and record it as the v2 home of the quality ceiling.

**Definition of Done.**
- Artifacts: the inline path, the ledger and its writer, the signature-moment lint, the `[3P]` refusal, the two grep assertions.
- Validation: an accepted off-system value appears in the ledger with a reason; a second signature moment is flagged; a redraw attempt on a `[3P]` mark is refused; no `Task(` spawn and no custom-code-block container exist.
- Demo-able increment: author one bespoke component inline, accept one off-system value, and read the resulting debt entry in the editor.
- `slice.yaml` mapping — `acceptance_criteria: [A75, SL-S62-1, SL-S62-2, SL-S62-3]`, `verification_method: exit-code` (A75: `manual-observation`, SL-S62-1: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-195, FR-196, FR-197 → file:line; (3) structural quality — one acceptance gate, one ledger writer; (4) functional testing — an off-system acceptance, a second-signature-moment fixture, a `[3P]` redraw attempt, the two greps; (5) security/compliance — state the trademark exposure plainly and confirm marks are used as supplied; (6) operational — how debt is reviewed and whether an entry can be retired; (7) self-assessment stating the v1 quality ceiling honestly.

## QA — zero-trust verification

- **Grep the whole path yourself** for `Task(`; one hit is a rejection under NA-10.
- **Accept an off-system value** and require a ledger entry with a reason — an entry with an empty reason is a rejection.
- **Author a second signature moment** and require the flag.
- **Attempt to have a platform badge generated** and require refusal; a redrawn mark is an immediate rejection.
- **Reject** any artifact that cites the coherence lint set by a bare count instead of the set version and named members.
- **Grep for an opaque custom-code-block container**; its presence in v1 is a rejection.

## Dev Learnings

_Not Done until filled. Required: what inline execution cost in context versus the rejected subagent path, and the first real coherence-debt entry recorded._

## QA Learnings

_Not Done until filled. Required: whether the lint set genuinely ran in full before acceptance, or a subset ran and the rest ran after._
