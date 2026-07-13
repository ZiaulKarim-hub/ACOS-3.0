#!/usr/bin/env python3
"""
emit_disclosure.py — F1 guardrail: per-run conflicts / independence disclosure.

Writes `<session>/conflicts-disclosure.yaml` — a governance record stamped every run so the
committee's independence posture, roster, excluded seats, and un-mitigable kill-criteria are
on the record alongside the verdict. Reads the session manifest for the deal + active seats.

This is a DISCLOSURE, not a gate: it documents that the AI seats hold no financial position in
the deal, that scrutiny seats deliberated independence-first (blind parallel opening), and which
risk categories are treated as un-mitigable. A human chair countersigns the `chair_signoff` line.

Stdlib only. Python 3.8+.
"""

import argparse
import os
import re
import sys

# Mirror verdict.py's default kill categories (documented here so the disclosure is self-contained;
# if a project overrides _KILL_CATEGORIES in verdict.py, pass --kill-categories to match).
DEFAULT_KILL = ["Fraud/Misrepresentation"]


def _manifest_field(text, key):
    m = re.search(r"^{}\s*:\s*(.+?)\s*$".format(re.escape(key)), text, re.MULTILINE)
    return m.group(1).strip() if m else None


def _active_seats(text):
    raw = _manifest_field(text, "active_seats") or "[]"
    return [int(n) for n in re.findall(r"\d+", raw)]


def build_disclosure(session_dir, kill_categories):
    manifest_path = os.path.join(session_dir, "manifest.yaml")
    text = open(manifest_path, "r", encoding="utf-8").read() if os.path.isfile(manifest_path) else ""
    deal = _manifest_field(text, "deal") or "(unspecified)"
    seats = _active_seats(text)
    # #9 (advocate) and #10 (gap-hunter) are non-voting by construction.
    voting = [n for n in seats if n not in (9, 10)]

    lines = []
    lines.append("# ACOS Investment Committee — per-run conflicts / independence disclosure")
    lines.append("# Stamped by emit_disclosure.py. Diligence support only; NOT investment advice.")
    lines.append("")
    lines.append("deal: {}".format(deal))
    lines.append("session_dir: {}".format(session_dir))
    lines.append("")
    lines.append("independence_attestation:")
    lines.append("  ai_financial_interest: none   # the AI seats hold no position in this deal")
    lines.append("  scrutiny_independence: \"blind parallel opening — seats formed objections from the")
    lines.append("    shared brief alone, with no visibility into one another (mechanical, not policy)\"")
    lines.append("  advocate_non_voting: true      # seat #9 defends but casts no scrutiny vote")
    lines.append("  chair_authority: procedural_only  # the human chair directs process, never truth")
    lines.append("")
    lines.append("active_seats: [{}]".format(", ".join(str(n) for n in seats)))
    lines.append("voting_seats:  [{}]".format(", ".join(str(n) for n in voting)))
    lines.append("non_voting:    [9, 10]   # Deal Advocate (defense), Gap-Hunter (procedural)")
    lines.append("")
    lines.append("kill_criteria_categories:   # a CORROBORATED objection here is UN-MITIGABLE (vetoes)")
    for c in kill_categories:
        lines.append("  - {}".format(c))
    lines.append("")
    lines.append("chair_signoff: null   # human chair countersigns here (name + date) before circulation")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Emit the per-run IC conflicts/independence disclosure.")
    ap.add_argument("--session", required=True, help="IC session directory (contains manifest.yaml)")
    ap.add_argument("--kill-categories", default=",".join(DEFAULT_KILL),
                    help="comma-separated un-mitigable categories (default: {})".format(",".join(DEFAULT_KILL)))
    args = ap.parse_args(argv)
    kills = [c.strip() for c in args.kill_categories.split(",") if c.strip()]
    out = build_disclosure(args.session, kills)
    out_path = os.path.join(args.session, "conflicts-disclosure.yaml")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(out)
    print("emit_disclosure: wrote {}".format(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
