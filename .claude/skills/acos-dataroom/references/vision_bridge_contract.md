# Vision Bridge — Request/Response Contract

The acos-dataroom skill does NOT call the Anthropic API directly from Python.
Instead, `scripts/ocr_and_vision.py` writes vision requests to a bridge
directory under the run, and the orchestrating Claude Code session fulfills
them by spawning a vision-capable `Task()` sub-agent for each request. This
routes vision through the user's Claude Code subscription rather than a
separately-billed API key.

This document defines the on-disk contract.

## Directory layout

All bridge artifacts live under:

    <run_dir>/intermediate/vision_bridge/

with these subdirectories:

| Subdirectory   | Written by    | Contents                                       |
|----------------|---------------|------------------------------------------------|
| `requests/`    | the script    | One JSON manifest per pending vision request   |
| `images/`      | the script    | The PNG to be analyzed (referenced by request) |
| `responses/`   | orchestrator  | Fulfilled response JSON                        |
| `fulfilled/`   | the script    | Archive of processed responses after rehydrate |

The script never reads from `responses/`. The orchestrator never writes to
`requests/` or `images/`. There is no shared mutable state besides the
files themselves.

## Request manifest schema

```json
{
  "schema_version": "1.0",
  "request_id": "req_<file_id>_p<page_number>",
  "file_id": "f_<12hex>",
  "page_number": 3,
  "image_path": "<absolute path to PNG in images/>",
  "trigger_reason": "ocr_confidence_below_threshold | native_extraction_empty | standalone_image",
  "ocr_confidence": 0.62,
  "ocr_text": "<best-effort OCR transcription>",
  "char_count_native": 0,
  "prompt": "<full VISION_PROMPT — copied in case the orchestrator wants to inspect>",
  "expected_schema": { ... shape the response must match ... },
  "model_hint": "claude-opus-4-7",
  "created_at": "2026-05-11T12:34:56Z",
  "status": "pending"
}
```

The `request_id` is also the filename (sans `.json`). The orchestrator's
fulfillment path is purely path-based: read the request, run the prompt
against the referenced image, write the response.

## Response schema

```json
{
  "request_id": "req_<file_id>_p<page_number>",
  "fulfilled_at": "2026-05-11T12:35:30Z",
  "fulfilled_by": "main-thread-task | manual | <agent-name>",
  "model": "claude-opus-4-7",

  "document_type": "<your guess>",
  "extracted_text": "<full transcription with [handwritten:...], [stamped:...], [signature:...], [illegible] markers>",
  "visual_elements": ["element 1", "element 2"],
  "critical_fields": {
    "dates": [],
    "parties": [],
    "monetary_amounts": [],
    "addresses": [],
    "signatures": [{"who": "...", "location": "...", "present": true}],
    "instrument_numbers": []
  },
  "privacy_flags": [],
  "confidence_self_assessment": 0.0,
  "notes": ""
}
```

The response filename MUST be `res_<file_id>_p<page_number>.json` (replace
the `req_` prefix with `res_`). The script's rehydrate step uses this
naming convention to locate the right page in the right extraction record.

## Orchestrator fulfillment recipe

For each pending request file in `vision_bridge/requests/`:

1. Read the request JSON; extract `image_path` and `prompt`.
2. Spawn a vision-capable sub-agent via `Task()` (Sonnet or Opus). Pass the
   image path + prompt + expected schema. The sub-agent runs inside Claude
   Code, so it inherits the user's session — no API key needed.
3. The sub-agent's final output should be the strict JSON described in
   "Response schema" above.
4. Write that JSON to `vision_bridge/responses/res_<file_id>_p<page>.json`.
5. (Optional) Remove the request file. If left in place, it is harmless —
   the script never resends a request whose status is already in the
   pages array as fulfilled.

Multiple requests can be fulfilled in parallel by spawning several Task()
agents simultaneously and writing their outputs to distinct response files.

## Script behavior

`ocr_and_vision.py --vision-mode batch` (default): writes requests and
returns immediately. The page's `vision_supplement.status` is `pending`.

`ocr_and_vision.py --vision-mode blocking`: same as batch, then polls the
response path every 2 seconds for up to `--vision-timeout-seconds`
(default 300). Use only when you know the orchestrator is going to fulfill
the request synchronously.

`ocr_and_vision.py --vision-mode skip`: do not write requests. The page's
`vision_supplement.status` is `skipped`. Useful for OCR-only smoke runs.

`ocr_and_vision.py --rehydrate --run-dir <run>`: walks
`vision_bridge/responses/`, merges each response into the corresponding
`extraction.json` page record, and archives the response file into
`vision_bridge/fulfilled/`. Idempotent — safe to re-run after additional
responses arrive.

## Failure modes

| Failure                        | Where surfaced                              | Recovery                                                          |
|--------------------------------|---------------------------------------------|-------------------------------------------------------------------|
| Orchestrator never fulfills    | `vision_supplement.status = "pending"`      | Re-run skill flow; orchestrator picks up pending requests.        |
| Blocking mode timeout          | `vision_supplement.status = "timeout"`      | Run `--rehydrate` after the response lands.                       |
| Response file malformed JSON   | `vision_supplement.status = "pending"`      | Rehydrate skips the file with a warning; orchestrator must re-fulfill. |
| Response contains `error` key  | `vision_supplement.status = "error"`        | QA report surfaces; boss decides re-run or omit per vision_fallback. |
| Image renderer unavailable     | `page_record.notes` includes `needs_fallback_but_no_renderer_available` | Install pdf2image or PyMuPDF, re-run augment. |

## Why a bridge, not an inline subprocess

Earlier versions of this skill called the Anthropic SDK directly with an
`ANTHROPIC_API_KEY` env var. That worked but billed to a separate
metered API account, defeating the user's Claude Code Max subscription. The
bridge inverts control: Python prepares the work, Claude Code drives the
fulfillment. The same pattern is used in `acos-grader` for the
`grader-vision-ocr` agent.
