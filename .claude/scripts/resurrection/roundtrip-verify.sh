#!/bin/bash
# roundtrip-verify.sh — SLICE-RES-22: blind round-trip verifier harness (close step 5).
#
# Interface:
#   roundtrip-verify.sh --handoff <path> --reentry <path> --out <result-path>
#                       [--attempt N] [--answer <path>]
#
# Division of labor (constraint): this script NEVER spawns Claude — Task() is
# unavailable to scripts. The /acos-safe-close SKILL dispatches ONE fresh
# general-purpose Task whose ENTIRE input is the assembled prompt file printed
# by assemble mode. That Task gets the handoff+reentry text ONLY — no repo, no
# cwd. "If it can read the repo it will pass a bad handoff" — the single most
# likely silent failure — so the repo is denied by construction.
#
# Modes:
#   assemble (no --answer): writes blind-prompt-attempt-<N>.txt next to --out —
#     handoff text VERBATIM + reentry text VERBATIM + the question — verifies
#     the embed by read-back, prints the dispatch instruction. No verdict, no
#     --out write.
#   validate (--answer <path>): checks the verifier's reply and writes the
#     result to --out; every receipt line below is printed from a READ-BACK of
#     the on-disk result, never from intent.
#
# Result file (--out) — plain-text stable line format carrying the fields
# {verdict, attempt, quoted_next_step}:
#     verdict: PASS|FAIL|DEGRADED
#     attempt: N
#     quoted_next_step: <one sentence>
#     next_step: <same sentence>
#   Line format, NOT structured JSON: the downstream consumer is
#   close-project.sh --roundtrip-result (parse_roundtrip, close-project.sh:192
#   — line-prefix parse of `verdict:` + `next_step:`), and system
#   /usr/bin/python3 is 3.9.6 with NO yaml module; handoff-adjacent files are
#   parsed by line prefix only. close-project.sh accepts ONLY PASS|DEGRADED,
#   so handing it a FAIL result refuses the close by construction.
#
# Verdicts and exit codes:
#   PASS      answer non-empty, one sentence extractable, sentence derivable
#             from the handoff (heuristic below).                      exit 0
#   FAIL      a check failed and attempt < 5 — Wigum retry.            exit 1
#   DEGRADED  a check failed at attempt >= 5 (Wigum cap): the close MAY
#             proceed, loudly marked; the close is NEVER halted on cap. exit 0
#   usage / IO / torn-write errors                                     exit 2
#
# Overlap heuristic (the load-bearing check), THRESHOLD DOCUMENTED HERE:
#   reference = the handoff's `next_action:` line + `next_actions:` items +
#   `intent*: |` literal-block lines (line-prefix parse — no yaml lib exists).
#   Answer sentence and reference are tokenized to lowercase content words
#   ([a-z0-9]{3,}) minus a stopword list that includes the question's own
#   vocabulary (state/one/sentence/next/concrete/step/work/text/...).
#   PASS requires BOTH:  matched distinct content words >= 3
#                 AND    matched / |answer content words| >= 0.40
#   Rationale: a grounded paraphrase of a real next_action clears 0.40
#   comfortably; a plausible-but-ungrounded answer against a gutted handoff
#   (intent core + next_action stripped) matches ~0 words. Permissive on
#   paraphrase, merciless on zero overlap.
#
# Writes ONLY: the prompt file (sibling of --out) and --out. Never the daemon
# state dir (that single write belongs to close-project.sh step 0 alone),
# never the registry, never memory/handoffs/.
set -euo pipefail

exec /usr/bin/python3 - "$@" <<'PYEOF'
import os, re, sys, time

WIGUM_CAP = 5          # attempt >= cap with a failing answer -> DEGRADED, never halt
RATIO_THRESHOLD = 0.40 # documented in the header block above
MIN_MATCHES = 3        # distinct matched content words required for PASS
SENTENCE_MAX = 600     # longer than this is not "one sentence"

QUESTION = ("State, in one sentence, the next concrete step of this work. "
            "You have NO other context; do not guess beyond the text.")

# Includes the question's own vocabulary so echoing the prompt earns no credit.
STOPWORDS = set("""the a an and or but of to in on at for with by from as is
are was were be been being it its this that these those then than so if not
no nor do does did done will would should shall can could may might must have
has had you your yours we our ours they their theirs he she his her him them
there here what which who whom when where why how all any both each few more
most other some such only own same very just also into over under again once
about against between through during before after above below out off up down
state one sentence next concrete step work text context guess beyond""".split())


def usage(msg):
    sys.stderr.write("roundtrip-verify: %s\n" % msg)
    sys.stderr.write("usage: roundtrip-verify.sh --handoff <path> --reentry <path> "
                     "--out <path> [--attempt N] [--answer <path>]\n")
    sys.exit(2)


def read_file(path, what):
    try:
        with open(path, "r") as fh:
            return fh.read()
    except OSError as exc:
        usage("%s unreadable: %s (%s)" % (what, path, exc))


def write_fsync(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())


def content_words(s):
    return set(w for w in re.findall(r"[a-z0-9]{3,}", s.lower()) if w not in STOPWORDS)


args = sys.argv[1:]
opt = {}
i = 0
while i < len(args):
    k = args[i]
    if k in ("--handoff", "--reentry", "--out", "--attempt", "--answer"):
        if i + 1 >= len(args):
            usage("missing value for %s" % k)
        opt[k] = args[i + 1]
        i += 2
    else:
        usage("unknown argument %r" % k)
for req in ("--handoff", "--reentry", "--out"):
    if req not in opt:
        usage("%s is required" % req)

HANDOFF = os.path.abspath(opt["--handoff"])
REENTRY = os.path.abspath(opt["--reentry"])
OUT = os.path.abspath(opt["--out"])
ANSWER = os.path.abspath(opt["--answer"]) if "--answer" in opt else None
try:
    ATTEMPT = int(opt.get("--attempt", "1"))
except ValueError:
    ATTEMPT = -1
if ATTEMPT < 1:
    usage("--attempt must be an integer >= 1")

handoff_text = read_file(HANDOFF, "handoff")
reentry_text = read_file(REENTRY, "reentry")
if not handoff_text.strip():
    usage("handoff is empty: %s" % HANDOFF)
if not reentry_text.strip():
    usage("reentry is empty: %s" % REENTRY)

# (a) assemble the blind prompt: handoff + reentry text VERBATIM + the question.
prompt_path = os.path.join(os.path.dirname(OUT), "blind-prompt-attempt-%d.txt" % ATTEMPT)
prompt_text = (
    "You are a BLIND round-trip verifier. The text below is your ONLY context:\n"
    "no repository, no working directory, no other files exist for you.\n\n"
    "=== BEGIN HANDOFF (verbatim) ===\n"
    + handoff_text + ("" if handoff_text.endswith("\n") else "\n")
    + "=== END HANDOFF ===\n\n"
    "=== BEGIN REENTRY (verbatim) ===\n"
    + reentry_text + ("" if reentry_text.endswith("\n") else "\n")
    + "=== END REENTRY ===\n\n"
    + QUESTION + "\n"
)
write_fsync(prompt_path, prompt_text)
disk_prompt = read_file(prompt_path, "assembled prompt")
if (handoff_text not in disk_prompt or reentry_text not in disk_prompt
        or QUESTION not in disk_prompt):
    sys.stderr.write("roundtrip-verify: prompt read-back failed the verbatim-embed "
                     "check: %s\n" % prompt_path)
    sys.exit(2)
print("prompt: %s (%d bytes; handoff %d bytes + reentry %d bytes embedded verbatim, read back)"
      % (prompt_path, len(disk_prompt.encode("utf-8")),
         len(handoff_text.encode("utf-8")), len(reentry_text.encode("utf-8"))))

if ANSWER is None:
    print("no --answer given: assemble-only mode — no verdict, %s not written." % OUT)
    print("DISPATCH (the skill's job — this script never spawns Claude):")
    print("  spawn ONE fresh general-purpose Task whose ENTIRE input is the contents of")
    print("  the prompt file above; grant it NO repo and NO cwd access. Save its reply")
    print("  to a file, then re-run with --answer <file> --attempt %d." % ATTEMPT)
    sys.exit(0)

# Reference lines: next_action + intent lines only — the fields a gutted
# handoff lacks. Line-prefix parse mirrors close-project.sh's writer format.
ref_lines = []
in_intent_block = False
in_next_list = False
for ln in handoff_text.splitlines():
    top = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$", ln)
    if top:
        key, val = top.group(1), top.group(2).strip()
        in_intent_block = (val == "|" and key.startswith("intent"))
        in_next_list = (key == "next_actions" and val == "")
        if key == "next_action" and val and val != "|":
            ref_lines.append(val)
        continue
    if in_intent_block and ln.strip():
        ref_lines.append(ln.strip())
    elif in_next_list and ln.strip().startswith("- "):
        ref_lines.append(ln.strip()[2:].strip())
ref_words = set()
for r in ref_lines:
    ref_words |= content_words(r)

# (b) validate the answer: non-empty -> one sentence extractable -> derivable.
answer_raw = read_file(ANSWER, "answer")
failure = None
sentence = ""
flat = re.sub(r"\s+", " ", answer_raw).strip()
if not flat:
    failure = "empty answer — the blind verifier produced nothing"
else:
    m = re.match(r"(.+?[.!?])(\s|$)", flat)
    sentence = (m.group(1) if m else flat).strip()
    if len(sentence) > SENTENCE_MAX:
        failure = ("no single sentence extractable: first sentence is %d chars "
                   "(cap %d)" % (len(sentence), SENTENCE_MAX))

answer_words = set()
matched = set()
ratio = 0.0
if failure is None:
    answer_words = content_words(sentence)
    matched = answer_words & ref_words
    ratio = (float(len(matched)) / len(answer_words)) if answer_words else 0.0
    if len(answer_words) < MIN_MATCHES:
        failure = ("answer too thin to verify: %d content words (< %d)"
                   % (len(answer_words), MIN_MATCHES))
    elif len(matched) < MIN_MATCHES or ratio < RATIO_THRESHOLD:
        failure = ("answer not derivable from the handoff: matched %d of %d answer "
                   "content words (ratio %.2f; need >= %d matches AND ratio >= %.2f) "
                   "against %d reference lines"
                   % (len(matched), len(answer_words), ratio, MIN_MATCHES,
                      RATIO_THRESHOLD, len(ref_lines)))

if failure is None:
    verdict = "PASS"
    quoted = sentence
elif ATTEMPT >= WIGUM_CAP:
    verdict = "DEGRADED"
    quoted = ("UNVERIFIED (Wigum cap %d reached): %s"
              % (WIGUM_CAP, sentence if sentence else "(no answer produced)"))
else:
    verdict = "FAIL"
    quoted = sentence if sentence else "(none)"

shown = sorted(matched)[:12]
out_lines = [
    "# blind round-trip result — written by roundtrip-verify.sh from verified read-backs",
    "verdict: %s" % verdict,
    "attempt: %d" % ATTEMPT,
    "quoted_next_step: %s" % quoted,
    "next_step: %s" % quoted,
    "checked_at: %s" % time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "prompt_file: %s" % prompt_path,
    "answer_file: %s" % ANSWER,
    "reference_lines: listed %d of %d (next_action + intent lines from the handoff)"
    % (len(ref_lines), len(ref_lines)),
    "matched_words: listed %d of %d%s"
    % (len(shown), len(matched), (": " + ", ".join(shown)) if shown else ""),
    "reason: %s" % (failure if failure else "-"),
]
write_fsync(OUT, "\n".join(out_lines) + "\n")

# Receipt: every line below comes from the on-disk result, not from intent.
disk_out = read_file(OUT, "result")
got = {}
for ln in disk_out.splitlines():
    if not ln.startswith("#") and ":" in ln:
        k, v = ln.split(":", 1)
        got.setdefault(k.strip(), v.strip())
if got.get("verdict") != verdict or got.get("attempt") != str(ATTEMPT):
    sys.stderr.write("roundtrip-verify: result read-back mismatch (torn write?): %s\n" % OUT)
    sys.exit(2)
print("result: %s (%d bytes, read back)" % (OUT, len(disk_out.encode("utf-8"))))
for key in ("verdict", "attempt", "quoted_next_step", "reference_lines",
            "matched_words", "reason"):
    for ln in disk_out.splitlines():
        if ln.startswith(key + ":"):
            print(ln)
            break

if verdict == "PASS":
    sys.exit(0)
if verdict == "DEGRADED":
    print("*** DEGRADED — Wigum cap %d reached without a verified reconstruction." % WIGUM_CAP)
    print("*** The close MAY proceed (never halted on cap) but is LOUDLY marked;")
    print("*** read the reentry with extra care on reopen.")
    sys.exit(0)
print("FAIL — Wigum retry: re-dispatch a FRESH blind Task (this was attempt %d of %d),"
      % (ATTEMPT, WIGUM_CAP))
print("then re-run with --answer <new reply> --attempt %d. A FAIL result is NOT valid"
      % (ATTEMPT + 1))
print("for close-project.sh --roundtrip-result (it accepts only PASS|DEGRADED).")
sys.exit(1)
PYEOF
