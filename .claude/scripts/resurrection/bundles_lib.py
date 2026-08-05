#!/usr/bin/env python3
"""bundles_lib.py — whose closed bundle is this? (ACOS Resurrection Protocol.)

A "bundle" is one directory under <root>/memory/handoffs/closed/, holding a
handoff.yaml and a <slug>.reentry.md written by one safe-close.

WHY THIS FILE EXISTS (MW-A, user brief 2026-08-04). adopt-project.sh used to
take the NEWEST .reentry.md anywhere under closed/. That is folder-scoped, and
19 registry rows share the ACOS 3.0 root, so it routinely handed a tab ANOTHER
project's note — observed live on 2026-08-05: adopting "Resurrection Protocol"
returned the "OKOA Works" note. It also hid every note but the last whenever
several windows closed one project.

Ownership now decides which bundle belongs to which project, and it lives HERE
rather than inside adopt-project.sh's heredoc because three callers need the
same answer — adopt (which note to show), backfill (whose knowledge to seed),
and the merge verb. Two copies of this ladder would drift, and a drifted
ownership rule silently mis-files someone's work.

THE LADDER, strongest evidence first. Every answer carries its evidence string
so a HEURISTIC match is visible AS a heuristic and never passes for certainty:

  1. <bundle>/.project-uuid — the hard marker close-project.sh writes once the
     row's uuid is known. Authoritative BOTH ways: a marker naming a different
     project is a definitive NO, never a fall-through to (3).
  2. the row's own last_close.reentry_path — an exact registry-recorded link,
     correct for each project's most recent close.
  3. slug match: <date>-<Name>-close against the row's name, punctuation
     flattened. Bundles written before the marker existed have nothing else.
     THIS RUNG REFUSES when the name points at more than one live row. Several
     projects can share one folder, and two rows can carry the same display
     name, so a name is not identity — it is only a last-resort hint, and a
     hint that points two ways is no hint at all. Measured harm before this
     refusal existed: both "FruitSync" rows claimed the same two bundles and
     were seeded the same 22 facts. Closing such a project once writes its
     .project-uuid marker and retires the guessing for good.

Constraints: stdlib only, python 3.9.6. Python (not TypeScript/Rust) because
it is imported by the embedded python body of adopt-project.sh, which is fixed
to the system interpreter — the existing-code exception.

Self-test: python3 bundles_lib.py --selftest --home DIR
"""

import argparse
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone

REENTRY_SUFFIX = ".reentry.md"
OWNER_MARKER = ".project-uuid"
CONSUMED_MARKER = ".reentry-consumed"

_SLUG_NOISE = re.compile(r"[^a-z0-9]+")
_SLUG_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-(?P<name>.+?)(?:-\d+)?-close(?:-\d+)?$")


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def closed_dir(root):
    return os.path.join(root, "memory", "handoffs", "closed")


def slug_key(text):
    """Punctuation-flattened casefold key, for slug <-> project-name comparison."""
    return _SLUG_NOISE.sub("", (text or "").casefold())


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read().strip()
    except (OSError, IOError):
        return None


def slug_name(bundle_dir):
    """The project-name part of a bundle slug, or None.

    Tolerates the MW-A2 collision suffix (`...-close-2`), so a project's second
    same-day bundle is still recognised as that project's.
    """
    m = _SLUG_RE.match(os.path.basename(str(bundle_dir).rstrip(os.sep)))
    return m.group("name") if m else None


def ambiguous_names(home=None):
    """Display names shared by MORE THAN ONE live row, casefolded.

    Several projects can live in one folder, and two rows can carry the same
    display name — measured on the real registry: two 'FruitSync' rows and two
    'Website-builder' rows. A name that points at two rows cannot identify
    either of them, so the name rung below must REFUSE on these rather than
    pick one. Guessing here mis-files a whole project's history.
    """
    try:
        import registry_lib
    except ImportError:
        return frozenset()
    counts = {}
    d = registry_lib.registry_dir(home)
    try:
        files = os.listdir(d)
    except OSError:
        return frozenset()
    for fn in sorted(files):
        if not fn.endswith(".json"):
            continue
        try:
            row = registry_lib.load_row(fn[:-5], home)
        except (ValueError, OSError):
            continue
        if row is None or row["status"] == "tombstoned":
            continue
        k = slug_key(row.get("name"))
        counts[k] = counts.get(k, 0) + 1
    return frozenset(k for k, n in counts.items() if n > 1)


def bundle_owner(bundle_dir, row, shared_names=frozenset()):
    """(owns: bool, evidence: str) — does `row` own this bundle?

    `shared_names` is the set from ambiguous_names(): display names that point
    to more than one live row. The name rung refuses on those.
    """
    marker = read_text(os.path.join(bundle_dir, OWNER_MARKER))
    if marker:
        return (marker.casefold() == row["project_uuid"].casefold(),
                "%s marker" % OWNER_MARKER)
    recorded = (row.get("last_close") or {}).get("reentry_path") or ""
    if recorded and os.path.dirname(os.path.abspath(recorded)) == os.path.abspath(bundle_dir):
        return True, "registry last_close.reentry_path"
    name = slug_name(bundle_dir)
    if name and slug_key(name) == slug_key(row.get("name")):
        # A name shared by two live rows identifies neither. Refuse rather than
        # hand one project another's history — measured harm: both 'FruitSync'
        # rows claimed the same two bundles and were seeded the same 22 facts.
        if slug_key(row.get("name")) in shared_names:
            return False, ("name %r is shared by more than one live row — refusing to "
                           "guess; close this project once to write its %s marker"
                           % (row.get("name"), OWNER_MARKER))
        return True, "slug name match (HEURISTIC — bundle predates %s)" % OWNER_MARKER
    return False, "no owner evidence"


def collect_reentries(root, row, home=None, shared_names=None):
    """Every .reentry.md under closed/ that belongs to THIS project, newest first.

    Returns (notes, closed_dir_path). Each note: path, bundle, evidence,
    consumed, mtime. Notes owned by OTHER projects are excluded — that
    exclusion is the whole point.

    `shared_names` defaults to the live registry's ambiguous display names, so
    the weakest rung of the ownership ladder never resolves a name that points
    at two rows. Pass an explicit set to control it (tests do).
    """
    if shared_names is None:
        shared_names = ambiguous_names(home)
    cdir = closed_dir(root)
    notes = []
    for dirpath, _dirnames, filenames in os.walk(cdir):
        owns = evidence = None
        for fn in filenames:
            if not fn.endswith(REENTRY_SUFFIX):
                continue
            if owns is None:
                owns, evidence = bundle_owner(dirpath, row, shared_names)
            if not owns:
                continue
            p = os.path.join(dirpath, fn)
            try:
                mtime = os.stat(p).st_mtime
            except OSError:
                continue
            notes.append({"path": p, "bundle": dirpath, "evidence": evidence,
                          "consumed": os.path.isfile(os.path.join(dirpath, CONSUMED_MARKER)),
                          "mtime": mtime})
    notes.sort(key=lambda n: n["mtime"], reverse=True)
    return notes, cdir


def resolve_reentry(root, row, home=None, shared_names=None):
    """(primary_path_or_None, source_note, notes) — project-filtered and merged.

    `primary` keeps the single-path contract callers already rely on: the
    NEWEST UNREAD note owned by this project. `notes` carries the rest, so
    nothing is hidden by recency.
    """
    notes, cdir = collect_reentries(root, row, home, shared_names)
    unread = [n for n in notes if not n["consumed"]]
    if unread:
        return unread[0]["path"], (
            "project-filtered merge — %d unread note%s owned by this project, of %d owned "
            "(NOT newest-in-folder)" % (len(unread), "" if len(unread) == 1 else "s", len(notes))
        ), notes
    if notes:
        return notes[0]["path"], (
            "project-filtered merge — all %d owned note%s already surfaced; showing the newest"
            % (len(notes), "" if len(notes) == 1 else "s")
        ), notes
    recorded = (row.get("last_close") or {}).get("reentry_path")
    if recorded and os.path.isfile(recorded):
        return recorded, ("FALLBACK: no .reentry.md owned by this project under %s — using the "
                          "registry-recorded reentry_path (may be stale; the scan is the truth "
                          "source)" % cdir), []
    return None, ("no .reentry.md owned by this project under %s, and no usable "
                  "registry-recorded reentry_path" % cdir), []


def mark_consumed(notes, project_uuid, ws_id):
    """Stamp each surfaced note's bundle as seen. APPEND-ONLY: the note file is
    never moved and never deleted, so a wrong stamp is undone by deleting the
    marker. Never fatal — a failed stamp leaves the note unread, which is the
    safe direction."""
    stamped = []
    for n in notes:
        mp = os.path.join(n["bundle"], CONSUMED_MARKER)
        try:
            with open(mp, "a") as fh:
                fh.write("surfaced_at: %s\nproject_uuid: %s\nworkspace: %s\n\n"
                         % (utc_now_iso(), project_uuid, ws_id))
            stamped.append(mp)
        except (OSError, IOError) as exc:
            print("WARN: could not stamp %s (%s) — that note stays UNREAD and will "
                  "surface again next adopt" % (mp, exc))
    return stamped


# --------------------------------------------------------------------------
# handoff.yaml reading — line-prefix parsing, never a yaml library
# --------------------------------------------------------------------------

def parse_handoff(path):
    """The handoff's scalar keys plus its literal blocks.

    System python has NO yaml module, and close-project.sh writes a stable
    line format on purpose, so this reads by line prefix — the same discipline
    close-project.sh's own parser uses. Returns {} on an unreadable file rather
    than raising: a malformed bundle must not stop a sweep over 24 of them.
    """
    out, block_key, block_lines = {}, None, []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return {}
    for line in lines:
        if block_key is not None:
            if line.startswith("  ") or not line.strip():
                block_lines.append(line[2:] if line.startswith("  ") else "")
                continue
            out[block_key] = "\n".join(block_lines).rstrip()
            block_key, block_lines = None, []
        if not line or line.startswith(" ") or line.startswith("-"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if val == "|":
            block_key, block_lines = key, []
        elif val:
            out[key] = val
    if block_key is not None:
        out[block_key] = "\n".join(block_lines).rstrip()
    return out


def iter_bundles(root):
    """Every bundle directory under closed/, oldest first by name (the slug
    starts with the date, so name order IS date order)."""
    cdir = closed_dir(root)
    try:
        names = sorted(os.listdir(cdir))
    except OSError:
        return []
    out = []
    for n in names:
        d = os.path.join(cdir, n)
        if os.path.isdir(d) and os.path.isfile(os.path.join(d, "handoff.yaml")):
            out.append(d)
    return out


def _selftest(home):
    if not home:
        print("REFUSED: selftest must run under a --home override, never the real ~")
        return 1
    failures = []

    def ck(label, cond, detail=""):
        if cond:
            print("  PASS  %s" % label)
        else:
            print("  FAIL  %s %s" % (label, detail))
            failures.append(label)

    root = tempfile.mkdtemp(dir=home, prefix="root-")
    cdir = closed_dir(root)
    os.makedirs(cdir)

    def bundle(slug, marker=None, next_action="do a thing"):
        d = os.path.join(cdir, slug)
        os.makedirs(d)
        with open(os.path.join(d, "%s.reentry.md" % slug), "w") as fh:
            fh.write("# Reentry — %s\n\nNEXT ACTION: %s\n" % (slug, next_action))
        with open(os.path.join(d, "handoff.yaml"), "w") as fh:
            fh.write("timestamp: 2026-01-01T00:00:00+00:00\nslug: %s\n"
                     "project_root: %s\nnext_action: %s\n"
                     "intent_core: |\n  traps: one trap line\n  second line\n" % (slug, root, next_action))
        if marker:
            with open(os.path.join(d, OWNER_MARKER), "w") as fh:
                fh.write(marker + "\n")
        return d

    A = {"project_uuid": "aaaa1111-2222-4333-8444-555555555555", "name": "Alpha Project",
         "last_close": None}
    B = {"project_uuid": "bbbb1111-2222-4333-8444-555555555555", "name": "Beta Project",
         "last_close": None}
    b_slug_a = bundle("2026-01-01-Alpha-Project-close")
    bundle("2026-01-02-Beta-Project-close")
    bundle("2026-01-03-Alpha-Project-close", marker=A["project_uuid"])
    b_conflict = bundle("2026-01-04-Alpha-Project-close", marker=B["project_uuid"])
    b_seq = bundle("2026-01-05-Alpha-Project-close-2")

    print("ownership ladder")
    a_notes, _ = collect_reentries(root, A)
    a_bundles = {n["bundle"] for n in a_notes}
    ck("Alpha owns its slug, marker and sequenced bundles", len(a_notes) == 3, len(a_notes))
    ck("the MW-A2 sequence suffix still resolves", b_seq in a_bundles)
    ck("a marker naming Beta denies Alpha", b_conflict not in a_bundles)
    ck("Beta owns the conflict bundle", b_conflict in {n["bundle"] for n in collect_reentries(root, B)[0]})

    print("evidence is reported, never assumed")
    ev = {n["bundle"]: n["evidence"] for n in a_notes}
    ck("heuristic matches say so", "HEURISTIC" in ev[b_slug_a], ev[b_slug_a])

    print("consume is append-only")
    primary, _src, notes = resolve_reentry(root, A)
    ck("primary is an unread owned note", primary is not None)
    mark_consumed([n for n in notes if n["bundle"] == b_seq], A["project_uuid"], "WS")
    ck("stamped note still on disk", os.path.isfile(os.path.join(b_seq, "%s.reentry.md"
                                                                 % os.path.basename(b_seq))))
    ck("stamped note now reads as seen",
       len([n for n in collect_reentries(root, A)[0] if not n["consumed"]]) == 2)

    print("handoff parsing without a yaml module")
    h = parse_handoff(os.path.join(b_seq, "handoff.yaml"))
    ck("scalar keys read", h.get("slug") == os.path.basename(b_seq), h.get("slug"))
    ck("literal block read", "one trap line" in (h.get("intent_core") or ""), h.get("intent_core"))
    ck("a missing file is {} not a crash", parse_handoff("/nope/handoff.yaml") == {})
    ck("bundles enumerated", len(iter_bundles(root)) == 5, len(iter_bundles(root)))

    shutil.rmtree(root, ignore_errors=True)
    print()
    if failures:
        print("FAILED: %d — %s" % (len(failures), "; ".join(failures)))
        return 1
    print("bundles_lib selftest: ALL PASSED")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="closed-bundle ownership and reading")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--home", default=None)
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest(args.home)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
