#!/usr/bin/env python3
"""test_resurrection_enroll.py — the SessionStart enrollment gates.

Written for the WORKTREE GATE (Zee, 2026-08-25). A git worktree is a second
working copy of one repository. It copies the repo's tracked files, so it
inherits CLAUDE.md and memory/handoffs — which are two of the three markers the
enroll hook uses to decide "this is a project". Every worktree therefore looked
like a brand-new project and minted its own row.

MEASURED: rows 54 and 55, "R2P tab-a ledger" and "R2P tab-b contracts", were
created 6 seconds apart on 2026-08-19T20:43 by two sessions opening inside
R2P/.claude/worktrees/. Neither ever held a close, a knowledge fact or a window
record; the real work had been parked to the R2P row, exactly as Zee remembered.
Three more worktrees sat in that folder ready to repeat it.

The case that keeps this honest is the LOOKALIKE: a real project honestly named
`worktrees-explained` must still enrol. A substring test would refuse it, and
refusing a real project silently is worse than the clutter this gate removes.

Every test runs the SHIPPED hook as a subprocess against a throwaway registry
home, exactly as SessionStart invokes it. Nothing here touches the real ~/.acos.
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
HOOK = os.path.join(_RESDIR, "enroll-project.sh")
sys.path.insert(0, _RESDIR)
import registry_lib  # noqa: E402


class EnrollGateTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="enroll-test-")
        os.makedirs(registry_lib.registry_dir(self.home), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def mkdir_with(self, rel, marker="CLAUDE.md"):
        d = os.path.join(self.home, rel)
        os.makedirs(d, exist_ok=True)
        if marker == "CLAUDE.md":
            with open(os.path.join(d, "CLAUDE.md"), "w") as fh:
                fh.write("# project\n")
        elif marker == "handoffs":
            os.makedirs(os.path.join(d, "memory", "handoffs"), exist_ok=True)
        return d

    def enroll(self, cwd):
        """Run the hook the way SessionStart does: JSON on stdin."""
        env = dict(os.environ)
        env["ACOS_REGISTRY_HOME"] = self.home
        out = subprocess.run(
            ["/bin/bash", HOOK], input=json.dumps({"session_id": "s1", "cwd": cwd}),
            capture_output=True, text=True, timeout=60, env=env)
        return out

    def roots(self):
        """Enrolled roots, REALPATH-normalised on both sides of every compare.

        The row stores `root` as an abspath. On macOS /var is a symlink to
        /private/var, so a tempdir under /var enrols as /var/... while
        os.path.realpath answers /private/var/... — the same directory, two
        spellings. Normalising here compares directories, not strings."""
        return sorted(os.path.realpath(r["root"])
                      for r in registry_lib._iter_rows(self.home))

    def real(self, path):
        return os.path.realpath(path)

    # ------------------------------------------------------------ refusals

    def test_a_claude_worktree_is_not_enrolled(self):
        """The exact shape that minted rows 54 and 55."""
        d = self.mkdir_with(os.path.join("proj", ".claude", "worktrees", "tab-a"))
        out = self.enroll(d)
        self.assertEqual(out.returncode, 0, "the hook must never block a session")
        self.assertIn("worktree path — NOT enrolled", out.stderr)
        self.assertEqual(self.roots(), [])

    def test_a_git_worktree_is_not_enrolled(self):
        d = self.mkdir_with(os.path.join("proj", ".git", "worktrees", "wt1"))
        self.enroll(d)
        self.assertEqual(self.roots(), [])

    def test_a_worktree_carrying_memory_handoffs_is_not_enrolled(self):
        """A worktree inherits memory/handoffs too, not only CLAUDE.md."""
        d = self.mkdir_with(os.path.join("proj", ".claude", "worktrees", "tab-b"),
                            marker="handoffs")
        self.enroll(d)
        self.assertEqual(self.roots(), [])

    def test_a_worktree_nested_deeper_is_still_not_enrolled(self):
        d = self.mkdir_with(os.path.join("proj", ".claude", "worktrees", "tab-a", "sub"))
        self.enroll(d)
        self.assertEqual(self.roots(), [])

    # ------------------------------------------------------------ still enrols

    def test_a_real_project_is_still_enrolled(self):
        d = self.mkdir_with("real-project")
        self.enroll(d)
        self.assertEqual(self.roots(), [self.real(d)])

    def test_a_folder_honestly_named_worktrees_explained_is_enrolled(self):
        """The lookalike. A substring test would refuse a real project here,
        and silently losing a real project is worse than the clutter."""
        d = self.mkdir_with("worktrees-explained")
        self.enroll(d)
        self.assertEqual(self.roots(), [self.real(d)])

    def test_the_worktrees_container_itself_is_enrolled_if_it_is_a_project(self):
        """`.../worktrees` with nothing below it is not a worktree — it is the
        directory that HOLDS them. The gate needs a level beneath the segment."""
        d = self.mkdir_with(os.path.join("proj", "worktrees"))
        self.enroll(d)
        self.assertEqual(self.roots(), [self.real(d)])

    def test_a_project_named_worktrees_at_the_top_is_enrolled(self):
        d = self.mkdir_with("worktrees")
        self.enroll(d)
        self.assertEqual(self.roots(), [self.real(d)])

    # ------------------------------------------------------------ fail-open

    def test_the_hook_never_blocks_a_session(self):
        """Contract from the hook's own header: fail-open, always exit 0."""
        for cwd in (os.path.join(self.home, "does-not-exist"),
                    self.mkdir_with(os.path.join("p", ".claude", "worktrees", "w")),
                    self.mkdir_with("ok")):
            self.assertEqual(self.enroll(cwd).returncode, 0, cwd)

    def test_a_folder_with_no_marker_is_not_enrolled(self):
        """Unchanged behaviour — the marker gate still does its own job."""
        d = os.path.join(self.home, "bare")
        os.makedirs(d, exist_ok=True)
        self.enroll(d)
        self.assertEqual(self.roots(), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
