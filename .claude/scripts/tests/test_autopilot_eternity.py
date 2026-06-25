#!/usr/bin/env python3
"""test_autopilot_eternity.py — stdlib unittest for eternity-protocol in-flight detection
(_autopilot_eternity.py), focused on the 2026-06-24 freeze-early arming marker and its
AGE-GC self-expiry (the autonomy guarantee: a crashed/aborted fire can never freeze the
autopilot forever).

Both governance hooks (Oracle, autopilot Stop handler) subordinate on
is_eternity_protocol_active(); this module is its single source of truth, so proving the
detection here proves both hooks behave correctly.

DAEMON_STATE and project_session_ids are monkeypatched so the tests touch only a tmpdir and
a fixed session-id set — no real daemon state, no creds.
"""

import importlib.util
import os
import shutil
import sys
import tempfile
import time
import unittest


_THIS = os.path.dirname(os.path.abspath(__file__))
_SCR = os.path.abspath(os.path.join(_THIS, os.pardir))


def _load(modname, filename):
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(modname, os.path.join(_SCR, filename))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


et = _load("_autopilot_eternity", "_autopilot_eternity.py")

_SID = "11111111-2222-3333-4444-555555555555"
_FOREIGN_SID = "99999999-8888-7777-6666-555555555555"


class _EternityBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-eternity-test-")
        self._orig_state = et.DAEMON_STATE
        self._orig_psi = et.project_session_ids
        et.DAEMON_STATE = __import__("pathlib").Path(self.tmp)
        # Only _SID belongs to "this project"; _FOREIGN_SID never does.
        et.project_session_ids = lambda cwd: {_SID}

    def tearDown(self):
        et.DAEMON_STATE = self._orig_state
        et.project_session_ids = self._orig_psi
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _touch(self, name, *, age_seconds=0.0, content="x"):
        p = os.path.join(self.tmp, name)
        with open(p, "w") as f:
            f.write(content)
        if age_seconds:
            t = time.time() - age_seconds
            os.utime(p, (t, t))
        return p


class ArmingMarkerTest(_EternityBase):
    def test_no_markers_not_active(self):
        self.assertFalse(et.is_eternity_protocol_active("/cwd"))

    def test_fresh_arming_marker_is_active(self):
        self._touch(f"{et.ARMING_MARKER_PREFIX}{_SID}", age_seconds=30)
        self.assertTrue(et.is_eternity_protocol_active("/cwd"))
        sid, marker = et.detect_eternity_marker("/cwd")
        self.assertEqual(sid, _SID)
        self.assertTrue(marker.startswith(et.ARMING_MARKER_PREFIX))

    def test_stale_arming_marker_does_not_freeze(self):
        # THE autonomy guarantee: an arming marker older than the TTL stops counting, so a
        # crashed fire that left the marker behind cannot freeze the autopilot forever.
        self._touch(f"{et.ARMING_MARKER_PREFIX}{_SID}",
                    age_seconds=et.ARMING_MARKER_TTL_SECONDS + 60)
        self.assertFalse(et.is_eternity_protocol_active("/cwd"))
        self.assertEqual(et.detect_eternity_marker("/cwd"), (None, None))

    def test_ttl_boundary_still_live(self):
        # at exactly the TTL (<=), still considered live (no premature unfreeze)
        self._touch(f"{et.ARMING_MARKER_PREFIX}{_SID}",
                    age_seconds=et.ARMING_MARKER_TTL_SECONDS - 5)
        self.assertTrue(et.is_eternity_protocol_active("/cwd"))

    def test_foreign_sid_arming_marker_ignored(self):
        # a fresh arming marker for a session NOT in this project must not subordinate us
        self._touch(f"{et.ARMING_MARKER_PREFIX}{_FOREIGN_SID}", age_seconds=10)
        self.assertFalse(et.is_eternity_protocol_active("/cwd"))


class DaemonMarkerTtlExemptionTest(_EternityBase):
    def test_daemon_markers_ignore_ttl(self):
        # daemon-managed markers are NOT age-GC'd — even an "old" pending-resume still counts
        # (the daemon owns its lifecycle; only the in-repo arming marker self-expires).
        self._touch(f"pending-resume-{_SID}.txt", age_seconds=et.ARMING_MARKER_TTL_SECONDS + 600)
        self.assertTrue(et.is_eternity_protocol_active("/cwd"))

    def test_clear_requested_marker_active(self):
        self._touch(f".clear-requested-{_SID}", age_seconds=5)
        self.assertTrue(et.is_eternity_protocol_active("/cwd"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
