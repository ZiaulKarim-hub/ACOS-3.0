"""isodate CLI — single-file command-line tool.

This module contains the three LEAF logical components of the isodate tool,
as importable functions, plus the ROOT (C-000) entrypoint that wires them
together into a real CLI.

Standard library only.

Leaves:
  - C-001 clock provider:      now(utc=False, fixed=None) -> datetime
  - C-002 date/time formatter: format_line(dt, with_time) -> str
  - C-003 argument parser:     parse_args(argv) -> Namespace{utc, time}

Root:
  - C-000 entrypoint:          main(argv) -> int  (wires C-003 -> C-001 -> C-002 -> print)
"""

import argparse
import datetime
import sys


# ---------------------------------------------------------------------------
# C-001 — Clock provider
# Single responsibility: return the current instant as a datetime (local or
# UTC), honoring an injected fixed clock when provided.
# ---------------------------------------------------------------------------
def now(utc=False, fixed=None):
    """Return the current instant as a datetime.

    Args:
        utc: If True, return a timezone-aware datetime in UTC; otherwise the
            local current instant (naive-local).
        fixed: Optional injected fixed datetime. When provided it is returned
            verbatim, making formatter/parser/clock tests deterministic. The
            injected value takes precedence over the utc flag (the caller is
            responsible for supplying a value already in the desired zone).

    Returns:
        datetime: the injected fixed value, or the real current instant.
    """
    if fixed is not None:
        return fixed
    if utc:
        return datetime.datetime.now(datetime.timezone.utc)
    return datetime.datetime.now()


# ---------------------------------------------------------------------------
# C-002 — Date/time formatter
# Single responsibility: turn a datetime plus a with_time flag into the
# correct output string.
# ---------------------------------------------------------------------------
def format_line(dt, with_time):
    """Format a datetime into the output line.

    Args:
        dt: the datetime instant to format.
        with_time: if True append ' HH:MM:SS'; otherwise date only.

    Returns:
        str: 'YYYY-MM-DD', or 'YYYY-MM-DD HH:MM:SS' when with_time is True.
    """
    if with_time:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# C-003 — Argument parser
# Single responsibility: parse argv into validated flags {utc, time}, or exit
# non-zero with a usage message on bad input (argparse contract).
# ---------------------------------------------------------------------------
def parse_args(argv):
    """Parse argv into a flags Namespace.

    Args:
        argv: list of command-line arguments (e.g. sys.argv[1:]).

    Returns:
        argparse.Namespace with boolean attributes .utc and .time.

    Raises:
        SystemExit: with a non-zero code (argparse: 2) and a usage message on
            stderr for unknown/bad flags; exit 0 for --help.
    """
    parser = argparse.ArgumentParser(
        prog="isodate",
        description="Print the current date (and optionally time) in ISO 8601 format.",
    )
    parser.add_argument(
        "--utc",
        action="store_true",
        help="Use UTC instead of local time.",
    )
    parser.add_argument(
        "--time",
        action="store_true",
        help="Append the time as HH:MM:SS.",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# C-000 — Root entrypoint (pure composition of the three leaves)
# Single responsibility: print the requested date/time line to stdout and
# return the correct exit code for the given argv.
#
# This node has NO behavior of its own beyond wiring its children together
# per integration-map.json:
#   C-003 parse_args(argv) -> flags {utc, time}
#   C-001 now(utc=flags.utc) -> dt           (the instant to format)
#   C-002 format_line(dt, flags.time) -> line (the exact stdout text)
#   print(line) -> stdout; return 0 on success.
#
# On bad flags, parse_args (argparse) raises SystemExit(non-zero) with usage
# on stderr BEFORE any other component runs. We deliberately do NOT catch it:
# letting it propagate is the contracted error path (C-003 usage_error output),
# and the __main__ dispatch / callers observe the non-zero exit. No hidden
# error handling is smuggled into the parent.
# ---------------------------------------------------------------------------
def main(argv):
    """Wire the three leaves into the product behavior.

    Args:
        argv: command-line arguments without the program name (sys.argv[1:]).

    Returns:
        int: 0 on success. (Bad flags propagate SystemExit from parse_args.)
    """
    flags = parse_args(argv)               # C-003 — may raise SystemExit on bad flags
    dt = now(utc=flags.utc)                # C-001 — clock mode selected by --utc
    line = format_line(dt, flags.time)     # C-002 — append time iff --time
    print(line)                            # the product's stdout
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
