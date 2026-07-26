## 3. Users and usage model

### 3.1 Primary user

One person — the ACOS owner — building sites for their own projects (FruitSync, OKOA, future ventures). Technically capable, not a trained designer, has strong taste but limited design vocabulary. Owns a Claude subscription with web access. Works on macOS. **[V — established from repo context and the user's own prior work at `/Users/zee/Documents/Vibe Coding/website-design-okoa/`]**

The primary user is the sole *aesthetic judge* in this system (see §3.4): every direction, variant, and layout decision routes through their taste. They are not, however, the only stakeholder this PRD has obligations toward — see §3.2's tertiary class below, which the primary user will never directly interview but for whom the machine still enforces correctness.

### 3.2 Secondary and tertiary users (design for, don't optimise for)

**Secondary — people who touch the editor:**

- A future collaborator reviewing a site before LOCK (read-only preview link, v2).
- The user themselves six months later, making a copy change (content mode, v2).

**Tertiary — the published site's visitors.** *(Added — closes a gap: neither the primary user in §3.1 nor either secondary user above is the person who actually loads the finished, LOCKed website. Every stakeholder named in §3.1–3.2 touches the *editor*; none of them is the audience the *output* is built for.)*

- Never interviewed, never named individually, never given a persona beyond "whoever the ACOS owner is building this site for" (could be OKOA investors, FruitSync players, a future venture's customers — the identity varies per project and is out of scope for this PRD to enumerate).
- They are the reason the machine-enforced correctness gates in §13 (contrast, reflow, keyboard/pointer-alternative dragging, licence attribution, photosensitivity, responsive behaviour) are non-negotiable even though the human is the aesthetic judge and could otherwise wave any of them through. Without a named tertiary class, those gates read as generic compliance boilerplate; with one, they read as this PRD keeping a promise to a real (if unspecified) audience the primary user cannot fully represent on their own — the primary user can tell you a button looks good, not that it is operable for a visitor using a screen reader or a 320px phone.
- **Scope boundary, stated plainly:** this PRD does not run user research, usability testing, or persona work for the tertiary class — that would require a per-project interview the skill does not conduct. Instead it treats the tertiary class as the *justification* for machine correctness rather than a group whose preferences get elicited. This is a deliberate, narrower commitment than full accessibility/UX research, and it is named here so the gap between "gates exist" and "a visitor was actually consulted" is visible rather than implied away.
- **Open question — no known mitigation:** if a given project's tertiary audience has known access needs (e.g., a visually-impaired investor, a specific screen-reader user), nothing in the current interview (§2) surfaces that and routes it into stricter per-project gate thresholds. This PRD does not propose a mechanism for that today; it would need a user decision on whether the Step-1 interview should ask "who is this site for, and do they have access needs you know about?" and, if yes, how that answer tightens §13's gates on a per-project basis.

### 3.3 Usage model

| Mode | Trigger | What happens | Session shape |
|---|---|---|---|
| Cold start | `/acos-website-builder` in a project with no prior site | Full interview → prompt → hand-carry → build → edit → lock | One long session, resumable |
| Warm start | Prior design system detected at Step 0 | "What's changing?" interview (much shorter) → optionally reuse tokens → build | Half a session |
| Return-to-edit | `/acos-website-builder --resume` | Reads `state.json`, recomputes phase from disk, re-attaches to the running server or restarts it | Minutes |
| Content edit | `/acos-website-builder --content` (v2) | Text-only editing path, no dev server, no design layer | Minutes |
| Variant round | User clicks "more variants" in the editor | Deterministic generator produces 5–10 neighbours; no claude.ai hop | Seconds |
| System redesign | User asks for a new/partial design-system prompt | Back to Step 2 with prior parameters as negative constraints | New hand-carry cycle |

None of these six modes is driven by, or informed by, the tertiary visitor class in §3.2 — every trigger and session shape here is authored from the primary/secondary users' actions inside the editor. The tertiary class only enters the system indirectly, via the correctness gates each mode's build/edit/lock step runs against (§13). This is intentional (visitors don't operate the editor) and is noted here so the absence isn't mistaken for an oversight.

### 3.4 The human's role, stated plainly

The human supplies **taste** (which direction, which variant, where things go, what the copy says) and **acceptance** (LOCK). The machine supplies **coherence** (derived tokens, direction hashing, lint), **correctness** (contrast, reflow, licence, export purity), and **labour** (generation, layout, build, publish). The machine never overrides a taste decision; it may refuse to ship a correctness violation.

Restated against §3.2's three-tier user model: the primary and secondary users (§3.2) are who the human's taste judgment serves — they are in the room, they can see the site, they can say "I like this." The tertiary visitor class is who the machine's correctness mandate serves — they are never in the room, so the machine holds the line on their behalf even when no human present would notice or object to a violation (e.g., a contrast ratio that reads fine to the sighted primary user but fails for a low-vision visitor). This is the load-bearing reason "the machine may refuse to ship a correctness violation" is not merely a safety rail on the *product* — it is the only mechanism in this entire usage model that represents the tertiary user's interests at all.

---
