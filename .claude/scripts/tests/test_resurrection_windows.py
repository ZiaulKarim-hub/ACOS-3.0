#!/usr/bin/env python3
"""test_resurrection_windows.py — stdlib unittest for several windows working
ONE project (MW-C and its D11/D12/D14 rules, user brief 2026-08-04).

windows_lib.py carries its own --selftest for the manifest internals. This
module covers the adopt-side naming helpers and the manifest behaviours the
receipt depends on:

D11 the one-project-one-tab guard STAYS the default; picking an already-open
    project ASKS rather than forcing the jump.
D12 window names derive from the project name — "OKOA works *label*".
D14 the row parks only when the LAST window closes.

The adopt-side helpers live in an embedded python heredoc inside
adopt-project.sh, so they are extracted and exec'd here — the assertions run
against shipped code, not a transcription.
"""

import os
import shutil
import sys
import tempfile
import unittest

_THIS = os.path.dirname(os.path.abspath(__file__))
_RESDIR = os.path.abspath(os.path.join(_THIS, os.pardir, "resurrection"))
_ADOPT = os.path.join(_RESDIR, "adopt-project.sh")
sys.path.insert(0, _RESDIR)
import windows_lib  # noqa: E402


def _adopt_body():
    with open(_ADOPT) as fh:
        src = fh.read()
    body = src.split("<<'PYEOF'\n", 1)[1].rsplit("\nPYEOF", 1)[0]
    body = body.split("\ntry:\n    sys.exit(main())", 1)[0]
    os.environ["AP_LIB_DIR"] = _RESDIR
    ns = {"__name__": "adopt_body_under_test"}
    exec(compile(body, _ADOPT + " (heredoc)", "exec"), ns)
    return ns


class WindowNamingTest(unittest.TestCase):
    """D12: the project name is always the stem."""

    @classmethod
    def setUpClass(cls):
        cls.ns = _adopt_body()

    def name_for(self, project, label, taken):
        return self.ns["window_name_for"](project, label, taken)

    def label_of(self, window_name, project):
        return self.ns["window_label_of"](window_name, project)

    def test_a_label_is_appended_to_the_project_stem(self):
        self.assertEqual(self.name_for("OKOA Works", "Golden East", []),
                         "OKOA Works Golden East")

    def test_the_first_window_is_named_plainly(self):
        self.assertEqual(self.name_for("OKOA Works", "", []), "OKOA Works")

    def test_an_unlabelled_second_window_is_numbered_not_collided(self):
        """Two tabs both reading 'OKOA Works' would be indistinguishable in the
        sidebar — the confusion D12 exists to prevent."""
        self.assertEqual(self.name_for("OKOA Works", "", ["OKOA Works"]), "OKOA Works 2")
        self.assertEqual(self.name_for("OKOA Works", "", ["OKOA Works", "OKOA Works 2"]),
                         "OKOA Works 3")

    def test_numbering_ignores_case_when_checking_what_is_taken(self):
        self.assertEqual(self.name_for("OKOA Works", "", ["okoa works"]), "OKOA Works 2")

    def test_a_given_label_wins_even_when_names_are_taken(self):
        self.assertEqual(self.name_for("OKOA Works", "Flyer", ["OKOA Works", "OKOA Works 2"]),
                         "OKOA Works Flyer")

    def test_name_and_label_round_trip(self):
        for label in ("Golden East", "Flyer", "2"):
            name = self.name_for("OKOA Works", label, [])
            self.assertEqual(self.label_of(name, "OKOA Works"), label)

    def test_the_plain_window_round_trips_to_no_label(self):
        self.assertIsNone(self.label_of("OKOA Works", "OKOA Works"))

    def test_an_unrelated_window_name_is_kept_whole(self):
        self.assertEqual(self.label_of("Something Else", "OKOA Works"), "Something Else")


class SharedProjectBriefTest(unittest.TestCase):
    """MW-C: a new window reads what the others are doing."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="mw-c-")
        self.uuid = "77777777-8888-4999-8aaa-bbbbbbbbbbbb"

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def test_a_new_window_sees_what_the_others_are_working_on(self):
        windows_lib.claim_window(self.uuid, "WS-1", label="Golden East",
                                 working_on="the outparcel pricing", home=self.home)
        windows_lib.claim_window(self.uuid, "WS-2", label="Flyer",
                                 working_on="the broker flyer", home=self.home)
        others = windows_lib.other_windows(self.uuid, "WS-3", ["WS-1", "WS-2", "WS-3"],
                                           home=self.home)
        doing = sorted(o["working_on"] for o in others)
        self.assertEqual(doing, ["the broker flyer", "the outparcel pricing"])

    def test_a_window_never_reports_itself_as_another_window(self):
        windows_lib.claim_window(self.uuid, "WS-1", label="Only", home=self.home)
        self.assertEqual(windows_lib.other_windows(self.uuid, "WS-1", ["WS-1"], home=self.home), [])

    def test_a_dead_windows_claim_is_never_counted_as_open(self):
        """A claim proves a window once opened the project, not that it still
        exists — cmux can restart under a live process."""
        windows_lib.claim_window(self.uuid, "WS-GONE", label="Ghost", home=self.home)
        live, stale = windows_lib.live_windows(self.uuid, ["WS-OTHER"], home=self.home)
        self.assertEqual(live, [])
        self.assertEqual(len(stale), 1)

    def test_reaping_never_runs_when_liveness_is_unknown(self):
        """Reaping on unknown liveness would wipe every claim the moment cmux
        is unreachable."""
        windows_lib.claim_window(self.uuid, "WS-1", label="Keep me", home=self.home)
        self.assertEqual(windows_lib.reap_stale(self.uuid, None, home=self.home), [])
        self.assertEqual(len(windows_lib.all_claims(self.uuid, self.home)), 1)

    def test_the_description_line_reads_as_a_fact(self):
        e = windows_lib.claim_window(self.uuid, "WS-1", label="Golden East",
                                     working_on="the outparcel pricing", home=self.home)
        line = windows_lib.describe(e)
        self.assertIn("Golden East", line)
        self.assertIn("the outparcel pricing", line)

    def test_an_unstated_task_says_so_rather_than_reading_as_idle(self):
        e = windows_lib.claim_window(self.uuid, "WS-1", label="Quiet", home=self.home)
        self.assertIn("not stated", windows_lib.describe(e))


class LastWindowParksTest(unittest.TestCase):
    """D14: closing ONE window does not park the project."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="mw-d14-")
        self.uuid = "88888888-9999-4aaa-8bbb-cccccccccccc"
        windows_lib.claim_window(self.uuid, "WS-1", label="One", home=self.home)
        windows_lib.claim_window(self.uuid, "WS-2", label="Two", home=self.home)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def test_closing_one_of_two_windows_is_not_the_last(self):
        self.assertFalse(windows_lib.is_last_window(self.uuid, "WS-1", ["WS-1", "WS-2"],
                                                    home=self.home))

    def test_closing_the_remaining_window_is_the_last(self):
        windows_lib.release_window(self.uuid, "WS-1", home=self.home)
        self.assertTrue(windows_lib.is_last_window(self.uuid, "WS-2", ["WS-2"], home=self.home))

    def test_unknown_liveness_is_answered_conservatively(self):
        """Returning True preserves today's behaviour (a close parks) rather
        than silently leaving rows active forever when cmux cannot be read."""
        self.assertTrue(windows_lib.is_last_window(self.uuid, "WS-1", None, home=self.home))


class MergeVerbTest(unittest.TestCase):
    """MW-D: fold one window's thread into another when the work converges."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="mw-d-")
        self.uuid = "99999999-aaaa-4bbb-8ccc-dddddddddddd"
        windows_lib.claim_window(self.uuid, "WS-1", label="Flyer",
                                 working_on="the broker flyer", home=self.home)
        windows_lib.claim_window(self.uuid, "WS-2", label="Golden East",
                                 working_on="the outparcel pricing", home=self.home)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def test_neither_threads_description_is_lost(self):
        r = windows_lib.merge_window(self.uuid, "WS-1", "WS-2", home=self.home)
        self.assertIn("the broker flyer", r["working_on"])
        self.assertIn("the outparcel pricing", r["working_on"])

    def test_the_absorbed_window_stops_reporting_as_open(self):
        windows_lib.merge_window(self.uuid, "WS-1", "WS-2", home=self.home)
        others = windows_lib.other_windows(self.uuid, "WS-2", ["WS-1", "WS-2"], home=self.home)
        self.assertEqual(others, [], "a merged-away claim would read as work still in flight")

    def test_the_target_records_what_it_absorbed(self):
        windows_lib.merge_window(self.uuid, "WS-1", "WS-2", home=self.home)
        claims = windows_lib.all_claims(self.uuid, self.home)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["merged_in"][0]["label"], "Flyer")

    def test_merging_a_window_that_never_claimed_is_refused(self):
        """Merging an unknown window would invent a thread that never existed."""
        self.assertIsNone(windows_lib.merge_window(self.uuid, "WS-NOPE", "WS-2",
                                                   home=self.home))
        self.assertIsNone(windows_lib.merge_window(self.uuid, "WS-1", "WS-NOPE",
                                                   home=self.home))


class CollisionWarningTest(unittest.TestCase):
    """MW-E: off by default, behind a switch, and never a false alarm."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="mw-e-")
        self.uuid = "aaaabbbb-cccc-4ddd-8eee-ffffffffffff"
        windows_lib.claim_window(self.uuid, "WS-1", label="One",
                                 working_on="edit A", home=self.home)
        windows_lib.claim_window(self.uuid, "WS-2", label="Two",
                                 working_on="edit B", home=self.home)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def test_it_is_off_until_the_switch_is_set(self):
        """Claude costed this high and advised deferring; Zee said do all five.
        It ships complete but dormant."""
        self.assertFalse(windows_lib.collision_warning_enabled(self.home))
        windows_lib.set_collision_warning(True, self.home)
        self.assertTrue(windows_lib.collision_warning_enabled(self.home))
        windows_lib.set_collision_warning(False, self.home)
        self.assertFalse(windows_lib.collision_warning_enabled(self.home))

    def test_only_a_genuinely_shared_file_is_reported(self):
        windows_lib.record_touch(self.uuid, "WS-1", ["/tmp/shared.py", "/tmp/mine.py"],
                                 home=self.home)
        windows_lib.record_touch(self.uuid, "WS-2", ["/tmp/shared.py", "/tmp/theirs.py"],
                                 home=self.home)
        got = windows_lib.collisions(self.uuid, "WS-1", ["WS-1", "WS-2"], home=self.home)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["files"], ["/tmp/shared.py"])

    def test_a_closed_windows_ledger_is_history_not_a_conflict(self):
        windows_lib.record_touch(self.uuid, "WS-1", ["/tmp/shared.py"], home=self.home)
        windows_lib.record_touch(self.uuid, "WS-2", ["/tmp/shared.py"], home=self.home)
        self.assertEqual(windows_lib.collisions(self.uuid, "WS-1", ["WS-1"], home=self.home), [],
                         "reporting a dead window would be a false alarm every time")

    def test_no_ledger_means_no_guess(self):
        """Nothing feeds touches automatically — the watcher is the part that
        was costed high and deferred. With no ledger it must report nothing,
        not infer something."""
        self.assertEqual(windows_lib.collisions(self.uuid, "WS-1", ["WS-1", "WS-2"],
                                                home=self.home), [])

    def test_a_window_can_find_its_own_project_without_being_told(self):
        """The feeder hook resolves the project from the claim adopt already
        wrote. One identity resolver is enough; a second would drift."""
        self.assertEqual(windows_lib.project_for_workspace("WS-1", self.home), self.uuid)
        self.assertIsNone(windows_lib.project_for_workspace("WS-NEVER-CLAIMED", self.home))
        self.assertIsNone(windows_lib.project_for_workspace(None, self.home))

    def test_the_ledger_is_capped_so_it_cannot_grow_without_bound(self):
        paths = ["/tmp/f%d.py" % i for i in range(windows_lib.TOUCH_CAP + 25)]
        windows_lib.record_touch(self.uuid, "WS-1", paths, home=self.home)
        entry = windows_lib.all_claims(self.uuid, self.home)[0]
        self.assertEqual(len(entry["touched"]), windows_lib.TOUCH_CAP)
        self.assertIn(paths[-1], entry["touched"], "the most recent touches are kept")


if __name__ == "__main__":
    unittest.main(verbosity=2)
