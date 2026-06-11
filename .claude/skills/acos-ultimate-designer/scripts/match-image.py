#!/usr/bin/env python3
"""
match-image.py — pick the best manifest entry for a photo slot.

Given a slot (semantic tags + content context) and a manifest, return the
top-scoring entry (token-overlap + named-entity bonus), excluding entries
rejected for similar contexts.

Usage:
    match-image.py --slot '{...json...}' --manifest <path>
                   [--threshold 0.6] [--verbose]

Output (stdout, JSON):
    {"source": "brand", "file_path": "/abs/path", "score": 0.72, "reasoning": "..."}
  OR
    {"action": "fallback", "query": "derived query string", "score": 0.3, "reasoning": "..."}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pyyaml required\n")
    sys.exit(1)


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def score_entry(slot: dict, entry: dict) -> tuple[float, str]:
    slot_tags = set(t.lower() for t in slot.get("semantic_tags", []))
    entry_tags = set(t.lower() for t in (entry.get("semantic_tags") or []) + (entry.get("aesthetic_tags") or []))
    base = jaccard(slot_tags, entry_tags)

    ctx = (slot.get("content_context") or "").lower()
    entity_bonus = 0.0
    if entry.get("deal_match") and entry["deal_match"].lower() in ctx:
        entity_bonus = 0.3
    elif entry.get("deal_match"):
        # tokens of deal_match appear in ctx
        tokens = entry["deal_match"].lower().split()
        if any(t in ctx for t in tokens if len(t) > 3):
            entity_bonus = 0.15

    return base + entity_bonus, f"jaccard={base:.2f} entity_bonus={entity_bonus:.2f}"


def is_rejected_for(entry: dict, slot: dict) -> bool:
    rejected = entry.get("user_rejected_for") or []
    if not rejected:
        return False
    ctx = (slot.get("content_context") or "").lower()
    for r in rejected:
        rctx = (r.get("context") or "").lower()
        if rctx and rctx in ctx or ctx in rctx:
            return True
        # token overlap >= 50%
        a = set(ctx.split())
        b = set(rctx.split())
        if a and b and len(a & b) / max(1, min(len(a), len(b))) >= 0.5:
            return True
    return False


def derive_query(slot: dict) -> str:
    tags = slot.get("semantic_tags", [])[:5]
    return " ".join(tags) if tags else "architectural landscape"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slot", required=True, help="JSON: {slot_id, semantic_tags, content_context, page_number}")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    slot = json.loads(args.slot)
    mf_path = Path(args.manifest)
    if not mf_path.exists():
        print(json.dumps({"action": "fallback", "query": derive_query(slot), "score": 0.0, "reasoning": "manifest missing"}))
        return 0

    manifest = yaml.safe_load(mf_path.read_text()) or {}
    entries = manifest.get("entries", {})

    scored: list[tuple[float, dict, str]] = []
    for h, entry in entries.items():
        if is_rejected_for(entry, slot):
            continue
        s, why = score_entry(slot, entry)
        scored.append((s, entry, why))
    scored.sort(key=lambda x: x[0], reverse=True)

    if args.verbose:
        for s, e, w in scored[:5]:
            sys.stderr.write(f"  {s:.3f}  {e.get('filename'):<40} {w}\n")

    if scored and scored[0][0] >= args.threshold:
        s, entry, why = scored[0]
        print(json.dumps({
            "source": "brand",
            "file_path": entry.get("path"),
            "file_hash": entry.get("file_hash"),
            "description": entry.get("description", ""),
            "score": round(s, 3),
            "reasoning": why,
        }))
    else:
        top_score = scored[0][0] if scored else 0.0
        print(json.dumps({
            "action": "fallback",
            "query": derive_query(slot),
            "score": round(top_score, 3),
            "reasoning": f"best score {top_score:.2f} < threshold {args.threshold}",
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
