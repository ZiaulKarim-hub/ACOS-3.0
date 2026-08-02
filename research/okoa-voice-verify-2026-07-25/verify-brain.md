# Fact Verification — Voice-Agent Brain / Orchestration / Technique
Verifier: brain | Date run: 2026-07-24 | Method: WebFetch against live primary sources (WebSearch budget was exhausted; all findings come from direct fetches of official docs / GitHub / model cards / W3C).

---

## B1 — Qwen3-30B-A3B-Instruct-2507 (Apache-2.0, MoE ~3B active, single-GPU real-time voice brain)
VERDICT: VERIFIED (with one deployment caveat)

Primary source: https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507 (official Qwen org model card)
- License: Apache-2.0 — CONFIRMED.
- Architecture: Mixture-of-Experts — 128 total experts, 8 activated per token, 48 layers — CONFIRMED.
- Params: 30.5B total / 3.3B activated (29.9B non-embedding). "~3B active" — CONFIRMED (3.3B).
- Context: 262,144 native, up to 1M with long-context techniques.
- Deployment: card documents serving via vLLM and SGLang.

Caveat on the "fast/low-latency single-GPU real-time voice brain" portion: the card does NOT literally claim single-GPU real-time voice serving. It's an engineering inference, and a reasonable one — only 3.3B params are active per token (low per-token compute → low latency), but the full 30.5B weights are ~61 GB at bf16, so a single 24-32 GB GPU requires quantization (e.g., 4-bit ≈ ~17-20 GB). So: model existence + license + MoE + ~3B-active = fully VERIFIED from primary source; "single-GPU real-time" = achievable but a deployment claim, not stated on the card.
Note: "2507" = July 2025 release (year 25, month 07), not May.
Page date: model collection shown updated 2025-12-31.

---

## B2 — LiveKit Agents (open-source, self-hostable STT+LLM+TTS orchestration, Telnyx SIP)
VERDICT: VERIFIED

Primary sources:
- https://github.com/livekit/agents — README + license. Open-source, License: Apache-2.0 (plus a separate LiveKit Model License for turn-detection models). "any combination of STT, LLM, TTS, or realtime API can be used." "Works seamlessly with LiveKit's telephony stack, allowing your agent to make calls to or receive calls from phones." CONFIRMED open-source + STT+LLM+TTS + SIP telephony.
- https://docs.livekit.io/sip/quickstarts/configuring-telnyx-trunk/ — "Create and configure Telnyx SIP trunk … Step-by-step instructions for creating inbound and outbound SIP trunks using Telnyx." CONFIRMS Telnyx is an officially documented SIP-trunk provider.
Page render date on the Telnyx doc: 2026-07-24.

---

## B3 — Pipecat (open-source, self-hostable, Telnyx telephony, STT+LLM+TTS with barge-in)
VERDICT: VERIFIED

Primary sources:
- https://github.com/pipecat-ai/pipecat — "Pipecat is an open-source Python framework for building real-time voice and multimodal conversational agents." License: BSD-2-Clause. STT (Deepgram, Whisper…), LLM (Anthropic, OpenAI…), TTS (ElevenLabs, OpenAI…). Telnyx listed under Serializers (telephony). CONFIRMED open-source + self-hostable + Telnyx + STT+LLM+TTS.
- https://docs.pipecat.ai/pipecat/fundamentals/interruptions.md — "Interruptions are enabled by default." On user speech: every processor cancels work, LLM stops generating, TTS clears buffers, transport flushes unplayed audio; "The bot goes silent within roughly one audio write." CONFIRMS barge-in/interruption handling on by default.

---

## B4 — SSML <say-as interpret-as="telephone"/digits/characters"> forces digit-by-digit reading (real, standardized)
VERDICT: VERIFIED (mechanism real & standardized; one nuance on "digits")

Primary sources:
- https://www.w3.org/TR/speech-synthesis11/ — SSML 1.1, W3C Recommendation dated 2010-09-07. Defines the say-as element and interpret-as attribute but deliberately does NOT enumerate the value list: "SSML only specifies the say-as element, its attributes, and their purpose. It does not enumerate the possible values for the attributes."
- https://www.w3.org/TR/ssml-sayas/ — "SSML say-as attribute values," W3C Working Group Note dated 2005-05-26. Defines interpret-as="telephone" (a telephone number, hinting the processor to speak it properly) and interpret-as="characters" (spoken as a series of alpha-numeric characters). It defines six values: date, time, telephone, characters, cardinal, ordinal. It does NOT define a "digits" value — digit-by-digit under this note falls under "characters."
- https://docs.aws.amazon.com/polly/latest/dg/say-as-tag.html — live vendor primary source confirming the mechanism is real and shipped: `digits` = "Spells out each digit individually, as in 1-2-3-4"; `telephone` = "Interprets the numerical text as a 7-digit or 10-digit telephone number" and "says each digit individually"; `characters`/`spell-out` = "Spells out each letter of the text, as in a-b-c."

Bottom line: forcing digit-by-digit reading via say-as is a real, standardized technique. "telephone" and "characters" are the W3C-noted values; "digits" is a widely-implemented vendor value (Amazon Polly, and likewise Azure/Google) but is NOT in the W3C say-as note. So the claim is correct in substance; the only correction is that "digits" specifically is a de-facto vendor extension, not a W3C-standardized token.

---

## B5 — Telnyx programmable Voice + Messaging (SIP, media streaming) for AI voice agents
VERDICT: VERIFIED

Primary sources:
- https://telnyx.com/products/voice-api — programmable Voice; "Real-time media streaming … Stream bi-directional RTP audio over secure WebSockets"; "Add voice agents to any call in minutes by chaining TTS, STT, and LLM logic via simple AI Gather and AI Assistant commands"; scale "10M+ call minutes per day," "140+ countries." SIP + media streaming + AI-voice-suitable = CONFIRMED.
- https://telnyx.com/products/messaging-api — "Send and receive SMS or MMS globally with the Telnyx Messaging API"; carrier-grade SMS/MMS with direct routing; SDKs (Python, Java, Node, Ruby, .NET, PHP). CONFIRMS Messaging.
Page render date: 2026-07-24.

---

## B6 — Anthropic Opus 4.8 too slow to be the real-time shipping brain for a live voice call
VERDICT: UNVERIFIABLE as a quantitative fact → correctly framed as a DESIGN ASSUMPTION (directionally supported by primary qualitative data). Plus an UPDATE: Opus 4.8 is now a legacy model.

Primary source: https://platform.claude.com/docs/en/about-claude/models/overview (Anthropic official; docs.claude.com 302-redirects here).
- Claude Opus 4.8 (`claude-opus-4-8`) IS a real model, but it now appears under "Legacy models," superseded by Claude Opus 5 (and Claude Fable 5, GA 2026-06-09). Migration guide points Opus 4.8 → Opus 5.
- Anthropic publishes NO absolute latency figure (no ms/token or TTFT numbers). The only latency signal is a qualitative "Comparative latency" column:
  - Opus 4.8 = "Moderate"
  - Opus 5 = "Moderate"
  - Sonnet 5 = "Fast"
  - Haiku 4.5 = "Fastest"
  - Fable 5 = "Slower"
- Additional latency-relevant fact: "On Claude Opus 4.8, the `effort` parameter defaults to `high` on all surfaces," i.e., it does more reasoning by default → higher latency.

Interpretation: Because no primary numeric latency figure exists, "Opus 4.8 is too slow to be the live-call shipping brain" must be treated as a design assumption, not a verified fact — exactly as the claim itself hedges. It IS directionally supported by primary data: Opus 4.8's comparative latency is "Moderate" (vs Haiku "Fastest" / Sonnet "Fast"), and its default effort=high adds reasoning latency. For a sub-second real-time voice loop, a "Fastest"/"Fast" small model (Haiku, or a self-hosted small MoE like Qwen3-30B-A3B) is the appropriate shipping brain; a "Moderate"-latency frontier reasoning model like Opus 4.8/Opus 5 is better used off the hot path (async/tool/summarization). Design assumption = sound; not a published quantitative fact.
Page date: current as of fetch 2026-07-24 (references Opus 5 / Fable 5 GA 2026-06-09).
