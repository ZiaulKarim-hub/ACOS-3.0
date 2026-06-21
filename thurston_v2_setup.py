#!/usr/bin/env python3
"""acos-dataroom-v2 scoped run — setup: run dir, scoped manifest, source shape."""
import os, json, hashlib, datetime, sys
sys.path.insert(0, "/Users/zee/Documents/Vibe Coding/ACOS 3.0")
import thurston_dataroom_classify as v1

SOURCE = "/Users/zee/Thurston Staging"
INVOCATION_DIR = "/Users/zee/Documents/Vibe Coding/ACOS 3.0"
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
h = hashlib.sha256(SOURCE.encode()).hexdigest()[:8]
RUN_ID = f"run_{ts}_{h}"
RUN_DIR = os.path.join(INVOCATION_DIR, "_acos_dataroom_v2_output", RUN_ID)

for sub in ["phase1/proposals", "phase2/votes", "phase2/disputed", "phase2_5",
            "phase3", "phase6", "intermediate", "extraction", "logs"]:
    os.makedirs(os.path.join(RUN_DIR, sub), exist_ok=True)

# --- scoped manifest: v1 INCLUDE + REVIEW files (decision-relevant) ----------
src_rows = []
for r in v1.SRC_ROOTS:
    src_rows += v1.walk(r)

scoped, prebucket = [], []
for (root, rel, name) in src_rows:
    verdict, item, cat, rationale, sens, conf = v1.classify(root + "/" + rel)
    fid = "f_" + hashlib.sha256((root + "/" + rel).encode()).hexdigest()[:12]
    rec = {"file_id": fid, "loan": "Lux II" if root == "Thurston Lux 2" else "Haystack",
           "root": root, "relpath": rel, "name": name,
           "abspath": os.path.join(SOURCE, root, rel),
           "folder": os.path.dirname(rel) or "(root)",
           "v1_verdict": verdict, "v1_item": item, "v1_category": cat}
    if verdict in ("INCLUDE", "REVIEW"):
        scoped.append(rec)
    else:
        prebucket.append({**rec, "prebucket_reason": rationale})

with open(os.path.join(RUN_DIR, "intermediate", "scoped_manifest.json"), "w") as f:
    json.dump(scoped, f, indent=2)
with open(os.path.join(RUN_DIR, "intermediate", "prebucketed_exclude.json"), "w") as f:
    json.dump(prebucket, f, indent=2)

# --- source shape (Phase 1 input) -------------------------------------------
shape = {"source": SOURCE, "loan_folders": {}}
for r in v1.SRC_ROOTS:
    base = os.path.join(SOURCE, r)
    folders = {}
    for dp, _, files in os.walk(base):
        rel = os.path.relpath(dp, base)
        n = len([x for x in files if x not in (".DS_Store",)])
        if rel == ".":
            rel = "(root)"
        folders[rel] = n
    shape["loan_folders"][r] = {"top_folders": sorted(folders.items())}
high_signal = [rec["name"] for rec in scoped if any(
    k in rec["name"].lower() for k in ["loan agreement", "note", "term sheet", "mortgage",
                                       "deed of trust", "guarant"])][:12]
shape["high_signal_filenames"] = high_signal
with open(os.path.join(RUN_DIR, "phase1", "source_shape.json"), "w") as f:
    json.dump(shape, f, indent=2)

# --- run state ---------------------------------------------------------------
state = {"run_id": RUN_ID, "source": SOURCE,
         "objective_brief": "Prepare the existing OKOA loan-document package for the takeout "
         "lender that will pay off OKOA's Thurston (Lux II + Haystack) loan at closing.",
         "started_at": datetime.datetime.now().isoformat(),
         "phase": "0_setup", "last_completed_checkpoint": None,
         "skill_version": "v2.0.0", "run_mode": "scoped-advisory",
         "scoped_files": len(scoped), "prebucketed_exclude": len(prebucket)}
with open(os.path.join(RUN_DIR, "run_state.json"), "w") as f:
    json.dump(state, f, indent=2)

# pointer file so later steps find the run dir
with open(os.path.join(INVOCATION_DIR, ".thurston_v2_run_dir"), "w") as f:
    f.write(RUN_DIR)

print("RUN_DIR:", RUN_DIR)
print("scoped (decision-relevant):", len(scoped))
print("pre-bucketed EXCLUDE:", len(prebucket))
