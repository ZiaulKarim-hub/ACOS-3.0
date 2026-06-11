# Phase 0 — Wizard

## Purpose
Collect user inputs, establish session workspace, write session manifest.

## Flow

### Step 1 — Mode selection

Use `AskUserQuestion`:

> Question: "Which wizard mode?"
> Options:
> - "Quick (3 prompts)" — content path, output format, brand-asset path
> - "Detailed (6 prompts)" — adds document type, special instructions, iteration ceiling

### Step 2 — Quick prompts (always run)

**Prompt 2.1 — Content source path** (text input):
> "Path to your content file (YAML or markdown)?"

Validation: file exists, extension in `{.yaml, .yml, .md}`. If invalid, re-prompt with error.

**Prompt 2.2 — Output format** (`AskUserQuestion`):
> "Which output format?"
> Options: `pdf`, `pptx`, `both`

**Prompt 2.3 — Brand-asset directory path** (text input, may be empty):
> "Path to your brand-asset directory (or leave empty for Unsplash/Pexels only)?"

Validation: if non-empty, directory must exist.

### Step 3 — Detailed prompts (only if Detailed mode)

**Prompt 3.1 — Document type** (`AskUserQuestion`):
> "Document type?"
> Options: `editorial` (magazine-style), `technical` (structured, dense), `executive` (short, summary-focused)

**Prompt 3.2 — Special instructions** (text input, optional):
> "Any special instructions? (e.g., 'use dark cover', 'emphasize growth', or leave empty)"

**Prompt 3.3 — Iteration ceiling** (text input, optional):
> "Wigum max iterations? (default 5)"

Validation: integer 1–10.

### Step 4 — Derive session ID + directory

> `SKILL_DIR` below is the repo-absolute skill path; set it the same way as the
> other phase blocks (`.claude/skills/acos-ultimate-designer` when running inline).

```bash
SKILL_DIR=".claude/skills/acos-ultimate-designer"
SESSION_ID="$(date +%Y%m%d-%H%M%S)-$(SKILL_DIR="$SKILL_DIR" python3 -c "
import os, re, importlib.util
from pathlib import Path

content_path = Path('{content_path}')
title = 'doc'
try:
    # Reuse decompose-content.py's load_content so markdown front-matter titles
    # are honored (not just .yaml/.yml). Falls back to the file stem / 'doc'.
    spec = importlib.util.spec_from_file_location(
        'decompose_content',
        Path(os.environ['SKILL_DIR']) / 'scripts' / 'decompose-content.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    data = mod.load_content(content_path)
    if isinstance(data, dict):
        title = data.get('title') or content_path.stem or 'doc'
except Exception:
    title = content_path.stem or 'doc'

slug = re.sub(r'[^a-z0-9-]', '-', str(title).lower()).strip('-')[:40]
print(slug or 'doc')
")"

SESSION_DIR=".acos/ultimate-designer/sessions/$SESSION_ID"
mkdir -p "$SESSION_DIR"/{phase1,phase2,phase3,visual-audit}
```

### Step 5 — Write session manifest

```yaml
# {SESSION_DIR}/manifest.yaml
session_id: "{SESSION_ID}"
created: "{iso8601_timestamp}"
mode: "quick" | "detailed"

inputs:
  content_path: "{absolute_path}"
  output_format: "pdf" | "pptx" | "both"
  asset_dir: "{absolute_path_or_null}"
  doc_type: "editorial" | "technical" | "executive" | null
  special_instructions: "{user_text_or_null}"
  iteration_ceiling: 5

status:
  current_phase: "phase0_complete"
  last_updated: "{iso8601_timestamp}"
```

### Step 6 — Echo plan

Print a summary of collected inputs and what happens next. Use clickable `file://` links to the content file and session dir.

## Output

- `{SESSION_DIR}/manifest.yaml` (session manifest)
- Session directory structure under `.acos/ultimate-designer/sessions/{session_id}/`

## Next Phase

Proceed to `phase1-html.md` with `{session_id}` and `{manifest.yaml}` available.
