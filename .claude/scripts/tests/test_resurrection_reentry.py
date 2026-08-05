#!/usr/bin/env python3
"""test_resurrection_reentry.py — stdlib unittest for the reentry-note fixes
(MW-A and MW-A2, user brief 2026-08-04 / found 2026-08-05).

MW-A  adopt-project.sh used to serve the NEWEST .reentry.md anywhere under
      <root>/memory/handoffs/closed/. That is folder-scoped, and 19 registry
      rows share the ACOS 3.0 root, so it routinely served ANOTHER project's
      note (observed live: adopting 'Resurrection Protocol' returned the
      'OKOA Works' note). It also hid every note but the last when several
      windows closed one project. Notes are now project-filtered and merged.

MW-A2 close-project.sh built the bundle slug from date+name only, so two
      windows of one project closing on the SAME DAY collided and the second
      close OVERWROTE the first bundle — destroying its note, silently, exit 0.
      MW-A cannot rescue that: the note is gone before adopt scans. Bundle
      directories are now never reused.

The adopt-side logic is an embedded python heredoc inside adopt-project.sh, so
these tests EXTRACT AND EXEC THAT REAL BODY rather than re-implementing it —
the assertions run against shipped code. The close-side test drives the real
script as a subprocess under ACOS_REGISTRY_HOME / RESURRECTION_PROJECT_ROOT /
RESURRECTION_STATE_DIR overrides, so it never touches the real registry, the
real daemon state, or the real project.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

_THIS = os.path.dirname(os.path.abspath(__file__))
_RESDIR = os.path.abspath(os.path.join(_THIS, os.pardir, "resurrection"))
_ADOPT = os.path.join(_RESDIR, "adopt-project.sh")
_CLOSE = os.path.join(_RESDIR, "close-project.sh")

A_UUID = "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa"
B_UUID = "bbbbbbbb-2222-4222-8222-bbbbbbbbbbbb"


def _adopt_body():
    """Extract + exec the python heredoc from adopt-project.sh (real shipped code)."""
    with open(_ADOPT) as fh:
        src = fh.read()
    body = src.split("<<'PYEOF'\n", 1)[1].rsplit("\nPYEOF", 1)[0]
    body = body.split("\ntry:\n    sys.exit(main())", 1)[0]
    os.environ["AP_LIB_DIR"] = _RESDIR
    ns = {"__name__": "adopt_body_under_test"}
    exec(compile(body, _ADOPT + " (heredoc)", "exec"), ns)
    return ns


def _row(uuid_, name, last_close_path=None):
    """Minimal registry row shape the reentry resolver reads."""
    return {"project_uuid": uuid_, "name": name,
            "last_close": {"reentry_path": last_close_path} if last_close_path else None}


class ReentryOwnershipTest(unittest.TestCase):
    """MW-A: a note is served to the project that OWNS it, and none is hidden."""

    @classmethod
    def setUpClass(cls):
        cls.ns = _adopt_body()

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="mw-a-")
        self.closed = os.path.join(self.root, "memory", "handoffs", "closed")
        os.makedirs(self.closed)
        base = time.time() - 10000
        # legacy bundles: no owner marker, matched by slug only
        self.p_alpha_slug = self._bundle("2026-01-01-Alpha-Project-close", mtime=base + 100)
        self.p_beta_slug = self._bundle("2026-01-02-Beta-Project-close", mtime=base + 200)
        # marker bundles
        self.p_alpha_mark = self._bundle("2026-01-03-Alpha-Project-close",
                                         marker=A_UUID, mtime=base + 300)
        # slug SAYS Alpha, marker SAYS Beta — the marker must win, both ways
        self.p_conflict = self._bundle("2026-01-04-Alpha-Project-close",
                                       marker=B_UUID, mtime=base + 400)
        self.alpha = _row(A_UUID, "Alpha Project")
        self.beta = _row(B_UUID, "Beta Project")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _bundle(self, slug, marker=None, mtime=None):
        d = os.path.join(self.closed, slug)
        os.makedirs(d)
        p = os.path.join(d, "%s.reentry.md" % slug)
        with open(p, "w") as fh:
            fh.write("# Reentry — %s\n\nNEXT ACTION: work on %s\n" % (slug, slug))
        if marker:
            with open(os.path.join(d, ".project-uuid"), "w") as fh:
                fh.write(marker + "\n")
        if mtime:
            os.utime(p, (mtime, mtime))
            os.utime(d, (mtime, mtime))
        return p

    def _paths(self, row):
        notes, _closed = self.ns["collect_reentries"](self.root, row)
        return sorted(n["path"] for n in notes)

    def test_each_project_gets_only_its_own_notes(self):
        self.assertEqual(self._paths(self.alpha),
                         sorted([self.p_alpha_slug, self.p_alpha_mark]))
        self.assertEqual(self._paths(self.beta),
                         sorted([self.p_beta_slug, self.p_conflict]))

    def test_another_projects_note_is_never_served(self):
        self.assertNotIn(self.p_beta_slug, self._paths(self.alpha))
        self.assertNotIn(self.p_alpha_slug, self._paths(self.beta))

    def test_owner_marker_beats_the_slug_in_both_directions(self):
        # a marker naming Beta DENIES Alpha even though the slug reads "Alpha"
        self.assertNotIn(self.p_conflict, self._paths(self.alpha))
        self.assertIn(self.p_conflict, self._paths(self.beta))

    def test_registry_last_close_is_accepted_as_ownership_evidence(self):
        row = _row(A_UUID, "Nothing Matches This Name", last_close_path=self.p_alpha_slug)
        notes, _ = self.ns["collect_reentries"](self.root, row)
        got = [n for n in notes if n["path"] == self.p_alpha_slug]
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["evidence"], "registry last_close.reentry_path")

    def test_heuristic_matches_are_labelled_as_heuristic(self):
        notes, _ = self.ns["collect_reentries"](self.root, self.alpha)
        by_path = {n["path"]: n["evidence"] for n in notes}
        self.assertIn("HEURISTIC", by_path[self.p_alpha_slug])
        self.assertEqual(by_path[self.p_alpha_mark], ".project-uuid marker")

    def test_the_old_newest_by_mtime_scan_would_have_served_the_wrong_project(self):
        """Regression guard for the exact live failure this work exists to fix."""
        found = []
        for dp, _dn, fns in os.walk(self.closed):
            for fn in fns:
                if fn.endswith(".reentry.md"):
                    q = os.path.join(dp, fn)
                    found.append((os.stat(q).st_mtime, q))
        old_pick = sorted(found)[-1][1]
        self.assertEqual(old_pick, self.p_conflict, "fixture drift: newest is not the Beta bundle")
        primary, _src, _notes = self.ns["resolve_reentry"](self.root, self.alpha)
        self.assertNotEqual(primary, old_pick)

    def test_a_name_shared_by_two_rows_resolves_nothing(self):
        """A display name is NOT identity. Several projects can share one
        folder, and two rows can carry the same name — measured on the real
        registry: two 'FruitSync' rows and two 'Website-builder' rows. When the
        name rung fires on such a name it mis-files a whole project's history:
        before this refusal, both FruitSync rows claimed the same two bundles
        and were seeded the same 22 facts.
        """
        twin_a = _row("11110000-1111-4111-8111-111111111111", "Alpha Project")
        twin_b = _row("22220000-2222-4222-8222-222222222222", "Alpha Project")
        import bundles_lib
        shared = frozenset({bundles_lib.slug_key("Alpha Project")})
        for twin in (twin_a, twin_b):
            notes, _ = bundles_lib.collect_reentries(self.root, twin, shared_names=shared)
            self.assertEqual(notes, [], "an ambiguous name must resolve to nothing")

    def test_the_refusal_says_how_to_fix_it(self):
        import bundles_lib
        twin = _row("11110000-1111-4111-8111-111111111111", "Alpha Project")
        shared = frozenset({bundles_lib.slug_key("Alpha Project")})
        _owns, evidence = bundles_lib.bundle_owner(
            os.path.dirname(self.p_alpha_slug), twin, shared)
        self.assertIn("shared by more than one live row", evidence)
        self.assertIn(".project-uuid", evidence)

    def test_a_hard_marker_still_wins_over_an_ambiguous_name(self):
        """The refusal must not disarm the strong rungs — a bundle carrying an
        owner marker is still resolved, ambiguous name or not."""
        import bundles_lib
        marked = _row(A_UUID, "Alpha Project")
        shared = frozenset({bundles_lib.slug_key("Alpha Project")})
        notes, _ = bundles_lib.collect_reentries(self.root, marked, shared_names=shared)
        self.assertEqual([n["path"] for n in notes], [self.p_alpha_mark])

    def test_a_project_with_no_notes_says_so_instead_of_borrowing_one(self):
        gamma = _row("cccccccc-3333-4333-8333-cccccccccccc", "Gamma Project")
        primary, src, notes = self.ns["resolve_reentry"](self.root, gamma)
        self.assertIsNone(primary)
        self.assertEqual(notes, [])
        self.assertIn("no .reentry.md owned by this project", src)


class ReentryMergeAndStampTest(unittest.TestCase):
    """MW-A: every unread note surfaces; marking one read never destroys it."""

    @classmethod
    def setUpClass(cls):
        cls.ns = _adopt_body()

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="mw-a-merge-")
        self.closed = os.path.join(self.root, "memory", "handoffs", "closed")
        os.makedirs(self.closed)
        base = time.time() - 10000
        self.paths = []
        for i in (1, 2, 3):
            slug = "2026-02-0%d-Multi-Window-close" % i
            d = os.path.join(self.closed, slug)
            os.makedirs(d)
            p = os.path.join(d, "%s.reentry.md" % slug)
            with open(p, "w") as fh:
                fh.write("# Reentry — %s\n\nNEXT ACTION: window %d\n" % (slug, i))
            with open(os.path.join(d, ".project-uuid"), "w") as fh:
                fh.write(A_UUID + "\n")
            os.utime(p, (base + i * 100, base + i * 100))
            self.paths.append(p)
        self.row = _row(A_UUID, "Multi Window")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _snapshot(self):
        return sorted(os.path.relpath(os.path.join(dp, f), self.root)
                      for dp, _d, fs in os.walk(self.root) for f in fs)

    def test_all_windows_notes_surface_none_hidden_by_recency(self):
        primary, src, notes = self.ns["resolve_reentry"](self.root, self.row)
        self.assertEqual(len(notes), 3)
        self.assertTrue(all(not n["consumed"] for n in notes))
        self.assertEqual(primary, self.paths[-1], "primary should be the newest UNREAD")
        self.assertIn("project-filtered", src)

    def test_stamping_is_append_only_and_reversible(self):
        before = self._snapshot()
        _p, _s, notes = self.ns["resolve_reentry"](self.root, self.row)
        target = [n for n in notes if n["path"] == self.paths[1]]
        self.ns["mark_consumed"](target, A_UUID, "WS-TEST")

        _p2, _s2, notes2 = self.ns["resolve_reentry"](self.root, self.row)
        self.assertEqual(len(notes2), 3, "a stamped note must never drop out of the list")
        self.assertEqual(len([n for n in notes2 if not n["consumed"]]), 2)

        after = self._snapshot()
        self.assertTrue(set(before).issubset(set(after)), "no original file may disappear")
        added = set(after) - set(before)
        self.assertEqual(added, {os.path.join("memory", "handoffs", "closed",
                                              "2026-02-02-Multi-Window-close",
                                              ".reentry-consumed")})

        # un-seeing is deleting the marker — the note comes back unread
        os.remove(os.path.join(self.root, list(added)[0]))
        _p3, _s3, notes3 = self.ns["resolve_reentry"](self.root, self.row)
        self.assertEqual(len([n for n in notes3 if not n["consumed"]]), 3)

    def test_when_all_notes_are_seen_the_newest_is_still_shown(self):
        _p, _s, notes = self.ns["resolve_reentry"](self.root, self.row)
        self.ns["mark_consumed"](notes, A_UUID, "WS-TEST")
        primary, src, notes2 = self.ns["resolve_reentry"](self.root, self.row)
        self.assertIsNotNone(primary, "a fully-read project must not go blank")
        self.assertEqual(len(notes2), 3)
        self.assertIn("already surfaced", src)


class SameDayCloseCollisionTest(unittest.TestCase):
    """MW-A2: two windows closing one project on one day keep BOTH notes."""

    def setUp(self):
        self.sb = tempfile.mkdtemp(prefix="mw-a2-")
        self.proj = os.path.join(self.sb, "proj")
        os.makedirs(self.proj)
        subprocess.run(["git", "init", "-q"], cwd=self.proj, check=True)
        with open(os.path.join(self.proj, "r.txt"), "w") as fh:
            fh.write("hi\n")
        subprocess.run(["git", "add", "-A"], cwd=self.proj, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-qm", "init"], cwd=self.proj, check=True)

    def tearDown(self):
        shutil.rmtree(self.sb, ignore_errors=True)

    def _close(self, n):
        intent = os.path.join(self.sb, "intent%d.md" % n)
        with open(intent, "w") as fh:
            fh.write("next_action: Window %d closing on the very same day\n"
                     "project: MW-A2 collision test\n"
                     "decisions: |\n  - Window %d of the same project.\n"
                     "traps: |\n  - Same-day slug collision is the thing under test.\n"
                     "open_questions: |\n  - None.\n" % (n, n))
        env = dict(os.environ,
                   RESURRECTION_SKIP_CMUX="1",
                   ACOS_REGISTRY_HOME=os.path.join(self.sb, "home"),
                   RESURRECTION_STATE_DIR=os.path.join(self.sb, "state"),
                   RESURRECTION_PROJECT_ROOT=self.proj)
        return subprocess.run(["bash", _CLOSE, "--intent-file", intent,
                               "--session-id", "0000000%d-2222-3333-4444-555555555555" % n],
                              cwd=self.proj, env=env, capture_output=True, text=True)

    def test_three_same_day_closes_keep_all_three_notes(self):
        outs = [self._close(i) for i in (1, 2, 3)]
        for i, o in enumerate(outs, 1):
            self.assertEqual(o.returncode, 0, "close %d failed:\n%s" % (i, o.stdout + o.stderr))

        closed = os.path.join(self.proj, "memory", "handoffs", "closed")
        bundles = sorted(os.listdir(closed))
        self.assertEqual(len(bundles), 3, "expected one bundle per close, got %r" % bundles)

        actions = []
        for b in bundles:
            for fn in os.listdir(os.path.join(closed, b)):
                if fn.endswith(".reentry.md"):
                    with open(os.path.join(closed, b, fn)) as fh:
                        actions += [ln.strip() for ln in fh if ln.startswith("NEXT ACTION")]
        for i in (1, 2, 3):
            self.assertTrue(any("Window %d " % i in a for a in actions),
                            "window %d's note was destroyed; got %r" % (i, actions))

    def test_the_collision_is_announced_never_silent(self):
        self._close(1)
        second = self._close(2)
        self.assertIn("BUNDLE COLLISION", second.stdout,
                      "a redirected bundle must be reported, not silent")

    def test_every_bundle_carries_its_owner_marker(self):
        self._close(1)
        self._close(2)
        closed = os.path.join(self.proj, "memory", "handoffs", "closed")
        for b in os.listdir(closed):
            marker = os.path.join(closed, b, ".project-uuid")
            self.assertTrue(os.path.isfile(marker), "%s has no owner marker" % b)
            with open(marker) as fh:
                self.assertEqual(len(fh.read().strip()), 36, "marker is not a uuid")


if __name__ == "__main__":
    unittest.main(verbosity=2)
