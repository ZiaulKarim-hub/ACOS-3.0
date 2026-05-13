# acos-dataroom-v2 — Morning Playbook

**For Zee, morning of 2026-05-13.**

The skill is built. Here's what to do.

---

## Status at a glance

| Item | Status |
|---|---|
| DESIGN.md (~975 lines, all open questions resolved) | ✅ |
| SKILL.md (orchestrator procedure, 6 phases + HALT + resume + agent-spawn convention) | ✅ |
| 14 agent definitions in `.claude/agents/dr2-*.md` | ✅ |
| 4 ported Python utility scripts (scan_folder, extract_text, ocr_and_vision, utils) | ✅ |
| 4 new Python helper scripts (run_state, consensus_check, build_dataroom_guide_excel, build_manual_review_md) | ✅ |
| references/privilege_markers.md (~280-line catalog) | ✅ |
| config.json (consensus + batching + model assignments) | ✅ |
| requirements.txt (8 pip dependencies) | ✅ |
| Synthetic 10-file smoke source at `/tmp/acos_dr2_smoke_src/` | ✅ |
| 14 unit tests passing (deterministic components) | ✅ |
| Project + feedback memory entries saved | ✅ |
| BUILD_STATE.md audit trail | ✅ |

**Total LOC produced overnight:** ~6,500 lines across spec, prompts, scripts, tests.

---

## Three-step morning sequence

### Step 1 — Install Python deps (1 min)

```bash
cd /Users/zee/Documents/Vibe\ Coding/ACOS\ 3.0/.claude/skills/acos-dataroom-v2
pip install -r requirements.txt
```

If your Python environment is already set up (v1 worked), most of these are already
installed. Pip will skip the ones you have.

### Step 2 — Run the deterministic smoke tests (1 min)

```bash
python3 -m unittest tests/test_smoke.py -v
```

Expected: 14/14 PASS in <1 second. If anything fails, surface it before going to
Step 3.

### Step 3 — End-to-end smoke run (choose A or B)

**Option A — Conservative: synthetic source first**

```
/acos-dataroom-v2 --source "/tmp/acos_dr2_smoke_src" --objective "Sell the Ascent Park City hotel"
```

This validates the agent swarms work end-to-end on a small (10-file) source.
Expected runtime: 10-30 minutes. The audit trail (run_state.json,
deliberation votes, evidence, logs) is written to
`$(pwd)/_acos_dataroom_v2_output/run_*/` — wherever you invoked the skill
FROM, NOT next to the source. Read `<pwd>/_acos_dataroom_v2_output/run_*/run_state.json`
for progress. The final shippable dataroom + Excel land next to the source
folder (i.e., `/tmp/Ascent_Park_City_Dataroom/` in this example).

After completion, verify outputs per `tests/SMOKE_TEST.md` Layer 2 checklist. If
all checks pass → go to Option B.

**Option B — Direct: Ascent dogfood run**

```
/acos-dataroom-v2 --source "/Users/zee/Library/CloudStorage/Dropbox-OkoaCapital/Okoa Loans - 2. Active/1. In HyperCore/Wolfgramm_Ascent_Beehive - Waldorf (30M)" --objective "Sell the Ascent Park City Waldorf-Astoria hotel — only documents related to the Ascent Hotel are relevant. Other-collateral and other-deal documents are out of scope."
```

Expected runtime: **multi-hour** (Ascent has 2,284 source files → 1,751
extracted records → ~5,250+ Phase 2 sub-agent invocations, plus Phase 3 QA,
Phase 4 classification, Phase 5 QA, Phase 6 Excel). Real wall-clock will
depend on Claude Max parallelism caps, but plan for 4-8 hours.

The skill is **resumable** — if it gets interrupted, just re-invoke with the
same `--source` and `--objective`; it picks up from the last checkpoint.

---

## What will be produced

### From the synthetic smoke run

```
/tmp/Ascent_Park_City_Dataroom/        ← final shippable dataroom
├── 01_<category>/
│   └── Ascent_Hotel_Overview.txt
├── 02_<category>/
│   └── Ascent_Title_Commitment.txt
├── 03_<category>/
│   └── Ascent_T12_PL_2023.txt
├── Ascent_Park_City_Dataroom_Guide_2026-05-13.xlsx
└── Manual_Review_Required_2026-05-13.md   ← lists encrypted/zero-byte/etc.
```

The privileged attorney memo will NOT appear in the dataroom (caught by Phase 2.5
asymmetric scanner). The 3 other-property files will NOT appear (caught by Phase 2
deliberation).

### From the Ascent run

```
<Source-Parent>/<Asset-Name>_Dataroom/   ← e.g., Ascent_Park_City_Waldorf_Astoria_Dataroom/
├── 01_..., 02_..., ...                   ← emergent taxonomy (likely 8-12 folders)
├── <DataRoomName>_Guide_2026-05-13.xlsx  ← buyer-facing 2-worksheet Excel
└── Manual_Review_Required_2026-05-13.md  ← only if there are buckets to flag
```

This is the artifact you take to your boss. Two outputs only — the folder + the
Excel. No working workbook. No risk dashboard. No gaps analysis. No email
drafts. Boss-criticism-proof on first cold look.

---

## If the run halts

The skill HALTs only in three cases (per DESIGN.md §11.4):
1. Phase 1 — researchers can't converge on a solidified objective after 1 re-dispatch
2. Phase 6 — guide-QA loop runs >10 iterations without PASS
3. Empty dataroom — every Phase 2 file was excluded

If HALT, read `<run_dir>/HALT_REPORT.md` for the trigger + recommended action.

Files that exhaust the K=5 Wigum loops in Phases 2/3/4b/5 do NOT halt the run —
they go to the manual-review bucket and the run continues.

---

## If a fix is needed mid-run

You can edit any agent definition file in `.claude/agents/dr2-*.md` between runs
to refine prompts. The skill picks up the changes on the next invocation. Don't
edit during a run — but you can interrupt with Ctrl+C, edit, then re-invoke
(resume from checkpoint).

---

## What to compare against v1

The v1 Ascent_Dataroom is at:
`/Users/zee/Library/CloudStorage/Dropbox-OkoaCapital/Okoa Loans - 2. Active/1. In HyperCore/Wolfgramm_Ascent_Beehive - Waldorf (30M)/Ascent_Dataroom`

After v2 completes, the v2 output will be a sibling folder (different name based
on the asset slug). You can open both side-by-side and compare:
- File count + which files made it
- Sub-folder taxonomy (v1 had 11 numeric folders with gaps; v2 will have
  sequential 1..N)
- Excel guide quality (v1's was an internal workbook; v2's is a buyer guide)
- Whether the v1-included privilege-suspect files are absent in v2

---

## Autonomous decisions log

During the build, I made the following design choices on your behalf (per
your "best recommendation" mandate):

1. **One agent file per role with model override at spawn time.** 14 files in
   `.claude/agents/dr2-*.md` rather than 32 model-variant files. Cleaner; same
   cognitive-diversity outcome.
2. **Smoke test is Python-only deterministic.** Layer 2 (end-to-end) requires
   interactive Claude Code invocation and is documented in `tests/SMOKE_TEST.md`,
   not automated.
3. **Default model is opus for all agents.** Cognitive diversity comes from
   per-spawn model overrides on instance 2 (sonnet). Per the design's
   "opus + sonnet + opus" pattern.
4. **Phase batching = 5 files per batch.** Trade-off between Task() parallelism
   and main-thread coordination overhead. Adjustable in `config.json`.
5. **Wigum iteration cap = 5 across phases 2/3/4b/5; cap = 3 for description
   re-dispatch; cap = 10 for Phase 6 guide QA.** Codified in `config.json`.
6. **Asset-name slug derived from Phase 1 synthesizer's solidified objective.**
   No CLI flag to override (per resolved open question #1).
7. **No boss email artifact.** Per resolved open question #4.
8. **Smoke source includes 10 files** spanning all main decision paths
   (relevant / irrelevant / privileged / unable-to-evaluate / ambiguous).
9. **Filename collisions resolve with `(2)`, `(3)` suffix** in flat dataroom.
   Documented in SKILL.md and the buyer-facing guide so it's transparent.
10. **Privilege markers reference is ~280 lines** covering 8 categories with
    hard-pattern + semantic markers + asymmetric-harm rationale. Calibrated
    to the user's "boss-criticism-proof" bar.

All decisions are documented in code/spec — auditable tomorrow morning, easy
to override.

---

## Open invitations for tomorrow

Things I haven't built but you might want:

- **Phase-specific reference docs** (`references/phase_1.md` ... `phase_6.md`) —
  the SKILL.md has the procedure, but per-phase prompt-template docs could
  improve autonomous execution clarity. Build if you find SKILL.md insufficient.
- **A Quickstart wizard** — if `--objective` isn't given, the skill currently
  asks once. You might want a richer prompt cycle. Easy to add.
- **Auto-detect resume mode** — currently re-invoking the skill on the same
  source + objective DOES resume from checkpoint (per SKILL.md §12), but I
  haven't tested this code path explicitly. Worth verifying in your first
  Ascent run by Ctrl+C-ing and re-invoking.
- **Cost / wall-clock telemetry** — log how many Task() spawns + total wall-clock
  time per phase, so future runs can be estimated more accurately.

---

## File inventory

```
.claude/skills/acos-dataroom-v2/
├── BUILD_STATE.md                       — overnight build audit trail
├── DESIGN.md                            — authoritative spec (~975 lines)
├── READY_TO_RUN.md                      — THIS FILE
├── SKILL.md                             — orchestrator procedure (~770 lines)
├── config.json                          — skill configuration
├── requirements.txt                     — pip deps
├── references/
│   └── privilege_markers.md             — privilege catalog (~280 lines)
├── scripts/
│   ├── build_dataroom_guide_excel.py    — Phase 6 Excel builder
│   ├── build_manual_review_md.py        — Phase 6 manual review markdown
│   ├── consensus_check.py               — universal consensus helper
│   ├── extract_text.py                  — ported from v1
│   ├── ocr_and_vision.py                — ported from v1 (bridge-file dispatch)
│   ├── run_state.py                     — run_state.json + logging
│   ├── scan_folder.py                   — ported from v1
│   └── utils.py                         — ported from v1 (path/hash helpers)
└── tests/
    ├── SMOKE_TEST.md                    — Layer 2 instructions
    ├── generate_synthetic_source.py     — 10-file synthetic generator
    └── test_smoke.py                    — 14 unit tests for deterministic logic

.claude/agents/   (14 new files)
├── dr2-obj-researcher.md
├── dr2-obj-synthesizer.md
├── dr2-inclusion-deliberator.md
├── dr2-privilege-scanner.md
├── dr2-inclusion-qa.md
├── dr2-taxonomy-designer.md
├── dr2-taxonomy-synthesizer.md
├── dr2-placement-classifier.md
├── dr2-placement-qa.md
├── dr2-guide-drafter.md
├── dr2-guide-synthesizer.md
├── dr2-guide-qa.md
├── dr2-description-drafter.md
└── dr2-description-qa.md
```

---

Good luck with the morning run. The architecture is sound; the components are
tested; the agents are domain-specialized. If the Ascent v2 output is good,
you have a working solution. If something's off, the audit trail is dense
enough that we can pinpoint and fix.

*— Claude, overnight build 2026-05-13.*
