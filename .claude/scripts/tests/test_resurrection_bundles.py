#!/usr/bin/env python3
"""test_resurrection_bundles.py — deleting a row archives its handoffs.

Zee's ruling 2026-08-24, in his words: "when a project is deleted, treat it as
/acos-complete". That skill marks handoffs `status: completed` and moves them to
memory/handoffs/archive/. A ROW's history is a different set — the CLOSE BUNDLES
under memory/handoffs/closed/ — so those land in archive/closed/.

The cases that matter:

  * a proven-owned bundle is stamped completed and moved
  * a bundle owned only by a GUESS is left alone and reported — moving a
    project's history on a resemblance is the failure this prevents
  * `.resume.md` files are never relabelled; the eternity protocol needs them
  * another row's bundle in the same folder is never touched — 22 rows share
    the ACOS 3.0 folder on this machine, so this is the live risk
  * restore puts the bundles back, and does NOT revert the completed stamp
  * purge keeps both the archived bundles and the knowledge facts

Plus the stamper that makes ownership provable in the first place, including
its second rung: a bundle whose folder has exactly ONE row is owned by that row
even when its display name is shared with a row somewhere else.

Fixture registry under a throwaway home; the real ~/.acos is never touched.
"""

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
import bundles_lib  # noqa: E402
import knowledge_lib  # noqa: E402
import ordinal_lib  # noqa: E402
import registry_lib  # noqa: E402


def _load(stem, filename):
    spec = importlib.util.spec_from_file_location(stem, os.path.join(_RESDIR, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


manage = _load("manage_ordinals", "manage-ordinals.py")
stamper = _load("stamp_bundle_owners", "stamp-bundle-owners.py")

HANDOFF = """timestamp: 2026-08-01T00:00:00+00:00
status: active
session_summary: fixture close
next_action: do the next thing
"""


class BundleTestBase(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="bundle-test-")
        os.makedirs(registry_lib.registry_dir(self.home), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def mkrow(self, uuid, name, root_name=None):
        root = os.path.join(self.home, "roots", root_name or name)
        os.makedirs(root, exist_ok=True)
        return registry_lib.upsert_row(
            {"project_uuid": uuid, "root": root, "workspace_name": name,
             "status": "parked"}, self.home)

    def closed_dir(self, row):
        return os.path.join(row["root"], "memory", "handoffs", "closed")

    def mkbundle(self, row, slug, owner_uuid=None, resume=True):
        """A close bundle. owner_uuid=None leaves it unstamped."""
        d = os.path.join(self.closed_dir(row), slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "handoff.yaml"), "w") as fh:
            fh.write(HANDOFF)
        with open(os.path.join(d, "%s.reentry.md" % slug), "w") as fh:
            fh.write("# Reentry\nNEXT ACTION: do the next thing\n")
        if resume:
            with open(os.path.join(d, "%s.resume.md" % slug), "w") as fh:
                fh.write("Read memory/handoffs/closed/%s/handoff.yaml\n" % slug)
        if owner_uuid:
            with open(os.path.join(d, bundles_lib.OWNER_MARKER), "w") as fh:
                fh.write(owner_uuid + "\n")
        return d

    def archived(self, row, slug):
        return os.path.join(manage.archived_closed_dir(row["root"]), slug)

    def run_verb(self, argv):
        return manage.main(list(argv) + ["--home", self.home])


# ------------------------------------------------------ delete archives them

class DeleteArchivesBundlesTest(BundleTestBase):
    def test_a_proven_bundle_is_stamped_completed_and_moved(self):
        row = self.mkrow("u-a", "Alpha")
        b = self.mkbundle(row, "2026-08-01-Alpha-close", owner_uuid="u-a")
        self.assertEqual(
            self.run_verb(["delete", str(row["pick_ordinal"]),
                           "--confirm-name", "Alpha", "--apply", "--no-cmux"]), 0)
        self.assertFalse(os.path.isdir(b), "left memory/handoffs/closed/")
        dst = self.archived(row, "2026-08-01-Alpha-close")
        self.assertTrue(os.path.isdir(dst), "landed in archive/closed/")
        text = open(os.path.join(dst, "handoff.yaml")).read()
        self.assertIn("status: completed", text)
        self.assertNotIn("status: active", text)

    def test_resume_siblings_are_moved_with_the_bundle_but_not_relabelled(self):
        """/acos-complete protects `.resume.md` by name; so does this."""
        row = self.mkrow("u-a", "Alpha")
        self.mkbundle(row, "2026-08-01-Alpha-close", owner_uuid="u-a")
        self.run_verb(["delete", str(row["pick_ordinal"]),
                       "--confirm-name", "Alpha", "--apply", "--no-cmux"])
        dst = self.archived(row, "2026-08-01-Alpha-close")
        resume = os.path.join(dst, "2026-08-01-Alpha-close.resume.md")
        self.assertTrue(os.path.exists(resume))
        self.assertNotIn("status: completed", open(resume).read())

    def test_a_guessed_bundle_is_left_alone(self):
        """Moving a project's history on a resemblance is the real harm here."""
        row = self.mkrow("u-a", "Alpha")
        b = self.mkbundle(row, "2026-08-01-Alpha-close")      # NO owner marker
        self.assertEqual(
            self.run_verb(["delete", str(row["pick_ordinal"]),
                           "--confirm-name", "Alpha", "--apply", "--no-cmux"]), 0)
        self.assertTrue(os.path.isdir(b), "an unproven bundle never moves")
        self.assertIn("status: active", open(os.path.join(b, "handoff.yaml")).read())

    def test_another_rows_bundle_in_the_same_folder_is_untouched(self):
        """22 rows share the ACOS 3.0 folder on this machine. This is the risk."""
        a = self.mkrow("u-a", "Alpha", root_name="shared")
        b = self.mkrow("u-b", "Bravo", root_name="shared")
        mine = self.mkbundle(a, "2026-08-01-Alpha-close", owner_uuid="u-a")
        theirs = self.mkbundle(b, "2026-08-01-Bravo-close", owner_uuid="u-b")
        self.run_verb(["delete", str(a["pick_ordinal"]),
                       "--confirm-name", "Alpha", "--apply", "--no-cmux"])
        self.assertFalse(os.path.isdir(mine))
        self.assertTrue(os.path.isdir(theirs), "Bravo's history stayed put")

    def test_the_receipt_names_the_rows_real_destination(self):
        """Regression. `dst` held the row's trash path, then the bundle loop
        reassigned it, so the receipt printed a BUNDLE path on the "row moved
        to" line — a receipt that lied about where the row went."""
        import contextlib, io
        row = self.mkrow("u-a", "Alpha")
        self.mkbundle(row, "2026-08-01-Alpha-close", owner_uuid="u-a")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.run_verb(["delete", str(row["pick_ordinal"]),
                           "--confirm-name", "Alpha", "--apply", "--no-cmux"])
        line = [l for l in buf.getvalue().split("\n") if "row moved to" in l][0]
        self.assertIn(manage.deleted_row_path("u-a", self.home), line)
        self.assertNotIn("archive", line)
        self.assertTrue(os.path.exists(manage.deleted_row_path("u-a", self.home)))

    def test_a_row_with_no_bundles_deletes_cleanly(self):
        row = self.mkrow("u-a", "Alpha")
        self.assertEqual(
            self.run_verb(["delete", str(row["pick_ordinal"]),
                           "--confirm-name", "Alpha", "--apply", "--no-cmux"]), 0)
        self.assertIsNone(registry_lib.load_row("u-a", self.home))


# ------------------------------------------------------------ restore + purge

class RestoreAndPurgeBundlesTest(BundleTestBase):
    def _delete_alpha(self):
        row = self.mkrow("u-a", "Alpha")
        self.mkbundle(row, "2026-08-01-Alpha-close", owner_uuid="u-a")
        self.run_verb(["delete", str(row["pick_ordinal"]),
                       "--confirm-name", "Alpha", "--apply", "--no-cmux"])
        return row

    def test_restore_moves_the_bundles_back(self):
        row = self._delete_alpha()
        self.assertEqual(self.run_verb(["restore", "u-a", "--apply"]), 0)
        back = os.path.join(self.closed_dir(row), "2026-08-01-Alpha-close")
        self.assertTrue(os.path.isdir(back))
        self.assertFalse(os.path.isdir(self.archived(row, "2026-08-01-Alpha-close")))

    def test_restore_does_not_revert_the_completed_stamp(self):
        """The close really did happen. Archiving is what gets undone."""
        row = self._delete_alpha()
        self.run_verb(["restore", "u-a", "--apply"])
        text = open(os.path.join(self.closed_dir(row),
                                 "2026-08-01-Alpha-close", "handoff.yaml")).read()
        self.assertIn("status: completed", text)

    def test_purge_keeps_the_archived_bundles_and_the_facts(self):
        row = self._delete_alpha()
        knowledge_lib.append_fact(
            "u-a", {"kind": "machine", "subject": "traps", "claim": "must outlive purge",
                    "evidence": {"type": "command", "value": "echo x"}}, home=self.home)
        self.assertEqual(
            self.run_verb(["purge", "u-a", "--confirm-name", "Alpha", "--apply"]), 0)
        self.assertTrue(os.path.isdir(self.archived(row, "2026-08-01-Alpha-close")),
                        "purging a ROW does not erase the project's history")
        self.assertEqual(len(knowledge_lib.load_facts("u-a", self.home)), 1)

    def test_the_manifest_records_what_moved(self):
        self._delete_alpha()
        path = manage.deleted_bundles_manifest("u-a", self.home)
        self.assertTrue(os.path.exists(path))
        entries = json.load(open(path))["bundles"]
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["from"].endswith("2026-08-01-Alpha-close"))

    def test_restore_survives_a_missing_manifest(self):
        """A restore that refused over a manifest would strand the row itself."""
        self._delete_alpha()
        os.unlink(manage.deleted_bundles_manifest("u-a", self.home))
        self.assertEqual(self.run_verb(["restore", "u-a", "--apply"]), 0)
        self.assertIsNotNone(registry_lib.load_row("u-a", self.home))


# ----------------------------------------------------------------- the stamper

class StamperTest(BundleTestBase):
    def test_a_sole_claimant_is_stamped(self):
        row = self.mkrow("u-a", "Alpha")
        b = self.mkbundle(row, "2026-08-01-Alpha-close")
        stamper.main(["--home", self.home, "--apply"])
        marker = os.path.join(b, bundles_lib.OWNER_MARKER)
        self.assertTrue(os.path.exists(marker))
        self.assertEqual(open(marker).read().strip(), "u-a")

    def test_rung_two_settles_a_shared_name_at_a_sole_folder(self):
        """The live case: two rows both named `Website-builder`, at DIFFERENT
        folders. The name rung refuses. Location is a fact about the file, so
        the row that owns the folder owns the bundle."""
        far = self.mkrow("u-far", "Website-builder", root_name="far")
        near = self.mkrow("u-near", "Website-builder", root_name="near")
        b = self.mkbundle(near, "2026-08-01-Website-builder-close")
        stamper.main(["--home", self.home, "--apply"])
        marker = os.path.join(b, bundles_lib.OWNER_MARKER)
        self.assertTrue(os.path.exists(marker))
        self.assertEqual(open(marker).read().strip(), "u-near")
        self.assertNotEqual(open(marker).read().strip(), far["project_uuid"])

    def test_two_rows_at_one_folder_are_left_alone(self):
        a = self.mkrow("u-a", "Same", root_name="shared")
        self.mkrow("u-b", "Same", root_name="shared")
        b = self.mkbundle(a, "2026-08-01-Same-close")
        stamper.main(["--home", self.home, "--apply"])
        self.assertFalse(os.path.exists(os.path.join(b, bundles_lib.OWNER_MARKER)),
                         "neither rung can split two rows at one folder")

    def test_an_existing_marker_is_never_overwritten(self):
        row = self.mkrow("u-a", "Alpha")
        b = self.mkbundle(row, "2026-08-01-Alpha-close", owner_uuid="u-other")
        stamper.main(["--home", self.home, "--apply"])
        self.assertEqual(
            open(os.path.join(b, bundles_lib.OWNER_MARKER)).read().strip(), "u-other")

    def test_the_stamper_never_moves_or_edits_a_bundle(self):
        row = self.mkrow("u-a", "Alpha")
        b = self.mkbundle(row, "2026-08-01-Alpha-close")
        before = sorted(os.listdir(b))
        text = open(os.path.join(b, "handoff.yaml")).read()
        stamper.main(["--home", self.home, "--apply"])
        self.assertTrue(os.path.isdir(b))
        self.assertEqual(sorted(n for n in os.listdir(b)
                                if n != bundles_lib.OWNER_MARKER), before)
        self.assertEqual(open(os.path.join(b, "handoff.yaml")).read(), text)

    def test_a_dry_run_writes_nothing(self):
        row = self.mkrow("u-a", "Alpha")
        b = self.mkbundle(row, "2026-08-01-Alpha-close")
        stamper.main(["--home", self.home])
        self.assertFalse(os.path.exists(os.path.join(b, bundles_lib.OWNER_MARKER)))


if __name__ == "__main__":
    unittest.main(verbosity=1)
