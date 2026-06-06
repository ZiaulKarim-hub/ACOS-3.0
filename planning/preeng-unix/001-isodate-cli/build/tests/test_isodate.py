"""Tests for the isodate CLI components.

Layout note: the auto_check commands set PYTHONPATH to build/tests, so this
file is importable as `test_isodate`. The module under test (`isodate.py`)
lives one directory up in build/, so we add build/ to sys.path here.
"""

import os
import sys
import subprocess
import unittest
import datetime

BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ISODATE_PY = os.path.join(BUILD_DIR, "isodate.py")
sys.path.insert(0, BUILD_DIR)

import isodate  # noqa: E402  (import after sys.path tweak, by design)


# ---------------------------------------------------------------------------
# C-001 — Clock provider
# ---------------------------------------------------------------------------
class ClockTests(unittest.TestCase):
    def test_fixed_injection_returns_exact_value(self):
        fixed = datetime.datetime(2020, 1, 2, 3, 4, 5)
        self.assertEqual(isodate.now(fixed=fixed), fixed)

    def test_fixed_injection_overrides_utc_flag(self):
        fixed = datetime.datetime(2020, 1, 2, 3, 4, 5)
        self.assertEqual(isodate.now(utc=True, fixed=fixed), fixed)

    def test_utc_true_returns_tz_aware_utc(self):
        result = isodate.now(utc=True)
        self.assertIsNotNone(result.tzinfo)
        self.assertEqual(result.utcoffset(), datetime.timedelta(0))

    def test_local_now_is_naive_datetime(self):
        result = isodate.now(utc=False)
        self.assertIsInstance(result, datetime.datetime)
        self.assertIsNone(result.tzinfo)


# ---------------------------------------------------------------------------
# C-002 — Date/time formatter
# ---------------------------------------------------------------------------
class FormatterTests(unittest.TestCase):
    def setUp(self):
        self.dt = datetime.datetime(2026, 6, 5, 14, 3, 9)

    def test_date_only(self):
        self.assertEqual(isodate.format_line(self.dt, False), "2026-06-05")

    def test_date_and_time(self):
        self.assertEqual(isodate.format_line(self.dt, True), "2026-06-05 14:03:09")

    def test_deterministic(self):
        first = isodate.format_line(self.dt, True)
        second = isodate.format_line(self.dt, True)
        self.assertEqual(first, second)

    def test_zero_padding(self):
        dt = datetime.datetime(2026, 1, 2, 3, 4, 5)
        self.assertEqual(isodate.format_line(dt, False), "2026-01-02")
        self.assertEqual(isodate.format_line(dt, True), "2026-01-02 03:04:05")


# ---------------------------------------------------------------------------
# C-003 — Argument parser
# ---------------------------------------------------------------------------
class ParserTests(unittest.TestCase):
    def test_utc_flag(self):
        flags = isodate.parse_args(["--utc"])
        self.assertTrue(flags.utc)
        self.assertFalse(flags.time)

    def test_time_flag(self):
        flags = isodate.parse_args(["--time"])
        self.assertTrue(flags.time)
        self.assertFalse(flags.utc)

    def test_no_flags(self):
        flags = isodate.parse_args([])
        self.assertFalse(flags.utc)
        self.assertFalse(flags.time)

    def test_composed_flags(self):
        flags = isodate.parse_args(["--utc", "--time"])
        self.assertTrue(flags.utc)
        self.assertTrue(flags.time)

    def test_unknown_flag_exits_nonzero(self):
        with self.assertRaises(SystemExit) as cm:
            isodate.parse_args(["--bogus"])
        self.assertNotEqual(cm.exception.code, 0)


# ---------------------------------------------------------------------------
# End-to-end (C-000) — Integrator's responsibility. These exercise the
# assembled CLI (root product = C-003 -> C-001 -> C-002 -> stdout/exit code),
# both via in-process main() and as a real subprocess. They cover every
# acceptance criterion of the root contract.
# ---------------------------------------------------------------------------
def _run_cli(args, env=None):
    """Run isodate.py as a real subprocess and return (rc, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, ISODATE_PY, *args],
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


class EndToEndTests(unittest.TestCase):
    # --- in-process main() wiring -----------------------------------------
    def test_default_run_prints_date(self):
        """No-flag run: exactly one YYYY-MM-DD line, exit 0."""
        import io
        import contextlib

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = isodate.main([])
        out = buf.getvalue()
        self.assertEqual(code or 0, 0)
        self.assertEqual(len(out.splitlines()), 1)
        # parses as a date (shape YYYY-MM-DD)
        datetime.datetime.strptime(out.strip(), "%Y-%m-%d")

    def test_time_flag_appends_hms(self):
        """--time appends ' HH:MM:SS' (local), exit 0."""
        import io
        import contextlib

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = isodate.main(["--time"])
        out = buf.getvalue().strip()
        self.assertEqual(code or 0, 0)
        datetime.datetime.strptime(out, "%Y-%m-%d %H:%M:%S")

    def test_utc_path_prints_date(self):
        """--utc path runs the UTC clock branch, still a date line, exit 0."""
        import io
        import contextlib

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = isodate.main(["--utc"])
        out = buf.getvalue().strip()
        self.assertEqual(code or 0, 0)
        datetime.datetime.strptime(out, "%Y-%m-%d")

    def test_utc_time_composition_prints_datetime(self):
        """--utc --time composes both flags into a UTC datetime line, exit 0."""
        import io
        import contextlib

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = isodate.main(["--utc", "--time"])
        out = buf.getvalue().strip()
        self.assertEqual(code or 0, 0)
        datetime.datetime.strptime(out, "%Y-%m-%d %H:%M:%S")

    def test_bad_flag_exits_nonzero(self):
        """Bad flag: argparse SystemExit propagates with a non-zero code."""
        with self.assertRaises(SystemExit) as cm:
            isodate.main(["--bogus"])
        self.assertNotEqual(cm.exception.code, 0)

    # --- real subprocess CLI ----------------------------------------------
    def test_subprocess_default_prints_date_exit0(self):
        rc, out, err = _run_cli([])
        self.assertEqual(rc, 0)
        self.assertEqual(len(out.splitlines()), 1)
        datetime.datetime.strptime(out.strip(), "%Y-%m-%d")

    def test_subprocess_utc_time_prints_datetime_exit0(self):
        rc, out, err = _run_cli(["--utc", "--time"])
        self.assertEqual(rc, 0)
        datetime.datetime.strptime(out.strip(), "%Y-%m-%d %H:%M:%S")

    def test_subprocess_bad_flag_usage_on_stderr_nonzero(self):
        """Bad flag via the real CLI: non-zero exit + usage written to stderr."""
        rc, out, err = _run_cli(["--bogus"])
        self.assertNotEqual(rc, 0)
        self.assertEqual(out, "")
        self.assertIn("usage", err.lower())

    def test_subprocess_utc_time_value_deterministic_via_fixed_clock(self):
        """Inject a fixed UTC instant through the clock to assert exact output.

        We monkeypatch isodate.now in a child interpreter so the CLI is fully
        deterministic end-to-end (proves the wiring carries the clock's value
        verbatim through the formatter to stdout)."""
        prog = (
            "import sys, datetime; "
            "sys.path.insert(0, %r); "
            "import isodate; "
            "_orig = isodate.now; "
            "isodate.now = lambda utc=False, fixed=None: "
            "datetime.datetime(2020, 1, 2, 3, 4, 5); "
            "sys.exit(isodate.main(sys.argv[1:]))" % BUILD_DIR
        )
        proc = subprocess.run(
            [sys.executable, "-c", prog, "--utc", "--time"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "2020-01-02 03:04:05")


if __name__ == "__main__":
    unittest.main()
