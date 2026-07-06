#!/usr/bin/env python3
"""
verify_ledger.py — tamper-evidence check for the claim ledger (PLAN.md §5.4).

Recomputes every entry_hash and validates the prev_hash chain. Any altered field,
removed line, or reordering is reported with its line number.

  exit 0  intact
  exit 1  tampered (problems printed)

Usage:
  python3 verify_ledger.py <ledger.jsonl>
"""

import argparse
import sys

import axiom_ledger as al


def main(argv=None):
    ap = argparse.ArgumentParser(description="Verify the ledger hash-chain is intact.")
    ap.add_argument("ledger", help="path to claims.jsonl")
    args = ap.parse_args(argv)

    ok, problems = al.verify_chain(args.ledger)
    if ok:
        print(f"OK: ledger intact. head={al.ledger_head(args.ledger)}")
        return 0
    print("TAMPERED:", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
