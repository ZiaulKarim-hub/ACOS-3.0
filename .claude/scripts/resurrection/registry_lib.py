#!/usr/bin/env python3
"""registry_lib.py — durable per-project registry substrate (ACOS Resurrection Protocol).

Storage model (design.md, Vision 1):
  ~/.acos/registry.d/<project_uuid>.json   one file per project, one writer per file
  ~/.acos/registry-audit.jsonl             append-only, ONE os.write per line

Hard constraints honored here:
  * stdlib only, Python 3.9.6; JSON only (no yaml module exists on system python).
  * Atomic write: tempfile.mkstemp(dir=<target's own dir>) -> write -> fsync(tmp)
    -> os.replace(tmp, target) -> fsync(dir fd). NEVER a fixed .tmp name (the
    fixed-name pattern measured 180/360 torn under contention; mkstemp: 0).
  * No blocking lock (LOCK_EX) and no lock that survives SIGKILL (mkdir-lock).
  * Rows are tombstoned, never deleted; deletion is a human act only.
  * load_row fails LOUDLY on truncated/invalid JSON — never returns a partial.
  * Identity: project_uuid (uuid4, minted once at enrollment). Lookup index is
    (realpath(root).casefold(), workspace_name.casefold()) — several projects
    may share one root, distinguished by the cmux SIDEBAR name (custom_title,
    the human-set label; has_custom_title=true). workspace_name=None marks the
    folder-level row (non-cmux sessions fall back here). Re-link key is
    (st_dev, st_ino). Git facts are captured attributes, NEVER identity.
    BANNED as identity: sanitize(cwd), git remote, cmux workspace UUID,
    session UUID, and the DYNAMIC tab title (ws['title'] — programs rewrite
    it live; only the human-set custom_title may enter the lookup).
  * Every row field is derived or generated — none hand-typed.
  * Timestamps are timezone-aware UTC ISO-8601.

Every public function takes `home=None`; tests pass an override so they never
touch the real ~/.acos.

Self-test: python3 registry_lib.py --selftest [--home DIR]
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
import uuid
from datetime import datetime, timezone

STATUSES = ("active", "parked", "completed", "tombstoned")

LAST_CLOSE_KEYS = ("at", "handoff_path", "reentry_path", "sha256", "next_action")
GIT_KEYS = ("branch", "head", "dirty_count")

ROW_KEYS = (
    "project_uuid",
    "root",
    "root_casefold",
    "dev_ino",
    "name",
    "workspace_name",
    "status",
    "enrolled_at",
    "last_verified_at",
    "last_close",
    "last_session_id_hint",
    "git",
    "tombstoned_at",
    # The PERMANENT pick number (Zee's ruling, 2026-08-19). Assigned once and
    # never moved on its own; see ordinal_lib.py for the ever-issued ledger.
    # Null only on a pre-backfill row — backfill-ordinals.py fills those in.
    "pick_ordinal",
)


def _home(home=None):
    """Resolve the home root; `home` overrides so tests never touch ~/.acos."""
    return home if home else os.path.expanduser("~")


def registry_dir(home=None):
    return os.path.join(_home(home), ".acos", "registry.d")


def audit_path(home=None):
    return os.path.join(_home(home), ".acos", "registry-audit.jsonl")


def row_path(project_uuid, home=None):
    return os.path.join(registry_dir(home), "%s.json" % project_uuid)


def utc_now_iso():
    """Timezone-aware UTC ISO-8601 with explicit offset."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def atomic_write_json(path, obj):
    """Write `obj` as JSON to `path` using the mandated crash-safe pattern.

    mkstemp(dir=target's own dir) -> write -> fsync(tmp) -> os.replace(tmp,
    target) -> fsync(dir fd). The temp name is unique per call (mkstemp), so
    concurrent writers can never truncate each other's in-flight temp file —
    the failure mode that tears a fixed-.tmp scheme. A reader can only ever
    observe the previous complete file or the new complete file.
    """
    path = os.path.abspath(path)
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    data = (json.dumps(obj, indent=2) + "\n").encode("utf-8")
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".reg-", suffix=".part")
    fd_open = True
    try:
        os.write(fd, data)
        os.fsync(fd)
        os.close(fd)
        fd_open = False
        os.replace(tmp, path)
    except BaseException:
        if fd_open:
            os.close(fd)
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    dir_fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def audit_append(event, home=None):
    """Append one JSON line to the audit log with a SINGLE os.write.

    O_APPEND + one write() of one newline-terminated line means concurrent
    appenders cannot interleave bytes within a line on a local filesystem.
    The log is append-only; nothing in this library truncates or rewrites it.
    """
    if not isinstance(event, dict):
        raise TypeError("audit event must be a dict, got %r" % type(event))
    record = dict(event)
    record.setdefault("at", utc_now_iso())
    line = (json.dumps(record, separators=(",", ":")) + "\n").encode("utf-8")
    path = audit_path(home)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, line)  # exactly one write per line
    finally:
        os.close(fd)
    return record


def _validate_row(row):
    """Schema gate: exact key set, legal status, well-formed nested blocks."""
    missing = [k for k in ROW_KEYS if k not in row]
    if missing:
        raise ValueError("row missing keys: %s" % ", ".join(missing))
    extra = [k for k in row if k not in ROW_KEYS]
    if extra:
        raise ValueError("row has unknown keys: %s" % ", ".join(extra))
    if row["status"] not in STATUSES:
        raise ValueError("illegal status %r (allowed: %s)" % (row["status"], "/".join(STATUSES)))
    wn = row["workspace_name"]
    if wn is not None and (not isinstance(wn, str) or not wn.strip()):
        raise ValueError("workspace_name must be null or a non-empty string, got %r" % (wn,))
    if not (isinstance(row["dev_ino"], list) and len(row["dev_ino"]) == 2):
        raise ValueError("dev_ino must be [st_dev, st_ino], got %r" % (row["dev_ino"],))
    lc = row["last_close"]
    if lc is not None:
        if not isinstance(lc, dict) or set(lc) != set(LAST_CLOSE_KEYS):
            raise ValueError("last_close must be null or have keys %s" % (LAST_CLOSE_KEYS,))
    git = row["git"]
    if git is not None:
        if not isinstance(git, dict) or set(git) != set(GIT_KEYS):
            raise ValueError("git must be null or have keys %s" % (GIT_KEYS,))
    po = row["pick_ordinal"]
    if po is not None:
        # bool is an int subclass; True would otherwise pass as ordinal 1.
        if isinstance(po, bool) or not isinstance(po, int):
            raise ValueError("pick_ordinal must be null or an int, got %r" % (po,))
        if po <= 0:
            raise ValueError(
                "pick_ordinal must be >= 1; 0 is reserved for 'new project' "
                "(acos-safe-close/SKILL.md:235-241), got %d" % po)
    return row


def load_row(project_uuid, home=None):
    """Load one row by project_uuid. Missing file -> None.

    Truncated or otherwise invalid JSON raises (json.JSONDecodeError /
    ValueError) — a corrupt registry row must be LOUD, never a silent partial.
    """
    path = row_path(project_uuid, home)
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except FileNotFoundError:
        return None
    row = json.loads(raw.decode("utf-8"))  # raises loudly on truncation
    if not isinstance(row, dict):
        raise ValueError("row file %s is not a JSON object" % path)
    # Pre-workspace_name rows (seeded before the sidebar-name migration) lack
    # the key: default to the folder-level marker. Persisted on next upsert.
    row.setdefault("workspace_name", None)
    # Pre-ordinal rows (every row written before 2026-08-19) lack pick_ordinal.
    # Default to null rather than minting here: minting on READ would hand out
    # a number every time a book is drawn, which is the per-render counter this
    # ruling replaced. backfill-ordinals.py assigns them, once, deliberately.
    row.setdefault("pick_ordinal", None)
    return _validate_row(row)


def upsert_row(fields, home=None):
    """Create or update the row for fields['project_uuid'].

    Requires project_uuid and root. All index/derived fields (root_casefold,
    dev_ino, name) are recomputed here from the filesystem — never hand-typed.
    enrolled_at is set once at creation; last_verified_at refreshes on every
    upsert. Only optional attributes (status, last_close, git,
    last_session_id_hint) are taken from `fields`; unknown keys are rejected.
    """
    allowed_input = {"project_uuid", "root", "status", "last_close", "git",
                     "last_session_id_hint", "workspace_name"}
    unknown = set(fields) - allowed_input
    if unknown:
        raise ValueError("upsert_row got non-derivable/unknown fields: %s" % ", ".join(sorted(unknown)))
    project_uuid = fields["project_uuid"]
    root = os.path.abspath(fields["root"])

    existing = load_row(project_uuid, home)  # raises loudly if the file is corrupt
    now = utc_now_iso()

    try:
        st = os.stat(root)
        dev_ino = [st.st_dev, st.st_ino]
    except FileNotFoundError:
        if existing is None:
            raise
        dev_ino = existing["dev_ino"]  # root temporarily absent: keep re-link key

    workspace_name = fields.get(
        "workspace_name", existing["workspace_name"] if existing else None
    )
    row = {
        "project_uuid": project_uuid,
        "root": root,
        "root_casefold": os.path.realpath(root).casefold(),
        "dev_ino": dev_ino,
        # Display name: the human-set cmux sidebar name when the row has one;
        # the folder basename only for folder-level (workspace_name=None) rows.
        "name": workspace_name if workspace_name else os.path.basename(root.rstrip(os.sep)),
        "workspace_name": workspace_name,
        "status": fields.get("status", existing["status"] if existing else "active"),
        "enrolled_at": existing["enrolled_at"] if existing else now,
        "last_verified_at": now,
        "last_close": fields.get("last_close", existing["last_close"] if existing else None),
        "last_session_id_hint": fields.get(
            "last_session_id_hint", existing["last_session_id_hint"] if existing else None
        ),
        "git": fields.get("git", existing["git"] if existing else None),
        "tombstoned_at": existing["tombstoned_at"] if existing else None,
        # NEVER recomputed. An existing row keeps the number it already holds,
        # through park, active, finish and tombstone alike. Only the explicit
        # verbs in manage-ordinals.py (renumber / swap / restore / compact) may
        # move it, and only on a human's instruction.
        "pick_ordinal": existing["pick_ordinal"] if existing else None,
    }

    # A genuinely NEW row mints its number HERE rather than at each call site,
    # so every creation path — enroll-project.sh, the `add` verb, anything added
    # later — is covered by construction instead of by memory. Since 2026-08-24
    # that number is the LOWEST FREE one, not max(ever issued) + 1 (Zee: "A
    # freed number can be assigned, change that rule"); ordinal_lib owns the
    # definition of free, and counts a row in deleted/ as still holding its.
    minted = None
    if existing is None:
        import ordinal_lib  # lazy: ordinal_lib imports this module at its top
        minted = ordinal_lib.next_ordinal(home)
        row["pick_ordinal"] = minted

    _validate_row(row)
    atomic_write_json(row_path(project_uuid, home), row)
    # Ledger AFTER the row lands. A crash between the two leaves a row holding
    # an unrecorded number, which conflict-scan can see; the reverse would burn
    # an ordinal on a row that never existed and is not detectable at all.
    if minted is not None:
        import ordinal_lib
        ordinal_lib.append_event("issue", minted, project_uuid, row["name"], home)
    audit_append(
        {"event": "upsert", "project_uuid": project_uuid, "root": root,
         "status": row["status"], "pick_ordinal": row["pick_ordinal"]},
        home,
    )
    return row


def set_pick_ordinal(project_uuid, ordinal, home=None):
    """Set one row's permanent pick number. Deliberate act, never derived.

    Kept OUT of upsert_row on purpose: upsert recomputes derived fields on
    every close, park and verify, and an ordinal that could ride along on
    those writes would be a per-write counter wearing a different name.
    Callers (manage-ordinals.py) are responsible for the ledger entry — this
    function only moves the number on the row, so a caller cannot half-record
    a swap by forgetting which verb it was performing.
    """
    row = load_row(project_uuid, home)
    if row is None:
        raise KeyError("no registry row for project_uuid %s" % project_uuid)
    previous = row["pick_ordinal"]
    row["pick_ordinal"] = ordinal
    _validate_row(row)
    atomic_write_json(row_path(project_uuid, home), row)
    audit_append({"event": "set_pick_ordinal", "project_uuid": project_uuid,
                  "from": previous, "to": ordinal}, home)
    return row


def tombstone_row(project_uuid, home=None):
    """Mark a row tombstoned. NEVER unlinks — deletion is a human act only.

    Idempotent: a second tombstone keeps the original tombstoned_at.
    """
    row = load_row(project_uuid, home)
    if row is None:
        raise KeyError("no registry row for project_uuid %s" % project_uuid)
    if row["status"] != "tombstoned":
        row["status"] = "tombstoned"
        row["tombstoned_at"] = utc_now_iso()
        atomic_write_json(row_path(project_uuid, home), row)
        audit_append({"event": "tombstone", "project_uuid": project_uuid}, home)
    return row


def _iter_rows(home=None):
    """Yield every row in registry.d, loudly — a corrupt row file raises."""
    directory = registry_dir(home)
    try:
        names = sorted(n for n in os.listdir(directory) if n.endswith(".json"))
    except FileNotFoundError:
        return
    for name in names:
        yield load_row(name[: -len(".json")], home)


def rows_for_root(root, home=None):
    """All rows (any status) whose root_casefold matches realpath(root).casefold().

    Several projects may share one root (distinguished by workspace_name);
    this returns every one of them, read-only, in registry file order.
    """
    key = os.path.realpath(root).casefold()
    return [row for row in _iter_rows(home) if row["root_casefold"] == key]


def find_row(root, workspace_name=None, home=None):
    """Row lookup by (root, cmux sidebar name). Read-only — never heals.

    workspace_name=None finds the FOLDER-LEVEL row (workspace_name null) —
    the pre-migration semantics, used by non-cmux sessions. A named lookup
    casefolds both sides (sidebar names are hand-typed). Returns the row
    whatever its status; callers decide what tombstoned/completed mean.
    """
    want = workspace_name.casefold() if workspace_name else None
    for row in rows_for_root(root, home):
        have = row["workspace_name"].casefold() if row["workspace_name"] else None
        if have == want:
            return row
    return None


def find_by_root(root, home=None):
    """Folder-level row for `root`: casefold index first, then (st_dev, st_ino) heal.

    Primary index is realpath(root).casefold() (APFS is case-insensitive;
    realpath does not casefold), filtered to the folder-level row
    (workspace_name null). If NO row of any kind matches the casefold key and
    `root` exists, rows whose stored (st_dev, st_ino) match the live directory
    have merely been renamed/moved: HEAL every one of them — update
    root/root_casefold (and name, for folder-level rows only; named rows keep
    their sidebar name) in place, keeping each project_uuid — instead of ever
    tombstoning a relocated project. Returns the folder-level row or None.
    """
    matches = rows_for_root(root, home)
    if matches:
        for row in matches:
            if row["workspace_name"] is None:
                return row
        return None  # only sidebar-named rows live at this root

    try:
        st = os.stat(root)
    except FileNotFoundError:
        return None
    live = [st.st_dev, st.st_ino]
    key = os.path.realpath(root).casefold()
    folder_row = None
    for row in _iter_rows(home):
        if row["status"] == "tombstoned":
            continue
        if row["dev_ino"] == live:
            old_root = row["root"]
            new_root = os.path.abspath(root)
            row["root"] = new_root
            row["root_casefold"] = key
            if row["workspace_name"] is None:
                row["name"] = os.path.basename(new_root.rstrip(os.sep))
            row["last_verified_at"] = utc_now_iso()
            _validate_row(row)
            atomic_write_json(row_path(row["project_uuid"], home), row)
            audit_append(
                {
                    "event": "relink",
                    "project_uuid": row["project_uuid"],
                    "old_root": old_root,
                    "new_root": new_root,
                },
                home,
            )
            if row["workspace_name"] is None:
                folder_row = row
    return folder_row


# --------------------------------------------------------------------------
# Self-test. Runs entirely under a throwaway --home; refuses the real one.
# --------------------------------------------------------------------------

def _contend_worker(home, project_uuid, root, count):
    """Subprocess body for the contention storm: N upserts to ONE row file."""
    pid = os.getpid()
    for i in range(count):
        upsert_row(
            {"project_uuid": project_uuid, "root": root, "last_session_id_hint": "%d-%d" % (pid, i)},
            home=home,
        )
    return 0


def _reader_loop(path, stop, stats, lock):
    """Continuous concurrent reader: every read must decode as complete JSON."""
    while not stop.is_set():
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
            json.loads(raw.decode("utf-8"))
            ok = True
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            ok = False
        except FileNotFoundError:
            continue  # only possible before the seed write; not a tear
        with lock:
            stats["reads"] += 1
            if not ok:
                stats["torn"] += 1


def _selftest(home):
    if os.path.realpath(home) == os.path.realpath(os.path.expanduser("~")):
        print("REFUSED: selftest must run under a --home override, never the real ~")
        return 2
    results = []

    def check(name, fn):
        try:
            fn()
            results.append((name, "PASS", ""))
            print("PASS  %s" % name)
        except Exception as exc:  # noqa: BLE001 — selftest reports, then fails the run
            results.append((name, "FAIL", "%s: %s" % (type(exc).__name__, exc)))
            print("FAIL  %s -> %s: %s" % (name, type(exc).__name__, exc))

    # -- 1. atomic write pattern honored ------------------------------------
    def t_atomic():
        target = os.path.join(home, ".acos", "registry.d", "atomic-probe.json")
        atomic_write_json(target, {"k": "v", "n": 1})
        with open(target) as fh:
            assert json.load(fh) == {"k": "v", "n": 1}
        residue = [n for n in os.listdir(os.path.dirname(target)) if n.endswith(".part")]
        assert residue == [], "leftover mkstemp temp files: %s" % residue
        os.unlink(target)  # probe file, not a registry row

    check("atomic-write-pattern (mkstemp->fsync->replace->fsync(dir), no residue)", t_atomic)

    # -- 2. enrollment + schema ---------------------------------------------
    proj_root = os.path.join(home, "proj", "AlphaProject")
    os.makedirs(proj_root, exist_ok=True)
    pid_a = str(uuid.uuid4())

    def t_enroll():
        row = upsert_row({"project_uuid": pid_a, "root": proj_root}, home=home)
        assert set(row) == set(ROW_KEYS)
        assert row["status"] == "active" and row["name"] == "AlphaProject"
        assert row["enrolled_at"].endswith("+00:00") and row["last_verified_at"].endswith("+00:00")
        st = os.stat(proj_root)
        assert row["dev_ino"] == [st.st_dev, st.st_ino]
        again = load_row(pid_a, home=home)
        assert again == row

    check("enroll+schema (all fields derived, tz-aware UTC timestamps)", t_enroll)

    # -- 2b. sidebar-name rows: several projects share one root --------------
    pid_ws = str(uuid.uuid4())

    def t_workspace_name():
        row = upsert_row({"project_uuid": pid_ws, "root": proj_root,
                          "workspace_name": "Alpha Sidebar"}, home=home)
        assert row["workspace_name"] == "Alpha Sidebar" and row["name"] == "Alpha Sidebar"
        got = find_row(proj_root, "alpha sidebar", home=home)
        assert got is not None and got["project_uuid"] == pid_ws, "casefolded name lookup failed"
        folder = find_row(proj_root, None, home=home)
        assert folder is not None and folder["project_uuid"] == pid_a, "folder-level row lost"
        assert find_by_root(proj_root, home=home)["project_uuid"] == pid_a
        both = rows_for_root(proj_root, home=home)
        assert {r["project_uuid"] for r in both} == {pid_a, pid_ws}

    check("workspace-name rows (shared root, casefolded name lookup, folder row intact)", t_workspace_name)

    # -- 3. loud failure on truncated JSON ----------------------------------
    def t_truncation():
        path = row_path(pid_a, home=home)
        with open(path, "rb") as fh:
            whole = fh.read()
        with open(path, "wb") as fh:
            fh.write(whole[: len(whole) // 2])  # simulate a torn/partial file
        raised = False
        try:
            load_row(pid_a, home=home)
        except (json.JSONDecodeError, ValueError):
            raised = True
        assert raised, "truncated row file did NOT raise"
        atomic_write_json(path, json.loads(whole.decode("utf-8")))  # restore

    check("loud-truncation (half-truncated row file raises, never partial)", t_truncation)

    # -- 4. casefold lookup --------------------------------------------------
    def t_casefold():
        swapped = os.path.join(os.path.dirname(proj_root), "alphaPROJECT")
        found = find_by_root(swapped, home=home)
        # On case-sensitive filesystems the swapped-case path does not exist;
        # the index itself is still exercised with the true-case path.
        if found is None:
            found = find_by_root(proj_root.upper() if os.path.exists(proj_root.upper()) else proj_root, home=home)
        assert found is not None and found["project_uuid"] == pid_a

    check("casefold-lookup (realpath().casefold() index)", t_casefold)

    # -- 5. (st_dev, st_ino) heal after rename ------------------------------
    def t_heal():
        moved = os.path.join(home, "proj", "AlphaRenamed")
        os.rename(proj_root, moved)
        found = find_by_root(moved, home=home)
        assert found is not None, "moved root not healed"
        assert found["project_uuid"] == pid_a, "heal minted a new identity"
        assert found["root"] == moved and found["name"] == "AlphaRenamed"
        on_disk = load_row(pid_a, home=home)
        assert on_disk["root"] == moved, "heal not persisted"

    check("dev-ino-heal (rename -> re-link, uuid kept)", t_heal)

    # -- 6. tombstone never deletes -----------------------------------------
    def t_tombstone():
        row = tombstone_row(pid_a, home=home)
        assert row["status"] == "tombstoned" and row["tombstoned_at"] is not None
        first_ts = row["tombstoned_at"]
        assert os.path.exists(row_path(pid_a, home=home)), "tombstone unlinked the row file"
        again = tombstone_row(pid_a, home=home)
        assert again["tombstoned_at"] == first_ts, "tombstone not idempotent"

    check("tombstone (status+tombstoned_at set, file NEVER unlinked, idempotent)", t_tombstone)

    # -- 7. contention storm: 6 procs x 60 upserts, continuous readers -------
    storm_root = os.path.join(home, "proj", "StormProject")
    os.makedirs(storm_root, exist_ok=True)
    pid_storm = str(uuid.uuid4())
    storm_stats = {"reads": 0, "torn": 0}

    def t_storm():
        upsert_row({"project_uuid": pid_storm, "root": storm_root}, home=home)  # seed
        path = row_path(pid_storm, home=home)
        stop = threading.Event()
        lock = threading.Lock()
        readers = [
            threading.Thread(target=_reader_loop, args=(path, stop, storm_stats, lock), daemon=True)
            for _ in range(3)
        ]
        for r in readers:
            r.start()
        procs = [
            subprocess.Popen(
                [sys.executable, os.path.abspath(__file__), "--contend-worker",
                 home, pid_storm, storm_root, "60"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            for _ in range(6)
        ]
        rcs = [p.wait() for p in procs]
        stop.set()
        for r in readers:
            r.join(timeout=10)
        for p, rc in zip(procs, rcs):
            if rc != 0:
                raise AssertionError("worker rc=%d stderr=%s" % (rc, p.stderr.read().decode()[-400:]))
        final = load_row(pid_storm, home=home)  # raises if the survivor is torn
        assert final["project_uuid"] == pid_storm
        assert storm_stats["torn"] == 0, "%d torn reads of %d" % (storm_stats["torn"], storm_stats["reads"])
        assert storm_stats["reads"] > 0, "reader loop never sampled the file"
        print("      storm: 6 procs x 60 upserts = 360 writes; %d concurrent reads, %d torn"
              % (storm_stats["reads"], storm_stats["torn"]))

    check("contention-storm (6x60 -> 0 worker errors, 0 torn concurrent reads)", t_storm)

    # -- 8. audit log integrity after the storm -----------------------------
    def t_audit():
        with open(audit_path(home), "rb") as fh:
            lines = fh.read().splitlines()
        assert len(lines) >= 360, "expected >=360 audit lines, got %d" % len(lines)
        for i, line in enumerate(lines):
            rec = json.loads(line.decode("utf-8"))  # any torn line raises here
            assert "event" in rec and "at" in rec, "audit line %d missing fields" % i
        events = {}
        for line in lines:
            ev = json.loads(line.decode("utf-8"))["event"]
            events[ev] = events.get(ev, 0) + 1
        print("      audit: %d lines, all valid JSON; events=%s" % (len(lines), events))

    check("audit-integrity (every JSONL line valid after storm; O_APPEND single-write)", t_audit)

    failed = [r for r in results if r[1] == "FAIL"]
    print("\nSELFTEST %s — %d/%d passed (home=%s)"
          % ("PASS" if not failed else "FAIL", len(results) - len(failed), len(results), home))
    return 1 if failed else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--selftest", action="store_true", help="run the self-test suite")
    parser.add_argument("--home", help="home-root override (tests never touch the real ~/.acos)")
    parser.add_argument("--contend-worker", nargs=4, metavar=("HOME", "UUID", "ROOT", "N"),
                        help=argparse.SUPPRESS)  # internal: contention-storm subprocess
    args = parser.parse_args(argv)

    if args.contend_worker:
        w_home, w_uuid, w_root, w_n = args.contend_worker
        return _contend_worker(w_home, w_uuid, w_root, int(w_n))
    if args.selftest:
        home = args.home or tempfile.mkdtemp(prefix="registry-selftest-")
        return _selftest(home)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
