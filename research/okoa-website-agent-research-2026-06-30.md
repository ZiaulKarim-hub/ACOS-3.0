# OKOA Capital — Public-Website AI Voice Agent: Technology Selection & Recommended Architecture

**One-line purpose:** A decision-ready evaluation of frameworks, models, voice stacks, and memory for an autonomous, voice-first AI agent embedded on OKOA Capital's public website — with a concrete recommended build, costs, and risks.

**Date:** 2026-06-30

> **Pricing & product-status caveat (read first).** Claude model pricing/capabilities are from the authoritative Anthropic catalog. **All non-Claude pricing, all benchmark numbers, and all product-status claims** (e.g. "PlayHT shut down," "OpenAI AgentKit Builder wound down," "Retell SOC 2 on standard plans," GA/launch dates) are from June-2026 third-party aggregators and vendor pages — they are **volatile and must be re-verified before contracting.** Items that are load-bearing but unconfirmed are tagged **[verify]** throughout.

---

## 1. Executive Summary

**RECOMMENDATION (bottom line):** Build a **composable voice pipeline** — **LiveKit Agents** (open-source voice orchestration) → **Deepgram** speech-to-text → **Claude as the brain** (Haiku 4.5 by default, escalating to Sonnet 5 for any factual claim about the firm/funds/terms) → **ElevenLabs or Cartesia** text-to-speech → **Cloudflare Durable Objects** for per-visitor durable memory, hosted on **Cloudflare**. Do **not** adopt Flue as the spine: it is a weeks-old beta and its voice support is unproven.

This stack wins on the three things that matter most for OKOA. **Brand/compliance safety:** a text checkpoint at the Claude layer lets you ground, filter, and refuse before any audio is spoken — critical because a confidently-wrong answer about a fund's returns or terms to an institutional/HNW visitor is a **securities-marketing risk** (SEC Marketing Rule + Reg D accreditation/general-solicitation exposure), not merely a UX glitch. **Cost control:** voice I/O is 80–95% of the bill, so running a web/WebRTC pipeline with a cheap-Claude default + prompt caching keeps cost to roughly **$0.24–0.32 per 4-minute session** and avoids frontier API sticker shock — priced at **real API rates**, not on any consumer-plan loophole. **Durable cross-session memory:** Cloudflare Durable Objects persist per-visitor state across restarts by design.

The single most important architectural fact: **Claude has no native speech.** Choosing "the brain" and "the voice stack" are two separate decisions. Native speech-to-speech models (OpenAI Realtime, Gemini Live) **cannot run Claude** and give you far less control over what gets said — the wrong trade for a regulated lender. Note also that "native = faster" is only half-true: real-world data puts OpenAI Realtime at a **median 2.2s round-trip (4–6s in long sessions)**, *slower* than the Claude pipeline's ~700ms–1.2s; only Gemini Live is reliably sub-1s.

A single **cheaper alternative** — Gemini Live, single-vendor speech-to-speech — is documented in §12. Once native-audio output is priced correctly it is **roughly cost-comparable to the recommended pipeline, not a dramatic "floor,"** and it sacrifices the brand-safety checkpoint; it is a budget/simplicity option, not the institutional-grade default.

---

## 2. Requirements Recap

OKOA Capital (a private-equity real-estate lender) wants an agent on its **public marketing website** that satisfies five needs:

1. **Answer visitor questions** about the firm, its funds, and its lending — accurately, for an institutional / high-net-worth audience.
2. **Fill out forms autonomously** on a visitor's behalf (contact / inquiry / intake forms).
3. **Remember returning users across sessions** and resume where they left off (persistent cross-session memory).
4. **Handle voice — TOP PRIORITY.** Must be excellent at speech recognition and understanding spoken input, then respond and act on it. Voice is explicitly the highest-weighted requirement.
5. Be **autonomous, durable** (survive restarts and resume work), **sandboxed**, and **cost-efficient** — OKOA finds frontier-model API pricing too expensive.

**Overriding constraint:** Audience is institutional and HNW. Accuracy and brand safety are first-order — a confidently wrong answer about a fund, terms, or returns is a **regulatory (securities-marketing) and reputational** risk, not just a UX glitch.

---

## 3. Key Architectural Finding: Claude Has No Native Speech I/O

**Claude is a text-and-vision model only. It cannot hear audio or speak audio.** Even Anthropic's own "Claude Voice Mode" is itself a pipeline — it transcribes speech to text, runs Claude on the text, then synthesizes the reply with a third-party voice engine (Anthropic names ElevenLabs as a TTS subcontractor). Audio never enters or leaves the Claude model directly.

**What this means — the brain and the voice are two separate purchases:**

- **The "brain"** is the reasoning/tool-calling model that decides what to say and which forms to fill. Candidates: Claude, GPT, Gemini, or a cheap open model.
- **The "voice layer"** is a *separate* set of components: speech-to-text (STT/ASR) and text-to-speech (TTS). Candidates: Deepgram, ElevenLabs, Cartesia, AssemblyAI, etc.

There are three ways to assemble this:

- **(A) Native speech-to-speech** (OpenAI Realtime, Gemini Live): one model ingests audio and emits audio end-to-end. Most natural prosody — **but there is no seam to insert Claude as the brain**, and you get far less control over the exact words spoken.
- **(B) Pipeline** (STT → text brain → TTS): the *only* way to use Claude as the brain. Adds STT+TTS hops, but gives you a text checkpoint to ground/filter/refuse before audio is spoken, swap models per turn for cost, and run tool-calling for form-fills.
- **(C) Platform** (Vapi, Retell): a managed pipeline — same shape as B, less wiring, higher per-minute markup and more lock-in.

**On latency (corrected):** the common claim that native S2S is "lowest latency" holds only for **Gemini Live** (sub-1s). **OpenAI Realtime** measures a **median 2.2s round-trip in real-world data (4–6s in long sessions)** — *slower* than a well-built Claude pipeline at ~700ms–1.2s. So choosing Claude over OpenAI Realtime is **not** a latency penalty; choosing Claude over Gemini Live costs roughly ~300–500ms. State this honestly rather than as a blanket "native is faster."

**Consequence for OKOA:** Because brand safety and cost control dominate, OKOA should treat voice as a pipeline (B) with Claude as the swappable, controllable brain — not a native black-box (A). The voice transport layer (LiveKit/Pipecat) is essentially free and open-source; the real cost driver is the per-minute voice I/O, not the brain model.

---

## 4. Agent-Framework Comparison

The ten options are **not peers** — they split into a *voice transport layer* (LiveKit, Pipecat, Cloudflare voice), a *durable brain layer* (the rest), and the *model* itself. Voice being top priority means the transport layer is almost certainly LiveKit or Pipecat regardless of brain.

**Axis mapping (corrected so Speed ≠ maturity):**
- **Price** = Cost model column.
- **Speed** = real runtime latency / dev-to-ship speed (Dev effort), **not** maturity.
- **Performance** = Autonomous / Durable / Memory / Sandbox / Voice columns.
- **Risk** = Maturity/stability + Lock-in (these are risk, not speed).

| Option | Autonomous | Durable / Resume | Memory | Sandbox | Voice support | Deploy targets | Maturity *(risk)* | Lock-in *(risk)* | Dev effort *(speed-to-ship)* | Cost model *(price)* |
|---|---|---|---|---|---|---|---|---|---|---|
| **Flue** (withastro/flue) | Yes (native) | Strong — Durable Streams ledger, auto-resume | Session/ID persistence; cross-session "returning user" = DIY | Yes — just-bash / local / remote | **NOT native** — only via Cloudflare `@cloudflare/voice` (experimental); Flue↔voice integration **unverified** | Node (single-node now), Cloudflare Workers (best), VMs | **High risk** — June-2026 beta, breaking changes expected, thin docs **[verify status]** | Low framework / Med-High in practice (voice+cheap models lean Cloudflare) | Medium | Free (Apache-2.0) + model tokens + CF hosting |
| **Anthropic Managed Agents (CMA)** | Yes | Strong — server-side sessions, clean resume, "dreaming" | **Yes, native** — persistent filesystem memory, per-user stores, redact/audit | Yes — Anthropic-hosted sandbox/REPL | **None native** — bolt on STT/TTS or front with LiveKit/Pipecat | Fully hosted by Anthropic | New (GA Apr 2026 **[verify date]**), evolving | **High** (Anthropic cloud + Claude) | **Low** | Anthropic token pricing + $0.08/session-hr **[verify]** (frontier-priced — collides with cost goal) |
| **Claude Agent SDK** | Yes | Strong — auto-compaction, session resume | Filesystem/context memory; you wire persistence | Yes — built-in | **None native**; documented STT→SDK→TTS pattern | Self-host, any infra | Mature (ex-Claude Code SDK) | Medium (Claude-shaped) | Medium | Claude API token pricing. *(A consumer/Max-plan path technically exists but is almost certainly outside that plan's terms for a commercial, public, always-on service — see §5 note. Do not budget on it.)* |
| **OpenAI Agents SDK** | Yes | Strong — durable fibers, checkpointing | **Yes** — built-in Sessions (hosted Conversations API) | Hosted code-interpreter sandbox | **Best native voice** — Realtime Agents, true speech-to-speech | Self-host or OpenAI platform | Mature SDK (but AgentKit *Builder/Evals* reportedly winding down Nov 2026 **[verify]** — use the SDK, not Builder) | High (OpenAI cloud) | Low–Medium | OpenAI token + realtime audio pricing (premium) |
| **LangGraph** | Yes | **Strong, granular** — per-super-step checkpointer, time-travel, HITL (≠ full external durable execution) | **Yes** — thread state + store (Postgres/DynamoDB/SQLite) | No native sandbox — you isolate tools | **None native** — pair with LiveKit/Pipecat | Self-host; LangGraph Platform optional | Mature, enterprise-heavy | Low–Med (OSS, model-agnostic) | **High** — most wiring | OSS free + infra + model |
| **Vercel AI SDK** | Yes (`DurableAgent`) | Tools retryable/resumable; deeper via Temporal/vercel-workflow | Lightweight; you persist | No native sandbox | **Transcription + TTS providers** (pipeline-level, not real-time RTC) | Self-host / Vercel | Mature for TS; agent/voice newer | Low (OSS, TS) | Medium | OSS free + infra + model (watch Vercel egress) |
| **CrewAI** | Yes | Runtime checkpointing + Flows (not full durable exec) | **Yes, rich** — short/long/entity memory; SQLite→Postgres/pgvector | No native sandbox | **None native** — documented LiveKit/Pipecat/ElevenLabs integrations | Self-host; Enterprise option | Mature, popular | Low–Med (OSS) | Medium | OSS free; Enterprise paid; + model |
| **Cloudflare Agents SDK (DO/Workflows)** | Yes | **Excellent** — Durable Objects + Workflows survive restart/deploy/eviction | **Yes** — per-agent SQLite (Facets); state persists by design | Edge isolates + DO sandboxing | **Experimental** `@cloudflare/voice` — STT+TTS over WebSocket in ~30 lines | Cloudflare edge (global, low-latency) | DO/Workflows mature; Agents SDK + voice newer/**experimental** | Med–High (CF platform) | **Very cost-efficient** — edge pricing, zero egress | Medium |
| **Pipecat** | Orchestrator | Pipeline-level; resume relies on your state store | No built-in long-term (add vector store) | No (orchestrator only) | **Excellent, voice-native** — Python STT→LLM→TTS, 60+ swappable services, v1.0 Apr 2026 **[verify]** (~800–950ms) | Self-host (any transport) | Mature for voice, v1.0 | **Lowest** (OSS, provider-agnostic) | Medium (plumbing yours) | OSS free + providers + infra |
| **LiveKit Agents** | Orchestrator | Session-level; durability via your backend (pairs with durable brain) | No built-in long-term (add store) | No (media + agent infra) | **Best-in-class real-time voice** — WebRTC, ~750–900ms, telephony, barge-in, first-class Anthropic plugin | Self-host (Apache-2.0, ~$10–20/mo) or LiveKit Cloud | Mature, production-grade | Low self-host / Med Cloud | Medium | **OSS free self-host**; Cloud tiers $0/$50/$500; ~$0.01/agent-min |

**Read-out:** Voice-as-top-priority eliminates the pure-brain frameworks as standalone answers. The strongest voice front-end is **LiveKit Agents** (lowest latency, WebRTC, telephony-ready, first-class Claude plugin, free to self-host), with **Pipecat** the close Python alternative. The durable brain pairs best with the **Claude Agent SDK on metered API pricing** (Claude-grade accuracy, controllable cost via the cheap-default router) plus **Cloudflare Durable Objects** for memory. Flue is portable but beta + voice-unproven — exactly why OKOA should look past it.

---

## 5. Brain-Model Comparison

Standard tier, USD per 1M tokens. **Claude figures are authoritative (Anthropic catalog); all others are June-2026 third-party aggregators — treat as approximate / verify before contracting.** Axes: **Price** (in/out), **Speed** (latency/throughput), **Performance** (reasoning + tool/function-calling), **Risk**.

> **Benchmark note (corrected):** an earlier draft cited specific "BFCL ~41.3 / ~41.5" tool-calling scores and concluded Gemini 3 Flash is the single best tool-caller, beating Opus, Gemini 3 Pro, and GPT-5.5. Those numbers look like a different or mislabeled metric (frontier models score far higher than 41 on BFCL accuracy), and a *Flash*-class model topping every frontier model is implausible. **The specific numbers are dropped.** Tool-calling quality below is stated qualitatively and should be re-verified against a current, version-pinned leaderboard before it drives a vendor choice.

| Model | Price (in / out per 1M) | Speed (latency / throughput) | Performance (reasoning + tool-calling) | Context | Risk | Notes |
|---|---|---|---|---|---|---|
| **Claude Opus 4.8** | **$5 / $25 [verify — historically $15/$75; this is either a real cut or an error, confirm before relying on "escalate to Opus" math]** | High latency (reasoning) | Excellent; top-tier tool-calling | 1M | Low (strongest refuse-to-fabricate) | Best brand-safety; cache read ~0.1×, batch −50% |
| **Claude Sonnet 5** | $3 / $15 ($2 / $10 intro→Aug 31) | Medium | Excellent (near-Opus) | 1M | Low | **Accuracy-critical workhorse**; best Claude value |
| **Claude Haiku 4.5** | $1 / $5 | **<600ms (fastest tier)** | Good; weaker on hard multi-step tool chains | 200K | Low-Med | Cheap, fast — good default router brain |
| **Gemini 3 Pro** | $2 / $12 | Medium | Excellent | 1M+ | Med (data-residency/vendor) | High capability, cheaper than Opus |
| **Gemini 3 Flash** | $0.50 / $3 | **<600ms** | **Excellent tool-caller at near-cheapest price** (specific rank unverified) | 1M+ | Med | Best value brain; context caching, batch −50% |
| **GPT-5.5** | $5 / $30 | High | Excellent | ~400K | Med | Top quality, priciest output; cached in $0.50 |
| **GPT-5.4** | $2.50 / $15 | Medium | Excellent | ~400K | Med | Half the price of 5.5; cached $0.25 |
| **GPT-5.4 mini** | $0.75 / $4.50 | Fast | Good | ~400K | Med | Mid-tier cost |
| **GPT-5.4 nano** | $0.20 / $1.25 | Fastest OpenAI | Fair — thin for autonomous tools | ~400K | Med-High | Cheapest GPT; too thin for compliance tool-chains |
| **DeepSeek V3 / V4-Flash** | $0.14 / $0.28 | Medium | Good (improving) | 128K | **High** (data-residency / brand for institutional) | Rock-bottom price; fine internal, not customer-facing voice |
| **Llama 4 Scout (Groq)** | $0.11 / $0.34 | **Very fast (Groq)** | Fair–Good | long | Med-High (open-weight, you host safety) | Cheap + fast |
| **Qwen3 32B (Groq)** | $0.29 / $0.59 | Very fast | Good tool-caller | long | Med-High | Strong open-weight |
| **Llama 3.3 70B (Together/Groq)** | $0.59–0.88 / $0.79–0.88 | Fast | Good | 128K | Med-High | Mature open-weight baseline |
| **GPT-OSS 20B (Together)** | $0.05 / $0.20 | Fast | Fair — light tasks only | long | High | Floor pricing; not for reliable tool chains |
| **Cloudflare Workers AI — open models** | **Neuron-based, not per-token; quoted per-token figures in earlier drafts (~$2.50/$10 for 8B, ~$15/$40 for 72B) appear badly inflated and are withdrawn pending re-verification [verify against Workers AI neuron pricing]** | Edge (low) | Fair–Good (model-dependent) | varies | Med | Edge deploy, no API keys, generous free tier; **the "expensive at edge" conclusion is NOT reliable** and may reverse — re-price before excluding |

**Verdict:** The accuracy/cost sweet spot is a **two-tier router**: a cheap fast model for navigation/intent/form-filling/chit-chat, escalating to Claude for any answer that asserts a fact about OKOA. **For OKOA's compliance profile we weight brand safety highest → default to a Claude two-tier (Haiku 4.5 default → Sonnet 5 escalation),** because keeping the brain in one vendor (Claude) maximizes refuse-to-fabricate brand safety. **Gemini 3 Flash is a legitimate cheaper default brain** (frontier-grade, very cheap, strong tool-calling) if single-vendor Claude isn't required — but the "single best tool-caller" claim should not by itself decide this. Re-price **Cloudflare Workers AI** before excluding it (its earlier per-token figures were likely wrong); avoid pure open/DeepSeek as the *customer-facing* voice on brand/data-residency grounds.

> **⚠️ Consumer/Max-subscription "brain" — do NOT budget on it.** Earlier drafts treated running the Claude brain on a personal **$200/mo Max subscription** via the Agent SDK as a near-zero-token-cost win. **For this use case that is almost certainly a terms-of-service violation:** consumer/Max plans are for individual interactive use, not for powering a commercial, public-facing, always-on production service. **The recommended economics in this document are priced at real metered API rates and do not depend on the Max path.** If OKOA ever wants to explore a plan-based path, it requires written confirmation from Anthropic first; treat it as out-of-scope for production budgeting.

---

## 6. Voice-Stack Comparison (MOST IMPORTANT)

All-in pricing is **web/WebRTC** (no telephony — OKOA is web-embedded, which removes the biggest cost line). Axes: **Price** ($/min), **Speed** (latency), **Performance** (quality, STT accuracy, languages, barge-in), **Risk**. Model name standardized to **`gpt-realtime`** (OpenAI's realtime family).

| Option | Type | Price ($/min, web all-in) | Speed (latency) | Performance (quality / STT / languages / barge-in) | Claude as brain? | Risk |
|---|---|---|---|---|---|---|
| **OpenAI Realtime (`gpt-realtime`)** | Native (A) | $0.18–0.46; **$0.05–0.10 cached**; mini $0.06–0.15 | TTFB ~500ms; **median round-trip 2.2s, 4–6s long sessions** | Excellent prosody; good built-in STT; multilingual; native barge-in (server VAD) | **No** | Premium price; vendor lock (brain+voice+ASR fused); least output control; **slower real-world round-trip than the pipeline** |
| **Google Gemini Live** | Native (A) | **~$0.06–0.12 all-in [verify]** (native-audio *output* tokens are the cost driver — the earlier ~$0.02–0.05 floor was too low) | **Sub-1s** | Very good, expressive; built-in STT; strong multilingual; native barge-in | **No** | **Genuinely sub-1s**, but single-Google-vendor and least brand/output control — compliance concern; **not a dramatic cost floor once audio-out is priced** |
| **Pipeline: Deepgram + Claude + ElevenLabs/Cartesia** | Pipeline (B) | **~$0.08–0.20** (STT ~$0.005–0.008 + TTS ~$0.05–0.10 + Claude tokens) | **~700ms–1.2s** round-trip; TTS TTFA 40–75ms | Excellent TTS; **best-in-class STT** (Deepgram Nova-3 WER ~5.3%, Flux lowest end-of-speech latency); 90+ langs; framework barge-in | **Yes** | More subprocessors to govern; you own orchestration (also lowest lock-in) |
| **Cartesia (Sonic TTS)** | Pipeline component (B) | TTS ~$0.05/1k chars; **~40ms TTFA** (latency/cost leader) | ~40ms first audio | Natural; pair with any STT + Claude | **Yes** (as TTS in a Claude pipeline) | Single-component vendor; newer brand |
| **Vapi** | Platform (C) | $0.05/min orchestration + providers → **$0.12–0.35 all-in** | Sub-1s (depends on stack) | Depends on chosen STT/TTS; built-in barge-in | **Yes** (select Anthropic LLM) | Orchestration markup; lock-in; least control |
| **Retell AI** | Platform (C) | $0.07/min + providers → **$0.13–0.31 all-in** | **~620ms out-of-box** | Configurable STT/TTS; multilingual; built-in barge-in; compliance certifications advertised **[verify SOC 2 / plan scope]** | **Yes** (Anthropic supported) | Orchestration markup; lock-in |
| **LiveKit Agents** | Framework, OSS (B/C) | Providers + infra only → **~$0.08–0.20** | ~700ms–1.2s; TTS 40–75ms | **Best available — your choice of STT/TTS**; built-in turn detection/barge-in | **Yes** (first-class Anthropic plugin) | Lowest markup/lock-in; you assemble (Medium dev effort) |
| **Pipecat** | Framework, OSS (B/C) | Providers only → **~$0.08–0.20** | ~700ms–1.2s | Your choice STT/TTS; built-in barge-in | **Yes** (built-in Anthropic support) | Lowest lock-in; voice plumbing is yours |

**STT detail (the voice-recognition priority):** Deepgram **Nova-3** (~$0.0043 batch / $0.0077 streaming, WER ~5.3%) and **Flux** (purpose-built for voice agents, lowest end-of-speech latency, $0.0065/min) lead on latency. **AssemblyAI Universal-2** is cheapest at scale and best at alphanumerics — important for OKOA, where visitors speak emails, dollar amounts, and loan figures aloud. **TTS:** Cartesia Sonic (~40ms, cost/latency leader); ElevenLabs Flash v2.5 (~75ms, naturalness leader). **PlayHT is reportedly defunct (acquired by Meta 2025, shut down Dec 2025) [verify] — do not design around it.**

**Read-out:** For OKOA — needing Claude as brain, cross-session memory, web embedding, and brand safety — the fit is a **pipeline orchestrated by LiveKit Agents (or Pipecat): Deepgram Flux/Nova-3 → Claude → Cartesia/ElevenLabs.** Trade-off stated precisely: choosing Claude over **Gemini Live** costs ~300–500ms; choosing Claude over **OpenAI Realtime** actually *gains* you latency (the pipeline is faster than Realtime's real-world 2.2s). For a compliance-sensitive lender, controllability + accuracy + cost outweigh the small Gemini-Live latency gap.

---

## 7. Memory / Persistence Comparison

"Memory" is two problems: **(1) identity** (knowing this is the same human — you must own this; no vendor gives it to you for anonymous traffic) and **(2) the keyed store** (below). Axes — now including **Speed** (recall latency) and **Performance** (recall accuracy) so all four axes are present:

> **Identity is the weak link — stated plainly (see §11).** Recognition rests on a first-party **device token** (cookie / localStorage). For anonymous public-website visitors this **fails across devices, in incognito, and on cookie-clear** — so "remembers returning users across sessions" reliably works only **same-device, and best after the visitor has identified themselves via a form**. It also raises a **consent question**: silently fingerprinting anonymous institutional visitors is a privacy/consent posture decision, not a default. Treat cross-device/durable recognition as available only post-identification (email/phone captured with consent).

| Option | What it stores | Persistence | Speed (recall latency) | Performance (recall accuracy) | Price (rough) | Complexity | Privacy / PII | Returning-user fit |
|---|---|---|---|---|---|---|---|---|
| **Anthropic Memory tool** (client-side) | Files the model writes; you host the bytes | Yes — via *your* backend | Backend-dependent | Model-curated; you control | Tokens only; storage = your infra | Medium | Full control (your infra) | Good — bolt onto your own identity key |
| **Anthropic Memory Stores** (managed) | Text-doc memories, mounted to sandbox; immutable versions | Yes — native; "one store per user" | Low (mounted to sandbox) | Strong (versioned docs) | $0.08/session-hr + tokens **[verify]** | Low (managed) | Strong — versioning + **redact** endpoint, 30-day audit | Excellent fit, but frontier-token cost collides with cost goal |
| **mem0** | Auto-extracted user facts (+ graph on paid) | Yes — keyed by `user_id` | Low | Recall ~49% LongMemEval **[verify]** | Free 1k/mo → $19/mo → $249 graph; OSS self-host | Low-Med | Managed (DPA) or self-host | Low-friction "remember the user" |
| **Letta / MemGPT** | Working + archival memory, agent-managed | Yes — agent is durable state | Med (agent round-trips) | Agent-curated | Free OSS (infra + model) | **High** | Self-host = full control | Over-engineered for a web Q&A/form bot |
| **Zep (Graphiti)** | Temporal knowledge graph + episodes | Yes — per user/session, time-aware | Low–Med | **Best accuracy (63.8% LongMemEval) [verify]** | Free → $25/mo Flex; self-host | Medium | Managed or self-host; temporal audit | Ideal when LP status evolves over months |
| **pgvector (Postgres)** | Embeddings in Postgres | Yes (it's a DB) | Low (indexed) | DIY recall quality | ~$20–300/mo on RDS | High (DIY recall) | Full control, inside your Postgres | Backing store only — you build logic; data-sovereign |
| **Pinecone** | Embeddings (managed) | Yes | 50–100ms | Managed ANN | ~$70/mo → $700–5,000+ at scale | High (DIY recall) | Vendor cloud (DPA) | Overkill at OKOA's modest scale |
| **Cloudflare Durable Objects / Agents** | Per-instance SQLite: history + context-memory blocks | **Yes — survives restart/deploy/eviction automatically** | **Very low (edge, co-located)** | Exact-key + your recall logic | Very low; **free when idle** | Medium | Your data on CF edge | **Strongest for durable + sandboxed + resume + cheap + model-agnostic** |
| **Redis (Upstash)** | Session state, recent-turn buffer, vectors | Yes if persistence configured (else ephemeral) | **Sub-ms / 5–15ms (fastest)** | Buffer + vector recall | $0.20/100k cmds; ~$10/mo | Low-Med | Your infra | Hot session / "resume pointer" layer, not system-of-record |

**Read-out (layered design):** **Cloudflare Durable Objects** — one DO per visitor identity — directly answers the durable/sandboxed/resume/cheap/model-agnostic spec. Add **mem0** (fast) or **Zep** (time-aware LP-status tracking) on **self-hosted pgvector** for long-term facts; **Redis/Upstash** as the hot "resume where left off" pointer. Attach firm/fund knowledge as **read-only** memory to block prompt-injection poisoning. If staying all-Anthropic, **Memory Stores** gives per-user memory + PII redact/audit at the cost of session-hour + token pricing.

---

## 8. Autonomous Form-Filling

Two architectures: **(A) function-calling → your own intake API** (the model emits a typed JSON object; your backend writes it — the "form" is just a schema) vs **(B) browser automation → the live DOM** (the agent drives a real browser). Axes: **Price**, **Speed/reliability (Performance)**, **Risk**.

| Dimension (axis) | (A) Function-calling → your form API | (B) Browser automation → live DOM |
|---|---|---|
| **Best fit** | Forms **you own/host** (OKOA's case) | Forms on **3rd-party sites you don't control** |
| **Performance / reliability** | Schema-valid by construction; truth still needs a validation layer | DOM-driven ~92% (Playwright+Claude), vision ~75–78%; **validation-event breakage** ("looks filled, didn't submit") |
| **PII/financial hallucination** | Shape guaranteed, **values not** — echo-back + validate | Same model-extraction risk **plus** mis-typed/mis-targeted fields |
| **Price (cost)** | Cheapest (single structured call; no browser) | $0.02–0.10 DOM, $0.20–0.50 vision per task |
| **Speed / durability** | Low latency, easy to checkpoint/resume | Heavier; browser session must survive restarts |
| **Risk: auditability** | Native: structured object + per-field provenance | Harder — reconstruct from page state/screenshots |
| **Risk: prompt-injection blast radius** | Smaller (no general computer control) | Larger (a browser is a powerful tool) |
| **Voice-first compatibility** | Excellent — voice → intent → schema is one clean hop | Indirect — extra DOM-translation layer |

**PII / financial-risk note:** The danger is **not** malformed JSON — it's the model **confidently inventing or altering** a name, email, phone, entity, ticket size, or accreditation status. Both architectures share this because both depend on the same LLM extraction step. Even the best browser stack tops out near **92% — roughly 1 in 12 submissions mis-fills** without a verification layer, which is unacceptable for institutional lead capture left unattended.

**Recommended safe pattern (use A as primary; B only for external sites; never auto-submit OKOA's own forms without confirmation):**

1. **Conversational capture** (voice or text); answer Q&A only from a citation-grounded retrieval corpus; escalate to "I'll connect you with the team" rather than improvise on anything material.
2. **Schema-constrained extraction** into a typed `IntakeForm` object — **only transcribe values the visitor explicitly stated**, attaching the source utterance per field. No inferred PII/financials.
3. **Deterministic validation gate** (type/format/enum/bounds + PII detection/masking) **before** any write; failures route back to the visitor as field-level prompts, never silent auto-retry.
4. **Visitor-as-human-in-the-loop:** render the assembled form back for one-tap **Confirm / Edit** before submit. This is the load-bearing control — the visitor verifies their own data, supplying the human authorization compliance frameworks require, at zero OKOA staffing cost.
5. **Submit via your own validated API** (not DOM injection); verify the written record.
6. **Tamper-evident audit log:** transcript + proposed object + per-field provenance + confirmation event + final record, immutable.
7. **Injection containment:** the submit tool is reachable **only** post-confirmation, never from model free-text.

---

## 9. End-to-End Recommended Architecture

**Stack:** LiveKit Agents (voice orchestration, self-hosted) · Deepgram STT · Claude brain (Haiku 4.5 default → Sonnet 5 escalation) · ElevenLabs/Cartesia TTS · Cloudflare Durable Objects + pgvector/Redis memory · Cloudflare hosting.

```
  Visitor browser (WebRTC mic + chat)
            │  16kHz audio
            ▼
  ┌─────────────────────────────────────────────┐
  │  LiveKit Agents  (voice transport + barge-in)│
  └───────┬───────────────────────────┬─────────┘
          │ audio                      ▲ audio
          ▼                            │
   Deepgram STT (Flux/Nova-3)   ElevenLabs / Cartesia TTS
          │ text                       ▲ text
          ▼                            │
  ┌─────────────────────────────────────────────┐
  │  CLAUDE BRAIN (text checkpoint)              │
  │  • Haiku 4.5 default (intent, nav, form)     │
  │  • Sonnet 5 escalation (any firm/fund claim) │
  │  • Retrieval-grounded answers w/ citations   │
  │  • Tool-calling → typed IntakeForm object    │
  └───────┬───────────────────────────┬─────────┘
          │ retrieval                  │ form submit (post-confirm only)
          ▼                            ▼
  RAG corpus (firm/fund/        Your validated Intake API → CRM
  lending, read-only memory)         │
          ▲                          ▼
  ┌─────────────────────────────────────────────┐
  │  MEMORY  (Cloudflare Durable Object / visitor)│
  │  • per-visitor durable state, survives restart│
  │  • mem0/Zep on pgvector = long-term facts     │
  │  • Redis = hot "resume where left off" pointer│
  │  • Identity: device token → email on 1st form │
  │    (same-device only; cross-device needs login)│
  └─────────────────────────────────────────────┘
   All hosted on Cloudflare (zero egress, free-when-idle)
```

**Rationale:**
- **Voice (top priority):** LiveKit gives best-in-class real-time WebRTC, native barge-in, ~700ms–1.2s round-trip (faster than OpenAI Realtime's real-world 2.2s; ~300–500ms behind Gemini Live), and the highest-quality STT (Deepgram leads alphanumeric accuracy — essential for spoken dollar amounts, fund names, emails).
- **Brand/compliance safety:** the Claude text checkpoint lets you ground, filter, and refuse before any audio is spoken — impossible with a native black-box. Sonnet 5 escalation on any factual claim leans on Claude's strongest property: refusing to fabricate. This is the control that keeps a public answer about fund returns inside the SEC Marketing Rule.
- **Cost-efficiency:** voice I/O is 80–95% of the bill; web/WebRTC removes telephony fees; Haiku default + prompt caching makes the brain a rounding error; Cloudflare = zero egress (audio is bandwidth-heavy). **Costs are modeled at real metered API rates — no consumer-plan dependency.**
- **Durable / sandboxed / resume:** Cloudflare Durable Objects persist per-visitor state across restarts/deploys/eviction by design and cost nothing when idle.
- **Lowest lock-in:** Deepgram, Claude, ElevenLabs/Cartesia are each independently swappable behind your own orchestration — the right posture for a regulated firm that wants exit optionality. Put a thin internal abstraction over each provider.

---

## 10. Cost Model

Modeling assumptions: a "session" = one visitor; **100% voice (worst case)**, 4-minute average, ~8 turns; web/WebRTC (no telephony); prompt caching on (cache reads ~0.1× input). Chat-only sessions cost ~5–10× less. Claude: Haiku 4.5 $1/$5, Sonnet 5 $3/$15 ($2/$10 intro). **All figures are budgeting estimates at real metered rates, not quotes, and do not assume any consumer-plan path.**

**Per-4-min-session voice cost (the dominant driver):**

| Architecture | Voice I/O $/min | Brain add | $/session |
|---|---|---|---|
| **A. Pipeline (Deepgram+ElevenLabs) + Haiku** *(recommended default)* | ~$0.05 | +$0.04 | **~$0.24** |
| A. Pipeline + Sonnet 5 (all answers) | ~$0.05 | +$0.12 | **~$0.32** |
| B1. OpenAI `gpt-realtime` (cached) | ~$0.10 incl. brain | — | **~$0.40** |
| B2. Gemini Live (cheaper alternative) | ~$0.06–0.12 incl. brain **[verify]** | — | **~$0.24–0.48** |
| C. Vapi / Retell platform | ~$0.15 incl. brain | — | **~$0.60** |

> **Correction vs. earlier draft:** Gemini Live was previously shown at ~$0.03/min / ~$0.12/session. Re-deriving from current native-audio *output* token pricing puts it at **~$0.06–0.12/min / ~$0.24–0.48/session** — **overlapping the recommended pipeline, not a dramatic floor.** Gemini Live's real advantages are single-vendor simplicity and sub-1s latency, **not** decisive cost savings. The tables below show it as a range.

**LOW — 500 sessions/mo (~2,000 voice min):**

| Line item | A·Haiku | A·Sonnet | B1·OpenAI | B2·Gemini | C·Platform |
|---|---|---|---|---|---|
| Voice + brain | $120 | $160 | $200 | $120–240 | $300 |
| Memory/storage | $30 | $30 | $30 | $30 | incl. |
| Hosting (Cloudflare) | $25 | $25 | $10 | $10 | $5 |
| **Total / mo** | **~$175** | **~$215** | **~$240** | **~$160–280** | **~$305** |

**MEDIUM — 5,000 sessions/mo (~20,000 voice min):**

| Line item | A·Haiku | A·Sonnet | B1·OpenAI | B2·Gemini | C·Platform |
|---|---|---|---|---|---|
| Voice + brain | $1,200 | $1,600 | $2,000 | $1,200–2,400 | $3,000 |
| Memory/storage | $75 | $75 | $75 | $75 | incl. |
| Hosting | $150 | $150 | $40 | $40 | $20 |
| **Total / mo** | **~$1,425** | **~$1,825** | **~$2,115** | **~$1,315–2,515** | **~$3,020** |

**HIGH — 50,000 sessions/mo (~200,000 voice min):**

| Line item | A·Haiku | A·Sonnet | B1·OpenAI | B2·Gemini | C·Platform |
|---|---|---|---|---|---|
| Voice + brain | $12,000 | $16,000 | $20,000 | $12,000–24,000 | $30,000 |
| Memory/storage | $400 | $400 | $400 | $400 | incl. |
| Hosting (+media servers) | $900 | $900 | $200 | $200 | $100 |
| **Total / mo** | **~$13,300** | **~$17,300** | **~$20,600** | **~$12,600–24,600** | **~$30,100*** |

*At High volume, platforms move to enterprise contracts (~$40k–70k/yr access alone) plus usage. **[verify]**

**Key takeaways:** (1) **Voice I/O is 80–95% of the bill at every tier** — optimizing the voice architecture matters ~10× more than the model. (2) **Gemini Live is no longer a clear cost floor** once audio-out is priced correctly — it overlaps the recommended **Pipeline+Haiku**, which remains the best balance of cost, control, and brand safety; **swap Haiku→Sonnet 5 for high-stakes answers at ~+$0.08/session** — trivial. (3) **Prompt caching is essential** (cuts brain cost 70–90%). (4) **Host on Cloudflare** (zero egress; Vercel's $0.15/GB egress is the classic blowout). (5) Platforms cost 2–5× more and lock you in — justified only for a fast Low-volume pilot.

---

## 11. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Confidently-wrong answer about a fund/terms/returns → SEC Marketing Rule + Reg D violation** (securities-marketing + reputational liability) | Medium | **Critical** | Retrieval-grounded, cited knowledge base; refuse out-of-scope; route any factual/performance claim to Sonnet 5/Opus; **never state returns/XIRR/fund terms from free recall**; "connect you with the team" fallback; standing disclaimer + human handoff; treat any public performance statement as advertising subject to the Marketing Rule |
| **General-solicitation / accreditation exposure** (agent invites investment or implies an offering to unverified visitors under Reg D 506(b)/(c)) | Medium | **High** | Agent must not solicit or imply an offering; gate any fund/investment discussion behind accreditation-aware disclaimers and human handoff; legal review of agent script; log every investment-adjacent exchange |
| **Hallucinated PII/financial values reaching CRM** | Medium | High | Only transcribe explicitly-stated values; deterministic validation gate; visitor Confirm/Edit before submit; per-field provenance audit log |
| **Prompt injection** (visitor coaxes off-brand statements or unauthorized form submits / data exfil) | Medium-High | High | Submit tool reachable only post-confirmation; minimize tool surface for untrusted input; read-only firm-knowledge memory; treat all tool inputs as untrusted |
| **Flue beta instability / unproven voice** (if adopted) | High (if used) | High | **Don't make Flue the spine**; use LiveKit/Pipecat + Claude; if Flue, spike `@cloudflare/voice` first |
| **Vendor lock-in** (platforms / native S2S fuse brain+voice+ASR) | Medium | Medium | Composable pipeline (A) — each component independently swappable; thin internal abstraction layer |
| **Data privacy / NPI + biometric (voiceprint) exposure** | Medium | High | Signed DPA + zero-retention/no-train terms from every vendor; **Anthropic's Fable-tier models require 30-day retention and are excluded from ZDR — use Haiku/Sonnet/Opus, which support ZDR**; voiceprint may be biometric under state law (BIPA/CCPA) → disclose recording + consent; transcribe-and-discard raw audio. (GLBA/consumer-privacy and SOC 2 are secondary hygiene, not the operative regime — the operative regime is securities marketing.) |
| **Cost runaway** (voice minutes scale linearly with traffic/abuse) | Medium | Medium | Cap session length; per-IP/session quotas; bot-protection on WebRTC endpoint; minute-spend alerts |
| **Latency too high for institutional UX** | Low-Med | Medium | Streaming + prompt caching; Deepgram Flux + Cartesia (~40ms TTS); pipeline already beats OpenAI Realtime real-world; ~300–500ms behind Gemini Live is acceptable |
| **Returning-user mis-recognition / cross-device gap** (device-token identity fails in incognito, cross-device, on cookie-clear) | Medium-High | Low-Med | Own the identity key: device token → promote to email/phone on first form (same-device); offer optional login/magic-link for true cross-device continuity; consent-gate any pre-identification tracking |
| **Vendor outage** (single-model native fails closed) | Low | Medium | Composable pipeline fails over per-component (swap TTS/STT) |

---

## 12. Final Recommendation & Phased Rollout

**RECOMMENDATION:** Build **Architecture A — the composable Claude pipeline on Cloudflare**: LiveKit Agents → Deepgram STT → Claude (Haiku 4.5 default, Sonnet 5 escalation for any firm/fund/lending claim) → ElevenLabs/Cartesia TTS → Cloudflare Durable Objects memory. It is mid-cost (~$0.24–0.32/session at real API rates), the lowest lock-in, the most contractually governable, and gives full control over brand voice and grounding — the right answer for an institutional/HNW audience where a confidently-wrong answer about a fund is a **securities-marketing** liability.

**Phased rollout:**

- **MVP (4–8 weeks):** Text + voice chat widget on the public site. LiveKit + Deepgram + Claude Haiku/Sonnet + ElevenLabs. Retrieval-grounded Q&A with citations over a curated firm/fund/lending corpus. Form-fill via function-calling into your intake API with **visitor Confirm/Edit before submit**. Memory via a single Cloudflare Durable Object per device token (anonymous, same-device), promoted to email on first form. Zero-retention vendor terms in place. Legal review of the agent script against the SEC Marketing Rule / Reg D before launch. Ship a Confirm-before-submit + cited-answers-only posture from day one. *(A fast Low-volume pilot could instead start on Vapi/Retell to validate UX before building, then migrate — accept the lock-in only at pilot scale.)*
- **v2 (next quarter):** Add cross-session long-term fact memory (mem0 or Zep on self-hosted pgvector) for returning-LP recognition and "resume where you left off," plus optional login/magic-link for true cross-device continuity. Add the two-tier router (cheap default → Claude escalation) and prompt caching for cost. Add tamper-evident audit logging, PII redaction/right-to-be-forgotten, per-IP quotas, and a human-handoff path. Re-price Cloudflare Workers AI as a candidate cheap router model (its earlier per-token figures were unreliable).

**CHEAPER ALTERNATIVE (one, clearly labeled):** If single-vendor simplicity and sub-1s latency matter more than brand-safety control, use **Gemini Live** (native speech-to-speech) as brain+voice. **Honest trade-offs:** once native-audio output is priced, it is **~$0.24–0.48/session — roughly cost-comparable to the recommended pipeline, NOT a dramatic floor**; you cannot use Claude as the brain; you get the least control over exactly what is said (weaker brand/compliance guardrails); there is no text checkpoint to refuse before audio; and brain+voice+ASR are locked to one vendor. For a lender where a confidently-wrong answer is a securities-marketing event, this is a real downgrade in brand safety — acceptable for a budget/simplicity-driven pilot, not the institutional-grade default.
*(Also-ran, one line: the **Cloudflare Agents SDK** with experimental `@cloudflare/voice` is the most cost-efficient single-platform option, at the price of voice maturity (experimental) and Cloudflare lock-in — keep it on the bench, not as the primary cheaper alternative.)*

---

## 13. Open Questions / Assumptions

- **Expected volume tier?** Cost ranges from ~$175/mo (Low) to ~$17k/mo (High) for the recommended stack — pilot vs. production architecture depends on this.
- **Voice share?** Tables assume 100% voice (worst case). If most sessions are chat, costs drop 5–10×.
- **Consumer/Max-subscription brain path is OUT for production** — almost certainly a ToS violation for a commercial, public, always-on service. The recommended economics are priced at real API rates and do not depend on it. Only revisit with written Anthropic confirmation.
- **Opus 4.8 at $5/$25** is below historical Opus pricing ($15/$75) — confirm it is a real cut, not an error, before any "escalate to Opus" cost math.
- **Gemini Live per-minute** must be re-derived from current native-audio-output token pricing before relying on the "cheaper alternative" number; the floor is higher than early aggregator estimates suggested.
- **Cloudflare Workers AI pricing** is neuron-based; earlier per-token figures were likely wrong — re-price before excluding it as a router model.
- **Tool-calling benchmark numbers** (BFCL, etc.) were dropped as unreliable — re-verify against a version-pinned leaderboard before letting a benchmark decide the default brain.
- **Product-status claims tagged [verify]:** PlayHT shutdown, OpenAI AgentKit Builder/Evals wind-down, Retell SOC 2 / plan scope, Anthropic Managed Agents GA date, Pipecat v1.0, Memory-Stores session-hour pricing.
- **Identity strategy** must be owned by OKOA (device token → email-on-form, same-device; login/magic-link for cross-device). No vendor solves recognition for anonymous public traffic, and silent fingerprinting needs a consent decision.
- **Non-Claude pricing is June-2026 third-party data** — re-verify before contracting. Claude figures are authoritative.
- **Compliance contracts:** DPA + zero-retention/no-training terms must be *contracted, not assumed*, from every vendor in the path (Anthropic, Deepgram, ElevenLabs/Cartesia, Cloudflare).
- **SEC/legal review** of the agent's answering script (Marketing Rule, Reg D solicitation) is a gating item before public launch.
- **Brand-voice / persona** for TTS (which ElevenLabs/Cartesia voice represents OKOA) is a separate design decision.
- **Latency tolerance:** is ~700ms–1.2s acceptable, or does OKOA want strict sub-1s (forcing Gemini Live and a non-Claude brain)? The recommendation assumes controllability beats the ~300–500ms gap vs. Gemini Live.

---

## 14. Sources (deduplicated)

> All Claude pricing/capabilities are from the authoritative Anthropic model catalog (loaded `claude-api` skill). **All non-Claude pricing, benchmark figures, and product-status claims below are June-2026 third-party aggregators and provider pages — volatile; re-verify before contracting.**

**Frameworks — Flue / Cloudflare:**
- https://github.com/withastro/flue · https://flueframework.com/ · https://flueframework.com/blog/flue-1-0-beta/
- https://blog.cloudflare.com/agents-platform-flue-sdk/ · https://blog.cloudflare.com/voice-agents/ · https://blog.cloudflare.com/introducing-agent-memory/
- https://developers.cloudflare.com/agents/ · https://developers.cloudflare.com/workflows/get-started/durable-agents/ · https://developers.cloudflare.com/durable-objects/ · https://developers.cloudflare.com/agents/concepts/conversation-state-and-memory/ · https://developers.cloudflare.com/workers/platform/pricing/ · https://developers.cloudflare.com/workers-ai/platform/pricing/
- https://betterstack.com/community/guides/ai/flue-framework/ · https://www.stork.ai/blog/astros-secret-ai-agent-framework · https://www.cloudflare.com/agents-week/updates/

**Frameworks — other brains:**
- https://platform.claude.com/docs/en/managed-agents/overview · https://platform.claude.com/docs/en/managed-agents/memory · https://claude.com/blog/claude-managed-agents-memory · https://www.anthropic.com/engineering/managed-agents
- https://code.claude.com/docs/en/agent-sdk/overview · https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan · https://code.claude.com/docs/en/voice-dictation
- https://openai.github.io/openai-agents-python/ · https://openai.github.io/openai-agents-python/sessions/ · https://openai.com/index/the-next-evolution-of-the-agents-sdk/ · https://openai.com/index/introducing-agentkit/
- https://docs.langchain.com/oss/python/langgraph/durable-execution · https://github.com/langchain-ai/langgraph · https://www.diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows
- https://vercel.com/blog/ai-sdk-6 · https://github.com/vercel/workflow · https://temporal.io/blog/building-durable-agents-with-temporal-and-ai-sdk-by-vercel
- https://docs.crewai.com/en/concepts/memory · https://crewai.com/blog/how-we-built-cognitive-memory-for-agentic-systems

**Voice stacks:**
- https://github.com/livekit/agents · https://docs.livekit.io/agents/models/llm/anthropic/ · https://livekit.com/pricing · https://docs.livekit.io/transport/self-hosting/
- https://github.com/pipecat-ai/pipecat · https://webrtc.ventures/2026/03/choosing-a-voice-ai-agent-production-framework/ · https://www.channel.tel/blog/pipecat-vs-livekit-voice-framework-decision
- https://openai.com/index/introducing-gpt-realtime/ · https://developers.openai.com/api/docs/guides/latency-optimization · https://hackernoon.com/openai-realtime-api-pricing-in-2026-real-world-data-from-4000-measured-sessions · https://callsphere.ai/blog/vw2c-openai-realtime-cost-per-minute-math-2026 · https://tokenmix.ai/blog/openai-realtime-voice-api-2026-cost-latency · https://www.eesel.ai/blog/gpt-realtime-mini-pricing
- https://ai.google.dev/gemini-api/docs/pricing · https://ai.google.dev/gemini-api/docs/live-api/capabilities · https://the-rogue-marketing.github.io/google-gemini-tts-speech-audio-api-pricing-may-2026/
- https://deepgram.com/pricing · https://deepgram.com/learn/best-speech-to-text-apis-2026 · https://www.coval.ai/blog/best-speech-to-text-providers-in-2026-independent-benchmarks-and-how-to-choose/ · https://www.coval.ai/blog/best-text-to-speech-providers-in-2026-how-to-choose-(and-why-vendor-benchmarks-lie)/ · https://futureagi.com/blog/speech-to-text-apis-in-2026-benchmarks-pricing-developer-s-decision-guide/ · https://www.buildmvpfast.com/api-costs/transcription
- https://elevenlabs.io/pricing · https://www.cekura.ai/blogs/elevenlabs-pricing · https://sureprompts.com/blog/voice-generation-models-compared-2026
- https://vapi.ai/pricing · https://www.retellai.com/pricing · https://www.cekura.ai/blogs/retell-ai-pricing-per-minute · https://superdupr.com/blog/vapi-vs-bland-vs-retell · https://klariqo.com/blog/voice-ai-cost-per-minute/ · https://www.famulor.io/blog/ai-voice-agent-pricing-2026-what-10-platforms-actually-cost-per-minute
- https://weesperneonflow.ai/en/blog/2026-02-23-claude-ai-voice-mode-2026-features-vs-dedicated-dictation/ · https://techcrunch.com/2026/03/03/claude-code-rolls-out-a-voice-mode-capability/

**Brain-model pricing/benchmarks:**
- https://developers.openai.com/api/docs/pricing · https://devtk.ai/en/blog/openai-api-pricing-guide-2026/ · https://www.morphllm.com/openai-api-pricing
- https://www.aifreeapi.com/en/posts/gemini-api-pricing-2026 · https://pricepertoken.com/pricing-page/model/google-gemini-3-flash-preview
- https://api-docs.deepseek.com/quick_start/pricing · https://www.cloudzero.com/blog/deepseek-pricing/ · https://groq.com/pricing · https://www.aipricing.guru/together-pricing/ · https://markaicode.com/pricing/cloudflare-workers-cost-analysis/
- https://llm-stats.com/leaderboards/best-ai-for-tool-calling · https://www.llmreference.com/benchmarks · https://benchlm.ai/llm-speed · https://aimultiple.com/llm-latency-benchmark · https://www.assemblyai.com/blog/best-speech-to-speech-voice-agent-api

**Memory / persistence:**
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool · https://claudeapi.com/en/blog/dev-guides/claude-memory-tool-guide/ · https://www.edtechinnovationhub.com/news/anthropic-brings-persistent-memory-to-claude-managed-agents-in-public-beta
- https://mem0.ai/pricing · https://particula.tech/blog/agent-memory-frameworks-tested-mem0-zep-letta-cognee-2026 · https://dev.to/anajuliabit/mem0-vs-zep-vs-langmem-vs-memoclaw-ai-agent-memory-comparison-2026-1l1k · https://vectorize.io/articles/mem0-vs-zep
- https://leanopstech.com/blog/vector-database-cost-comparison-2026/ · https://www.groovyweb.co/blog/vector-database-comparison-2026 · https://encore.dev/articles/pgvector-vs-pinecone · https://ranksquire.com/2026/03/04/vector-database-pricing-comparison-2026/ · https://upstash.com/pricing/redis · https://redis.io/blog/top-pinecone-alternatives-for-vector-search/

**Form-filling / compliance / security:**
- https://www.digitalapplied.com/blog/browser-automation-ai-agents-playwright-stagehand-2026 · https://www.nxcode.io/resources/news/stagehand-vs-browser-use-vs-playwright-ai-browser-automation-2026
- https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms · https://blog.newtum.com/llm-function-calling-structured-outputs/ · https://machinelearningmastery.com/5-practical-techniques-to-detect-and-mitigate-llm-hallucinations-beyond-prompt-engineering/
- https://galileo.ai/blog/human-in-the-loop-agent-oversight · https://www.kiteworks.com/regulatory-compliance/human-in-the-loop-ai-compliance/ · https://www.blockchain-council.org/agentic-ai/human-in-the-loop-agentic-ai-keep-humans-in-control/
- https://aisera.com/blog/agentic-ai-compliance/ · https://predictionguard.com/blog/ai-agent-deployment-in-financial-services-compliance-data-residency-and-regulatory-requirements · https://www.usefini.com/guides/ai-agents-autonomous-billing-actions-pci-compliant
- https://www.evidentlyai.com/llm-guide/prompt-injection-llm · https://www.wiz.io/academy/ai-security/prompt-injection-attack · https://arxiv.org/pdf/2506.08837 · https://air-governance-framework.finos.org/risks/ri-10_prompt-injection.html
- SEC marketing/solicitation context (verify against current rules): SEC Marketing Rule 206(4)-1; Regulation D Rules 506(b)/506(c) accredited-investor & general-solicitation provisions.

**Hosting / cost-at-scale:**
- https://www.vantage.sh/blog/cloudflare-workers-vs-aws-lambda-cost · https://www.morphllm.com/comparisons/cloudflare-workers-vs-vercel · https://www.retellai.com/blog/ai-voice-agent-pricing-full-cost-breakdown-platform-comparison-roi-analysis · https://www.yesworkflow.com/blog/ai-voice-agent-cost
