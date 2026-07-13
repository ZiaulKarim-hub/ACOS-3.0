#!/usr/bin/env python3
"""Append a spoken turn or chair action to <session>/transcript.md (append-only record). Mode-B SLICE-D1."""
import argparse, os, time
ap = argparse.ArgumentParser(); ap.add_argument("--session", required=True)
ap.add_argument("--who", required=True); ap.add_argument("--text", required=True); ap.add_argument("--kind", default="turn")
a = ap.parse_args(); p = os.path.join(os.path.abspath(a.session), "transcript.md")
fresh = (not os.path.exists(p)) or os.path.getsize(p) == 0
with open(p, "a", encoding="utf-8") as fh:
    if fresh: fh.write("# Committee Meeting Transcript\n\n")
    fh.write("**%s** _(%s · %s)_\n\n%s\n\n---\n\n" % (a.who, a.kind, time.strftime("%H:%M:%S"), a.text))
print("appended to", p)
