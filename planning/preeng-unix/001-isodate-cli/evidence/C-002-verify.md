VERDICT: PASS
component: C-002 (Date/time formatter)
auto_check: ran=yes result=pass
  command: PYTHONPATH=planning/preeng-unix/001-isodate-cli/build/tests python3 -m unittest test_isodate.FormatterTests
  captured output:
    ....
    ----------------------------------------------------------------------
    Ran 4 tests in 0.000s

    OK
  exit=0
human_test: pass  observed: `python3 -c "...dt=datetime.datetime(2026,6,5,14,3,9); print(format_line(dt,False)); print(format_line(dt,True))"` printed line1=`2026-06-05`, line2=`2026-06-05 14:03:09`.
acceptance:
  - "format_line(dt, False) returns dt's date as YYYY-MM-DD.": met — printed 2026-06-05.
  - "format_line(dt, True) returns 'YYYY-MM-DD HH:MM:SS'.": met — printed 2026-06-05 14:03:09.
  - "Deterministic: same dt + flag always yields the same string.": met — pure strftime, no hidden state; FormatterTests assert exact strings.
  - "Uses only stdlib datetime/strftime.": met — implementation is dt.strftime(...); module imports only argparse+datetime.
output_artifact_present: yes — build/isodate.py defines format_line(dt, with_time); produces the observable string output.
