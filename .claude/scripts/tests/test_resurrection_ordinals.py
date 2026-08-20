#!/usr/bin/env python3
"""test_resurrection_ordinals.py — stdlib unittest for permanent pick numbers.

Covers Zee's two rulings of 2026-08-19 (items 7 and 8 of
planning/resurrection-fix/BRIEF.md): a pick number is assigned once and never
moves on its own, and the delete / restore / purge / swap / renumber / compact
verbs that let a human move one deliberately.

Before this file there was ZERO coverage of numbering:
test_resurrection_book.py's 14 methods all either test window_label() or call
render_human() with pick_number hardcoded to 1, and build_book was never
called by any test.

Every test runs against a FIXTURE registry under a throwaway home. Nothing
here ever reads or writes the real ~/.acos.
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
import windows_lib  # noqa: E402


def _load(stem, filename):
    """Import a hyphenated script by path — `import backfill-ordinals` is not
    legal Python, and the assertions must run against SHIPPED code."""
    spec = importlib.util.spec_from_file_location(stem, os.path.join(_RESDIR, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


backfill = _load("backfill_ordinals", "backfill-ordinals.py")
manage = _load("manage_ordinals", "manage-ordinals.py")
cscan = _load("conflict_scan", "conflict-scan.py")
view = _load("resurrect_view", "resurrect-view.py")


class OrdinalTestBase(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="ord-test-")
        os.makedirs(registry_lib.registry_dir(self.home), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def mkrow(self, uuid, name, enrolled_at, status="active", ordinal=None):
        """Write a fixture row directly, bypassing upsert_row's minting."""
        root = os.path.join(self.home, "roots", name)
        os.makedirs(root, exist_ok=True)
        st = os.stat(root)
        row = {
            "project_uuid": uuid, "root": root,
            "root_casefold": os.path.realpath(root).casefold(),
            "dev_ino": [st.st_dev, st.st_ino], "name": name,
            "workspace_name": name, "status": status,
            "enrolled_at": enrolled_at, "last_verified_at": enrolled_at,
            "last_close": None, "last_session_id_hint": None, "git": None,
            "tombstoned_at": None, "pick_ordinal": ordinal,
        }
        registry_lib.atomic_write_json(registry_lib.row_path(uuid, self.home), row)
        return row

    # enrolled_at ascending == this order, so after a backfill Alpha is always
    # 1, Bravo 2, Charlie 3, Delta 4 — whatever n is. Tests name rows by that.
    NAMES = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot"]
    STAMPS = {"Alpha": "2026-01-01", "Bravo": "2026-02-02", "Charlie": "2026-03-03",
              "Delta": "2026-04-04", "Echo": "2026-05-05", "Foxtrot": "2026-06-06"}

    def seed(self, n=4):
        """The first n names, WRITTEN in scrambled order on purpose.

        The scramble is the point: a backfill that used directory order or
        creation order instead of enrolled_at would pass a test that created
        rows in the order it expects them back.
        """
        names = self.NAMES[:n]
        write_order = sorted(names, key=lambda s: (len(s), s), reverse=True)
        for name in write_order:
            self.mkrow("uuid-" + name.lower(), name,
                       self.STAMPS[name] + "T00:00:00+00:00")
        return names

    def backfill_all(self):
        assignments, _, _ = backfill.plan(self.home)
        backfill.apply_plan(assignments, self.home)
        return assignments

    def run_verb(self, argv):
        """Invoke manage-ordinals.py's main() in-process, capturing the code."""
        return manage.main(list(argv) + ["--home", self.home])


# ---------------------------------------------------------------- backfill ---

class BackfillTest(OrdinalTestBase):
    def test_backfill_is_deterministic_over_a_fixture_registry(self):
        """Same registry in, same assignment out — every time.

        A backfill that depended on directory order would drift between
        machines and between runs, and the whole point of a permanent number
        is that it cannot drift."""
        self.seed(4)
        first = [(r["name"], n) for r, n in backfill.plan(self.home)[0]]
        second = [(r["name"], n) for r, n in backfill.plan(self.home)[0]]
        self.assertEqual(first, second)
        self.assertEqual(first, [("Alpha", 1), ("Bravo", 2), ("Charlie", 3), ("Delta", 4)])

    def test_backfill_orders_by_enrolled_at_not_by_file_order(self):
        """The oldest project gets 1. That is the one ordering a human can
        predict without reading anything."""
        self.seed(4)
        assigned = {r["name"]: n for r, n in backfill.plan(self.home)[0]}
        self.assertEqual(assigned["Alpha"], 1)
        self.assertEqual(assigned["Delta"], 4)

    def test_backfill_is_idempotent(self):
        """A second run must do nothing at all — not re-issue, not re-order,
        and not append duplicate ledger lines."""
        self.seed(4)
        self.backfill_all()
        before = ordinal_lib.read_events(self.home)
        again, numbered, _ = backfill.plan(self.home)
        self.assertEqual(again, [])
        self.assertEqual(len(numbered), 4)
        backfill.apply_plan(again, self.home)
        self.assertEqual(ordinal_lib.read_events(self.home), before)

    def test_an_interrupted_backfill_resumes_without_displacing(self):
        """Half a run then a full run must land where one clean run would.

        This is the crash case: the process dies partway through, and the
        numbers already written must be treated as final."""
        self.seed(4)
        assignments, _, _ = backfill.plan(self.home)
        backfill.apply_plan(assignments[:2], self.home)   # only Alpha and Bravo
        rest, numbered, start = backfill.plan(self.home)
        self.assertEqual(start, 3)
        self.assertEqual([(r["name"], n) for r, n in rest],
                         [("Charlie", 3), ("Delta", 4)])
        self.assertEqual(registry_lib.load_row("uuid-alpha", self.home)["pick_ordinal"], 1)

    def test_archived_rows_are_numbered_too(self):
        """A tombstoned row that carries no number cannot be named by restore,
        renumber or purge — it is invisible to every verb."""
        self.seed(3)
        self.mkrow("uuid-tomb", "Tombstoned", "2026-07-07T00:00:00+00:00", "tombstoned")
        assigned = {r["name"]: n for r, n in backfill.plan(self.home)[0]}
        self.assertIn("Tombstoned", assigned)
        self.assertIsNotNone(assigned["Tombstoned"])


# ------------------------------------------------------------- persistence ---

class OrdinalPersistenceTest(OrdinalTestBase):
    def test_a_new_row_takes_max_plus_one_from_the_ledger(self):
        self.seed(4)
        self.backfill_all()
        root = os.path.join(self.home, "roots", "New")
        os.makedirs(root, exist_ok=True)
        row = registry_lib.upsert_row(
            {"project_uuid": "uuid-new", "root": root, "workspace_name": "New"}, self.home)
        self.assertEqual(row["pick_ordinal"], 5)

    def test_max_plus_one_counts_tombstoned_and_deleted_rows(self):
        """The ledger, not the live rows, is what `max+1` reads.

        A deleted row is gone from registry.d/, so a live-row scan would hand
        its number straight to the next project — which is the collision the
        ledger exists to prevent."""
        self.seed(4)
        self.backfill_all()
        registry_lib.tombstone_row("uuid-delta", self.home)          # ordinal 4, hidden
        self.run_verb(["delete", "3", "--confirm-name", "Charlie",   # ordinal 3, moved away
                       "--apply", "--no-cmux"])
        self.assertIsNone(registry_lib.load_row("uuid-charlie", self.home))
        root = os.path.join(self.home, "roots", "New")
        os.makedirs(root, exist_ok=True)
        row = registry_lib.upsert_row(
            {"project_uuid": "uuid-new", "root": root, "workspace_name": "New"}, self.home)
        self.assertEqual(row["pick_ordinal"], 5, "must not reuse 3 or 4")

    def test_an_ordinal_survives_park_active_park(self):
        """Status changes are the common case — they must never touch the
        number. This is the exact drift the ruling removed."""
        self.seed(2)
        self.backfill_all()
        root = registry_lib.load_row("uuid-alpha", self.home)["root"]
        for status in ("parked", "active", "parked"):
            row = registry_lib.upsert_row(
                {"project_uuid": "uuid-alpha", "root": root, "status": status}, self.home)
            self.assertEqual(row["pick_ordinal"], 1)

    def test_an_ordinal_survives_finish_and_tombstone(self):
        self.seed(2)
        self.backfill_all()
        root = registry_lib.load_row("uuid-bravo", self.home)["root"]
        registry_lib.upsert_row(
            {"project_uuid": "uuid-bravo", "root": root, "status": "completed"}, self.home)
        self.assertEqual(registry_lib.load_row("uuid-bravo", self.home)["pick_ordinal"], 2)
        registry_lib.tombstone_row("uuid-bravo", self.home)
        self.assertEqual(registry_lib.load_row("uuid-bravo", self.home)["pick_ordinal"], 2)

    def test_zero_is_rejected_by_the_schema(self):
        """0 is reserved: acos-safe-close/SKILL.md:235-241 uses it for
        'new project', so a row holding 0 would read as 'not a project yet'."""
        self.seed(1)
        with self.assertRaises(ValueError):
            registry_lib.set_pick_ordinal("uuid-alpha", 0, self.home)

    def test_true_is_not_accepted_as_ordinal_one(self):
        """bool is an int subclass in Python, so True would pass a naive
        isinstance(x, int) check and land as ordinal 1."""
        self.seed(1)
        with self.assertRaises(ValueError):
            registry_lib.set_pick_ordinal("uuid-alpha", True, self.home)


# ------------------------------------------------------------------ ledger ---

class LedgerTest(OrdinalTestBase):
    def test_a_retired_ordinal_is_never_auto_reissued(self):
        self.seed(3)
        self.backfill_all()
        ordinal_lib.append_event("retire", 2, "uuid-bravo", "Bravo", self.home)
        self.assertEqual(ordinal_lib.next_ordinal(self.home), 4)
        self.assertIn(2, ordinal_lib.retired_ordinals(self.home))

    def test_a_garbage_ledger_line_raises_rather_than_being_skipped(self):
        """A skipped line would make a retired number look free — the exact
        failure the ledger exists to prevent."""
        self.seed(1)
        self.backfill_all()
        with open(ordinal_lib.ledger_path(self.home), "a") as fh:
            fh.write("{ this is not json\n")
        with self.assertRaises(ValueError):
            ordinal_lib.read_events(self.home)


# ------------------------------------------------------------------- verbs ---

class DeleteRestorePurgeTest(OrdinalTestBase):
    def test_delete_moves_the_row_and_never_unlinks(self):
        self.seed(3)
        self.backfill_all()
        code = self.run_verb(["delete", "1", "--confirm-name", "Alpha",
                              "--apply", "--no-cmux"])
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(registry_lib.row_path("uuid-alpha", self.home)))
        self.assertTrue(os.path.exists(manage.deleted_row_path("uuid-alpha", self.home)))

    def test_delete_moves_window_manifests_alongside_the_row(self):
        """A restore that brought the row back but not its windows would
        leave the project unable to say which windows it had open."""
        self.seed(2)
        self.backfill_all()
        windows_lib.claim_window("uuid-alpha", "WS-1", label="tab-a", home=self.home)
        self.assertTrue(os.path.isdir(windows_lib.windows_dir("uuid-alpha", self.home)))
        self.run_verb(["delete", "1", "--confirm-name", "Alpha", "--apply", "--no-cmux"])
        self.assertFalse(os.path.isdir(windows_lib.windows_dir("uuid-alpha", self.home)))
        self.assertTrue(os.path.isdir(manage.deleted_windows_dir("uuid-alpha", self.home)))

    def test_delete_leaves_the_knowledge_store_in_place(self):
        """It is addressed by project_uuid and survives independently. The
        receipt must SAY so rather than leaving it a silent orphan."""
        self.seed(2)
        self.backfill_all()
        kdir = os.path.join(self.home, ".acos", "knowledge", "uuid-alpha")
        os.makedirs(kdir, exist_ok=True)
        open(os.path.join(kdir, "facts.jsonl"), "w").close()
        self.run_verb(["delete", "1", "--confirm-name", "Alpha", "--apply", "--no-cmux"])
        self.assertTrue(os.path.isdir(kdir))

    def test_delete_refuses_a_bare_yes(self):
        """Akhawe & Felt 2013: extra clicks do not deter — 84% of users who
        did the first two clicks did the third. The NAME must be typed."""
        self.seed(2)
        self.backfill_all()
        code = self.run_verb(["delete", "1", "--confirm-name", "y", "--apply", "--no-cmux"])
        self.assertEqual(code, 1)
        self.assertTrue(os.path.exists(registry_lib.row_path("uuid-alpha", self.home)))

    def test_delete_refuses_with_no_confirmation_at_all(self):
        self.seed(2)
        self.backfill_all()
        code = self.run_verb(["delete", "1", "--apply", "--no-cmux"])
        self.assertEqual(code, 1)
        self.assertTrue(os.path.exists(registry_lib.row_path("uuid-alpha", self.home)))

    def test_delete_refuses_a_live_row(self):
        """Deleting a row while a window is open on it would leave that window
        bound to a row the book no longer lists."""
        self.seed(2)
        self.backfill_all()
        row = registry_lib.load_row("uuid-alpha", self.home)
        live = {"uuid-alpha": ["workspace:7 [key:uuid-alpha] Alpha"]}
        with self.assertRaises(manage.Refused) as ctx:
            manage._assert_not_live(row, live, None, "delete")
        self.assertIn("workspace:7", str(ctx.exception))

    def test_delete_refuses_when_the_liveness_check_cannot_run(self):
        """An unknown answer is not a safe answer. Refusing beats guessing."""
        self.seed(2)
        self.backfill_all()
        row = registry_lib.load_row("uuid-alpha", self.home)
        with self.assertRaises(manage.Refused) as ctx:
            manage._assert_not_live(row, {}, "cmux could not be run", "delete")
        self.assertIn("could not run", str(ctx.exception))

    def test_a_delete_retires_the_ordinal(self):
        self.seed(3)
        self.backfill_all()
        self.run_verb(["delete", "2", "--confirm-name", "Bravo", "--apply", "--no-cmux"])
        self.assertIn(2, ordinal_lib.retired_ordinals(self.home))
        self.assertEqual(ordinal_lib.next_ordinal(self.home), 4)

    def test_restore_brings_the_row_and_its_number_back(self):
        self.seed(3)
        self.backfill_all()
        self.run_verb(["delete", "2", "--confirm-name", "Bravo", "--apply", "--no-cmux"])
        code = self.run_verb(["restore", "uuid-bravo", "--apply"])
        self.assertEqual(code, 0)
        row = registry_lib.load_row("uuid-bravo", self.home)
        self.assertEqual(row["pick_ordinal"], 2)
        self.assertNotIn(2, ordinal_lib.retired_ordinals(self.home))

    def test_restore_refuses_when_the_original_number_is_taken(self):
        """Never silently displace a live row. Name the holder and stop."""
        self.seed(3)
        self.backfill_all()
        self.run_verb(["delete", "2", "--confirm-name", "Bravo", "--apply", "--no-cmux"])
        # Charlie moves onto the freed 2 by deliberate, confirmed reuse.
        self.run_verb(["renumber", "3", "2", "--reuse-retired", "--apply"])
        code = self.run_verb(["restore", "uuid-bravo", "--apply"])
        self.assertEqual(code, 1)
        self.assertIsNone(registry_lib.load_row("uuid-bravo", self.home))

    def test_purge_refuses_a_row_that_was_never_deleted(self):
        """An unlink always takes two separate human acts."""
        self.seed(2)
        self.backfill_all()
        code = self.run_verb(["purge", "uuid-alpha", "--confirm-name", "Alpha", "--apply"])
        self.assertEqual(code, 1)
        self.assertTrue(os.path.exists(registry_lib.row_path("uuid-alpha", self.home)))

    def test_purge_unlinks_only_from_deleted_and_keeps_the_ordinal_retired(self):
        self.seed(2)
        self.backfill_all()
        self.run_verb(["delete", "1", "--confirm-name", "Alpha", "--apply", "--no-cmux"])
        code = self.run_verb(["purge", "uuid-alpha", "--confirm-name", "Alpha", "--apply"])
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(manage.deleted_row_path("uuid-alpha", self.home)))
        self.assertIn(1, ordinal_lib.retired_ordinals(self.home))


class SwapTest(OrdinalTestBase):
    def test_swap_exchanges_two_numbers_and_leaves_no_clash(self):
        self.seed(3)
        self.backfill_all()
        code = self.run_verb(["swap", "1", "3", "--apply"])
        self.assertEqual(code, 0)
        self.assertEqual(registry_lib.load_row("uuid-alpha", self.home)["pick_ordinal"], 3)
        self.assertEqual(registry_lib.load_row("uuid-charlie", self.home)["pick_ordinal"], 1)
        holders = ordinal_lib.live_holders(self.home)
        self.assertTrue(all(len(v) == 1 for v in holders.values()))

    def test_swap_retires_nothing(self):
        """Both numbers are still held afterwards, so neither is retired."""
        self.seed(3)
        self.backfill_all()
        self.run_verb(["swap", "1", "3", "--apply"])
        self.assertEqual(ordinal_lib.retired_ordinals(self.home), {})

    def test_swap_writes_one_ledger_entry_naming_both_sides(self):
        self.seed(3)
        self.backfill_all()
        before = len(ordinal_lib.read_events(self.home))
        self.run_verb(["swap", "1", "3", "--apply"])
        events = ordinal_lib.read_events(self.home)
        self.assertEqual(len(events), before + 1)
        entry = events[-1]
        self.assertEqual(entry["verb"], "swap")
        self.assertEqual(entry["counterpart"]["project_uuid"], "uuid-charlie")

    def test_a_partial_swap_is_detected_on_re_read(self):
        """There is no lock, so the swap cannot be atomic. A half-applied
        swap must be reported LOUDLY, never retried silently — a silent retry
        over a half-applied swap is how one number lands on two rows."""
        self.seed(3)
        self.backfill_all()
        real = registry_lib.set_pick_ordinal
        calls = {"n": 0}

        def flaky(uuid, ordinal, home=None):
            calls["n"] += 1
            if calls["n"] == 2:
                return registry_lib.load_row(uuid, home)   # second write silently lost
            return real(uuid, ordinal, home)

        registry_lib.set_pick_ordinal = flaky
        try:
            code = self.run_verb(["swap", "1", "3", "--apply"])
        finally:
            registry_lib.set_pick_ordinal = real
        self.assertEqual(code, 1, "a partial swap must not report success")
        holders = ordinal_lib.live_holders(self.home)
        self.assertEqual(len(holders.get(3, [])), 2, "the fixture should now clash")
        clashes = [f for f in cscan.scan(self.home) if f["type"] == "ORDINAL-CLASH"]
        self.assertTrue(clashes, "conflict-scan must name the clash")

    def test_swap_refuses_a_number_no_row_holds(self):
        self.seed(2)
        self.backfill_all()
        self.assertEqual(self.run_verb(["swap", "1", "99", "--apply"]), 1)


class RenumberTest(OrdinalTestBase):
    def test_renumber_refuses_zero(self):
        self.seed(2)
        self.backfill_all()
        self.assertEqual(self.run_verb(["renumber", "1", "0", "--apply"]), 1)
        self.assertEqual(registry_lib.load_row("uuid-alpha", self.home)["pick_ordinal"], 1)

    def test_renumber_refuses_a_negative_number(self):
        self.seed(2)
        self.backfill_all()
        self.assertEqual(self.run_verb(["renumber", "1", "-4", "--apply"]), 1)

    def test_renumber_refuses_a_target_held_by_a_live_row(self):
        """Never silently displace. Name the holder and suggest swap."""
        self.seed(3)
        self.backfill_all()
        self.assertEqual(self.run_verb(["renumber", "1", "2", "--apply"]), 1)
        self.assertEqual(registry_lib.load_row("uuid-alpha", self.home)["pick_ordinal"], 1)

    def test_renumber_refuses_a_retired_target_without_the_extra_flag(self):
        """Manual reuse is ALLOWED — but as a decision, not a collision."""
        self.seed(3)
        self.backfill_all()
        self.run_verb(["delete", "2", "--confirm-name", "Bravo", "--apply", "--no-cmux"])
        self.assertEqual(self.run_verb(["renumber", "1", "2", "--apply"]), 1)
        self.assertEqual(self.run_verb(["renumber", "1", "2", "--reuse-retired", "--apply"]), 0)
        self.assertEqual(registry_lib.load_row("uuid-alpha", self.home)["pick_ordinal"], 2)

    def test_renumber_to_a_free_never_issued_number_moves_the_high_water_mark(self):
        self.seed(2)
        self.backfill_all()
        self.assertEqual(self.run_verb(["renumber", "1", "40", "--apply"]), 0)
        self.assertEqual(ordinal_lib.max_ever_issued(self.home), 40)
        self.assertEqual(ordinal_lib.next_ordinal(self.home), 41)

    def test_the_vacated_number_is_retired_not_freed(self):
        self.seed(2)
        self.backfill_all()
        self.run_verb(["renumber", "1", "40", "--apply"])
        self.assertIn(1, ordinal_lib.retired_ordinals(self.home))

    def test_renumber_accepts_the_word_to(self):
        """`renumber 7 to 9` is how the brief writes it and how a human says
        it; `renumber 7 9` must keep working too."""
        self.seed(2)
        self.backfill_all()
        self.assertEqual(self.run_verb(["renumber", "1", "to", "40", "--apply"]), 0)
        self.assertEqual(registry_lib.load_row("uuid-alpha", self.home)["pick_ordinal"], 40)


class CompactTest(OrdinalTestBase):
    def test_compact_renumbers_one_to_n(self):
        self.seed(4)
        self.backfill_all()
        self.run_verb(["delete", "2", "--confirm-name", "Bravo", "--apply", "--no-cmux"])
        code = self.run_verb(["compact", "--confirm", "compact", "--apply"])
        self.assertEqual(code, 0)
        holders = ordinal_lib.live_holders(self.home)
        self.assertEqual(sorted(holders), [1, 2, 3])

    def test_compact_writes_one_ledger_entry_per_moved_row(self):
        self.seed(4)
        self.backfill_all()
        self.run_verb(["delete", "1", "--confirm-name", "Alpha", "--apply", "--no-cmux"])
        before = len(ordinal_lib.read_events(self.home))
        self.run_verb(["compact", "--confirm", "compact", "--apply"])
        moved = len(ordinal_lib.read_events(self.home)) - before
        self.assertEqual(moved, 3, "Bravo/Charlie/Delta each move down by one")

    def test_compact_refuses_a_bare_yes(self):
        """It invalidates every number the user has memorised, so the word
        `compact` must be typed in full."""
        self.seed(3)
        self.backfill_all()
        self.run_verb(["delete", "1", "--confirm-name", "Alpha", "--apply", "--no-cmux"])
        self.assertEqual(self.run_verb(["compact", "--confirm", "y", "--apply"]), 1)

    def test_compact_refuses_while_a_clash_exists(self):
        """Compacting over a clash would silently pick a winner."""
        self.seed(3)
        self.backfill_all()
        registry_lib.set_pick_ordinal("uuid-charlie", 1, self.home)   # now 1 is doubled
        self.assertEqual(self.run_verb(["compact", "--confirm", "compact", "--apply"]), 1)

    def test_compact_is_a_no_op_when_there_are_no_gaps(self):
        self.seed(3)
        self.backfill_all()
        before = len(ordinal_lib.read_events(self.home))
        self.assertEqual(self.run_verb(["compact", "--confirm", "compact", "--apply"]), 0)
        self.assertEqual(len(ordinal_lib.read_events(self.home)), before)


# ------------------------------------------------------------------- book ----

class BookTest(OrdinalTestBase):
    """build_book was never called by any existing test. These call it."""

    def build(self):
        return view.build_book(home=self.home, no_cmux=True, no_procs=True)

    def test_the_book_reads_the_stored_number_and_never_counts(self):
        self.seed(3)
        self.backfill_all()
        registry_lib.set_pick_ordinal("uuid-alpha", 40, self.home)
        book = self.build()
        got = {p["name"]: p["pick_number"] for p in book["projects"]}
        self.assertEqual(got["Alpha"], 40, "must be the row's number, not a position")

    def test_gutter_integer_equals_book_json_pick_number_for_every_row(self):
        """The invariant at resurrect-view.py:501-506, preserved. One
        persisted value cannot drift from itself."""
        import re
        self.seed(4)
        self.backfill_all()
        book = self.build()
        text = view.render_human(book, use_color=False)
        gutter = {int(m.group(1)): m.group(2).strip()
                  for m in re.finditer(r"^\s{2}\s*(\d+)\.\s+(\S[^\n]*?)\s{2,}",
                                       text, re.M)}
        expected = {p["pick_number"]: p["name"] for p in book["projects"]}
        self.assertEqual(set(gutter), set(expected))
        for n, name in expected.items():
            self.assertTrue(gutter[n].startswith(name[:12]),
                            "gutter %d shows %r, book.json says %r" % (n, gutter[n], name))

    def test_archived_rows_carry_a_number_but_are_not_pickable(self):
        """Numbered is not pickable. Being numbered lets restore/renumber/
        purge name them; `pickable` is what open-picks.sh must test."""
        self.seed(2)
        self.mkrow("uuid-tomb", "Tombstoned", "2026-07-07T00:00:00+00:00", "tombstoned")
        self.backfill_all()
        book = self.build()
        arch = [p for p in book["projects"] if p["tier"] == "ARCHIVED"]
        self.assertEqual(len(arch), 1)
        self.assertIsNotNone(arch[0]["pick_number"])
        self.assertFalse(arch[0]["pickable"])
        self.assertTrue(all(p["pickable"] for p in book["projects"] if p["tier"] != "ARCHIVED"))

    def test_an_unnumbered_row_is_surfaced_not_silently_blank(self):
        """An unnumbered row cannot be picked, restored or renumbered — it is
        invisible to every verb, so the book must say so."""
        self.seed(2)
        self.backfill_all()
        self.mkrow("uuid-new", "Newcomer", "2026-09-09T00:00:00+00:00")
        book = self.build()
        self.assertEqual(book["unnumbered_count"], 1)
        self.assertIn("backfill-ordinals.py", view.render_human(book, use_color=False))


# ---------------------------------------------------------- conflict scan ----

class ConflictScanTest(OrdinalTestBase):
    def test_ordinal_clash_fires_on_two_live_rows_sharing_a_number(self):
        self.seed(3)
        self.backfill_all()
        registry_lib.set_pick_ordinal("uuid-charlie", 1, self.home)
        found = [f for f in cscan.scan(self.home) if f["type"] == "ORDINAL-CLASH"]
        self.assertEqual(len(found), 1)
        self.assertIn("Alpha", found[0]["detail"])
        self.assertIn("Charlie", found[0]["detail"])

    def test_ordinal_clash_ignores_a_tombstoned_row(self):
        """A tombstoned row is hidden, so it cannot be picked by number and
        cannot make a typed number ambiguous."""
        self.seed(2)
        self.backfill_all()
        self.mkrow("uuid-tomb", "Tombstoned", "2026-07-07T00:00:00+00:00",
                   "tombstoned", ordinal=1)
        found = [f for f in cscan.scan(self.home) if f["type"] == "ORDINAL-CLASH"]
        self.assertEqual(found, [])

    def test_ordinal_missing_fires_on_an_unnumbered_live_row(self):
        self.seed(2)
        self.backfill_all()
        self.mkrow("uuid-new", "Newcomer", "2026-09-09T00:00:00+00:00")
        found = [f for f in cscan.scan(self.home) if f["type"] == "ORDINAL-MISSING"]
        self.assertEqual(len(found), 1)
        self.assertIn("Newcomer", found[0]["detail"])

    def test_the_bleed_fix_line_is_runnable_as_printed(self):
        """It named prune-state-bindings.sh run under bash. The file is .ts
        and runs under bun, so as printed the fix could not be run at all."""
        src = open(os.path.join(_RESDIR, "conflict-scan.py")).read()
        # Assert on the COMMAND, not the bare filename: the surrounding comment
        # names the old broken path on purpose, to record what was wrong.
        self.assertNotIn("bash .claude/scripts/resurrection/prune-state-bindings.sh", src)
        self.assertIn("bun .claude/scripts/resurrection/prune-state-bindings.ts", src)
        self.assertTrue(os.path.exists(os.path.join(_RESDIR, "prune-state-bindings.ts")),
                        "the fix line must name a file that actually exists")
        self.assertFalse(os.path.exists(os.path.join(_RESDIR, "prune-state-bindings.sh")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
