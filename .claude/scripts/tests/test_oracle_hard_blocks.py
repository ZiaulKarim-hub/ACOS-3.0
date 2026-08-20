"""The Oracle's hard blocks must actually match — found dead 2026-08-17.

Python, not TypeScript, by exception 1 of the language rule: this extends
`oracle-evaluate.py`, which is existing Python, and a hook cannot be split
across two runtimes.

## What was wrong

`.acos/config/oracle.yaml` writes each pattern the way YAML requires:

    hard_blocks:
      - "git\\s+push"

A real YAML reader turns `\\s` into `\s`, giving the regex `git\s+push`, which
matches. The Oracle ships its own miniature YAML reader, and `_parse_value`
stripped the quotes without ever processing escapes. So the pattern arrived as
the literal two characters `\` `\` followed by `s` — a regex that matches a
backslash, then an `s`. No shell command contains that.

The consequence was total and silent: **every project whose oracle.yaml lists
`hard_blocks` had all of them dead, at every threshold.** Nothing errored.
`--diagnose` still printed the list. A `git push` sailed through at threshold 9
exactly as it would at 12, which is the one thing the hard-block list exists to
prevent. It was found because a real `git push personal main` ran unblocked and
the reason did not add up.

Projects that never override the list were unaffected, because the built-in
`DEFAULTS["hard_blocks"]` are `r"..."` literals in code and never touch the
YAML path. That is why this survived: the default is fine, and only a project
that customised its config lost the guard.

## What is pinned here

1. Double-quoted scalars unescape, so config patterns compile to live regexes.
2. Single-quoted scalars do NOT unescape backslashes — that is real YAML's rule
   and regexes are usually written in single quotes elsewhere; getting this
   backwards would break them the other way.
3. The seven shipped patterns each match the command they name, loaded through
   the real config file rather than through a copy of the list.
4. The YOLO boundary is 12, not 11, in BOTH the enforcing branch and the
   diagnose banner — they disagreed, and the banner cried wolf.
"""

import importlib.util
import re
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
HOOK = SCRIPTS / "oracle-evaluate.py"


def _load():
    """Import the hook by path — its filename has a hyphen, so no plain import."""
    spec = importlib.util.spec_from_file_location("oracle_evaluate_undertest", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


oe = _load()


# ── 1. the escape bug itself ────────────────────────────────────────────────


def test_double_quoted_scalar_unescapes_backslashes():
    # The exact byte sequence the config file holds.
    assert oe._parse_value(r'"git\\s+push"') == r"git\s+push"


def test_double_quoted_pattern_is_a_live_regex():
    pattern = oe._parse_value(r'"git\\s+push"')
    assert re.search(pattern, "git push personal main", re.IGNORECASE)
    assert re.search(pattern, "cd /tmp && git  push origin main")


def test_single_quoted_scalar_does_not_unescape():
    # Real YAML: single quotes are literal apart from a doubled quote. A regex
    # written as 'git\s+push' must survive intact rather than lose its escape.
    assert oe._parse_value(r"'git\s+push'") == r"git\s+push"
    assert re.search(oe._parse_value(r"'git\s+push'"), "git push origin main")


def test_double_quoted_handles_the_other_escapes():
    assert oe._parse_value(r'"a\nb"') == "a\nb"
    assert oe._parse_value(r'"a\tb"') == "a\tb"
    assert oe._parse_value(r'"say \"hi\""') == 'say "hi"'


def test_unquoted_scalars_are_untouched():
    # Nothing above may start eating backslashes in bare scalars.
    assert oe._parse_value(r"git\s+push") == r"git\s+push"
    assert oe._parse_value("9") == 9
    assert oe._parse_value("true") is True


# ── 2. end to end, through a real config file ───────────────────────────────


SHIPPED = """\
enabled: true
threshold: 9
hard_blocks:
  - "git\\\\s+push"
  - "rm\\\\s+-rf\\\\s+/\\\\s*$"
  - "rm\\\\s+-rf\\\\s+~/?\\\\s*$"
  - "rm\\\\s+-rf\\\\s+\\\\.\\\\s*$"
  - "git\\\\s+reset\\\\s+--hard\\\\s+(origin/)?(main|master)"
  - "DROP\\\\s+(TABLE|DATABASE)"
  - "git\\\\s+branch\\\\s+-D\\\\s+(main|master)"
"""

# One command per shipped pattern, in the same order. These are the commands
# the list exists to stop; if any stops matching, that guard is gone.
BLOCKED_COMMANDS = [
    "git push personal main",
    "rm -rf /",
    "rm -rf ~",
    "rm -rf .",
    "git reset --hard origin/main",
    "DROP TABLE item",
    "git branch -D main",
]


def _project_with_config(tmp, body):
    root = Path(tmp)
    cfg = root / ".acos" / "config"
    cfg.mkdir(parents=True)
    (cfg / "oracle.yaml").write_text(body)
    return root


def test_every_shipped_pattern_still_blocks_its_command():
    with tempfile.TemporaryDirectory() as tmp:
        root = _project_with_config(tmp, SHIPPED)
        config = oe.load_config(root)
        assert len(config["hard_blocks"]) == 7

        for command in BLOCKED_COMMANDS:
            assert oe.check_hard_blocks("Bash", {"command": command}, config), (
                f"{command!r} was NOT hard-blocked — a guard silently died. "
                f"patterns loaded: {config['hard_blocks']}"
            )


def test_ordinary_commands_are_not_blocked():
    # The mirror. A guard that blocks everything is as broken as one that
    # blocks nothing, and would be far more obvious — so it is pinned too.
    with tempfile.TemporaryDirectory() as tmp:
        config = oe.load_config(_project_with_config(tmp, SHIPPED))
        for command in [
            "git status",
            "git pull",
            "flutter test",
            "rm -rf build/",          # a NAMED folder, not / or ~ or .
            "SELECT * FROM item",
        ]:
            assert not oe.check_hard_blocks("Bash", {"command": command}, config), (
                f"{command!r} was blocked and should not be"
            )


def test_a_config_list_is_no_weaker_than_the_built_in_default():
    # The regression in one sentence: customising the config used to DISARM the
    # list. Loading the same seven patterns from YAML must behave exactly as the
    # code defaults do.
    with tempfile.TemporaryDirectory() as tmp:
        from_yaml = oe.load_config(_project_with_config(tmp, SHIPPED))
    with tempfile.TemporaryDirectory() as tmp:
        bare = oe.load_config(Path(tmp))  # no config file -> DEFAULTS

    for command in BLOCKED_COMMANDS:
        assert oe.check_hard_blocks("Bash", {"command": command}, from_yaml) == \
               oe.check_hard_blocks("Bash", {"command": command}, bare), \
               f"config-loaded and built-in disagree about {command!r}"


# ── 3. the YOLO boundary, in both places that name it ───────────────────────


def test_yolo_boundary_is_twelve_in_the_source():
    # Zee moved YOLO 11 -> 12 on 2026-08-16; 11 became autopilot. The enforcing
    # branch was updated and the diagnose banner was not, so --diagnose reported
    # "ALL guardrails are disabled" while the hard blocks were still live.
    # Pinned as source text because both are plain integer comparisons with no
    # seam to call.
    src = HOOK.read_text()
    assert "if threshold >= 12:" in src, "the enforcing branch must bypass only at 12"
    assert "yolo_active = threshold >= 12" in src, (
        "the diagnose banner must use the same boundary as the branch it reports on"
    )
    assert "yolo_active = threshold >= 11" not in src, "the stale 11 boundary is back"


def test_hard_blocks_survive_threshold_eleven():
    # The behaviour the boundary is for: at 11 a hard-blocked command is still
    # refused. Only 12 waves it through.
    with tempfile.TemporaryDirectory() as tmp:
        root = _project_with_config(tmp, SHIPPED.replace("threshold: 9", "threshold: 11"))
        config = oe.load_config(root)
        assert config["threshold"] == 11
        assert oe.check_hard_blocks("Bash", {"command": "git push personal main"}, config)


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL  {name}\n        {e}")
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"  ERROR {name}\n        {type(e).__name__}: {e}")
    print(f"\n{'FAILED' if failures else 'ALL PASSED'} — {failures} failure(s)")
    sys.exit(1 if failures else 0)
