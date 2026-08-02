# Domain Competency Questions — 005-resurrection-protocol
*(Constitutional Domain Compilation, Phase 1 CQs — §0.2. 18 questions a practitioner must answer before
building. Each is a `cq` node in `domain-lattice.json` (`CQ1`..`CQ18`) with a <=2-hop path to a method,
a metric, and a standard/pattern; mechanically-computed coverage = 100% — see `research.md` validation note.)*

- **CQ1 (registry atomicity)** — How must a per-project write guarantee that a crash or a concurrent second
  writer never leaves a valid-but-silently-wrong JSON record (3/25 unlocked writes survived while remaining
  VALID JSON), and why is `mkstemp`-in-target-dir -> `fsync(tmp)` -> `os.replace` -> `fsync(dir)` with one
  writer per file the answer rather than a fixed `.tmp` name or a lock? -> M-atomic-write, MET-torn-writes, STD-posix-fsync.
- **CQ2 (identity)** — What is the canonical project identity, the lookup index, and the re-link key, and which
  candidate keys are BANNED and why (uuid4 at enrollment; `realpath.casefold`; `(st_dev,st_ino)`; banned:
  `sanitize(cwd)`, git remote, workspace UUID, session UUID, title)? -> M-uuid4-identity, MET-dangling-rate, STD-apfs-case.
- **CQ3 (close lifecycle)** — What is the exact ordered close protocol (steps 0-10), which single statement must
  be literally last, and what are the four non-negotiable guards plus the last-workspace guard? -> M-close-steps,
  MET-daemon-writes, STD-spine7.
- **CQ4 (focus-vs-launch)** — How does a pick distinguish same-root / open-elsewhere / not-open, and what
  mechanism focuses an existing workspace without ever creating a duplicate (SPINE 1; cmux does NO dedup)? ->
  M-focus-not-launch, MET-workspace-constant, STD-spine1.
- **CQ5 (Eternity coexistence)** — What namespace, extension, and daemon-state discipline keep Resurrection
  fully disjoint from Eternity (`closed/<slug>/`, `.reentry.md` never `.resume.md`, only `state/stop-<sid>`),
  and why is Resurrection pane-INDEPENDENT while Eternity is pane-DURABLE? -> M-colocated-namespace,
  MET-daemon-writes, STD-spine7 / PAT-disjoint-namespace.
- **CQ6 (enrollment membership)** — What marker gate establishes membership on first sight (`.acos/` OR
  `CLAUDE.md` OR `memory/handoffs/`), and why are BOTH naive scan and close-time creation rejected (DR-8:
  force-quit leaves a close-populated registry empty at its only moment)? -> M-marker-gate, MET-rebuild-rows, STD-spine2.
- **CQ7 (next_action generation)** — How is the <=90-char headline GENERATED (imperative verb first, never
  truncated) from 400-800-char next-step fields, and why is this the single highest-risk dependency? ->
  M-next-action-gen, MET-next-action-chars, STD-spine2 / PAT-generated-not-truncated.
- **CQ8 (receipt honesty)** — What makes a safe-close receipt trustworthy — which lines are read back from
  disk, what does `listed N of M` assert (M == `git status --porcelain | wc -l`), and who alone may print
  `SAFE TO CLOSE THIS TAB`? -> M-verified-receipt, MET-listed-n-of-m, STD-spine3.
- **CQ9 (cmux RPC verification)** — Which cmux 0.64.19 methods are present-but-behavior-UNVERIFIED
  (`workspace.select`, `workspace.close` against a live session, `surface.resume.*`, `session.restore_previous`),
  and what Phase-0 probe battery + DP2 sacrificial tests must confirm before the close skill ships? ->
  M-phase0-probe, MET-probe-pass, STD-dp2-sacrificial.
- **CQ10 (liveness computation)** — How is "is project P open? / where is its pane? / which row is this
  workspace?" computed LIVE (never a stored flag) using un-lie-able joins (`lsof` PID->cwd; `ps` tty->cmux tree;
  `[key:<uuid>]` tag), and why is `identify --surface` a fail-open false positive? -> M-liveness-join,
  MET-workspace-constant, STD-spine5 / PAT-red-amber.
- **CQ11 (rebuild-from-disk)** — What enumeration sources let `rebuild-registry.py` reconstruct the 16/16
  baseline reading NO registry file across BOTH parents plus `~/.claude.json` (lossy hint), and why does a
  derived index DELETE (not mitigate) the 55%-dangling-pointer class? -> M-rebuild-disk, MET-rebuild-rows, STD-spine2.
- **CQ12 (adoption economics)** — Why does deliberate-with-deferred-payoff fail while 147 hand-run
  `/acos-complete` rituals succeeded, and how do menu-first economics + the DR-1 gate + append-only audit
  measurement invert the ~30%-at-day-60 decay without a nagger? -> M-dr1-gate, MET-adoption-day60, PAT-menu-first.
- **CQ13 (storage-substrate exclusions)** — Why are YAML (no yaml module; 19/30 silent), SQLite (opaque; zero
  writers in a force-quit), a single shared file, and cmux workspace state each disqualified on THIS machine? ->
  M-sharded-store, MET-torn-writes, STD-json-fail-loud.
- **CQ14 (argv delivery)** — Why is argv the only route for a multi-line reentry (lands as ONE message, 5/6),
  why do `cmux send`/`surface.send_text` shred at every `\n`, and how is delivery verified given the 1-in-6
  silent drop and the "Quick safety check" trust gate? -> M-argv-delivery, MET-delivery-marker, PAT-receipt-not-promise.
- **CQ15 (blind round-trip verification)** — What must the verifier be DENIED (all repo/cwd access), what is
  the Wigum cap (5, then DEGRADE never halt), and how do you test the tester (a gutted handoff must FAIL; the
  real one must yield a next-step quote that appears in the receipt)? -> M-blind-roundtrip, MET-wigum-cap, STD-lce.
- **CQ16 (DR-1 ship gate)** — What exactly constitutes the one recorded close->resume round-trip that gates
  shipping (real project, receipt SAFE, tab gone, later resume, user-confirmed continuity, recording archived),
  and why can the skill not ship on a promise (placebo -> trust death)? -> M-dr1-gate, MET-dr1-roundtrip, PAT-receipt-not-promise.
- **CQ17 (silent-failure defense)** — Given silent failure is the base rate (ALL-GREEN doctor over 2,000+
  failures; `head -40` hiding 34/74 in an "inspect FIRST" block), what design rule enforces facts-not-verdicts
  and red/amber-only rendering, and why does a single false green cost permanent trust? -> M-facts-render,
  MET-silent-failure-rate, STD-spine3 / PAT-red-amber.
- **CQ18 (absolute-binary paths + version-control-where-it-executes)** — Why must every script call the
  absolute `claude` and `cmux` bundle paths (two PATH shadows: `_acos_cli` at `~/.zshrc:215` + a cmux shim),
  and why must every dependency be version-controlled where it actually executes (the live in-pane hook outside
  the repo = highest-severity doc drift)? -> M-abs-binary / M-vcs-where-executes, MET-binary-shadow, STD-spine4.
