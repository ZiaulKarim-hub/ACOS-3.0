#!/bin/sh
# clean-env.sh — run a command with an environment its caller cannot have poisoned (SEC-40).
#
# WHY THIS EXISTS. The quality gates spawn their children through runGate, which passes
# only an allowlisted environment (SEC-35). That fixes the children and never claimed to
# fix the gate's OWN process: `bun tools/checks/tests.ts` honours BUN_OPTIONS from whoever
# started it, and BUN_OPTIONS can carry `--preload <file>`.
#
# AND AN IN-PROCESS GUARD CANNOT REPAIR THAT, measured 2026-11-18 on bun 1.3.9: a preload
# module runs BEFORE the entry file and can replace what the entry later imports. A preload
# that swapped spawnSync made the gate's own `/bin/echo hello` return "faked" without
# /bin/echo ever running. So a re-exec written at the top of a gate would itself be run by
# code the attacker had already replaced. The cleaning has to happen in a process that is
# not bun, which is what this script is.
#
# WHY A SHELL SCRIPT RATHER THAN A LINE IN package.json. `bun run` executes scripts with
# Bun's own shell, and a line using nested quotes with `$(command -v bun)` did not run as
# written -- bun printed its help instead. PATH on this machine also contains a space, so
# every expansion must be quoted, which a /bin/sh script does plainly and a one-liner does
# not.
#
# IT KNOWS NOTHING ABOUT BUN ON PURPOSE. The command to run is argv[1], so each caller
# keeps whatever interpreter it had already pinned -- .nemesis/config.json passes bun by
# absolute path, which is the SEC-30 defence, and this script does not weaken it by looking
# the name up again.
#
# WHAT IT CANNOT DO. The process that runs `bun run <script>` is still the caller's own,
# and a preload there could in principle interfere with how the script is launched. That
# residual is irreducible: whoever starts the gate controls the gate. What this closes is
# the hop that was inside our control.
#
# Only PATH, HOME, TMPDIR and USER survive, and USER only when it is set -- an empty PATH
# and no PATH are different things to a child process, so nothing is passed as empty.
set -eu

if [ "$#" -lt 1 ]; then
  echo "clean-env: needs a command to run" >&2
  exit 2
fi

set -- PATH="$PATH" HOME="$HOME" TMPDIR="${TMPDIR:-/tmp}" "$@"
if [ -n "${USER:-}" ]; then
  set -- "USER=$USER" "$@"
fi
exec /usr/bin/env -i "$@"
