# Phase 1 — Ingest

Run in the primary conversation. No agent spawning. This phase produces the
session manifest that all downstream agents consume.

## Inputs (from Phase 0)

- `rubric_path` — absolute path to a DOCX/PDF/XLSX rubric
- `scripts_folder` — absolute path to a directory of papers
- `total_floor`, `total_ceiling` — integer grade range
- `subject_subtype` — one of the seven specializations
- `batch_window` — default 5
- `max_iters` — default 5
- `output_path` — final XLSX destination

## Step 1.1 — Generate session ID

Compute `session_id = "grader-YYYYMMDDTHHMMSS"` (UTC). Create the session
directory:

```bash
SESSION_ID="grader-$(date -u +%Y%m%dT%H%M%S)"
SESSION_DIR=".acos/state/grader-sessions/${SESSION_ID}"
mkdir -p "${SESSION_DIR}/papers" "${SESSION_DIR}/grading" "${SESSION_DIR}/synthesis" "${SESSION_DIR}/results" "${SESSION_DIR}/audit"
```

Record the session_id — it is referenced in every subsequent step.

## Step 1.2 — Parse the rubric (heuristic first)

Dispatch to the heuristic rubric parser:

```bash
python3 .claude/scripts/grader-parse-rubric.py \
  --input "${rubric_path}" \
  --output "${SESSION_DIR}/rubric.yaml"
```

The parser extracts criteria from table-structured rubrics (XLSX cells, DOCX
tables, PDF tables via pdfplumber) and from numbered/bulleted lists with
inline point annotations (e.g., "1. Cap rate identification (10 points)").

**If the heuristic parser exits cleanly**, proceed to validation below.

## Step 1.2a — LLM fallback for prose rubrics

If the heuristic parser exits non-zero with an error like `"Could not extract
any criteria"`, spawn the `grader-rubric-parser` agent to handle the rubric
via LLM extraction. This covers rubrics that are:

- Free-form prose without tables or numbered lists
- Mixed formats (narrative context + inline criteria)
- Exported from non-standard tools with unusual structure

```
# First, extract the raw text from the source file (no structure detection)
python3 .claude/scripts/grader-ingest-paper.py \
  --input "${rubric_path}" \
  --output "${SESSION_DIR}/rubric-raw.txt"

# Then spawn the LLM parser
Task(
  subagent_type="grader-rubric-parser",
  prompt=f"""
source_file_path: {rubric_path}
extracted_text: <contents of {SESSION_DIR}/rubric-raw.txt>
declared_total_points: {total_points_if_known_else_null}
output_path: {SESSION_DIR}/rubric.yaml
schema_template_path: .claude/skills/acos-grader/templates/rubric-schema.yaml
""",
)
```

The agent produces the same rubric.yaml format as the heuristic parser. If
the agent cannot parse the rubric (output begins with `PARSE_FAILED:`),
surface the error to the user and abort Phase 1.

## Step 1.2b — Validate the rubric (regardless of source)

Once rubric.yaml exists (from either Step 1.2 or 1.2a), validate:

- `total_points` equals the sum of all `criteria[].points`
- Every criterion has non-empty `name`, `description`, and `points > 0`
- `total_floor < total_ceiling` and both ≤ `total_points`
- Every criterion id is unique

If validation fails, abort and surface the specific error. Do NOT attempt to
auto-repair the rubric — bad structure means the user needs to fix the source
file.

## Step 1.2c — Ingest questions / requirements (if provided)

If `--questions-file` was supplied (or the wizard collected a path), extract
its text using the same ingestion script used for papers:

```bash
python3 .claude/scripts/grader-ingest-paper.py \
  --input "${questions_file_path}" \
  --output "${SESSION_DIR}/questions.txt" \
  --lang eng
```

This reuses the DOCX / PDF / XLSX / image / TXT handling — including OCR for
scanned question sheets — so the user can drop in whatever form their
questions exist in.

Validate:
- Output is non-empty (exit code 0; text layer + OCR fallback should always
  produce *something* for a legitimate questions document)
- If extraction is empty, abort Phase 1 with a clear error — do NOT continue
  with no-questions fallback when the user explicitly asked for them

If `--questions-file` was NOT supplied: skip this step. `questions.txt` will
not exist; downstream agents must tolerate its absence. Graders in that
configuration receive only the rubric and paper text, as in the original
skill behavior.

Record in the manifest:
```yaml
questions:
  enabled: true
  source_path: "${questions_file_path}"
  extracted_text_path: "${SESSION_DIR}/questions.txt"
  extraction_method: "text_layer|ocr|docx|txt"   # from ingest script
  chars: <N>
```

## Step 1.3 — Inventory papers

```bash
find "${scripts_folder}" -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.txt" -o -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.tiff" \) | sort
```

For each file, derive:
- `paper_id` — filename without extension (e.g., `STUDENT_123.pdf` → `STUDENT_123`)
- `source_type` — `typed` (pdf/docx/txt with text layer) or `scan` (images, or
  pdf without text layer)

## Step 1.4 — Ingest paper text

Dispatch to the concrete ingestion script for each paper:

```bash
python3 .claude/scripts/grader-ingest-paper.py \
  --input "${paper_path}" \
  --output "${SESSION_DIR}/papers/<paper_id>.txt" \
  --lang eng
```

The script handles all formats:

- **TXT** → copied verbatim
- **DOCX** → python-docx paragraph + table extraction **plus** every embedded
  image in the body, headers, footers, and footnotes (walked via
  `doc.part.package.iter_parts()`) passed through Claude vision. Transcribed
  text is inlined as student content; any diagram description is fenced with
  `[FIGURE DESCRIPTION: ...]` so the grader can distinguish vision commentary
  from the student's own writing.
- **PDF with text layer** → PyMuPDF `page.get_text()` for typed content,
  **plus** Claude vision on every unique embedded image (deduplicated by
  `xref`) so charts, hand-drawn diagrams, spreadsheet screenshots, and
  equation images inside an otherwise-typed PDF are not silently dropped.
- **PDF scan** (text layer <100 chars total) → PyMuPDF renders each page to
  PNG at 300 DPI, then each page is passed through Claude vision and emitted
  with a `--- Page N ---` header.
- **Image** (png/jpg/jpeg/tif/tiff/bmp/webp) → Claude vision directly;
  tif/tiff/bmp are rasterized to PNG first via PyMuPDF.

The vision model is `claude-sonnet-4-6` (override with `--vision-model`).
Vision requires `ANTHROPIC_API_KEY` OR `ANTHROPIC_AUTH_TOKEN` in the
environment. If neither is set, the anthropic SDK is not installed, the API
call fails after one retry, or `--no-vision` is passed, the script falls back
to **tesseract** and prints a warning to stderr. The output carries one of
`mode=vision(N)`, `mode=vision(N)+tesseract-fallback(M)`,
`mode=tesseract-fallback(N)`, `mode=tesseract-only`, or `mode=no-images` on
the final `INGESTED ...` line so the orchestrator can log which backend ran.

### Alternate flow: Task()-based vision (no API key required)

When the user has only a Claude subscription (no API key / the subscription
token is rejected by `api.anthropic.com`), the SDK path cannot fire. Use the
Task()-based flow instead. Vision runs inside Claude Code via the
`grader-vision-ocr` agent, inheriting the user's session authentication.

Three steps per paper:

1. **Plan** — call the script in `--plan-out` mode. It extracts text and
   dumps every embedded image to a staging directory, writing a plan.json
   with an ordered assembly list (text parts + image entries). No Anthropic
   calls are made.
   ```bash
   python3 .claude/scripts/grader-ingest-paper.py \
     --input "${paper_path}" \
     --plan-out   "${SESSION_DIR}/plans/${paper_id}.json" \
     --staging-dir "${SESSION_DIR}/staging/${paper_id}/"
   ```

2. **Vision** — for each `embedded_image` / `page_image` entry in the plan,
   spawn the `grader-vision-ocr` agent via Task(). Parallelize within a
   window (e.g., 10 images in flight at a time). The agent reads the image
   and writes structured output to
   `${SESSION_DIR}/vision-results/${paper_id}/img-NNN.txt` or
   `page-NNN.txt`.

   Prompt template for each Task() call:
   ```
   image_path: <absolute path from plan>
   output_path: <results-dir>/img-NNN.txt
   context: <context string from plan>
   idx: <idx from plan>

   Read the image, then write the <transcription>...<description>... blocks
   to output_path. Final message: VISION_OCR_DONE idx=<N> output=<path>.
   ```

3. **Assemble** — call the script in `--assemble-from` mode to stitch the
   text parts with the vision outputs.
   ```bash
   python3 .claude/scripts/grader-ingest-paper.py \
     --assemble-from "${SESSION_DIR}/plans/${paper_id}.json" \
     --output "${SESSION_DIR}/papers/${paper_id}.txt" \
     --vision-results-dir "${SESSION_DIR}/vision-results/${paper_id}/"
   ```

The output file carries a `(vision-task)` tag on each `[EMBEDDED IMAGE N ...]`
header (instead of `(vision)` or `(tesseract)`), so the provenance of every
image's content is visible in the final paper text.

**When to use which flow:** prefer the direct SDK flow when an API key is
available (one subprocess per paper, fastest). Fall back to the Task()-based
flow when the only auth available is a Claude subscription. The
`--no-vision` flag remains the tesseract-only escape hatch.

A `--max-images N` flag (default 200) controls a **cost guardrail**: if a
single input contains more embedded images than the threshold, a warning is
printed to stderr (no abort). Use this to catch runaway photo-scanned exam
folders before they rack up a bill.

The script returns exit code 0 on success, 2 if the extraction produced empty
output (treat as OCR failure).

Parallelize via a Python loop — xargs's handling of per-command exit codes is
unreliable, and filename-based shell expansion creates hazards. Use the loop
below (single shell invocation, clean exit-code aggregation):

```bash
# NOTE: unquoted heredoc (<<PY, not <<'PY') so the shell expands ${SESSION_DIR}
# and ${scripts_folder} before Python sees them. There is no literal `$` in this
# body that would be wrongly expanded.
python3 - <<PY
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SESSION_DIR = Path("${SESSION_DIR}")
SOURCE_DIR  = Path("${scripts_folder}")
SUPPORTED   = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
SCRIPT      = ".claude/scripts/grader-ingest-paper.py"

papers = [p for p in SOURCE_DIR.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED]
failures, successes = [], []

def ingest_one(paper_path: Path) -> dict:
    paper_id = paper_path.stem
    output   = SESSION_DIR / "papers" / f"{paper_id}.txt"
    result = subprocess.run(
        ["python3", SCRIPT, "--input", str(paper_path), "--output", str(output)],
        capture_output=True, text=True, timeout=600,
    )
    return {
        "paper_id": paper_id,
        "source":   str(paper_path),
        "rc":       result.returncode,
        "stderr":   result.stderr.strip()[-500:],
    }

with ThreadPoolExecutor(max_workers=4) as pool:
    for future in as_completed([pool.submit(ingest_one, p) for p in papers]):
        r = future.result()
        (successes if r["rc"] == 0 else failures).append(r)

(SESSION_DIR / "audit").mkdir(parents=True, exist_ok=True)
(SESSION_DIR / "audit" / "ingest-failures.yaml").write_text(
    "failures:\n" + "\n".join(
        f"  - paper_id: {f['paper_id']}\n    rc: {f['rc']}\n    stderr: {json.dumps(f['stderr'])}"
        for f in failures
    ) + "\n"
)
print(f"Ingested {len(successes)} OK, {len(failures)} failed.")
PY
```

### Updating manifest status per paper

For EVERY paper in the manifest, set its `status` field based on ingest result:

- Exit code 0 → `status: ingested`
- Exit code 2 (empty text produced) → `status: ocr_failed`
- Any other non-zero → `status: ingest_error`
- Timeout / exception → `status: ingest_error`

**Phase 2 MUST skip any paper whose status is not `ingested`.** Skipped papers
appear in the cohort summary as UNGRADED with the failure reason. Do not
dispatch grader agents on papers with empty or missing text — doing so causes
graders to award floor scores on non-existent content, producing fake grades
indistinguishable from real ones.

### System dependencies

- **anthropic** (Python SDK) — for Claude vision OCR. Install via
  `pip install anthropic`. Accepts either of two env vars:
  - `ANTHROPIC_API_KEY` — standard API account (x-api-key header, per-token billing)
  - `ANTHROPIC_AUTH_TOKEN` — Claude subscription bearer token. Generate via
    `claude setup-token` (requires Max / Pro / Team subscription). Uses
    subscription quota, no separate API billing.

  If both are set, the subscription token wins. **Optional but strongly
  recommended** — without either, the script silently falls back to tesseract
  and loses all embedded-image content interpretation (graders will only see
  typed text and bare OCR character strings, not diagram structure).
- **tesseract** (system binary) — already present at `/opt/homebrew/bin/tesseract`
  on this system (macOS/Homebrew). On Linux: `apt-get install tesseract-ocr`.
  Acts as the fallback path.
- **PyMuPDF** (Python, imported as `fitz`) — already present. Handles PDF
  parsing, page rasterization, and exotic-format image conversion (TIFF, BMP,
  JPX → PNG) for vision payloads.
- **python-docx** — required; install via `pip install python-docx` if missing.

No `pytesseract`, `pdf2image`, or `poppler` needed — tesseract is invoked via
subprocess and PyMuPDF does its own rendering.

## Step 1.5 — Derive per-criterion ranges

For each criterion in the rubric:

```python
criterion_floor   = (total_floor   / total_points) * criterion_points
criterion_ceiling = (total_ceiling / total_points) * criterion_points

# Round to 0.5-point increments
criterion_floor   = round(criterion_floor   * 2) / 2
criterion_ceiling = round(criterion_ceiling * 2) / 2
```

Store derived bounds in the session manifest per criterion.

## Step 1.6 — Write the session manifest

Populate `templates/session-manifest.yaml` with all inputs, paper inventory,
derived criterion bounds, and configuration. Write to
`${SESSION_DIR}/manifest.yaml`.

## Step 1.7 — Confirm with user

Present a summary:

```
Session: grader-20261018T143000
Rubric: fall-2026-portfolio-theory-rubric.docx
  └ 8 criteria, 100 total points
Papers: 47 inventoried, 47 ingested, 0 failed
Grade range: 70–90 (per-criterion ranges derived pro-rata)
Subject: Investment Management
Batch window: 5 papers in flight
Max iterations per criterion: 5
Target curve: mean=80, stdev=5 (z-score rescale)
Output: ~/exams/fall-2026/grades.xlsx

Proceed to grading? (y/n)
```

Wait for user confirmation. On `y`, proceed to Phase 2. On `n`, halt — session
state is preserved and can be resumed later.

## Post-conditions

- Session directory populated with rubric.yaml, papers/, and manifest.yaml
- All papers ingested OR failures logged
- User has confirmed readiness to proceed

Phase 2 consumes `${SESSION_DIR}/manifest.yaml` as its only input.
