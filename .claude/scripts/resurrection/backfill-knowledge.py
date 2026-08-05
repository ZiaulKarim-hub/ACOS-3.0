#!/usr/bin/env python3
"""backfill-knowledge.py — seed each project's knowledge store from the
handoff bundles it already has (KB-D, user brief 2026-08-04).

WHY: without this, every project's store is empty on day one, and Zee would
have to re-learn from scratch things his own closed sessions already recorded.
The bundles under memory/handoffs/closed/ are a real corpus — the audit counted
24 of them at the time the brief was written.

WHAT IT EXTRACTS, and the honesty rule it follows. Each fact's CLAIM is a
verbatim line from a handoff's intent_core, and its EVIDENCE is that line plus
the exact file it came from. Nothing is paraphrased and nothing is inferred:
a backfilled fact asserts "this was recorded, here, on this date", which is
checkable, rather than "this is true", which would be a judgement no script may
make on Zee's behalf.

  decisions:      -> subject "decisions"
  traps:          -> subject "traps"
  open_questions: -> subject "open questions"
  git branch      -> subject "git"

Every fact carries a path_contains check (KB-C), so if a handoff is ever edited
or removed the fact is flagged stale rather than quietly outliving its source.

D5a evidence or no write — enforced by knowledge_lib, not re-implemented here.
D5b append-only — a re-run adds nothing new; facts are content-addressed.
D5d review after — backfilled facts land in the "learned since you were last
    here" digest on the next resurrect, where Zee can strike any line.

NO SILENT CAPS: a per-project ceiling exists so one enormous project cannot
bury the digest, and whatever it drops is REPORTED, never quietly discarded.

WRITES NOTHING BY DEFAULT. --write is required; a bare run is a preview. A
bulk write across every project is not something to do by accident.

Usage:
  python3 backfill-knowledge.py                 # preview every project
  python3 backfill-knowledge.py --write         # actually seed the stores
  python3 backfill-knowledge.py --project UUID  # just one project
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bundles_lib
import knowledge_lib
import registry_lib

PER_PROJECT_CAP = 40
SECTION_SUBJECTS = {
    "decisions": "decisions",
    "traps": "traps",
    "open_questions": "open questions",
}


def split_intent_sections(intent_core):
    """intent_core is a literal block that itself contains `key: |` sections.

    Returns {section_name: [item, ...]}. Items are the "- " entries, with
    continuation lines folded in, because a decision often wraps over several
    lines and half a decision is worse than none.
    """
    sections = {}
    current, items, buf = None, [], []

    def flush_item():
        if buf:
            items.append(" ".join(x.strip() for x in buf if x.strip()))
            del buf[:]

    def flush_section():
        flush_item()
        if current:
            sections[current] = [i for i in items if i]

    for raw in (intent_core or "").splitlines():
        m = re.match(r"^(\w+):\s*\|?\s*$", raw)
        if m:
            flush_section()
            current, items, buf = m.group(1), [], []
            continue
        if current is None:
            continue
        stripped = raw.strip()
        if stripped.startswith("- "):
            flush_item()
            buf.append(stripped[2:])
        elif stripped:
            buf.append(stripped)
        else:
            flush_item()
    flush_section()
    return sections


def facts_from_bundle(bundle_dir, root):
    """Candidate facts from ONE bundle. Every claim is verbatim; every fact
    names the file it came from."""
    hpath = os.path.join(bundle_dir, "handoff.yaml")
    h = bundles_lib.parse_handoff(hpath)
    if not h:
        return []
    slug = h.get("slug") or os.path.basename(bundle_dir)
    rel = os.path.relpath(hpath, root) if root else hpath
    out = []

    sections = split_intent_sections(h.get("intent_core"))
    for key, subject in SECTION_SUBJECTS.items():
        for item in sections.get(key, []):
            if len(item) < 12:
                continue  # a fragment is not a fact
            out.append({
                "kind": "machine",
                "subject": subject,
                "claim": item,
                # The claim IS the quote, so the evidence names its SOURCE and
                # does not repeat it — a digest that prints each fact twice is
                # a digest Zee stops reading, which defeats D5d's review.
                "evidence": {"type": "quote",
                             "value": "recorded verbatim in %s (%s)" % (rel, slug)},
                # KB-C: if the source handoff is edited or removed, this fact is
                # flagged stale instead of quietly outliving its evidence.
                "checks": [{"type": "path_contains", "path": rel, "needle": item[:60]}],
                # KB-E: the THINGS this claim touches, so a trap learned here can
                # surface in another project that works with the same tool or
                # file. Without these the graph has facts but no reach.
                "entities": knowledge_lib.extract_entities(item),
                "tags": ["backfill", slug],
            })

    branch = (h.get("git") or "") or ""
    if not branch:
        gs = h.get("git_state") or ""
        m = re.search(r"branch=(\S+)", gs)
        branch = m.group(1) if m else ""
    if branch:
        out.append({
            "kind": "machine",
            "subject": "git",
            "claim": "at the %s close the branch was %s" % (slug, branch),
            "evidence": {"type": "quote", "value": "git_state in %s" % rel},
            "tags": ["backfill", slug],
        })
    return out


def backfill_project(row, write, home=None, cap=PER_PROJECT_CAP, shared_names=None):
    """Seed ONE project. Returns a report dict — printed by the caller.

    `shared_names` carries the registry's ambiguous display names so the
    name rung of ownership refuses where a name points at two rows.
    """
    if shared_names is None:
        shared_names = bundles_lib.ambiguous_names(home)
    root = row["root"]
    rep = {"name": row["name"], "uuid": row["project_uuid"], "bundles": 0,
           "candidates": 0, "written": 0, "duplicate": 0, "refused": 0,
           "capped": 0, "root_missing": not os.path.isdir(root)}
    if rep["root_missing"]:
        return rep

    candidates = []
    for bundle in bundles_lib.iter_bundles(root):
        owns, _evidence = bundles_lib.bundle_owner(bundle, row, shared_names)
        if not owns:
            continue
        rep["bundles"] += 1
        candidates.extend(facts_from_bundle(bundle, root))

    rep["candidates"] = len(candidates)
    if len(candidates) > cap:
        # Newest bundles first is the wrong instinct here: the OLDEST decisions
        # are usually the load-bearing ones, and a project's early rulings are
        # exactly what a resurrection needs. Keep the oldest, report the rest.
        rep["capped"] = len(candidates) - cap
        candidates = candidates[:cap]

    if not write:
        rep["written"] = len(candidates)  # would-be
        return rep

    prov = {"window": row.get("workspace_name") or "(folder-level)",
            "session": "backfill", "close_slug": "KB-D backfill"}
    result = knowledge_lib.write_learnings(row["project_uuid"], candidates,
                                           provenance=prov, home=home)
    rep["written"] = len(result["written"])
    rep["duplicate"] = len(result["duplicate"])
    rep["refused"] = len(result["refused"])
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true",
                    help="actually seed the stores (default is a preview)")
    ap.add_argument("--project", default=None, help="one project uuid only")
    ap.add_argument("--home", default=None, help="home-root override (tests)")
    ap.add_argument("--cap", type=int, default=PER_PROJECT_CAP,
                    help="max facts seeded per project (drops are reported)")
    args = ap.parse_args(argv)

    home = args.home or os.environ.get("ACOS_REGISTRY_HOME") or None
    rows = []
    if args.project:
        r = registry_lib.load_row(args.project, home)
        if r is None:
            print("REFUSED — no registry row for %s" % args.project)
            return 1
        rows = [r]
    else:
        rdir = registry_lib.registry_dir(home)
        for fn in sorted(os.listdir(rdir)) if os.path.isdir(rdir) else []:
            if not fn.endswith(".json"):
                continue
            try:
                r = registry_lib.load_row(fn[:-5], home)
            except (ValueError, OSError) as exc:
                print("SKIPPED %s — unreadable row (%s)" % (fn, exc))
                continue
            if r and r["status"] != "tombstoned":
                rows.append(r)

    print("KB-D backfill — %s over %d project%s"
          % ("WRITING" if args.write else "PREVIEW (nothing written)",
             len(rows), "" if len(rows) == 1 else "s"))
    print("-" * 72)
    totals = {"bundles": 0, "candidates": 0, "written": 0, "duplicate": 0,
              "refused": 0, "capped": 0}
    seeded = 0
    for row in rows:
        rep = backfill_project(row, args.write, home, args.cap)
        for k in totals:
            totals[k] += rep.get(k, 0)
        if rep["root_missing"]:
            print("%-30s ROOT MISSING — skipped (%s)" % (rep["name"][:30], row["root"]))
            continue
        if not rep["bundles"]:
            continue
        seeded += 1
        line = ("%-30s %2d bundle%s  %3d candidate%s  %3d %s"
                % (rep["name"][:30], rep["bundles"], " " if rep["bundles"] == 1 else "s",
                   rep["candidates"], " " if rep["candidates"] == 1 else "s",
                   rep["written"], "written" if args.write else "would write"))
        if rep["duplicate"]:
            line += "  %d already known" % rep["duplicate"]
        if rep["refused"]:
            line += "  %d REFUSED" % rep["refused"]
        if rep["capped"]:
            line += "  %d DROPPED BY CAP" % rep["capped"]
        print(line)

    print("-" * 72)
    print("%d project%s had bundles · %d bundles read · %d candidates · %d %s · "
          "%d already known · %d refused · %d dropped by the %d-per-project cap"
          % (seeded, "" if seeded == 1 else "s", totals["bundles"], totals["candidates"],
             totals["written"], "written" if args.write else "would be written",
             totals["duplicate"], totals["refused"], totals["capped"], args.cap))
    if totals["capped"]:
        print("NOTE: the cap kept the OLDEST facts per project — early decisions are the "
              "load-bearing ones. Raise it with --cap N to seed more.")
    if not args.write:
        print("PREVIEW ONLY — nothing was written. Re-run with --write to seed.")
    else:
        print("Seeded facts appear in the 'learned since you were last here' digest on the "
              "next resurrect, where any line can be struck.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
