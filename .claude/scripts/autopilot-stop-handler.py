#!/usr/bin/env python3
"""
Autopilot Stop hook — continuation loop with safety brakes.

Fires when Claude finishes a turn. If autopilot is active, decides whether to:
  - Continue (return decision="block" with a continuation reason — keeps Claude going)
  - Terminate (delete sentinel, log final status)

Exit conditions (in priority order):
  1. stop_hook_active is true (harness re-fire safeguard) — never re-block
  2. AUTOPILOT_GOAL_COMPLETE marker phrase in last assistant message → goal-done exit
  3. Iteration count >= max_iterations (default 150) → cap exit
  4. Last FIVE iterations all had 0 tool calls → idle exit
  5. Sentinel missing → autopilot off, nothing to do

Output format (Stop hook):
  - To continue: {"decision": "block", "reason": "<continuation directive>"}
  - To terminate: emit nothing (just exit 0) and the session naturally stops

Fail-open: any error → exit 0 silently (no continuation, no crash).
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


GOAL_COMPLETE_MARKER = "AUTOPILOT_GOAL_COMPLETE"
IDLE_WINDOW = 5  # consecutive zero-tool-call iterations before idle exit


def find_project_root(cwd):
    path = Path(cwd).resolve()
    for parent in [path] + list(path.parents):
        if (parent / ".acos").is_dir():
            return parent
    try:
        script_dir = Path(__file__).resolve().parent
        for parent in [script_dir] + list(script_dir.parents):
            if (parent / ".acos").is_dir():
                return parent
    except (NameError, OSError):
        pass
    return Path(cwd).resolve()


def audit(project_root, line):
    log = project_root / ".acos" / "state" / "oracle-audit.log"
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def read_transcript_tail(transcript_path, max_lines=200):
    """Read the last N JSONL events from the transcript."""
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [json.loads(l) for l in lines[-max_lines:] if l.strip()]
    except (OSError, json.JSONDecodeError):
        return []


def _is_tool_result_carrier(content):
    """True if a user event's content is purely tool_result blocks (no human text).

    In Claude Code transcripts, tool_result blocks are emitted as USER-role events
    interleaved within a single multi-step assistant turn. These are NOT the start
    of a new human turn and must not terminate the backward walk.
    """
    if not isinstance(content, list):
        return False
    saw_tool_result = False
    for block in content:
        if not isinstance(block, dict):
            # Non-dict block (e.g. bare string) counts as human content
            return False
        btype = block.get("type")
        if btype == "tool_result":
            saw_tool_result = True
        elif btype == "text":
            # Any actual text makes this a genuine human turn
            if block.get("text", "").strip():
                return False
        else:
            # Unknown block type — treat conservatively as human content
            return False
    return saw_tool_result


def count_last_turn_tool_calls(events):
    """Walk events backward from the most recent assistant turn and count tool_use blocks.

    A single Claude turn is: assistant(tool_use) -> user(tool_result) -> assistant(tool_use)
    -> ... -> assistant(text). The user(tool_result) events are intra-turn carriers, not
    new human turns, so we continue past them and sum tool_use across all assistant
    segments. We break only on a GENUINE human user message (content that is not a pure
    tool_result carrier).
    """
    count = 0
    found_assistant = False
    for ev in reversed(events):
        role = ev.get("role") or (ev.get("message", {}) or {}).get("role")
        if role == "user" and found_assistant:
            content = (ev.get("message", {}) or {}).get("content")
            if ev.get("content") is not None and content is None:
                content = ev.get("content")
            if _is_tool_result_carrier(content):
                # Intra-turn tool_result carrier — keep walking, do not break
                continue
            # Genuine human message — start of the previous turn
            break
        if role == "assistant":
            found_assistant = True
            content = (ev.get("message", {}) or {}).get("content")
            if content is None:
                content = ev.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        count += 1
    return count


def last_assistant_text(events):
    """Return concatenated text from ALL consecutive assistant events of the final turn.

    A single logical turn can split its final text across multiple consecutive
    assistant 'text' events (interleaved with intra-turn user tool_result carriers).
    We walk backward, collecting text from every assistant segment, treating
    tool_result-only user events as intra-turn carriers (mirroring
    count_last_turn_tool_calls), and break only on a GENUINE human user message.
    """
    fragments = []
    found_assistant = False
    for ev in reversed(events):
        role = ev.get("role") or (ev.get("message", {}) or {}).get("role")
        if role == "user" and found_assistant:
            content = (ev.get("message", {}) or {}).get("content")
            if ev.get("content") is not None and content is None:
                content = ev.get("content")
            if _is_tool_result_carrier(content):
                # Intra-turn tool_result carrier — keep walking, do not break
                continue
            # Genuine human message — start of the previous turn
            break
        if role == "assistant":
            found_assistant = True
            content = (ev.get("message", {}) or {}).get("content")
            if content is None:
                content = ev.get("content")
            if isinstance(content, str):
                fragments.append(content)
            elif isinstance(content, list):
                texts = [b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text"]
                fragments.append(" ".join(texts))
    # Walked back-to-front; restore chronological order before joining.
    fragments.reverse()
    return "\n".join(f for f in fragments if f)


def emit_continue(reason):
    json.dump({"decision": "block", "reason": reason}, sys.stdout)


def build_directive(goal, iter_num, max_iter, prior_tool_counts, goal_file=None):
    goal_file_line = (
        f"GOAL_FILE: {goal_file}  (re-read this anytime for the full vision)\n"
        if goal_file else ""
    )
    return (
        f"─────────────────────────────────────────────────\n"
        f"AUTOPILOT MODE ACTIVE — iteration {iter_num}/{max_iter}\n"
        f"GOAL: {goal}\n"
        f"{goal_file_line}"
        f"─────────────────────────────────────────────────\n"
        f"Rules while autopilot is active:\n"
        f"  • Do NOT ask free-text confirmation questions in your output text.\n"
        f"  • For any AskUserQuestion you must invoke, the harness auto-picks "
        f"(Recommended) — proceed as if the recommended option was selected.\n"
        f"  • For ExitPlanMode, the harness auto-accepts.\n"
        f"  • Proceed with best judgment. Do not stop to clarify minor decisions.\n"
        f"  • Destructive operations policy:\n"
        f"      - These are UNBLOCKED entirely: find ... -delete, DROP TABLE/DATABASE/"
        f"SCHEMA, TRUNCATE, DELETE FROM without WHERE. Use them when legitimate.\n"
        f"      - These are LOGGED to .acos/state/requested-destructive.log but ALLOWED "
        f"to proceed silently: rm -rf against $HOME / / . .. (broad targets), "
        f"xargs rm, shred, dd to /dev/*. Use sparingly and only when necessary; the log "
        f"is the user's morning-review audit trail.\n"
        f"      - Specific-file deletions (rm old_file.py, rm -rf node_modules, rm -rf "
        f"./build) are normal and pass through silently.\n"
        f"  • If a user message arrives during autopilot, it is MID-COURSE GUIDANCE, "
        f"NOT a stop signal. Read it, adjust if applicable, and CONTINUE working toward "
        f"the goal. The user wanting to stop autopilot will use /acos-oracle-protocol "
        f"autopilot-off or run the activate.py off command in a shell — not a regular "
        f"prompt message.\n"
        f"  • When the goal is GENUINELY complete (acceptance criteria fully met, "
        f"not just 'I've done one step'), emit the exact phrase {GOAL_COMPLETE_MARKER} "
        f"as the last line of your final response. This terminates autopilot cleanly.\n"
        f"  • Idle-exit threshold: {IDLE_WINDOW} consecutive iterations with zero tool "
        f"calls will exit autopilot. Recent tool-call counts per iteration: "
        f"{prior_tool_counts}. If you have no more work to do toward the goal, emit "
        f"{GOAL_COMPLETE_MARKER} explicitly rather than letting idle-exit fire.\n"
        f"\n"
        f"Continue working on the goal now."
    )


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        cwd = data.get("cwd", os.getcwd())
        transcript_path = data.get("transcript_path", "")
        stop_hook_active = bool(data.get("stop_hook_active", False))

        project_root = find_project_root(cwd)
        sentinel = project_root / ".acos" / "state" / "autopilot-active"
        loop_state_path = project_root / ".acos" / "state" / "autopilot-loop-state.json"

        if not sentinel.is_file():
            sys.exit(0)

        if stop_hook_active:
            # Harness re-fire safeguard — bail out
            sys.exit(0)

        try:
            state = json.loads(sentinel.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            sys.exit(0)

        goal = state.get("goal", "")
        goal_file = state.get("goal_file")
        max_iter = int(state.get("max_iterations", 150))
        iter_count = int(state.get("iteration_count", 0))
        # Backwards-compat: accept old field name if present
        prior_counts = list(
            state.get("recent_iter_tool_counts",
                      state.get("last_two_iter_tool_counts", []))
        )

        events = read_transcript_tail(transcript_path, max_lines=400) if transcript_path else []
        this_iter_tool_count = count_last_turn_tool_calls(events) if events else 0
        last_text = last_assistant_text(events) if events else ""

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # ── Exit condition: goal-complete marker ───────────────────────────────
        # Require the marker to be the LAST non-empty line of the assistant text
        # (the directive instructs Claude to emit it "as the last line"). A bare
        # substring test falsely terminates when the marker is echoed mid-narrative,
        # since the marker string circulates in injected context/directives.
        marker_lines = last_text.strip().splitlines()
        if marker_lines and marker_lines[-1].strip().startswith(GOAL_COMPLETE_MARKER):
            audit(project_root,
                  f"[{ts}] AUTOPILOT_GOAL_COMPLETE | iter={iter_count} | goal={goal[:80]}")
            try:
                sentinel.unlink()
            except OSError:
                pass
            try:
                if loop_state_path.is_file():
                    loop_state_path.unlink()
            except OSError:
                pass
            sys.exit(0)

        # Update iteration tracking
        iter_count += 1
        new_prior = (prior_counts + [this_iter_tool_count])[-IDLE_WINDOW:]

        # ── Exit condition: iteration cap ──────────────────────────────────────
        if iter_count > max_iter:
            audit(project_root,
                  f"[{ts}] AUTOPILOT_CAP_HIT | iter={iter_count}>{max_iter} | goal={goal[:80]}")
            try:
                sentinel.unlink()
            except OSError:
                pass
            try:
                if loop_state_path.is_file():
                    loop_state_path.unlink()
            except OSError:
                pass
            sys.exit(0)

        # ── Exit condition: idle (IDLE_WINDOW consecutive zero-tool-call iters) ───
        if len(new_prior) >= IDLE_WINDOW and all(c == 0 for c in new_prior):
            audit(project_root,
                  f"[{ts}] AUTOPILOT_IDLE_EXIT | iter={iter_count} | "
                  f"consecutive_zero_tool_iters | goal={goal[:80]}")
            try:
                sentinel.unlink()
            except OSError:
                pass
            try:
                if loop_state_path.is_file():
                    loop_state_path.unlink()
            except OSError:
                pass
            sys.exit(0)

        # ── Persist updated state ──────────────────────────────────────────────
        state["iteration_count"] = iter_count
        state["recent_iter_tool_counts"] = new_prior
        # Remove legacy field if present (clean migration)
        state.pop("last_two_iter_tool_counts", None)
        try:
            sentinel.write_text(json.dumps(state, indent=2), encoding="utf-8")
            loop_state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except OSError:
            pass

        audit(project_root,
              f"[{ts}] AUTOPILOT_CONTINUE | iter={iter_count}/{max_iter} | "
              f"tools_last_turn={this_iter_tool_count} | recent={new_prior}")

        emit_continue(build_directive(goal, iter_count, max_iter, new_prior, goal_file))

    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
