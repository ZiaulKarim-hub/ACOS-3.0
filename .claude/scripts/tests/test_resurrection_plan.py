#!/usr/bin/env python3
"""test_resurrection_plan.py — the bulk renumber sheet (Zee's ask, 2026-08-24).

`manage-ordinals.py renumber` moves ONE row and cannot express a reshuffle at
all: to swap 5 and 7 you must move one onto a number the other still holds, and
that REFUSES. Zee's answer is a spreadsheet — every row, its number, and an
empty column he fills in — read back and applied in one planned pass.

The cases that matter, in the order they would bite:

  * a swap works, which is the whole reason this exists
  * a blank cell means LEAVE IT ALONE, not "clear the number"
  * the sheet is refused if the book moved under it (the stale-plan guard)
  * two rows given one number is refused, naming both
  * a number given to a mover while a NON-mover still holds it is refused
  * 0 is refused; it is reserved for "new project"
  * a whole-number check: Excel hands back 3, 3.0 and "3" for one typed cell
  * the in-progress breadcrumb exists only while writes are in flight

Every test runs against a FIXTURE registry under a throwaway home. Nothing here
reads or writes the real ~/.acos, and RESURRECTION_SKIP_CMUX keeps the book
render away from live cmux.
"""

import csv
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

_THIS = os.path.dirname(os.path.abspath(__file__))
_RESDIR = os.path.abspath(os.path.join(_THIS, os.pardir, "resurrection"))
sys.path.insert(0, _RESDIR)
import ordinal_lib  # noqa: E402
import registry_lib  # noqa: E402


def _load(stem, filename):
    spec = importlib.util.spec_from_file_location(stem, os.path.join(_RESDIR, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


plan = _load("plan_ordinals", "plan-ordinals.py")


class PlanTestBase(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="plan-test-")
        os.makedirs(registry_lib.registry_dir(self.home), exist_ok=True)
        self._prev_home = plan.REG_HOME
        plan.REG_HOME = self.home
        os.environ["ACOS_REGISTRY_HOME"] = self.home
        os.environ["RESURRECTION_SKIP_CMUX"] = "1"

    def tearDown(self):
        plan.REG_HOME = self._prev_home
        os.environ.pop("ACOS_REGISTRY_HOME", None)
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
        ordinal_lib.append_event("issue", ordinal, uuid, name, self.home)
        return row

    def records(self, *pairs):
        """(uuid, current, new) triples -> the dicts read_sheet would produce."""
        out = []
        for uuid, cur, new in pairs:
            row = registry_lib.load_row(uuid, self.home)
            out.append({"name": row["name"], "current_number": cur, "new_number": new,
                        "status": row["status"], "tier": "RECENT", "root": row["root"],
                        "project_uuid": uuid})
        return out

    def ordinal_of(self, uuid):
        return registry_lib.load_row(uuid, self.home)["pick_ordinal"]

    def mkbundle(self, uuid, slug, owned=True):
        """A close bundle under the row's own root, stamped by default."""
        import bundles_lib
        row = registry_lib.load_row(uuid, self.home)
        d = os.path.join(row["root"], "memory", "handoffs", "closed", slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "handoff.yaml"), "w") as fh:
            fh.write("timestamp: x\nstatus: active\nnext_action: y\n")
        if owned:
            with open(os.path.join(d, bundles_lib.OWNER_MARKER), "w") as fh:
                fh.write(uuid + "\n")
        return d

    def apply_sheet(self, records):
        """The whole cmd_apply path in-process: checks, deletes, then moves."""
        moves, deletes, unchanged, _, _m = plan.build_plan(records, self.home)
        plan.check_deletable(deletes, self.home)
        done, failed = plan.apply_deletes(deletes, self.home)
        problems = plan.apply_plan(moves, self.home) if moves else []
        return moves, deletes, done, failed, problems

    def run_plan(self, records):
        moves, deletes, unchanged, _, _m = plan.build_plan(records, self.home)
        problems = plan.apply_plan(moves, self.home)
        return moves, unchanged, problems


# ------------------------------------------------------------- the happy path

class BulkMoveTest(PlanTestBase):
    def test_a_swap_works(self):
        """The reason this tool exists. A sequence of single renumbers cannot
        do this: whichever row moves first lands on a number the other holds."""
        self.mkrow("u-a", "Alpha", 5)
        self.mkrow("u-b", "Bravo", 7)
        _, _, problems = self.run_plan(self.records(("u-a", 5, 7), ("u-b", 7, 5)))
        self.assertEqual(problems, [])
        self.assertEqual(self.ordinal_of("u-a"), 7)
        self.assertEqual(self.ordinal_of("u-b"), 5)

    def test_a_three_way_rotation_works(self):
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        self.mkrow("u-c", "Charlie", 3)
        _, _, problems = self.run_plan(
            self.records(("u-a", 1, 2), ("u-b", 2, 3), ("u-c", 3, 1)))
        self.assertEqual(problems, [])
        self.assertEqual(
            [self.ordinal_of(u) for u in ("u-a", "u-b", "u-c")], [2, 3, 1])

    def test_a_blank_cell_leaves_the_row_alone(self):
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        moves, unchanged, problems = self.run_plan(
            self.records(("u-a", 1, 9), ("u-b", 2, "")))
        self.assertEqual(problems, [])
        self.assertEqual(len(moves), 1)
        self.assertEqual(len(unchanged), 1)
        self.assertEqual(self.ordinal_of("u-b"), 2, "a blank must never clear a number")

    def test_a_cell_equal_to_the_current_number_is_not_a_move(self):
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        moves, unchanged, _ = self.run_plan(self.records(("u-a", 1, 9), ("u-b", 2, 2)))
        self.assertEqual([m["name"] for m in moves], ["Alpha"])
        self.assertEqual(len(unchanged), 1)

    def test_one_ledger_entry_per_row_naming_the_real_from_and_to(self):
        """The parking numbers are machinery. Logging them would make
        history_for() answer with numbers no project ever really had."""
        self.mkrow("u-a", "Alpha", 5)
        self.mkrow("u-b", "Bravo", 7)
        before = len(ordinal_lib.read_events(self.home))
        self.run_plan(self.records(("u-a", 5, 7), ("u-b", 7, 5)))
        events = ordinal_lib.read_events(self.home)[before:]
        self.assertEqual(len(events), 2)
        self.assertTrue(all(e["verb"] == "renumber" for e in events))
        self.assertEqual({(e["from_ordinal"], e["ordinal"]) for e in events},
                         {(5, 7), (7, 5)})

    def test_no_intermediate_state_puts_two_rows_on_one_number(self):
        self.mkrow("u-a", "Alpha", 5)
        self.mkrow("u-b", "Bravo", 7)
        self.run_plan(self.records(("u-a", 5, 7), ("u-b", 7, 5)))
        holders = ordinal_lib.live_holders(self.home)
        self.assertTrue(all(len(v) == 1 for v in holders.values()))

    def test_the_in_progress_breadcrumb_is_gone_afterwards(self):
        """It exists so a crash mid-rearrangement is diagnosable. A leftover
        one on a SUCCESSFUL run would be a false alarm forever."""
        self.mkrow("u-a", "Alpha", 5)
        self.mkrow("u-b", "Bravo", 7)
        self.run_plan(self.records(("u-a", 5, 7), ("u-b", 7, 5)))
        self.assertFalse(os.path.exists(plan.in_progress_path(self.home)))


# ------------------------------------------------- ask: 0 means DELETE the row

class ZeroDeletesTest(PlanTestBase):
    """Zee, 2026-08-25: "if I put zero for a row, that row project should be
    deleted." 0 is the one value that cannot mean a position — no row can hold
    it — so it is free to carry this meaning in this column."""

    def test_zero_deletes_the_row(self):
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        _m, deletes, done, failed, _p = self.apply_sheet(
            self.records(("u-a", 1, 0), ("u-b", 2, "")))
        self.assertEqual(len(deletes), 1)
        self.assertEqual(failed, [])
        self.assertIsNone(registry_lib.load_row("u-a", self.home))
        self.assertIsNotNone(registry_lib.load_row("u-b", self.home))

    def test_the_deleted_rows_number_is_freed(self):
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        self.apply_sheet(self.records(("u-a", 1, 0), ("u-b", 2, "")))
        self.assertNotIn(1, ordinal_lib.held_ordinals(self.home))
        self.assertEqual(ordinal_lib.next_ordinal(self.home), 1)

    def test_another_row_may_move_into_a_number_freed_in_the_same_sheet(self):
        """The reason deletes run FIRST. Mark row 5 with 0 and send row 9 to 5;
        doing the move first would collide with a row that still held 5."""
        self.mkrow("u-a", "Alpha", 5)
        self.mkrow("u-b", "Bravo", 9)
        _m, _d, _done, failed, problems = self.apply_sheet(
            self.records(("u-a", 5, 0), ("u-b", 9, 5)))
        self.assertEqual(failed, [])
        self.assertEqual(problems, [])
        self.assertIsNone(registry_lib.load_row("u-a", self.home))
        self.assertEqual(registry_lib.load_row("u-b", self.home)["pick_ordinal"], 5)

    def test_a_delete_archives_the_rows_close_bundles(self):
        self.mkrow("u-a", "Alpha", 1)
        b = self.mkbundle("u-a", "2026-08-01-Alpha-close")
        self.apply_sheet(self.records(("u-a", 1, 0)))
        self.assertFalse(os.path.isdir(b))
        row_root = os.path.join(self.home, "roots", "Alpha")
        arch = os.path.join(row_root, "memory", "handoffs", "archive", "closed",
                            "2026-08-01-Alpha-close")
        self.assertTrue(os.path.isdir(arch))
        self.assertIn("status: completed", open(os.path.join(arch, "handoff.yaml")).read())

    def test_a_delete_keeps_the_knowledge_facts(self):
        import knowledge_lib
        self.mkrow("u-a", "Alpha", 1)
        knowledge_lib.append_fact(
            "u-a", {"kind": "machine", "subject": "traps", "claim": "survives the sheet",
                    "evidence": {"type": "command", "value": "echo x"}}, home=self.home)
        self.apply_sheet(self.records(("u-a", 1, 0)))
        self.assertEqual(len(knowledge_lib.load_facts("u-a", self.home)), 1)

    def test_an_unproven_bundle_refuses_the_whole_sheet(self):
        """Per row, manage-ordinals reports a guess and moves on. In a BULK run
        nobody reads per-row notes, so it is promoted to a refusal."""
        self.mkrow("u-a", "Alpha", 1)
        self.mkbundle("u-a", "2026-08-01-Alpha-close", owned=False)
        _m, deletes, _u, _f, _mg = plan.build_plan(self.records(("u-a", 1, 0)), self.home)
        with self.assertRaises(plan.Refused) as ctx:
            plan.check_deletable(deletes, self.home)
        msg = str(ctx.exception)
        self.assertIn("GUESS", msg)
        self.assertIn("stamp-bundle-owners.py", msg)
        self.assertIsNotNone(registry_lib.load_row("u-a", self.home), "nothing written")

    def test_a_sheet_of_only_deletes_is_not_refused_as_nothing_to_do(self):
        self.mkrow("u-a", "Alpha", 1)
        moves, deletes, _u, _f, _mg = plan.build_plan(self.records(("u-a", 1, 0)), self.home)
        self.assertEqual(moves, [])
        self.assertEqual(len(deletes), 1)

    def test_zero_still_counts_as_a_change_for_the_nothing_to_do_check(self):
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        with self.assertRaises(plan.Refused) as ctx:
            plan.build_plan(self.records(("u-a", 1, ""), ("u-b", 2, "")), self.home)
        self.assertIn("marked 0 for deletion", str(ctx.exception))

    def test_the_plan_render_names_every_deletion(self):
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        moves, deletes, unchanged, _f, _mg = plan.build_plan(
            self.records(("u-a", 1, 0), ("u-b", 2, 9)), self.home)
        text = plan.render_plan(moves, deletes, unchanged)
        self.assertIn("1 DELETED", text)
        self.assertIn("DEL", text)
        self.assertIn("Alpha", text)

    def test_zero_survives_a_csv_round_trip(self):
        """Excel writes 0 in that cell; the reader must not see it as blank."""
        self.mkrow("u-a", "Alpha", 1)
        path = os.path.join(self.home, "sheet.csv")
        plan.write_csv(path, [
            {"name": "Alpha", "current_number": 1, "new_number": 0,
             "status": "parked", "tier": "RECENT", "root": "/x", "project_uuid": "u-a"}])
        _m, deletes, _u, _f, _mg = plan.build_plan(plan.read_sheet(path), self.home)
        self.assertEqual(len(deletes), 1)


# ------------------------------------------------------------- the refusals

class PlanRefusalTest(PlanTestBase):
    def assertRefuses(self, records, needle):
        with self.assertRaises(plan.Refused) as ctx:
            plan.build_plan(records, self.home)
        self.assertIn(needle, str(ctx.exception))

    def test_a_stale_sheet_is_refused(self):
        """The guard that makes exporting current_number worth doing. If the
        book moved after the export, the plan describes a book that is gone."""
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        recs = self.records(("u-a", 1, 9), ("u-b", 2, ""))
        registry_lib.set_pick_ordinal("u-a", 4, self.home)  # something moved meanwhile
        self.assertRefuses(recs, "The book changed")
        self.assertEqual(self.ordinal_of("u-a"), 4, "nothing was written")

    def test_two_rows_given_one_number_is_a_merge_not_a_refusal(self):
        """CHANGED 2026-08-25 on Zee's ruling. He gave one number to two or more
        rows in eight places, meaning "these are one project, join them". It was
        a refusal before; it is now a merge group."""
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        self.mkbundle("u-a", "2026-01-01-Alpha-close")   # breaks the tie
        _m, _d, _u, _f, merges = plan.build_plan(
            self.records(("u-a", 1, 8), ("u-b", 2, 8)), self.home)
        self.assertEqual(len(merges), 1)
        self.assertEqual(merges[0]["to"], 8)
        names = {merges[0]["survivor"]["name"]} | {L["name"] for L in merges[0]["losers"]}
        self.assertEqual(names, {"Alpha", "Bravo"})

    def test_moving_onto_a_blank_rows_number_is_still_refused(self):
        """A merge needs the number TYPED on every row in the group. A BLANK
        cell was never typed, so this is a collision, not an instruction to
        join. Live case 2026-08-25: Zee sent row 17 to 34 while `zee` sat on 34
        with an empty cell. Reading that as a merge would have deleted a row he
        never marked."""
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        self.assertRefuses(self.records(("u-a", 1, 2), ("u-b", 2, "")),
                           "collision rather than a merge")

    def test_the_same_number_typed_on_both_rows_IS_a_merge(self):
        """The difference from the test above is one typed cell. Zee's own
        sheet does this: FruitSync #12 is typed 6 and stays, while FruitSync
        #26 is typed 6 and moves."""
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        self.mkbundle("u-b", "2026-01-01-Bravo-close")   # breaks the tie
        _m, _d, _u, _f, merges = plan.build_plan(
            self.records(("u-a", 1, 2), ("u-b", 2, 2)), self.home)
        self.assertEqual(len(merges), 1)
        self.assertEqual(merges[0]["to"], 2)
        names = {merges[0]["survivor"]["name"]} | {L["name"] for L in merges[0]["losers"]}
        self.assertEqual(names, {"Alpha", "Bravo"})

    def test_a_negative_number_is_refused(self):
        self.mkrow("u-a", "Alpha", 1)
        self.assertRefuses(self.records(("u-a", 1, -3)), "cannot hold a negative number")

    def test_a_fraction_is_refused_rather_than_rounded(self):
        """Rounding 3.5 would silently pick a row the user did not name."""
        self.mkrow("u-a", "Alpha", 1)
        self.assertRefuses(self.records(("u-a", 1, 3.5)), "whole numbers only")

    def test_excel_style_floats_and_strings_are_accepted_as_whole_numbers(self):
        """One typed cell can come back as 3, 3.0 or '3'. All three mean 3."""
        self.mkrow("u-a", "Alpha", 1)
        for value in (3, 3.0, "3", " 3 "):
            registry_lib.set_pick_ordinal("u-a", 1, self.home)
            moves, _, _, _, _m = plan.build_plan(self.records(("u-a", 1, value)), self.home)
            self.assertEqual(moves[0]["to"], 3, "value %r" % (value,))

    def test_a_row_that_no_longer_exists_is_refused(self):
        self.mkrow("u-a", "Alpha", 1)
        recs = self.records(("u-a", 1, 9))
        os.unlink(registry_lib.row_path("u-a", self.home))
        self.assertRefuses(recs, "no registry row")

    def test_an_empty_uuid_is_refused(self):
        self.mkrow("u-a", "Alpha", 1)
        recs = self.records(("u-a", 1, 9))
        recs[0]["project_uuid"] = ""
        self.assertRefuses(recs, "project_uuid is empty")

    def test_the_same_row_twice_is_refused(self):
        self.mkrow("u-a", "Alpha", 1)
        recs = self.records(("u-a", 1, 9)) + self.records(("u-a", 1, 10))
        self.assertRefuses(recs, "appears twice")

    def test_a_sheet_with_no_changes_is_refused_rather_than_silently_doing_nothing(self):
        self.mkrow("u-a", "Alpha", 1)
        self.assertRefuses(self.records(("u-a", 1, "")), "nothing to do")

    def test_a_missing_column_is_refused_with_the_column_named(self):
        self.mkrow("u-a", "Alpha", 1)
        recs = self.records(("u-a", 1, 9))
        del recs[0]["project_uuid"]
        self.assertRefuses(recs, "missing required column")


# --------------------------------------------------------- file round-tripping

class SheetFileTest(PlanTestBase):
    def test_csv_round_trips_through_the_reader(self):
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        path = os.path.join(self.home, "sheet.csv")
        rows = [{"name": "Alpha", "current_number": 1, "new_number": 2,
                 "status": "parked", "tier": "RECENT", "root": "/x", "project_uuid": "u-a"},
                {"name": "Bravo", "current_number": 2, "new_number": 1,
                 "status": "parked", "tier": "RECENT", "root": "/y", "project_uuid": "u-b"}]
        plan.write_csv(path, rows)
        back = plan.read_sheet(path)
        moves, _, _, _, _m = plan.build_plan(back, self.home)
        self.assertEqual(sorted((m["from"], m["to"]) for m in moves), [(1, 2), (2, 1)])

    def test_a_csv_blank_cell_survives_the_round_trip_as_leave_alone(self):
        self.mkrow("u-a", "Alpha", 1)
        self.mkrow("u-b", "Bravo", 2)
        path = os.path.join(self.home, "sheet.csv")
        plan.write_csv(path, [
            {"name": "Alpha", "current_number": 1, "new_number": 9,
             "status": "parked", "tier": "RECENT", "root": "/x", "project_uuid": "u-a"},
            {"name": "Bravo", "current_number": 2, "new_number": "",
             "status": "parked", "tier": "RECENT", "root": "/y", "project_uuid": "u-b"}])
        moves, deletes, unchanged, _, _m = plan.build_plan(plan.read_sheet(path), self.home)
        self.assertEqual(len(moves), 1)
        self.assertEqual(len(unchanged), 1)

    def test_an_unknown_file_type_is_refused(self):
        with self.assertRaises(plan.Refused) as ctx:
            plan.read_sheet(os.path.join(self.home, "sheet.txt"))
        self.assertIn("unrecognised file type", str(ctx.exception))

    @unittest.skipUnless(
        importlib.util.find_spec("openpyxl"), "openpyxl not importable here")
    def test_xlsx_round_trips_through_the_reader(self):
        self.mkrow("u-a", "Alpha", 5)
        self.mkrow("u-b", "Bravo", 7)
        path = os.path.join(self.home, "sheet.xlsx")
        plan.write_xlsx(path, [
            {"name": "Alpha", "current_number": 5, "new_number": 7,
             "status": "parked", "tier": "RECENT", "root": "/x", "project_uuid": "u-a"},
            {"name": "Bravo", "current_number": 7, "new_number": 5,
             "status": "parked", "tier": "RECENT", "root": "/y", "project_uuid": "u-b"}])
        moves, _, _, _, _m = plan.build_plan(plan.read_sheet(path), self.home)
        self.assertEqual(sorted((m["from"], m["to"]) for m in moves), [(5, 7), (7, 5)])

    @unittest.skipUnless(
        importlib.util.find_spec("openpyxl"), "openpyxl not importable here")
    def test_xlsx_header_spaces_map_back_to_the_column_names(self):
        """write_xlsx prints `new number`; the reader must see `new_number`."""
        path = os.path.join(self.home, "sheet.xlsx")
        plan.write_xlsx(path, [
            {"name": "Alpha", "current_number": 1, "new_number": "",
             "status": "parked", "tier": "RECENT", "root": "/x", "project_uuid": "u-a"}])
        back = plan.read_sheet(path)
        self.assertIn("new_number", back[0])
        self.assertIn("project_uuid", back[0])


class CarryForwardTests(PlanTestBase):
    """Exporting rewrites the whole sheet. Zee filled 50 cells on 2026-08-25 and
    a re-export would have blanked every one of them, so the fresh sheet copies
    the earlier one's typed column across before it is written."""

    def sheet(self, path, triples):
        """triples = (name, current, new, uuid)."""
        plan.write_xlsx(path, [
            {"name": n, "current_number": c, "new_number": v, "status": "parked",
             "tier": "RECENT", "root": "/x", "project_uuid": u}
            for n, c, v, u in triples])
        return path

    def fresh(self, *triples):
        return [{"name": n, "current_number": c, "new_number": "", "status": "parked",
                 "tier": "RECENT", "root": "/x", "project_uuid": u}
                for n, c, u in triples]

    def test_a_typed_number_survives_a_re_export(self):
        old = self.sheet(os.path.join(self.home, "old.xlsx"),
                         [("Alpha", 1, 7, "u-a"), ("Beta", 2, "", "u-b")])
        rows = self.fresh(("Alpha", 1, "u-a"), ("Beta", 2, "u-b"))
        carried, dropped, blank = plan.carry_forward(rows, old)
        self.assertEqual([r["name"] for r in carried], ["Alpha"])
        self.assertEqual(rows[0]["new_number"], 7)
        self.assertEqual(rows[1]["new_number"], "")
        self.assertEqual(dropped, [])
        self.assertEqual([r["name"] for r in blank], ["Beta"])

    def test_rows_are_matched_by_uuid_not_by_name(self):
        """Names repeat on this machine — three rows are called FruitSync. Only
        the uuid says which typed cell belongs to which row."""
        old = self.sheet(os.path.join(self.home, "old.xlsx"),
                         [("FruitSync", 1, 6, "u-1"), ("FruitSync", 2, 40, "u-2")])
        rows = self.fresh(("FruitSync", 2, "u-2"), ("FruitSync", 1, "u-1"))
        plan.carry_forward(rows, old)
        by_uuid = {r["project_uuid"]: r["new_number"] for r in rows}
        self.assertEqual(by_uuid["u-1"], 6)
        self.assertEqual(by_uuid["u-2"], 40)

    def test_a_renamed_row_still_carries_its_number(self):
        """The uuid is stable across a rename, so the typing follows the row."""
        old = self.sheet(os.path.join(self.home, "old.xlsx"), [("Old Name", 1, 9, "u-a")])
        rows = self.fresh(("Brand New Name", 1, "u-a"))
        carried, dropped, _ = plan.carry_forward(rows, old)
        self.assertEqual(rows[0]["new_number"], 9)
        self.assertEqual(len(carried), 1)
        self.assertEqual(dropped, [])

    def test_a_deleted_row_is_reported_not_dropped_in_silence(self):
        """The two R2P worktree rows were deleted between the two exports. Their
        typed numbers cannot land anywhere, and saying so is the whole point."""
        old = self.sheet(os.path.join(self.home, "old.xlsx"),
                         [("Alpha", 1, 7, "u-a"), ("R2P tab-a ledger", 54, 13, "u-gone")])
        rows = self.fresh(("Alpha", 1, "u-a"))
        carried, dropped, _ = plan.carry_forward(rows, old)
        self.assertEqual(len(carried), 1)
        self.assertEqual(len(dropped), 1)
        self.assertEqual(dropped[0]["name"], "R2P tab-a ledger")
        self.assertEqual(dropped[0]["new_number"], 13)

    def test_a_typed_zero_carries_across(self):
        """0 means delete this row. It is a real instruction, not an empty cell,
        so it must survive a re-export like any other number."""
        old = self.sheet(os.path.join(self.home, "old.xlsx"), [("Doomed", 1, 0, "u-a")])
        rows = self.fresh(("Doomed", 1, "u-a"))
        carried, _, blank = plan.carry_forward(rows, old)
        self.assertEqual(rows[0]["new_number"], 0)
        self.assertEqual(len(carried), 1)
        self.assertEqual(blank, [])

    def test_filled_count_sees_typed_cells_only(self):
        path = self.sheet(os.path.join(self.home, "s.xlsx"),
                          [("A", 1, 5, "u-a"), ("B", 2, "", "u-b"), ("C", 3, 0, "u-c")])
        self.assertEqual(plan.filled_count(path), 2)

    def test_filled_count_of_a_missing_file_is_zero(self):
        """A first-ever export has nothing to protect, and must not crash."""
        self.assertEqual(plan.filled_count(os.path.join(self.home, "nope.xlsx")), 0)

    def test_a_csv_sheet_carries_forward_too(self):
        """openpyxl is not always importable, so export falls back to CSV. The
        fallback must not be the path that loses work."""
        path = os.path.join(self.home, "old.csv")
        plan.write_csv(path, [
            {"name": "Alpha", "current_number": 1, "new_number": 7, "status": "parked",
             "tier": "RECENT", "root": "/x", "project_uuid": "u-a"}])
        rows = self.fresh(("Alpha", 1, "u-a"))
        plan.carry_forward(rows, path)
        self.assertEqual(rows[0]["new_number"], 7)

    def test_a_blank_uuid_in_the_old_sheet_is_ignored(self):
        """If Zee pastes a row in by hand and leaves the uuid off, that cell
        cannot be matched to anything. Skip it rather than guess by name."""
        old = self.sheet(os.path.join(self.home, "old.xlsx"), [("Alpha", 1, 7, "")])
        rows = self.fresh(("Alpha", 1, "u-a"))
        carried, dropped, blank = plan.carry_forward(rows, old)
        self.assertEqual(carried, [])
        self.assertEqual(dropped, [])
        self.assertEqual(len(blank), 1)

    def test_a_junk_cell_is_refused_with_its_line_number(self):
        """Garbage in the column is a refusal that names where to look, not a
        silently skipped row."""
        old = self.sheet(os.path.join(self.home, "old.xlsx"), [("Alpha", 1, "seven", "u-a")])
        rows = self.fresh(("Alpha", 1, "u-a"))
        with self.assertRaises(plan.Refused):
            plan.carry_forward(rows, old)



if __name__ == "__main__":
    unittest.main(verbosity=1)
