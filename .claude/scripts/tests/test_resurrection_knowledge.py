#!/usr/bin/env python3
"""test_resurrection_knowledge.py — stdlib unittest for the per-project
knowledge store (KB-A capture loop + KB-C staleness re-check, user brief
2026-08-04).

knowledge_lib.py carries its own --selftest for the library internals. This
module tests the part the selftest cannot reach: the CLOSE INTEGRATION, i.e.
that close-project.sh --learnings-file applies D4 (silent Kind 1 / asked
Kind 2 / 2-question cap) and D5a (evidence or no write) on a real close, and
that a failure in capture can never turn a good close into a failed one.

Everything runs under ACOS_REGISTRY_HOME / RESURRECTION_PROJECT_ROOT /
RESURRECTION_STATE_DIR overrides — the real registry, the real daemon state
and the real knowledge store are never touched.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

_THIS = os.path.dirname(os.path.abspath(__file__))
_RESDIR = os.path.abspath(os.path.join(_THIS, os.pardir, "resurrection"))
_CLOSE = os.path.join(_RESDIR, "close-project.sh")
sys.path.insert(0, _RESDIR)
import knowledge_lib  # noqa: E402


class CloseCaptureTest(unittest.TestCase):
    """KB-A through the real close script."""

    def setUp(self):
        self.sb = tempfile.mkdtemp(prefix="kb-a-")
        self.proj = os.path.join(self.sb, "proj")
        self.home = os.path.join(self.sb, "home")
        os.makedirs(os.path.join(self.proj, "data"))
        for i in range(5):
            with open(os.path.join(self.proj, "data", "f%d.txt" % i), "w") as fh:
                fh.write("x")
        with open(os.path.join(self.proj, "r.txt"), "w") as fh:
            fh.write("hi\n")
        subprocess.run(["git", "init", "-q"], cwd=self.proj, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.proj, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-qm", "init"], cwd=self.proj, check=True)
        self.intent = os.path.join(self.sb, "intent.md")
        with open(self.intent, "w") as fh:
            fh.write("next_action: Confirm the knowledge capture behaves\n"
                     "project: KB-A capture test\n"
                     "decisions: |\n  - Testing the capture loop.\n"
                     "traps: |\n  - None.\n"
                     "open_questions: |\n  - None.\n")

    def tearDown(self):
        shutil.rmtree(self.sb, ignore_errors=True)

    def _close(self, learnings=None, sid="aaaaaaa1-2222-3333-4444-555555555555"):
        args = ["bash", _CLOSE, "--intent-file", self.intent, "--session-id", sid]
        if learnings is not None:
            lp = os.path.join(self.sb, "learn-%s.json" % sid[:8])
            with open(lp, "w") as fh:
                json.dump(learnings, fh)
            args += ["--learnings-file", lp]
        env = dict(os.environ,
                   RESURRECTION_SKIP_CMUX="1",
                   ACOS_REGISTRY_HOME=self.home,
                   RESURRECTION_STATE_DIR=os.path.join(self.sb, "state"),
                   RESURRECTION_PROJECT_ROOT=self.proj)
        return subprocess.run(args, cwd=self.proj, env=env, capture_output=True, text=True)

    def _project_uuid(self):
        kdir = os.path.join(self.home, ".acos", "knowledge")
        entries = os.listdir(kdir)
        self.assertEqual(len(entries), 1, "expected one project store, got %r" % entries)
        return entries[0]

    def _sample(self):
        return [
            {"kind": "machine", "subject": "data folder", "claim": "data/ holds 5 files",
             "evidence": {"type": "command", "value": "ls data | wc -l"},
             "checks": [{"type": "file_count", "path": "data", "expect": 5}],
             "entities": ["data folder"]},
            {"kind": "machine", "subject": "readme", "claim": "r.txt exists at the project root",
             "evidence": {"type": "path", "value": "r.txt"},
             "checks": [{"type": "file_exists", "path": "r.txt"}]},
            {"kind": "machine", "subject": "broken", "claim": "this has no evidence at all"},
            {"kind": "ruling", "subject": "broker material",
             "claim": "never print LendSure on broker material",
             "evidence": {"type": "quote", "value": "Zee, 2026-08-03"}},
            {"kind": "ruling", "subject": "naming",
             "claim": "deal folders use the borrower name",
             "evidence": {"type": "quote", "value": "Zee, 2026-08-01"}},
            {"kind": "ruling", "subject": "third", "claim": "this one is past the cap",
             "evidence": {"type": "quote", "value": "Zee"}},
        ]

    def test_machine_facts_are_written_silently_and_rulings_are_not(self):
        out = self._close(self._sample())
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        facts = knowledge_lib.load_facts(self._project_uuid(), self.home)
        claims = {f["claim"] for f in facts}
        self.assertIn("data/ holds 5 files", claims)
        self.assertIn("r.txt exists at the project root", claims)
        self.assertTrue(all(f["kind"] == "machine" for f in facts),
                        "a ruling must never reach the store without an answer")
        for ruling in ("never print LendSure on broker material",
                       "deal folders use the borrower name",
                       "this one is past the cap"):
            self.assertNotIn(ruling, claims)

    def test_a_fact_with_no_evidence_is_refused_and_said_out_loud(self):
        out = self._close(self._sample())
        self.assertIn("REFUSED (no write)", out.stdout)
        claims = {f["claim"] for f in knowledge_lib.load_facts(self._project_uuid(), self.home)}
        self.assertNotIn("this has no evidence at all", claims)

    def test_at_most_two_rulings_are_raised_and_the_overflow_is_reported(self):
        out = self._close(self._sample())
        self.assertIn("ASK ZEE (2, cap 2)", out.stdout)
        self.assertIn("DROPPED:", out.stdout)
        self.assertIn("past the 2-question cap", out.stdout)

    def test_provenance_records_which_window_learned_it(self):
        self._close(self._sample())
        facts = knowledge_lib.load_facts(self._project_uuid(), self.home)
        for f in facts:
            self.assertIn("session", f["provenance"])
            self.assertIn("close_slug", f["provenance"])

    def test_capture_never_breaks_a_close(self):
        """A malformed learnings file must degrade to a note, not a failed close."""
        bad = os.path.join(self.sb, "bad.json")
        with open(bad, "w") as fh:
            fh.write("{not json at all")
        env = dict(os.environ, RESURRECTION_SKIP_CMUX="1", ACOS_REGISTRY_HOME=self.home,
                   RESURRECTION_STATE_DIR=os.path.join(self.sb, "state"),
                   RESURRECTION_PROJECT_ROOT=self.proj)
        out = subprocess.run(["bash", _CLOSE, "--intent-file", self.intent,
                              "--session-id", "bbbbbbb1-2222-3333-4444-555555555555",
                              "--learnings-file", bad],
                             cwd=self.proj, env=env, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, "capture failure must not fail the close")
        self.assertIn("step 8b knowledge: SKIPPED", out.stdout)
        self.assertIn("SAFE TO CLOSE THIS TAB", out.stdout)

    def test_close_without_the_flag_behaves_exactly_as_before(self):
        out = self._close(None)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("no --learnings-file given", out.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.home, ".acos", "knowledge")))


class StalenessRecheckTest(unittest.TestCase):
    """KB-C: a stored count/path claim is re-verified, and drift is named."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="kb-c-home-")
        self.root = tempfile.mkdtemp(prefix="kb-c-root-")
        self.uuid = "dddddddd-1111-4111-8111-dddddddddddd"
        os.makedirs(os.path.join(self.root, "data"))
        for i in range(5):
            with open(os.path.join(self.root, "data", "f%d.txt" % i), "w") as fh:
                fh.write("x")
        knowledge_lib.write_learnings(self.uuid, [
            {"kind": "machine", "subject": "data folder", "claim": "data/ holds 5 files",
             "evidence": {"type": "command", "value": "ls data | wc -l"},
             "checks": [{"type": "file_count", "path": "data", "expect": 5}]},
        ], home=self.home)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.root, ignore_errors=True)

    def test_a_true_claim_reads_ok(self):
        found = knowledge_lib.recheck(self.uuid, self.root, self.home)
        self.assertEqual([f["status"] for f in found], ["ok"])

    def test_a_claim_the_world_moved_past_is_flagged_with_both_numbers(self):
        """The exact failure the audit measured: a stored count read confidently
        while the live count had moved on (1,305 stored vs 1,594 live)."""
        for i in range(5, 8):
            with open(os.path.join(self.root, "data", "f%d.txt" % i), "w") as fh:
                fh.write("x")
        found = knowledge_lib.recheck(self.uuid, self.root, self.home)
        self.assertEqual(found[0]["status"], "DRIFTED")
        self.assertIn("8 files", found[0]["detail"])
        self.assertIn("claim says 5", found[0]["detail"])

    def test_a_missing_path_is_drift_not_a_crash(self):
        shutil.rmtree(os.path.join(self.root, "data"))
        found = knowledge_lib.recheck(self.uuid, self.root, self.home)
        self.assertEqual(found[0]["status"], "DRIFTED")
        self.assertIn("MISSING DIR", found[0]["detail"])

    def test_a_stored_check_can_never_be_a_shell_command(self):
        """The store must not become an execution channel: a wrong or hostile
        auto-written fact would otherwise run code at every resurrect."""
        with self.assertRaises(ValueError):
            knowledge_lib.validate_check({"type": "shell", "cmd": "rm -rf /"})
        rep = knowledge_lib.write_learnings(self.uuid, [
            {"kind": "machine", "subject": "evil", "claim": "runs a command",
             "evidence": {"type": "path", "value": "/tmp/x"},
             "checks": [{"type": "shell", "cmd": "rm -rf /"}]}], home=self.home)
        self.assertEqual(len(rep["written"]), 0)
        self.assertEqual(len(rep["refused"]), 1)


class SupersedeRuleTest(unittest.TestCase):
    """A subject that holds MANY facts must not collapse to its last one.

    Regression guard, measured on the real corpus: superseding on subject alone
    turned 25 backfilled facts into 3 live ones, because 'decisions' and
    'traps' each hold many independent claims. Only a SINGLE-VALUED subject —
    'the count is N', 'the branch is X' — may be replaced by a newer claim.
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="kb-sv-")
        self.uuid = "ffffffff-1111-4111-8111-ffffffffffff"

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def _add(self, subject, claim, single=False):
        return knowledge_lib.write_learnings(self.uuid, [
            {"kind": "machine", "subject": subject, "claim": claim,
             "evidence": {"type": "path", "value": "/tmp/x"},
             "single_valued": single}], home=self.home)

    def test_many_traps_all_stay_live(self):
        for i in range(5):
            self._add("traps", "trap number %d" % i)
        self.assertEqual(len(knowledge_lib.live_facts(self.uuid, self.home)), 5)

    def test_a_single_valued_subject_keeps_only_its_newest_claim(self):
        self._add("file count", "holds 5 files", single=True)
        self._add("file count", "holds 8 files", single=True)
        live = knowledge_lib.live_facts(self.uuid, self.home)
        self.assertEqual([f["claim"] for f in live], ["holds 8 files"])
        self.assertEqual(len(knowledge_lib.load_facts(self.uuid, self.home)), 2,
                         "the superseded row must stay on disk (D5b)")

    def test_single_valued_must_be_a_bool(self):
        rep = knowledge_lib.write_learnings(self.uuid, [
            {"kind": "machine", "subject": "s", "claim": "c",
             "evidence": {"type": "path", "value": "/tmp/x"},
             "single_valued": "yes"}], home=self.home)
        self.assertEqual(len(rep["refused"]), 1)


class BackfillTest(unittest.TestCase):
    """KB-D: seed a store from bundles the project already has."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "backfill_knowledge", os.path.join(_RESDIR, "backfill-knowledge.py"))
        cls.bf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.bf)

    def test_intent_sections_are_split_into_their_items(self):
        text = ("next_action: do a thing\n"
                "decisions: |\n"
                "  - first decision that is long enough\n"
                "  - second decision, which wraps\n"
                "    onto another line entirely\n"
                "traps: |\n"
                "  - a trap worth remembering\n")
        got = self.bf.split_intent_sections(text)
        self.assertEqual(got["decisions"][0], "first decision that is long enough")
        self.assertEqual(got["decisions"][1],
                         "second decision, which wraps onto another line entirely",
                         "a wrapped decision must not be cut in half")
        self.assertEqual(got["traps"], ["a trap worth remembering"])

    def test_an_empty_intent_core_yields_nothing_rather_than_crashing(self):
        self.assertEqual(self.bf.split_intent_sections(""), {})
        self.assertEqual(self.bf.split_intent_sections(None), {})

    def test_every_backfilled_fact_carries_its_source(self):
        sb = tempfile.mkdtemp(prefix="kb-d-")
        try:
            bundle = os.path.join(sb, "memory", "handoffs", "closed",
                                  "2026-01-01-Demo-close")
            os.makedirs(bundle)
            with open(os.path.join(bundle, "handoff.yaml"), "w") as fh:
                fh.write("slug: 2026-01-01-Demo-close\n"
                         "git_state: branch=main head=abc dirty_count=0\n"
                         "intent_core: |\n"
                         "  traps: |\n"
                         "    - the trap that must be remembered\n")
            facts = self.bf.facts_from_bundle(bundle, sb)
            self.assertTrue(facts)
            for f in facts:
                self.assertTrue(f["evidence"]["value"], "evidence or no write (D5a)")
                self.assertEqual(f["kind"], "machine")
                self.assertIn("backfill", f["tags"])
            trap = [f for f in facts if f["subject"] == "traps"][0]
            self.assertEqual(trap["claim"], "the trap that must be remembered")
            self.assertEqual(trap["checks"][0]["type"], "path_contains",
                             "a backfilled fact must go stale if its source changes")
            self.assertTrue(any(f["subject"] == "git" and "main" in f["claim"]
                                for f in facts))
        finally:
            shutil.rmtree(sb, ignore_errors=True)

    def test_short_fragments_are_not_promoted_to_facts(self):
        sb = tempfile.mkdtemp(prefix="kb-d2-")
        try:
            bundle = os.path.join(sb, "memory", "handoffs", "closed",
                                  "2026-01-01-Demo-close")
            os.makedirs(bundle)
            with open(os.path.join(bundle, "handoff.yaml"), "w") as fh:
                fh.write("slug: 2026-01-01-Demo-close\n"
                         "intent_core: |\n  traps: |\n    - none\n    - n/a\n")
            facts = [f for f in self.bf.facts_from_bundle(bundle, sb)
                     if f["subject"] == "traps"]
            self.assertEqual(facts, [], "'none' and 'n/a' are not knowledge")
        finally:
            shutil.rmtree(sb, ignore_errors=True)


class CrossProjectReachTest(unittest.TestCase):
    """KB-E: a trap learned in one project surfaces in another that shares the
    same tool or file — and does NOT surface on a word they merely both used."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="kb-e-")
        self.a = "aaaa0000-1111-4111-8111-aaaaaaaaaaaa"
        self.b = "bbbb0000-1111-4111-8111-bbbbbbbbbbbb"

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def _add(self, project, subject, claim, entities):
        knowledge_lib.write_learnings(project, [
            {"kind": "machine", "subject": subject, "claim": claim,
             "evidence": {"type": "quote", "value": "somewhere"},
             "entities": entities}], home=self.home)

    def test_a_trap_about_a_shared_tool_travels(self):
        self._add(self.a, "traps", "WeasyPrint drops the last row of a table", ["WeasyPrint"])
        self._add(self.b, "decisions", "we render invoices with WeasyPrint", ["WeasyPrint"])
        hits = knowledge_lib.cross_project_hits(self.b, home=self.home)
        self.assertEqual(len(hits), 1)
        self.assertIn("WeasyPrint", hits[0]["shared"])
        self.assertEqual(hits[0]["project_uuid"], self.a)

    def test_a_project_never_teaches_itself(self):
        self._add(self.a, "traps", "a trap about WeasyPrint", ["WeasyPrint"])
        self._add(self.a, "decisions", "we use WeasyPrint", ["WeasyPrint"])
        self.assertEqual(knowledge_lib.cross_project_hits(self.a, home=self.home), [])

    def test_projects_with_nothing_in_common_are_not_linked(self):
        self._add(self.a, "traps", "a trap about WeasyPrint", ["WeasyPrint"])
        self._add(self.b, "decisions", "we use LanceDB", ["LanceDB"])
        self.assertEqual(knowledge_lib.cross_project_hits(self.b, home=self.home), [])

    def test_only_traps_travel_by_default(self):
        """A decision is usually project-local; a trap is the thing most worth
        not hitting twice."""
        self._add(self.a, "decisions", "we chose WeasyPrint for invoices", ["WeasyPrint"])
        self._add(self.b, "decisions", "we also use WeasyPrint", ["WeasyPrint"])
        self.assertEqual(knowledge_lib.cross_project_hits(self.b, home=self.home), [])
        widened = knowledge_lib.cross_project_hits(self.b, home=self.home,
                                                   subjects=("decisions",))
        self.assertEqual(len(widened), 1)


class EntityExtractionTest(unittest.TestCase):
    """KB-E only reaches as far as the things it can name."""

    def test_it_finds_tools_files_and_identifier_shaped_ids(self):
        got = knowledge_lib.extract_entities(
            "WeasyPrint chokes; see github-repo-guard.ts and SLICE-RES-13")
        self.assertIn("WeasyPrint", got)
        self.assertIn("github-repo-guard.ts", got)
        self.assertIn("SLICE-RES-13", got)

    def test_backticked_spans_are_taken_whole(self):
        self.assertIn("git push --force",
                      knowledge_lib.extract_entities("never run `git push --force` here"))

    def test_shouted_english_is_not_mistaken_for_an_acronym(self):
        """The handoff corpus shouts for emphasis. Matching those linked
        unrelated projects on nothing at all."""
        got = knowledge_lib.extract_entities(
            "NEVER do this. BOTH are the SAME. This is GLOBAL and REAL.")
        self.assertEqual(got, [], "got %r" % got)

    def test_ordinary_prose_yields_nothing(self):
        self.assertEqual(knowledge_lib.extract_entities(
            "we talked about it and agreed to move on"), [])


class DigestWatermarkTest(unittest.TestCase):
    """KB-B / D5d: the 'learned since you were last here' list must actually
    reach Zee.

    Regression guard. The first build advanced the watermark at CLOSE time, so
    every fact was marked seen before he ever saw it and the digest showed
    'nothing new' forever — the same silent-death the old mining loop suffered
    (.last-mined unmoved for 18 days). Only a REOPEN may advance it.
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="kb-b-")
        self.uuid = "eeeeeeee-1111-4111-8111-eeeeeeeeeeee"
        knowledge_lib.write_learnings(self.uuid, [
            {"kind": "machine", "subject": "s1", "claim": "first thing learned",
             "evidence": {"type": "path", "value": "/tmp/a"}},
            {"kind": "machine", "subject": "s2", "claim": "second thing learned",
             "evidence": {"type": "path", "value": "/tmp/b"}},
        ], home=self.home)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def test_a_close_does_not_mark_facts_as_seen(self):
        self.assertIsNone(knowledge_lib.get_last_seen(self.uuid, self.home),
                          "capture must not advance the watermark")
        self.assertEqual(len(knowledge_lib.digest(self.uuid, home=self.home)), 2)

    def test_the_first_reopen_shows_everything_then_the_next_shows_nothing_new(self):
        first = knowledge_lib.digest(self.uuid, home=self.home)
        self.assertEqual(len(first), 2)
        knowledge_lib.set_last_seen(self.uuid, home=self.home)          # the reopen
        self.assertEqual(knowledge_lib.digest(self.uuid, home=self.home), [])

    def test_facts_learned_after_a_reopen_show_up_on_the_next_one(self):
        knowledge_lib.set_last_seen(self.uuid, home=self.home)
        knowledge_lib.write_learnings(self.uuid, [
            {"kind": "machine", "subject": "s3", "claim": "learned later",
             "evidence": {"type": "path", "value": "/tmp/c"}}], home=self.home)
        later = knowledge_lib.digest(self.uuid, home=self.home)
        self.assertEqual([f["claim"] for f in later], ["learned later"])

    def test_a_struck_fact_disappears_from_the_view_but_not_from_disk(self):
        target = knowledge_lib.live_facts(self.uuid, self.home)[0]["id"]
        knowledge_lib.strike_fact(self.uuid, target, home=self.home)
        live = {f["id"] for f in knowledge_lib.live_facts(self.uuid, self.home)}
        on_disk = {f["id"] for f in knowledge_lib.load_facts(self.uuid, self.home)}
        self.assertNotIn(target, live)
        self.assertIn(target, on_disk)


if __name__ == "__main__":
    unittest.main(verbosity=2)
