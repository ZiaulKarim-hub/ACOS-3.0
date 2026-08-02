# Eternity Protocol — Non-Firing Root Cause & Hardened Fix Plan

**Report date:** 2026-07-05
**Trigger:** "Since I changed the threshold, the eternity protocol is not running" — repeated in the FruitSync cmux window.
**Method:** 6-lane multi-agent audit (37 agents, adversarially verified), grounded in live process table + on-disk code + daemon logs.
**Goal bar:** the protocol must NEVER silently stall and must NOT be hijackable/compromisable.
**Result:** 27 confirmed failure modes. Root cause is NOT the threshold.

> **STATUS — Stage 1 + Stage 2 APPLIED + VERIFIED 2026-07-06. Doctor: ALL GREEN.**
> **Stage 1 (restore):** transport (P0-A/B/C), carrier arbitration (daemon detection-only
> when `.cmux-inpane-inject` present), in-pane resume arm-after-verify + health-gate +
> widened window. **Stage 2 (harden):** P1-D plist `EnvironmentVariables` PATH (watchers
> now show `/opt/homebrew/bin` in `ps eww`); P1-E class-independent breaker (rc=2/rc=1 now
> trip it — unit-verified); P1-F pane-gate fail-closed + `self_terminate` preserves
> `cmux-surface`; P1-G threshold clamp `[50k,2M]` (unit-verified: 9999999/0/-5 → default);
> P2-H user-visible `.eternity-ALERT` + osascript one-shot (verified fired); P2-I doctor
> plist-PATH check + §5b dispatch-failure log-scan + liveness-aware coverage. Verified:
> injector rc=4 (not rc=2) under bare PATH; post-respawn rc=2 = 0; manifest regenerated;
> plist reloaded; watchers respawned.
> **DEFERRED (lower-priority residuals, not applied):** surface re-discovery on rc=5
> (residual #6); P2-J per-session heartbeat (SKILL.md lockstep risk); in-pane hook
> alert-on-failure; `eternity-resume-prepend.sh` path-(3) pane-scoping (residual #10).
> The definitive end-to-end proof is the next real FruitSync threshold cross.

---

## 1. Root cause of the non-firing

**The `cmux` binary is not on the daemon watcher's `PATH`, so every injection fails when it shells out to `cmux`.**

- Loaded LaunchAgent `com.acos.token-watcher-backfill` has **no `EnvironmentVariables`/`PATH`** → inherits launchd bare `PATH=/usr/bin:/bin:/usr/sbin:/sbin`.
- `AbandonProcessGroup=true` keeps ~11 watchers alive on that bare PATH for the daemon's whole lifetime.
- `cmux` exists only at `/opt/homebrew/bin/cmux` — not on the bare PATH → `FileNotFoundError`.
- Verified: `launchctl list` (only backfill loaded); plist env grep = 0; `ps eww` live watchers = bare PATH; `env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin command -v cmux` = not found.

**Chain is broken at every hop:** launchd (bare PATH) → `backfill-watchers.sh` (bare `python3`) → `token-watcher.py` (spawns injector bare `["python3", …]`, no `env=`) → `inject-via-cmux.py` (bare `["cmux", …]`). No hop restores `/opt/homebrew/bin`.

**All four cmux flows fail:** threshold `/clear` fire, post-compaction resume, `/clear` inject, autonomous orphan-claim resume.

### Why the 2026-07-05 `find_cmux_cli()` fix is incomplete
The absolute-path fallback added today is used ONLY as a boolean pre-flight gate (`inject-via-cmux.py:260`); the resolved path is discarded. `cmux_ping()` (`:140`) and `cmux_send()` (`:162`) still call bare `["cmux", …]`. Net effect: failure just moves from rc=2 to rc=3. The protocol still doesn't fire. The watcher's own recovery probe `cmux_ping_ok()` (`:424`) is bare too, so it can never self-recover.

## 2. Why the threshold change was a red herring
- Session `03c15d0c` failed identically at the OLD 400k threshold (first cross `approx=402,550`).
- The threshold IS crossed and a fire IS attempted every event (2,180+ `THRESHOLD CROSSED … DISPATCH FAILED`). Failure is downstream, at cmux resolution — independent of threshold value.
- Corpus totals: rc=2 ×1391, rc=1 ×718, rc=5 ×78, rc=3 ×39; only ~6 successful `FIRED` across all daemon logs.

## 3. THE decisive architectural finding (from adversarial review)
**The daemon injector is a REDUNDANT/RACING path (~6 `FIRED` ever). The real working carrier is the IN-PANE hooks** — `eternity-cmux-inpane.sh` (Stop) + `eternity-cmux-resume-inpane.sh` (SessionStart), enabled via `state/.cmux-inpane-inject`. They run in-pane where bare `cmux send` resolves. Implications:
1. Fixing the daemon PATH alone does NOT achieve the goal.
2. P0 fixes can INTRODUCE a **double-`/clear` race** (daemon + in-pane both send `/clear`).
3. The in-pane resume path has its own CRITICAL bug: `.autoresume-fired-$SID` is armed BEFORE an unverified `cmux send` and NEVER cleared; cmux reuses one session_id across `/clear` cycles → **cycle 2+ is permanently disarmed** (why FruitSync stalls after the first cycle). Plus a 5-minute `.clear-fired` window that silently drops on slow compaction, and no cmux health gate.

## 4. Prioritized failure-mode table (corrected severities)

| ID | Failure | Sev | Silent? | Evidence |
|----|---------|-----|---------|----------|
| plist-no-path-env | Backfill plist sets no PATH; watchers inherit bare launchd PATH | CRITICAL | Yes | plist (no env); `ps eww` |
| inj-ping-send-bare-cmux | Injector ping/send still bare `["cmux"]`; find_cmux_cli result discarded | CRITICAL | Yes | inject-via-cmux.py:140,162,260,90 |
| orphan-claim-rides-broken-injector | Sole autonomous post-/clear resume path rides the broken injector, drops silently | CRITICAL | Yes | token-watcher.py:1072-1082,534,1099 |
| breaker-ignores-rc1-rc2 | Breaker counts only rc in (3,5); rc=2 (1391×) + rc=1 (718×) never trip it | CRITICAL | Yes | token-watcher.py:512 |
| no-user-alert-on-dispatch-failure | 1391 failures, zero user alerts; alert fires only on watcher process absence | CRITICAL | Yes | backfill:206-230; tw:1596-1603 |
| inpane-resume-guard-disarms-cycle2 | `.autoresume-fired` armed pre-verify, never cleared → cycle 2+ dead | HIGH→CRIT | Yes | eternity-cmux-resume-inpane.sh:132,144 |
| watcher-spawn-no-env | Watcher spawns injector bare `python3`, no `env=` | HIGH | Yes | token-watcher.py:313,534 |
| inj-fix-converts-storm-to-silent-wedge | Partial fix latches breaker (rc=3) → ~10-min silent wedge | HIGH | Yes | inj:273-279; tw:488-495,512 |
| pane-gate-fallthrough-wrong-handoff | Cross-pane guard only when both surfaces known; unknown → adopts other pane's resume | HIGH | Yes | token-watcher.py:1003-1009,784 |
| inpane-5min-window | In-pane resume 5-min `.clear-fired` window silently drops | HIGH | Yes | eternity-cmux-resume-inpane.sh:93-94 |
| plist-discrepancy-path-regression | Retired com.acos.token-monitor.plist HAD the correct PATH; migration dropped it | HIGH | Yes | retired plist:38-42 |
| doctor-blind-to-dispatch-failures | eternity-doctor reports ALL-GREEN during the storm; never reads logs | HIGH | Yes | eternity-doctor.sh:65-85 |
| cmux-app-down-inpane-no-healthgate | In-pane blind `cmux send`, unchecked return; app-down/stale-socket drops silently | HIGH | Yes | inpane resume:144 |
| cfg-threshold-no-upper-bound | No upper clamp; huge threshold parses clean, disables fire forever | MEDIUM | Yes | token-watcher.py:210-221 |
| surface-staleness-no-rediscovery | cmux restart re-mints surfaces; no re-discovery on rc=5 | MEDIUM | Yes | inject-via-cmux.py:216 |
| heartbeat-write-only-unmonitored | Global heartbeat read by nothing; one healthy tick hides N dead watchers | MEDIUM | Yes | token-watcher.py:66,794-803 |
| prepend-last-resort-cross-pane | UserPromptSubmit fallback picks newest-in-project, no pane scoping | MEDIUM | Yes | eternity-resume-prepend.sh:158-169 |
| cfg-malformed-threshold-safe-default | POSITIVE: malformed threshold → safe 400000 default | LOW | — | token-watcher.py:210-214 |

(Full 27-item set + per-finding verifier reasoning in the workflow transcript.)

## 5. Hardened fix plan

Apply the set WHOLE and force-respawn watchers. Partial apply degrades a loud rc=2 storm into a quiet rc=3 latch-and-suppress wedge.

### P0 — stop the silent stall (transport + breaker)
- **P0-A** `inject-via-cmux.py`: thread the resolved `cmux_bin` into `cmux_ping()`/`cmux_send()` (`:140`,`:162`); belt-and-suspenders prepend its dir to `os.environ["PATH"]` in `inject()`.
- **P0-B** `token-watcher.py`: prepend `/opt/homebrew/bin:/usr/local/bin` to PATH at top of `main()`; spawn injector with `sys.executable` + `env=os.environ.copy()` (`:313`,`:534`).
- **P0-C** `token-watcher.py`: resolve cmux absolutely in `cmux_ping_ok()` (`:424`) so the daemon can self-recover.

### P1 — defense-in-depth + correctness
- **P1-D** backfill plist: add `EnvironmentVariables`→`PATH` incl `/opt/homebrew/bin`; reload; retire the stale `com.acos.token-monitor.plist`.
- **P1-E** `token-watcher.py:498-513`: make the breaker class-independent (rc=2/rc=-1 = hard fault, mark on first; explicit `else` counts unknown rc).
- **P1-F** `token-watcher.py`: fail CLOSED on unknown surface for cmux cross-SID claims (`:1003-1009`); stop deleting `cmux-surface-<sid>` in `self_terminate` (`:783-786`).
- **P1-G** `token-watcher.py:210-221`: clamp threshold to `[50_000, 2_000_000]` in the consumer, fall back to default with WARN.

### P2 — observability & escalation
- **P2-H** user-visible alert (`.eternity-ALERT` + one-shot `osascript` notification) on first hard fault.
- **P2-I** `eternity-doctor.sh`: scan logs for dispatch failures; add a bare-PATH cmux probe to expose the mismatch.
- **P2-J** per-session heartbeat + doctor staleness check (lockstep: update `acos-eternity-protocol/SKILL.md:147-158` which reads the global heartbeat).

### CRITICAL additions from the adversarial review (required for the goal bar)
- **Arbitrate the two carriers:** gate the daemon `/clear`/resume on ABSENCE of `state/.cmux-inpane-inject` (pick ONE carrier — prefer in-pane) to avoid the double-`/clear` race P0 would otherwise create.
- **Fix the in-pane resume guard:** clear/rekey `.autoresume-fired` per `/clear` cycle; arm only AFTER a verified send; widen/rekey the 5-min gate off the arming marker; add a cmux health gate before the in-pane send.
- **Single-line autonomous resume:** inject a slash-command/trigger, never the multi-line body (kills the rc=6 disk-fallback-needs-human silent drop).

## 6. Residual risks if only P0 is applied
- Double-`/clear` race (daemon + in-pane).
- Autonomous resume still drops from cycle 2 (in-pane guard bug).
- rc=1 injector crash class still silent/unbounded without P1-E.
- Reboot / cold-cmux window; surface staleness after cmux restart.

## Bottom line
The non-firing is a missing `PATH` on the launchd watcher — not the threshold. But because the daemon is a redundant carrier, truly hitting "never silently stalls" requires ALSO arbitrating the two `/clear` carriers, fixing the in-pane resume guard (the cycle-2 disarm is why FruitSync stalls), and making autonomous resume single-line. Apply whole, force-respawn watchers, and verify with the cmux app both up AND killed.
