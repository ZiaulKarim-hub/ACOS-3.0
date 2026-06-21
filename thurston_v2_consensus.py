#!/usr/bin/env python3
"""acos-dataroom-v2 — Phase 2 consensus computation."""
import os, json, glob, sys, collections

RUN_DIR = open("/Users/zee/Documents/Vibe Coding/ACOS 3.0/.thurston_v2_run_dir").read().strip()
man = {r["file_id"]: r for r in json.load(open(os.path.join(RUN_DIR, "intermediate", "scoped_manifest.json")))}
votes_dir = os.path.join(RUN_DIR, "phase2", "votes")
batches = json.load(open(os.path.join(RUN_DIR, "phase2", "batches.json")))

# round arg: which iteration's vote files to read (suffix)
rnd = sys.argv[1] if len(sys.argv) > 1 else ""   # "" = base, "r1".."r5" = re-dispatch
suffix = ("__" + rnd) if rnd else ""

# collect votes per file_id
votes = collections.defaultdict(dict)   # file_id -> {role: vote}
for b in batches:
    for role in ("del_A", "del_B", "del_C"):
        vf = os.path.join(votes_dir, f"{b['batch_id']}{suffix}__{role}.json")
        if rnd:
            vf = os.path.join(votes_dir, f"{b['batch_id']}__{rnd}__{role}.json")
        else:
            vf = os.path.join(votes_dir, f"{b['batch_id']}__{role}.json")
        if not os.path.exists(vf):
            continue
        data = json.load(open(vf))
        for fid, v in data.items():
            votes[fid][role] = v

results = {}   # file_id -> {consensus, verdicts, privilege_any, reasonings}
for fid in man:
    vs = votes.get(fid, {})
    verds = [vs[r]["verdict"].upper() for r in ("del_A", "del_B", "del_C") if r in vs]
    privs = [bool(vs[r].get("privilege_flag")) for r in ("del_A", "del_B", "del_C") if r in vs]
    reasons = {r: vs[r].get("reasoning", "") for r in vs}
    confs = [vs[r].get("confidence", 0) for r in vs]
    if len(verds) < 3:
        cons = "MISSING_VOTES"
    elif all(v == "INCLUDE" for v in verds):
        cons = "INCLUDE"
    elif all(v == "EXCLUDE" for v in verds):
        cons = "EXCLUDE"
    else:
        cons = "SPLIT"
    results[fid] = {"consensus": cons, "verdicts": verds, "privilege_any": any(privs),
                    "privilege_votes": sum(privs), "reasonings": reasons,
                    "inc_votes": verds.count("INCLUDE"), "confidences": confs}

json.dump(results, open(os.path.join(RUN_DIR, "phase2", "consensus.json"), "w"), indent=2)

tally = collections.Counter(r["consensus"] for r in results.values())
print("Phase 2 consensus:", dict(tally))
splits = [fid for fid, r in results.items() if r["consensus"] == "SPLIT"]
print(f"SPLIT files ({len(splits)}):")
for fid in splits:
    print(f"  {man[fid]['name'][:55]:57s} verdicts={results[fid]['verdicts']}")
miss = [fid for fid, r in results.items() if r["consensus"] == "MISSING_VOTES"]
if miss:
    print(f"MISSING VOTES ({len(miss)}): {[man[f]['name'] for f in miss]}")
priv = [fid for fid, r in results.items() if r["privilege_any"] and r["consensus"] == "INCLUDE"]
print(f"INCLUDE files with >=1 privilege flag (-> Phase 2.5 scrutiny): {len(priv)}")
