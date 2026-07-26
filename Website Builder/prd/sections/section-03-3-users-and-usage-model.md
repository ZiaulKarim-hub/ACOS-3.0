## 3. Users and usage model

### 3.1 Primary user

One person — the ACOS owner — building sites for their own projects (FruitSync, OKOA, future ventures). Technically capable, not a trained designer, has strong taste but limited design vocabulary. Owns a Claude subscription with web access. Works on macOS. **[V — established from repo context and the user's own prior work at `/Users/zee/Documents/Vibe Coding/website-design-okoa/`]**

### 3.2 Secondary users (design for, don't optimise for)

- A future collaborator reviewing a site before LOCK (read-only preview link, v2).
- The user themselves six months later, making a copy change (content mode, v2).

### 3.3 Usage model

| Mode | Trigger | What happens | Session shape |
|---|---|---|---|
| Cold start | `/acos-website-builder` in a project with no prior site | Full interview → prompt → hand-carry → build → edit → lock | One long session, resumable |
| Warm start | Prior design system detected at Step 0 | "What's changing?" interview (much shorter) → optionally reuse tokens → build | Half a session |
| Return-to-edit | `/acos-website-builder --resume` | Reads `state.json`, recomputes phase from disk, re-attaches to the running server or restarts it | Minutes |
| Content edit | `/acos-website-builder --content` (v2) | Text-only editing path, no dev server, no design layer | Minutes |
| Variant round | User clicks "more variants" in the editor | Deterministic generator produces 5–10 neighbours; no claude.ai hop | Seconds |
| System redesign | User asks for a new/partial design-system prompt | Back to Step 2 with prior parameters as negative constraints | New hand-carry cycle |

### 3.4 The human's role, stated plainly

The human supplies **taste** (which direction, which variant, where things go, what the copy says) and **acceptance** (LOCK). The machine supplies **coherence** (derived tokens, direction hashing, lint), **correctness** (contrast, reflow, licence, export purity), and **labour** (generation, layout, build, publish). The machine never overrides a taste decision; it may refuse to ship a correctness violation.

---

