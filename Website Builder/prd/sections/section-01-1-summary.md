## 1. Summary

### What this is

Website Builder is an ACOS skill that turns a conversation into a distinctive, hand-adjustable website. It runs in eight steps:

1. It checks whether you already have a design system or a prior site (warm start).
2. It **interviews you** — about purpose, audience, positioning, taste, accessibility, performance, and constraints.
3. It **writes a prompt** for you to paste into claude.ai on the web, where Claude's design/artifact generation produces a complete design system: typography, colour, motion, artwork, components, and everything else the site needs.
4. You **hand-carry** the result back.
5. It **interviews you again** to select each component, then builds the site as a **live editable design surface** — gridlines you snap to, components you drag, text you edit in place, a component bar for swapping any element for a comparable variant, and a save button.
6. You can ask for **more variants** or a **redesigned system** at any point.
7. You can add **custom components** the standard system doesn't cover (charts, calculators, maps).
8. You say **LOCK** — the design toolbars and gridlines disappear and you get a clean static site with no editor code in it, while the editable version stays beside it. Then it publishes, with a licence-and-evidence bundle listing every font and asset.

The human is the aesthetic judge. There is no AI critic scoring screenshots in a loop. Machines enforce the things machines are good at — contrast ratios, token purity, reflow at 320px, licence completeness, "does the editor runtime actually not ship" — and the human decides everything about how it looks.

### What this is not

- **Not an autonomous site generator.** The prior swarm report designed an award-quality generator that judges its own screenshots and iterates. That architecture is explicitly replaced. Its rubrics, anti-slop lint, stack recommendations, licensing policy, performance gates, and capture protocol are reused; its judge loop is not.
- **Not Webflow.** The pixel canvas is the last thing built, not the first, and the layout model is constraint-based by default (D2), not free x/y.
- **Not a template picker.** Directions are generated per project against the interview answers, not chosen from a fixed gallery.
- **Not a claim of WCAG certification.** Automated accessibility tooling tops out around 57% of real issues [V — Deque Accessibility Coverage Report, 13,000+ pages/page-states]. The evidence bundle will say "passed N automated gates," never "AA compliant."
- **Not a raster art generator.** claude.ai cannot produce bitmap images [V — confirmed by Anthropic, April 2026]. Art comes from code-drawn SVG/CSS/canvas, from an ingested asset library, or from a separately-scoped external generator. See §7.9 and §17-R1.
- **Not award-winning by construction.** A swap-menu builder produces coherent, bespoke, hand-adjustable sites. Award juries recognise assembled output [V — prior swarm report Finding 2]. The one lever that raises the ceiling is the custom code block (§10.7, §14.4), and the PRD says so plainly rather than over-promising.

---

