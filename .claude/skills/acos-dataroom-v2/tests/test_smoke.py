"""Smoke tests for acos-dataroom-v2 deterministic components.

These tests validate the Python helpers (run_state.py, consensus_check.py,
build_dataroom_guide_excel.py, build_manual_review_md.py) work correctly with
synthetic inputs. They do NOT exercise the full skill end-to-end — that
requires actually invoking /acos-dataroom-v2 inside a Claude Code session,
which can only be tested by manual operator invocation (see SMOKE_TEST.md).

Run with: pytest tests/test_smoke.py -v
Or:        python3 -m unittest tests/test_smoke.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"


def _run_script(script_name: str, *args: str) -> tuple[int, str, str]:
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


class TestRunState(unittest.TestCase):
    def test_init_creates_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run_test"
            code, out, err = _run_script(
                "run_state.py", "init",
                "--run-dir", str(run_dir),
                "--source", "/tmp/fake_source",
                "--objective", "Test objective",
            )
            self.assertEqual(code, 0, f"init failed: {err}")
            self.assertTrue((run_dir / "run_state.json").exists())
            state = json.loads((run_dir / "run_state.json").read_text())
            self.assertEqual(state["phase"], "0_setup")
            self.assertEqual(state["objective_brief"], "Test objective")

    def test_set_phase_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run_test"
            _run_script("run_state.py", "init", "--run-dir", str(run_dir),
                        "--source", "/tmp/fake", "--objective", "Test")
            code, out, _ = _run_script(
                "run_state.py", "set",
                "--run-dir", str(run_dir),
                "--phase", "1_objective_solidified",
                "--checkpoint", "phase1_synthesis_complete",
            )
            self.assertEqual(code, 0)
            state = json.loads((run_dir / "run_state.json").read_text())
            self.assertEqual(state["phase"], "1_objective_solidified")
            self.assertEqual(state["last_completed_checkpoint"], "phase1_synthesis_complete")

    def test_log_appends(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run_test"
            _run_script("run_state.py", "init", "--run-dir", str(run_dir),
                        "--source", "/tmp/fake", "--objective", "Test")
            _run_script("run_state.py", "log", "--run-dir", str(run_dir),
                        "--message", "Test message 1")
            _run_script("run_state.py", "log", "--run-dir", str(run_dir),
                        "--message", "Test message 2", "--phase", "2_inclusion")
            log = (run_dir / "logs" / "run_log.txt").read_text()
            self.assertIn("Test message 1", log)
            self.assertIn("Test message 2", log)
            self.assertIn("[2_inclusion]", log)


class TestConsensusCheck(unittest.TestCase):
    def _write_vote(self, dir: Path, agent: str, vote_data: dict):
        dir.mkdir(parents=True, exist_ok=True)
        (dir / f"{agent}.json").write_text(json.dumps(vote_data))

    def test_unanimous_include(self):
        with tempfile.TemporaryDirectory() as tmp:
            votes = Path(tmp) / "votes"
            for agent in ("a1", "a2", "a3"):
                self._write_vote(votes, agent, {"verdict": "INCLUDE", "agent_id": agent})
            code, out, _ = _run_script("consensus_check.py", "inclusion", "--votes-dir", str(votes))
            self.assertEqual(code, 0)
            result = json.loads(out)
            self.assertEqual(result["verdict"], "INCLUDE")

    def test_unanimous_exclude(self):
        with tempfile.TemporaryDirectory() as tmp:
            votes = Path(tmp) / "votes"
            for agent in ("a1", "a2", "a3"):
                self._write_vote(votes, agent, {"verdict": "EXCLUDE", "agent_id": agent})
            _, out, _ = _run_script("consensus_check.py", "inclusion", "--votes-dir", str(votes))
            self.assertEqual(json.loads(out)["verdict"], "EXCLUDE")

    def test_split_inclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            votes = Path(tmp) / "votes"
            self._write_vote(votes, "a1", {"verdict": "INCLUDE", "agent_id": "a1"})
            self._write_vote(votes, "a2", {"verdict": "INCLUDE", "agent_id": "a2"})
            self._write_vote(votes, "a3", {"verdict": "EXCLUDE", "agent_id": "a3"})
            _, out, _ = _run_script("consensus_check.py", "inclusion", "--votes-dir", str(votes))
            result = json.loads(out)
            self.assertEqual(result["verdict"], "SPLIT")
            self.assertEqual(result["breakdown"], {"INCLUDE": 2, "EXCLUDE": 1})

    def test_privilege_any_flag_removes(self):
        with tempfile.TemporaryDirectory() as tmp:
            votes = Path(tmp) / "votes"
            # 2 KEEP + 1 FLAG → REMOVE per asymmetric rule
            self._write_vote(votes, "a1", {"verdict": "KEEP", "agent_id": "a1"})
            self._write_vote(votes, "a2", {"verdict": "KEEP", "agent_id": "a2"})
            self._write_vote(votes, "a3", {"verdict": "FLAG", "agent_id": "a3",
                                            "triggered_markers": ["1.1: 'Privileged & Confidential' header"]})
            _, out, _ = _run_script("consensus_check.py", "privilege", "--votes-dir", str(votes))
            result = json.loads(out)
            self.assertEqual(result["verdict"], "REMOVE")
            self.assertIn("a3", result["flagging_agents"])

    def test_privilege_unanimous_keep_stays(self):
        with tempfile.TemporaryDirectory() as tmp:
            votes = Path(tmp) / "votes"
            for agent in ("a1", "a2", "a3"):
                self._write_vote(votes, agent, {"verdict": "KEEP", "agent_id": agent})
            _, out, _ = _run_script("consensus_check.py", "privilege", "--votes-dir", str(votes))
            self.assertEqual(json.loads(out)["verdict"], "STAY")

    def test_qa_any_fail_returns(self):
        with tempfile.TemporaryDirectory() as tmp:
            votes = Path(tmp) / "votes"
            self._write_vote(votes, "a1", {"verdict": "PASS", "agent_id": "a1"})
            self._write_vote(votes, "a2", {"verdict": "PASS", "agent_id": "a2"})
            self._write_vote(votes, "a3", {"verdict": "FAIL", "agent_id": "a3", "concerns": ["bad"]})
            _, out, _ = _run_script("consensus_check.py", "qa", "--votes-dir", str(votes))
            self.assertEqual(json.loads(out)["verdict"], "FAIL")

    def test_placement_unanimous(self):
        with tempfile.TemporaryDirectory() as tmp:
            votes = Path(tmp) / "votes"
            for agent in ("a1", "a2", "a3"):
                self._write_vote(votes, agent, {"agent_id": agent, "folder_num": 2})
            _, out, _ = _run_script("consensus_check.py", "placement", "--votes-dir", str(votes))
            result = json.loads(out)
            self.assertEqual(result["verdict"], "UNANIMOUS")
            self.assertEqual(result["folder_num"], 2)

    def test_placement_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            votes = Path(tmp) / "votes"
            self._write_vote(votes, "a1", {"agent_id": "a1", "folder_num": 2})
            self._write_vote(votes, "a2", {"agent_id": "a2", "folder_num": 3})
            self._write_vote(votes, "a3", {"agent_id": "a3", "folder_num": 2})
            _, out, _ = _run_script("consensus_check.py", "placement", "--votes-dir", str(votes))
            self.assertEqual(json.loads(out)["verdict"], "SPLIT")


class TestManualReviewBuilder(unittest.TestCase):
    def test_no_review_needed(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run_test"
            run_dir.mkdir()
            (run_dir / "intermediate").mkdir()
            output = run_dir / "Manual_Review_Required.md"
            code, out, _ = _run_script("build_manual_review_md.py", "--run-dir", str(run_dir), "--output", str(output))
            self.assertEqual(code, 0)
            self.assertIn("NO_MANUAL_REVIEW_NEEDED", out)
            self.assertFalse(output.exists())

    def test_with_unable_to_evaluate(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run_test"
            (run_dir / "intermediate").mkdir(parents=True)
            (run_dir / "intermediate" / "unable_to_evaluate.csv").write_text(
                "filename,reason,source_path\n"
                "encrypted.pdf,encrypted,/src/encrypted.pdf\n"
                "empty.txt,zero_byte,/src/empty.txt\n"
            )
            output = run_dir / "Manual_Review_Required.md"
            code, out, _ = _run_script("build_manual_review_md.py", "--run-dir", str(run_dir), "--output", str(output))
            self.assertEqual(code, 0)
            self.assertTrue(output.exists())
            content = output.read_text()
            self.assertIn("encrypted.pdf", content)
            self.assertIn("empty.txt", content)


class TestSyntheticSource(unittest.TestCase):
    def test_synthetic_source_generates(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "synth_source"
            script = SKILL_DIR / "tests" / "generate_synthetic_source.py"
            result = subprocess.run(
                [sys.executable, str(script), "--output", str(output)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, f"generate failed: {result.stderr}")
            self.assertTrue(output.is_dir())
            # Check expected files exist
            self.assertTrue((output / "Property" / "Ascent_Hotel_Overview.txt").exists())
            self.assertTrue((output / "Legal" / "PRIVILEGED_Attorney_Memo_re_Foreclosure.txt").exists())
            self.assertTrue((output / "Misc" / "empty_placeholder.txt").exists())
            # File count
            files = list(output.rglob("*"))
            files = [f for f in files if f.is_file()]
            self.assertGreaterEqual(len(files), 10)


if __name__ == "__main__":
    unittest.main()
