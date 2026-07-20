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
bash "$CLOSE" --intent-file "$SCRATCH/safe-close-intent.txt" --session-id "$SID" \
  --roundtrip-result "$SCRATCH/roundtrip-result.txt" \
  > "$SCRATCH/close-receipt-final.txt" 2>&1; RC=$?
cat "$SCRATCH/close-receipt-final.txt"; echo "exit=$RC"
```

(Omit `--roundtrip-result` only when the harness is absent — Step 4 already covered
that case. The final pass re-runs every script step; its receipt records the
round-trip verdict. The semantic payload — intent core, `next_action` — is unchanged
from what the verifier saw.)

Present the receipt to the user as the `cat` output, whole and unmodified, inside one
fenced block. The SAFE line exists only if the script printed it.

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

---

*ACOS Safe Close — the scripts decide; the skill relays.*
