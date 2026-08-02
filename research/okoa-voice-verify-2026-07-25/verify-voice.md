# Voice-layer fact verification — 2026-07-24

Method: LIVE primary-source WebFetch only (official Cartesia + ElevenLabs docs and
product/pricing pages). WebSearch budget was exhausted (200/200), so all findings come
from direct fetches of official documentation URLs. No memory/training used. Pages did
not surface explicit "last updated" dates in the fetched markdown (Cartesia and
ElevenLabs docs do not print per-page dates), so `as_of` = "fetched 2026-07-24" unless
noted.

---

## V1 — Cartesia Sonic latency: ~90ms model time and ~188ms measured (P50, TTFA)
VERDICT: VERIFIED (partial — vendor confirms the 90ms model figure; the 188ms measured
value is NOT vendor-published)

- Cartesia's own Sonic product page headline states Sonic is "the fastest and most
  natural text to speech model" with "sub-90ms latency."
- This corroborates the "~90ms model time" portion of the claim.
- The "~188ms measured (P50, time-to-first-audio)" number does NOT appear on any Cartesia
  primary source. That is a third-party end-to-end benchmark figure (e.g.
  Artificial Analysis / independent TTFA measurements), not published by Cartesia. It
  cannot be confirmed from a primary vendor source.
- Corrected framing: Cartesia publishes "sub-90ms latency" (model latency). Any ~188ms
  P50 TTFA is a measured, network-inclusive third-party figure, not a Cartesia claim.
- Source: https://cartesia.ai/sonic  (no page date shown)

## V2 — Cartesia can output native telephony audio at 8kHz (mu-law / a-law)
VERDICT: VERIFIED

- Cartesia TTS API reference lists encodings: `pcm_f32le`, `pcm_s16le`, `pcm_mulaw`
  (mu-law), `pcm_alaw` (a-law).
- Supported sample rates include 8000 Hz (plus 16000, 22050, 24000, 44100, 48000).
- 8kHz + mu-law/a-law = standard telephony (G.711) audio. Claim fully confirmed.
- Source: https://docs.cartesia.ai/api-reference/tts/tts  (no page date shown)

## V3 — Cartesia supports voice cloning; self-hosted/on-prem EXCLUDES cloning creation
VERDICT: VERIFIED

- Voice cloning IS a Cartesia product feature: dedicated docs exist
  (clone-voices, clone-voices-pro, /api-reference/voices/clone).
- Self-hosted introduction page's supported-products table explicitly states:
  "Voice Cloning — Not supported" (self-hosted also does not support Voice Agents).
  Self-hosted covers the TTS/STT models only (Sonic 2 / 3 / 3.5, Ink Whisper, Ink 2 via
  Kubernetes; Sonic 3 also AWS SageMaker), with an air-gapped deployment option.
- Both halves of the claim confirmed: cloning offered in cloud; excluded self-hosted.
- Sources:
  https://docs.cartesia.ai/self-hosted/introduction  ("Voice Cloning — Not supported")
  https://docs.cartesia.ai/build-with-cartesia/capability-guides/clone-voices  (cloning offered)
  (no page dates shown)

## V4 — ElevenLabs TTS latency ~264ms (Turbo/Flash tier) time-to-first-audio
VERDICT: UPDATED (corrected — vendor's published figures are much lower)

- ElevenLabs models overview lists Flash v2.5 at "Ultra-low latency (~75ms†)" where the
  dagger means "Excluding application & network latency" — i.e. ~75ms MODEL INFERENCE.
- Latency-optimization guide gives Flash v2.5 real, network-inclusive WebSocket TTFB by
  region: North America / Europe / Southeast Asia = "100-150ms"; South Asia /
  Northeast Asia = "150-200ms".
- The latency-concepts page repeats "~75ms model inference for typical short inputs."
- So ElevenLabs' OWN numbers are ~75ms model inference and 100-200ms end-to-end TTFB for
  Flash v2.5 — NOT ~264ms. The 264ms figure is not vendor-published (would be a
  third-party end-to-end measurement) and exceeds the vendor's stated TTFB.
- Turbo v2.5 has no specific ms figure in the fetched official pages.
- Corrected value: Flash v2.5 ≈ 75ms model inference / 100-200ms TTFB (region-dependent).
- Sources:
  https://elevenlabs.io/docs/overview/models  ("~75ms†")
  https://elevenlabs.io/docs/eleven-api/guides/how-to/best-practices/latency-optimization  ("100-150ms" / "150-200ms")
  https://elevenlabs.io/docs/eleven-api/concepts/latency  ("~75ms model inference")
  (no page dates shown)

## V5 — ElevenLabs supports brand-voice cloning
VERDICT: VERIFIED

- ElevenLabs offers Instant Voice Cloning AND Professional Voice Cloning (PVC).
- PVC page: "create a custom voice clone from your own audio recordings" via speaker
  separation, verification, and training; requires Creator plan or above and identity
  verification (voice owner records a CAPTCHA phrase). This is exactly brand/custom-voice
  cloning.
- Source:
  https://elevenlabs.io/docs/eleven-api/guides/how-to/voices/professional-voice-cloning
  (also instant-voice-cloning; no page date shown)

## V6 — ElevenLabs: no true customer-run VPC/on-prem GA; only data residency +
##        zero-retention; on-prem early-access/waitlist
VERDICT: UPDATED (claim's spirit holds — nothing self-serve/GA on-prem — but it now
understates what exists: a gated Private Deployment inside the customer's own AWS cloud)

- Enterprise page: offers regional Data Residency (US, EU, India), Zero-Retention Mode
  (HIPAA — inputs/outputs not stored after processing), and "custom deployments" where a
  forward-deployed engineering team integrates ElevenLabs "across private environments."
- Private Deployment overview: "available to authorized enterprise customers" — contact
  sales, NOT generally available / not self-serve. Runs models "within their own secure
  cloud infrastructure" via AWS Marketplace, Amazon SageMaker, and AWS Nitro Enclaves;
  "all text, audio or call data remains within your infrastructure." Includes v2/v2.5 TTS
  and Scribe V2 STT.
- So: there is NO self-serve, generally-available on-prem product, and no self-serve VPC —
  consistent with the claim's intent (gated / contact-sales, effectively early-access).
  BUT the claim's "only data residency + zero-retention" is now outdated: ElevenLabs has a
  gated Private Deployment that runs in the customer's OWN AWS cloud (SageMaker / Nitro
  Enclaves). That is cloud-in-your-own-account, still not true on-prem, and still
  enterprise/sales-gated (not GA).
- Corrected value: No self-serve/GA on-prem or VPC. Options = Data Residency (US/EU/India)
  + Zero-Retention + a contact-sales/enterprise-gated Private Deployment inside the
  customer's own AWS cloud (Marketplace / SageMaker / Nitro Enclaves). No true on-prem GA.
- Sources:
  https://elevenlabs.io/docs/eleven-api/private-deployment/overview  ("available to authorized enterprise customers")
  https://elevenlabs.io/enterprise  (data residency + zero-retention + private-environment custom deployments)
  (no page dates shown)

## V7 — No vendor publishes a voice-quality score measured at 8kHz telephone bandwidth
##        (all quality/MOS numbers are 24kHz wideband/studio)
VERDICT: UNVERIFIABLE (a universal negative cannot be confirmed from primary sources)

- Neither Cartesia nor ElevenLabs published any MOS / quality score at 8kHz telephone
  bandwidth in the official pages reviewed. Their quality positioning is "most natural" /
  studio-grade wideband (24kHz-class), consistent with the claim's direction.
- However, proving that NO vendor anywhere publishes an 8kHz-bandwidth quality score is a
  universal negative; absence in the pages I fetched is not proof of absence everywhere.
  Per instructions, this is marked UNVERIFIABLE rather than VERIFIED.
- Consistent-with-claim evidence: no 8kHz MOS found on Cartesia or ElevenLabs docs;
  quality framing is wideband/studio.
- Sources (absence of 8kHz MOS): https://cartesia.ai/sonic ; https://elevenlabs.io/docs/overview/models

## V8 — Both Cartesia and ElevenLabs support SSML (or equivalent) with say-as / digits
##        control to force digit-by-digit read-back
VERDICT: UPDATED (asymmetric — Cartesia YES with a real digit/spell tag; ElevenLabs has
NO documented say-as; digit-by-digit is only achievable via a pronunciation-dictionary
alias workaround)

- Cartesia: SSML-tags guide supports `speed`, `volume`, `emotion` (beta), `break`, and
  `<spell>` — "To read input out character by character, wrap it in `<spell>` tags.
  This is useful for confirmation codes, order IDs, serial numbers, or spelling a name."
  Cartesia does NOT support standard `<say-as interpret-as="...">`, but `<spell>` is the
  functional equivalent for digit-by-digit / character-by-character read-back. Cartesia
  also has custom-pronunciation and pronunciation-dictionary endpoints. => Cartesia side
  of the claim SATISFIED (equivalent markup with a digit/spell control).
- ElevenLabs: pronunciation-dictionaries page documents PLS (Pronunciation Lexicon
  Specification) XML with IPA/CMU phoneme tags — and "phoneme tags only work with
  `eleven_flash_v2` and `eleven_v3` models" (other models ignore them). There is NO
  documented `<say-as>` / spell-out / digit-by-digit SSML control. Digit-by-digit
  read-back must be forced via a pronunciation-dictionary ALIAS substitution (e.g. map
  "123" -> "1 2 3") or by spacing digits in the input text — a workaround, not a native
  say-as/digits control.
- Net: the claim that BOTH support a say-as/digits control is not accurate as stated.
  Cartesia has a genuine `<spell>` digit tag; ElevenLabs has phoneme tags (limited to
  flash_v2 / v3) + alias dictionaries, but no native say-as/spell-out.
- Sources:
  https://docs.cartesia.ai/build-with-cartesia/capability-guides/ssml-tags  (`<spell>`)
  https://elevenlabs.io/docs/eleven-api/guides/how-to/text-to-speech/pronunciation-dictionaries  (PLS/phoneme, flash_v2 & v3 only; no say-as)
  (no page dates shown)

---

## Summary of verdicts
- V1 VERIFIED (90ms model confirmed; 188ms measured is third-party, not vendor)
- V2 VERIFIED (8kHz + mu-law/a-law confirmed)
- V3 VERIFIED (cloning offered; self-hosted "Voice Cloning — Not supported")
- V4 UPDATED (vendor: ~75ms model / 100-200ms TTFB Flash v2.5, not ~264ms)
- V5 VERIFIED (Instant + Professional voice cloning)
- V6 UPDATED (no self-serve/GA on-prem; now also a gated Private Deployment in customer's own AWS cloud)
- V7 UNVERIFIABLE (universal negative; no 8kHz MOS found, consistent with claim)
- V8 UPDATED (Cartesia `<spell>` yes; ElevenLabs no native say-as, only phoneme/alias workaround)
