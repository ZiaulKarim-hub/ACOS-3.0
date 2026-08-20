#!/bin/bash
# close-project.sh — safe-close protocol, steps 0-10 (ACOS Resurrection Protocol).
#
# Interface:
#   close-project.sh --intent-file <path> --session-id <sid>
#                    [--roundtrip-result <path>] [--learnings-file <path>]
#                    [--park-to <uuid>] [--auto-close] [--dry-run]
#
# --park-to <uuid> is the DESTINATION PICKER (Zee's brief, 2026-08-18). Without
# it a close parks the tab's work onto the tab's own row, which is all a close
# could ever do. With it, the reentry note, the registry last_close and the
# captured learnings all land on the NAMED row instead — so a scratch tab whose
# work turned out to belong to "Skill Workshop" can be filed there rather than
# leaving a stray project behind. The tab's own row is then retired (step 7b),
# which is the half that needs guards: it is refused outright if that row holds
# knowledge facts, a prior close, or another live window.
#
# --learnings-file is the KB-A capture loop (user brief 2026-08-04). It takes a
# JSON array of candidate learnings the SESSION composed — the Kind-1/Kind-2
# sort is a judgement, exactly like the intent core, so the session makes it and
# this script gates it. Kind 1 (machine-verifiable) is written silently and
# always; Kind 2 (Zee's own rulings) is never written here, only reported back
# so the session can ask him, capped at 2 questions. Omitting the flag closes
# exactly as before — capture is additive and never blocks a close.
# Env overrides (tests only):
#   RESURRECTION_STATE_DIR    daemon state dir (default ~/Library/Application Support/acos-token-monitor/state)
#   ACOS_REGISTRY_HOME        registry home override (never the real ~ in tests)
#   RESURRECTION_PROJECT_ROOT project root (default $PWD)
#   RESURRECTION_SKIP_CMUX=1  skip workspace validation (sandbox)
#
# Contract: the receipt is printed BY THIS SCRIPT from verified read-backs —
# the model/skill never composes receipt content. Every failure branch's action
# is "don't close": NOT SAFE + nonzero exit. The tab vanishing IS the success
# signal; the tab staying open IS the failure signal.

set -u

CLOSE_INTENT_FILE=""
CLOSE_SESSION_ID=""
CLOSE_ROUNDTRIP=""
CLOSE_LEARNINGS=""
CLOSE_PARK_TO=""
CLOSE_AUTO=0
CLOSE_DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --intent-file)      CLOSE_INTENT_FILE="${2:-}"; shift 2 ;;
    --session-id)       CLOSE_SESSION_ID="${2:-}";  shift 2 ;;
    --roundtrip-result) CLOSE_ROUNDTRIP="${2:-}";   shift 2 ;;
    --learnings-file)   CLOSE_LEARNINGS="${2:-}";   shift 2 ;;
    --park-to)          CLOSE_PARK_TO="${2:-}";     shift 2 ;;
    --auto-close)       CLOSE_AUTO=1; shift ;;
    --dry-run)          CLOSE_DRY=1;  shift ;;
    *) echo "NOT SAFE — unknown argument: $1" >&2; exit 2 ;;
  esac
done
export CLOSE_INTENT_FILE CLOSE_SESSION_ID CLOSE_ROUNDTRIP CLOSE_LEARNINGS CLOSE_AUTO CLOSE_DRY CLOSE_PARK_TO
CLOSE_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export CLOSE_LIB_DIR

# exec: the python exit status is the script's; nothing runs after the heredoc.
exec /usr/bin/python3 - <<'PYEOF'
"""close-project.sh embedded body — safe-close steps 0-10.

Constraints:
  * System /usr/bin/python3 is 3.9.6 with NO yaml module. handoff.yaml is plain
    text in a stable line format (key: value, "  - " list items, "key: |"
    literal blocks) parsed by line prefix — never by a yaml library.
  * Registry access ONLY via registry_lib.py (same directory).
  * The daemon state dir receives EXACTLY ONE write ever: step 0's stop-<sid>
    (the documented Eternity opt-out marker). pending-resume-*.txt and
    RESCUED-resume-*.txt are never touched.
  * Close artifacts live under <root>/memory/handoffs/closed/<slug>/ — outside
    Eternity's non-recursive glob (memory/handoffs/*.md|*.yaml). Never
    top-level memory/handoffs/*, never *.resume.md.
  * DP2 is UNANSWERED: closing a workspace containing a live Claude session has
    UNKNOWN behavior. Auto-close is OFF by default and refuses unless
    RESURRECTION_DP2_CONFIRMED=1 AND the workspace is not the last in its window.
  * workspace.close is the LITERAL LAST statement of this module.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

CMUX_BIN = "/Applications/cmux.app/Contents/Resources/bin/cmux"
GIT_BIN = "/usr/bin/git"
DIRTY_LIST_CAP = 200

INTENT = os.environ.get("CLOSE_INTENT_FILE", "")
SID = os.environ.get("CLOSE_SESSION_ID", "")
ROUNDTRIP = os.environ.get("CLOSE_ROUNDTRIP", "")
LEARNINGS = os.environ.get("CLOSE_LEARNINGS", "")
# --park-to <uuid>: park THIS tab's work onto a DIFFERENT project's row (Zee's
# destination-picker brief, 2026-08-18). The tab's own row becomes the ORPHAN and
# is retired afterwards, under the guards in step 7b. Empty = today's behaviour.
PARK_TO = os.environ.get("CLOSE_PARK_TO", "").strip()
AUTO = os.environ.get("CLOSE_AUTO", "0") == "1"
DRY = os.environ.get("CLOSE_DRY", "0") == "1"
ROOT = os.path.abspath(os.environ.get("RESURRECTION_PROJECT_ROOT") or os.getcwd())
STATE_DIR = os.environ.get("RESURRECTION_STATE_DIR") or os.path.join(
    os.path.expanduser("~"), "Library", "Application Support", "acos-token-monitor", "state")
REG_HOME = os.environ.get("ACOS_REGISTRY_HOME") or None
SKIP_CMUX = os.environ.get("RESURRECTION_SKIP_CMUX") == "1"

RECEIPT = []


def emit(line):
    RECEIPT.append(line)


def flush_receipt():
    for ln in RECEIPT:
        print(ln)


_STOP_MARKER_WRITTEN = None


def refuse(reason, code=1):
    """Every failure branch lands here: print what completed, then don't close."""
    flush_receipt()
    # A refused close must not leave the session opted out of the Eternity
    # 400k auto-fire (tamper-verdict D3): remove the marker THIS run wrote.
    if _STOP_MARKER_WRITTEN:
        try:
            os.unlink(_STOP_MARKER_WRITTEN)
            print("stop marker removed — Eternity auto-fire re-armed (a refused close must not opt out)")
        except OSError:
            print("WARN: could not remove stop marker %s — this session stays opted out of Eternity auto-fire" % _STOP_MARKER_WRITTEN)
    print("NOT SAFE — %s" % reason)
    sys.exit(code)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def write_file(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())


def read_intent(path):
    """Step 1 gate: next_action must exist and be <=90 chars — generated by the
    parent, never truncated here from a longer field."""
    try:
        with open(path, "r") as fh:
            text = fh.read()
    except OSError as exc:
        refuse("intent file unreadable: %s (%s)" % (path, exc))
    na = None
    for ln in text.splitlines():
        if ln.startswith("next_action:"):
            na = ln[len("next_action:"):].strip()
            break
    if not na:
        refuse("intent file has no next_action line — the parent must GENERATE one (<=90 chars); refusing to invent it")
    if len(na) > 90:
        refuse("next_action is %d chars (limit 90) — regenerate a shorter line; this script never truncates" % len(na))
    return text, na


def git_facts(root):
    """Captured git attributes + dirty list. None when not a usable git repo."""
    if not os.path.exists(os.path.join(root, ".git")):
        return None

    def probe(args):
        return subprocess.run([GIT_BIN, "-C", root] + args,
                              capture_output=True, text=True, timeout=10)
    try:
        branch = probe(["rev-parse", "--abbrev-ref", "HEAD"])
        head = probe(["rev-parse", "HEAD"])
        status = probe(["status", "--porcelain"])
    except (subprocess.TimeoutExpired, OSError):
        return None
    if branch.returncode or head.returncode or status.returncode:
        return None
    dirty = [ln for ln in status.stdout.splitlines() if ln.strip()]
    return {"branch": branch.stdout.strip(), "head": head.stdout.strip(),
            "dirty_count": len(dirty), "dirty": dirty}


def parse_handoff(path):
    """Line-prefix parser for the stable handoff format (no yaml lib exists on
    system python 3.9.6). Top-level `key: value`, `key: |` literal blocks
    (2-space indented), `key:` + `  - item` lists, `key:` + indented sub-lines."""
    with open(path, "r") as fh:
        lines = fh.read().splitlines()
    d = {}
    key = None
    mode = None  # None | "block" | "sub"
    for ln in lines:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$", ln)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            if val == "|":
                d[key] = ""
                mode = "block"
            elif val == "":
                d[key] = []
                mode = "sub"
            else:
                d[key] = val
                mode = None
        elif mode == "block":
            d[key] += (ln[2:] if ln.startswith("  ") else ln) + "\n"
        elif mode == "sub" and ln.strip():
            item = ln.strip()
            if item.startswith("- "):
                item = item[2:].strip()
            d[key].append(item)
    return d


def parse_roundtrip(path):
    """Step 5: blind round-trip result (produced by SLICE-RES-22's verifier).
    Line format: `verdict: PASS|DEGRADED` + `next_step: <quoted reconstruction>`."""
    try:
        with open(path, "r") as fh:
            text = fh.read()
    except OSError as exc:
        refuse("roundtrip result unreadable: %s (%s)" % (path, exc))
    verdict = None
    nstep = None
    for ln in text.splitlines():
        if verdict is None and ln.startswith("verdict:"):
            verdict = ln.split(":", 1)[1].strip()
        if nstep is None and ln.startswith("next_step:"):
            nstep = ln.split(":", 1)[1].strip()
    if verdict not in ("PASS", "DEGRADED"):
        refuse("roundtrip verdict %r is not PASS|DEGRADED — PASS required for SAFE (DEGRADED only after the Wigum cap)" % verdict)
    if not nstep:
        refuse("roundtrip quoted next-step is missing/empty — a round-trip without a reconstruction proves nothing")
    return verdict, nstep


def cleanup_inline(root):
    """Inline mirror of session-cleanup.sh's .acos/state allowlist. Runs ONLY in
    the auto-close branch: the SessionEnd hook is presumed dead under the
    workspace.close process kill. Explicit allowlist — never a blanket rm."""
    state = os.path.join(root, ".acos", "state")
    if not os.path.isdir(state):
        return
    import glob as _glob
    names = [".token-gate-cache", ".handoff-enforcement", ".stop-retry-count",
             "continue-pending", "continue-success", "continue-failed",
             ".continue-launcher.sh", "model-session.yaml",
             "autopilot-active", "autopilot-loop-state.json"]
    for n in names:
        try:
            os.unlink(os.path.join(state, n))
        except OSError:
            pass
    for pat in (".continue-launcher-*.command", "handoff-triggered-*"):
        for p in _glob.glob(os.path.join(state, pat)):
            try:
                os.unlink(p)
            except OSError:
                pass


# --------------------------------------------------------------------------
# Agent-03's verification gate, quoted VERBATIM from
# .acos/swarm/swarm-20260714-084532/agent-03/findings.md
# ("Appendix: Verification Spec (step 4 — the exact check)"):
#
#   fail() { echo "CLOSE ABORTED — $1" >&2; exit 1; }   # tab stays open. Always.
#
#   # 1. handoff exists and is non-empty
#   [[ -s "$HANDOFF" ]] || fail "handoff missing/empty: $HANDOFF"
#
#   # 2. handoff is FRESH (<300s) — catches a no-op'd generator leaving a stale file.
#   #    Existence alone is NOT enough: memory/handoffs/ always has old files that
#   #    would pass an existence check and silently register week-old context.
#   AGE=$(( $(date +%s) - $(stat -f%m "$HANDOFF") ))
#   [[ $AGE -le 300 ]] || fail "handoff is ${AGE}s old — generator likely no-op'd"
#
#   # 3. handoff PARSES and is a mapping
#   python3 -c 'import yaml,sys; d=yaml.safe_load(open(sys.argv[1])); assert isinstance(d,dict)' \
#     "$HANDOFF" || fail "handoff does not parse as a YAML mapping"
#
#   # 4. handoff is NOT still the stub, and carries an actionable next step
#   python3 - "$HANDOFF" <<'PY' || fail "handoff incomplete (stub or missing next_actions)"
#   import yaml, sys
#   d = yaml.safe_load(open(sys.argv[1]))
#   assert "STUB" not in (d.get("session_summary") or "").upper(), "still a stub"
#   for k in ("session_summary","next_actions","git_state"):
#       assert d.get(k), f"missing/empty: {k}"
#   assert len(d["next_actions"]) >= 1
#   PY
#
#   # 5. resume prompt exists and is non-empty
#   [[ -s "$RESUME" ]] || fail "resume prompt missing/empty: $RESUME"
#
#   # 6. resume prompt is not truncated (byte floor)
#   [[ $(wc -c < "$RESUME") -ge 200 ]] || fail "resume prompt suspiciously small"
#
#   # 7. THE STRONGEST CHECK — the resume prompt must reference the handoff we JUST wrote.
#   #    Catches the real bug class in this repo: a resume regenerated from an OLDER
#   #    handoff (cf. the stale-handoff freeze, and the `.resume.resume.md` doubling
#   #    guarded against in eternity-protocol-core.sh:84-87). Without this, checks
#   #    1-6 all pass while the registry row points at last week's context.
#   grep -qF "$(basename "$HANDOFF")" "$RESUME" \
#     || fail "resume does not reference $(basename "$HANDOFF") — regenerated from a STALE handoff"
#
#   # → ONLY NOW write the registry row (atomic tmp+rename), read it back,
#   #   assert sha256(handoff) matches the row, then close.
#
# Implementation adaptations (constraints, not redesign):
#   * checks 3+4: no yaml module exists on system python 3.9.6 — the mapping/
#     stub checks run against the line-prefix parser over the same stable format.
#   * check 7: in the closed/<slug>/ layout basename is always "handoff.yaml",
#     so the needle is the slug-qualified path "closed/<slug>/handoff.yaml" —
#     it CONTAINS the basename (strictly stronger, same intent: the reentry
#     must reference THIS close's handoff, not an older one).
# Every measured value below is read back from disk at check time.
# --------------------------------------------------------------------------
def verification_gate(handoff_path, reentry_path, slug):
    lines = []
    # 1. handoff exists and is non-empty
    try:
        size = os.stat(handoff_path).st_size
    except OSError:
        refuse("gate check 1 failed: handoff missing: %s" % handoff_path)
    if size <= 0:
        refuse("gate check 1 failed: handoff empty: %s" % handoff_path)
    lines.append("   [1] handoff exists non-empty: %d bytes" % size)
    # 2. handoff is FRESH (<300s)
    age = int(time.time() - os.stat(handoff_path).st_mtime)
    if age > 300:
        refuse("gate check 2 failed: handoff is %ds old — generator likely no-op'd" % age)
    lines.append("   [2] handoff fresh: %ds old (limit 300s)" % age)
    # 3. handoff PARSES and is a mapping
    try:
        d = parse_handoff(handoff_path)
    except OSError as exc:
        refuse("gate check 3 failed: handoff unreadable (%s)" % exc)
    if not isinstance(d, dict) or not d:
        refuse("gate check 3 failed: handoff does not parse as a mapping")
    lines.append("   [3] handoff parses as mapping: %d top-level keys" % len(d))
    # 4. handoff is NOT still the stub, and carries an actionable next step
    ss = d.get("session_summary") or ""
    if "STUB" in ss.upper():
        refuse("gate check 4 failed: handoff is still a stub")
    for k in ("session_summary", "next_actions", "git_state"):
        if not d.get(k):
            refuse("gate check 4 failed: handoff missing/empty: %s" % k)
    n_actions = len(d["next_actions"])
    if n_actions < 1:
        refuse("gate check 4 failed: next_actions is empty")
    lines.append("   [4] not a stub + actionable: session_summary present, "
                 "next_actions listed %d of %d, git_state present" % (n_actions, n_actions))
    # 5. resume (reentry) prompt exists and is non-empty
    try:
        rsize = os.stat(reentry_path).st_size
    except OSError:
        refuse("gate check 5 failed: reentry missing: %s" % reentry_path)
    if rsize <= 0:
        refuse("gate check 5 failed: reentry empty: %s" % reentry_path)
    lines.append("   [5] reentry exists non-empty: %d bytes" % rsize)
    # 6. resume prompt is not truncated (byte floor)
    if rsize < 200:
        refuse("gate check 6 failed: reentry suspiciously small (%d < 200 bytes)" % rsize)
    lines.append("   [6] reentry byte floor: %d >= 200" % rsize)
    # 7. the reentry must reference the handoff we JUST wrote
    needle = "closed/%s/handoff.yaml" % slug
    with open(reentry_path, "r") as fh:
        rtext = fh.read()
    if needle not in rtext:
        refuse("gate check 7 failed: reentry does not reference %s — regenerated from a STALE handoff" % needle)
    lines.append("   [7] reentry references THIS handoff: '%s' found" % needle)
    return lines, d


def main():
    global ROOT  # re-rooted below when this tab was ADOPTED (SPINE 2)
    if not SID or not re.fullmatch(r"[A-Za-z0-9._-]+", SID):
        refuse("--session-id missing or not filename-safe ([A-Za-z0-9._-]+)", code=2)
    if not INTENT:
        refuse("--intent-file is required (the parent writes the intent core — never delegated)", code=2)
    if not os.path.isdir(ROOT):
        refuse("project root does not exist: %s" % ROOT, code=2)

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Sidebar-name detection (identity is sidebar-name first; several projects
    # share one root). Fail-open probe: a real cmux problem is caught by the
    # fail-closed validation in step 5 — this early pass only names the close.
    # Only the human-set custom_title counts, never the dynamic title.
    ws_name = None
    ws_tag = None  # the workspace's [key:<uuid>] tag — outranks the name
    if not SKIP_CMUX and os.environ.get("CMUX_WORKSPACE_ID"):
        try:
            probe = subprocess.run([CMUX_BIN, "rpc", "workspace.list"],
                                   capture_output=True, text=True, timeout=10)
            for w in json.loads(probe.stdout).get("workspaces", []):
                if w.get("id") == os.environ["CMUX_WORKSPACE_ID"]:
                    if w.get("has_custom_title") and (w.get("custom_title") or "").strip():
                        ws_name = w["custom_title"].strip()
                    m = re.search(r"\[key:([0-9a-fA-F-]{36})\]", w.get("description") or "")
                    ws_tag = m.group(1).lower() if m else None
                    break
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError):
            ws_name = None
            ws_tag = None

    # ADOPTED-TAB RE-ROOT (SPINE 2, 2026-07-26). adopt-project.sh can bind this
    # tab to a project whose root is NOT the tab's cwd — a cmux workspace's
    # folder cannot be changed after creation, so an adopted tab is identified
    # by its [key:<uuid>] tag, not by where its shell happens to sit. Without
    # this, ROOT stays the tab's cwd and the close would: (a) fail the tag's
    # root-equality check below, (b) fall through to find_row(cwd, ws_name),
    # (c) find nothing, and (d) MINT A DUPLICATE ROW while writing the handoff
    # into the wrong folder. Re-rooting here fixes all four at once — the
    # root-equality check below then passes as the assertion it was meant to be,
    # and closed_dir / git_facts / the upsert all target the real project.
    # LOUD, never silent: the re-root is printed in the receipt path below.
    # READ-ONLY here. The D2 rule ("registry access only at step 7") governs
    # WRITES — a refused close must never park a row. load_row writes nothing,
    # so resolving identity early cannot re-open that hole.
    adopted_root_note = None
    if ws_tag:
        sys.path.insert(0, os.environ.get("CLOSE_LIB_DIR", ""))
        import registry_lib as _reg
        try:
            _tagged = _reg.load_row(ws_tag, home=REG_HOME)
        except (ValueError, json.JSONDecodeError):
            _tagged = None
        if (_tagged is not None and _tagged["status"] != "tombstoned"
                and _tagged["root_casefold"] != os.path.realpath(ROOT).casefold()
                and os.path.isdir(_tagged["root"])):
            adopted_root_note = ("ADOPTED TAB: [key:%s] binds this tab to %r rooted at %s — "
                                 "closing THAT project, not the tab's cwd %s"
                                 % (ws_tag, _tagged["name"], _tagged["root"], ROOT))
            ROOT = _tagged["root"]

    name = ws_name or os.path.basename(ROOT.rstrip(os.sep))
    # MW-A2 (found while testing MW-A, 2026-08-05): the slug was date+name only,
    # so TWO WINDOWS of one project closing on the SAME DAY produced the SAME
    # bundle directory — the second close overwrote the first window's
    # handoff.yaml and .reentry.md and DESTROYED it. Silent: exit 0, no warning.
    # MW-A cannot rescue that; the note is gone before adopt ever scans. So a
    # bundle directory is NEVER reused: suffix until free. The probe is
    # read-only, so --dry-run reports the slug the real run would use.
    base_slug = "%s-%s-close" % (date, re.sub(r"[^A-Za-z0-9._-]+", "-", name))
    closed_parent = os.path.join(ROOT, "memory", "handoffs", "closed")
    slug = base_slug
    _seq = 1
    while os.path.exists(os.path.join(closed_parent, slug)):
        _seq += 1
        slug = "%s-%d" % (base_slug, _seq)
    bundle_collision_note = None
    if slug != base_slug:
        bundle_collision_note = (
            "BUNDLE COLLISION — %s already exists (an earlier close of this project, same day). "
            "Writing %s instead so the earlier window's reentry note is NOT overwritten."
            % (base_slug, slug))
    closed_dir = os.path.join(closed_parent, slug)
    handoff_path = os.path.join(closed_dir, "handoff.yaml")
    reentry_path = os.path.join(closed_dir, "%s.reentry.md" % slug)
    stop_marker = os.path.join(STATE_DIR, "stop-%s" % SID)

    # The re-root is a fact the user must see in EVERY run, dry or real — a
    # close that targets a different folder than the shell is in must never be
    # a silent surprise.
    if adopted_root_note:
        print(adopted_root_note)
    # Same rule for a bundle collision: a close that lands in a different folder
    # than its name implies must never be a silent surprise, dry or real.
    if bundle_collision_note:
        print(bundle_collision_note)

    # Step 10 semantics: --dry-run stops BEFORE any write, including step 0.
    if DRY:
        text, na = read_intent(INTENT)  # read-only; refuses on invalid next_action
        print("DRY RUN — no writes performed (step 0 not executed)")
        print("would write stop marker: %s" % stop_marker)
        print("would write handoff:     %s" % handoff_path)
        print("would write reentry:     %s" % reentry_path)
        print("would enrich registry row for %s (home=%s) to status=parked — ONLY after the verification gate passes"
              % (("(%s, sidebar %r)" % (ROOT, ws_name)) if ws_name else ("root %s (folder-level)" % ROOT),
                 REG_HOME or "~"))
        print("would validate workspace: %s" % (
            "SKIPPED (RESURRECTION_SKIP_CMUX=1)" if SKIP_CMUX
            else (os.environ.get("CMUX_WORKSPACE_ID") or "(CMUX_WORKSPACE_ID unset — would fail closed)")))
        print("next_action (%d/90 chars): %s" % (len(na), na))
        return None

    # Step 0 — stop-<sid>: the ONLY daemon-state write, ever. Written FIRST so
    # Eternity cannot fire mid-close.
    global _STOP_MARKER_WRITTEN
    os.makedirs(STATE_DIR, exist_ok=True)
    write_file(stop_marker, "eternity-opt-out: safe-close in progress\nsession_id: %s\nat: %s\n" % (SID, now_iso))
    _STOP_MARKER_WRITTEN = stop_marker
    with open(stop_marker, "r") as fh:
        marker_bytes = len(fh.read())
    emit("step 0  stop marker: %s (%d bytes, read back)" % (stop_marker, marker_bytes))

    # Step 1 — intent core, written by the PARENT session.
    intent_text, next_action = read_intent(INTENT)
    emit("step 1  intent: %s — next_action %d/90 chars" % (INTENT, len(next_action)))

    # Step 2 — assemble co-located handoff.yaml + <slug>.reentry.md.
    git = git_facts(ROOT)
    if git:
        shown = git["dirty"][:DIRTY_LIST_CAP]
        git_state_line = "branch=%s head=%s dirty_count=%d" % (git["branch"], git["head"], git["dirty_count"])
        git_block = ("git:\n  branch: %s\n  head: %s\n  dirty_count: %d\n  dirty_listed: listed %d of %d\n"
                     % (git["branch"], git["head"], git["dirty_count"], len(shown), git["dirty_count"]))
    else:
        shown = []
        git_state_line = "non-git project (no usable git state at root)"
        git_block = "git:\n  branch: null\n  head: null\n  dirty_count: 0\n  dirty_listed: listed 0 of 0\n"
    dirty_block = "dirty_files:\n" + "".join("  - %s\n" % ln for ln in shown)
    intent_block = "intent_core: |\n" + "".join("  %s\n" % ln for ln in intent_text.splitlines())
    summary = ("Safe close of %s — %s; next: %s"
               % (name, git_state_line if git else "non-git", next_action))
    handoff_text = (
        "timestamp: %s\n" % now_iso
        + "status: parked\n"
        + "type: close-project\n"
        + "session_id: %s\n" % SID
        + "slug: %s\n" % slug
        + "project_root: %s\n" % ROOT
        + "session_summary: %s\n" % summary
        + "git_state: %s\n" % git_state_line
        + git_block
        + dirty_block
        + "next_actions:\n  - %s\n" % next_action
        + "next_action: %s\n" % next_action
        + intent_block
    )
    expected_h = hashlib.sha256(handoff_text.encode("utf-8")).hexdigest()
    rel_handoff = "memory/handoffs/closed/%s/handoff.yaml" % slug
    rel_reentry = "memory/handoffs/closed/%s/%s.reentry.md" % (slug, slug)
    reentry_text = (
        "# Reentry — %s\n\n" % slug
        + "You are reopening this project after it was closed. This is NOT a post-/clear\n"
        + "resume — days or weeks may have passed. Verify git drift before acting.\n\n"
        + "NEXT ACTION: %s\n\n" % next_action
        + "Read first, in order:\n"
        + "1. %s — the dossier for this close: intent core (decisions, rejected\n" % rel_handoff
        + "   alternatives, traps, open questions), git snapshot, next_action.\n"
        + "2. git status + git log --oneline -8 — the handoff records %s;\n" % git_state_line
        + "   anything beyond that is drift that happened after the close.\n"
        + "3. planning/ and memory/decisions/ entries named in the intent core.\n\n"
        + "Handoff: %s (sha256 %s at close)\n" % (rel_handoff, expected_h)
        + "Session that closed: %s at %s\n" % (SID, now_iso)
    )
    expected_r = hashlib.sha256(reentry_text.encode("utf-8")).hexdigest()
    write_file(handoff_path, handoff_text)
    write_file(reentry_path, reentry_text)
    emit("step 2  handoff: %s (%d bytes)" % (rel_handoff, os.stat(handoff_path).st_size))
    emit("        reentry: %s (%d bytes)" % (rel_reentry, os.stat(reentry_path).st_size))

    # Step 3 — sha256 + read-back: the on-disk bytes must hash to what was intended.
    try:
        got_h = sha256_file(handoff_path)
        got_r = sha256_file(reentry_path)
    except OSError as exc:
        refuse("read-back failed: %s" % exc)
    if got_h != expected_h:
        refuse("handoff read-back sha256 mismatch (intended %s.., disk %s..) — torn/tampered write" % (expected_h[:12], got_h[:12]))
    if got_r != expected_r:
        refuse("reentry read-back sha256 mismatch (intended %s.., disk %s..) — torn/tampered write" % (expected_r[:12], got_r[:12]))
    emit("step 3  sha256 read-back: handoff %s.. MATCH; reentry %s.. MATCH" % (got_h[:12], got_r[:12]))

    # Step 4 — blind round-trip result (optional; the verifier is SLICE-RES-22).
    degraded = False
    verdict = None
    if ROUNDTRIP:
        verdict, nstep = parse_roundtrip(ROUNDTRIP)
        if verdict == "DEGRADED":
            degraded = True
            emit("step 4  roundtrip: verdict DEGRADED (Wigum cap reached) — DEGRADED CLOSE; quote: \"%s\"" % nstep)
        else:
            emit("step 4  roundtrip: verdict PASS — reconstructed next step: \"%s\"" % nstep)
    else:
        emit("step 4  roundtrip: not provided (blind round-trip verifier is SLICE-RES-22)")

    # Step 5 — workspace validation. Fail CLOSED on anything unvalidatable;
    # never fall back to `cmux identify` (it fails open — dead surfaces exit 0).
    ws_id = None
    ws_count = None
    last_ws = False
    # D14: the LIVE workspace ids, kept for step 7. Closing ONE window must not
    # park a project other windows are still working in.
    live_ws_ids = None
    if SKIP_CMUX:
        emit("step 5  workspace validation SKIPPED (RESURRECTION_SKIP_CMUX=1) — sandbox mode")
        # Tests-only seam, same family as RESURRECTION_SKIP_CMUX / _PROJECT_ROOT:
        # sandbox mode has no cmux, so D14's "is this the LAST window" path is
        # otherwise unreachable and would ship untested. Ignored entirely
        # outside sandbox mode — the real run always uses the live list above.
        fake = os.environ.get("RESURRECTION_FAKE_WORKSPACE_IDS", "")
        if fake:
            live_ws_ids = [x.strip() for x in fake.split(",") if x.strip()]
            ws_id = os.environ.get("CMUX_WORKSPACE_ID") or (live_ws_ids[0] if live_ws_ids else None)
            emit("        sandbox liveness: %d fake workspace id%s, this one=%s"
                 % (len(live_ws_ids), "" if len(live_ws_ids) == 1 else "s", ws_id))
    else:
        ws_id = os.environ.get("CMUX_WORKSPACE_ID", "")
        if not ws_id:
            refuse("workspace unvalidatable: CMUX_WORKSPACE_ID unset — fail closed, no close instruction")
        try:
            out = subprocess.run([CMUX_BIN, "rpc", "workspace.list"],
                                 capture_output=True, text=True, timeout=10)
            payload = json.loads(out.stdout)
            workspaces = payload.get("workspaces", [])
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError) as exc:
            refuse("workspace unvalidatable: workspace.list failed (%s: %s) — fail closed" % (type(exc).__name__, exc))
        ids = [w.get("id") for w in workspaces]
        live_ws_ids = [i for i in ids if i]
        if ws_id not in ids:
            refuse("workspace unvalidatable: CMUX_WORKSPACE_ID %s not in workspace.list "
                   "(listed %d of %d workspaces) — set-but-dead env; fail closed" % (ws_id, len(ids), len(ids)))
        ours = [w for w in workspaces if w.get("id") == ws_id][0]
        win = ours.get("window_id") or ours.get("window_ref")
        if win is not None:
            group = [w for w in workspaces if (w.get("window_id") or w.get("window_ref")) == win]
            scope = "in window"
        else:
            group = workspaces  # window grouping unavailable in list payload: count all (conservative)
            scope = "total (window grouping unavailable)"
        ws_count = len(group)
        last_ws = ws_count <= 1
        emit("step 5  workspace %s validated (listed %d of %d workspaces %s; last-workspace=%s)"
             % (ws_id, ws_count, ws_count, scope, "yes" if last_ws else "no"))
        emit("        sidebar name: %s" % (repr(ws_name) if ws_name else
                                           "(none — folder-level close)"))

    # Step 6 — agent-03's 7-check verification gate (quoted verbatim above).
    gate_lines, parsed = verification_gate(handoff_path, reentry_path, slug)
    emit("step 6  verification gate (agent-03, 7 of 7 checks):")
    for gl in gate_lines:
        emit(gl)
    git_items = parsed.get("git") or []
    m_line = [it for it in git_items if it.startswith("dirty_count:")]
    total_dirty = int(m_line[0].split(":", 1)[1].strip()) if m_line else 0
    listed_dirty = len(parsed.get("dirty_files") or [])
    emit("        dirty files: listed %d of %d — NOT stashed; working tree untouched, survives close"
         % (listed_dirty, total_dirty))

    # Step 7 — registry enrich via registry_lib (the ONLY registry access path).
    # Runs ONLY NOW — after the roundtrip check, workspace validation, and the
    # 7-check gate — per agent-03's spec ("ONLY NOW write the registry row").
    # Tamper-verdict D2: the pre-fix order let a REFUSED close park the row.
    sys.path.insert(0, os.environ.get("CLOSE_LIB_DIR", ""))
    import registry_lib
    pid_path = os.path.join(ROOT, ".acos", "project-id")
    enrolled_at_close = False
    if ws_name or ws_tag:
        # Sidebar-named close: the workspace's [key:<uuid>] tag first (a
        # renamed tab must not mint a duplicate row), then the (root,
        # sidebar-name) lookup. The project-id file is the FOLDER-LEVEL
        # identity only — not consulted here.
        existing = None
        if ws_tag:
            try:
                tagged = registry_lib.load_row(ws_tag, home=REG_HOME)
            except (ValueError, json.JSONDecodeError):
                tagged = None
            if (tagged is not None and tagged["status"] != "tombstoned"
                    and tagged["root_casefold"] == os.path.realpath(ROOT).casefold()):
                existing = tagged
        if existing is None and ws_name:
            existing = registry_lib.find_row(ROOT, ws_name, home=REG_HOME)
        if existing is not None and existing["status"] == "tombstoned":
            refuse("row for (%s, %r) is tombstoned — close refused; un-tombstoning is a human act"
                   % (ROOT, ws_name))
        if existing is not None:
            project_uuid = existing["project_uuid"]
        else:
            project_uuid = str(uuid.uuid4())
            enrolled_at_close = True
    else:
        project_uuid = None
        try:
            with open(pid_path, "r") as fh:
                project_uuid = str(uuid.UUID(fh.read().strip()))
        except (OSError, ValueError):
            project_uuid = None
        stale_pointer = None
        row = registry_lib.load_row(project_uuid, home=REG_HOME) if project_uuid else None
        if row is not None and row["status"] == "tombstoned":
            stale_pointer, project_uuid, row = project_uuid, None, None
        if row is None:
            existing = registry_lib.find_by_root(ROOT, home=REG_HOME)
            if existing is not None and existing["status"] != "tombstoned":
                project_uuid = existing["project_uuid"]
            elif project_uuid is None:
                project_uuid = str(uuid.uuid4())
            enrolled_at_close = registry_lib.load_row(project_uuid, home=REG_HOME) is None
            if stale_pointer:
                write_file(pid_path, project_uuid + "\n")  # heal the tombstoned pointer
            elif not os.path.exists(pid_path):
                os.makedirs(os.path.dirname(pid_path), exist_ok=True)
                write_file(pid_path, project_uuid + "\n")
    # ---- destination picker (2026-08-18, Zee's brief) ----------------------
    # Everything above resolved the row THIS TAB belongs to. --park-to says the
    # work belongs somewhere else, so the tab's row becomes the ORPHAN and the
    # named row becomes the destination. project_uuid is the single variable the
    # rest of this close writes through — the reentry owner marker, the registry
    # last_close, and knowledge_lib.write_learnings all read it — so redirecting
    # it here moves all three together, with no second code path to keep in sync.
    orphan_uuid = None
    if PARK_TO:
        try:
            target = registry_lib.load_row(PARK_TO, home=REG_HOME)
        except (ValueError, json.JSONDecodeError):
            target = None
        if target is None:
            refuse("--park-to %s names no registry row" % PARK_TO)
        if target["status"] == "tombstoned":
            refuse("--park-to %s is tombstoned — parking into a hidden row would put "
                   "this work out of reach too" % PARK_TO)
        if PARK_TO != project_uuid:
            orphan_uuid = project_uuid
            project_uuid = PARK_TO
            emit("step 6b PARK-TO %s (%r) — this tab's work files onto that row; "
                 "its own row %s becomes the orphan"
                 % (PARK_TO, target["name"], orphan_uuid))
        else:
            emit("step 6b PARK-TO names this tab's own row — closing normally, nothing orphaned")

    # D14 — closing ONE window does not park the project. The row stays active
    # while any other window is open, and parks only when the LAST one closes.
    # Parking early would put a project Zee is still working in back on the
    # shelf, and the other window's book row would go quiet under him.
    close_status = "parked"
    other_windows_open = []
    try:
        import windows_lib
        windows_lib.release_window(project_uuid, ws_id, home=REG_HOME)
        # is_last_window, NOT a bare other_windows count: it is the one place
        # that answers UNKNOWN liveness conservatively (park, the pre-multi-
        # window behaviour) instead of leaving rows active forever whenever
        # cmux cannot be read.
        if not windows_lib.is_last_window(project_uuid, ws_id, live_ws_ids, home=REG_HOME):
            close_status = "active"
            other_windows_open = windows_lib.other_windows(project_uuid, ws_id,
                                                           live_ws_ids, home=REG_HOME)
    except (ImportError, OSError, ValueError) as exc:
        emit("        WARN window manifest unreadable (%s) — parking as usual (D14 "
             "falls back to the pre-multi-window behaviour)" % exc)

    last_close = {"at": now_iso, "handoff_path": handoff_path, "reentry_path": reentry_path,
                  "sha256": got_h, "next_action": next_action}
    fields = {"project_uuid": project_uuid, "root": ROOT, "status": close_status,
              "last_close": last_close, "last_session_id_hint": SID}
    if ws_name:
        fields["workspace_name"] = ws_name
    if git:
        fields["git"] = {"branch": git["branch"], "head": git["head"], "dirty_count": git["dirty_count"]}
    registry_lib.upsert_row(fields, home=REG_HOME)
    back = registry_lib.load_row(project_uuid, home=REG_HOME)
    if (back is None or back["status"] != close_status or back["last_close"] is None
            or back["last_close"]["sha256"] != sha256_file(handoff_path)):
        refuse("registry read-back failed: row missing, status is not %r, or last_close.sha256 "
               "does not match the on-disk handoff" % close_status)
    emit("step 7  registry row %s status=%s last_close.sha256 MATCH (read back)" % (project_uuid, back["status"]))
    # ---- step 7b: retire the orphan row (2026-08-18, Zee's ruling) ---------
    # "If a tab is not parked to any old line ... retire it." A scratch tab that
    # files its work elsewhere leaves an empty row behind, and the book fills up
    # with them. Retiring is the half that is awkward to undo, so it is GUARDED:
    # anything that looks like real history refuses the retire and says why. This
    # is the same lesson the FruitSync merge taught the same day — row a156b1b8
    # looked disposable and held 14 facts, so retiring it first would have put
    # half a project's memory out of normal reach.
    #
    # A tombstone HIDES the row and keeps the file on disk; nothing here deletes.
    if orphan_uuid:
        orphan = registry_lib.load_row(orphan_uuid, home=REG_HOME)
        blockers = []
        if orphan is None:
            blockers.append("its row is already gone")
        elif orphan["status"] == "tombstoned":
            blockers.append("it is already retired")
        else:
            if orphan.get("last_close"):
                blockers.append("it holds a previous close from %s"
                                % (orphan["last_close"].get("at") or "an earlier session"))
            try:
                import knowledge_lib as _kl
                n_facts = len(_kl.load_facts(orphan_uuid, REG_HOME))
                if n_facts:
                    blockers.append("it holds %d knowledge fact%s"
                                    % (n_facts, "" if n_facts == 1 else "s"))
            except Exception as exc:  # noqa: BLE001 — unreadable store = refuse, never retire blind
                blockers.append("its knowledge store could not be read (%s)" % type(exc).__name__)
            try:
                import windows_lib as _wl
                still = _wl.other_windows(orphan_uuid, ws_id, live_ws_ids, home=REG_HOME)
                if still:
                    blockers.append("%d other window%s still open on it"
                                    % (len(still), "" if len(still) == 1 else "s"))
            except Exception:  # noqa: BLE001 — unknown liveness is a blocker, not a green light
                blockers.append("its live-window count could not be read")
        if blockers:
            emit("step 7b orphan %s NOT retired — %s" % (orphan_uuid, "; ".join(blockers)))
            emit("        it stays in the book on purpose. Merge what it holds first "
                 "(merge-knowledge.py --from %s --into %s), then retire it yourself."
                 % (orphan_uuid, project_uuid))
        else:
            registry_lib.tombstone_row(orphan_uuid, home=REG_HOME)
            back_o = registry_lib.load_row(orphan_uuid, home=REG_HOME)
            if back_o is None or back_o["status"] != "tombstoned":
                emit("step 7b orphan %s retire NOT VERIFIED — it is still in the book"
                     % orphan_uuid)
            else:
                emit("step 7b orphan %s retired (hidden in ARCHIVED; the row file is NOT deleted)"
                     % orphan_uuid)
                registry_lib.audit_append(
                    {"event": "orphan-retired-on-park", "project_uuid": orphan_uuid,
                     "parked_to": project_uuid, "session_id": SID}, home=REG_HOME)

    if other_windows_open:
        emit("        D14: %d other window%s still open on this project — row stays ACTIVE; "
             "it parks when the LAST window closes"
             % (len(other_windows_open), "" if len(other_windows_open) == 1 else "s"))
        for o in other_windows_open:
            emit("          still open: %s" % windows_lib.describe(o))
    # Owner marker (MW-A, user brief 2026-08-04). adopt-project.sh must be able
    # to tell WHOSE note this bundle holds: several projects share one root (19
    # share this repo's), so a folder-wide scan cannot. Written here, after the
    # uuid is definitively known and AFTER the sha256-gated files — it is a
    # sibling of handoff.yaml, never part of it, so no gate hash changes.
    # Failure is non-fatal: adopt falls back to slug matching, which is what
    # every pre-marker bundle already relies on.
    owner_marker = os.path.join(closed_dir, ".project-uuid")
    try:
        write_file(owner_marker, project_uuid + "\n")
        emit("        owner marker: .project-uuid = %s (read back: %s)"
             % (project_uuid, open(owner_marker).read().strip()))
    except (OSError, IOError) as exc:
        emit("        WARN owner marker NOT written (%s) — adopt will fall back to slug matching" % exc)
    emit("        identity: %s" % (("(root, sidebar %r)" % ws_name) if ws_name else "folder-level (no sidebar name)"))
    if enrolled_at_close:
        emit("        NOTE: row was ABSENT at close — enrolled now (SessionStart enrollment should have created it)")

    # Step 8 — audit event.
    registry_lib.audit_append({"event": "close", "project_uuid": project_uuid, "session_id": SID,
                               "slug": slug, "handoff_sha256": got_h,
                               "roundtrip_verdict": verdict}, home=REG_HOME)
    emit("step 8  audit: close event appended to registry-audit.jsonl")

    # Step 8b — KB-A capture loop (user brief 2026-08-04). Additive and LAST:
    # the close is already safe by this point, so nothing here can turn a good
    # close into a failed one. Every failure path below reports and continues.
    if LEARNINGS:
        try:
            import knowledge_lib
            with open(LEARNINGS, "r", encoding="utf-8") as fh:
                candidates = json.load(fh)
            if not isinstance(candidates, list):
                raise ValueError("learnings file must be a JSON array, got %s"
                                 % type(candidates).__name__)
            prov = {"window": ws_name or "(folder-level)", "session": SID, "close_slug": slug}
            rep = knowledge_lib.write_learnings(project_uuid, candidates,
                                                provenance=prov, home=REG_HOME)
            emit("step 8b knowledge: %d written, %d already known, %d refused, "
                 "%d to ask, %d dropped"
                 % (len(rep["written"]), len(rep["duplicate"]), len(rep["refused"]),
                    len(rep["ask"]), len(rep["dropped"])))
            for w in rep["written"]:
                emit("        wrote: %s" % w["claim"][:96])
            for r in rep["refused"]:
                emit("        REFUSED (no write): %s — %s" % (r["claim"][:60], r["reason"][:90]))
            for d in rep["dropped"]:
                emit("        DROPPED: %s — %s" % (d["claim"][:60], d["reason"]))
            if rep["ask"]:
                # Kind 2 is NEVER written by this path (D4). The session asks Zee
                # in plain language and calls knowledge_lib.confirm_ruling on yes.
                emit("        ASK ZEE (%d, cap %d) — not written until he answers:"
                     % (len(rep["ask"]), knowledge_lib.KIND2_QUESTION_CAP))
                for a in rep["ask"]:
                    emit("          - %s" % a["claim"][:96])
            # NOTE: the close deliberately does NOT advance the "last seen"
            # watermark. Only a reopen does, because that is when Zee actually
            # READS the digest. Stamping it here would mark facts seen before he
            # ever saw them and D5d's after-the-fact review would show an empty
            # list forever — which is exactly how the old mining loop went quiet.
        except (OSError, ValueError, ImportError) as exc:
            emit("step 8b knowledge: SKIPPED — %s: %s (the close itself is unaffected)"
                 % (type(exc).__name__, exc))
    else:
        emit("step 8b knowledge: no --learnings-file given — nothing captured this close")

    # Step 9 — the receipt. Every line above was produced from disk read-backs.
    flush_receipt()
    print("-" * 64)
    if degraded:
        print("*** DEGRADED ROUND-TRIP — the blind verifier hit its cap; read the reentry with extra care on reopen ***")
    print("SAFE TO CLOSE THIS TAB")
    disk_na = parse_handoff(handoff_path).get("next_action", "")
    print("next action (from on-disk handoff): \"%s\"" % disk_na)
    if SKIP_CMUX:
        print("close instruction: (sandbox) workspace validation skipped — close the workspace manually in cmux")
    else:
        print("close instruction: %s rpc workspace.close '%s'"
              % (CMUX_BIN, json.dumps({"workspace_id": ws_id})))
    if not AUTO:
        print("auto-close: OFF (default) — DP2 unanswered: closing a workspace with a live "
              "Claude session has UNKNOWN behavior; run the close instruction yourself")
        return None
    if SKIP_CMUX:
        print("auto-close REFUSED: RESURRECTION_SKIP_CMUX=1 — no validated workspace target")
        return None
    if os.environ.get("RESURRECTION_DP2_CONFIRMED") != "1":
        print("auto-close REFUSED: RESURRECTION_DP2_CONFIRMED != 1 — DP2 unanswered; set it "
              "only after the user-scheduled DP2 tests")
        return None
    if last_ws:
        print("auto-close SKIPPED: this is the last workspace in its window (listed %d of %d) — "
              "closing it may close the window or quit cmux (untested)" % (ws_count, ws_count))
        return None
    cleanup_inline(ROOT)  # SessionEnd hook will not survive the kill
    print("auto-close: closing workspace %s now — the tab vanishing IS the success signal" % ws_id)
    return ws_id


APPROVED_WORKSPACE = main()
if APPROVED_WORKSPACE:
    sys.stdout.flush()
    # LITERAL LAST STATEMENT — nothing may follow; the workspace (and this process) dies here.
    subprocess.run([CMUX_BIN, "rpc", "workspace.close", json.dumps({"workspace_id": APPROVED_WORKSPACE})])
PYEOF
