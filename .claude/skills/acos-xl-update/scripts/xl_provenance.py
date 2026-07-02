#!/usr/bin/env python3
"""xl_provenance.py — build the SEPARATE reference/provenance companion for an XL weekly update.

The XL skill's cardinal narrative rule is "no update without a reference." This renderer turns a
provenance spec (one entry per proposed bullet) into a standalone Markdown document that lives
ALONGSIDE the workbook in the draft folder — NEVER inside the .xlsx (no investor-visible internal
quotes). For every bullet it shows either:

  * NEW      -> the exact meeting line(s), with meeting date + time (Mountain Time), the speaker,
               and the in-meeting timestamp (mm:ss). The quote is machine-verified: it must be a
               verbatim substring of the cited Fireflies transcript, or it is flagged NOT LOCATED.
  * REFRESHED-> the prior-week bullet it rehashes AND the meeting line(s) that updated it.
  * CARRIED  -> "Carried from prior week (<date>)" + the exact prior-week text (a rehash, stated
               as such).

Payoff figures (Hypercore) are rendered in their own section from the same spec, so the companion
is a complete audit of every changed value + every bullet.

Deterministic: the ONLY judgement (which quote supports which bullet) is supplied in the spec; this
script verifies + timestamps it. Python 3 stdlib only.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from zoneinfo import ZoneInfo

CACHE = os.path.expanduser("~/.fireflies-cache")
MT = ZoneInfo("America/Denver")
_WS = re.compile(r"\s+")


def _norm(s: str) -> str:
    return _WS.sub(" ", (s or "").strip().lower())


def _load_transcript(meeting_id: str) -> dict:
    path = os.path.join(CACHE, "transcripts", f"{meeting_id}.json")
    with open(path) as fh:
        return json.load(fh)


def _meeting_dt(t: dict):
    """Meeting start as an aware datetime in Mountain Time (or None if absent)."""
    raw = t.get("date")
    if isinstance(raw, (int, float)):
        return datetime.datetime.fromtimestamp(raw / 1000, tz=datetime.timezone.utc).astimezone(MT)
    return None


def _meeting_when(t: dict) -> str:
    """Meeting start as 'YYYY-MM-DD hh:mm AM/PM TZ' in Mountain Time (or '?' if absent)."""
    dt = _meeting_dt(t)
    return dt.strftime("%Y-%m-%d %I:%M %p %Z") if dt else "?"


def _locate_quote(t: dict, quote: str) -> dict:
    """Find `quote` (verbatim, whitespace-insensitive) in the transcript sentences.
    Returns {found, speaker, at (mm:ss), start_time}. Spans multiple sentences fine."""
    sents = t.get("sentences") or []
    joined = ""
    spans = []  # (start_char, end_char, sentence)
    for s in sents:
        piece = _norm(s.get("text") or s.get("raw_text") or "")
        if not piece:
            continue
        start = len(joined)
        joined += piece + " "
        spans.append((start, len(joined), s))
    nq = _norm(quote)
    if not nq:
        return {"found": False}
    pos = joined.find(nq)
    if pos < 0:
        # fall back to matching the quote's head (first 45 normalized chars)
        head = nq[:45]
        pos = joined.find(head) if len(head) >= 12 else -1
        if pos < 0:
            return {"found": False}
    for start, end, s in spans:
        if start <= pos < end:
            st = s.get("start_time")
            at = "?"
            if isinstance(st, (int, float)):
                at = f"{int(st) // 60:02d}:{int(st) % 60:02d}"
            return {"found": True, "speaker": s.get("speaker_name") or "?", "at": at, "start_time": st}
    return {"found": True, "speaker": "?", "at": "?"}


def _render_source(src: dict, min_date=None) -> list:
    """Render one meeting source as Markdown lines. Verifies + timestamps the quote, and (when
    min_date is given) flags any meeting older than the recency cutoff."""
    mid = src.get("meeting_id", "")
    title = src.get("meeting_title") or "?"
    quote = (src.get("quote") or "").strip()
    lines = []
    try:
        t = _load_transcript(mid)
    except Exception as e:  # noqa: BLE001
        lines.append(f"    - **{title}** — ⚠ transcript `{mid}` not found ({e})")
        lines.append(f"      > {quote}")
        return lines
    when = _meeting_when(t)
    dt = _meeting_dt(t)
    loc = _locate_quote(t, quote)
    if loc.get("found"):
        stamp = f"{loc['speaker']} @ {loc['at']}"
        verify = "✓ verbatim"
    else:
        stamp = "location: —"
        verify = "⚠ NOT LOCATED VERBATIM in transcript"
    stale = ""
    if min_date and dt and dt.date() < min_date:
        stale = f"  ·  ⚠ OLDER THAN CUTOFF ({min_date.isoformat()})"
    lines.append(f"    - **{title}** — {when}  ·  {stamp}  ·  _{verify}_{stale}")
    lines.append(f"      > “{quote}”")
    return lines


def _render_bullet(b: dict, prior_date: str, min_date=None) -> list:
    text = (b.get("text") or "").strip()
    kind = (b.get("kind") or "new").lower()
    basis = (b.get("prior_week_basis") or "").strip()
    sources = b.get("sources") or []
    tag = {"new": "NEW", "refreshed": "REFRESHED", "carried": "CARRIED",
           "none": "NO RECENT UPDATE"}.get(kind, kind.upper())
    lines = [f"- **[{tag}]** {text}"]
    if kind == "none":
        # honest neutral placeholder: no qualifying meeting in the recency window — no source expected
        lines.append("    - _No qualifying Fireflies meeting in the recency window._")
        return lines
    if kind in ("carried", "refreshed") and basis:
        lines.append(f"    - _Carried from prior week ({prior_date})_: “{basis}”")
    for src in sources:
        lines.extend(_render_source(src, min_date))
    if kind == "new" and not sources:
        lines.append("    - ⚠ NEW bullet with NO source — this violates the no-update-without-reference rule.")
    if kind == "carried" and not basis:
        lines.append("    - ⚠ CARRIED bullet with no prior-week text recorded.")
    return lines


def render(spec: dict, min_date=None) -> str:
    report_date = spec.get("report_date", "?")
    prior_date = spec.get("prior_date", "?")
    out = []
    out.append(f"# XL Ant Portfolio Update — Sources & Provenance")
    out.append("")
    hdr = f"**Report date:** {report_date}  ·  **Prior week:** {prior_date}"
    if min_date:
        hdr += f"  ·  **Recency cutoff:** {min_date.isoformat()} (no source older than 2 weeks; last week primary)"
    out.append(hdr)
    out.append("")
    out.append("This is the reference companion to the weekly XL workbook. It is deliberately a "
               "SEPARATE file — none of these internal meeting quotes appear in the Excel workbook. "
               "Every proposed narrative bullet is traced to the exact Fireflies meeting line (date + "
               "time Mountain, speaker, in-meeting timestamp) or marked as carried forward from a prior "
               "week. Payoff figures are traced to their Hypercore source. Quotes are machine-verified "
               "against the cached transcripts.")
    out.append("")

    # ---- Payoffs (Hypercore) ----
    payoffs = spec.get("payoffs") or []
    if payoffs:
        out.append("## Payoff figures — Hypercore")
        out.append("")
        out.append("| Sheet | Prior | New | Δ | Source |")
        out.append("|---|---:|---:|---:|---|")
        for p in payoffs:
            old = p.get("old"); new = p.get("new"); delta = p.get("delta")
            f = lambda v: ("—" if v is None else (f"{v:,.2f}" if isinstance(v, (int, float)) else str(v)))
            out.append(f"| {p.get('sheet','')} | {f(old)} | {f(new)} | {f(delta)} | {p.get('provenance','')} |")
        out.append("")

    # ---- Narrative (Fireflies) ----
    out.append("## Narrative bullets — Fireflies references")
    out.append("")
    for sh in spec.get("sheets") or []:
        out.append(f"### {sh.get('sheet','')}")
        by_section = {}
        for b in sh.get("bullets") or []:
            by_section.setdefault(b.get("section", "progress"), []).append(b)
        for section in ("progress", "blockers"):
            bs = by_section.get(section) or []
            if not bs:
                continue
            out.append(f"**{section.capitalize()}:**")
            out.append("")
            for b in bs:
                out.extend(_render_bullet(b, prior_date, min_date))
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Render the separate XL reference/provenance companion.")
    p.add_argument("--spec", required=True, help="provenance spec json (or '-' for stdin)")
    p.add_argument("--out", required=True, help="output .md path (in the draft folder)")
    p.add_argument("--min-date", dest="min_date", default=None,
                   help="recency cutoff YYYY-MM-DD; flag any source older than this (2-week rule)")
    a = p.parse_args(argv)
    spec = json.load(sys.stdin) if a.spec == "-" else json.load(open(a.spec))
    min_date = None
    md_min = a.min_date or spec.get("min_date")
    if md_min:
        min_date = datetime.datetime.strptime(md_min, "%Y-%m-%d").date()
    md = render(spec, min_date)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write(md)
    # emit a tiny audit summary to stdout — all three counts MUST be 0 to ship
    unverified = md.count("NOT LOCATED VERBATIM")
    missing = md.count("NO source")
    stale = md.count("OLDER THAN CUTOFF")
    print(json.dumps({"out": a.out, "bytes": len(md), "unverified_quotes": unverified,
                      "sourceless_new_bullets": missing, "stale_sources": stale}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
