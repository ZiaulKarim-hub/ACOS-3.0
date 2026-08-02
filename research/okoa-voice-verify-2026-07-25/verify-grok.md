# Grok (xAI) — Real-Time Cascade BRAIN Verification
Verifier: grok | Date of research: 2026-07-24
Sources: LIVE primary xAI docs (docs.x.ai) fetched today. WebSearch budget was exhausted
(200/200) so all findings come from direct WebFetch of xAI's own documentation URLs.
Note: none of the fetched xAI pages display an explicit "last-updated" date; "as_of" = fetch date 2026-07-24.

---

## G1 — Does "Grok 4.5" exist? Current version(s)?  VERIFIED
YES. `grok-4.5` is a live, currently-recommended xAI model.
- Model card: ID `grok-4.5` (aliases `grok-4.5-latest`, `grok-build-latest`); 500k context;
  modalities text+image -> text; reasoning model; function calling YES; structured outputs YES.
- The models page lists it as "Recommended for code and chat."
Other current models in the live lineup (same pages):
  grok-4.3 (1M ctx), grok-4.20-0309-reasoning, grok-4.20-0309-non-reasoning,
  grok-4.20-multi-agent-0309 (all 1M ctx), grok-build-0.1 (256k ctx, coding, early access).
Primary URLs:
  https://docs.x.ai/docs/models/grok-4.5  (model card)
  https://docs.x.ai/docs/models          (lineup + pricing table)

## G2 — Availability: API? Cloud-only or self-host/open-weights?  VERIFIED (cloud API); NO self-host found
- Offered via xAI cloud API at base URL https://api.x.ai/v1 (OpenAI-compatible; XAI SDK, OpenAI SDK,
  Vercel AI SDK, cURL all shown).
- grok-4.5 availability regions: us-east-1, us-west-2.
- NO self-host / on-prem / open-weights option is mentioned anywhere in the current primary docs for
  grok-4.5 or any current model. The overview page explicitly frames all models as cloud APIs.
  (Historical Grok-1/Grok-2 weight releases are not the current model and were not confirmable via
  live primary source in this session — treat current Grok as cloud-only.)
Primary URLs:
  https://docs.x.ai/docs/overview
  https://docs.x.ai/docs/models/grok-4.5

## G3 — Real-time fitness: latency / TTFT / low-latency tier?  UNVERIFIABLE (no figures); NO fast tier found
- NO published latency, time-to-first-token, or tokens/sec figures appear on any fetched primary page
  (models, model card, pricing, chat guide, function-calling guide). UNVERIFIABLE from primary source.
- NO dedicated fast/mini/low-latency Grok tier found: URL https://docs.x.ai/docs/models/grok-4-fast
  returns HTTP 404, and the pricing page lists NO fast/mini tier.
- grok-4.5 is a REASONING model (adds thinking tokens/latency) — structurally poor for a sub-second
  voice turn. A lower-latency path would be the NON-reasoning variant `grok-4.20-0309-non-reasoning`,
  but no latency numbers are published to confirm sub-second turns.
=> Sub-second voice-turn fitness is UNPROVEN from primary sources; this is the load-bearing caveat.
Primary URLs:
  https://docs.x.ai/docs/models  |  https://docs.x.ai/docs/pricing  |  https://docs.x.ai/docs/guides/chat

## G4 — Pricing (per 1M tokens, published)  VERIFIED
grok-4.5:
  <200k prompt:  input $2.00 | cached $0.30 | output $6.00
  >=200k prompt: input $4.00 | cached $0.60 | output $12.00
For reference (cheaper alternates): grok-4.3 & grok-4.20-* = $1.25/$2.50 (<200k), $2.50/$5.00 (>=200k);
grok-build-0.1 = $1.00/$2.00 (<200k).
Rate limits (grok-4.5): 150 req/s, 50,000,000 tokens/min.
Primary URLs:
  https://docs.x.ai/docs/pricing  |  https://docs.x.ai/docs/models/grok-4.5

## G5 — Steerability: system prompts + tool calling?  VERIFIED
- System prompts: YES. Chat guide shows `{"role":"system","content":"You are Grok..."}` — supports a
  constitutional system prompt.
- Tool/function calling: YES ("Define custom tools that the model can invoke during a conversation...");
  model card lists "Function calling: Yes" and structured outputs YES — supports agent actions.
Primary URLs:
  https://docs.x.ai/docs/guides/function-calling  |  https://docs.x.ai/docs/guides/chat
  https://docs.x.ai/docs/models/grok-4.5

## G6 — Bottom line
Grok 4.5 is a VIABLE cloud cascade BRAIN on paper: live on the xAI API, OpenAI-compatible, supports
system prompts + tool calling + structured outputs, 500k context, mid-market pricing ($2/$6 per 1M).
BUT the load-bearing caveats for a REAL-TIME voice agent:
  1. NO published latency/TTFT and NO dedicated sub-second low-latency tier (grok-4-fast = 404) — the
     recommended model is a reasoning model, which adds thinking latency. Real-time voice turn latency
     is UNPROVEN from primary sources; must be benchmarked live before committing.
  2. Cloud-only — no self-host/open-weights path for the current model.
  3. Only 2 US regions (us-east-1, us-west-2).
Recommended: if pursuing Grok, benchmark `grok-4.20-0309-non-reasoning` (or grok-4.5 with reasoning
disabled if supported) for TTFT on a live voice turn before relying on it.

## Fetch failures / gaps
- https://x.ai/api returned HTTP 403 (could not verify marketing/API landing page).
- No primary page exposed an explicit publication/last-updated date.
