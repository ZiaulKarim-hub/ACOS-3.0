---
name: acos-safe-close
description: Safe-close (park) the current project via the Resurrection Protocol close script. A TYPED NUMBER IS THE DESTINATION — `/acos-safe-close 20` parks this tab's work at row 20 (the same row `/acos-resurrect 20` opens), shows `parking to: <name> @ <folder>` and waits for a typed yes. With no number it prints a SHORT menu — the likely rows (this tab's own row ranked first), `new <name>` to CREATE a brand-new row that takes the next number and replaces nothing, and `all` for the whole book — instead of the whole book every time. Thin router — the session composes the intent core itself, obtains the blind round-trip result, runs .claude/scripts/resurrection/close-project.sh, and relays the script-printed receipt VERBATIM; the model never composes receipt content. Trigger phrases: "close this project", "safe close", "park this project", "/acos-safe-close".
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
TARGETS="$RESDIR/close-targets.py"
[ -f "$CLOSE" ] || { echo "STOP: close-project.sh not found at $CLOSE"; exit 1; }
# Step 2c's destination router. Missing it must fail HERE, loudly, rather than
# half-way through a close with no way to name a destination.
[ -f "$TARGETS" ] || { echo "STOP: close-targets.py not found at $TARGETS"; exit 1; }
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
`ROOT`/`RESDIR`/`CLOSE`/`TARGETS`/`HARNESS`/`SID`/`SCRATCH` at the top of every block you
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

## Step 2a — Gather candidate learnings left by EARLIER `/clear` cycles

A long Eternity Protocol saga can leave MANY emergency handoffs in
`memory/handoffs/` before anyone ever closes — one per `/clear`. Each one may
carry its own `candidate_learnings:` list (things THAT cycle noticed — see
`handoff-agent.md`), and this session's own memory only reaches back to the
handoff it personally resumed from, not the ones before that. Run the
mechanical gatherer before you sort anything, so nothing older gets missed:

```bash
GATHER="$RESDIR/gather-candidate-learnings.py"
python3 "$GATHER" --root "$ROOT" \
  --out "$SCRATCH/gathered-candidates.json" \
  --sources-out "$SCRATCH/gathered-sources.json"
cat "$SCRATCH/gathered-candidates.json"
```

This only READS `memory/handoffs/*.yaml|*.md` and a harvested-marker directory
(`memory/handoffs/.harvested/`) — it writes nothing to the handoffs themselves,
mutates nothing, and cannot fail the close. If it finds nothing (first close,
or every handoff already harvested), `gathered-candidates.json` is `[]` — treat
that as the honest outcome it is, same as an empty Step 2b today.

## Step 2b — Compose this session's LEARNINGS (KB-A, optional but expected)

The intent core answers "where was I". This answers "what do I now know" — a
different job, kept in a different place (`~/.acos/knowledge/<project_uuid>/`),
and never merged into the handoff. Skip the file entirely and the close behaves
exactly as it always did.

**Fold in Step 2a's output.** Every item in `gathered-candidates.json` is a raw
`{claim, evidence}` pair — an earlier cycle's noticing, not yet sorted. Give
each one the SAME kind/evidence/checks treatment below as anything you
personally observed this session, and include it in the SAME
`safe-close-learnings.json` array. A raw candidate whose claim is Zee's own
call (naming, policy, a fact only he holds) is `"ruling"`, same as always —
gathering it from an old handoff does not make it any more machine-checkable
than if you'd noticed it yourself just now.

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

## Step 2c — Choose the DESTINATION (Zee's brief 2026-08-18; the number route 2026-08-24)

A close used to have exactly one destination: the row this tab is bound to. That
is wrong for a scratch tab — you open one for something unrelated, and only later
realise the work belongs with an existing project. Without a choice, the work is
filed under a stray row and the real project never learns it happened.

That fix printed the WHOLE book on every close. Zee's ruling 2026-08-24: he does
not need to read it every time. So there are now three routes into the same
`--park-to`, and the whole book is the third of them, not the first.

**A NUMBER MEANS THE SAME ROW HERE AS AT `/acos-resurrect`.** Both commands
resolve against the row's permanent `pick_ordinal`. `/acos-safe-close 20` parks
this tab's work at exactly the row `/acos-resurrect 20` would open.

**Read the argument from `<command-args>`, never by scanning the raw prompt
text.** This SKILL's own examples are expanded into the transcript, so anything
scanning raw text would read the examples below as his answer.

### Route A — a number was typed (`/acos-safe-close 20`)

Resolve it, show the confirm line, and WAIT for a yes. Zee asked for this check
himself: nothing is displayed before the write, so a slip of one digit would file
the work on the wrong project, and that is hard to notice later.

```bash
python3 "$RESDIR/close-targets.py" --resolve "<the number he typed>"; RC=$?
python3 "$RESDIR/close-targets.py" --resolve "<the number he typed>" --json > "$SCRATCH/park-target.json" 2>/dev/null
echo "exit=$RC"
```

Show that `parking to:` block verbatim, then ask in plain text for a typed
`yes`. `REFUSED` (exit 1) is the outcome — relay it and ask again; never guess a
neighbouring number. The script refuses a tombstoned or completed target itself.

On `yes`, take `project_uuid` from `park-target.json` and build the array below.
On anything else, do not park — offer Route B.

### Route B — no number was typed

Print the SHORT menu. It ranks the likely rows by evidence about THIS tab, and
carries the two standing choices:

```bash
python3 "$RESDIR/close-targets.py" > "$SCRATCH/close-menu.txt" 2>&1; RC=$?
cat "$SCRATCH/close-menu.txt"; echo "exit=$RC"
```

Show the `cat` output whole and unmodified in ONE fenced block — same relay rule
as `/acos-resurrect`. The script computes the ranking; you add nothing to it.
Then take a typed reply:

- **a number** → Route A's resolve + confirm, then park there. This tab's own
  row is not a separate choice: when it exists, the menu ranks it FIRST under
  choice 1, so filing onto it is just typing its number.
- **`new <name>`** → create a brand-new row. See Route D.
- **`all`** → Route C.

### Route C — `all`, the whole book

```bash
python3 "$RESDIR/resurrect-view.py" --color never > "$SCRATCH/close-book.txt" 2>&1; RC=$?
python3 "$RESDIR/resurrect-view.py" --json      > "$SCRATCH/close-book.json" 2>/dev/null
cat "$SCRATCH/close-book.txt"; echo "exit=$RC"
```

Show the `cat` output whole and unmodified in ONE fenced block. Then ask, in
plain text, for a typed reply:

> Park this tab's work where? Type the NUMBER of a project above, or
> `new <name>` for a brand-new row of its own.

`new <name>` routes to Route D. Resolve a numeric reply against `close-book.json`'s
`pick_number` EXACTLY — never re-count the printed rows yourself. Ambiguous or
out-of-range → say so and ask again; NEVER guess between two rows.

### Route D — `new <name>`, a brand-new row

Zee's ruling 2026-08-24: *"the intention was not to replace anything, just to
create a new row in an empty number."* So this MINTS. It never orphans, never
retires, and never touches whatever row this tab already owns.

```bash
PARK_ARGS=(--park-to-new "<the name he typed>")
```

The script does the rest and prints what it did:

- The new row takes `next_ordinal` — the LOWEST number no row holds (Zee's
  ruling 2026-08-24). It DOES fill a gap. A row waiting in `registry.d/deleted/`
  still counts as holding its number, so this can never take a number `restore`
  is going to want back; only `purge` truly frees one. Say the number the
  receipt prints; do not predict one.
- A name already used at this root is REFUSED, naming the row that holds it and
  its number. Creating is not reusing. Relay the refusal and ask for another
  name — never fall back to filing onto the existing row.
- `--park-to` and `--park-to-new` together are REFUSED. Pass exactly one.
- If this tab owned NO row, `.acos/project-id` is repointed at the new row, so
  the folder's identity names something that exists. The receipt says so.

If he asks for a new row without giving a name, ask for one. A row at this root
needs its own sidebar name to be a separate row at all — an unnamed one would
collide with the folder-level row this tab already resolves to.

### Building the flag (all four routes end here)

Build it ONCE, as an ARRAY, and reuse it in every later invocation:

```bash
# Nothing chosen (no argument, no menu answer) -> leave the array EMPTY. That is
# today's behaviour: the close lands on the row this tab already resolves to.
PARK_ARGS=()
# A number was picked and confirmed -> set it, using the uuid the resolve printed:
PARK_ARGS=(--park-to "<project_uuid of the picked row>")
# `new <name>` was chosen -> mint instead of resolve:
PARK_ARGS=(--park-to-new "<the name he typed>")
```

An ARRAY, not a string. This file already records why: the interactive shell is
zsh, and zsh does not word-split an unquoted string variable, so `$LEARN_ARG`
once arrived as ONE glued argument and the close refused it. `"${PARK_ARGS[@]}"`
is a different mechanism — it expands to zero or two separate words in bash AND
zsh — so it is safe where the string was not.

**Ask with a plain typed reply, NOT `AskUserQuestion`.** Autopilot answers that tool
by itself, and an auto-answered destination would file real work onto a project Zee
never chose — the failure this step exists to prevent, arriving by a different door.
This holds for Route A's `yes` as much as for the menu itself: an auto-answered
confirmation is not a confirmation.

**What a destination pick does.** The reentry note, the registry `last_close`, and
the captured learnings all land on the PICKED row instead of this tab's own row.
This tab's row then becomes the ORPHAN and `close-project.sh` step 7b retires it —
but only when it is genuinely empty. A row holding knowledge facts, an earlier
close, or another live window REFUSES the retire and prints why, naming
`merge-knowledge.py` as the thing to run first. Relay that refusal; never work
around it. Retiring means `tombstone`: the row is hidden in ARCHIVED and the row
file is never deleted.

**What `--park-to-new` does NOT do.** It does not orphan, retire, tombstone or
rename anything. That is the one behavioural difference from `--park-to`, and it
is deliberate: `--park-to` means "this work was really THAT project's", which
makes the tab's own row a leftover worth retiring; `--park-to-new` means "this
work is its own project now", which says nothing at all about the old row.

## Step 3 — Dry-run gate (writes nothing, including step 0)

```bash
bash "$CLOSE" --intent-file "$SCRATCH/safe-close-intent.txt" --session-id "$SID" \
  "${PARK_ARGS[@]}" --dry-run
```

`NOT SAFE` here means the intent file is invalid (usually `next_action`): fix the
intent and re-run Step 3. Intent refusals are the ONLY fix-and-retry in this skill;
any other refusal at any step → relay it verbatim and STOP.

## Step 4 — Generation pass (writes the close artifacts)

```bash
bash "$CLOSE" --intent-file "$SCRATCH/safe-close-intent.txt" --session-id "$SID" \
  "${PARK_ARGS[@]}" \
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
    "${PARK_ARGS[@]}" \
    > "$SCRATCH/close-receipt-final.txt" 2>&1; RC=$?
else
  bash "$CLOSE" --intent-file "$SCRATCH/safe-close-intent.txt" --session-id "$SID" \
    --roundtrip-result "$SCRATCH/roundtrip-result.txt" \
    "${PARK_ARGS[@]}" \
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

### Step 6c — Mark the gathered handoffs harvested (ONLY on a safe close)

Skip this step entirely if Step 2a's `gathered-sources.json` is `[]` or absent,
or if the close was NOT safe (below). Marking is a receipt-not-a-promise:
do it only once the close this session just ran has actually succeeded, so a
refused/`NOT SAFE` close never marks handoffs as consumed when their learnings
were never actually written anywhere.

```bash
if grep -qc '^SAFE TO CLOSE THIS TAB$' "$SCRATCH/close-receipt-final.txt" 2>/dev/null \
   && [ -s "$SCRATCH/gathered-sources.json" ]; then
  python3 "$RESDIR/gather-candidate-learnings.py" --mark-harvested --root "$ROOT" \
    --sources "$SCRATCH/gathered-sources.json"
fi
```

This is why Step 2a's gather runs BEFORE this session's own Step 2b sorting,
but marking runs AFTER the final receipt: the candidates must survive to be
sorted and written, and marking must never race ahead of that.

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
