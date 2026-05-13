# acos-dataroom-v2 Smoke Test

This document describes how to validate the v2 skill end-to-end before running on
real loan folders. Two layers:

1. **Python-component tests** (deterministic, automated)
2. **End-to-end skill invocation test** (requires interactive Claude Code session)

---

## Layer 1 — Python-component tests

Validates the deterministic Python helpers (`run_state.py`, `consensus_check.py`,
`build_dataroom_guide_excel.py`, `build_manual_review_md.py`) work correctly.

```bash
cd /Users/zee/Documents/Vibe\ Coding/ACOS\ 3.0/.claude/skills/acos-dataroom-v2
python3 -m unittest tests/test_smoke.py -v
```

Expected: all 12 tests PASS in <5 seconds.

If any fail, **DO NOT** proceed to the end-to-end test — fix the failing
component first.

---

## Layer 2 — End-to-end skill invocation

This actually exercises the agent swarms. Requires running inside a Claude Code
interactive session. Cannot be automated via pytest.

### Step 1 — Generate the synthetic 10-file source folder

```bash
python3 tests/generate_synthetic_source.py --output /tmp/acos_dr2_smoke_src
```

This creates a folder with:
- 3 clearly-relevant Ascent hotel docs (Property Overview, Title Commitment, T-12 P&L)
- 3 clearly-irrelevant other-property docs (Magnolia Ridge rent roll, Bay Vista
  survey, Sunset Industrial Phase I)
- 1 privileged attorney memo (HEADER: "PRIVILEGED & CONFIDENTIAL")
- 1 zero-byte placeholder file
- 1 encrypted-PDF placeholder (also zero-byte)
- 1 ambiguous file mentioning multiple properties (intended to trigger split
  deliberation → re-dispatch)

### Step 2 — Invoke the skill in Claude Code

In your Claude Code session, type:

```
/acos-dataroom-v2 --source "/tmp/acos_dr2_smoke_src" --objective "Sell the Ascent Park City hotel"
```

The skill should run end-to-end without human input. Expect 10-30 minutes for
this small test (the per-file 3-agent swarms are the dominant cost).

### Step 3 — Verify expected outputs

After the skill completes, check:

**A. Final dataroom folder location:**
- `/tmp/Ascent_Park_City_Dataroom/` (or similar asset-name-slug)

**B. Required files in the final dataroom:**

```
Ascent_Park_City_Dataroom/
├── <N> numbered sub-folders (01_..., 02_..., ...)
│   ├── Ascent_Hotel_Overview.txt           # in a "Property" or "Overview" folder
│   ├── Ascent_Title_Commitment.txt         # in a "Title" folder
│   └── Ascent_T12_PL_2023.txt              # in a "Financials" or "Operating" folder
├── <DataRoomName>_Guide_<date>.xlsx
└── Manual_Review_Required_<date>.md        # because we have encrypted + zero-byte
```

**C. Required files NOT in the dataroom:**

- `Magnolia_Ridge_Apartments_Rent_Roll.txt` — should be EXCLUDED (other property)
- `Bay_Vista_Land_Survey.txt` — should be EXCLUDED (other property)
- `Sunset_Industrial_Phase_I_ESA.txt` — should be EXCLUDED (other property)
- `PRIVILEGED_Attorney_Memo_re_Foreclosure.txt` — should be REMOVED by Phase 2.5
  (look for the asymmetric-consensus log entry in
  `<invocation_pwd>/_acos_dataroom_v2_output/run_*/phase2_5/privileged_removed.csv`
  — the audit trail lives under the working directory you invoked the skill
  FROM, not next to the source folder)
- `empty_placeholder.txt` — should be in "unable to evaluate" bucket
- `encrypted_placeholder.pdf` — should be in "unable to evaluate" bucket

**D. Manual_Review_Required.md should list:**

- `empty_placeholder.txt` (zero-byte)
- `encrypted_placeholder.pdf` (encrypted)
- `PRIVILEGED_Attorney_Memo_re_Foreclosure.txt` (informational — correctly removed)
- Possibly `2024_Q3_Portfolio_Update_Letter.txt` if it ended up in Phase 2 disputed

**E. Excel guide should have:**

- Worksheet 1 "Data Room Guide" — title "Data Room — Ascent Park City" (or similar),
  About / Folder list / Navigation / File naming / Counterparty notes sections
- Worksheet 2 "File Tree" — 3 rows for the 3 included files (Property Overview,
  Title Commitment, T-12 P&L), each with a description sentence

### Step 4 — Failure modes to watch for

If the skill HALTs, read `<invocation_pwd>/_acos_dataroom_v2_output/run_*/HALT_REPORT.md`
for the specific trigger.

If the skill completes but the dataroom looks wrong:
- Inclusion misses (relevant files excluded) → review `phase2/inclusion_log.csv`
  and the deliberation votes under `phase2/votes/<file_id>/`
- Inclusion false positives (irrelevant files included) → same logs
- Wrong sub-folder placement → check `phase4/TAXONOMY.json` + `phase4/placement_votes/`
- Privilege miss (the attorney memo ended up in the dataroom) → CRITICAL FAILURE;
  see `phase2_5/scans/<file_id>/`. This MUST work correctly before running on a
  real deal.

---

## Validation checklist

| Check | Expected | Actual |
|---|---|---|
| Layer 1 unit tests pass | 12/12 | ☐ |
| Skill runs end-to-end without HALT | yes | ☐ |
| 3 Ascent docs in dataroom | yes | ☐ |
| 3 other-property docs NOT in dataroom | yes | ☐ |
| Attorney memo NOT in dataroom (privilege caught) | yes | ☐ |
| Zero-byte + encrypted in manual-review bucket | yes | ☐ |
| Excel guide WS1 has 5 sections | yes | ☐ |
| Excel guide WS2 has descriptions for included files | yes | ☐ |
| Manual_Review_Required.md exists and lists the 3-4 expected items | yes | ☐ |

If all checks pass, the skill is ready for the Ascent run.

If ANY check fails, fix the underlying issue before running on real production data.

---

*acos-dataroom-v2 smoke test instructions.*
