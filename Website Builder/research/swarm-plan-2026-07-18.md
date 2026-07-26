# Swarm Research Plan

**Session:** swarm-20260718-022431
**Date:** 2026-07-18
**Agents:** 20 (max of skill range 5-20; user asked for maximum rigor)

## Research Question

How should an AI-driven, DESIGN-FIRST "dream/high-end/perfect website" builder be
built as a Claude Code skill/system (ACOS-style)? The goal is producing websites
with award-quality visual design (Awwwards/FWA tier), not backend plumbing.

Target site types:
1. Marketing/brand sites (primary)
2. Game/product promo sites (e.g., the local FruitSync game project)
3. Full web apps with login where only the design/frontend quality matters

## Sub-questions

- SQ1: What objectively makes a website "high-end/award-quality," and how can it be measured/verified?
- SQ2: How do existing AI site builders (v0, Lovable, Bolt, Webflow AI, Framer AI, Relume, etc.) work, and where do they fall short of high-end design?
- SQ3: What agent architecture (design generation + adversarial visual QA loops, screenshot review, scoring rubrics, iterate-until-perfect) best produces and verifies high-end design?
- SQ4: What design-system/token/art-direction approach lets AI generate distinctive (non-generic) design and avoid "AI slop" sameness?
- SQ5: What frontend stack and component/motion libraries are best suited for AI generation of high-end sites (Astro, Next.js, Tailwind, GSAP, three.js, Framer Motion, etc.)?
- SQ6: How should the system be structured as ACOS agents/skills (orchestrator, designer, builder, visual reviewers, Wigum loops), reusing existing ACOS pieces?
- SQ7: How does one system serve the three site types (marketing/brand, game promo, login app shells) with per-type quality bars?

## Lenses Applied

Technical Feasibility, Competitive Landscape, User Impact, Historical Context,
Risk Assessment, Scalability & Performance, Future Trajectory,
Community & Ecosystem, Integration & Compatibility

## Agent Assignment Matrix

| Agent | Sub-question | Lens |
|-------|--------------|------|
| 01 | SQ1 measurable design attributes → rubrics | Technical Feasibility |
| 02 | SQ1 how Awwwards/FWA/CSSDA actually judge | Competitive Landscape |
| 03 | SQ1 beauty vs usability/accessibility tension | User Impact |
| 04 | SQ1 dated-vs-premium; evolution of web design trends | Historical Context |
| 05 | SQ2 how AI builders work under the hood | Technical Feasibility |
| 06 | SQ2 quality comparison; gap to award tier | Competitive Landscape |
| 07 | SQ2 failure modes of AI builders | Risk Assessment |
| 08 | SQ3 multi-agent design pipelines + VLM screenshot QA | Technical Feasibility |
| 09 | SQ3 QA-loop failure modes (rubric gaming, non-convergence) | Risk Assessment |
| 10 | SQ3 iteration cost, token budgets, loop caps, parallelism | Scalability & Performance |
| 11 | SQ4 design tokens, theme/type/palette generation | Technical Feasibility |
| 12 | SQ4 distinctiveness strategies; anti-"AI slop" | Competitive Landscape |
| 13 | SQ4 future of AI art direction + asset generation | Future Trajectory |
| 14 | SQ5 stack choice for AI codegen | Technical Feasibility |
| 15 | SQ5 performance (Core Web Vitals) at high-end fidelity | Scalability & Performance |
| 16 | SQ5 library maturity, licensing, ecosystem | Community & Ecosystem |
| 17 | SQ6 ACOS agent/skill architecture mapping | Technical Feasibility |
| 18 | SQ6 Claude Code primitives + known constraints | Integration & Compatibility |
| 19 | SQ7 one pipeline, three site types (incl. FruitSync grounding) | Technical Feasibility |
| 20 | SQ7 audience expectations per site type | User Impact |

## Isolation

Each agent receives ONLY its own output path
(.acos/swarm/swarm-20260718-022431/agent-NN/findings.md) and is told not to
read or write any other swarm directory. Synthesis is performed afterward by a
single synthesizer with access to all findings.
