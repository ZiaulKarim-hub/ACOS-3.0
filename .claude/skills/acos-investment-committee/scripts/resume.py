#!/usr/bin/env python3
"""Resume a meeting: rebuild meeting-state.json from on-disk round files + transcript. Mode-B SLICE-D3."""
import argparse, os, subprocess, sys
CR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "committee-room")
ap = argparse.ArgumentParser(); ap.add_argument("--session", required=True); a = ap.parse_args()
r = subprocess.run([sys.executable, os.path.join(CR, "build_meeting.py"), "--session", os.path.abspath(a.session),
                    "--state-only"], capture_output=True, text=True)
sys.stdout.write(r.stdout or r.stderr)
