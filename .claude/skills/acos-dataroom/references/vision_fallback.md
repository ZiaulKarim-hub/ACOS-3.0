# Vision Fallback — When and How

Vision is **mandatory, not optional** for any document the skill cannot read
through native extraction or high-confidence OCR. A loan-critical document
must never be invisible to the skill because OCR failed.

---

## When Vision Fires

Vision is triggered when ANY of the following is true for a page or image:

1. **Native extraction returned zero text** AND the file has any visual content.
2. **OCR confidence on the page is below `0.70`** (configurable: `ocr_confidence_threshold`).
3. **The file is a standalone image** (always vision, regardless of OCR result).
4. **The page contains visible non-text elements** that matter for classification: signatures, embossed seals, notary stamps, recording stamps, handwritten dates, redaction blocks. Heuristic detection: if the page image has > 5% area as non-text-character pixels in the lower third (signature zone) or contains stamp-like shapes.
5. **The file is image-heavy by structure** — e.g., PowerPoint with embedded charts/photos, Word with > 50% image area.

The skill records *why* vision fired in `vision_supplement.trigger_reason`.

---

## Vision Prompt Template

When the skill calls Claude vision on a rendered page or image, it uses:

```
You are a document analysis assistant. The image below is a single page (or
standalone image) from a document being processed for an outbound diligence
data room. The OCR confidence on this page was [confidence] and/or native text
extraction returned [N] characters.

Your job is to recover content and structure that pure text extraction may
have missed. Specifically:

1. **Document type** — what is this page (e.g., signature page of a promissory
   note, recorded deed of trust, internal memo, photograph of property,
   handwritten ledger)?

2. **All visible text** — transcribe every legible word, including handwriting,
   stamps, seals, page numbers, headers, footers, and marginalia. Use clear
   formatting:
   - Use `[handwritten: ...]` for handwriting.
   - Use `[stamped: ...]` for stamps and seals.
   - Use `[signature: ...]` for signature blocks (describe whose, if known).
   - Use `[illegible]` for content you cannot read.

3. **Visual elements** — list structural cues that aren't text:
   - Signature blocks (who signed, location on page)
   - Embossed seals or notary stamps
   - Recording stamps (county, date, instrument number)
   - Redaction blocks (and their approximate location)
   - Handwritten annotations
   - Logos / letterheads
   - Charts, graphs, photos (briefly describe)

4. **Critical fields** — call out anything that matters for diligence:
   - Dates (execution, recording, expiration, etc.)
   - Parties (lender, borrower, guarantor, trustee, beneficiary)
   - Monetary amounts
   - Property addresses or legal descriptions
   - Loan / instrument numbers
   - Signatures present vs. blanks

5. **Privacy flags** — note any visible PII (SSN, EIN, account numbers, wire
   instructions). Do NOT redact in your response — flag for the skill to
   handle.

Return your analysis as structured JSON matching this schema:

{
  "document_type": "<your guess>",
  "extracted_text": "<full transcription>",
  "visual_elements": ["<element 1>", "<element 2>", ...],
  "critical_fields": {
    "dates": [...],
    "parties": [...],
    "monetary_amounts": [...],
    "addresses": [...],
    "signatures": [{"who": "...", "location": "...", "present": true|false}],
    "instrument_numbers": [...]
  },
  "privacy_flags": ["<flag 1>", "<flag 2>"],
  "confidence_self_assessment": <0.0–1.0>,
  "notes": "<anything else worth knowing>"
}
```

---

## Vision + OCR Reconciliation

When both OCR and vision run on the same page, the evidence bundle keeps
**both outputs separately**:

```json
"pages": [{
  "page_number": 3,
  "method": "ocr",
  "text": "<OCR output>",
  "confidence": 0.62,
  "vision_supplement": {
    "method": "claude_vision",
    "model": "claude-opus-4-7",
    "trigger_reason": "ocr_confidence_below_threshold",
    "extracted_text": "<vision output>",
    "visual_elements": [...],
    "critical_fields": {...}
  }
}]
```

The skill **does not merge** OCR text and vision text into a single string.
Downstream classification and summarization read both. If they conflict on a
specific value (e.g., "$4,500,000" in OCR vs. "$4,000,000" in vision), the
conflict is flagged and the file gets `qa_status: review_required`.

---

## Vision Cost Considerations

Vision calls are billable. The skill respects:

- A `--max-vision-calls` flag (default: 200 per run). If exceeded, remaining
  pages are processed OCR-only and flagged `vision_skipped_quota_exceeded`.
- Caching: identical page hashes (after rendering) reuse prior vision results
  within a run.
- The boss can override: `--force-vision <file_id>` runs vision on a specific
  file even if it didn't trigger naturally.

Cost note: as of v1.1.0, vision is dispatched via the bridge (see
`vision_bridge_contract.md`), so calls bill through the user's Claude Code
subscription rather than a separately-metered Anthropic API account.

---

## Dispatch (v1.1.0+)

`ocr_and_vision.py` does NOT call the Anthropic SDK. It writes a request
manifest plus a rendered PNG to `<run_dir>/intermediate/vision_bridge/`,
marks the page `vision_supplement.status = "pending"`, and returns.

The orchestrating Claude Code session reads pending requests, spawns a
vision-capable `Task()` sub-agent for each, and writes structured JSON
responses to `vision_bridge/responses/`. Then `ocr_and_vision.py
--rehydrate --run-dir <run>` merges the responses into each
`extraction.json`.

Full schema in `references/vision_bridge_contract.md`.

---

## When Vision Fails

If a vision call returns an error (rate limit, content policy, network):

1. The response file contains an `error` key; rehydrate marks the page
   `vision_supplement.status = "error"`.
2. The page is flagged `vision_failed` in `qa_flags` and the file gets
   `qa_status: review_required`.
3. The skill does NOT skip the file silently. It surfaces the failure in the
   QA report so the boss can decide whether to re-run, manually review, or
   omit.
