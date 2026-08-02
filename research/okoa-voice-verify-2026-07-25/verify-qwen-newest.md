# Qwen "newest model" verification — as of 2026-07-24

Verifier: qwen-newest
Method: LIVE primary sources only — Hugging Face JSON API (huggingface.co/api/models?author=Qwen),
Qwen HF model cards (huggingface.co/Qwen/...), and QwenLM GitHub (github.com/QwenLM/...).
WebSearch budget was exhausted; all findings below come from direct WebFetch of primary Qwen pages.
No memory/training fill. Anything not confirmable online now is marked UNVERIFIABLE.

------------------------------------------------------------------------
## QN1 — Does "Qwen 3.6" exist? Newest text model family/IDs
VERDICT: VERIFIED — Qwen 3.6 exists.

Primary evidence:
- GitHub repo README (github.com/QwenLM/Qwen3.6): "Qwen3.6 is the large language model series
  developed by Qwen team, Alibaba Group." License Apache 2.0.
- Hugging Face API (sort=createdAt, direction=-1) returns these exact IDs with createdAt:
    Qwen/Qwen3.6-27B-FP8        2026-04-21T07:51:33Z
    Qwen/Qwen3.6-27B            2026-04-21T07:50:43Z
    Qwen/Qwen3.6-35B-A3B-FP8    2026-04-15T06:05:13Z
    Qwen/Qwen3.6-35B-A3B        2026-04-15T05:59:19Z
- A separate, larger Qwen3.5 flagship family also exists (created 2026-04-23/24), exact IDs:
    Qwen/Qwen3.5-397B-A17B (+ -FP8, -GPTQ-Int4)   — top MoE, 397B total / 17B active
    Qwen/Qwen3.5-122B-A10B (+ -FP8, -GPTQ-Int4)   — 122B total / 10B active
    Qwen/Qwen3.5-35B-A3B (+ -FP8, -GPTQ-Int4)
    Qwen/Qwen3.5-27B (+ -FP8, -GPTQ-Int4)
    Qwen/Qwen3.5-9B-Base, Qwen3.5-4B-Base, Qwen3.5-2B-Base, Qwen3.5-0.8B-Base

Reading: "Qwen3.6" is a point-release covering the small/mid tier (27B dense, 35B-A3B MoE, ~Apr 2026),
sitting alongside the larger Qwen3.5 MoE flagships (397B-A17B / 122B-A10B). No "Qwen4" exists as of today.
NEWEST text model family = Qwen3.6 (Apr 2026). Prior research's Qwen3-30B-A3B is now one generation old.
Source: https://github.com/QwenLM/Qwen3.6 ; https://huggingface.co/api/models?author=Qwen&sort=createdAt&direction=-1

------------------------------------------------------------------------
## QN2 — Newest multimodal/speech (Omni) model; can it talk?
VERDICT: UPDATED — newest omni-modal UNDERSTANDING has advanced, but newest TALK model is unchanged.

- Newest audio releases (2026) are RECOGNITION ONLY, not talk:
    Qwen/Qwen3-ASR-0.6B-hf    created 2026-06-26, lastModified 2026-07-22  (speech-to-text)
    Qwen/Qwen3-ASR-1.7B-hf    created 2026-06-26, lastModified 2026-07-22  (speech-to-text)
    Qwen/Qwen3-ForcedAligner-0.6B-hf  created 2026-06-26                    (alignment)
  These transcribe; they do NOT speak.
- Newest model that OUTPUTS real-time speech (can talk) is STILL Qwen3-Omni, released 2025-09-22.
  Exact IDs (github.com/QwenLM/Qwen3-Omni): Qwen3-Omni-30B-A3B-Instruct,
  Qwen3-Omni-30B-A3B-Thinking, Qwen3-Omni-30B-A3B-Captioner.
  Repo states: "real-time streaming responses in both text and natural speech",
  "Low-latency streaming with natural turn-taking and immediate text or speech responses." => YES it talks.
- NO Qwen3.5-Omni or Qwen3.6-Omni exists as of 2026-07-24 (not in HF newest-created/newest-modified top 50;
  Qwen3-Omni repo shows no successor). Qwen3.6-35B-A3B has VISION (image understanding) but does NOT emit speech.
Source: https://github.com/QwenLM/Qwen3-Omni ; https://huggingface.co/api/models?author=Qwen&sort=lastModified&direction=-1

------------------------------------------------------------------------
## QN3 — Newest fast/small text brain for a real-time voice agent
Model: Qwen/Qwen3.6-35B-A3B  (direct successor to Qwen3-30B-A3B; same 3B active params)
- Size: "35B in total and 3B activated" (MoE). 256 experts, 8 routed + 1 shared active. 40 layers,
  hybrid arch "Gated DeltaNet -> MoE ... Gated Attention -> MoE".
- Context: 262,144 native, extensible to ~1,010,000 tokens.
- License: Apache 2.0.
- Type: multimodal (text+vision) reasoning model; "operate in thinking mode by default"
  (<think>...</think>). NOTE: for a low-latency voice agent you'd run it in non-thinking mode;
  a dedicated non-thinking "-Instruct-2507"-style variant was NOT confirmed for 3.6 (only the base
  thinking-by-default card was found). Consideration, not a blocker.
- Benchmarks (card): SWE-bench Verified 73.4, MMLU-Pro 85.2, AIME26 92.7, RealWorldQA 85.3, MMBench 92.8.
- Latency / tokens-per-sec: UNVERIFIABLE — no throughput or tok/s figures published on the model card.
- Smaller alternatives if you want dense + lower VRAM: Qwen/Qwen3.5-27B (dense) or Qwen/Qwen3.6-27B.
Source: https://huggingface.co/Qwen/Qwen3.6-35B-A3B

------------------------------------------------------------------------
## QN4 — Newest speech/omni model: self-host, cloning, latency
Model: Qwen/Qwen3-Omni-30B-A3B-Instruct (released 2025-09-22; still newest talk model)
- Self-host: YES. HF Transformers (class Qwen3OmniMoeForConditionalGeneration) and vLLM (custom branch)
  both documented for local deployment. Apache 2.0.
- Voices: FIXED PRESETS ONLY — three named voices: Ethan (M), Chelsie (F), Aiden (M).
  Voice cloning: NOT supported (no cloning mentioned; preset voices only).
- Real-time speech out: YES (repo: real-time streaming, low-latency, natural turn-taking).
- Numeric latency (first-packet / end-to-end ms): UNVERIFIABLE — no numeric latency figure appears on the
  GitHub repo page or the HF model card fetched today (only qualitative "low-latency / real-time").
Source: https://github.com/QwenLM/Qwen3-Omni ; https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct

------------------------------------------------------------------------
## QN5 — Bottom line
- TEXT BRAIN: YES, upgrade. Qwen3.6-35B-A3B (Apr 2026) is a newer, better fast self-hostable brain than
  Qwen3-30B-A3B-Instruct-2507 — same 3B active params, Apache 2.0, longer native context (256K), stronger
  benchmarks. It is the natural drop-in successor for the cascade's text brain. (Run non-thinking for latency.)
- BRAIN+VOICE (one model): NO newer option. Qwen3-Omni-30B-A3B (Sept 2025) is STILL the newest Qwen that
  can talk with real-time streaming speech; no Qwen3.5-Omni / Qwen3.6-Omni has shipped. The 2026 audio
  releases (Qwen3-ASR) are speech-to-text only. Voices remain 3 fixed presets, no cloning.
- Net: cascade path improves (swap brain to Qwen3.6-35B-A3B + your own TTS); single-model omni path is
  unchanged from prior research (Qwen3-Omni remains current).
