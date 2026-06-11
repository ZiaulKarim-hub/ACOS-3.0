#!/usr/bin/env python3
"""
ACOS PDF Layout Checker

Programmatic PDF layout analysis using text position data from pdfplumber.
Detects overlapping text, margin violations, orphan/widow lines, stranded
headers, split tables, blank pages, and font consistency issues.

Usage:
    python3 check-pdf-layout.py <pdf-file> [-o <report.yaml>] [--strict] [--verbose]
    python3 check-pdf-layout.py <pdf-file> --margins 36,36,36,36
    python3 check-pdf-layout.py --help

Exit codes:
    0  PASS (no errors; warnings/info only)
    1  FAIL (one or more errors found)
    2  Input error (file not found, dependency missing)

Dependencies: pdfplumber, PyYAML (Python stdlib otherwise)
"""

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Deferred dependency imports -- checked inside main() so --help works
# without pdfplumber/PyYAML installed.
# ---------------------------------------------------------------------------
pdfplumber = None  # type: ignore
yaml = None        # type: ignore


def _check_dependencies():
    """Import pdfplumber and PyYAML, exit with code 2 if missing."""
    global pdfplumber, yaml
    try:
        import pdfplumber as _pdfplumber
        pdfplumber = _pdfplumber
    except ImportError:
        print(
            "ERROR: pdfplumber is required but not installed.\n"
            "Install it with:  pip install pdfplumber\n"
            "(or: pip install 'pdfplumber[image]' for image-based debugging)",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        import yaml as _yaml
        yaml = _yaml
    except ImportError:
        print(
            "ERROR: PyYAML is required but not installed.\n"
            "Install it with:  pip install PyYAML",
            file=sys.stderr,
        )
        sys.exit(2)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_MARGIN_PT = 72  # 1 inch = 72 PDF points
MAX_UNIQUE_FONTS = 4    # more than this triggers INFO finding

# Minimum height threshold (in points) to consider text "header-sized".
# Typical body text is 10-12pt; headers are usually >= 14pt.
HEADER_FONT_SIZE_THRESHOLD = 13.5

# Vertical gap (points) below which two successive text elements are
# considered part of the same paragraph rather than separate blocks.
PARAGRAPH_GAP_THRESHOLD = 4.0

# Overlap tolerance in points -- two boxes must overlap by at least this
# much in both axes before we flag it.  Prevents false positives from
# floating-point rounding in glyph metrics.
OVERLAP_TOLERANCE_PT = 1.0


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
def bbox_overlap(a, b, tol=OVERLAP_TOLERANCE_PT):
    """Return True if bounding boxes *a* and *b* overlap by more than *tol*
    in both the x and y axes.

    Each bbox is (x0, top, x1, bottom).
    """
    x_overlap = min(a[2], b[2]) - max(a[0], b[0])
    y_overlap = min(a[3], b[3]) - max(a[1], b[1])
    return x_overlap > tol and y_overlap > tol


def bbox_area(box):
    """Area of a bounding box (x0, top, x1, bottom)."""
    w = max(0, box[2] - box[0])
    h = max(0, box[3] - box[1])
    return w * h


# ---------------------------------------------------------------------------
# Checker class
# ---------------------------------------------------------------------------
class PdfLayoutChecker:
    """Run all layout checks on a single PDF file."""

    def __init__(self, pdf_path, margins=None, strict=False, verbose=False):
        self.pdf_path = str(pdf_path)
        self.strict = strict
        self.verbose = verbose
        self.findings = []

        # Margins: (left, top, right, bottom) in points
        if margins:
            self.margins = tuple(margins)
        else:
            m = DEFAULT_MARGIN_PT
            self.margins = (m, m, m, m)

        self._broken = False
        self._broken_error = None
        self.page_count = 0

        try:
            self.pdf = pdfplumber.open(pdf_path)
            self.page_count = len(self.pdf.pages)
        except Exception as exc:
            self._broken = True
            self._broken_error = str(exc)

    # -- bookkeeping --------------------------------------------------------

    def add(self, check, severity, page, message, element=""):
        self.findings.append({
            "check": check,
            "severity": severity,
            "page": page,
            "element": element,
            "message": message,
        })

    def _log(self, msg):
        if self.verbose:
            print(f"  [verbose] {msg}", file=sys.stderr)

    # -- individual checks --------------------------------------------------

    def check_text_overlap(self):
        """Check 1 -- overlapping text bounding boxes on the same page."""
        for page in self.pdf.pages:
            page_num = page.page_number
            chars = page.chars
            if not chars:
                continue

            # Cluster characters into word-level bounding boxes using
            # pdfplumber's built-in word extraction.
            words = page.extract_words(
                keep_blank_chars=False,
                use_text_flow=False,
                extra_attrs=["fontname", "size"],
            )
            if not words:
                continue

            # Build bbox list: (x0, top, x1, bottom, text_preview)
            boxes = []
            for w in words:
                boxes.append((
                    float(w["x0"]),
                    float(w["top"]),
                    float(w["x1"]),
                    float(w["bottom"]),
                    w["text"][:40],
                ))

            # Pairwise overlap check (quadratic, but word count per page is
            # manageable -- typically < 500 words).
            overlap_count = 0
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    if bbox_overlap(boxes[i][:4], boxes[j][:4]):
                        overlap_count += 1
                        if overlap_count <= 5:  # cap detail messages
                            self.add(
                                "text_overlap", "ERROR", page_num,
                                f"Overlapping text: '{boxes[i][4]}' and "
                                f"'{boxes[j][4]}' on page {page_num}",
                            )
                        self._log(
                            f"Overlap on p{page_num}: "
                            f"'{boxes[i][4]}' vs '{boxes[j][4]}'"
                        )

            if overlap_count > 5:
                self.add(
                    "text_overlap", "ERROR", page_num,
                    f"... and {overlap_count - 5} more overlapping pairs "
                    f"on page {page_num}",
                )

    def check_margin_compliance(self):
        """Check 2 -- all text stays within configured margins."""
        left_m, top_m, right_m, bottom_m = self.margins

        for page in self.pdf.pages:
            page_num = page.page_number
            page_w = float(page.width)
            page_h = float(page.height)

            words = page.extract_words(keep_blank_chars=False)
            if not words:
                continue

            for w in words:
                x0 = float(w["x0"])
                top = float(w["top"])
                x1 = float(w["x1"])
                bottom = float(w["bottom"])
                text_preview = w["text"][:30]

                violations = []
                if x0 < left_m:
                    violations.append(
                        f"left ({x0:.1f}pt < {left_m}pt margin)"
                    )
                if top < top_m:
                    violations.append(
                        f"top ({top:.1f}pt < {top_m}pt margin)"
                    )
                if x1 > page_w - right_m:
                    violations.append(
                        f"right ({x1:.1f}pt > {page_w - right_m:.1f}pt limit)"
                    )
                if bottom > page_h - bottom_m:
                    violations.append(
                        f"bottom ({bottom:.1f}pt > {page_h - bottom_m:.1f}pt limit)"
                    )

                if violations:
                    sev = "ERROR" if self.strict else "WARNING"
                    self.add(
                        "margin_compliance", sev, page_num,
                        f"Text '{text_preview}' violates margin: "
                        + "; ".join(violations),
                    )

    def check_orphan_widow(self):
        """Check 3 -- orphan/widow line detection.

        Strategy: build a list of text lines per page (sorted by vertical
        position).  A 'paragraph' is a sequence of lines with small vertical
        gaps.  If the last line-group on a page has only one line AND the
        first line-group on the next page has more than one line at a similar
        x-offset, flag as orphan.  Mirror logic for widows.
        """
        _, _, _, bottom_m = self.margins

        page_lines = []  # list of list-of-lines per page
        page_heights = []  # page height (points) per page, for bottom-margin test
        for page in self.pdf.pages:
            page_heights.append(float(page.height))
            words = page.extract_words(keep_blank_chars=False)
            if not words:
                page_lines.append([])
                continue

            # Group words into lines by similar 'top' coordinate
            lines = _cluster_words_into_lines(words)
            page_lines.append(lines)

        for idx in range(len(page_lines) - 1):
            current_lines = page_lines[idx]
            next_lines = page_lines[idx + 1]
            if not current_lines or not next_lines:
                continue

            page_num = idx + 1  # 1-based

            # --- Orphan: single trailing line on current page,
            #     rest of paragraph continues on next page.
            tail_group = _trailing_paragraph_lines(current_lines)
            head_group = _leading_paragraph_lines(next_lines)

            # The leading >= 1 clause was dead (head_group is always non-empty),
            # collapsing this to "len(tail_group) == 1" and firing on virtually
            # every page break (headings, short closing lines). Tighten so the
            # finding carries real signal:
            #   - the lone trailing line must sit in the page's BOTTOM-margin
            #     region (a forced break, not a paragraph that simply ended), and
            #   - the next page must open with a genuine multi-line continuation.
            page_h = page_heights[idx]
            bottom_region_start = page_h - bottom_m  # top edge of bottom margin band
            tail_bottom = tail_group[0]["bottom"]
            if (len(tail_group) == 1
                    and len(head_group) >= 2
                    and tail_bottom >= bottom_region_start):
                # Heuristic: the lone trailing line and the leading group
                # should share a similar left-indent (within 20pt) to be
                # considered part of the same paragraph.
                tail_x = tail_group[0]["x0"]
                head_x = head_group[0]["x0"]
                if abs(tail_x - head_x) < 20:
                    self.add(
                        "orphan_widow", "WARNING", page_num,
                        f"Possible orphan: single trailing line on page "
                        f"{page_num} ('{tail_group[0]['text'][:50]}') "
                        f"continues on page {page_num + 1}",
                    )

            # --- Widow: single leading line on next page,
            #     bulk of paragraph on current page.
            # The trailing >= 1 clause was dead. Require the prior page to have
            # carried a genuine multi-line bulk (len(tail_group) >= 2) before a
            # single stranded head line on the next page counts as a widow.
            if len(head_group) == 1 and len(tail_group) >= 2:
                tail_x = tail_group[0]["x0"]
                head_x = head_group[0]["x0"]
                if abs(tail_x - head_x) < 20:
                    self.add(
                        "orphan_widow", "WARNING", page_num + 1,
                        f"Possible widow: single leading line on page "
                        f"{page_num + 1} ('{head_group[0]['text'][:50]}') "
                        f"from paragraph on page {page_num}",
                    )

    def check_page_break_quality(self):
        """Check 4 -- section headers stranded at the bottom of a page.

        A header is identified by font size (>= HEADER_FONT_SIZE_THRESHOLD)
        or by being significantly larger than the median text on the page.
        If the last non-empty text element on a page looks like a header
        and there is no body text following it on the same page, flag it.
        """
        for page in self.pdf.pages:
            page_num = page.page_number
            words = page.extract_words(
                keep_blank_chars=False,
                extra_attrs=["fontname", "size"],
            )
            if not words:
                continue

            lines = _cluster_words_into_lines(words, with_size=True)
            if len(lines) < 2:
                continue

            last_line = lines[-1]
            last_size = last_line.get("size", 0)

            # Compute median font size on the page
            sizes = [ln.get("size", 0) for ln in lines if ln.get("size", 0) > 0]
            if not sizes:
                continue
            sizes.sort()
            median_size = sizes[len(sizes) // 2]

            is_header = (
                last_size >= HEADER_FONT_SIZE_THRESHOLD
                or (median_size > 0 and last_size > median_size * 1.25)
            )

            if is_header:
                self.add(
                    "page_break_quality", "WARNING", page_num,
                    f"Possible stranded header at bottom of page {page_num}: "
                    f"'{last_line['text'][:60]}' "
                    f"(size {last_size:.1f}pt, page median {median_size:.1f}pt)",
                )

    def check_tables(self):
        """Check 5 -- table detection and split-table analysis."""
        prev_table_bottom = None
        prev_page_num = None

        for page in self.pdf.pages:
            page_num = page.page_number
            tables = page.find_tables()

            if not tables:
                prev_table_bottom = None
                prev_page_num = None
                continue

            for tbl in tables:
                bbox = tbl.bbox  # (x0, top, x1, bottom)
                if bbox is None:
                    continue

                # Check if table touches the bottom of the page (within 36pt
                # of the page bottom), suggesting it may continue.
                page_h = float(page.height)
                table_bottom = float(bbox[3])
                table_top = float(bbox[1])

                touches_bottom = (page_h - table_bottom) < 36
                touches_top = table_top < 72  # near top of page

                # If previous page ended with a table near bottom, and this
                # page starts with a table near top -> likely split table.
                if (prev_table_bottom is not None
                        and prev_page_num == page_num - 1
                        and touches_top):
                    # Try to detect repeated headers by comparing first row
                    # text of this table with text in the previous page's
                    # table (heuristic: if first row text matches, headers
                    # are repeated).
                    rows = tbl.extract()
                    has_repeated_header = False
                    if rows and len(rows) >= 2:
                        # We cannot easily access the previous table's rows
                        # at this point, so we use a simpler heuristic: if
                        # the first row looks like a header (non-numeric,
                        # short text) that is a good sign.
                        first_row = rows[0]
                        if first_row and all(
                            cell and not _looks_numeric(str(cell))
                            for cell in first_row
                            if cell is not None
                        ):
                            has_repeated_header = True

                    if has_repeated_header:
                        self.add(
                            "table_split", "INFO", page_num,
                            f"Table split across pages {page_num - 1}-"
                            f"{page_num} (headers appear repeated)",
                        )
                    else:
                        self.add(
                            "table_split", "WARNING", page_num,
                            f"Table split across pages {page_num - 1}-"
                            f"{page_num} without repeated headers",
                        )

                if touches_bottom:
                    prev_table_bottom = table_bottom
                    prev_page_num = page_num
                else:
                    prev_table_bottom = None
                    prev_page_num = None

    def check_blank_pages(self):
        """Check 6 -- pages with no text content."""
        for page in self.pdf.pages:
            page_num = page.page_number
            text = (page.extract_text() or "").strip()
            if not text:
                self.add(
                    "blank_page", "WARNING", page_num,
                    f"Page {page_num} has no text content",
                )

    def check_font_consistency(self):
        """Check 7 -- flag excessive unique font families."""
        all_fonts = set()
        for page in self.pdf.pages:
            for char in page.chars:
                fontname = char.get("fontname", "")
                if fontname:
                    # Normalise: strip subset prefix (e.g. 'BCDEEE+Arial')
                    if "+" in fontname:
                        fontname = fontname.split("+", 1)[1]
                    # Strip style suffixes for family grouping
                    base = _font_family(fontname)
                    all_fonts.add(base)

        if len(all_fonts) > MAX_UNIQUE_FONTS:
            self.add(
                "font_consistency", "INFO", 0,
                f"{len(all_fonts)} unique font families detected "
                f"(threshold: {MAX_UNIQUE_FONTS}): "
                + ", ".join(sorted(all_fonts)),
            )
        elif self.verbose:
            self._log(
                f"Font families ({len(all_fonts)}): "
                + ", ".join(sorted(all_fonts))
            )

    # -- orchestration ------------------------------------------------------

    def run_all(self):
        """Execute every check and return the structured report dict."""
        if self._broken:
            return {
                "validation": {
                    "pdf_path": self.pdf_path,
                    "page_count": 0,
                    "verdict": "FAIL",
                    "summary": {
                        "errors": 1,
                        "warnings": 0,
                        "info": 0,
                        "total": 1,
                    },
                    "findings": [{
                        "check": "file_integrity",
                        "severity": "ERROR",
                        "page": 0,
                        "element": "",
                        "message": (
                            f"Could not open PDF: {self._broken_error}"
                        ),
                    }],
                }
            }

        try:
            self.check_text_overlap()
            self.check_margin_compliance()
            self.check_orphan_widow()
            self.check_page_break_quality()
            self.check_tables()
            self.check_blank_pages()
            self.check_font_consistency()
        finally:
            self.pdf.close()

        errors = [f for f in self.findings if f["severity"] == "ERROR"]
        warnings = [f for f in self.findings if f["severity"] == "WARNING"]
        infos = [f for f in self.findings if f["severity"] == "INFO"]

        verdict = "FAIL" if errors else ("WARN" if self.strict and warnings else "PASS")

        return {
            "validation": {
                "pdf_path": self.pdf_path,
                "page_count": self.page_count,
                "verdict": verdict,
                "summary": {
                    "errors": len(errors),
                    "warnings": len(warnings),
                    "info": len(infos),
                    "total": len(self.findings),
                },
                "findings": self.findings,
            }
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cluster_words_into_lines(words, with_size=False):
    """Group extracted words into lines based on vertical proximity.

    Returns a list of dicts:
        {"text": str, "top": float, "bottom": float, "x0": float,
         "x1": float [, "size": float]}
    sorted by vertical position (top).
    """
    if not words:
        return []

    # Sort by vertical position first, then horizontal
    sorted_words = sorted(words, key=lambda w: (float(w["top"]), float(w["x0"])))

    lines = []
    current_line_words = [sorted_words[0]]
    current_top = float(sorted_words[0]["top"])

    for w in sorted_words[1:]:
        w_top = float(w["top"])
        # Same line if vertical position is within 3pt
        if abs(w_top - current_top) < 3:
            current_line_words.append(w)
        else:
            lines.append(_merge_line(current_line_words, with_size))
            current_line_words = [w]
            current_top = w_top

    if current_line_words:
        lines.append(_merge_line(current_line_words, with_size))

    return lines


def _merge_line(words, with_size=False):
    """Merge a list of word dicts into a single line dict."""
    text = " ".join(w["text"] for w in words)
    x0 = min(float(w["x0"]) for w in words)
    x1 = max(float(w["x1"]) for w in words)
    top = min(float(w["top"]) for w in words)
    bottom = max(float(w["bottom"]) for w in words)

    line = {"text": text, "top": top, "bottom": bottom, "x0": x0, "x1": x1}

    if with_size:
        sizes = [float(w.get("size", 0)) for w in words if w.get("size")]
        line["size"] = max(sizes) if sizes else 0

    return line


def _trailing_paragraph_lines(lines):
    """Return the trailing paragraph group (lines connected by small gaps)."""
    if not lines:
        return []
    group = [lines[-1]]
    for i in range(len(lines) - 2, -1, -1):
        gap = lines[i + 1]["top"] - lines[i]["bottom"]
        if gap < PARAGRAPH_GAP_THRESHOLD:
            group.insert(0, lines[i])
        else:
            break
    return group


def _leading_paragraph_lines(lines):
    """Return the leading paragraph group (lines connected by small gaps)."""
    if not lines:
        return []
    group = [lines[0]]
    for i in range(1, len(lines)):
        gap = lines[i]["top"] - lines[i - 1]["bottom"]
        if gap < PARAGRAPH_GAP_THRESHOLD:
            group.append(lines[i])
        else:
            break
    return group


def _font_family(fontname):
    """Reduce a full font name to its family (strip Bold, Italic, etc.)."""
    for suffix in (
        "-Bold", "-Italic", "-BoldItalic", "-Regular", "-Light",
        "-Medium", "-Semibold", "-SemiBold", "-ExtraBold",
        ",Bold", ",Italic", ",BoldItalic",
        "Bold", "Italic", "Regular", "Light", "Medium",
    ):
        if fontname.endswith(suffix):
            fontname = fontname[: -len(suffix)]
            break
    # Also strip trailing hyphens or commas left behind
    return fontname.rstrip("-,").strip()


def _looks_numeric(text):
    """Return True if *text* looks like a number (currency, percentage, etc.)."""
    if not text:
        return False
    cleaned = text.replace("$", "").replace(",", "").replace("%", "").strip()
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_margins(value):
    """Parse a margins string like '72' or '36,72,36,72' into a 4-tuple."""
    parts = [p.strip() for p in value.split(",")]
    if len(parts) == 1:
        m = float(parts[0])
        return (m, m, m, m)
    elif len(parts) == 4:
        return tuple(float(p) for p in parts)
    else:
        raise argparse.ArgumentTypeError(
            "Margins must be a single value or 4 comma-separated values "
            "(left,top,right,bottom) in PDF points."
        )


def main():
    parser = argparse.ArgumentParser(
        description="ACOS PDF Layout Checker -- detect layout defects via text position analysis",
        epilog=(
            "Examples:\n"
            "  python3 check-pdf-layout.py report.pdf\n"
            "  python3 check-pdf-layout.py report.pdf -o results.yaml --strict\n"
            "  python3 check-pdf-layout.py report.pdf --margins 36,36,36,36 --verbose\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("pdf_file", help="Path to the PDF file to check")
    parser.add_argument(
        "-o", "--output",
        help="Write YAML report to this file (default: stdout)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: warnings also cause FAIL verdict",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra diagnostic info to stderr",
    )
    parser.add_argument(
        "--margins",
        type=parse_margins,
        default=None,
        help=(
            "Margin requirement in PDF points. "
            "Single value (all sides) or left,top,right,bottom. "
            "Default: 72 (1 inch)"
        ),
    )
    args = parser.parse_args()

    # Check dependencies AFTER argparse so --help works without pdfplumber
    _check_dependencies()

    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(2)
    if not pdf_path.suffix.lower() == ".pdf":
        print(f"WARNING: File does not have .pdf extension: {pdf_path}", file=sys.stderr)

    checker = PdfLayoutChecker(
        pdf_path=pdf_path,
        margins=args.margins,
        strict=args.strict,
        verbose=args.verbose,
    )
    report = checker.run_all()

    report_yaml = yaml.dump(report, default_flow_style=False, sort_keys=False)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            f.write(report_yaml)
        print(f"Report written to: {args.output}")
    else:
        print(report_yaml)

    # Human-readable summary on stderr
    v = report["validation"]
    s = v["summary"]
    print(
        f"\nVerdict: {v['verdict']} "
        f"({s['errors']} errors, {s['warnings']} warnings, {s['info']} info) "
        f"-- {v['page_count']} pages checked",
        file=sys.stderr,
    )

    sys.exit(0 if v["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
