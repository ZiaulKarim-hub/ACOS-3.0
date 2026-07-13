#!/usr/bin/env python3
"""
extract_deal.py — shared deal extraction layer for acos-investment-committee (SLICE-B1).

Reads a deal dataroom directory EXACTLY ONCE and produces the two shared artifacts
every downstream expert seat reads instead of re-scanning the dataroom:

  <session-dir>/deal-brief/evidence-index.yaml  — a catalog of every file in the deal dir
  <session-dir>/deal-brief/deal-brief.yaml       — structured shared facts extracted from
                                                    the readable (text) documents

This is the single upfront extraction pass (see SLICE-B1-deal-intake.md). It reserves —
but NEVER populates — the `key_metrics.normalized_noi` slot. That value is written by
Accounting's (#3) own opening pass in a later slice; intake must not guess it, and any
document that self-labels a figure "normalized NOI" is deliberately NOT copied into that
slot (it is instead routed to `financials.flagged_for_accounting` for Accounting to see
and independently adjudicate).

stdlib only. Deterministic + idempotent: running twice against the same --deal/--session
pair (with unchanged source files) produces byte-identical output — no wall-clock
timestamps are written, files are processed in a fixed sorted order, and later matches
never overwrite an already-set field (first-match-wins).

Usage:
  python3 extract_deal.py --deal <deal-folder> --session <session-dir>
"""

import argparse
import csv
import io
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Constants / heuristics
# ---------------------------------------------------------------------------

TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml"}

RICH_EXTRACTION_HINTS = {
    ".pdf": "PDF document -- requires rich text/vision extraction (future layer)",
    ".xlsx": "Excel workbook -- requires rich tabular extraction (future layer)",
    ".xls": "Excel workbook (legacy) -- requires rich tabular extraction (future layer)",
    ".xlsm": "Excel workbook (macro) -- requires rich tabular extraction (future layer)",
    ".docx": "Word document -- requires rich text extraction (future layer)",
    ".doc": "Word document (legacy) -- requires rich text extraction (future layer)",
    ".ppt": "PowerPoint deck (legacy) -- requires rich extraction (future layer)",
    ".pptx": "PowerPoint deck -- requires rich extraction (future layer)",
    ".png": "image -- requires vision extraction (future layer)",
    ".jpg": "image -- requires vision extraction (future layer)",
    ".jpeg": "image -- requires vision extraction (future layer)",
    ".tif": "image -- requires vision extraction (future layer)",
    ".tiff": "image -- requires vision extraction (future layer)",
    ".gif": "image -- requires vision extraction (future layer)",
    ".heic": "image -- requires vision extraction (future layer)",
}

SKIP_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}

MAX_EXCERPT_CHARS = 20000

# Evidence-tier heuristic (data-model.md EvidenceCitation.tier: T1..T5 convention).
# Filename/path keyword match, first match wins, most-authoritative first. This is a
# documented heuristic for the shared evidence index only -- it is NOT a legal/financial
# determination of source authority.
TIER_KEYWORDS = (
    ("T1", (
        "term sheet", "termsheet", "loan agreement", "promissory note", "deed of trust",
        "mortgage", "rent roll", "rent-roll", "t-12", "t12", "trailing twelve",
        "financial statement", "appraisal", "title report", "note",
    )),
    ("T2", (
        "pro forma", "proforma", "business plan", "sponsor summary", "borrower summary",
        "budget", "underwriting",
    )),
    ("T3", (
        "photo", "marketing", "brochure", "flyer", "site plan", "survey",
    )),
    ("T4", (
        "email", "correspondence", "letter", "memo",
    )),
)
DEFAULT_TIER = "T5"

# Field-label synonyms -> dotted path into the deal-brief skeleton. Matched against a
# normalized ("lowercase, whitespace-collapsed") copy of a scanned "Label: value" line.
# First match across all documents wins (deterministic sorted-file-order processing);
# later matches for the same field are ignored rather than overwriting.
KEY_MAP = {
    # deal_meta
    "deal name": ("deal_meta", "name"),
    "project name": ("deal_meta", "name"),
    "asset type": ("deal_meta", "asset_type"),
    "fund id": ("deal_meta", "fund_id"),
    "loan tape reference": ("deal_meta", "fund_id"),
    # loan_terms
    "loan amount": ("loan_terms", "loan_amount"),
    "requested loan amount": ("loan_terms", "loan_amount"),
    "loan ask": ("loan_terms", "loan_amount"),
    "interest rate": ("loan_terms", "interest_rate"),
    "rate": ("loan_terms", "interest_rate"),
    "term": ("loan_terms", "term"),
    "loan term": ("loan_terms", "term"),
    "maturity": ("loan_terms", "term"),
    "lien position": ("loan_terms", "lien_position"),
    "ltv": ("loan_terms", "ltv"),
    "loan-to-value": ("loan_terms", "ltv"),
    "ltc": ("loan_terms", "ltc"),
    "loan-to-cost": ("loan_terms", "ltc"),
    "structure": ("loan_terms", "structure"),
    # sponsor
    "sponsor": ("sponsor", "name"),
    "sponsor name": ("sponsor", "name"),
    "borrower entity": ("sponsor", "borrower_entity"),
    "borrower": ("sponsor", "borrower_entity"),
    "guarantor": ("sponsor", "guarantor"),
    "net worth (sponsor-reported)": ("sponsor", "net_worth_reported"),
    "net worth": ("sponsor", "net_worth_reported"),
    "liquidity (sponsor-reported)": ("sponsor", "liquidity_reported"),
    "liquidity": ("sponsor", "liquidity_reported"),
    "years active": ("sponsor", "track_record", "years_active"),
    "multifamily units owned/managed": ("sponsor", "track_record", "units_owned_managed"),
    "units owned/managed": ("sponsor", "track_record", "units_owned_managed"),
    "prior okoa-style bridge loans completed": ("sponsor", "track_record", "prior_similar_loans_completed"),
    "prior similar loans completed": ("sponsor", "track_record", "prior_similar_loans_completed"),
    # collateral
    "property address": ("collateral", "address"),
    "address": ("collateral", "address"),
    "property type": ("collateral", "property_type"),
    "units": ("collateral", "units_or_sf"),
    "square footage": ("collateral", "units_or_sf"),
    # sources_uses (dict-of-dict targets)
    "purchase price": ("sources_uses", "uses", "purchase_price"),
    "total sources": ("sources_uses", "sources", "total"),
    "total uses": ("sources_uses", "uses", "total"),
    "loan proceeds": ("sources_uses", "sources", "loan_proceeds"),
    "sponsor equity": ("sources_uses", "sources", "sponsor_equity"),
    # financials -- deliberately labeled "reported", never "normalized"
    "in-place noi (sponsor-reported)": ("financials", "reported_noi"),
    "in-place noi": ("financials", "reported_noi"),
    "reported noi": ("financials", "reported_noi"),
    "noi (sponsor-reported)": ("financials", "reported_noi"),
}

# Any scanned label containing both of these tokens is a sponsor/document self-labeled
# "normalized NOI" figure. It must NEVER be written into key_metrics.normalized_noi at
# intake time (that is Accounting's (#3) exclusive, later write). Route it to
# financials.flagged_for_accounting instead, so Accounting sees it but intake never
# adjudicates or fabricates the canonical value.
NORMALIZED_NOI_GUARD_TOKENS = ("normalized", "noi")

KV_LINE_RE = re.compile(
    r"^\s*(?:[-*]\s+)?\**([A-Za-z][A-Za-z0-9 /&()\-]{1,70}?)\**\s*:\s+(.+?)\s*$"
)

STATE_ZIP_RE = re.compile(r",\s*([A-Z]{2})\s+\d{5}(?:-\d{4})?\b")


# ---------------------------------------------------------------------------
# Deal-brief skeleton
# ---------------------------------------------------------------------------

def new_brief_skeleton(deal_id, deal_dir_arg):
    return {
        "deal_meta": {
            "deal_id": deal_id,
            "deal_dir": deal_dir_arg,
            "name": "TBD",
            "asset_type": "TBD",
            "jurisdictions": [],
            "fund_id": "TBD",
        },
        "loan_terms": {
            "loan_amount": "TBD",
            "interest_rate": "TBD",
            "term": "TBD",
            "lien_position": "TBD",
            "ltv": "TBD",
            "ltc": "TBD",
            "structure": "TBD",
        },
        "sponsor": {
            "name": "TBD",
            "borrower_entity": "TBD",
            "guarantor": "TBD",
            "net_worth_reported": "TBD",
            "liquidity_reported": "TBD",
            "track_record": {
                "years_active": "TBD",
                "units_owned_managed": "TBD",
                "prior_similar_loans_completed": "TBD",
            },
        },
        "collateral": {
            "address": "TBD",
            "property_type": "TBD",
            "units_or_sf": "TBD",
        },
        "sources_uses": {
            "sources": {},
            "uses": {},
        },
        "financials": {
            "reported_noi": "TBD",
            "rent_roll_summary": {},
            "flagged_for_accounting": [],
        },
        "key_metrics": {
            # Reserved slot -- single canonical location for Accounting's (#3) later
            # normalized-NOI claim. Intake writes it once, unfilled, and never again.
            "normalized_noi": {
                "owner": "#3 Accounting",
                "value": None,
                "status": "unowned-until-accounting-run",
            },
        },
        "documents": [],
    }


def set_path(brief, path, value):
    """Set brief[path[0]][path[1]]... = value, only if currently unset ('TBD'/None/missing).
    First-match-wins -> deterministic across files processed in sorted order."""
    node = brief
    for key in path[:-1]:
        nxt = node.get(key)
        if not isinstance(nxt, dict):
            nxt = {}
            node[key] = nxt
        node = nxt
    leaf = path[-1]
    current = node.get(leaf, "TBD")
    if current in ("TBD", None, ""):
        node[leaf] = value
        return True
    return False


def apply_kv(brief, relpath, key, value):
    """Route one scanned "Label: value" pair into the deal-brief skeleton, if recognized."""
    normalized_key = re.sub(r"\s+", " ", key.strip().strip("*_").strip().lower())
    value = value.strip()
    if not normalized_key or not value:
        return

    if all(tok in normalized_key for tok in NORMALIZED_NOI_GUARD_TOKENS):
        brief["financials"]["flagged_for_accounting"].append(
            "{}: {} (source: {}) -- NOT copied into key_metrics.normalized_noi; "
            "Accounting (#3) must independently derive/own that value.".format(
                key.strip(), value, relpath
            )
        )
        return

    target = KEY_MAP.get(normalized_key)
    if target is None:
        return
    set_path(brief, target, value)

    # Opportunistic jurisdiction capture from any address-shaped value.
    if target == ("collateral", "address"):
        m = STATE_ZIP_RE.search(value)
        if m:
            state = m.group(1)
            if state not in brief["deal_meta"]["jurisdictions"]:
                brief["deal_meta"]["jurisdictions"].append(state)


def scan_kv_lines(text):
    """Yield (key, value) pairs from "Label: value" / "- Label: value" lines. Works for
    markdown/txt bullet-style docs and flat "key: value" content (plain text or naive
    single-level YAML, since PyYAML is not available in stdlib)."""
    for line in text.splitlines():
        m = KV_LINE_RE.match(line)
        if m:
            yield m.group(1), m.group(2)


# ---------------------------------------------------------------------------
# Evidence-index helpers
# ---------------------------------------------------------------------------

def classify_tier(relpath):
    lower = relpath.lower()
    for tier, keywords in TIER_KEYWORDS:
        if any(k in lower for k in keywords):
            return tier
    return DEFAULT_TIER


def one_line_hint_from_text(ext, text):
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            return stripped[:140]
    return "(empty {} file)".format(ext.lstrip("."))


def extract_csv_content(relpath, text):
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return {"header": [], "row_count": 0}, "(empty csv file)", None

    header = [h.strip() for h in rows[0]]
    data_rows = rows[1:]
    preview_cols = header[:6]
    hint = "CSV, {} columns ({}{}), {} data rows".format(
        len(header), ", ".join(preview_cols), "..." if len(header) > 6 else "", len(data_rows)
    )

    rent_roll_summary = None
    header_lower = [h.lower() for h in header]
    if any(("rent" in h or "unit" in h or "tenant" in h) for h in header_lower):
        rent_idx = next((i for i, h in enumerate(header_lower) if "rent" in h), None)
        status_idx = next(
            (i for i, h in enumerate(header_lower) if "status" in h or "occup" in h), None
        )
        occupied = 0
        vacant = 0
        total_rent = 0.0
        rent_hits = 0
        for row in data_rows:
            if status_idx is not None and status_idx < len(row):
                cell = row[status_idx].strip().lower()
                if "vac" in cell:
                    vacant += 1
                elif cell:
                    occupied += 1
            if rent_idx is not None and rent_idx < len(row):
                raw = row[rent_idx].strip().replace("$", "").replace(",", "")
                try:
                    total_rent += float(raw)
                    rent_hits += 1
                except ValueError:
                    pass
        rent_roll_summary = {
            "source": relpath,
            "unit_count": len(data_rows),
            "occupied_units": occupied if status_idx is not None else "TBD",
            "vacant_units": vacant if status_idx is not None else "TBD",
            "total_monthly_rent_reported": round(total_rent, 2) if rent_hits else "TBD",
        }

    return {"header": header, "row_count": len(data_rows)}, hint, rent_roll_summary


def extract_json_content(text):
    try:
        parsed = json.loads(text)
    except ValueError:
        return {}, "(unparseable JSON)", []

    kv_pairs = []
    if isinstance(parsed, dict):
        keys = list(parsed.keys())
        hint = "JSON object with keys: {}{}".format(
            ", ".join(str(k) for k in keys[:6]), "..." if len(keys) > 6 else ""
        )
        for k, v in parsed.items():
            if isinstance(v, (dict, list)):
                continue
            kv_pairs.append((str(k).replace("_", " "), str(v)))
        summary = {"top_level_type": "object", "keys": keys}
    elif isinstance(parsed, list):
        hint = "JSON array of {} items".format(len(parsed))
        summary = {"top_level_type": "array", "item_count": len(parsed)}
    else:
        hint = "JSON scalar value"
        summary = {"top_level_type": type(parsed).__name__}
    return summary, hint, kv_pairs


# ---------------------------------------------------------------------------
# Walk + index
# ---------------------------------------------------------------------------

def gather_files(deal_dir):
    """Return sorted relative paths (posix-style) of every non-junk file under deal_dir."""
    relpaths = []
    for root, dirnames, filenames in os.walk(deal_dir):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for fname in sorted(filenames):
            if fname.startswith(".") or fname in SKIP_NAMES:
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, deal_dir).replace(os.sep, "/")
            relpaths.append(rel)
    return sorted(relpaths)


def build_indices(deal_dir, deal_id, deal_dir_arg):
    evidence_files = []
    brief = new_brief_skeleton(deal_id, deal_dir_arg)
    needs_rich_count = 0

    for i, relpath in enumerate(gather_files(deal_dir), start=1):
        full_path = os.path.join(deal_dir, relpath.replace("/", os.sep))
        ext = os.path.splitext(relpath)[1].lower()
        size = os.path.getsize(full_path)
        entry = {
            "id": "ev-{:03d}".format(i),
            "path": relpath,
            "type": ext.lstrip(".") if ext else "unknown",
            "size": size,
            "tier": classify_tier(relpath),
        }

        if ext not in TEXT_EXTENSIONS:
            entry["needs_rich_extraction"] = True
            entry["one_line_hint"] = RICH_EXTRACTION_HINTS.get(
                ext, "opaque/binary format -- requires rich extraction (future layer)"
            )
            needs_rich_count += 1
            evidence_files.append(entry)
            continue

        # Single read for this file: feeds both the evidence-index content capture and
        # the shared deal-brief extraction pass. The dataroom is read exactly once.
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        entry["needs_rich_extraction"] = False

        if ext == ".csv":
            structure, hint, rent_roll_summary = extract_csv_content(relpath, text)
            entry["one_line_hint"] = hint
            entry["csv_header"] = structure["header"]
            entry["csv_row_count"] = structure["row_count"]
            if rent_roll_summary and not brief["financials"]["rent_roll_summary"]:
                brief["financials"]["rent_roll_summary"] = rent_roll_summary
        elif ext == ".json":
            summary, hint, kv_pairs = extract_json_content(text)
            entry["one_line_hint"] = hint
            entry["json_summary"] = summary
            for k, v in kv_pairs:
                apply_kv(brief, relpath, k, v)
        else:
            # .md / .txt / .yaml / .yml -- line-scan for "Label: value" content.
            entry["one_line_hint"] = one_line_hint_from_text(ext, text)
            excerpt = text[:MAX_EXCERPT_CHARS]
            entry["content_excerpt"] = excerpt
            entry["content_truncated"] = len(text) > MAX_EXCERPT_CHARS
            for k, v in scan_kv_lines(text):
                apply_kv(brief, relpath, k, v)

        evidence_files.append(entry)

    brief["documents"] = [
        {"id": e["id"], "path": e["path"], "type": e["type"], "tier": e["tier"]}
        for e in evidence_files
    ]

    evidence_index = {
        "deal_dir": deal_dir_arg,
        "file_count": len(evidence_files),
        "files": evidence_files,
    }
    return evidence_index, brief, needs_rich_count


# ---------------------------------------------------------------------------
# Minimal stdlib YAML emitter (block style; no external dependency)
# ---------------------------------------------------------------------------

_PLAIN_SAFE_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_ .\-/#%]*$")
_RESERVED_SCALARS = {
    "null", "Null", "NULL", "~",
    "true", "True", "TRUE", "false", "False", "FALSE",
    "yes", "Yes", "YES", "no", "No", "NO",
}
_LOOKS_NUMERIC_RE = re.compile(r"^[+-]?\d+(\.\d+)?$")


def _yaml_scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)

    s = str(value)
    if s == "":
        return "''"

    needs_quote = (
        s != s.strip()
        or s in _RESERVED_SCALARS
        or _LOOKS_NUMERIC_RE.match(s) is not None
        or not _PLAIN_SAFE_RE.match(s)
    )
    if not needs_quote:
        return s

    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\n", "\\n").replace("\t", "\\t")
    return '"{}"'.format(escaped)


def _emit(obj, indent):
    """Recursively render obj (dict/list/scalar) as a list of YAML lines at the given
    indent level (2 spaces per level)."""
    pad = "  " * indent
    lines = []

    if isinstance(obj, dict):
        if not obj:
            return [pad + "{}"]
        for key, value in obj.items():
            key_str = _yaml_scalar(key) if not isinstance(key, str) or not _PLAIN_SAFE_RE.match(key) else key
            if isinstance(value, dict):
                if not value:
                    lines.append("{}{}: {{}}".format(pad, key_str))
                else:
                    lines.append("{}{}:".format(pad, key_str))
                    lines.extend(_emit(value, indent + 1))
            elif isinstance(value, list):
                if not value:
                    lines.append("{}{}: []".format(pad, key_str))
                else:
                    lines.append("{}{}:".format(pad, key_str))
                    lines.extend(_emit(value, indent + 1))
            else:
                lines.append("{}{}: {}".format(pad, key_str, _yaml_scalar(value)))
        return lines

    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                if not item:
                    lines.append(pad + "- {}")
                    continue
                sub_lines = _emit(item, indent + 1)
                deep_pad = "  " * (indent + 1)
                first = sub_lines[0]
                first_content = first[len(deep_pad):] if first.startswith(deep_pad) else first.lstrip()
                lines.append("{}- {}".format(pad, first_content))
                lines.extend(sub_lines[1:])
            elif isinstance(item, list):
                lines.append(pad + "-")
                lines.extend(_emit(item, indent + 1))
            else:
                lines.append("{}- {}".format(pad, _yaml_scalar(item)))
        return lines

    return [pad + _yaml_scalar(obj)]


def dump_yaml(obj):
    lines = _emit(obj, 0)
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def _has_content(node):
    if isinstance(node, dict):
        return any(_has_content(v) for v in node.values())
    if isinstance(node, list):
        return len(node) > 0
    return node not in (None, "TBD", "unknown", "")


def sections_populated(brief):
    sections = (
        "deal_meta", "loan_terms", "sponsor", "collateral",
        "sources_uses", "financials", "key_metrics", "documents",
    )
    count = 0
    for section in sections:
        node = brief.get(section)
        if section == "key_metrics" and isinstance(node, dict):
            node = {k: v for k, v in node.items() if k != "normalized_noi"}
        if _has_content(node):
            count += 1
    return count, len(sections)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def slugify(name):
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name.strip()).strip("-").lower()
    return slug or "deal"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Shared deal extraction layer: read a deal dataroom once, produce "
        "deal-brief.yaml + evidence-index.yaml for all downstream IC seats."
    )
    parser.add_argument("--deal", required=True, help="Path to the deal dataroom folder.")
    parser.add_argument("--session", required=True, help="Path to the IC session directory.")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.deal):
        sys.stderr.write("ERROR: --deal directory not found: {}\n".format(args.deal))
        return 2

    deal_basename = os.path.basename(os.path.normpath(args.deal))
    deal_id = slugify(deal_basename)

    evidence_index, brief, needs_rich_count = build_indices(args.deal, deal_id, args.deal)

    out_dir = os.path.join(args.session, "deal-brief")
    os.makedirs(out_dir, exist_ok=True)

    evidence_path = os.path.join(out_dir, "evidence-index.yaml")
    brief_path = os.path.join(out_dir, "deal-brief.yaml")

    with open(evidence_path, "w", encoding="utf-8") as f:
        f.write(dump_yaml(evidence_index))
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(dump_yaml(brief))

    populated, total_sections = sections_populated(brief)

    print("extract_deal.py summary")
    print("  deal:            {}".format(args.deal))
    print("  session:         {}".format(args.session))
    print("  files indexed:   {}".format(evidence_index["file_count"]))
    print("  sections populated (non-TBD content): {}/{}".format(populated, total_sections))
    print("  flagged needs_rich_extraction: {}".format(needs_rich_count))
    print("  normalized_noi:  reserved (unfilled) -- owner #3 Accounting")
    print("  wrote: {}".format(evidence_path))
    print("  wrote: {}".format(brief_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
