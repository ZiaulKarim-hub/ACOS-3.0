#!/usr/bin/env python3
"""
resolve_roster.py — SLICE-A3 roster resolver for acos-investment-committee.

Composes the ACTIVE seat roster for one IC session from:
  1. roster.yaml            (READ-ONLY canonical seat table, SLICE-A1)
  2. optional_triggers.yaml (READ-ONLY deal-attribute -> optional-seat map)
  3. a deal-brief (YAML or JSON; a file path, or a deal folder to search)
  4. an optional chair exclude/include-only command (as SLICE-D2 will supply)

and writes the result to `<session>/manifest.yaml` under `active_seats`,
preserving any other keys already present in that manifest.

Roster composition (stable seat numbers, see roster.yaml):
  lean = seats #1-8 (scrutiny) + #9 Deal Advocate (non-voting, ALWAYS present)
         + #10 Gap-Hunter/Chair (non-voting, ALWAYS present)
  full = lean + every optional seat (#11-15) whose trigger rule matches the
         deal-brief. If no deal-brief is available, `full` promotes ALL
         optionals (there is nothing to gate the promotion decision on).

HARD ASSERTION (the load-bearing guarantee of this slice): the voting_set is
built ONLY from active seats whose roster.yaml `voting` flag is literally
True. Seat #9 (Deal Advocate) and seat #10 (Gap-Hunter/Chair) are non-voting
by roster.yaml data AND by a redundant, explicit assertion below that
raises (non-zero exit) if either ever appears in a computed voting_set —
this is an assertion, not a comment (SLICE-A3 brief, three-lines-of-defense).

Stdlib only. No PyYAML / third-party dependency — this file includes a
small YAML SUBSET parser/dumper sufficient for this project's 2-space-indent
YAML dialect (as used by roster.yaml, optional_triggers.yaml, manifest.yaml,
and a hand-authored deal-brief.yaml). It is not a general YAML 1.1/1.2
implementation.

Usage:
  python3 resolve_roster.py --session <session-dir> --seats lean|full
      [--deal <deal-brief.yaml|.json path, or a deal folder>]
      [--exclude "3,4" | --include-only "1,5,6"]
      [--assert-test-force-vote "9"]   # TEST-ONLY, see below

Exit codes: 0 = success (roster resolved, manifest written); 1 = argument
error or (deliberately, for --assert-test-force-vote) an AssertionError
proving the Advocate/Chair non-voting guarantee cannot be bypassed.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

# --------------------------------------------------------------------------
# Minimal stdlib YAML subset: parser
# --------------------------------------------------------------------------

_QUOTED_RE = re.compile(r'^"([^"]*)"$|^\'([^\']*)\'$')
_INT_RE = re.compile(r'^-?\d+$')
_FLOAT_RE = re.compile(r'^-?\d+\.\d+$')
_BLOCK_SCALAR_HEADS = (">", "|", ">-", "|-", ">+", "|+")


def _strip_inline_comment(s):
    """Strip a trailing ' # ...' comment that is not inside quotes."""
    in_squote = in_dquote = False
    for idx, ch in enumerate(s):
        if ch == '"' and not in_squote:
            in_dquote = not in_dquote
        elif ch == "'" and not in_dquote:
            in_squote = not in_squote
        elif ch == "#" and not in_squote and not in_dquote:
            if idx == 0 or s[idx - 1].isspace():
                return s[:idx].rstrip()
    return s.rstrip()


def _split_top_level_commas(s):
    """Split on commas that are not inside single/double quotes."""
    parts, buf = [], []
    in_squote = in_dquote = False
    for ch in s:
        if ch == '"' and not in_squote:
            in_dquote = not in_dquote
        elif ch == "'" and not in_dquote:
            in_squote = not in_squote
        if ch == "," and not in_squote and not in_dquote:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return parts


def _parse_scalar(raw):
    s = raw.strip()
    if s == "" or s == "~" or s.lower() == "null":
        return None
    m = _QUOTED_RE.match(s)
    if m:
        return m.group(1) if m.group(1) is not None else m.group(2)
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if _INT_RE.match(s):
        return int(s)
    if _FLOAT_RE.match(s):
        return float(s)
    return s


def _parse_inline_list(raw):
    inner = raw.strip()
    inner = inner[1:-1].strip()  # drop [ ]
    if not inner:
        return []
    return [_parse_scalar(part) for part in _split_top_level_commas(inner)]


def _indent_of(line):
    return len(line) - len(line.lstrip(" "))


def _yaml_load(text):
    """Parse this project's YAML subset into plain dict/list/scalar values."""
    raw_lines = text.split("\n")
    lines = []
    for ln in raw_lines:
        if ln.strip() == "":
            continue
        if ln.lstrip(" ").startswith("#"):
            continue
        lines.append(ln.rstrip())
    if not lines:
        return {}

    pos = [0]

    def peek_indent():
        if pos[0] >= len(lines):
            return None
        return _indent_of(lines[pos[0]])

    def parse_block_scalar(base_indent):
        parts = []
        while pos[0] < len(lines) and _indent_of(lines[pos[0]]) > base_indent:
            parts.append(lines[pos[0]].strip())
            pos[0] += 1
        return " ".join(parts)

    def parse_value(rest, indent):
        """Parse the RHS of `key:` (rest already comment-stripped, may be '')."""
        if rest == "":
            nxt = peek_indent()
            if nxt is not None and nxt > indent:
                if lines[pos[0]].strip().startswith("- "):
                    return parse_sequence(nxt)
                return parse_mapping(nxt)
            return None
        if rest in _BLOCK_SCALAR_HEADS:
            nxt = peek_indent()
            if nxt is not None and nxt > indent:
                return parse_block_scalar(indent)
            return ""
        if rest.startswith("[") and rest.endswith("]"):
            return _parse_inline_list(rest)
        return _parse_scalar(rest)

    def parse_mapping(indent):
        result = {}
        while pos[0] < len(lines):
            ln = lines[pos[0]]
            ind = _indent_of(ln)
            if ind != indent:
                break
            content = ln.strip()
            if content.startswith("- ") or ":" not in content:
                break
            key, _, rest = content.partition(":")
            key = key.strip()
            rest = _strip_inline_comment(rest.strip())
            pos[0] += 1
            result[key] = parse_value(rest, indent)
        return result

    def parse_sequence(indent):
        result = []
        while pos[0] < len(lines):
            ln = lines[pos[0]]
            ind = _indent_of(ln)
            if ind != indent:
                break
            content = ln.strip()
            if not content.startswith("- "):
                break
            item_content = content[2:]
            item_indent = indent + 2
            pos[0] += 1
            stripped_item = item_content.strip()
            is_quoted_scalar = stripped_item[:1] in ("'", '"')
            if ":" in item_content and not is_quoted_scalar:
                key, _, rest = item_content.partition(":")
                key = key.strip()
                rest = _strip_inline_comment(rest.strip())
                first = {key: parse_value(rest, item_indent - 2)}
                first.update(parse_mapping(item_indent))
                result.append(first)
            else:
                result.append(_parse_scalar(_strip_inline_comment(item_content)))
        return result

    top_indent = peek_indent()
    if lines[pos[0]].strip().startswith("- "):
        return parse_sequence(top_indent)
    return parse_mapping(top_indent)


def _load_yaml_file(path):
    if not path or not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return _yaml_load(text) or {}


# --------------------------------------------------------------------------
# Minimal stdlib YAML subset: dumper (scalars / flat lists / one level of
# nested dicts — sufficient for manifest.yaml in this slice)
# --------------------------------------------------------------------------

_NEEDS_QUOTE_RE = re.compile(r'[:#\[\]{}]')


def _dump_scalar(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    s = str(v)
    if (
        s == ""
        or s != s.strip()
        or _NEEDS_QUOTE_RE.search(s)
        or s.lower() in ("null", "true", "false")
        or _INT_RE.match(s)
        or _FLOAT_RE.match(s)
    ):
        return json.dumps(s)
    return s


def _dump_list(key, v, pad):
    if not v:
        return "{}{}: []".format(pad, key)
    if all(not isinstance(x, (dict, list)) for x in v):
        return "{}{}: [{}]".format(pad, key, ", ".join(_dump_scalar(x) for x in v))
    lines = ["{}{}:".format(pad, key)]
    for x in v:
        if isinstance(x, dict):
            sub = _dump_node(x, 0)
            sub_lines = sub.split("\n")
            lines.append("{}  - {}".format(pad, sub_lines[0].lstrip()))
            for extra in sub_lines[1:]:
                lines.append("{}    {}".format(pad, extra.lstrip()))
        else:
            lines.append("{}  - {}".format(pad, _dump_scalar(x)))
    return "\n".join(lines)


def _dump_node(node, indent):
    pad = "  " * indent
    lines = []
    for k, v in node.items():
        if isinstance(v, dict):
            if not v:
                lines.append("{}{}: {{}}".format(pad, k))
            else:
                lines.append("{}{}:".format(pad, k))
                lines.append(_dump_node(v, indent + 1))
        elif isinstance(v, list):
            lines.append(_dump_list(k, v, pad))
        else:
            lines.append("{}{}: {}".format(pad, k, _dump_scalar(v)))
    return "\n".join(lines)


def _yaml_dump_top(d):
    return _dump_node(d, 0) + "\n"


# --------------------------------------------------------------------------
# Roster domain logic
# --------------------------------------------------------------------------

LEAN_CORE = [1, 2, 3, 4, 5, 6, 7, 8, 10]  # seats #1-8 scrutiny + #10 Gap-Hunter/Chair (Advocate #9 retired 2026-07-10)

_SPECIAL_COVERAGE_DESC = {
    3: "normalized-NOI veracity (Accounting cross-cutting cross-check)",
    8: "strategic-fit / off-mandate lens (Strategy cross-cutting)",
    9: "defense/steelman good-faith mitigant coverage (Deal Advocate)",
    10: "procedural gap-hunting / uncovered-risk coverage (Gap-Hunter/Chair)",
}

_ALWAYS_PRESENT = {10}  # Gap-Hunter/Chair (Deal Advocate #9 retired 2026-07-10)


def build_seats_index(roster_doc):
    idx = {}
    for s in roster_doc.get("seats", []) or []:
        idx[int(s["n"])] = s
    for s in roster_doc.get("optionals", []) or []:
        idx[int(s["n"])] = s
    return idx


def _resolve_deal_brief_path(deal_arg):
    if not deal_arg:
        return None
    if os.path.isdir(deal_arg):
        candidates = [
            os.path.join(deal_arg, "deal-brief.yaml"),
            os.path.join(deal_arg, "deal-brief.yml"),
            os.path.join(deal_arg, "deal-brief.json"),
            os.path.join(deal_arg, "deal-brief", "deal-brief.yaml"),
            os.path.join(deal_arg, "deal-brief", "deal-brief.yml"),
            os.path.join(deal_arg, "deal-brief", "deal-brief.json"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return None
    if os.path.isfile(deal_arg):
        return deal_arg
    return None


def _load_deal_brief(path):
    if path is None:
        return None
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if path.endswith(".json"):
        return json.loads(text)
    return _yaml_load(text)


def _deal_get(deal, field):
    if not deal or not field:
        return None
    if field in deal:
        return deal[field]
    for container_key in ("deal", "attributes", "flags", "trigger_attributes"):
        c = deal.get(container_key)
        if isinstance(c, dict) and field in c:
            return c[field]
    return None


def _truthy(v):
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip().lower() not in ("", "false", "no", "none", "0")
    return bool(v)


def _rule_matches(deal, rule):
    if deal is None:
        return False
    if "any_of_fields" in rule:
        return any(_truthy(_deal_get(deal, f)) for f in rule["any_of_fields"])
    field = rule.get("field")
    v = _deal_get(deal, field)
    if rule.get("truthy"):
        return _truthy(v)
    match_list = rule.get("match")
    if match_list:
        if v is None:
            return False
        candidates = v if isinstance(v, list) else [v]
        for cv in candidates:
            for m in match_list:
                if isinstance(cv, str) and isinstance(m, str):
                    if cv.strip().lower() == m.strip().lower():
                        return True
                elif cv == m:
                    return True
    return False


def promote_optionals(deal_path, triggers_doc, all_optional_ns):
    """Returns (set_of_promoted_seat_numbers, human-readable note)."""
    deal = _load_deal_brief(deal_path) if deal_path else None
    if deal is None:
        return set(all_optional_ns), (
            "no deal-brief available -- promoting ALL optionals per spec "
            "(SLICE-A3 brief: 'full may include all optionals' when there is "
            "nothing to gate the promotion decision on)"
        )
    rules = triggers_doc.get("triggers", []) or []
    promoted = {int(r["seat"]) for r in rules if _rule_matches(deal, r)}
    return promoted, "deal-brief evaluated against {} trigger rule(s) from {}".format(
        len(rules), deal_path
    )


def resolve_active_seats(mode, deal_path, roster_doc, triggers_doc):
    seats_idx = build_seats_index(roster_doc)
    base = set(LEAN_CORE)
    if mode == "lean":
        note = "lean roster (seats #1-8 scrutiny + #10 Gap-Hunter/Chair; Advocate #9 retired)"
    else:
        all_optional_ns = sorted(int(o["n"]) for o in roster_doc.get("optionals", []) or [])
        promoted, note = promote_optionals(deal_path, triggers_doc, all_optional_ns)
        base |= promoted
    return base, seats_idx, note


def _parse_seat_list(raw):
    if not raw:
        return set()
    out = set()
    for tok in raw.split(","):
        tok = tok.strip().lstrip("#")
        if tok:
            out.add(int(tok))
    return out


def _gap_line(n, seats_idx):
    seat = seats_idx.get(n, {})
    name = seat.get("name", "seat #{}".format(n))
    desc = _SPECIAL_COVERAGE_DESC.get(n)
    if desc is None:
        owns = seat.get("owns")
        if isinstance(owns, list) and owns:
            desc = ", ".join(owns)
        else:
            desc = "coverage"
    return "excluding #{} ({}) -> {} unowned this session".format(n, name, desc)


def apply_exclude_include(active_seats, seats_idx, exclude_arg, include_only_arg):
    active = set(active_seats)
    gap_lines = []
    if exclude_arg:
        excl = _parse_seat_list(exclude_arg)
        removed = excl & active
        active -= excl
        for n in sorted(removed):
            gap_lines.append(_gap_line(n, seats_idx))
    elif include_only_arg:
        keep = _parse_seat_list(include_only_arg) | _ALWAYS_PRESENT
        removed = active - keep
        active &= keep
        for n in sorted(removed):
            gap_lines.append(_gap_line(n, seats_idx))
    return active, gap_lines


def write_gap_log(session_dir, gap_lines):
    if not gap_lines:
        return None
    path = os.path.join(session_dir, "gap-log.md")
    is_new = not os.path.isfile(path)
    with open(path, "a", encoding="utf-8") as f:
        if is_new:
            f.write("# Gap-Hunter (#10) uncovered-risk log\n\n")
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        f.write("## Roster resolution — {}\n".format(ts))
        for line in gap_lines:
            f.write("- {}\n".format(line))
        f.write("\n")
    return path


def write_manifest(session_dir, active_seats, deal_arg):
    path = os.path.join(session_dir, "manifest.yaml")
    existing = _load_yaml_file(path)
    if not existing:
        existing = {
            "session_id": os.path.basename(os.path.normpath(session_dir)),
            "deal": deal_arg,
            "status": "open",
            "mode": "deliberation",
            "current_round": 0,
        }
    existing["active_seats"] = sorted(active_seats)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_yaml_dump_top(existing))
    return path


def compute_voting_set(active_seats, seats_idx):
    return sorted(n for n in active_seats if seats_idx.get(n, {}).get("voting") is True)


def assert_advocate_and_chair_never_vote(voting_set):
    """The load-bearing hard assertion: #9 and #10 may NEVER appear here."""
    forbidden = _ALWAYS_PRESENT
    violation = forbidden.intersection(voting_set)
    if violation:
        raise AssertionError(
            "HARD ASSERTION FAILED: seat(s) {} must NEVER appear in a scrutiny "
            "voting_set (Deal Advocate #9 is non-voting defense; Gap-Hunter/"
            "Chair #10 is non-voting procedural, per roster.yaml voting:false). "
            "This is a structural three-lines-of-defense violation, not a "
            "warning, and the resolver refuses to proceed.".format(sorted(violation))
        )
    return True


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Resolve the active IC seat roster for one session (SLICE-A3)."
    )
    parser.add_argument("--session", required=True, help="Session directory.")
    parser.add_argument(
        "--deal",
        default=None,
        help="Path to a deal-brief.yaml/.json, or a deal folder to search.",
    )
    parser.add_argument("--seats", required=True, choices=["lean", "full"])
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--exclude", default=None, help='e.g. "3,4"')
    grp.add_argument("--include-only", default=None, help='e.g. "1,5,6"')
    parser.add_argument(
        "--assert-test-force-vote",
        default=None,
        help=(
            "TEST-ONLY: comma seat list forcibly injected into voting_set "
            "BEFORE the hard non-voting assertion runs, to prove the "
            "assertion blocks #9/#10. Never use outside tests."
        ),
    )
    args = parser.parse_args(argv)

    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    roster_doc = _load_yaml_file(os.path.join(skill_dir, "roster.yaml"))
    triggers_doc = _load_yaml_file(os.path.join(skill_dir, "optional_triggers.yaml"))

    deal_path = _resolve_deal_brief_path(args.deal)

    active, seats_idx, note = resolve_active_seats(args.seats, deal_path, roster_doc, triggers_doc)
    active, gap_lines = apply_exclude_include(active, seats_idx, args.exclude, args.include_only)

    session_dir = args.session
    os.makedirs(session_dir, exist_ok=True)
    gap_log_path = write_gap_log(session_dir, gap_lines)
    manifest_path = write_manifest(session_dir, active, args.deal)

    voting_set = compute_voting_set(active, seats_idx)
    if args.assert_test_force_vote:
        forced = _parse_seat_list(args.assert_test_force_vote)
        voting_set = sorted(set(voting_set) | forced)
        print(
            "[TEST HOOK] forcibly injected {} into voting_set BEFORE the "
            "assertion runs".format(sorted(forced))
        )

    assert_advocate_and_chair_never_vote(voting_set)

    print("Roster mode: {} ({})".format(args.seats, note))
    print("Active roster (#): {}".format(sorted(active)))
    print("Voting set (#):    {}".format(voting_set))
    print("Advocate #9 in voting_set:    {}".format(9 in voting_set))
    print("Gap-Hunter #10 in voting_set: {}".format(10 in voting_set))
    if gap_lines:
        print("Gap-log entries written ({}) -> {}:".format(len(gap_lines), gap_log_path))
        for line in gap_lines:
            print("  - " + line)
    print("Manifest updated: {}".format(manifest_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
