VERDICT: FAIL
component: C-003 (Argument parser)
auto_check: ran=yes result=pass
  command: PYTHONPATH=planning/preeng-unix/001-isodate-cli/build/tests python3 -m unittest test_isodate.ParserTests
  captured output:
    ...usage: isodate [-h] [--utc] [--time]
    isodate: error: unrecognized arguments: --bogus
    ..
    ----------------------------------------------------------------------
    Ran 5 tests in 0.001s

    OK
  exit=0
  note: ParserTests pass because they call parse_args() directly. The human_test exercises the FILE as a CLI and that path fails (see below).
human_test: FAIL  observed:
  - `python3 planning/preeng-unix/001-isodate-cli/build/isodate.py --bogus ; echo exit=$?` → printed NOTHING, REAL_EXIT=0 (captured with separate 2> redirect: stdout empty, stderr empty, exit 0).
  - `python3 planning/preeng-unix/001-isodate-cli/build/isodate.py --help` → printed NOTHING, exit=0 (expected: usage text + exit 0).
  pass_criteria ("Bad flag => usage on stderr AND non-zero exit; valid flags accepted") is NOT met: bad flag produces no usage, no stderr, and exit 0.
acceptance:
  - "parse_args(['--utc']) yields utc=True, time=False.": met — Namespace(utc=True, time=False).
  - "parse_args(['--time']) yields time=True.": met — Namespace(utc=False, time=True).
  - "parse_args([]) yields utc=False, time=False.": met — Namespace(utc=False, time=False).
  - "An unknown flag raises SystemExit with a non-zero code and writes usage to stderr.": NOT MET at the component's observable artifact. parse_args() raises correctly, but the declared output_artifact ("Running the file") does not: `isodate.py --bogus` exits 0 with no stderr because isodate.py defines NO main()/__main__ dispatch and never calls parse_args(sys.argv[1:]).
  - "Uses only stdlib argparse.": met — AST scan: imports only argparse+datetime.
output_artifact_present: partial/no — the parse_args function exists and is correct, BUT the component's stated observable behavior ("argparse handles usage/exit on bad flags" when the tool is run) is absent: the file has no entrypoint, so a human running it sees no usage and a wrong exit code.
reasons (if FAIL):
  - isodate.py has no `if __name__ == "__main__"` block and no main(); running `python3 isodate.py --bogus` parses nothing, prints nothing, and exits 0. The C-003 human_test bad-flag procedure produces exit=0 and empty stderr instead of usage-on-stderr + non-zero exit.
  - Add an entrypoint (or have C-000/Integrator wire one) that calls parse_args(sys.argv[1:]) so argparse's usage/non-zero-exit behavior is observable when the file is executed; or, if leaf-only by design, the C-003 verifier.human_test must not invoke the file directly (it should import and call parse_args, e.g. wrap in a try/except SystemExit asserting code!=0). As written, the human_test cannot pass against the current artifact.
suspected_cause: wrong-contract
  The artifact correctly implements parse_args (auto_check + unit asserts pass), but the C-003 output_artifact/human_test contract asserts file-level CLI behavior (running isodate.py --bogus) that belongs to the C-000 entrypoint. The leaf isodate.py was built deliberately WITHOUT a main() (per its own docstring lines 4-5: "deliberately does NOT define a main()... that is C-000's job"). The verifier human_test for a LEAF parser is therefore mis-scoped — it tests the assembled CLI, not the parse_args leaf. Route to Integrator: either re-scope the C-003 human_test to import-and-call parse_args, or build the C-000 entrypoint before this CLI-level observation can hold.
