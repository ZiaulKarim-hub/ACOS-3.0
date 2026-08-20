#!/usr/bin/env python3
"""merge-knowledge.py — fold one project row's knowledge store into another.

Why this exists (2026-08-18). The Resurrection Protocol already has a `merge`
verb, but it joins two WINDOWS of one project and deliberately leaves knowledge
alone — those windows share a single store, so there is nothing to move. Two
separate ROWS for one project is a different case, and nothing handled it.

FruitSync is the live example. Row a156b1b8 (closed 2026-07-20) holds 14 facts
about the Play Store launch; row abe958ef (closed 2026-07-26) holds 8 about the
parking and the uncommitted export work. Both are rooted at the same folder.
Retiring either row would put half a project's memory out of reach — a tombstone
hides a row without deleting it, but a hidden row cannot be picked.

Python, not TypeScript, by the standing exception: this extends the existing
Python knowledge_lib family and calls its writers directly, so the schema gate,
the content-addressed de-duplication and the append-only discipline all still
apply rather than being re-implemented.

WHAT IT DOES NOT DO
  - never deletes or edits the SOURCE store; the source is read-only here
  - never rewrites a fact; `append_fact` refuses a duplicate outright
  - never retires a row; tombstoning stays a separate, human act
  - refuses two rows with different roots — that is a rename, not a merge

Duplicates cost nothing: a fact's id is a hash of (subject, claim), so the same
claim landing twice collapses to one node.

Usage:
    python3 merge-knowledge.py --from <uuid> --into <uuid>          # dry run
    python3 merge-knowledge.py --from <uuid> --into <uuid> --apply
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import knowledge_lib  # noqa: E402
import registry_lib  # noqa: E402

CARRIED_RELS = ("struck", "strike-reason", "supersedes")


def _fact_payload(row):
    """The append_fact input shape, rebuilt from a stored row."""
    return {
        "kind": row.get("kind"),
        "subject": row.get("subject"),
        "claim": row.get("claim"),
        "evidence": row.get("evidence"),
        "checks": row.get("checks") or [],
        "entities": row.get("entities") or [],
        "tags": row.get("tags") or [],
        "single_valued": bool(row.get("single_valued", False)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--from", dest="src", required=True, help="source project uuid")
    ap.add_argument("--into", dest="dst", required=True, help="target project uuid")
    ap.add_argument("--apply", action="store_true", help="write (default is a dry run)")
    ap.add_argument("--allow-different-roots", action="store_true",
                    help="merge rows that do NOT share a root (rarely correct)")
    args = ap.parse_args(argv)

    home = os.environ.get("ACOS_REGISTRY_HOME") or None
    src, dst = args.src, args.dst

    if src == dst:
        print("REFUSED — --from and --into are the same row")
        return 2

    src_row = registry_lib.load_row(src, home=home)
    dst_row = registry_lib.load_row(dst, home=home)
    if src_row is None:
        print("REFUSED — no registry row for --from %s" % src)
        return 2
    if dst_row is None:
        print("REFUSED — no registry row for --into %s" % dst)
        return 2
    if dst_row["status"] == "tombstoned":
        print("REFUSED — the target row %s is tombstoned; merging into a hidden "
              "row would put the result out of reach too" % dst)
        return 2

    same_root = src_row["root_casefold"] == dst_row["root_casefold"]
    if not same_root and not args.allow_different_roots:
        print("REFUSED — these rows do not share a root, so they are probably two "
              "projects rather than one project wearing two rows:")
        print("    from: %-40r %s" % (src_row.get("workspace_name"), src_row["root"]))
        print("    into: %-40r %s" % (dst_row.get("workspace_name"), dst_row["root"]))
        print("  Pass --allow-different-roots only if you are certain.")
        return 2

    print("from: %s %r  root=%s  status=%s"
          % (src, src_row.get("workspace_name"), src_row["root"], src_row["status"]))
    print("into: %s %r  root=%s  status=%s"
          % (dst, dst_row.get("workspace_name"), dst_row["root"], dst_row["status"]))
    if not same_root:
        print("NOTE — roots differ; proceeding only because --allow-different-roots was given")

    src_facts = knowledge_lib.load_facts(src, home)
    dst_before = {f["id"] for f in knowledge_lib.load_facts(dst, home)}
    src_struck = knowledge_lib.struck_ids(src, home)
    src_dead = knowledge_lib.superseded_ids(src, home)

    new, already = [], []
    for f in src_facts:
        (already if f["id"] in dst_before else new).append(f)

    print("")
    print("source facts: %d   already in target: %d   would move: %d"
          % (len(src_facts), len(already), len(new)))
    if src_struck or src_dead:
        print("of the source facts, %d are struck and %d are superseded — they move "
              "too, WITH their edges, so the target keeps the same view"
              % (len(src_struck), len(src_dead)))

    if not new:
        print("nothing to move — the target already holds every source fact.")
        return 0

    print("")
    for f in new:
        flag = " [struck]" if f["id"] in src_struck else (" [superseded]" if f["id"] in src_dead else "")
        print("  %s  %-16s %s%s" % (f["id"], (f.get("subject") or "?")[:16],
                                    (f.get("claim") or "")[:96], flag))

    if not args.apply:
        print("")
        print("DRY RUN — nothing was written. Neither store changed.")
        print("Re-run with --apply to move these into %s." % dst)
        print("The source store is never modified, and no row is retired either way.")
        return 0

    moved, skipped, failed = 0, 0, []
    id_map = set()
    for f in new:
        try:
            prov = dict(f.get("provenance") or {})
            prov["merged_from_project"] = src
            prov["merged_at"] = knowledge_lib.utc_now_iso()
            fid, written = knowledge_lib.append_fact(dst, _fact_payload(f),
                                                     provenance=prov, home=home)
            id_map.add(fid)
            if written:
                moved += 1
            else:
                skipped += 1
        except Exception as exc:  # noqa: BLE001 — report, never half-die silently
            failed.append("%s: %s: %s" % (f["id"], type(exc).__name__, exc))

    # Carry the edges that make struck / superseded still MEAN something in the
    # target. Without these a struck fact would silently come back to life.
    dst_now = {f["id"] for f in knowledge_lib.load_facts(dst, home)}
    carried = 0
    for e in knowledge_lib.load_edges(src, home):
        if e.get("rel") not in CARRIED_RELS:
            continue
        if e.get("dst") not in dst_now:
            continue
        if e.get("rel") == "supersedes" and e.get("src") not in dst_now:
            continue
        knowledge_lib.append_edge(dst, e.get("src"), e.get("rel"), e.get("dst"), home=home)
        carried += 1

    knowledge_lib.build_index(dst, home)
    registry_lib.audit_append(
        {"event": "knowledge-merged", "project_uuid": dst, "from_project_uuid": src,
         "facts_moved": moved, "facts_already_present": skipped, "edges_carried": carried},
        home=home)

    print("")
    print("MOVED %d fact(s) into %s; %d were already there; %d edge(s) carried."
          % (moved, dst, skipped, carried))
    if failed:
        print("FAILED %d — these did NOT move:" % len(failed))
        for line in failed:
            print("   %s" % line)
    print("source store untouched at ~/.acos/knowledge/%s/ — nothing was deleted." % src)
    print("row %s was NOT retired; tombstoning stays a separate human act." % src)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
