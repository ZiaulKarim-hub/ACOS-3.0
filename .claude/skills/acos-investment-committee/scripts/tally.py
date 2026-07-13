#!/usr/bin/env python3
"""Interim/final tally: run the deterministic chain (build_facts -> run_synthesis -> verdict). Mode-B SLICE-D2."""
import argparse, json, os, subprocess, sys
SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument("--session", required=True); a = ap.parse_args()
sess = os.path.abspath(a.session)
for script, extra in [("build_facts.py", ["--round", "all"]), ("run_synthesis.py", []), ("verdict.py", [])]:
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), "--session", sess] + extra,
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("[tally] %s failed: %s" % (script, (r.stderr or "").strip()[:200]), file=sys.stderr)
v = os.path.join(sess, "verdict.json")
if os.path.exists(v):
    d = json.load(open(v))
    print(json.dumps({"verdict": d.get("verdict"), "deal_breakers": len(d.get("deal_breakers", []) or []),
                      "kill_findings": len(d.get("kill_findings", []) or [])}))
else:
    print(json.dumps({"verdict": "UNRESOLVED", "note": "no verdict.json yet"}))
