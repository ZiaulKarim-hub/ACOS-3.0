#!/usr/bin/env python3
"""
render.py — generate the human-readable source-of-truth.md from the ledger (PLAN.md §5.5).

The Markdown view is ALWAYS generated from claims.jsonl and never hand-edited. It
surfaces working truth, and — prominently — UNRESOLVED CONFLICTS, OPEN QUESTIONS,
and the SUPERSESSION LOG.

Usage:
  python3 render.py <ledger.jsonl> [--out source-of-truth.md] [--question "..."]
"""

import argparse
import sys

import axiom_ledger as al


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render source-of-truth.md from the ledger.")
    ap.add_argument("ledger", help="path to claims.jsonl")
    ap.add_argument("--out", default=None, help="output path (default: stdout)")
    ap.add_argument("--question", default=None, help="the scoped synthesis question")
    args = ap.parse_args(argv)

    md = al.render_markdown(al.read_ledger(args.ledger), question=args.question)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(md + "\n")
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(md + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
