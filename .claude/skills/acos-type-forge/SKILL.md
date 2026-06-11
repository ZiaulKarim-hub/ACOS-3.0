---
name: acos-type-forge
description: Type-Forge — a self-contained workshop for forking a custom font from an OFL-licensed base typeface. One unified local server fronts a home page linking a browser glyph paint editor (erase/fill/copy editable-polygon tools, transformable paste), a spacing editor (independent per-glyph cushions + live Compare-against-the-alphabet), and a specimen viewer (size waterfall, full character set, many lighting conditions). Renames OFL-compliantly, vectorizes raster edits back into real outlines via potrace, auto-spaces, exports TTF/WOFF2/OTF, and can wire the result into an Astro project. Use when the user wants to modify, fork, restyle, stencil, de-serif, space, or build a custom display/titling font from an existing one.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# acos-type-forge — Type-Forge

## Purpose
Turn an existing open-source (OFL) typeface into a renamed, custom derivative —
through a browser **paint editor** for freeform per-glyph sculpting, a **spacing
editor** for setting the rhythm by eye, a **specimen viewer** for judging it in
use, and a **programmatic pipeline** for deterministic transforms. Closes the full
loop from "modify a letter" to "installable, OFL-compliant, web-ready font."
The app is **brand-neutral and standalone** — reusable for any font, any project.

## When to Use
Apply this skill when the user wants to:
- Modify / fork / restyle an existing font (stencil cuts, remove serifs, tracking, custom letterforms)
- Hand-edit individual glyphs (erase parts, copy a serif/stem and reuse or mirror it)
- Produce a renamed derivative for a brand (e.g. a titling face for a website)
- Vectorize hand-painted glyph edits back into a real font
- Wire a custom font into an Astro site

NOT for: choosing/pairing existing fonts (no modification), licensing advice
beyond the OFL rename rule, or non-Latin shaping/OpenType-feature engineering.

## ⚖️ The one hard rule — OFL Reserved Font Name
OFL 1.1 grants modification + redistribution (even commercial), with ONE
constraint: your derivative's name must **NOT** contain the base font's *Reserved
Font Name*. Keep the original copyright/attribution (nameID 0) and ship the OFL +
a FONTLOG. `rename_export.py` enforces this (it asserts and scrubs). Renaming is a
feature: the derivative becomes a distinct brand asset.

## Setup
```
bash scripts/setup.sh      # fonttools, shapely, brotli, Pillow, fontforge, potrace
```

## The Type-Forge app — one server, one home page

Launch the whole app with a single command:
```
bash scripts/typeforge.sh /path/to/Base.ttf /path/to/built.ttf /path/to/edits_dir [port]
# → http://127.0.0.1:8800/   (home hub linking the three tools)
```
- **Base.ttf** — base typeface; the glyph editor's ghost (served as `base.woff2`).
- **built.ttf** — current vectorized font; shown in spacing + specimen (served as `font.woff2`). On the first run, before you've vectorized anything, pass the base TTF for both.
- **edits_dir** — holds `glyph-edits.json` (glyph paint) and `spacing.json` (cushions); both are read by `vectorize.py`.

One origin = relative links + shared `localStorage`. The glyph editor also **loads saved edits from disk** on startup, so work follows you across origins/machines.

### Home → three tools

**Glyph Editor** (`/editor.html`) — Pencil / Eraser / Straight-line + three
**editable-polygon** tools (**Erase**, **Fill**, **Copy**). Polygons have draggable
corners, mid-edge vertex-adders, a movable body, Apply. **Copy** lifts ink to a
**floating clipboard** persisting across letters; before stamping it is a live
**transform box** — move, **resize** (corner), **rotate** (top knob), **flip** —
then Stamp (⏎) rasterizes it. Side pane = **collapsible categories** with an
**A · Core (~80) / B · Full (~350)** scope toggle. Ink-centering, guides, ghost,
undo/redo, autosave; **💾 Save (⌘S)** writes `glyph-edits.json`.

**Spacing Editor** (`/spacing.html`) — set **independent L/R cushions per glyph** by
eye with live preview (font units; negative = overhang so neighbours tuck in).
**⊞ Compare all** flanks a chosen **focus letter** against every other letter at
real live spacing; the focus letter's sliders drive all rows, and clicking any
row's control letter tweaks *its* cushions too. **💾 Save** writes `spacing.json`.

**Specimen Viewer** (`/specimen.html`) — showcase the finished font: a size
**waterfall**, a tracking ladder, **the full character set** (every glyph in the
font, grouped), a sample setting, and **many backgrounds / lighting conditions**
(curated swatches + custom bg/text colour pickers) to stress-test legibility.
Optional `?name=Family%20Name` sets the displayed name.

## Programmatic transforms (optional, scriptable)
```
# tracking (FontForge embedded python — NOT system python):
fontforge -lang=py -script scripts/track.py --in base.ttf --out staged.ttf --track 30
# true-boolean stencil cut (Shapely):
python3 scripts/cut.py --in staged.ttf --out cut.ttf --letters OKA --y0 318 --y1 382
# foot-serif removal (clean-stem letters only):
python3 scripts/strip_serifs.py --in cut.ttf --out noserif.ttf --letters AFHIKMNPRT --serif-h 116
```

### Bridge — raster edits → real outlines
```
python3 scripts/vectorize.py --base base.ttf --edits edits/glyph-edits.json \
    --out edited.ttf --em 620 --baseline 740
```
By default vectorize **preserves the base font's metrics** (advance + LSB). If your
repainted ink is wider than the original glyph, letters will **touch** (e.g. "HE").
Add `--space <units>` to **auto-space**: each edited glyph gets LSB = RSB = `units`
and advance = ink_width + 2·units, computed from the *actual traced ink*. Try `--space 80`
(≈8% of a 1000-unit em) and tune in the spacing editor. Auto-spacing applies only to
edited glyphs; untouched glyphs keep their original metrics.

Spacing controls layer in increasing specificity (each overrides the previous):
- `--space N` — global sidebearing for all edited glyphs.
- `--uc-space N` — separate sidebearing for **uppercase** (caps usually want less than lowercase small-caps).
- `--lc-space N` — separate sidebearing for **lowercase** a-z (with `--lc-scale`, small-caps want a tighter sidebearing than `--space`).
- `--letter-space "CHARS:N,…"` — per-letter override, e.g. `"ANRUVWX:-20"` (diagonal/open letters want tighter or negative sidebearings; the triangular gap absorbs it).
- `--lc-scale F` — scale lowercase glyphs about the baseline (e.g. `0.75` makes small-caps); advances follow the new size.
- `--spacing-file spacing.json` — EXACT independent `{char:[L,R]}` cushions from the Spacing Editor; highest priority.

Any one of `--space` / `--uc-space` / `--lc-space` / `--letter-space` / `--spacing-file`
**enables auto-spacing on its own** — you do NOT also need `--space`. When `--space` is
omitted, letters not covered by the flag you passed fall back to a default sidebearing
(80 units ≈ 8% of a 1000-unit em), so e.g. `--spacing-file spacing.json` alone applies
the file's exact cushions and spaces every other glyph with the default. Note: entering
the spacing branch also strips inherited kerning (see warning below).

⚠️ Whenever you re-space (any spacing flag — `--space` / `--uc-space` / `--lc-space` /
`--letter-space` / `--spacing-file`) or scale (`--lc-scale`), vectorize
**strips the inherited GPOS/`kern` table** — the donor font's kerning was tuned for
its original widths and will fight your new sidebearings (e.g. a stale `h→e` kern of
−337 fuses "he"). After re-spacing, kerning is the renderer's job, not the donor's.

Typical full rebuild:
```
python3 scripts/vectorize.py --base base.ttf --edits edits/glyph-edits.json \
    --out build/edited.ttf --em 620 --baseline 740 \
    --space 30 --uc-space 10 --letter-space "ANRUVWX:-20" --lc-scale 0.75 \
    --spacing-file edits/spacing.json
```

### Review IN THE BROWSER (do this BEFORE finalizing) ⚠️
A font only reveals its spacing and character in real use, not glyph-by-glyph.
Re-launch the app on the freshly-built font and review before rename+export:
```
bash scripts/typeforge.sh base.ttf build/edited.ttf edits/ 8800   # → http://127.0.0.1:8800/
```
- **Spacing Editor** → tune cushions by eye (Compare mode flanks a letter against the whole alphabet); Save `spacing.json`, re-vectorize with `--spacing-file`.
- **Specimen Viewer** → judge size waterfall, the full character set, and the face across many backgrounds/lighting.
Iterate (re-edit glyphs / re-space) until it reads right. Only then finalize.
(Re-running the build → re-launching the server is the loop; the server reads the
font fresh each launch.)

### Finish — OFL rename + export, specimen, wire-in
```
python3 scripts/rename_export.py --in edited.ttf --family "Your Titling" \
    --reserved Cinzel --base "Cinzel Decorative" --author "Natanael Gama" \
    --owner "You" --out-dir build/ --mods "stencil cut + de-serif" --ofl src/OFL.txt
python3 scripts/specimen.py --base base.ttf --new build/YourTitling-Regular.ttf --text "Type" --out specimens/proof.png
python3 scripts/wire_astro.py --font build/YourTitling-Regular.woff2 --astro /path/to/site --css-var --font-titling --family "Your Titling"
```

## Skill Protocol
1. **Setup** deps (`setup.sh`). Obtain the base font's source TTF + OFL.txt (e.g. from the google/fonts repo).
2. **Decide workflow:** deterministic transform (tracking/cut/serif) vs hand sculpting (editor) vs both.
   - If using the editor, **ask the user the side-pane scope: A · Core (~80 core-Latin glyphs)
     or B · Full (~350, incl. accented + extended punctuation/currency).** Default to A for a
     titling/display face (uppercase-led brands rarely need accents). The user can also flip
     the A/B toggle live in the pane, so this is a starting point, not a lock-in.
3. **Edit.** For the editor, ALWAYS render specimens / screenshots and iterate ONE glyph at a time with the user — they decide visually (see Gotchas). The Copy tool's floating clip can be moved/resized/rotated/flipped before stamping. Save to disk.
4. **Vectorize** any raster edits back into outlines. If letters touch, re-run with `--space` (auto-spacing).
5. **Browser review** (`typeforge.sh`) — re-launch on the built font; tune cushions in the Spacing Editor, judge the Specimen Viewer; iterate (back to step 3/pipeline) until it reads right. **This gate precedes finalizing — do not skip it.**
6. **Rename + export** OFL-compliantly; emit a **before/after specimen** and confirm visually.
7. **Wire** into the target project if requested.

## Quality Checklist
- [ ] **Browser review BEFORE export** (`typeforge.sh`) — spacing tuned in the Spacing Editor; full character set + multiple lighting conditions judged in the Specimen Viewer, not just per-glyph
- [ ] New family name does NOT contain the base's Reserved Font Name; nameID 0 keeps attribution
- [ ] OFL.txt + FONTLOG.txt ship with the font
- [ ] Cuts verified by rendered specimen (areas DECREASE; no fill bars on K/A/E)
- [ ] Round/pointed letters not damaged by serif-strip (only clean-stem letters treated)
- [ ] Spacing checked in the proof — metrics preserved by default, or `--space` used so no letters touch
- [ ] Baseline preserved after vectorize (glyphs sit on the baseline; --em/--baseline match the editor canvas)
- [ ] WOFF2 emitted for web; TTF/OTF for desktop

## Gotchas (hard-won — do not relearn these)
- **FontForge `removeOverlap` FILLS empty regions** of a reverse-wound rectangle → a *bar*, not a cut, on letters with gaps at the cut height (K, A, E). **Use Shapely `difference`** for true boolean cuts (`glyphgeom.py` + `cut.py`). This was 4 failed attempts before the fix.
- **Round-trip outlines** TrueType-quadratic → flat rings (BasePen) → Shapely → `TTGlyphPen`; orient exterior CW / holes CCW.
- **Center glyphs by INK, not advance** in any preview/editor — decorative faces spill far outside their metrics box (Q's tail ≈ 1.5em, V above cap height), so advance-centering clips them.
- **Web fonts can't load over `file://`** in Chrome → always serve over localhost (`typeforge.sh`).
- **macOS APFS is case-insensitive** — `MyFont` and `myfont` collide; pick distinct names for sibling dirs.
- **FontForge side_bearing setters need int** — cast or they raise a float TypeError.
- **WOFF2 needs the `brotli` python module** (in setup).
- **Serif removal is per-letter**, not one-rule-fits-all: stem letters extrude cleanly; bowls (B,D) and bottom-arm letters (E,L,Z) need bespoke handling; round/pointed letters have no foot serif.

## Output Requirements
A `build/` with the renamed font in **WOFF2 + TTF (+ OTF)**, `FONTLOG.txt`, `OFL.txt`,
and a before/after specimen PNG. If editor edits were used, the source
`edits/glyph-edits.json` is retained for re-vectorizing.

## Reference instance
A complete working instance (Cinzel Decorative → a custom titling face) lives in a
`font-foundry/` working directory: `src/` (base TTF + OFL), `editor/edits/`
(`glyph-edits.json`, `spacing.json`), `build/` (vectorized + exported font). Mine it
for a concrete end-to-end example.

---
*Type-Forge (acos-type-forge) — fork a typeface, sculpt the glyphs, space it by eye, ship an OFL-clean font.*
