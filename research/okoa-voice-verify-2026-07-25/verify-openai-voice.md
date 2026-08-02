# OpenAI Voice Models — Fact Verification
Verifier: openai-voice | Research date: 2026-07-24
Primary sources: developers.openai.com/api/docs (OpenAI platform docs, moved from platform.openai.com), OpenAI changelog, learn.microsoft.com (Azure Foundry/OpenAI docs).
Method note: WebSearch budget was exhausted for the session (200/200); all findings below come from direct WebFetch of primary-source pages. openai.com/news and openai.com/index/* blog posts returned HTTP 403 (bot-blocked), so blog-only claims (notably latency ms) could not be confirmed and are marked UNVERIFIABLE rather than filled from memory.

WebFetch reliability caveat: OpenAI's individual model-detail pages, read through WebFetch's summarizer, repeatedly returned a bogus "Release Date: September 30, 2024" for multiple distinct models — a confabulation/template artifact. Dates below are taken from the OpenAI CHANGELOG and the Azure Foundry models table (which carry real per-model dates), not from those model-detail summaries.

---

## O1 — Current voice-capable models as of 2026-07-24

### Speech-to-speech / Realtime family (audio-in → audio-out)
Confirmed from OpenAI models list + Azure Foundry models table (learn.microsoft.com, page updated 2026-07-23):
- **gpt-realtime-2.1** — released 2026-07-06 (OpenAI changelog) / 2026-07-07 (Azure). NEWEST. "Reasoning model with tool use"; "Realtime 2 adds reasoning to speech-to-speech workflows." Azure notes: "Minor updates over gpt-realtime-2 with improved silence and noise handling." Docs: "updates GPT-Realtime-2 with improved alphanumeric recognition, silence and noise handling, and interruption behavior."  ← FLAGGED: released ~2.5 weeks ago; this is almost certainly the "GPT models with voice ~a week ago" the user meant.
- **gpt-realtime-2.1-mini** — released 2026-07-06/07. Distilled, faster, lower-cost. NEWEST. ← FLAGGED (same July release).
- gpt-realtime-2 — 2026-05-07
- gpt-realtime-translate — 2026-05-06 (streaming speech-to-speech translation; hourly billing)
- gpt-realtime-whisper — 2026-05-06 (streaming speech-to-TEXT / transcription; hourly billing)
- gpt-realtime-1.5 — 2026-02-23 (OpenAI models list still tags it "The best voice model for audio in, audio out")
- gpt-realtime (GA) — 2025-08-28; gpt-realtime-mini — 2025-10-06 / 2025-12-15 (OpenAI list shows gpt-realtime mini as Deprecated)

### Audio generation via Chat Completions (audio-in/text-in → audio-out)
- **gpt-audio-1.5** — released 2026-02-23 (Chat Completions API). Modalities in/out: text+audio. Usable as audio-out in a cascade via Chat Completions (`audio: { voice, format }`). NEWEST in this line.
- gpt-audio — 2025-08-28; gpt-audio-mini — 2025-10-06

### Dedicated text-to-speech (text-in → audio-out, /v1/audio/speech)
- **gpt-4o-mini-tts** — TTS guide calls it "our newest and most reliable text-to-speech model." Azure lists snapshots 2025-03-20 and 2025-12-15 (newest). NOTE CONFLICT: the OpenAI models *list*, read via WebFetch, showed a "Deprecated" badge on gpt-4o-mini-tts, but the TTS guide (2026) recommends it and Azure carries a fresh 2025-12-15 snapshot — so the "Deprecated" badge is judged a WebFetch misread; treat gpt-4o-mini-tts as CURRENT.
- Legacy TTS: tts-1, tts-1-hd (Azure: `tts`, `tts-hd`) — still available.

### Transcription (STT): gpt-4o-transcribe, gpt-4o-mini-transcribe, gpt-4o-transcribe-diarize, whisper, gpt-realtime-whisper.

Nothing dated exactly ~2026-07-17 for voice. Closest voice release = gpt-realtime-2.1 (July 6). GPT-5.6 model family shipped July 9, 2026 (text/reasoning, per changelog) — possible source of the user's "GPT models a week ago" impression, but the VOICE release is gpt-realtime-2.1.

---

## O2 — Newest speech-to-speech model (gpt-realtime-2.1)
- Model IDs: `gpt-realtime-2.1`, `gpt-realtime-2.1-mini`. Released 2026-07-06 (OpenAI) / 2026-07-07 (Azure).
- Capabilities: single-model speech-to-speech ("audio in, audio out"), reasoning with tool use (start `reasoning.effort: low` for production voice agents), image input also supported per model-detail summary; improved alphanumeric recognition, silence/noise handling, interruption/barge-in behavior. Azure context window listed as Input 32,000 / Output 4,096 tokens for the realtime line.
- Voices: PRESET voice set. The documented shared voice roster (from the TTS guide, 13 voices) is: alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer, verse, marin, cedar (marin & cedar are the newer flagship voices introduced with gpt-realtime). Realtime guide itself did not re-enumerate voices in fetched content.
- Custom voice CLONING: SUPPORTED for eligible customers. Changelog 2025-12-15: "This launch also includes support for Custom voices for eligible customers." TTS guide describes the process: a consent recording + a sample recording (max ~30s, specific formats); "custom voices are limited to eligible customers." So a brand voice is POSSIBLE but gated (approval + consent/sample recordings), not open self-serve.
- Latency: UNVERIFIABLE from a primary source reachable now. Docs describe the model as for "low-latency voice agents" but state no ms figure; OpenAI blog posts that historically cite ~sub-300ms/end-to-end numbers are 403 bot-blocked and were not used.

---

## O3 — Newest dedicated TTS (cascade) model
- Recommended dedicated TTS: **gpt-4o-mini-tts** (text-in → audio-out via /v1/audio/speech). Newest snapshot 2025-12-15 (Azure). Alternative audio-out path: gpt-audio-1.5 via Chat Completions.
- Voices: 13 — alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer, verse, marin, cedar (tts-1/tts-1-hd support a 9-voice subset).
- Style control: an `instructions` parameter controls accent, emotional range, intonation, impressions, speed, tone, whispering. Custom voices supported for eligible customers (see O2).
- SSML / say-as / digit control: NO SSML and NO say-as tag documented for the TTS endpoint. Instead, digit-by-digit / alphanumeric read-back is handled by PROMPTING on the realtime side. The Realtime prompting guide states: "Realtime S2S can blur or merge digits/letters when reading back key info (phone, credit card, order IDs). Explicit character-by-character confirmation prevents mishearing" and "For numeric identifiers, read the value back digit by digit. Reading the value as a full number can hide errors" (example: "8… 3… 5… 2… 1"), plus email spell-back guidance. So number-read-back control exists as a PROMPT technique, not a markup tag.
- Latency: no ms figure published; guide recommends `wav`/`pcm` output "for the fastest response times." UNVERIFIABLE (exact number).

---

## O4 — Deployment & data handling
- CLOUD-ONLY. These voice models are not open-weight; no self-host / on-prem / true VPC. Available via: (1) OpenAI API, (2) Azure OpenAI / Microsoft Foundry (realtime, completions, and /audio APIs; enterprise data residency; Azure states it doesn't use customer data to train), (3) OpenAI models on Amazon Bedrock via Responses API (changelog 2026-06-01) — but that path is text/Responses, not confirmed for realtime voice.
- Data retention (OpenAI, from docs/guides/your-data): API data not used to train models by default since 2023-03-01 (unless opted in). Default abuse-monitoring log retention up to 30 days. Zero Data Retention (ZDR) available to approved customers (forces store=false, excludes content from abuse logs). Audio-output application state stored 1 hour for multi-turn. /v1/audio/transcriptions and /v1/audio/translations have NO abuse-monitoring retention.
- Data residency: regional STORAGE in US, EEA+Switzerland, Australia, Canada, Japan, India, Singapore, South Korea, UK, UAE. Regional PROCESSING only US, Europe, UAE. Non-US regions need approval for Modified Abuse Monitoring/ZDR.

---

## O5 — Pricing (OpenAI pricing page, per 1M tokens; confirmed consistent across two fetches)
- gpt-realtime-2.1: audio input $32.00, audio output $64.00; text input $4.00, text output $24.00; cached input (text/audio) $0.40.
- gpt-realtime-2.1-mini: audio input $10.00, audio output $20.00; text input $0.60, text output $2.40.
- gpt-audio-1.5: audio input $32.00, audio output $64.00 (same as full realtime-2.1 audio rates).
- gpt-4o-mini-tts: exact rate NOT captured on the pricing page fetch — UNVERIFIABLE here (usage-based; historically per-character/per-token cheap, but not confirmed now).
- Per-MINUTE pricing: not published as a headline; realtime is TOKEN-based (Azure: "most realtime models use token-based input and output pricing"; gpt-realtime-translate and gpt-realtime-whisper use HOURLY billing). No confirmed $/minute figure — UNVERIFIABLE.

---

## O6 — Bottom line
OpenAI's newest voice models are a STRONG option for a real-time website + phone voice agent, in EITHER architecture:
- One-model brain+voice: gpt-realtime-2.1 (or -mini for cost) does speech-to-speech with reasoning + tool use in a single model — lowest-latency path, and July 6 2026 improvements specifically target alphanumeric recognition, barge-in, and noise handling that matter for phone.
- Cascade: your own LLM → gpt-4o-mini-tts (or gpt-audio-1.5) for the voice, giving finer control over exactly what text is spoken.

Load-bearing caveats:
1. Number read-back: there is NO SSML/say-as tag. Digit-by-digit reading of phone numbers, payoff figures, loan IDs, per-diem, etc. must be enforced by PROMPTING (the realtime prompting guide explicitly instructs digit-by-digit read-back). gpt-realtime-2.1 improved alphanumeric handling, but correctness still rides on the prompt — build and test read-back for OKOA dollar amounts/IDs.
2. Brand voice / cloning: custom voices ARE supported but ONLY for "eligible customers" (approval + consent recording + sample recording ≤~30s). Not open self-serve. If a specific branded voice is required, budget for the eligibility/approval process; otherwise use a preset (marin/cedar are the flagship natural voices).
3. Latency: no official ms figure was confirmable from a primary source now (blog 403-blocked) — validate empirically before committing for phone.
4. Cloud-only: no on-prem/self-host; if data isolation is a hard requirement, use Azure OpenAI regional deployment + OpenAI ZDR (approval needed).
5. Cost: realtime audio is $32 in / $64 out per 1M tokens (mini: $10/$20) — meaningfully pricier per conversation than text; model the per-call cost for phone volume, consider gpt-realtime-2.1-mini.
