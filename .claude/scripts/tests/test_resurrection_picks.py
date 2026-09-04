#!/usr/bin/env python3
"""test_resurrection_picks.py — the typed-number routes (Zee's asks, 2026-08-24).

Covers the four changes that turned a number into a real handle:

  ask 1  the number verbs are reachable — the book itself names them
  ask 2  `/acos-resurrect 20` opens row 20 with no menu, and an ARCHIVED row
         is refused IN THE PRE-CHECK (brief item 4) instead of late
  ask 3  `here` routes the pick to adopt-project.sh, takes exactly one pick,
         and refuses alongside --focus-existing
  ask 4  close-targets.py ranks the likely park rows and resolves one number
         to the `parking to:` confirm line

Every test runs against a FIXTURE registry under a throwaway home, with
RESURRECTION_SKIP_CMUX=1 so nothing here reads or writes the real ~/.acos and
nothing touches live cmux. That second half matters: before the sandbox flag
was threaded into fresh_book(), a fixture row's TIER depended on whatever
workspaces happened to be open on the machine running the test.
"""

import importlib.util
import json
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

OPEN_PICKS = os.path.join(_RESDIR, "open-picks.sh")
CLOSE_TARGETS = os.path.join(_RESDIR, "close-targets.py")
VIEW = os.path.join(_RESDIR, "resurrect-view.py")


def _load(stem, filename):
    spec = importlib.util.spec_from_file_location(stem, os.path.join(_RESDIR, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


view = _load("resurrect_view", "resurrect-view.py")


class PickTestBase(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="pick-test-")
        os.makedirs(registry_lib.registry_dir(self.home), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def mkrow(self, uuid, name, ordinal, status="parked", root=None):
        root = root or os.path.join(self.home, "roots", name)
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
            "tombstoned_at": ("2026-02-02T00:00:00+00:00" if status == "tombstoned" else None),
            "pick_ordinal": ordinal,
        }
        registry_lib.atomic_write_json(registry_lib.row_path(uuid, self.home), row)
        # Record the number in the ledger too. A fixture that writes rows
        # straight to disk skips upsert_row, which is where a real row's `issue`
        # event is appended — and ordinal_lib.next_ordinal reads the LEDGER, not
        # the rows, by design (Zee's item 8: the ledger is the source of truth
        # for "ever issued"; conflict-scan's ORDINAL-CLASH is the detector for
        # the two disagreeing). Without this the fixture looks like a registry
        # whose ledger was lost, and next_ordinal answers 1 no matter what the
        # rows hold.
        if ordinal is not None:
            ordinal_lib.append_event("issue", ordinal, uuid, name, self.home)
        return row

    def env(self, **extra):
        e = dict(os.environ)
        e["ACOS_REGISTRY_HOME"] = self.home
        e["RESURRECTION_SKIP_CMUX"] = "1"
        e.pop("CMUX_WORKSPACE_ID", None)
        e.update(extra)
        return e

    def picks(self, *argv, cwd=None):
        return subprocess.run(["/bin/bash", OPEN_PICKS] + list(argv),
                              capture_output=True, text=True, timeout=180,
                              env=self.env(), cwd=cwd or self.home)

    def targets(self, *argv, cwd=None, **envextra):
        return subprocess.run([sys.executable, CLOSE_TARGETS] + list(argv),
                              capture_output=True, text=True, timeout=180,
                              env=self.env(**envextra), cwd=cwd or self.home)


# ------------------------------------------------- ask 2: the status pre-check

class PreCheckStatusTest(PickTestBase):
    """Brief item 4. Every row is numbered now, ARCHIVED ones included, so an
    archived row can be NAMED by number for the first time. It must be refused
    before anything opens, not late inside the sequential loop."""

    def test_tombstoned_number_is_refused_with_no_opt_in(self):
        self.mkrow("u-live", "Live", 1)
        self.mkrow("u-dead", "Dead", 2, status="tombstoned")
        out = self.picks("--picks", "2", "--dry-run")
        self.assertEqual(out.returncode, 2, out.stdout)
        self.assertIn("TOMBSTONED", out.stdout)
        self.assertIn("NOTHING was opened", out.stdout)
        # and no opt-in exists for it
        out2 = self.picks("--picks", "2", "--include-archived", "--dry-run")
        self.assertEqual(out2.returncode, 2, out2.stdout)
        self.assertIn("TOMBSTONED", out2.stdout)

    def test_completed_number_is_refused_by_default_and_names_the_opt_in(self):
        self.mkrow("u-done", "Done", 3, status="completed")
        out = self.picks("--picks", "3", "--dry-run")
        self.assertEqual(out.returncode, 2, out.stdout)
        self.assertIn("COMPLETED", out.stdout)
        self.assertIn("--include-archived", out.stdout)

    def test_completed_number_opens_with_the_explicit_opt_in(self):
        """The resurrect LOOP survives: a finished project reopens on purpose."""
        self.mkrow("u-done", "Done", 3, status="completed")
        out = self.picks("--picks", "3", "--include-archived", "--dry-run")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("all-or-nothing check passed", out.stdout)

    def test_one_bad_row_in_a_list_opens_nothing(self):
        """All-or-nothing holds for a STATUS refusal, not just an unknown number."""
        self.mkrow("u-live", "Live", 1)
        self.mkrow("u-dead", "Dead", 2, status="tombstoned")
        out = self.picks("--picks", "1, 2", "--dry-run")
        self.assertEqual(out.returncode, 2, out.stdout)
        self.assertIn("NOTHING was opened", out.stdout)
        self.assertNotIn("all-or-nothing check passed", out.stdout)

    def test_a_live_number_still_resolves(self):
        self.mkrow("u-live", "Live", 7)
        out = self.picks("--picks", "7", "--dry-run")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("all-or-nothing check passed", out.stdout)


# -------------------------------------------------------- ask 3: the `here` route

class HereRouteTest(PickTestBase):
    def test_here_refuses_a_list(self):
        """A tab hosts ONE project. Taking the first pick silently would strand
        the rest, so the refusal is the contract."""
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        out = self.picks("--picks", "1, 2", "--here", "--dry-run")
        self.assertEqual(out.returncode, 2, out.stdout)
        # The wording lost its dashes on 2026-08-25: the same refusal now covers
        # the --here FLAG and the bare word `here` typed among the picks.
        self.assertIn("`here` takes exactly ONE pick", out.stdout)

    def test_here_refuses_alongside_focus_existing(self):
        self.mkrow("u-a", "Alpha", 1)
        out = self.picks("--picks", "1", "--here", "--focus-existing", "--dry-run")
        self.assertEqual(out.returncode, 2, out.stdout)
        self.assertIn("opposite things", out.stdout)

    def test_here_routes_to_adopt_not_launch(self):
        """The observable difference: the banner says ADOPT HERE, and the
        sandbox decision printed is adopt's, not launch's workspace-create."""
        self.mkrow("u-a", "Alpha", 1)
        out = self.picks("--picks", "1", "--here", "--dry-run")
        self.assertIn("ADOPT HERE", out.stdout)
        self.assertNotIn("CREATE workspace", out.stdout)

    def test_without_here_the_pick_still_launches_a_window(self):
        self.mkrow("u-a", "Alpha", 1)
        out = self.picks("--picks", "1", "--dry-run")
        self.assertIn("OPEN 1/1", out.stdout)
        self.assertNotIn("ADOPT HERE", out.stdout)


# ------------------------------------------ 2026-09-03: the account word


class AccountWordTest(PickTestBase):
    """`5 jason` / `5 personal` choose the Claude account the NEW window signs
    in as. The word is read out of the picks (like a route word), echoed back
    as typed, and refused alongside `here` (that tab's Claude already runs)."""

    def test_account_word_is_read_and_echoed(self):
        self.mkrow("u-a", "Alpha", 1)
        out = self.picks("--picks", "1 jason", "--dry-run")
        self.assertIn("account word 'jason' read from the picks", out.stdout)
        self.assertIn("CLAUDE_ACCOUNT=jason", out.stdout)
        self.assertIn("OPEN 1/1", out.stdout)  # the word did not become a row name

    def test_account_word_is_case_insensitive_and_passes_to_launch(self):
        self.mkrow("u-a", "Alpha", 1)
        out = self.picks("--picks", "1 Personal", "--dry-run")
        self.assertIn("account word 'Personal' read from the picks", out.stdout)
        self.assertIn("signs in as personal", out.stdout)

    def test_two_account_words_refuse(self):
        self.mkrow("u-a", "Alpha", 1)
        out = self.picks("--picks", "1 jason personal", "--dry-run")
        self.assertEqual(out.returncode, 2, out.stdout)
        self.assertIn("different accounts", out.stdout)

    def test_account_word_alongside_here_refuses(self):
        self.mkrow("u-a", "Alpha", 1)
        out = self.picks("--picks", "1 here jason", "--dry-run")
        self.assertEqual(out.returncode, 2, out.stdout)
        self.assertIn("no account can be chosen", out.stdout)

    def test_account_flag_rejects_unknown_value(self):
        self.mkrow("u-a", "Alpha", 1)
        out = self.picks("--picks", "1", "--account", "bogus", "--dry-run")
        self.assertEqual(out.returncode, 2, out.stdout)
        self.assertIn("jason or personal", out.stdout)


# ----------------------------------------------- ask 4: close destination menu

class CloseTargetsResolveTest(PickTestBase):
    def test_resolve_prints_the_confirm_line_with_name_and_folder(self):
        row = self.mkrow("u-a", "Alpha", 11)
        out = self.targets("--resolve", "11")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("parking to: Alpha @ %s" % row["root"], out.stdout)
        self.assertIn("uuid u-a", out.stdout)

    def test_resolve_json_carries_the_uuid_the_skill_needs(self):
        self.mkrow("u-a", "Alpha", 11)
        out = self.targets("--resolve", "11", "--json")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertEqual(json.loads(out.stdout)["project_uuid"], "u-a")

    def test_resolve_refuses_a_tombstoned_row(self):
        self.mkrow("u-d", "Dead", 12, status="tombstoned")
        out = self.targets("--resolve", "12")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("TOMBSTONED", out.stdout)

    def test_resolve_refuses_a_completed_row(self):
        self.mkrow("u-c", "Done", 13, status="completed")
        out = self.targets("--resolve", "13")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("COMPLETED", out.stdout)

    def test_resolve_refuses_an_unknown_number_and_names_the_range(self):
        self.mkrow("u-a", "Alpha", 4)
        out = self.targets("--resolve", "999")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("not a number in this book", out.stdout)

    def test_resolve_refuses_a_non_number(self):
        self.mkrow("u-a", "Alpha", 4)
        out = self.targets("--resolve", "Alpha")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("takes a book NUMBER", out.stdout)


class CloseTargetsMenuTest(PickTestBase):
    def test_same_folder_rows_rank_as_strong_candidates(self):
        shared = os.path.join(self.home, "shared")
        self.mkrow("u-a", "Alpha", 1, root=shared)
        self.mkrow("u-b", "Bravo", 2, root=shared)
        self.mkrow("u-far", "Far", 3)
        out = self.targets(cwd=shared)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("same folder as this tab", out.stdout)
        data = json.loads(self.targets("--json", cwd=shared).stdout)
        strong = [r["name"] for r in data["likely"] if "same folder" in r["why"]]
        self.assertEqual(sorted(strong), ["Alpha", "Bravo"])

    def test_archived_rows_are_never_offered_as_park_targets(self):
        shared = os.path.join(self.home, "shared")
        self.mkrow("u-a", "Alpha", 1, root=shared)
        self.mkrow("u-d", "Dead", 2, status="tombstoned", root=shared)
        self.mkrow("u-c", "Done", 3, status="completed", root=shared)
        data = json.loads(self.targets("--json", cwd=shared).stdout)
        names = [r["name"] for r in data["likely"]]
        self.assertIn("Alpha", names)
        self.assertNotIn("Dead", names)
        self.assertNotIn("Done", names)

    def test_menu_carries_all_three_of_zees_choices(self):
        self.mkrow("u-a", "Alpha", 1)
        out = self.targets()
        self.assertIn("1. A LIKELY ROW", out.stdout)
        self.assertIn("`new <name>`", out.stdout)
        self.assertIn("CREATE A NEW ROW", out.stdout)
        self.assertIn("`all`", out.stdout)

    def test_choice_two_names_the_number_a_new_row_would_take(self):
        """Zee's words: "create a new row in an empty number". The menu says
        WHICH number. Since his follow-up ruling — "A freed number can be
        assigned, change that rule" — that is the LOWEST free number, so gaps
        close instead of growing."""
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        out = self.targets()
        self.assertIn("which takes number 3", out.stdout)
        self.assertIn("lowest free number", out.stdout)
        data = json.loads(self.targets("--json").stdout)
        self.assertEqual(data["next_number"], 3)

    def test_a_gap_in_the_middle_is_the_number_offered(self):
        """The whole point of the reversal: a hole gets filled, not skipped."""
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-c", "Charlie", 3)
        self.mkrow("u-d", "Delta", 4)
        out = self.targets()
        self.assertIn("which takes number 2", out.stdout)
        data = json.loads(self.targets("--json").stdout)
        self.assertEqual(data["next_number"], 2)

    def test_choice_two_promises_nothing_is_replaced(self):
        self.mkrow("u-a", "Alpha", 1)
        out = self.targets()
        self.assertIn("Nothing is replaced", out.stdout)

    def test_the_cap_is_printed_whenever_it_bites(self):
        """A silent truncation would read as 'these are all the candidates'."""
        shared = os.path.join(self.home, "shared")
        for i in range(1, 6):
            self.mkrow("u-%d" % i, "Row%d" % i, i, root=shared)
        out = self.targets(cwd=shared)
        self.assertIn("not listed — capped at 3", out.stdout)
        data = json.loads(self.targets("--json", cwd=shared).stdout)
        self.assertEqual(len(data["likely"]), 3)
        self.assertEqual(data["dropped"], data["strong_count"] - 3)

    def test_filler_is_labelled_as_weak_not_as_evidence(self):
        """A row with no link to this tab may fill the menu, but it must not
        claim to be evidence about this tab."""
        self.mkrow("u-far", "Far", 1)
        elsewhere = os.path.join(self.home, "elsewhere")
        os.makedirs(elsewhere, exist_ok=True)
        data = json.loads(self.targets("--json", cwd=elsewhere).stdout)
        self.assertTrue(data["likely"])
        self.assertIn("weak", data["likely"][0]["why"])
        self.assertEqual(data["strong_count"], 0)
        self.assertEqual(data["dropped"], 0)

    def test_no_cmux_key_tag_is_reported_not_swallowed(self):
        self.mkrow("u-a", "Alpha", 1)
        data = json.loads(self.targets("--json").stdout)
        self.assertIsNone(data["key_uuid"])
        self.assertTrue(data["key_note"])


# ------------------------------------------------ ask 1: the verbs are findable

class NumberVerbDiscoverabilityTest(PickTestBase):
    def test_the_book_footer_names_the_number_verbs(self):
        """Ask 1 was a DISCOVERY gap, not a capability gap: manage-ordinals.py
        already had the verbs and no render or skill named the file."""
        self.mkrow("u-a", "Alpha", 1)
        book = view.build_book(self.home, True, True)
        text = view.render_human(book, False)
        self.assertIn("`numbers`", text)
        self.assertIn("`number <n> to <m>`", text)
        self.assertIn("`swap <a> <b>`", text)

    def test_the_footer_does_not_disturb_the_gutter_invariant(self):
        """resurrect-view.py's standing invariant: the gutter integer and
        book.json's pick_number are the same value for every row."""
        self.mkrow("u-a", "Alpha", 41)
        self.mkrow("u-b", "Bravo", 42)
        book = view.build_book(self.home, True, True)
        text = view.render_human(book, False)
        for p in book["projects"]:
            if p.get("pick_number"):
                self.assertRegex(text, r"(?m)^\s*%d\.\s" % p["pick_number"])


class TierOrderTest(PickTestBase):
    """Inside a tier, rows run in PICK-NUMBER order (Zee, 2026-08-25).

    The page was already sorted by time, newest activity first. What he was
    missing was his own numbering: he had just assigned every number by hand,
    and they jumped around the page, which made a book he had ordered look
    unordered. Time is not lost — the TIER is the age signal (COLD is more than
    30 days), and every line still prints its own age."""

    def numbers_in(self, text, tier):
        """The gutter integers listed under one tier heading, in page order."""
        import re
        lines = text.splitlines()
        out, inside = [], False
        for line in lines:
            if re.match(r"^[A-Z][A-Z ]+\(\d+\)\s*$", line.strip()):
                inside = line.strip().startswith(tier + " (")
                continue
            if not inside:
                continue
            m = re.match(r"^\s*(\d+)\.\s", line)
            if m:
                out.append(int(m.group(1)))
        return out

    def test_a_tier_is_listed_in_number_order(self):
        for uuid, name, n in (("u-c", "Charlie", 21), ("u-a", "Alpha", 3),
                              ("u-b", "Bravo", 9), ("u-d", "Delta", 15)):
            self.mkrow(uuid, name, n)
        book = view.build_book(self.home, True, True)
        text = view.render_human(book, False)
        listed = [p["pick_number"] for p in book["projects"]]
        self.assertEqual(listed, sorted(listed),
                         "book.json order must match the page, not just the render")
        self.assertEqual(self.numbers_in(text, "NO HANDOFF"), [3, 9, 15, 21])

    def test_a_higher_number_sits_below_a_lower_one_even_when_touched_later(self):
        """The case that made the old order look wrong: R2P was number 13 and
        the most recently touched, so it sat above numbers 1 and 2."""
        self.mkrow("u-low", "Low number", 1)
        self.mkrow("u-high", "High number", 13)
        row = registry_lib.load_row("u-high", self.home)
        row["last_verified_at"] = "2026-12-31T00:00:00+00:00"   # touched much later
        registry_lib.atomic_write_json(
            registry_lib.row_path("u-high", self.home), row)
        book = view.build_book(self.home, True, True)
        order = [p["pick_number"] for p in book["projects"]]
        self.assertLess(order.index(1), order.index(13))

    def test_the_header_no_longer_claims_numbers_are_out_of_order(self):
        """The header used to read "they do not run in order down the page".
        That became false the moment the sort changed, and a render that
        contradicts itself is worse than either order alone."""
        self.mkrow("u-a", "Alpha", 1)
        text = view.render_human(view.build_book(self.home, True, True), False)
        self.assertNotIn("do not run in order", text)
        self.assertIn("NUMBER order", text)
        self.assertIn("gaps are normal", text, "gaps are still expected after a delete")


if __name__ == "__main__":
    unittest.main(verbosity=1)
