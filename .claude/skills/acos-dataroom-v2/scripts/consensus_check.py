"""Consensus-checking helper for acos-dataroom-v2.

Reads a directory of agent vote JSON files for a single file_id and emits
a consensus verdict (INCLUDE / EXCLUDE / KEEP / FLAG / PLACEMENT_n).

Note: inclusion consensus is ASYMMETRIC in v2.1 — any single EXCLUDE vote
wins and there is NO re-dispatch loop. There is no SPLIT inclusion verdict.

CLI usage:
  # Phase 2 inclusion consensus
  python3 consensus_check.py inclusion --votes-dir <DIR>

  # Phase 2.5 privilege consensus (asymmetric — any FLAG removes)
  python3 consensus_check.py privilege --votes-dir <DIR>

  # Phase 3 / Phase 5 QA consensus
  python3 consensus_check.py qa --votes-dir <DIR>

  # Phase 4b placement consensus (returns folder number on unanimous)
  python3 consensus_check.py placement --votes-dir <DIR>

  # Phase 6 WS2 description-similarity consensus (LLM-judge externally needed for full
  # similarity check; this CLI only checks vote count + simple text agreement)
  python3 consensus_check.py description --votes-dir <DIR>

Outputs a JSON object to stdout with: {verdict, breakdown, reasoning}.
Exit code 0 on success regardless of verdict (the caller decides what to do).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _load_votes(votes_dir: Path) -> list[dict[str, Any]]:
    """Load all *.json vote files in votes_dir."""
    votes = []
    for fp in sorted(Path(votes_dir).glob("*.json")):
        try:
            with fp.open("r", encoding="utf-8") as f:
                v = json.load(f)
            v["_source_file"] = fp.name
            votes.append(v)
        except Exception as e:
            print(f"WARNING: could not parse {fp}: {e}", file=sys.stderr)
    return votes


def inclusion_consensus(votes_dir: Path) -> dict[str, Any]:
    """v2.1 ASYMMETRIC inclusion consensus — any single EXCLUDE wins, no loop.

    - any vote is EXCLUDE        -> EXCLUDE
    - all 3 votes are INCLUDE    -> INCLUDE
    - otherwise (non-unanimous)  -> EXCLUDE (any non-unanimous-include is an exclude)

    There is NO SPLIT verdict and NO re-dispatch path in v2.1. The Phase 3
    fresh-eyes QA loop is the recovery mechanism for over-aggressive cuts.
    """
    votes = _load_votes(votes_dir)
    if len(votes) < 3:
        return {
            "verdict": "INCOMPLETE",
            "breakdown": {"votes_received": len(votes)},
            "reasoning": f"Only {len(votes)} of 3 votes received.",
        }
    verdicts = [v.get("verdict") for v in votes]
    counts = Counter(verdicts)
    if counts.get("EXCLUDE", 0) >= 1:
        excluding = [v for v in votes if v.get("verdict") == "EXCLUDE"]
        return {
            "verdict": "EXCLUDE",
            "breakdown": dict(counts),
            "reasoning": "At least one deliberator voted EXCLUDE. Asymmetric "
                         "consensus excludes the file (single-veto-wins, no loop).",
            "excluding_agents": [v.get("agent_id") for v in excluding],
        }
    if counts.get("INCLUDE", 0) == 3:
        return {
            "verdict": "INCLUDE",
            "breakdown": dict(counts),
            "reasoning": "Unanimous INCLUDE across all 3 agents.",
        }
    return {
        "verdict": "EXCLUDE",
        "breakdown": dict(counts),
        "reasoning": f"Non-unanimous INCLUDE ({dict(counts)}). Any non-unanimous-"
                     "include is an EXCLUDE under v2.1 asymmetric consensus.",
    }


def privilege_consensus(votes_dir: Path) -> dict[str, Any]:
    """Asymmetric: ANY FLAG → REMOVE. All KEEP → STAY."""
    votes = _load_votes(votes_dir)
    if len(votes) < 3:
        return {
            "verdict": "INCOMPLETE",
            "breakdown": {"votes_received": len(votes)},
            "reasoning": f"Only {len(votes)} of 3 scans received.",
        }
    verdicts = [v.get("verdict") for v in votes]
    counts = Counter(verdicts)
    if counts.get("FLAG", 0) >= 1:
        flagging = [v for v in votes if v.get("verdict") == "FLAG"]
        return {
            "verdict": "REMOVE",
            "breakdown": dict(counts),
            "reasoning": "At least one scanner flagged privilege. Asymmetric consensus removes the file.",
            "flagging_agents": [v.get("agent_id") for v in flagging],
            "triggered_markers": [m for v in flagging for m in v.get("triggered_markers", [])],
        }
    return {
        "verdict": "STAY",
        "breakdown": dict(counts),
        "reasoning": "All 3 scanners returned KEEP. File stays in dataroom.",
    }


def qa_consensus(votes_dir: Path) -> dict[str, Any]:
    votes = _load_votes(votes_dir)
    if len(votes) < 3:
        return {
            "verdict": "INCOMPLETE",
            "breakdown": {"votes_received": len(votes)},
            "reasoning": f"Only {len(votes)} of 3 QA verdicts received.",
        }
    verdicts = [v.get("verdict") for v in votes]
    counts = Counter(verdicts)
    if counts.get("PASS", 0) == 3:
        return {
            "verdict": "PASS",
            "breakdown": dict(counts),
            "reasoning": "Unanimous PASS.",
        }
    failing = [v for v in votes if v.get("verdict") == "FAIL"]
    return {
        "verdict": "FAIL",
        "breakdown": dict(counts),
        "reasoning": f"{len(failing)} of 3 agents failed.",
        "failing_agents": [v.get("agent_id") for v in failing],
        "concerns": [c for v in failing for c in v.get("concerns", [])],
    }


def placement_consensus(votes_dir: Path) -> dict[str, Any]:
    votes = _load_votes(votes_dir)
    if len(votes) < 3:
        return {
            "verdict": "INCOMPLETE",
            "breakdown": {"votes_received": len(votes)},
            "reasoning": f"Only {len(votes)} of 3 placement votes received.",
        }
    folder_nums = [v.get("folder_num") for v in votes]
    counts = Counter(folder_nums)
    if len(set(folder_nums)) == 1:
        return {
            "verdict": "UNANIMOUS",
            "folder_num": folder_nums[0],
            "breakdown": dict(counts),
            "reasoning": f"Unanimous placement in folder {folder_nums[0]}.",
        }
    return {
        "verdict": "SPLIT",
        "breakdown": dict(counts),
        "reasoning": f"Split placement: {dict(counts)}. Re-dispatch required.",
    }


def description_consensus(votes_dir: Path) -> dict[str, Any]:
    """For descriptions, the LLM-judge similarity check happens in the orchestrator.
    This helper just confirms 3 votes exist and surfaces them for the orchestrator to
    judge similarity."""
    votes = _load_votes(votes_dir)
    if len(votes) < 3:
        return {
            "verdict": "INCOMPLETE",
            "breakdown": {"votes_received": len(votes)},
            "reasoning": f"Only {len(votes)} of 3 description drafts received.",
        }
    return {
        "verdict": "VOTES_READY",
        "votes": [{"agent_id": v.get("agent_id"), "description": v.get("description")} for v in votes],
        "reasoning": "All 3 description drafts present. Similarity judgment must be performed by main session (LLM-judge).",
    }


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="acos-dataroom-v2 consensus check")
    parser.add_argument("mode", choices=["inclusion", "privilege", "qa", "placement", "description"])
    parser.add_argument("--votes-dir", required=True, type=Path)
    args = parser.parse_args(argv)

    if not args.votes_dir.is_dir():
        print(json.dumps({"verdict": "ERROR", "reasoning": f"votes-dir not found: {args.votes_dir}"}))
        return 2

    fns = {
        "inclusion": inclusion_consensus,
        "privilege": privilege_consensus,
        "qa": qa_consensus,
        "placement": placement_consensus,
        "description": description_consensus,
    }
    result = fns[args.mode](args.votes_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
