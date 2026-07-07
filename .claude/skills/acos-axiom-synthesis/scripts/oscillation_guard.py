#!/usr/bin/env python3
"""
oscillation_guard.py — Phase 4 helper (PLAN.md §15.4).

The Stage-5 refuter is deliberately fresh each round (for independence), so it will
re-raise objections already adjudicated — an infinite-loop risk. This records each
ruling and lets the orchestrator inject "already settled — do not re-raise" into every
later refuter prompt. Keeps the refuter fresh for NEW attacks while killing re-litigation.

Machine store: `settled-objections.jsonl` (one ruling per line). A human-readable
`settled-objections.md` mirror can be rendered from it. Stdlib only.
"""

import json
import re


def _key(objection_text):
    return re.sub(r"\s+", " ", str(objection_text).strip().lower())


def load(path):
    rulings = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rulings.append(json.loads(line))
    except FileNotFoundError:
        return []
    return rulings


def is_settled(path, objection_text):
    k = _key(objection_text)
    return any(r.get("key") == k for r in load(path))


def record(path, objection_text, ruling, disposition):
    """Append a ruling. No-op (idempotent) if this objection is already settled."""
    if is_settled(path, objection_text):
        return False
    entry = {"key": _key(objection_text), "objection": objection_text,
             "ruling": ruling, "disposition": disposition}
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return True


def injection_block(path):
    """Text to prepend to a refuter prompt so it won't re-raise settled points."""
    rulings = load(path)
    if not rulings:
        return ""
    lines = ["These objections are already SETTLED — do NOT re-raise them:"]
    for r in rulings:
        lines.append(f"  - {r['objection']}  (ruling: {r['ruling']})")
    return "\n".join(lines)
