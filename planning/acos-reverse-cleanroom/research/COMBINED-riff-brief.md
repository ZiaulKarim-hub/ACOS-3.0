# /acos-reverse-cleanroom — Combined Riff Brief

**Date:** 2026-07-21
**Inputs:** handoff archaeology + `/acos-deep-research` (6 agents) + `/acos-swarm-research` (10 agents)
**Status:** research complete; skill NOT yet built. This is the riff substrate.
**Companions:** `research/deep-research-report.md` · `.acos/swarm/swarm-20260721-231940/synthesis/report.md`

---

## Part 0 — What you already built (the handoff dig)

On **2026-04-14** you did an off-plan session on `okoa-loan-intake-system` and produced **two** things that are the seed of this skill:

1. **A 6,762-line vendor-neutral blueprint** (`blueprint/` in that repo) — captured by **5 parallel domain agents** (data model + state machines; 100+ backend functions; integrations HubSpot/Box/Gmail/Resend; REST API + developer portal; 32 frontend routes/flows) + a `cloudflare-mapping.md` appendix. It documents *behavior* on any stack, with vendor-neutral type conventions.
2. **An `okoa-brand` design-system extraction** — you ran `acos-design-system-forge` on the live URL, producing `design-system-spec.yaml` (1,399 lines), `IMPLEMENTATION.md`, a 12-influence dossier, and a compliance report (0.91–0.92), registered into two ACOS design libraries.

**The crucial self-critique already in your own blueprint README:** it is *behavior-preserving, not intent-level.* Its own "Cross-cutting findings" flag **architecture inflation** — "100+ backend functions is roughly 2× a typical loan-intake backend… consolidate to ~60" — plus 12-state enums that should be columns, dead routes, and prod-shipped test code. **This is the exact gap /acos-reverse-cleanroom exists to close:** the blueprint captured *what the app does*; the new skill must capture *why*, so a rebuild sheds the accidental 40 functions instead of faithfully porting them.

So the lineage is: **design-system-forge** (visual tokens) + **blueprint capture** (behavior) → **reverse-cleanroom** (intent + multi-model rebuild spec). Two of three legs already exist as working skills.

---

## Part 1 — The single biggest thing your prompt is missing

Your prompt treats **Stage 1 (strip to intent)** as the easy part and the **AI fan-out** as the clever part. The research says the opposite.

- LLMs recover *mechanics* well but **omit 33–90% of user-goal-level (WHY) requirements** (UCRBench, Dec 2025). The "strip to intent" step is the maximum-risk stage, not a warm-up.
- Confabulated intent is **fluent and passes citation-QA** — your own Waldorf/Tapestry incident (2026-05-20) proved all 15 quotes can be verbatim-correct while the top-level framing is invented.
- The most dangerous logic is **invisible from the outside**: server-side authz, payment gating, idempotency, rounding/cutoff rules, cron/webhooks. A same-spec study had *every* clone tool skip CSRF, rate-limiting, HSTS, CSP.

**Reframe:** the skill's value and its core hazard are the SAME operation — lossy compression of a real system into intent. Every design decision below is about making that compression honest and loud when it fails.

---

## Part 2 — The 6-stage architecture (your 3 stages, corrected)

Your concept: (1) strip → intent · (2) blind multi-model rebuild · (3) synthesize.
Research says insert a Stage 0, a validation gate, a prioritization pass, and a parity oracle:

```
Stage 0  CAPTURE + BASELINE (the "dirty room")
         7-layer truth stack: structure discovery → Playwright/CDP+HAR behavior →
         HAR→OpenAPI contracts → source-map extraction → vision screenshots →
         auth-role sweep (logged-out/user/admin/paid) → probe server-invisible
         behavior (rate-limits, webhooks, emails, cron) as confidence-flagged inference.
         Capture characterization/golden-master tests + NFR baselines (Lighthouse,
         p95 latency) from the ORIGINAL. Stamp an observation epoch + source_ref.

Stage 1  EXTRACT INTENT (still dirty room → spec wall)
         Goal-oriented (WHY graph: each feature = why it exists, who depends, what
         satisfies). Evidence-link every intent to an observation. Verbatim RULE LEDGER
         for numbers/formulas/rounding/cutoffs (exempt from abstraction). Tag each claim
         confirmed / inferred / gap (Reversa schema). DUAL/TRIPLE BLIND extraction + diff:
         divergence = spec defect. UX-intent layer: jobs/journeys/story-map + state matrix
         (statecharts) + a11y-as-intent + perceived-performance classes + voice/tone.

GATE 1   VALIDATE (before anything leaves the machine)
         Spec wall/monitor strips literal expression, secrets, PII, tech nouns (contamination
         lint). Completeness = external surface census (route/screen/endpoint census) as the
         denominator the LLM can't fudge. grep-audit categorical claims. Few, sharp human
         gates: low-confidence claims + rule ledger + coverage census only (avoid fatigue).

Stage 1.5 PRIORITIZE (the anti-inflation stage — your blueprint's own lesson)
         Inverted MoSCoW + feature-value archaeology: decide what NOT to rebuild. This is
         where "100+ functions → ~60" happens by design.

Stage 2  BLIND MULTI-MODEL REBUILD (the "clean room")
         N=3–5 comparable-strength models from DISTINCT families (Claude, GLM, Gemini,
         Kimi/DeepSeek, OpenAI). ONE verbatim proposer prompt (divergence is the product).
         Blind: no model sees another's proposal or identity. No debate. Dead lane =
         INCONCLUSIVE; 3-of-5 quorum. Clean room sees ONLY the intent spec, never the original.

Stage 3  SYNTHESIZE (backbone-first, not blend)
         Pick ONE proposal as architectural backbone; graft only compatible strengths from
         others (each justified against the backbone's assumption set). Per-section: facts via
         convergence rules; design choices via pairwise-judged trade-offs. ASYMMETRIC VETO on
         catastrophic axes (security/data-loss/dropped-requirement). Security/edge requirements
         = UNION, never vote. Cross-family synthesizer (not a proposer family). Patch-don't-
         renarrate on iterations. Plan-then-write section-sequential emission.

Stage 4  PARITY + TRACEABILITY (the acceptance oracle)
         Every acceptance criterion = a behavioral-parity golden test vs the ORIGINAL
         (parity-manifest.json, confidence-banded, knownDeviation[]). intent_id → spec-section
         traceability matrix as a HARD GATE (every intent mapped or explicitly waived).
         Adversarial red-team of the fused spec (different family, blind to fusion rationale).
         Output lands into ACOS Vision/Epic/Story/Slice + Genesis component-tree — never a
         parallel format. Recommend strangler-fig incremental adoption, never big-bang.
```

---

## Part 3 — The design decisions to riff on (each has a research-backed default)

| # | Decision | Research-backed default | Live tension to riff |
|---|---|---|---|
| D1 | Same-purpose vs same-behavior rebuild? | Per-project scoping gate (Hyrum's Law) | Consumer-facing APIs need behavior parity; internal tools want purpose only |
| D2 | How many proposer models (N)? | 3–5 distinct families | Subscription-covered (Claude, GLM) are "free"; is same-family Claude diversity enough? |
| D3 | Fusion method | Backbone + grafts | vs the axiom-synthesis claim-engine you already have — reuse or bypass? |
| D4 | Consensus meaning | Diversity-fusion; union security; NEVER majority-vote | Feels counterintuitive — agreement is *weak* evidence here |
| D5 | Proprietary-target egress | ZDR/paid keys or self-host open weights | Kimi trains by default; is it in the proprietary path at all? |
| D6 | Third-party targets | Refuse auth-gated scraping; frame as personal aid | Legal status of AI cleanroom specs untested — how conservative? |
| D7 | Output format | Land into Genesis component-tree + Slices | Genesis is the closest existing consumer — extend it or wrap it? |
| D8 | Human gates | Few + sharp (divergence, rule ledger, census) | Where exactly do YOU want to sit in the loop vs full autopilot? |
| D9 | Reuse vs build | design-system-forge + blueprint capture already exist | Is reverse-cleanroom an orchestrator that CALLS them, or a monolith? |

---

## Part 4 — What you must KNOW before building (the non-obvious facts)

1. **Citation-QA is not enough** — verify the support *relation* between evidence and stated intent, and grep-audit every categorical claim. (Your own incident.)
2. **A verbatim rule ledger is mandatory** — prose abstraction destroys rounding modes, day-counts, cutoff timezones. Capture numbers exactly with input→output examples.
3. **Agreement across models is weak evidence** — correlated errors (~60% joint) mean unanimity can reproduce a commonly-blogged anti-pattern. Downgrade, don't upgrade, on consensus.
4. **Debate makes it worse** — keep proposals blind end-to-end; resolve conflicts with structure, not conversation.
5. **The synthesizer must not be a proposer family** — self-preference bias is real and reads as merit.
6. **Cost is a non-issue; context window and law are the real limits** — synthesis belongs on in-session Claude (1M ctx, $0 marginal); proprietary targets need ZDR or self-hosted open weights.
7. **You already hit the failure mode this fixes** — the blueprint's "100+ functions, consolidate to ~60." Stage 1.5 (prioritize) is the fix; don't skip it.
8. **Land into existing ACOS shapes** — Vision/Epic/Story/Slice + Genesis; the parity manifest becomes each slice's `verification_method`.

---

## Part 5 — Open questions the research could NOT answer (genuine unknowns)
- No benchmark exists for whole-app intent-extraction accuracy or multi-spec fusion — you'd be defining a new eval axis.
- Whether same-family Claude panels give enough effective diversity (unmeasured).
- Legal status of AI-authored cleanroom specs (no case law).
- Whether OpenRouter→GLM inherits GLM's zero-retention DPA or the aggregator's weaker terms.

---

## Part 6 — Suggested riff agenda (what to decide together next)
1. **Scope of v1**: own apps only (safer, your loan-intake is the natural first target) vs any URL?
2. **D9 — architecture**: orchestrator that calls design-system-forge + a blueprint-capture agent + the fan-out, or one new monolith skill?
3. **D2/D5 — the model roster**: which 3–5 families, and does Kimi make the cut given train-by-default?
4. **D3 — fusion**: reuse acos-axiom-synthesis for the factual layer, or a fresh backbone+graft synthesizer?
5. **D8 — autonomy**: how many human gates, and where?
6. **First test target**: re-run on `okoa-loan-intake-system` so we can measure intent-spec vs the existing behavior blueprint (built-in ground truth).
