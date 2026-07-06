#!/usr/bin/env python3
"""
ledger_writer.py — the ONLY command permitted to change a claim's state (PLAN.md §15.1).

Reads a proposed claim record (JSON, from a file or stdin), validates it against the
current ledger, and either appends it or REFUSES with a non-zero exit code:

  exit 0  written
  exit 2  schema error
  exit 3  invariant violation (corroboration gate / single-source cap / falsification
          gate / dependency integrity)
  exit 4  illegal state transition

Every other part of the pipeline must go through this. A refusal is a hard stop — do
not catch-and-ignore it.

Usage:
  python3 ledger_writer.py <ledger.jsonl> --claim <record.json|-> [--now <ISO8601>]
"""

import argparse
import json
import sys

import axiom_ledger as al


def main(argv=None):
    ap = argparse.ArgumentParser(description="Append a validated claim to the ledger (single writer).")
    ap.add_argument("ledger", help="path to claims.jsonl (created if absent)")
    ap.add_argument("--claim", required=True, help="path to a JSON claim record, or '-' for stdin")
    ap.add_argument("--now", default=None, help="ISO8601 timestamp to stamp (optional)")
    args = ap.parse_args(argv)

    raw = sys.stdin.read() if args.claim == "-" else open(args.claim, "r", encoding="utf-8").read()
    try:
        record = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"REFUSED (schema): input is not valid JSON: {exc}", file=sys.stderr)
        return al.CODE_SCHEMA

    try:
        rec = al.append_claim(args.ledger, record, now=args.now)
    except al.LedgerError as exc:
        kind = {al.CODE_SCHEMA: "schema", al.CODE_INVARIANT: "invariant",
                al.CODE_TRANSITION: "transition"}.get(exc.code, "error")
        print(f"REFUSED ({kind}): {exc.message}", file=sys.stderr)
        return exc.code

    print(json.dumps({
        "ok": True,
        "id": rec["id"],
        "state": rec["state"],
        "confidence": rec["confidence"],
        "entry_hash": rec["entry_hash"],
        "ledger_head": rec["entry_hash"],
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
