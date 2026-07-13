#!/usr/bin/env python3
"""
next_claims.py — the resumable work frontier (PLAN.md §15.3).

A PURE FUNCTION of on-disk ledger state: it reads claims.jsonl and reports which
claims still need work. There is no in-memory to-do list, so an interrupted run
resumes exactly by re-running this. `done: true` when nothing needs work.

Usage:
  python3 next_claims.py <ledger.jsonl>
"""

import argparse
import json
import sys

import axiom_ledger as al


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compute the resumable work frontier from the ledger.")
    ap.add_argument("ledger", help="path to claims.jsonl")
    args = ap.parse_args(argv)

    frontier = al.compute_frontier(al.read_ledger(args.ledger))
    print(json.dumps(frontier, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
