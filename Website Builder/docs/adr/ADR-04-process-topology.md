# ADR-04 — Process topology: single origin versus two origins

**Status: NON-DECISION. §17-O4 REMAINS OPEN. §16.6.2 remains candidate architecture,
not architecture of record.**

**Date:** 2026-09-22 · **Slice:** `S04` (Process-topology spike and ADR) ·
**Resolves:** nothing · **Refers:** §16.6.1, §17-O4, §11.7 · **Verification:** `manual-observation`

§16.6.1 names four measurements for this spike. Two are complete, one is partial,
and one was **not run at all** — and the one not run is the only axis on which
candidate B carries any risk. The measurements below are real, and they are
one-sided in B's favour. That one-sidedness is an artefact of which axes were
tested, not evidence that B is better. Recording a decision on this evidence
would be recording a decision from the wrong experiment.

## Context — the two candidates

Restated from §16.6.1, unchanged:

- **Candidate A — two origins.** A renderer on one port; the editor chrome on
  another; the site in an `<iframe>`; `postMessage` with explicit `targetOrigin`.
- **Candidate B — single origin.** One server **proxies** the renderer; editor
  chrome and site preview are same-origin, so the editor reads the preview DOM directly.

## What was actually built

| Path | Port | Role |
|---|---|---|
| `spikes/topology/shared/doc.json` | — | one document, seeded `h1,p1,p2` |
| `spikes/topology/shared/model.ts` | — | one `move()` and one `renderPreview()`, shared by both |
| `spikes/topology/b-single-origin/server.ts` | 8830 | candidate B: editor + preview + API, one process |
| `spikes/topology/a-two-origin/preview-server.ts` | 8832 | candidate A: preview + API, injects the bridge |
| `spikes/topology/a-two-origin/editor-server.ts` | 8831 | candidate A: editor chrome only |

Both topologies mutate the same document through the same `move()`. Lines that
exist **only** to carry the chrome↔preview channel are tagged `//CHANNEL` in source.

## The measurements

### (i) Lines of code in the chrome↔preview channel — COMPLETE

| Topology | Channel-only lines | Method |
|---|---|---|
| **A — two origins** | **48** | `grep -h '//CHANNEL' a-two-origin/*.ts \| grep -vc '^\s*\*'` |
| **B — single origin** | **4** | same, `b-single-origin/*.ts` |
| **Delta** | **+44 permanent lines in A** | |

The count excludes the one doc-comment that merely names the tag. What the 44
extra lines *are* matters more than the count: two `e.origin` equality checks,
a five-key CORS header helper plus an `OPTIONS` preflight branch, a
request/reply protocol with correlation ids and a 2-second reject timeout, and
a bridge `<script>` injected into every preview response. **Every one of them is
security-relevant.** A dropped `e.origin` check or a `targetOrigin` of `"*"`
converts this channel into an open door, and neither mistake fails any test —
it just works, insecurely.

### (ii) Preview-only screenshot without editor chrome in frame — COMPLETE, both achievable

| Capture | sha256 | Size |
|---|---|---|
| `preview-only-A-bare.png` (bridge suppressed via `?bare=1`) | `6699982bd8fcffff1097c81c0018f950f227f8bda9fa1ff4cca9c1b0797eecbd` | 700×420 |
| `preview-only-A-bridged.png` | `6699982bd8fcffff1097c81c0018f950f227f8bda9fa1ff4cca9c1b0797eecbd` | 700×420 |
| `preview-only-B.png` | `6699982bd8fcffff1097c81c0018f950f227f8bda9fa1ff4cca9c1b0797eecbd` | 700×420 |

**All three are byte-identical.** Both topologies satisfy the requirement, and
the injected bridge leaves no visible artefact whatsoever.

**Caveat, stated because the result flatters B.** Identical bytes prove the
*bridge* is invisible. They do not prove B keeps its preview DOM clean under a
real editor, because **neither spike injects editor affordances** — no selection
outlines, no drag handles, no gridlines — into the preview DOM. §16.6.1 names
"harder to keep the preview DOM free of editor artifacts" as B's risk, and this
spike never created the condition under which that risk appears.

### (iii) HMR round-trip latency — **NOT MEASURED**

Neither spike runs Astro, Vite, or any hot-module-reload machinery at all.

What was measured instead is a **document-move round trip**: POST `/api/move` →
server mutates → iframe reloads → editor reads the block order back. 25
iterations each, first iteration discarded as warm-up:

| Topology | n | min | **p50** | p90 | max | mean |
|---|---|---|---|---|---|---|
| **B — single origin** | 24 | 2.5 | **5.0 ms** | 9.7 | 23.2 | 6.4 ms |
| **A — two origins** | 24 | 3.2 | **6.3 ms** | 14.5 | 23.8 | 7.6 ms |

The `postMessage` leg costs roughly **1.3 ms at the median** — two orders of
magnitude below the ~100 ms threshold at which an interaction stops feeling
immediate. On this axis the two topologies are indistinguishable to a user.

**This is not the chartered measurement.** A move round trip and an HMR round
trip differ in exactly the component that makes HMR risky for B: the websocket
passthrough inside the proxy. Reporting this number under the name "HMR latency"
would be reporting a different experiment.

### (iv) Behaviour after killing and restarting the renderer — PARTIAL, and it **inverts** the PRD's stated benefit

§16.6.1 credits candidate A with: *"Isolation: the site page stays pristine;
editor survives an Astro restart."*

Measured, after 30 successful moves had taken both documents to order `p2,h1,p1`:

| Step | A — two origins | B — single origin |
|---|---|---|
| Kill the preview process | editor `:8831/editor` → **HTTP 200, survives** | editor `:8830/editor` → **connection refused** |
| Preview after the kill | connection refused | connection refused |
| Any operation after the kill | **connection refused** | connection refused |
| Document order after restart | **`h1,p1,p2`** — reverted to seed | **`h1,p1,p2`** — reverted to seed |
| Unsaved-edit counter after restart | **0** — all 30 lost | **0** — all 30 lost |

A's editor process survives, but it survives as a **shell that refuses every
action**, and the user's 30 edits are lost regardless, because the document
lives in the process that was killed. On this evidence A's isolation is
**cosmetic** — and a live-looking editor that silently refuses everything is
arguably a worse failure mode than a window that visibly disappears, because
only the second one tells the user what happened.

**Two honest limits on that finding.** First, this is a property of *where this
spike put the state*, not of the topology: a two-origin design that owns the
document in the **editor** process would genuinely survive a renderer restart,
and neither spike implements that. The measurement therefore retires the
isolation claim *as embodied here*, not the claim in principle. Second, what was
killed was a Bun preview server, **not `astro dev`** — the shape is analogous,
the subject is not the chartered one.

## Charter behaviours that were never exercised

§16.6.1 requires the slice to *"load a page, select a node, change one text
string, swap one component variant, observe HMR."*

| Behaviour | Status |
|---|---|
| Load a page | done |
| Mutate the document (block order) | done — **not one of the five** |
| Select a node | **not done** |
| Change one text string | **not done** |
| Swap one component variant | **not done** |
| Observe HMR | **not done** |

## Why this cannot decide O4

§17-O4 asks, verbatim: *"Single-origin proxy vs two-origin iframe + postMessage —
which is less total complexity **once auth, SSE and HMR are wired**?"*

**None of auth, SSE, or HMR is wired in either spike.** Worse, §16.6.1's named
risk for candidate B is *"HMR websocket breakage inside the proxy"* — and the B
built here **is not a proxy at all**. It serves its own preview directly, which
is the one configuration in which that risk cannot occur.

So the spike measured the three axes where B wins cheaply and skipped the single
axis where B might lose. B leading 48-to-4 on channel code is true and it is not
evidence, because the proxy code that would close that gap was never written.

## Spec defect found — §11.7 contradicts §16.6.1

§11.7 is titled, normatively, **"Preview must be a same-origin iframe."**
§16.6.1 states that single-origin versus two-origin is **open**.

Both cannot hold. If §11.7's title binds, candidate A is already excluded and
there is nothing for this spike to settle. If instead "same-origin" is inherited
from the quoted Puck documentation — §11.7's stated *reason* is media-query
evaluation, which **any** iframe satisfies regardless of origin — then O4 is
genuinely open and §11.7's title overstates its own requirement.

**Referred, not resolved.** O4 is an open item, and this ADR does not decide open
items. This contradiction should be settled **before** the spike is redone,
because one reading makes the spike unnecessary.

## Decision

**None.** §17-O4 stays open. §16.6.2 stays candidate architecture. Until O4
lands, only §16.6.2's topology-independent invariants may be built.

## What would actually settle it

1. Settle §11.7 first. If its title binds, O4 is moot and the spike is not rerun.
2. Put `astro dev` behind candidate B as a **real proxy**, passing the HMR
   websocket through, and wire `wb-server`'s SSE on the same origin — B's two
   named risks, neither of which exists in the current B.
3. Re-run (iii) as a genuine HMR round trip, not a move round trip.
4. Exercise the four missing charter behaviours: select a node, change a text
   string, swap a variant, observe HMR.
5. Move document ownership into the editor process in candidate A before
   re-testing (iv), so the isolation claim is tested at its strongest.

## Harness defects found and fixed during this spike

Recorded because they explain why (iii) reported nothing for several attempts,
and because two of them are the same class of bug:

1. **Both bench pages contained a JavaScript syntax error.** `\n` inside a Bun
   template literal became a *real* newline in the served HTML, splitting a
   quoted string across two lines. The whole `<script>` failed to parse, so no
   request ever left the page — `unsaved` stayed at 0 while the page read
   "running…". Fixed by reporting results as JSON instead of an escaped string.
   This is the same shell/template escape-mangling that produced the invalid
   `c.font` assignment in the S02 fixture.
2. **Neither bench page ever POSTed its result.** `/api/bench-result` was polled
   but nothing wrote to it, so it would have read `{"pending":true}` forever even
   after fix 1.
3. **Candidate A's initial iframe wait could never resolve.** It awaited
   `pv.onload` with no already-loaded guard; if the iframe had already loaded,
   the event never fired again. Both pages now force one reload and cap the wait.
4. **`--virtual-time-budget` is required for `--screenshot` and fatal for the
   bench.** Without it a headless screenshot of the bridged preview never
   returned; with it, the interactive bench froze before its first request.
   The two runs now use different Chrome invocations for that reason.
5. **A stale-result read produced a fabricated-looking statistic.** An n=25 run
   was polled against a result the server still held from an n=5 run, and the
   "n=25" table printed n=4. Caught because A appeared to beat B, which is
   backwards. The poller now waits for the matching `n`.

## Evidence

`.acos/evidence/2026-09-22/S04-topology/` — five PNGs (hashes above).
Raw latency arrays: `/tmp/bench-B-n25.json`, `/tmp/bench-A-n25.json`.

- B: `[13.6,23.2,9.1,9.3,14.6,7,5,7.6,7.7,6.2,3.3,2.5,3,3.7,9.7,4.1,3.7,5,2.7,3.2,2.9,3.7,8.3,3.6,4.5]`
- A: `[14.6,12.1,23.8,14.5,10.9,16.5,8.7,6.3,5,6.9,3.7,9.6,4.2,4.5,8.6,4.2,3.7,6.6,3.6,3.2,5.8,7.4,4,5.2,3.8]`
