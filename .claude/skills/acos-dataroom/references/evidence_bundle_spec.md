# Evidence Bundle Specification

The evidence bundle is the **spine of the no-hallucination guarantee**. Every
claim in the Excel guide must be traceable to a snippet in the corresponding
evidence bundle.

## Location

`<run_dir>/evidence/<file_id>.json` — one bundle per processed file.

## JSON Schema

```jsonc
{
  "file_id": "f_a3f7b2c19e0d",
  "schema_version": "1.0",
  "source": {
    "path": "/path/to/source/file.pdf",
    "name": "Loan_Agreement_Signed.pdf",
    "sha256": "a3f7b2c19e0d...",
    "size_bytes": 1234567,
    "modified_date": "2024-08-15T14:32:11Z",
    "extension": ".pdf"
  },
  "extraction": {
    "methods_used": ["native_pdf", "ocr_page_3", "vision_page_3"],
    "library_versions": {
      "pypdf": "4.2.0",
      "pdfplumber": "0.11.0",
      "pytesseract": "0.3.10"
    },
    "pages": [
      {
        "page_number": 1,
        "method": "native_pdf",
        "char_count": 2147,
        "text": "<full extracted text>",
        "confidence": 1.0
      },
      {
        "page_number": 3,
        "method": "ocr",
        "char_count": 612,
        "text": "<OCR'd text>",
        "confidence": 0.62,
        "vision_supplement": {
          "method": "claude_vision",
          "model": "claude-opus-4-7",
          "rendered_at": "2026-05-06T15:14:22Z",
          "description": "<vision narrative>",
          "extracted_text": "<text vision recovered>",
          "visual_elements": ["signature_block_lower_right", "embossed_seal", "handwritten_date"]
        }
      }
    ]
  },
  "classification": {
    "category": "loan_documents",
    "subcategory": "executed_note",
    "confidence": 0.94,
    "reasoning": "<paragraph explaining why this category was chosen>",
    "snippets_supporting": [
      {"page": 1, "text": "PROMISSORY NOTE", "char_range": [0, 16]},
      {"page": 1, "text": "Borrower promises to pay to the order of Lender", "char_range": [142, 188]}
    ],
    "alternatives_considered": [
      {"category": "loan_documents", "subcategory": "loan_agreement", "confidence": 0.41, "rejected_because": "Document title and structure match a Note, not an Agreement; lacks recitals and covenants sections."}
    ]
  },
  "summary": {
    "brief": "Promissory Note dated 2024-08-15 from BorrowerCo LLC to OKOA Capital for $4,500,000 at 11.5% interest, maturing 2026-08-15.",
    "detailed": "<one-paragraph summary>",
    "claims": [
      {
        "claim": "Note amount is $4,500,000",
        "snippet": {"page": 1, "text": "principal sum of FOUR MILLION FIVE HUNDRED THOUSAND DOLLARS ($4,500,000)", "char_range": [301, 376]}
      },
      {
        "claim": "Interest rate is 11.5% per annum",
        "snippet": {"page": 1, "text": "interest at the rate of eleven and one-half percent (11.5%) per annum", "char_range": [432, 502]}
      },
      {
        "claim": "Maturity date is 2026-08-15",
        "snippet": {"page": 2, "text": "Maturity Date: August 15, 2026", "char_range": [88, 119]}
      }
    ],
    "unable_to_verify": []
  },
  "extracted_data": {
    "key_entities": ["BorrowerCo LLC", "OKOA Capital", "John Q. Borrower (guarantor)"],
    "key_dates": [
      {"date": "2024-08-15", "label": "execution_date", "page": 1},
      {"date": "2026-08-15", "label": "maturity_date", "page": 2}
    ],
    "monetary_amounts": [
      {"amount": 4500000, "currency": "USD", "label": "principal", "page": 1}
    ],
    "document_date": "2024-08-15",
    "document_status": "executed"
  },
  "sensitivity": {
    "level": "high",
    "reasons": ["contains_borrower_ssn_pattern_on_page_3", "contains_wire_instructions_page_4"],
    "redaction_recommended": true,
    "redaction_targets": [
      {"page": 3, "type": "ssn", "approximate_location": "lower_third"},
      {"page": 4, "type": "wire_instructions", "approximate_location": "section_4.2"}
    ]
  },
  "external_room_recommendation": {
    "value": "include_after_redaction",
    "reasoning": "Core enforceability document — must be in the room. Contains PII (SSN) and wire details that need redaction before external sharing."
  },
  "qa_flags": []
}
```

## The No-Hallucination Rule (Enforced)

Every entry in `summary.claims` MUST cite a snippet that exists in the
extraction `pages[].text`. The skill verifies this via **layered matching**
in `scripts/verify_no_hallucination.py`:

| Layer | Check | Confidence |
|---|---|---:|
| 1. Verbatim | `snippet.text` is a verbatim substring of the source | 1.00 |
| 2. Whitespace-normalized | matches after collapsing whitespace | 0.97 |
| 3. Format-normalized | matches after stripping currency symbols, commas, decorative punctuation, casing | 0.92 |
| 4. Paraphrase-likely | ≥80% of *claim* tokens appear in source AND every number in the claim appears in the source | 0.70–0.90 |
| Fail: number_mismatch | claim contains numbers not in source (strong hallucination signal) | 0.00 |
| Fail: low_token_overlap | <80% of claim tokens in source | 0.00 |

A claim that fails all layers either:
- Goes into `summary.unable_to_verify[]` with the failure layer + missing tokens / numbers, AND the corresponding cell in the workbook reads `"Unable to verify — see evidence bundle"`.
- OR is removed from the summary before the bundle is finalized.

**Snippet authoring rules (for the classification agent):**

When backing a factual claim, **prefer verbatim source snippets**. If a
verbatim snippet would be misleading without context, you may paraphrase the
claim text — but the `snippet.text` field MUST remain as-extracted from the
source. Never reformat numbers (`11500000` stays as `11500000`; do NOT
substitute `$11,500,000`). Never expand abbreviations in the snippet (`Orig
Fee` stays `Orig Fee`; the claim text can read "origination fee").

The verifier's Layer 3 catches currency reformatting and Layer 4 catches
paraphrasing — but agents that emit verbatim snippets at Layer 1 produce
the highest-confidence audit trail.

**Number-mismatch is the strongest hallucination signal.** A claim that cites
a number (case number, dollar amount, date) which does not appear in the
source extraction text is treated as unverified at confidence 0.00. There is
no "soft" path — numbers either match or the claim is rejected. This guards
against the failure mode where an agent confidently invents specifics
(case numbers, account numbers, dates) that "sound right" for the document
type but aren't actually present.

## Hyperlinking

The Excel guide hyperlinks each row's `evidence_bundle_link` to the local
`<run_dir>/evidence/<file_id>.json` file. Boss can click through to inspect
the snippet trail.

## When Vision is Used

A bundle whose `extraction.methods_used` contains any `vision_*` method is
flagged in QA Pass #4. Reviewers should expect:

- `vision_supplement.description` — narrative description of what's visible.
- `vision_supplement.extracted_text` — text the vision model recovered (may overlap with OCR; both are kept).
- `vision_supplement.visual_elements` — list of structural cues (signatures, seals, stamps, handwriting, charts).

## Bundle Versioning

`schema_version: "1.0"` — bumped on any breaking change to the bundle
structure. The `validate-guide` script refuses to process bundles with
unrecognized schema versions.
