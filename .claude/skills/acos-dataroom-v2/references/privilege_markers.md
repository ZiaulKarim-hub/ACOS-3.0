# Privileged Content Markers — Reference for Phase 2.5 Scanners

**Audience:** the three `privilege-scanner` agents (Phase 2.5).
**Purpose:** comprehensive catalog of markers indicating privileged or otherwise
sensitive content that MUST NOT ship to an outbound dataroom buyer.

**Scanner mandate:** read the file's full extracted text + vision summary, and
issue **KEEP** (no privilege detected) or **FLAG** (privilege detected) with
specific reasoning citing which marker(s) triggered.

**Consensus rule reminder:** Phase 2.5 is ASYMMETRIC. Three scanners run blind;
**any single FLAG removes the file** from the dataroom. There is no
re-dispatch on FLAG. False positives are recoverable (operator can manually
override later); false negatives are catastrophic (privilege waiver,
litigation exposure, malpractice liability).

**Posture:** when in doubt, FLAG. The asymmetric-harm calculus makes
flagging the safe default.

---

## 1. Attorney-Client Privilege Markers

### 1.1 Header / footer / cover-page markers (HARD — pattern-detectable)

Any document carrying ANY of these markings is presumptively privileged:

- `Privileged & Confidential` / `Privileged and Confidential`
- `Attorney-Client Privileged` / `Attorney/Client Privileged`
- `Attorney-Client Communication`
- `Subject to Attorney-Client Privilege`
- `Privileged — Subject to Common Interest Doctrine`
- `Confidential — Attorney-Client Privileged`
- `Privileged: Litigation Strategy`
- `Do Not Distribute — Privileged`

These markings frequently appear in:
- Page headers / footers (every page)
- Cover sheets / cover memos
- Email subject lines (e.g., "Privileged & Confidential — RE: …")
- Email metadata visible in printed/saved emails

If you see ANY of these phrases anywhere in the document, FLAG.

### 1.2 Attorney-as-party communications (SEMANTIC — judgment required)

Communications between OKOA and its legal counsel, OR between OKOA principals
discussing legal advice received, are privileged regardless of header markings.

Signs to flag:
- Letterhead or signature block of a law firm (e.g., "Latham & Watkins LLP,"
  "Snell & Wilmer LLP," "Kirkland & Ellis LLP," "Holland & Knight LLP," any
  ".law" or "@firm.com" email domains)
- Attorney signature line (e.g., "John Smith, Esq.," "Jane Doe, Partner")
- Counsel writing TO the borrower / OKOA / OKOA principals about legal
  matters
- OKOA principal writing TO counsel asking for legal advice
- Counsel-to-counsel communications about an OKOA matter

**Important nuance:** a transactional document drafted BY counsel (loan
agreement, note, deed of trust, security agreement) is NOT privileged just
because counsel drafted it. The drafting attorney's work was to produce a
document intended for third-party execution / recording. These are
**transactional work product**, distinct from privileged communications.
Keep them.

The privilege attaches to communications ABOUT the transaction, not the
transactional documents themselves.

---

## 2. Attorney Work Product Doctrine Markers

The work-product doctrine (Federal Rule of Civil Procedure 26(b)(3))
protects materials prepared by attorneys "in anticipation of litigation."

### 2.1 Hard-pattern markers

- `Attorney Work Product` / `Work Product`
- `Prepared in Anticipation of Litigation`
- `Litigation Work Product`
- `Attorney Work Product — Do Not Disclose`

### 2.2 Semantic markers

Documents prepared by or at the direction of counsel analyzing legal
exposure, litigation strategy, or trial preparation:

- Litigation case memoranda (e.g., "Memo: Wolfgramm v. OKOA — Strategy")
- Witness interview memos / debriefs
- Mock-trial summaries / mooting notes
- Damages-model spreadsheets prepared by counsel
- Settlement valuation analyses prepared for client
- Trial preparation materials (witness outlines, exhibit lists from
  litigation work)

FLAG if the document analyzes a legal dispute, names opposing parties, and
appears to be prepared FOR OKOA's benefit in that dispute.

---

## 3. Settlement Negotiation Materials (FRE 408)

Federal Rule of Evidence 408 protects settlement communications. While
technically not "privileged" in the attorney-client sense, settlement
materials are similarly excluded from outbound disclosure because:
(a) admitting them in subsequent litigation is barred,
(b) sharing them with a third party (buyer) may waive the protection.

### 3.1 Hard-pattern markers

- `Settlement Communication — FRE 408`
- `Subject to Rule 408 Privilege`
- `For Settlement Purposes Only`
- `Without Prejudice`
- `Inadmissible Under FRE 408`

### 3.2 Semantic markers

- Pre-execution settlement drafts / red-lines
- Mediator's settlement proposals (mediator privilege also applies)
- Offer / demand exchanges marked "for settlement purposes"
- Internal valuations of settlement positions
- Confidential mediation briefs
- "Term sheet" labeled documents in active litigation

**Important nuance:** an EXECUTED settlement agreement is generally
disclosable (and OKOA's Ascent Phase 7c flagged the 2025-04-23 and
2025-05-14 settlement agreements as expected to ship). The privilege
attaches to the NEGOTIATION materials, not the final executed agreement.

FLAG: pre-execution drafts, internal valuation memos, mediator communications.
KEEP: fully executed settlement agreements (with the counterparty acknowledging
they exist).

---

## 4. Internal Legal Memos & Analyses

Memos from in-house or outside counsel analyzing legal questions for OKOA's
internal use. These are core attorney-client privilege material.

### 4.1 Semantic markers

- Memos titled "Legal Analysis of …," "Re: [matter] — Legal Risk
  Assessment," "Memo to [OKOA principal] re Legal Position"
- Sections labeled "Legal Conclusion," "Privileged Analysis," "Risk
  Assessment for Internal Use"
- Analyses comparing alternative legal strategies
- Discussion of statutes / case law applied to OKOA's specific situation
- Recommendations to OKOA principals about legal actions to take

If the document's purpose is for OKOA to receive legal advice or assessment,
FLAG.

---

## 5. Discovery & Litigation Production Materials

Materials produced or received in a litigation context.

### 5.1 Hard-pattern markers

- Bates stamps (e.g., `OKOA-000123`, `LK-CAP-000456`) on every page
- `Confidential — Subject to Protective Order`
- `Highly Confidential — Attorney's Eyes Only`
- `Subject to Stipulated Protective Order`
- Production cover sheets ("Document Production — Case No. …")

### 5.2 Semantic markers

- Deposition transcripts (typically formatted with line numbers, witness Q/A)
- Interrogatory responses
- Document request responses
- Privilege logs
- Discovery production cover letters from opposing counsel

FLAG any document that appears to be part of a litigation discovery
production — these typically came to OKOA under a protective order that
prohibits onward disclosure.

---

## 6. Outside-Counsel Invoices & Bills

Invoices from law firms to OKOA often contain detailed time-entry
descriptions that disclose the matters counsel was working on. These
descriptions are themselves privileged.

### 6.1 Markers

- Law-firm letterhead invoice with itemized time entries
- Phrases like "Reviewed [document] re [legal matter]"
- "Drafted memo re [legal strategy]"
- "Conference with [client/principal] re [legal advice]"
- "Researched [legal question]"

FLAG: any invoice with substantive time-entry descriptions.
KEEP: redacted invoices with only dollar amounts (operator would need to
manually redact and re-add — out of scope for autonomous v2).

---

## 7. Internal Strategy / Deliberation Materials

Even without attorney involvement, internal OKOA strategy memos analyzing
how to position the deal, what to disclose, what NOT to disclose to a
buyer, are sensitive and typically excluded from outbound diligence.

### 7.1 Semantic markers

- Internal memos titled "Strategy for [Deal]," "Disclosure Position,"
  "Negotiation Posture"
- Discussion of asking price floor vs. ceiling
- Analysis of why a particular issue should NOT be highlighted to buyers
- Internal valuation memos showing reservation prices
- Email threads among OKOA principals deliberating disclosure choices

This category overlaps with v1's `internal_only_strategic` classification.
v2 Phase 2 deliberation agents should typically catch these for relevance,
but Phase 2.5 scanners FLAG them additionally as a safety net.

---

## 8. Personally Identifiable Information (PII) — Severe

PII that has not been redacted is not "privileged" but is similarly
catastrophic to leak. PII handling in v2:

### 8.1 Hard-pattern markers (HIGH severity — FLAG)

- Social Security numbers (pattern: `XXX-XX-XXXX` or `XXXXXXXXX` in
  context suggesting SSN)
- Bank account numbers (long numeric strings in financial context)
- Wire transfer instructions with routing + account numbers
- Credit card numbers (16-digit patterns)
- Driver's license numbers
- Passport numbers
- Date of birth combined with full name

### 8.2 Lower-severity PII (judgment — typically KEEP unless prominent)

- Names + addresses (standard contact info, generally OK)
- Phone numbers (generally OK)
- Email addresses (generally OK)

**Decision rule:** if a document's PRIMARY content is high-severity PII
(e.g., a wire-instructions sheet, an SSN form, a bank-statement page
showing account numbers), FLAG. If high-severity PII is incidental (one
SSN buried in a 50-page contract), document the location in reasoning but
still typically FLAG — redaction is the right path, not inclusion.

---

## 9. Markers That Are NOT Privilege Triggers

Common false-positives to AVOID flagging on:

- "Confidential" alone (without "privileged" or "attorney") — most
  business documents are confidential; this is not privilege.
- "Internal" — internal documents are not categorically privileged. Many
  internal docs (e.g., operating financials, capex plans) belong in a
  dataroom.
- Boilerplate confidentiality disclaimers in email footers — these claim
  privilege over EVERY email but are not legally controlling. Look at the
  CONTENT, not the boilerplate.
- "Sensitive" — too vague to be a privilege marker.
- An attorney's name appearing in a CC list of a transactional email —
  not enough on its own to trigger privilege. The attorney must be giving
  or receiving legal advice on the matter for privilege to attach.

---

## 10. Decision Format

Each scanner's output (per file) MUST be a JSON object:

```json
{
  "verdict": "KEEP" | "FLAG",
  "triggered_markers": ["1.1: 'Privileged & Confidential' header", "..."],
  "reasoning": "<paragraph explaining the decision>",
  "confidence": 0.0-1.0,
  "evidence_snippets": ["<verbatim excerpt 1>", "<verbatim excerpt 2>"]
}
```

If `verdict: "FLAG"`, `triggered_markers` MUST be non-empty.
If `verdict: "KEEP"`, `triggered_markers` SHOULD be empty (or may list false-positive considerations rejected).

`evidence_snippets` MUST be verbatim from the source document. Do not paraphrase. Do not normalize numbers. Preserve original formatting / abbreviations.

---

## 11. Final reminder

**Asymmetric harm calculus:** missing a privileged doc = potential malpractice
suit + privilege waiver across the entire matter. Falsely flagging a
non-privileged doc = the file goes to manual-review bucket and the operator
can review it.

**Therefore: when in doubt, FLAG.**

Better to surface 5 files for manual review than to leak 1 privileged communication.

---

*References: Federal Rules of Civil Procedure 26(b)(3) (work product), Federal Rules of Evidence 408 (settlement negotiations), 502 (privilege waiver), state-law attorney-client privilege as embedded in California Evidence Code §952 and similar state statutes. Diligence support only — not legal advice.*
