---
name: acos-ultimate-designer
description: "Use this skill when the user wants to generate an institutional-grade coffee-table-book-style PDF or editable PPTX from arbitrary content (YAML or markdown). The skill uses OKOA's design system (Cormorant Garamond headlines with italic accents, IBM Plex body, warm-neutral + sage + navy + coral palette, Carbon 16-column grid), page-as-canvas composition with 9 art-directed templates (cover, two-column-narrative, metric-grid, timeline, chapter-divider, product-detail, portfolio-grid, photo-break, closing), brand-asset image sourcing with Unsplash/Pexels fallback, and visual verification via opus-pinned screenshot review with a Wigum loop. Triggers on requests to create investor books, coffee-table PDFs, OKOA-styled documents, editorial briefs, private-credit tear sheets, or any long-form document that needs the v3 Private Credit Capabilities aesthetic."
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion, Glob, Grep
---

# acos-ultimate-designer

## Purpose

Transform arbitrary user content into institutional-grade documents (PDF or editable PPTX) matching the OKOA coffee-table aesthetic. Composes Brad's OKOA design system (style source) with loan-doc's conversion + visual-verification machinery (rendering infrastructure) — zero design-library content loads, Brad is the sole style authority.

Output matches the v3 Private Credit Capabilities reference: full-bleed cover, chapter dividers, mid-content photo bands, Cormorant italic accents, roman "N / total" page numbers, closing dark panel.

## Protocol

### Phase 0 — Wizard

**Mode selection:** Ask the user "Quick wizard (3 prompts) or Detailed wizard (6 prompts)?" via `AskUserQuestion`.

**Quick mode** (3 prompts):
1. **Content source path** (text input) — absolute path to a YAML or markdown file containing the document content.
2. **Output format** (`AskUserQuestion`, options: `pdf`, `pptx`, `both`).
3. **Brand-asset directory path** (text input, may be empty) — absolute path to a directory of OKOA brand images. If empty, the skill uses Unsplash/Pexels-only mode.

**Detailed mode** (adds 3 more prompts after the Quick set):
4. **Document type** (`AskUserQuestion`, options: `editorial`, `technical`, `executive`) — informs template selection emphasis.
5. **Special instructions** (text input, optional) — e.g., "use dark cover", "emphasize growth".
6. **Iteration ceiling override** (text input, optional, default 5) — max Wigum iterations before surfacing.

**Session setup:**
- Session ID: `YYYYMMDD-HHMMSS-<slug>` where `<slug>` is derived from the content title (fallback: `doc`).
- Session directory: `.acos/ultimate-designer/sessions/{session_id}/`
- Write all collected inputs to `{session_dir}/manifest.yaml` (the session manifest, not the brand-asset manifest).

Read the full wizard spec in [phases/phase0-wizard.md](phases/phase0-wizard.md).

### Phase 1 — HTML Emission

Dispatch per [phases/phase1-html.md](phases/phase1-html.md). In short:

> **Note on `SKILL_DIR`:** the `readlink -f "$0"` form below only resolves
> correctly when this block is saved to a file and executed. When you run these
> commands inline (where `$0` is the shell name, e.g. `-bash`), set
> `SKILL_DIR` to the repo-absolute skill path instead:
> `SKILL_DIR=".claude/skills/acos-ultimate-designer"`. The same applies to every
> bash block in this SKILL.md and the phase files.

```bash
SKILL_DIR="$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")/.."
SESSION_DIR=".acos/ultimate-designer/sessions/{session_id}"

python3 "$SKILL_DIR/scripts/decompose-content.py" \
  "{content_path}" "$SESSION_DIR/page-plan.yaml"

python3 "$SKILL_DIR/scripts/html-emit.py" \
  "$SESSION_DIR/page-plan.yaml" "$SESSION_DIR/output.html"

python3 "$SKILL_DIR/scripts/html-qa-gate.py" \
  "$SESSION_DIR/output.html" "$SESSION_DIR/qa-report.yaml"
```

On QA gate failure (exit 1), STOP and report the failing items. On Wigum-triggered re-entry, pass `--fix-context {session_dir}/fix-instructions.yaml` to `decompose-content.py`.

### Phase 2 — Image Sourcing

Dispatch per [phases/phase2-images.md](phases/phase2-images.md). In short:

```bash
if [ -n "{asset_dir}" ] && [ -d "{asset_dir}" ]; then
  python3 "$SKILL_DIR/scripts/bootstrap-manifest.py" --asset-dir "{asset_dir}"
fi

python3 "$SKILL_DIR/scripts/fill-photo-slots.py" \
  --html "$SESSION_DIR/output.html" \
  --manifest "{asset_dir}/.acos-ultimate-designer-manifest.yaml" \
  --session-dir "$SESSION_DIR" \
  --output "$SESSION_DIR/output.html"
```

Missing `UNSPLASH_ACCESS_KEY` and `PEXELS_API_KEY`: log warning and continue — unmatched slots become visible empty-slot placeholders caught by Phase 4.

### Phase 3 — Convert

Dispatch per [phases/phase3-convert.md](phases/phase3-convert.md). Conditional on output format.

**For `pdf` or `both`:**
```bash
bash "$SKILL_DIR/scripts/render-pdf.sh" \
  --input "$SESSION_DIR/output.html" \
  --output "$SESSION_DIR/output.pdf"
```

**For `pptx` or `both`:**
```bash
python3 "$SKILL_DIR/scripts/emit-pptx-content.py" \
  --page-plan "$SESSION_DIR/page-plan.yaml" \
  --image-log "$SESSION_DIR/image-resolution.log" \
  --output "$SESSION_DIR/pptx-content.yaml"

bash "$SKILL_DIR/scripts/render-pptx.sh" \
  --content "$SESSION_DIR/pptx-content.yaml" \
  --template "$SKILL_DIR/templates/template.pptx" \
  --design-spec "$SKILL_DIR/templates/pptx-design-spec.yaml" \
  --output "$SESSION_DIR/output.pptx"
```

### Phase 4 — Visual Verification + Wigum Loop

Dispatch per [phases/phase4-verify.md](phases/phase4-verify.md). This phase is the master Wigum orchestrator — it invokes Phase 1-3 internally on each iteration.

```bash
python3 "$SKILL_DIR/scripts/wigum-loop.py" \
  --session-dir "$SESSION_DIR" \
  --format "{output_format}" \
  --max-iterations "{iteration_ceiling}" \
  --hard-ceiling 10
```

The wigum loop:
1. Runs render-and-verify.sh on the current output
2. If PASS: copies final output to session root, exits 0
3. If FAIL: classifies defects, writes `fix-instructions.yaml`, re-enters Phase 1 with fix context
4. A (criterion,page) WARNING seen on 3 consecutive iterations escalates to ERROR on the 3rd
5. Soft max (`--max-iterations`): exit 4 ("needs operator review") when the soft-max iteration still fails
6. Hard ceiling: after the 10th (hard-ceiling) iteration fails, exit code 2 with an aggregated defects report

**CRITICAL:** The visual-reviewer agent is hard-pinned to `model: opus` — this is documented in [phases/phase4-verify.md](phases/phase4-verify.md) and enforced in [scripts/render-and-verify.sh](scripts/render-and-verify.sh). It is NOT inherited from session config.

### Final Report

Upon PASS verdict:

```
Output ready:
  PDF:  file://{session_dir}/output.pdf    ({page_count} pages, {file_size_mb} MB)
  PPTX: file://{session_dir}/output.pptx   ({slide_count} slides, {file_size_mb} MB)
  Images used: {image_count} ({brand_count} from manifest, {fallback_count} from Unsplash/Pexels)
  Attributions: file://{session_dir}/ATTRIBUTION.md
  Wigum iterations: {N}
```

### Wigum Exit Codes

`wigum-loop.py` (and the Phase 4 wrapper) exit with:

- **0** — PASS. Final output copied to session root.
- **2** — Hard ceiling reached (the 10th iteration failed). Aggregated defects saved; review manually.
- **3** — `needs_agent`. render-and-verify.sh emitted a needs_agent sentinel — spawn an opus `Task` with the latest `visual-audit/iteration-NN/agent-prompt.md`, populate `visual-defects.yaml`, then resume with `--resume-from-iteration <that iteration>`.
- **4** — Soft max reached (`--max-iterations` iteration still failed). Needs operator review; re-run with a higher `--max-iterations` and `--resume-from-iteration <next>` to continue.

## Subcommands

### status

Lists all sessions under `.acos/ultimate-designer/sessions/` with `{session_id, doc_title, format, current_phase, verdict, iteration_count, created}`. Implemented inline in this protocol — read each `manifest.yaml` + `wigum.log`.

### resume [session_id]

Reads the session's `manifest.yaml` and `wigum.log`, determines last completed phase, re-enters from the next. If no `session_id` given, resumes the most recent.

### feedback

Invoked when user says "swap the image on page N". Runs:
```bash
python3 "$SKILL_DIR/scripts/record-image-feedback.py" \
  --session-id "{session_id}" --page {N} --reason "{user_reason}"
```
Then re-runs Phase 2 + Phase 3 + Phase 4 to regenerate with the rejection applied.

## Hard Constraints

1. **Zero content from loan-doc's design-library loads.** Agent prompts and scripts in this skill must NEVER read `design-library/index.yaml`, `design-patterns.yaml`, or `benchmark-criteria.yaml`.
2. **Brad's SKILL.md + tokens.css are the sole style source.** No design drift.
3. **Page-as-canvas composition.** Every page is an 8.5×11in `.page` div with `@page { size: Letter; margin: 0; }`. Not flow layout.
4. **Coffee-table rhythm.** ≥1 full-bleed photo per 3 content pages, chapter divider between parts, Cormorant italic accents on section titles, roman page numbers in "N / total" format, closing dark panel.
5. **Visual reviewer pinned to opus** — hardcoded in `render-and-verify.sh`, not session config.
6. **Wigum ceiling 5 default, 10 hard.**

## Notes

- Session isolation: sessions at `.acos/ultimate-designer/sessions/{session_id}/` never collide with parallel runs.
- Brand asset manifest lives INSIDE the asset directory as `.acos-ultimate-designer-manifest.yaml` (hidden). Users can version-control asset+manifest together.
- The skill is authored in ACOS 3.0 source and symlinked into `~/.claude/skills/`. Never edit the symlink destination directly — edit in source.
