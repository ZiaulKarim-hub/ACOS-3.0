#!/usr/bin/env python3
"""stamp-bundle-owners.py — write the owner marker on close bundles that lack one.

  stamp-bundle-owners.py            dry run: what would be stamped, and why
  stamp-bundle-owners.py --apply    write the markers

WHY (Zee, 2026-08-24). A close bundle under <root>/memory/handoffs/closed/ says
which row owns it in a `.project-uuid` marker file. Bundles written before that
marker existed have none, so bundles_lib falls back to matching the folder name
— and labels that answer HEURISTIC, because a name is not proof. That was fine
while ownership only picked which reentry note to show. It stops being fine once
`delete` ARCHIVES a row's bundles: archiving on a guess moves another project's
history.

The fix is not to refuse. It is to stamp. MEASURED 2026-08-24 across every
registered root: 119 bundles, 91 already stamped, 28 not. Of those 28, 24 are
claimed by exactly ONE row — `2026-07-24-Word-gen-close` can only be Word-gen.
Stamping those retires the guessing permanently, for them and for every future
delete.

TWO RUNGS, and the second one is why 3 "unclaimed" bundles are really 1.
  1. NAME — bundles_lib's own resolver. It deliberately refuses a display name
     shared by more than one LIVE row, because a shared name identifies neither.
     Measured harm it prevents: both `FruitSync` rows once claimed the same two
     bundles and were seeded the same 22 facts.
  2. SOLE ROW AT THIS FOLDER — a bundle physically lives under one project root.
     If exactly ONE registered row calls that folder its root, that row owns the
     bundle, and a name shared with a row at a DIFFERENT folder cannot make it
     ambiguous. This is strictly stronger evidence than the name, not weaker:
     location is a fact about the file, not a resemblance.
     It rescues the two `Website-builder` bundles sitting in the Website Builder
     folder, whose name is shared with a second row rooted at ACOS 3.0.

WHAT IT REFUSES TO DECIDE. A bundle claimed by more than one row, or by none
under either rung, is REPORTED and left alone. Those are the duplicate-row pairs
Zee is merging — two rows at ONE folder, which neither rung can split. After a
merge one row remains and the ambiguity resolves itself. Re-run this then.

SAFE BY CONSTRUCTION:
  * only ever CREATES a marker file; never edits, moves or deletes a bundle
  * never overwrites an existing marker — a stamped bundle is already decided
  * a wrong stamp is undone by deleting one small file

HUMAN-INITIATED ONLY, like every verb in manage-ordinals.py.

Exit codes: 0 = done, 1 = refused (a stated reason), 2 = could not run.
"""

import argparse
import os
import sys

HERE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE_DIR)
import bundles_lib  # noqa: E402
import registry_lib  # noqa: E402

MARKER = bundles_lib.OWNER_MARKER


def classify(home=None):
    """(stampable, ambiguous, unclaimed, already) over every registered root."""
    rows = list(registry_lib._iter_rows(home))
    shared = bundles_lib.ambiguous_names(home)
    by_root = {}
    for r in rows:
        by_root.setdefault(r["root_casefold"], []).append(r)

    stampable, ambiguous, unclaimed, already = [], [], [], 0
    for root in sorted({r["root"] for r in rows}):
        cdir = os.path.join(root, "memory", "handoffs", "closed")
        if not os.path.isdir(cdir):
            continue
        siblings = by_root.get(os.path.realpath(root).casefold(), [])
        for name in sorted(os.listdir(cdir)):
            bundle = os.path.join(cdir, name)
            if not os.path.isdir(bundle):
                continue
            if os.path.exists(os.path.join(bundle, MARKER)):
                already += 1
                continue
            hits = [r for r in siblings if bundles_lib.bundle_owner(bundle, r, shared)[0]]
            if len(hits) == 1:
                stampable.append((bundle, hits[0], "name match, sole claimant"))
            elif len(hits) > 1:
                ambiguous.append((bundle, hits))
            elif len(siblings) == 1:
                # Rung 2. The bundle lives under exactly one root, and exactly
                # one row claims that root. Nothing else can own it.
                stampable.append((bundle, siblings[0],
                                  "sole row at this folder (name is shared elsewhere)"))
            else:
                unclaimed.append((bundle, siblings))
    return stampable, ambiguous, unclaimed, already


def main(argv=None):
    ap = argparse.ArgumentParser(prog="stamp-bundle-owners.py",
                                 description=__doc__.splitlines()[0])
    ap.add_argument("--home", default=None, help="override ~ (tests only)")
    ap.add_argument("--apply", action="store_true", help="write the markers")
    args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    home = args.home or os.environ.get("ACOS_REGISTRY_HOME") or None

    stampable, ambiguous, unclaimed, already = classify(home)
    print("close bundles: %d already stamped, %d stampable, %d ambiguous, %d unclaimed"
          % (already, len(stampable), len(ambiguous), len(unclaimed)))
    print("")

    if stampable:
        print("STAMPABLE — exactly one row can own each of these:")
        for bundle, row, why in stampable:
            print("  %-46s -> %-24s [%s]"
                  % (os.path.basename(bundle)[:46], row["name"][:24], why))
        print("")
    if ambiguous:
        print("AMBIGUOUS — more than one row claims these; LEFT ALONE:")
        for bundle, hits in ambiguous:
            print("  %-52s -> %s" % (os.path.basename(bundle)[:52],
                                     ", ".join(h["name"] for h in hits)))
        print("  Merge those rows first; the survivor then owns the bundle. Re-run this.")
        print("")
    if unclaimed:
        print("UNCLAIMED — neither rung settles these; LEFT ALONE:")
        for bundle, siblings in unclaimed:
            print("  %-52s" % os.path.basename(bundle)[:52])
            print("       rows at that folder (%d): %s"
                  % (len(siblings), ", ".join(r["name"] for r in siblings) or "none"))
        print("  Two rows at ONE folder: merge them, then re-run — the survivor owns it.")
        print("  No row at all: enrol one, or leave the bundle where it is.")
        print("")

    if not stampable:
        print("nothing to stamp.")
        return 0
    if not args.apply:
        print("DRY RUN — no marker written. Re-run with --apply.")
        return 0

    written = 0
    for bundle, row, _why in stampable:
        path = os.path.join(bundle, MARKER)
        if os.path.exists(path):        # re-checked: never overwrite a decision
            continue
        with open(path, "w") as fh:
            fh.write(row["project_uuid"] + "\n")
        written += 1
    print("STAMPED %d bundle%s." % (written, "" if written == 1 else "s"))
    print("  Each now carries a %s file naming its row. Ownership is proof, not a guess."
          % MARKER)
    print("  To undo one, delete that single file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
