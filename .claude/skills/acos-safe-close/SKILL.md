---
name: acos-safe-close
description: Safe-close (park) the current project via the Resurrection Protocol close script. Thin router — the session composes the intent core itself, obtains the blind round-trip result, runs .claude/scripts/resurrection/close-project.sh, and relays the script-printed receipt VERBATIM; the model never composes receipt content. Trigger phrases: "close this project", "safe close", "park this project", "/acos-safe-close".
disable-model-invocation: false
user-invocable: true
---

# ACOS Safe Close — thin router over close-project.sh

Close = park this project so a future session (days or weeks later) can resurrect it.
ALL safety-critical logic lives in the scripts:
`.claude/scripts/resurrection/close-project.sh` (steps 0-10, guards, agent-03's
7-check verification gate) and `.claude/scripts/resurrection/roundtrip-verify.sh`
(blind-verifier adjudication, Wigum cap). This skill only routes: compose the intent
core, dispatch the blind verifier, run the close script, relay its outcome. Every
receipt line is printed BY A SCRIPT from disk read-backs.

## Hard rules (violating any one is a defect)

- NEVER compose, retype, summarize, reorder, trim, decorate, or badge a receipt line.
  Receipts reach the user only as unmodified `cat` output of the captured receipt
  file. No green badges, no checkmarks added by you.
  - SOLE EXCEPTION — the Step 7 verdict banner, which is MANDATORY and always last.
    It repeats the receipt's OWN verdict line byte-for-byte as an unmissable
    heading. It adds no words, no emoji, no checkmark, and no judgement of yours; it
    is a typographic repeat of a line the script already printed, never a substitute
    for the verbatim receipt block, which is still shown in full above it. It is
    CONDITIONAL on that exact line being present in the receipt file — see Step 7.
    A banner printed when the script did not print that line is a fabricated verdict
    and the worst defect this skill can produce.
- NEVER write to top-level `memory/handoffs/`, `memory/handoffs/archive/`, or the
  daemon state dir (`~/Library/Application Support/acos-token-monitor/state/` — the
  close script's step 0 is that dir's ONLY writer, ever). NEVER touch
  `pending-resume-*.txt` / `RESCUED-resume-*.txt`.
- NEVER author a round-trip verdict or result file yourself; the harness writes it
  from its own adjudication. A self-written PASS is a fabricated verification.
  Harness absent → no `--roundtrip-result` at all; never simulate one.
- NEVER pass `--auto-close` unless the user explicitly asked for it in this
  conversation AND the user already exported `RESURRECTION_DP2_CONFIRMED=1` (the DP2
  tests are user-scheduled; never set that variable yourself). DP2 is unanswered:
  closing a workspace holding a live Claude session has UNKNOWN behavior.
- The intent core is composed by YOU, the parent session — never delegated to a
  subagent. The blind verifier is ONE fresh general-purpose Task agent per attempt —
  never a swarm, and no new `.claude/agents/` files.

## Step 1 — Preflight

Run from the root of the project being closed.

```bash
ROOT="$(pwd)"
# This skill is global; the scripts live ONCE, in the ACOS 3.0 install. Prefer
# a local copy; else fall back to the canonical path (the same absolute path
# the enroll hook uses). ROOT stays $(pwd): close-project.sh closes THIS
# project (its own $PWD), wherever the scripts themselves live.
RESDIR="$ROOT/.claude/scripts/resurrection"
[ -f "$RESDIR/close-project.sh" ] || RESDIR="/Users/zee/Documents/Vibe Coding/ACOS 3.0/.claude/scripts/resurrection"
CLOSE="$RESDIR/close-project.sh"
HARNESS="$RESDIR/roundtrip-verify.sh"
[ -f "$CLOSE" ] || { echo "STOP: close-project.sh not found at $CLOSE"; exit 1; }
SESSION_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
# 2026-07-20 FIX — folder-vs-window session-identity bug. The old line was:
#   SID=$(basename "$(ls -t "$SESSION_DIR"/*.jsonl | head -1)" .jsonl)
# It picked the NEWEST transcript in the project FOLDER. Claude Code files every
# session of a directory into ONE folder, so when sibling sessions are live in
# the same project this returned a DIFFERENT session. close-project.sh then wrote
# stop-<wrong-sid>, silently+permanently muting another live session's eternity
# (reproduced live 2026-07-20: resolved 02e5c4f0 while the caller was 8298d84e).
# Fix: use the session id Claude Code hands to every tool call; fall back to the
# folder heuristic ONLY when unambiguous, and REFUSE to guess when it is not.
SID=""
# (1) Authoritative: Claude Code exports the running session's id to tool calls.
if [[ -n "${CLAUDE_CODE_SESSION_ID:-}" && -f "$SESSION_DIR/${CLAUDE_CODE_SESSION_ID}.jsonl" ]]; then
    SID="$CLAUDE_CODE_SESSION_ID"
fi
# (2) Fallback (older Claude Code with no such env var): newest transcript in the
#     folder — BUT only when it is unambiguous. If 2+ transcripts here are freshly
#     active (<90s), sibling sessions are live and a newest-wins guess is exactly
#     the bug above, so refuse and ask for an explicit pin instead of guessing.
if [ -z "$SID" ]; then
    _now=$(date +%s); _fresh=0
    while IFS= read -r _j; do
        [ -n "$_j" ] || continue
        _m=$(stat -f %m "$_j" 2>/dev/null || stat -c %Y "$_j" 2>/dev/null)
        [ -n "$_m" ] && [ $(( _now - _m )) -lt 90 ] && _fresh=$(( _fresh + 1 ))
    done < <(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null)
    if [ "$_fresh" -gt 1 ]; then
        echo "STOP: cannot identify this session — CLAUDE_CODE_SESSION_ID is unset and"
        echo "      $_fresh sessions in this folder are freshly active. Refusing to guess"
        echo "      (a wrong guess would mute another live session's eternity)."
        echo "      Re-run with an explicit pin:"
        echo "        CLAUDE_CODE_SESSION_ID=<your-session-id> /acos-safe-close"
        exit 1
    fi
    SID=$(basename "$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)" .jsonl)
fi
{ [ -n "$SID" ] && [ "$SID" != "." ]; } || { echo "STOP: cannot resolve session_id in $SESSION_DIR"; exit 1; }
case "$SID" in *[!a-zA-Z0-9_-]*) echo "STOP: invalid session_id: $SID"; exit 1;; esac
echo "SID=$SID"
if [ -f "$HARNESS" ]; then echo "roundtrip harness: present"; else echo "roundtrip harness: ABSENT — Step 5 will be skipped (no --roundtrip-result)"; fi
```

`SCRATCH` = the session scratchpad directory named in your system prompt
(fallback: `mktemp -d`). Each fenced block runs in its own shell — re-derive
`ROOT`/`RESDIR`/`CLOSE`/`HARNESS`/`SID`/`SCRATCH` at the top of every block you
run, carrying the same `RESDIR` fallback shown above (this skill is global; the
scripts live in ACOS 3.0). `ROOT` is always `$(pwd)` — the project being closed.

## Step 2 — Compose the intent core (yourself)

Think first: what did this session decide and why; what alternatives were rejected
and why; what traps must the reopener not fall into; what is genuinely unresolved.
GENERATE `next_action` — one imperative line, <=90 characters, the single first thing
to do on reopen. The script refuses a longer line and never truncates; regenerate
shorter instead. (Known trap: avoid the substring "stub" anywhere in `next_action` —
the gate's stub check matches it.)

```bash
cat > "$SCRATCH/safe-close-intent.txt" <<'INTENT'
next_action: <one generated imperative line, <=90 chars>
project: <project name>
decisions: |
  - <decision — and why>
rejected_alternatives: |
  - <alternative — and why it lost>
traps: |
  - <gotcha the reopener must not fall into>
open_questions: |
  - <what is genuinely unresolved>
INTENT
```

Keep `next_action:` as the first line — the script takes the first matching line.

## Step 2b — Compose this session's LEARNINGS (KB-A, optional but expected)

The intent core answers "where was I". This answers "what do I now know" — a
different job, kept in a different place (`~/.acos/knowledge/<project_uuid>/`),
and never merged into the handoff. Skip the file entirely and the close behaves
exactly as it always did.

**You do the sorting; the script gates it.** For each durable thing this session
learned, decide which kind it is:

- **Kind 1 `"machine"`** — a MACHINE could check it. File paths, file counts,
  a command that worked, a render trap, a library quirk. These are written
  **silently, always**. Zee is never asked.
- **Kind 2 `"ruling"`** — Zee's own call. Business policy, naming, what may
  leave the building, a deal fact only he holds. These are **never written
  here**; the script hands them back and you ask him in plain language about
  the DECISION, not the mechanism — at most **two** questions, ever.
  - Good: "You said we never print LendSure on broker material. Standing rule?"
  - Bad: "Record that break-before:page yields blank pages in WeasyPrint?"

**When the sorter is unsure, choose `ruling`.** An unasked Kind 2 is dropped;
a wrongly auto-written Kind 1 enters the store without Zee seeing it.

Every fact needs `evidence` or it is refused — no working shown, no write. Add
`checks` when the claim names a count, a path or a date, so it is re-verified on
every resurrect instead of quietly going stale. Set `"single_valued": true` only
when the subject holds exactly ONE true claim at a time (a count, a branch); a
subject like `traps` accumulates and must not be single-valued.

```bash
cat > "$SCRATCH/safe-close-learnings.json" <<'LEARN'
[
  {"kind": "machine", "subject": "<what it is about>",
   "claim": "<the durable fact, one sentence>",
   "evidence": {"type": "path|command|quote|observation", "value": "<the proof>"},
   "checks": [{"type": "file_count", "path": "<dir>", "expect": 0}],
   "entities": ["<tool or file the fact touches>"],
   "single_valued": true},
  {"kind": "ruling", "subject": "<area>", "claim": "<Zee's call>",
   "evidence": {"type": "quote", "value": "Zee, <date>"}}
]
LEARN
```

Check types are a fixed whitelist — `file_exists`, `file_count`,
`path_contains`, `value_matches`. A shell command is refused: the store must
never become a thing that runs code at every resurrect.

If the session learned nothing durable, skip the file. An empty capture is an
honest outcome; an invented one poisons the store.

## Step 3 — Dry-run gate (writes nothing, including step 0)

```bash
bash "$CLOSE" --intent-file "$SCRATCH/safe-close-intent.txt" --session-id "$SID" --dry-run
```

`NOT SAFE` here means the intent file is invalid (usually `next_action`): fix the
intent and re-run Step 3. Intent refusals are the ONLY fix-and-retry in this skill;
any other refusal at any step → relay it verbatim and STOP.

## Step 4 — Generation pass (writes the close artifacts)

```bash
bash "$CLOSE" --intent-file "$SCRATCH/safe-close-intent.txt" --session-id "$SID" \
  > "$SCRATCH/close-receipt-gen.txt" 2>&1; RC=$?
echo "exit=$RC"; grep -n -A 1 "^step 2" "$SCRATCH/close-receipt-gen.txt"
```

Purpose: put `memory/handoffs/closed/<slug>/handoff.yaml` and `<slug>.reentry.md` on
disk for the blind verifier. If `exit != 0`: `cat "$SCRATCH/close-receipt-gen.txt"`
verbatim and STOP — the open tab is the warning.
- Harness ABSENT: this pass IS the final pass. Apply Step 6's print rules to
  `close-receipt-gen.txt`, then go to Step 7.
- Harness present: do NOT present this receipt as final and ignore its close
  instruction — the round-trip has not run yet. Set `HY`/`RY` to the two paths on
  the receipt's `step 2` lines, prefixed with `$ROOT/` (they are repo-relative).

## Step 5 — Blind round-trip (ONE fresh Task agent per attempt, via the harness)

The verifier receives ONLY the handoff+reentry text — no paths, no repo or cwd
access, no hints — and must state the next step it reconstructed. The harness owns
prompt assembly, adjudication (derivability heuristic), the Wigum count (cap 5, then
DEGRADED — the close is never halted on cap), and writing the result file. It writes
ONLY the prompt file and the result file.

Attempt N (start at 1) — assemble the blind prompt:

```bash
bash "$HARNESS" --handoff "$HY" --reentry "$RY" --out "$SCRATCH/roundtrip-result.txt" --attempt 1
```

Then dispatch: spawn ONE fresh general-purpose Task agent whose ENTIRE prompt is the
contents of the printed `blind-prompt-attempt-1.txt` — add nothing, no repo access,
no cwd. Save the agent's reply verbatim to `$SCRATCH/roundtrip-answer-1.txt`
(heredoc is fine), then validate:

```bash
bash "$HARNESS" --handoff "$HY" --reentry "$RY" --out "$SCRATCH/roundtrip-result.txt" \
  --attempt 1 --answer "$SCRATCH/roundtrip-answer-1.txt"
```

Relay the harness output verbatim. Exit 0 with `verdict: PASS` or
`verdict: DEGRADED` → Step 6. Exit 1 (`verdict: FAIL`, Wigum retry) → re-dispatch a
FRESH Task agent with the new `blind-prompt-attempt-<N+1>.txt` and re-validate with
`--attempt <N+1>`, exactly as the harness's printed instruction says (it caps itself
at 5 → DEGRADED). Never edit the answer to make it pass; never write
`roundtrip-result.txt` yourself.

## Step 6 — Final pass + verbatim receipt

```bash
# Two explicit invocations, NOT a $LEARN_ARG variable: the interactive shell is
# zsh, and zsh does not word-split an unquoted variable — the flag and its path
# arrive glued as ONE argument and the close refuses with "unknown argument"
# (hit live 2026-08-05). An if/else cannot be mis-expanded by any shell.
if [ -f "$SCRATCH/safe-close-learnings.json" ]; then
  bash "$CLOSE" --intent-file "$SCRATCH/safe-close-intent.txt" --session-id "$SID" \
    --roundtrip-result "$SCRATCH/roundtrip-result.txt" \
    --learnings-file "$SCRATCH/safe-close-learnings.json" \
    > "$SCRATCH/close-receipt-final.txt" 2>&1; RC=$?
else
  bash "$CLOSE" --intent-file "$SCRATCH/safe-close-intent.txt" --session-id "$SID" \
    --roundtrip-result "$SCRATCH/roundtrip-result.txt" \
    > "$SCRATCH/close-receipt-final.txt" 2>&1; RC=$?
fi
cat "$SCRATCH/close-receipt-final.txt"; echo "exit=$RC"
```

(Omit `--roundtrip-result` only when the harness is absent — Step 4 already covered
that case. The final pass re-runs every script step; its receipt records the
round-trip verdict. The semantic payload — intent core, `next_action` — is unchanged
from what the verifier saw. `--learnings-file` is added only if Step 2b wrote one;
capture runs after the close is already safe and can never turn a good close into a
failed one, and re-running is harmless because facts are content-addressed.)

Present the receipt to the user as the `cat` output, whole and unmodified, inside one
fenced block. The SAFE line exists only if the script printed it.

### Step 6b — Put the Kind 2 questions to Zee (at most two)

If the receipt shows an `ASK ZEE (n, cap 2)` block, those rulings were NOT
written. Ask him about each one in plain language — about the decision, never
the mechanism — and for every "yes", record it:

```bash
RES_DIR="$RESDIR" RES_UUID="<project_uuid from the receipt's step 7 line>" \
RES_CLAIM="<his ruling, one sentence>" RES_SUBJ="<area>" python3 - <<'PY'
import os, sys
sys.path.insert(0, os.environ["RES_DIR"])
import knowledge_lib
fid, written = knowledge_lib.confirm_ruling(
    os.environ["RES_UUID"],
    {"subject": os.environ["RES_SUBJ"], "claim": os.environ["RES_CLAIM"],
     "evidence": {"type": "quote", "value": "Zee confirmed at close"}},
    home=os.environ.get("ACOS_REGISTRY_HOME") or None)
print("ruling recorded:" if written else "already known:", fid)
PY
```

A "no" writes nothing — and that is the whole point of asking. Never record a
ruling he did not give, and never re-ask past the cap.

## Step 7 — Relay the outcome

- Receipt contains `SAFE TO CLOSE THIS TAB` and `exit=0` → quote the receipt's own
  `close instruction:` line and tell the user to run it. The tab vanishing is the
  success signal. (`--auto-close` only under the Hard rules above; even then the
  script refuses on the last workspace of a window.)
- Receipt ends `NOT SAFE — ...` or `exit != 0` → relay that line verbatim and STOP.
  Do not close, do not retry (except Step 3 intent fixes and Step 5 Wigum
  re-dispatches), do not work around. The open tab is the warning.
- `DEGRADED` banner in the receipt → quote it too; the reopener must read the reentry
  with extra care.

### Step 7b — The verdict banner (MANDATORY, and it goes LAST)

The verdict is the one thing the user must not miss, and a verbatim receipt buries it
in the middle of a wall of step lines. So the reply ENDS with the verdict, rendered
unmissably. Required reply order, every time:

1. the verbatim receipt, whole and unmodified, in one fenced block
2. the `exit=` line
3. any prose you owe the user (what was verified, what is still open)
4. the receipt's own `close instruction:` line, in a copyable code block
5. **the banner — the last thing in the reply, with nothing after it**

Decide which banner MECHANICALLY, never by impression:

```bash
grep -c '^SAFE TO CLOSE THIS TAB$' "$SCRATCH/close-receipt-final.txt"   # 1 = safe
grep -n 'NOT SAFE' "$SCRATCH/close-receipt-final.txt"                    # any hit = not safe
```

**Safe** — only when that grep returns `1` AND `exit=0`. Emit exactly:

```
---

# <u>SAFE TO CLOSE THIS TAB</u>
```

**Not safe** — the grep returns `0`, or `NOT SAFE` appears, or `exit != 0`. Emit the
heading below, then the receipt's own `NOT SAFE — ...` line verbatim beneath it (if
the script printed one). Never soften it, never add a workaround:

```
---

# <u>DO NOT CLOSE THIS TAB</u>
```

**Degraded** — receipt carries the `DEGRADED` banner but is still safe: emit the SAFE
banner, then on the line under it, verbatim, the receipt's own DEGRADED line. A
degraded close is still a close; the reopener just reads the reentry harder.

Rules for the banner, all load-bearing:
- The words inside it are the script's, byte-for-byte. Add nothing — no emoji, no
  checkmark, no "✅", no "all good", no restatement in your own words.
- One `#` heading (large + bold) wrapped in `<u>…</u>` (underlined). Nothing louder,
  nothing quieter.
- NOTHING follows it. Not a question, not an offer, not a sign-off. If you owe the
  user a question, it goes in the prose at position 3.
- It NEVER replaces the verbatim receipt block. Both appear, receipt first.
- If you cannot read the receipt file to run that grep, you have no verdict to
  banner: say so plainly and emit no banner at all.

---

*ACOS Safe Close — the scripts decide; the skill relays.*
