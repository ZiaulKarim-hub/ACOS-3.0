# ADR-02 — Font policy on the generation surface

**Status: PARTIAL. The local control is settled. The generation-surface observation is
OUTSTANDING, and it is the question this slice exists to answer.**

**Observed:** 2026-09-23 (UTC) · **Slice:** `S02-o1-font-policy-probe` · **Requirement:** FR-004
· **CQ5 · EL-067** · Acceptance: SL-S02-1, SL-S02-2

**This fact decays.** It is a point-in-time observation of a third-party surface, and the date
above is part of the finding, not decoration.

## Why the question matters

If the surface silently falls back to a system face, **the human picks a look they have never
seen** (R2, critical). The whole of Step 2 rests on the person judging a real specimen.

## The finding that changes how this is tested — `document.fonts.check` LIES

`document.fonts.check('96px "Playfair Display"')` returned **`true` in all three fixtures**,
including the **control**, which declares no font at all and demonstrably fell back.

**So the obvious API for this question is a false-positive oracle, and any probe built on it
would have reported success everywhere.** The `@font-face` registry is no better on its own:
fixture A listed four entries, three `unloaded` and one `loaded`, which needs interpretation
before it means anything.

**What does work is a width measurement.** Render one probe string at 96px in the target family
and in a family that cannot exist. Equal widths mean fallback. That is a number, and it needs no
devtools — which matters, because devtools are unreachable on most surfaces worth testing.

## Measurements

Probe string `Handgloves WMwmil 0123` at 96px. Target `Playfair Display` 700, chosen because its
metrics are far from any system serif.

| Fixture | width(target) | width(missing family) | delta | `fonts.check` | Verdict |
|---|---|---|---|---|---|
| **C — control**, no font declared | 1071.89 | 1071.89 | **0.00** | `true` | **FELL BACK** |
| **A — linked stylesheet** | 1160.83 | 1071.89 | **88.94** | `true` | **RENDERED** |
| **B — base64 `data:font/woff2`** | 1160.83 | 1071.89 | **88.94** | `true` | **RENDERED** |

Reference widths, identical across all three: `serif` **1071.89**, `sans-serif` **1136.44**.

**Two independent signals agree, which the slice requires — one alone is insufficient, because a
fallback can look plausible.**
- **Numeric:** the delta above.
- **Visual:** in the control screenshot the two specimen lines are the same Times-like serif. In
  A and B the top line is visibly Playfair — higher stroke contrast, different letterforms,
  wider — against the grey `serif` line beneath it.

A and B produce the **identical** delta of 88.94px, which is the corroboration that B's embedded
binary is the same face rather than something merely different from the fallback.

## What is NOT established

**This was measured in local headless Chrome, not on the generation surface.** Local Chrome has
no content-security policy restricting font origins; the generation surface may. **The result
above is therefore the CONTROL, not the answer.**

Concretely outstanding, and each takes about a minute:
1. Render fixture A **on the generation surface** and read the VERDICT line.
2. Render fixture B **on the generation surface** and read the VERDICT line.
3. Capture the network entry for the font binary verbatim — succeeded, or blocked, and by what.

**No conclusion may rest on the absence of an error message.** If the surface blocks the font,
fixture A's own report will say `FELL BACK` with a delta of `0.00`, which is a positive
observation rather than a silence.

## Decision

**Deferred.** The choice — link a hosted stylesheet, or embed the binary as base64 — cannot be
made until the surface is observed.

**What the local control already tells us about the two options**, independent of the surface:

| | A — linked stylesheet | B — base64 embedded |
|---|---|---|
| Remote origins in the fixture | **3** (`fonts.googleapis.com`, `fonts.gstatic.com`) | **0** |
| Self-contained | no | **yes** |
| Cost | one stylesheet line | **31088 base64 characters** for one weight of one family, from a 23316-byte `woff2` |
| Fails if the surface blocks remote fonts | **yes** | no |

**B is immune to the failure mode this slice is about, and it costs roughly 31 KB of prompt per
weight per family.** That cost lands directly against the output ceiling that `S06` measures and
`O2` still treats as unverified, so B is not free and the trade cannot be priced here.

## How to re-run this in under a minute

Open `scripts/probes/font-policy/fixture-{a-linked,b-base64,c-control}.html` and **read the
VERDICT line**. The fixtures self-report; nothing has to be inspected by eye and no devtools are
needed. Paste the same file onto the generation surface to test it there.

**Always run the control alongside.** Without it, `RENDERED` is a claim about a number with
nothing to compare it to — and the control is what caught `document.fonts.check` lying.
