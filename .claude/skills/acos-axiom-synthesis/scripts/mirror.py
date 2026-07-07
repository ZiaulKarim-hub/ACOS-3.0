#!/usr/bin/env python3
"""
mirror.py — Phase 7: ACOS-visible evidence/metrics mirror (PLAN.md §15.5).

The claims.jsonl ledger is the canonical, self-contained source of truth. This mirror
additionally appends a one-line completion record so a synthesis run shows up in
/acos-status and the metrics tooling, exactly as acos-synthesis-protocol mirrors its
verdicts. Convenience only — never the gate. Stdlib only.

Date is passed in (deterministic for tests / avoids clock coupling).
"""

import json
import os


def mirror_run(repo_root, session, date_str, summary):
    """Append a completion record to .acos/evidence/<date>/axiom-<session>/run.log and
    log agent identity to .acos/metrics/agent-completions.log. Returns the two paths."""
    ev_dir = os.path.join(repo_root, ".acos", "evidence", date_str, f"axiom-{session}")
    os.makedirs(ev_dir, exist_ok=True)
    run_log = os.path.join(ev_dir, "run.log")
    with open(run_log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"session": session, "date": date_str, **summary}, ensure_ascii=False) + "\n")

    metrics_dir = os.path.join(repo_root, ".acos", "metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    metrics_log = os.path.join(metrics_dir, "agent-completions.log")
    with open(metrics_log, "a", encoding="utf-8") as fh:
        fh.write(f"{date_str}\tacos-axiom-synthesis\t{session}\t"
                 f"facts={summary.get('facts', '?')}\tstate={summary.get('status', '?')}\n")
    return {"run_log": run_log, "metrics_log": metrics_log}
