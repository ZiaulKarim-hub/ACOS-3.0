#!/usr/bin/env python3
"""hca-catalog-refresh.py — Phase 6: detect Hypercore schema DRIFT against the committed catalog.

Re-runs live introspection, re-harvests the active value-leaf paths, and diffs them against the
committed `catalog-paths.json` snapshot — reporting fields that Hypercore ADDED or REMOVED since the
catalog was last built. Run periodically (or before trusting the catalog for a new ask).

    doppler run --project hypercore-ask --config dev_personal -- \
        python3 .claude/skills/acos-hypercore-ask/catalog/hca-catalog-refresh.py

Exit code 0 = no drift; 1 = drift detected (details printed); 2 = could not refresh (introspection
failed — e.g. missing creds). Read-only: introspection is a single GraphQL `query`. Does NOT rewrite
the catalog — on drift, re-run hca-catalog-harvest.py + (re-probe) + hca-catalog-build.py.
"""
import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir, os.pardir, "scripts"))
_INTRO = os.path.join(_HERE, "_introspection_refresh.json")
_CAND = os.path.join(_HERE, "_candidates_refresh.json")
_SNAPSHOT = os.path.join(_HERE, "catalog-paths.json")
_VALUE_KINDS = {"money", "rate", "count", "date", "enum", "bool", "text"}


def _run(cmd, env=None):
    return subprocess.run(cmd, cwd=_HERE, env=env, capture_output=True, text=True)


def main():
    if not os.path.exists(_SNAPSHOT):
        print("FAIL: no committed catalog-paths.json — build the catalog first "
              "(hca-catalog-build.py).")
        return 2

    # 1) live introspection -> _introspection_refresh.json
    env = dict(os.environ, HCA_INTROSPECTION_OUT=_INTRO)
    r = _run([sys.executable, os.path.join(_SCRIPTS, "hca-introspect-full.py")], env=env)
    if r.returncode != 0 or not os.path.exists(_INTRO):
        print("FAIL: introspection did not complete (creds? network?). Last output:")
        print((r.stdout or "")[-400:], (r.stderr or "")[-400:])
        return 2

    # 2) re-harvest active value paths
    r = _run([sys.executable, os.path.join(_HERE, "hca-catalog-harvest.py"),
              "--introspection", _INTRO, "--depth", "4", "--out", _CAND])
    if r.returncode != 0 or not os.path.exists(_CAND):
        print("FAIL: harvest did not complete:", (r.stderr or r.stdout)[-400:])
        return 2

    fresh = json.load(open(_CAND))
    committed = json.load(open(_SNAPSHOT))
    drift = False
    print("=== Hypercore catalog drift check (vs %s) ===" % committed.get("generated_at"))
    for domain in committed["domains"]:
        fresh_paths = set(e["path"] for e in fresh["domains"][domain]["leaves"]
                          if e["tier"] == "active" and e["value_kind"] in _VALUE_KINDS)
        old_paths = set(committed["domains"][domain])
        added = sorted(fresh_paths - old_paths)
        removed = sorted(old_paths - fresh_paths)
        if added or removed:
            drift = True
            print("\n[%s] +%d added, -%d removed" % (domain, len(added), len(removed)))
            for p in added[:25]:
                print("   + %s" % p)
            if len(added) > 25:
                print("   ... +%d more added" % (len(added) - 25))
            for p in removed[:25]:
                print("   - %s" % p)
            if len(removed) > 25:
                print("   ... -%d more removed" % (len(removed) - 25))
        else:
            print("[%s] no drift (%d fields)" % (domain, len(old_paths)))

    # cleanup the refresh temporaries (regenerable)
    for f in (_INTRO, _CAND):
        try:
            os.remove(f)
        except OSError:
            pass

    if drift:
        print("\nDRIFT DETECTED — re-run harvest + probe + build to update the catalog.")
        return 1
    print("\nNo drift. Catalog is current.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
