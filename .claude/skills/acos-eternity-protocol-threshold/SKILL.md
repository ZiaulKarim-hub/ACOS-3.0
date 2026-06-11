---
name: acos-eternity-protocol-threshold
description: Sets the auto-fire threshold for the eternity protocol. Edits ~/Library/Application Support/acos-token-monitor/config.yaml so the daemon acts when the token count crosses the new value. The daemon dispatches by SESSION VARIANT — it fires /acos-eternity-protocol-cmux for cmux sessions; for warp sessions it only logs that manual invocation is required (auto-fire disabled 2026-06-04). The retired /acos-eternity-protocol skill is no longer dispatched. Hot-reloads — no daemon restart needed. Usage. /acos-eternity-protocol-threshold 350000
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash
---

# ACOS Eternity Protocol Threshold

## Overview

Convenience skill to change the eternity-protocol auto-fire threshold without
remembering the YAML path.

When the token count crosses the threshold, the token-watcher daemon dispatches
by **session variant**: for cmux sessions it fires
`/acos-eternity-protocol-cmux`; for warp sessions it only logs that manual
invocation is required (warp auto-fire was disabled 2026-06-04 due to the
AXTitle marker race). The legacy `/acos-eternity-protocol` skill was retired
2026-05-28 and is no longer dispatched.

The token-watcher daemon hot-reloads its config when the file mtime changes,
so the new threshold takes effect immediately on the next event.

Note: the `fire_command` field in `config.yaml` is **informational-only** — the
daemon's dispatch is variant-based and ignores `fire_command` entirely.

## Usage

```
/acos-eternity-protocol-threshold <number>
```

Example:
```
/acos-eternity-protocol-threshold 350000   ← fire at 350k tokens
/acos-eternity-protocol-threshold 200000   ← aggressive
/acos-eternity-protocol-threshold 500000   ← lazy
```

If invoked with no argument, prints the current threshold.

## Protocol

### Step 1: Parse and validate the argument

```bash
NEW_THRESHOLD=$(echo "$ARGUMENTS" | tr -d ', \t\n\r')

# HARD GATE before this value reaches the sed substitution in Step 2. Without
# it, a non-numeric or sed-metacharacter argument (`/`, `&`, `\`) would corrupt
# the config.yaml that the daemon hot-reloads — directly breaking the auto-loop.
# Require a pure integer (no signs, no decimals, no metachars).
[[ "$NEW_THRESHOLD" =~ ^[0-9]+$ ]] || { echo "ERROR: threshold must be a positive integer (got: '$ARGUMENTS')"; exit 1; }

# Lower-bound sanity: a tiny threshold would make the daemon fire on almost
# every event — a smoothness hazard (constant /clear churn). Reject < 10000.
if [[ "$NEW_THRESHOLD" -lt 10000 ]]; then
    echo "ERROR: threshold $NEW_THRESHOLD is too small (< 10000) — would make the daemon fire constantly."
    echo "       Use a realistic value (default 400000; see the guidance table below)."
    exit 1
fi

# Soft upper/odd-range warnings — apply anyway (these are valid integers).
if [[ "$NEW_THRESHOLD" -lt 50000 ]]; then
    echo "WARN: threshold $NEW_THRESHOLD is unusually aggressive (< 50000) — applying anyway."
elif [[ "$NEW_THRESHOLD" -gt 950000 ]]; then
    echo "WARN: threshold $NEW_THRESHOLD effectively disables auto-fire (> 950000) — applying anyway."
fi
```

- Must parse to a positive integer (enforced above — rejects non-numeric and
  sed-metacharacter input before it can corrupt config.yaml)
- Hard-rejects < 10000 (constant-fire smoothness hazard)
- Soft-warns on < 50,000 or > 950,000 but applies anyway

### Step 2: Update the YAML

Each fenced bash block runs in its OWN shell, so `$NEW_THRESHOLD` validated in
Step 1 is empty here. Re-derive AND re-validate it before it reaches `sed` —
the validation is what protects config.yaml from a corrupting substitution, so
it must live in the same block that runs the `sed`.

```bash
NEW_THRESHOLD=$(echo "$ARGUMENTS" | tr -d ', \t\n\r')
# Re-validate in this block (self-contained guard right before sed).
[[ "$NEW_THRESHOLD" =~ ^[0-9]+$ ]] || { echo "ERROR: threshold must be a positive integer (got: '$ARGUMENTS')"; exit 1; }
[[ "$NEW_THRESHOLD" -ge 10000 ]] || { echo "ERROR: threshold $NEW_THRESHOLD is too small (< 10000)"; exit 1; }

CONFIG="$HOME/Library/Application Support/acos-token-monitor/config.yaml"
sed -i '' "s/^threshold:.*/threshold: ${NEW_THRESHOLD}/" "$CONFIG"
```

The path `$HOME/Library/Application Support/acos-token-monitor/config.yaml`
contains a space; double-quote it everywhere.

### Step 3: Verify

```bash
grep '^threshold:' "$CONFIG"
pgrep -fl token-watcher.py >/dev/null && echo "Daemon running — new threshold active immediately."
```

### Step 4: Report

Print:
- Old threshold (if known)
- New threshold
- Whether the daemon is running
- Note: `~/Library/Application Support/acos-token-monitor/state/.compact-fired-<session_id>`
  may need clearing if the user wants to re-trigger from the new threshold:
  ```bash
  rm -f "$HOME/Library/Application Support/acos-token-monitor/state/.compact-fired-"*
  ```

## Sensible threshold guidance

| Threshold | Behavior |
|-----------|----------|
| 100k–200k | Aggressive. Fires early, lots of cycles, very small loss-of-context risk per cycle. |
| 300k–450k | Balanced. Default range. Fires when context comfortably full. |
| 500k–800k | Lazy. Fires only when context is genuinely tight. |
| > 950k | Off (effectively). |

## Manual one-liner equivalent

```bash
sed -i '' 's/^threshold:.*/threshold: 350000/' "$HOME/Library/Application Support/acos-token-monitor/config.yaml"
```

---

*ACOS Eternity Protocol Threshold — hot-reload tuning.*
