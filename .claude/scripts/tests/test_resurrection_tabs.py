#!/usr/bin/env python3
"""test_resurrection_tabs.py — the TAB route (brief item 2, Zee 2026-08-25).

A "window" on a project used to mean a cmux WORKSPACE, always. Opting in with
`tab` makes the second window a TAB inside the workspace the project is
already open in, so one project keeps one workspace however many windows it
has. The workspace route is untouched and stays the default; nothing here
passes unless that is still true.

What is covered, and why each one is here rather than assumed:

  the key       a window is identified by the PAIR (workspace, tab). A
                workspace-route window keeps its BARE workspace id, so every
                manifest written before the tab route still loads — there is no
                migration, and this suite is what says so.
  MW-C          two tabs in one workspace must SEE each other. Keyed on the
                workspace they collapsed into one file and `other_windows`
                returned [] forever.
  D14           closing one tab must NOT park a project whose sibling tab is
                still working. That followed directly from the [] above.
  liveness      a CLOSED tab in a still-open workspace is stale — but only when
                a surface list was supplied. Without one it is unverifiable,
                and an unverifiable tab is never reaped.
  self-merge    merging a window into itself read one file into two variables,
                wrote it back, then released the source — deleting the very
                entry it had just written.
  route words   `here`, `tab`, `window` and `adopt` are routes, not row names.
                `20 here` typed as a reply to the book used to resolve `here`
                as a NAME, fail, and then all-or-nothing refused the valid 20
                along with it.
  the default   a bare number still opens a WORKSPACE. This is the test that
                fails if the opt-in ever stops being opt-in.

Everything runs against a FIXTURE registry under a throwaway home with
RESURRECTION_SKIP_CMUX=1, so nothing reads or writes the real ~/.acos and
nothing touches live cmux.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

_THIS = os.path.dirname(os.path.abspath(__file__))
_RESDIR = os.path.abspath(os.path.join(_THIS, os.pardir, "resurrection"))
sys.path.insert(0, _RESDIR)
import ordinal_lib  # noqa: E402
import registry_lib  # noqa: E402
import windows_lib  # noqa: E402

OPEN_PICKS = os.path.join(_RESDIR, "open-picks.sh")
LAUNCH = os.path.join(_RESDIR, "launch-project.sh")

U = "11111111-2222-4333-8444-555555555555"


class TabBase(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="tab-test-")
        os.makedirs(registry_lib.registry_dir(self.home), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def mkrow(self, uuid, name, ordinal, status="parked"):
        root = os.path.join(self.home, "roots", name)
        os.makedirs(root, exist_ok=True)
        st = os.stat(root)
        row = {
            "project_uuid": uuid, "root": root,
            "root_casefold": os.path.realpath(root).casefold(),
            "dev_ino": [st.st_dev, st.st_ino], "name": name,
            "workspace_name": name, "status": status,
            "enrolled_at": "2026-01-01T00:00:00+00:00",
            "last_verified_at": "2026-01-01T00:00:00+00:00",
            "last_close": None, "last_session_id_hint": None, "git": None,
            "tombstoned_at": None, "pick_ordinal": ordinal,
        }
        registry_lib.atomic_write_json(registry_lib.row_path(uuid, self.home), row)
        if ordinal is not None:
            ordinal_lib.append_event("issue", ordinal, uuid, name, self.home)
        return row

    def env(self, **extra):
        e = dict(os.environ)
        e["ACOS_REGISTRY_HOME"] = self.home
        e["RESURRECTION_SKIP_CMUX"] = "1"
        e.pop("CMUX_WORKSPACE_ID", None)
        e.pop("CMUX_SURFACE_ID", None)
        e.update(extra)
        return e

    def picks(self, *argv):
        return subprocess.run(["/bin/bash", OPEN_PICKS] + list(argv),
                              capture_output=True, text=True, timeout=180,
                              env=self.env(), cwd=self.home)

    def launch(self, *argv):
        return subprocess.run(["/bin/bash", LAUNCH] + list(argv),
                              capture_output=True, text=True, timeout=180,
                              env=self.env(), cwd=self.home)


# ---------------------------------------------------------------------------
# the key — a window is the PAIR, and yesterday's manifests still load
# ---------------------------------------------------------------------------
class WindowKeyTest(TabBase):
    def test_a_workspace_route_window_keeps_its_bare_id(self):
        self.assertEqual(windows_lib.window_key("WS-A"), "WS-A")
        self.assertEqual(windows_lib.window_key("WS-A", None), "WS-A")
        self.assertEqual(windows_lib.window_key("WS-A", ""), "WS-A")

    def test_a_tab_appends_its_own_id(self):
        self.assertEqual(windows_lib.window_key("WS-A", "SF-1"), "WS-A__SF-1")

    def test_a_manifest_written_before_tabs_existed_still_resolves(self):
        # No window_key, no surface_id — exactly what was on disk before.
        legacy = {"project_uuid": U, "workspace_id": "WS-OLD", "label": "Old"}
        self.assertEqual(windows_lib.claim_key(legacy), "WS-OLD")

    def test_the_stored_key_wins_over_a_rebuild(self):
        e = windows_lib.claim_window(U, "WS-A", surface_id="SF-1", home=self.home)
        self.assertEqual(e["window_key"], "WS-A__SF-1")
        self.assertEqual(windows_lib.claim_key(e), "WS-A__SF-1")

    def test_two_tabs_in_one_workspace_are_two_claims(self):
        windows_lib.claim_window(U, "WS", surface_id="SF-1", label="One", home=self.home)
        windows_lib.claim_window(U, "WS", surface_id="SF-2", label="Two", home=self.home)
        claims = windows_lib.all_claims(U, self.home)
        self.assertEqual(len(claims), 2)
        self.assertEqual({c["label"] for c in claims}, {"One", "Two"})

    def test_a_tab_and_its_host_can_share_one_workspace(self):
        windows_lib.claim_window(U, "WS", label="The workspace", home=self.home)
        windows_lib.claim_window(U, "WS", surface_id="SF-1", label="A tab", home=self.home)
        self.assertEqual(len(windows_lib.all_claims(U, self.home)), 2)


# ---------------------------------------------------------------------------
# MW-C and D14 across tabs
# ---------------------------------------------------------------------------
class SiblingTabTest(TabBase):
    def setUp(self):
        super().setUp()
        windows_lib.claim_window(U, "WS", surface_id="SF-1", label="One",
                                 working_on="the first thread", home=self.home)
        windows_lib.claim_window(U, "WS", surface_id="SF-2", label="Two",
                                 working_on="the second thread", home=self.home)

    def test_a_sibling_tab_is_seen_as_another_window(self):
        others = windows_lib.other_windows(U, "WS", ["WS"], self.home,
                                           my_surface_id="SF-1",
                                           live_surface_ids=["SF-1", "SF-2"])
        self.assertEqual(len(others), 1)
        self.assertEqual(others[0]["label"], "Two")
        self.assertEqual(others[0]["working_on"], "the second thread")

    def test_a_tab_is_never_its_own_sibling(self):
        others = windows_lib.other_windows(U, "WS", ["WS"], self.home,
                                           my_surface_id="SF-1",
                                           live_surface_ids=["SF-1", "SF-2"])
        self.assertTrue(all(o.get("surface_id") != "SF-1" for o in others))

    def test_closing_one_tab_does_not_park_while_the_sibling_works(self):
        self.assertFalse(windows_lib.is_last_window(
            U, "WS", ["WS"], self.home, my_surface_id="SF-1",
            live_surface_ids=["SF-1", "SF-2"]))

    def test_the_last_tab_standing_does_park(self):
        self.assertTrue(windows_lib.is_last_window(
            U, "WS", ["WS"], self.home, my_surface_id="SF-1",
            live_surface_ids=["SF-1"]))

    def test_a_tab_says_it_is_a_tab_in_the_receipt(self):
        others = windows_lib.other_windows(U, "WS", ["WS"], self.home,
                                           my_surface_id="SF-1",
                                           live_surface_ids=["SF-1", "SF-2"])
        self.assertIn("[tab]", windows_lib.describe(others[0]))


# ---------------------------------------------------------------------------
# liveness — the second dimension, and what happens without it
# ---------------------------------------------------------------------------
class TabLivenessTest(TabBase):
    def setUp(self):
        super().setUp()
        windows_lib.claim_window(U, "WS", surface_id="SF-1", label="Open", home=self.home)
        windows_lib.claim_window(U, "WS", surface_id="SF-2", label="Closed", home=self.home)

    def test_a_closed_tab_in_a_live_workspace_is_stale(self):
        live, stale = windows_lib.live_windows(U, ["WS"], self.home, live_surface_ids=["SF-1"])
        self.assertEqual([c["label"] for c in live], ["Open"])
        self.assertEqual([c["label"] for c in stale], ["Closed"])

    def test_without_a_surface_list_a_tab_falls_back_to_its_workspace(self):
        live, stale = windows_lib.live_windows(U, ["WS"], self.home)
        self.assertEqual(len(live), 2)
        self.assertEqual(stale, [])

    def test_an_unverifiable_tab_is_never_reaped(self):
        self.assertEqual(windows_lib.reap_stale(U, ["WS"], self.home), [])
        self.assertEqual(len(windows_lib.all_claims(U, self.home)), 2)

    def test_with_a_surface_list_the_closed_tab_is_reaped(self):
        reaped = windows_lib.reap_stale(U, ["WS"], self.home, live_surface_ids=["SF-1"])
        self.assertEqual([c["label"] for c in reaped], ["Closed"])
        self.assertEqual(len(windows_lib.all_claims(U, self.home)), 1)

    def test_a_tab_of_a_DEAD_workspace_is_reaped_without_a_surface_list(self):
        reaped = windows_lib.reap_stale(U, ["SOME-OTHER-WS"], self.home)
        self.assertEqual(len(reaped), 2)

    def test_reaping_is_still_refused_on_unknown_workspace_liveness(self):
        self.assertEqual(windows_lib.reap_stale(U, None, self.home), [])
        self.assertEqual(len(windows_lib.all_claims(U, self.home)), 2)


# ---------------------------------------------------------------------------
# the resolver, and the self-merge that used to delete its own target
# ---------------------------------------------------------------------------
class ResolverAndMergeTest(TabBase):
    def setUp(self):
        super().setUp()
        windows_lib.claim_window(U, "WS", label="Host", working_on="the host thread",
                                 home=self.home)
        windows_lib.claim_window(U, "WS", surface_id="SF-1", label="Tab",
                                 working_on="the tab thread", home=self.home)

    def test_a_tab_resolves_to_its_project(self):
        self.assertEqual(windows_lib.project_for_workspace("WS", self.home, "SF-1"), U)

    def test_the_workspace_route_window_resolves_without_a_surface(self):
        self.assertEqual(windows_lib.project_for_workspace("WS", self.home), U)

    def test_an_unclaimed_tab_falls_back_to_its_workspace_project(self):
        self.assertEqual(windows_lib.project_for_workspace("WS", self.home, "SF-UNKNOWN"), U)

    def test_an_unknown_workspace_resolves_to_nothing(self):
        self.assertIsNone(windows_lib.project_for_workspace("WS-NOPE", self.home))

    def test_merging_a_window_into_itself_is_refused(self):
        key = windows_lib.window_key("WS", "SF-1")
        self.assertIsNone(windows_lib.merge_window(U, key, key, self.home))

    def test_and_the_target_survives_that_refusal(self):
        key = windows_lib.window_key("WS", "SF-1")
        windows_lib.merge_window(U, key, key, self.home)
        claims = {c["label"] for c in windows_lib.all_claims(U, self.home)}
        self.assertEqual(claims, {"Host", "Tab"})

    def test_a_tab_folds_into_the_host_window(self):
        r = windows_lib.merge_window(U, windows_lib.window_key("WS", "SF-1"), "WS", self.home)
        self.assertIsNotNone(r)
        self.assertIn("the tab thread", r["working_on"])
        self.assertIn("the host thread", r["working_on"])

    def test_the_merged_tab_is_released_and_recorded(self):
        windows_lib.merge_window(U, windows_lib.window_key("WS", "SF-1"), "WS", self.home)
        claims = windows_lib.all_claims(U, self.home)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["merged_in"][0]["surface_id"], "SF-1")


# ---------------------------------------------------------------------------
# route words — the bug Zee hit typing `20 here` at the rendered book
# ---------------------------------------------------------------------------
class RouteWordTest(TabBase):
    def setUp(self):
        super().setUp()
        self.mkrow(U, "Alpha", 1)
        self.mkrow("22222222-3333-4444-8555-666666666666", "Beta", 2)

    def test_here_typed_among_the_picks_is_a_route_not_a_row_name(self):
        out = self.picks("--picks", "1 here", "--dry-run")
        self.assertIn("route word 'here'", out.stdout)
        self.assertNotIn("matches no row name", out.stdout)

    def test_tab_typed_among_the_picks_is_a_route(self):
        out = self.picks("--picks", "1 tab", "--dry-run")
        self.assertIn("route word 'tab'", out.stdout)
        self.assertNotIn("matches no row name", out.stdout)

    def test_adopt_is_a_synonym_for_here(self):
        out = self.picks("--picks", "adopt 1", "--dry-run")
        self.assertIn("THIS TAB becomes the project", out.stdout)

    def test_window_states_the_default_route_out_loud(self):
        out = self.picks("--picks", "1 window", "--dry-run")
        self.assertIn("a new workspace (the default)", out.stdout)

    def test_the_route_word_is_case_insensitive(self):
        out = self.picks("--picks", "1 HERE", "--dry-run")
        self.assertIn("route word 'HERE'", out.stdout)

    def test_two_different_routes_at_once_are_refused(self):
        out = self.picks("--picks", "1 here tab", "--dry-run")
        self.assertIn("REFUSED", out.stdout)
        self.assertIn("different routes at once", out.stdout)

    def test_a_route_word_with_no_project_is_refused_by_name(self):
        out = self.picks("--picks", "here", "--dry-run")
        self.assertIn("named no project", out.stdout)

    def test_here_still_takes_exactly_one_pick(self):
        out = self.picks("--picks", "1 2 here", "--dry-run")
        self.assertIn("`here` takes exactly ONE pick", out.stdout)

    def test_tab_may_take_a_list(self):
        out = self.picks("--picks", "1, 2 tab", "--dry-run")
        self.assertNotIn("REFUSED", out.stdout)
        self.assertIn("resolved 2 picks", out.stdout)

    def test_tab_and_focus_existing_are_refused_together(self):
        out = self.picks("--picks", "1 tab", "--focus-existing", "--dry-run")
        self.assertIn("REFUSED", out.stdout)
        self.assertIn("opposite things", out.stdout)


# ---------------------------------------------------------------------------
# the default has to stay the default
# ---------------------------------------------------------------------------
class DefaultRouteTest(TabBase):
    def setUp(self):
        super().setUp()
        self.mkrow(U, "Alpha", 1)

    def test_a_bare_number_says_nothing_about_a_tab(self):
        out = self.picks("--picks", "1", "--dry-run")
        self.assertNotIn("route word", out.stdout)
        self.assertNotIn("--tab", out.stdout)

    def test_a_bare_number_takes_the_workspace_route(self):
        out = self.picks("--picks", "1", "--dry-run")
        self.assertIn("CREATE with --name", out.stdout)

    def test_launch_refuses_tab_together_with_focus_existing(self):
        out = self.launch("--project", U, "--tab", "--focus-existing", "--dry-run")
        self.assertEqual(out.returncode, 2)
        self.assertIn("opposite things", out.stderr)

    def test_the_tab_flag_is_named_in_the_sandbox_decision(self):
        out = self.launch("--project", U, "--tab", "--dry-run")
        self.assertIn("SANDBOX --tab", out.stdout)

    def test_without_the_flag_the_sandbox_says_nothing_about_tabs(self):
        out = self.launch("--project", U, "--dry-run")
        self.assertNotIn("SANDBOX --tab", out.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
