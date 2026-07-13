#!/usr/bin/env python3
"""Shared turn-cache + hashing for the SNAPPY chaired meeting (Instant room + pre-gen).

Division of labour (the one hard constraint: real generation needs the model / moderator):
  • ic-turn-daemon.py SERVES a pre-generated turn instantly from cache (no model, ~0.5s).
  • the moderator (Claude) PRE-FILLS the cache one move ahead, and generates the genuinely-new
    turns (misses) that a daemon cannot.

A cached turn for seat N is valid ONLY while the discussion has not advanced — keyed by a
`transcript hash` over the timeline. A `speak` command that carries a NEW chair argument is
ALWAYS a miss: you cannot pre-answer a point you have not seen. Stdlib only.
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import meeting_state as ms  # reuse load/save (atomic os.replace)


def transcript_hash(st):
    """Stable 16-hex digest over the spoken timeline. Changes when a turn is added -> every
    cached turn goes stale after each move (correct: seats must react to the newest turn)."""
    h = hashlib.sha256()
    for t in st.get("timeline", []):
        h.update(str(t.get("seat")).encode())
        h.update((t.get("text") or "").encode("utf-8"))
    return h.hexdigest()[:16]


def cache_dir(sess):
    d = os.path.join(sess, "turn-cache")
    os.makedirs(d, exist_ok=True)
    return d


def cache_file(sess, seat):
    return os.path.join(cache_dir(sess), "seat-%02d.json" % int(seat))


def write_cache(sess, seat, name, short, text, reactions=None, hands=None, thash=None):
    """Moderator pre-fills a seat's next turn for the CURRENT transcript."""
    if thash is None:
        thash = transcript_hash(ms.load(sess))
    e = {"seat": int(seat), "name": name, "short": short, "text": text,
         "reactions": reactions or {}, "hands": hands or [], "hash": thash}
    p = cache_file(sess, seat)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(e, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, p)
    return e


def read_valid(sess, seat, cur_hash):
    p = cache_file(sess, seat)
    if not os.path.exists(p):
        return None
    try:
        e = json.load(open(p, encoding="utf-8"))
    except Exception:
        return None
    return e if e.get("hash") == cur_hash else None


def append_turn(sess, seat, name, short, text, reactions=None, hands=None):
    """Append a spoken turn to meeting-state (same shape as meeting_state add-turn) and clear the
    thinking state. Idempotent: if the last turn is already this seat+text, do nothing (so a
    re-processed inbox line never double-appends)."""
    st = ms.load(sess)
    tl = st.setdefault("timeline", [])
    if tl and tl[-1].get("seat") == int(seat) and tl[-1].get("text") == text:
        st.pop("thinking", None)
        ms.save(sess, st)
        return st
    tl.append({"type": "turn", "seat": int(seat), "name": name, "short": short, "text": text,
               "reactions": reactions or {}, "hands": hands or []})
    st["floor"] = {"seat": int(seat), "text": text}
    st["phase"] = "in-session"
    if reactions is not None:
        st["reactions"] = reactions
    if hands is not None:
        st["hands"] = hands
    st.pop("thinking", None)
    ms.save(sess, st)
    return st


def set_thinking(sess, seat):
    """Instant feedback on a miss: the browser shows this seat typing immediately."""
    st = ms.load(sess)
    st["thinking"] = {"seat": int(seat)}
    ms.save(sess, st)
    return st


# ---- single-consumer lock: only ONE process may consume chair-inbox.jsonl at a time ----
def _inbox_owner_path(sess):
    return os.path.join(cache_dir(sess), ".inbox-owner")


def _pid_alive(pid):
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except (OSError, ValueError, TypeError):
        return False
    return True


def claim_inbox(sess, who):
    """Claim sole ownership of chair-inbox. Returns {'ok':True} if claimed, or
    {'ok':False,'owner':{...}} if another LIVE process already owns it (prevents the
    double-consume that would process every command twice → duplicate turns)."""
    p = _inbox_owner_path(sess)
    if os.path.exists(p):
        try:
            cur = json.load(open(p, encoding="utf-8"))
            opid = int(cur.get("pid", -1))
            if opid != os.getpid() and _pid_alive(opid):
                return {"ok": False, "owner": cur}
        except Exception:
            pass
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"pid": os.getpid(), "who": who}, fh)
    os.replace(tmp, p)
    return {"ok": True}


def release_inbox(sess):
    p = _inbox_owner_path(sess)
    try:
        if os.path.exists(p):
            cur = json.load(open(p, encoding="utf-8"))
            if int(cur.get("pid", -1)) == os.getpid():
                os.remove(p)
    except Exception:
        pass


def _main():
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pc = sub.add_parser("write-cache")
    for f in ("session", "seat", "name", "short", "text"):
        pc.add_argument("--" + f, required=True)
    pc.add_argument("--reactions", default=None)
    pc.add_argument("--hands", default=None)
    ph = sub.add_parser("hash"); ph.add_argument("--session", required=True)
    pl = sub.add_parser("list"); pl.add_argument("--session", required=True)
    a = ap.parse_args()
    sess = os.path.abspath(a.session)
    if a.cmd == "hash":
        print(transcript_hash(ms.load(sess))); return
    if a.cmd == "list":
        cur = transcript_hash(ms.load(sess))
        print("current transcript hash:", cur)
        for f in sorted(os.listdir(cache_dir(sess))):
            if f.startswith("seat-") and f.endswith(".json"):
                e = json.load(open(os.path.join(cache_dir(sess), f), encoding="utf-8"))
                print("  %s  seat %s  %s  %s" % (f, e.get("seat"), e.get("hash"),
                      "VALID" if e.get("hash") == cur else "stale"))
        return
    if a.cmd == "write-cache":
        reactions = json.loads(a.reactions) if a.reactions else {}
        hands = [int(x) for x in a.hands.split(",") if x.strip()] if a.hands else []
        e = write_cache(sess, a.seat, a.name, a.short, a.text, reactions, hands)
        print(json.dumps({"cached": e["seat"], "hash": e["hash"]}))


if __name__ == "__main__":
    _main()
