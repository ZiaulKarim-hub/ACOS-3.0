#!/usr/bin/env python3
"""
session_scaffold.py — deterministic session-directory scaffold for acos-investment-committee.

Creates (idempotently) the canonical on-disk subtree for one IC session:

  .acos/investment-committee/<session-id>/
    manifest.yaml
    transcript.md
    rounds/
    sidebars/
    ledger/
    evidence/

Also implements the autopilot pre-flight assertion stub: if
`.acos/state/autopilot-active` exists, this script ABORTS (non-zero exit + a clear
message) before creating/touching anything. There is no fallback branch — the design
guarantee is that the user disables autopilot manually; this script only asserts and
refuses (SLICE-DIAG-01 step 5 / tech_prd.md §1.10, hardened later by F1).

Stdlib only. Idempotent: re-running with the same --session-id (and same --deal)
produces byte-identical output — no diff, no re-creation of existing files/dirs.

Usage:
  python3 session_scaffold.py --session-id SESSION_ID [--deal PATH] [--autopilot-check]
"""

import argparse
import os
import sys

AUTOPILOT_MARKER = os.path.join(".acos", "state", "autopilot-active")

MANIFEST_TEMPLATE = """\
session_id: {session_id}
deal: {deal}
status: open
mode: deliberation
current_round: 0
active_seats: []
"""

CANONICAL_SUBDIRS = ("rounds", "sidebars", "ledger", "evidence")


def autopilot_check(cwd="."):
    """Abort (return False) if the autopilot-active marker exists. No fallback branch."""
    marker_path = os.path.join(cwd, AUTOPILOT_MARKER)
    if os.path.isfile(marker_path):
        sys.stderr.write(
            "ABORT: autopilot is active (found {marker}).\n"
            "The Investment Committee skill cannot run while autopilot is active — "
            "disable autopilot manually (remove/let autopilot clear {marker}) before "
            "invoking acos-investment-committee. There is no autonomous-fallback mode; "
            "this is a pre-flight assertion, not a workaround.\n".format(marker=marker_path)
        )
        return False
    return True


def _yaml_scalar(value):
    """Render a value for the manifest.yaml scalar fields (deal may be None)."""
    if value is None:
        return "null"
    return str(value)


def scaffold(session_id, deal, base_dir="."):
    """
    Deterministically create the canonical session subtree.

    Returns the session directory path. Idempotent: existing files/dirs are left
    untouched (never overwritten) except that missing pieces are created.
    """
    session_dir = os.path.join(base_dir, ".acos", "investment-committee", session_id)
    os.makedirs(session_dir, exist_ok=True)

    for sub in CANONICAL_SUBDIRS:
        os.makedirs(os.path.join(session_dir, sub), exist_ok=True)

    manifest_path = os.path.join(session_dir, "manifest.yaml")
    if not os.path.exists(manifest_path):
        content = MANIFEST_TEMPLATE.format(
            session_id=_yaml_scalar(session_id),
            deal=_yaml_scalar(deal),
        )
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(content)

    transcript_path = os.path.join(session_dir, "transcript.md")
    if not os.path.exists(transcript_path):
        # Empty file, per spec ("empty transcript.md").
        open(transcript_path, "w", encoding="utf-8").close()

    return session_dir


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Scaffold a deterministic acos-investment-committee session directory."
    )
    parser.add_argument("--session-id", required=True, help="Session identifier (directory name).")
    parser.add_argument("--deal", default=None, help="Optional path to the deal folder/context.")
    parser.add_argument(
        "--autopilot-check",
        action="store_true",
        help="Run ONLY the autopilot pre-flight assertion and exit "
        "(non-zero if .acos/state/autopilot-active exists); no scaffolding is performed.",
    )
    args = parser.parse_args(argv)

    if not autopilot_check("."):
        return 1

    if args.autopilot_check:
        print("autopilot pre-flight assertion: OK (no autopilot-active marker found)")
        return 0

    session_dir = scaffold(args.session_id, args.deal)
    print("scaffolded: {}".format(session_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
