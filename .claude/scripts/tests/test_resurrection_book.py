#!/usr/bin/env python3
"""test_resurrection_book.py — stdlib unittest for the multi-window book view
(MW-B, user brief 2026-08-04).

D10 one row per project, carrying a live-window COUNT. Splitting a project
    into several rows was explicitly rejected — it defeats the point of one
    accumulating project.
D12 window names derive from the project name, Zee's wording "OKOA works
    *label*", so the project name is always the stem and the row identity is
    never in doubt.
"""

import importlib.util
import os
import sys
import unittest

_THIS = os.path.dirname(os.path.abspath(__file__))
_RESDIR = os.path.abspath(os.path.join(_THIS, os.pardir, "resurrection"))


def _load_view():
    """resurrect-view.py has a hyphen in its name, so it is not importable by
    the normal statement — load it by path."""
    spec = importlib.util.spec_from_file_location(
        "resurrect_view", os.path.join(_RESDIR, "resurrect-view.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class WindowLabelTest(unittest.TestCase):
    """D12: the label is what is left after the project-name stem."""

    @classmethod
    def setUpClass(cls):
        cls.view = _load_view()

    def label(self, title, project):
        return self.view.window_label(title, project)

    def test_the_stem_is_stripped_to_leave_the_label(self):
        self.assertEqual(self.label("OKOA Works Golden East", "OKOA Works"), "Golden East")
        self.assertEqual(self.label("OKOA Works Flyer", "OKOA Works"), "Flyer")

    def test_the_plain_window_has_no_label(self):
        self.assertIsNone(self.label("OKOA Works", "OKOA Works"))
        self.assertIsNone(self.label("okoa works", "OKOA Works"), "match is case-insensitive")

    def test_separators_between_stem_and_label_are_trimmed(self):
        for sep in (" - ", " — ", ": ", " · "):
            self.assertEqual(self.label("OKOA Works%sFlyer" % sep, "OKOA Works"), "Flyer")

    def test_an_unrelated_name_is_shown_whole_never_guessed_at(self):
        """Inventing a label out of a name that does not carry the stem would
        be inventing a fact about which project a window belongs to."""
        self.assertEqual(self.label("Something Else", "OKOA Works"), "Something Else")

    def test_a_window_with_no_human_set_name_has_no_label(self):
        self.assertIsNone(self.label(None, "OKOA Works"))
        self.assertIsNone(self.label("", "OKOA Works"))


class RowDisplayTest(unittest.TestCase):
    """D10: the count rides on the project's single row."""

    @classmethod
    def setUpClass(cls):
        cls.view = _load_view()

    def _render(self, project, tier="OPEN NOW"):
        """render_human on a minimal one-row book. Returns the rendered text."""
        counts = {t: 0 for t in self.view.TIER_ORDER}
        counts[tier] = 1
        book = {
            "generated_at": "2026-08-05T00:00:00+00:00",
            "registry_dir": "/tmp/reg", "fresh": "fresh",
            "liveness": {"procs_skipped": False, "cmux_skipped": False,
                         "live_session_total": 0, "cmux_workspace_total": 0,
                         "proc_error": None, "cmux_error": None},
            "projects": [dict(project, tier=tier)],
            "unreadable_rows": [], "unmatched_workspaces": [],
            "tier_counts": counts, "broken_count": 0,
            "listed": 1, "total": 1,
        }
        return self.view.render_human(book, use_color=False)

    def test_render_shows_the_open_count_on_one_row(self):
        out = self._render({
            "name": "OKOA Works", "pick_number": 1,
            "next_action": "do the thing", "age_days": 0.0,
            "broken": None, "name_drift": None,
            "live": {"workspace_count": 2, "window_labels": ["Golden East", "Flyer"]},
        })
        self.assertIn("OKOA Works (2 open)", out)
        self.assertIn("windows: Golden East · Flyer", out)
        self.assertEqual(out.count("OKOA Works"), 1,
                         "D10: one row per project, never one row per window")

    def test_a_single_labelled_window_reads_in_the_singular(self):
        out = self._render({
            "name": "OKOA Works", "pick_number": 1,
            "next_action": None, "age_days": 0.0,
            "broken": None, "name_drift": None,
            "live": {"workspace_count": 1, "window_labels": ["Flyer"]},
        })
        self.assertIn("OKOA Works (1 open)", out)
        self.assertIn("window: Flyer", out)
        self.assertNotIn("windows:", out)

    def test_a_project_with_no_live_window_shows_no_count(self):
        out = self._render({
            "name": "Quiet Project", "pick_number": 1,
            "next_action": None, "age_days": 3.0,
            "broken": None, "name_drift": None,
            "live": {"workspace_count": 0, "window_labels": []},
        }, tier="RECENT")
        # Scoped to the ROWS, not the whole page: since 2026-09-04 the render
        # ends with a fixed WHAT YOU CAN DO verb sheet that names `window` as a
        # route word. That legend is the same on every render and says nothing
        # about any row, so a whole-page assertNotIn was never testing what this
        # test is about — a quiet project's own row carrying no live-window count.
        rows = out.split("\nlisted ")[0]
        self.assertIn("Quiet Project", rows)
        self.assertNotIn("open)", rows)
        self.assertNotIn("window", rows)

    def test_a_folder_level_row_is_marked_as_a_placeholder(self):
        """A row with no sidebar name displays its folder basename — a
        PLACEHOLDER, not a project name (several projects can live in one
        folder; user rule, restated 2026-08-05). The book must say so on the
        row, so a folder name can never masquerade as a real project."""
        out = self._render({
            "name": "chart-maker", "pick_number": 1,
            "next_action": None, "age_days": 18.0,
            "broken": None, "name_drift": None, "folder_level": True,
            "live": {"workspace_count": 0, "window_labels": []},
        }, tier="NO HANDOFF")
        self.assertIn("chart-maker  [folder]", out)
        self.assertIn("[folder] = 1 row enrolled from a folder", out)

    def test_a_named_project_row_carries_no_folder_tag(self):
        out = self._render({
            "name": "OKOA Works", "pick_number": 1,
            "next_action": None, "age_days": 1.0,
            "broken": None, "name_drift": None, "folder_level": False,
            "live": {"workspace_count": 0, "window_labels": []},
        })
        self.assertNotIn("[folder]", out)

    def test_the_folder_tag_survives_a_truncated_long_name(self):
        """The name column truncates with an ellipsis. The tag is appended
        AFTER truncation — a marker that sometimes vanishes is a marker that
        lies."""
        out = self._render({
            "name": "SLOPE-Structured_Life_Organization_and_Planning_Engine",
            "pick_number": 1, "next_action": None, "age_days": 18.0,
            "broken": None, "name_drift": None, "folder_level": True,
            "live": {"workspace_count": 0, "window_labels": []},
        }, tier="NO HANDOFF")
        self.assertIn("[folder]", out)

    def test_broken_and_name_drift_notes_still_show_alongside_windows(self):
        """Hard rule: facts are never hidden. Adding the window sub-line must
        not have displaced the existing warning sub-lines."""
        out = self._render({
            "name": "Trouble", "pick_number": 1,
            "next_action": None, "age_days": 1.0,
            "broken": "root directory missing: /gone",
            "name_drift": ["saved name no longer matches"],
            "live": {"workspace_count": 2, "window_labels": ["A", "B"]},
        })
        self.assertIn("windows: A · B", out)
        self.assertIn("NAME DRIFT:", out)
        self.assertIn("BROKEN:", out)


class VerbSheetTest(unittest.TestCase):
    """Zee's ask, 2026-09-04: a render must say what can be DONE with it, not
    only which projects exist. The sheet lives in the renderer precisely so it
    cannot be trimmed, forgotten or paraphrased by a caller — so its presence
    is a rendering fact, and tested like one."""

    @classmethod
    def setUpClass(cls):
        cls.view = _load_view()

    def _empty_render(self):
        counts = {t: 0 for t in self.view.TIER_ORDER}
        book = {
            "generated_at": "2026-09-04T00:00:00+00:00",
            "registry_dir": "/tmp/reg", "fresh": "fresh",
            "liveness": {"procs_skipped": False, "cmux_skipped": False,
                         "live_session_total": 0, "cmux_workspace_total": 0,
                         "proc_error": None, "cmux_error": None},
            "projects": [], "unreadable_rows": [], "unmatched_workspaces": [],
            "tier_counts": counts, "broken_count": 0, "listed": 0, "total": 0,
        }
        return self.view.render_human(book, use_color=False)

    def test_the_short_sheet_rides_on_every_render(self):
        out = self._empty_render()
        self.assertIn("WHAT YOU CAN DO", out)
        for verb in ("13 here", "13 tab", "13 jason", "13 personal", "`help`"):
            self.assertIn(verb, out, "the short sheet dropped %r" % verb)

    def test_the_short_sheet_survives_an_empty_book(self):
        """No rows is exactly when a user most needs to know what to type."""
        self.assertIn("WHAT YOU CAN DO", self._empty_render())

    def test_the_full_sheet_names_every_verb_the_skill_routes(self):
        full = self.view.VERBS_FULL
        for verb in ("adopt", "finish", "tombstone", "curate", "numbers",
                     "swap", "compact", "numbers sheet", "delete", "restore",
                     "purge", "strike", "merge", "conflicts", "dry run",
                     "label"):
            self.assertIn(verb, full, "the full sheet never names %r" % verb)

    def test_the_short_sheet_points_at_the_full_one(self):
        """The short sheet is only safe to keep short while `help` reaches the
        rest. If that pointer is ever dropped, the trimmed verbs go dark."""
        self.assertIn("help", self.view.VERBS_SHORT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
