# Tests for scripts/autonomous_runner.py
#
# These tests validate the runner's helper functions and CLI parsing
# without requiring GitHub API access or DeerFlow dependencies.
#
# Run:  pytest tests/test_autonomous_runner.py -v

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make the scripts directory importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import autonomous_runner  # noqa: E402


# ---------------------------------------------------------------------------
# build_mission_prompt
# ---------------------------------------------------------------------------

class TestBuildMissionPrompt:
    def test_includes_issue_metadata(self):
        issue = {
            "number": 42,
            "title": "Acquire skill: pdf-parser",
            "body": "## Objective\nWrap pdf-parser as a skill.",
            "labels": [{"name": "mission:dev"}, {"name": "status:active"}],
        }
        prompt = autonomous_runner.build_mission_prompt(issue, "owner/repo")
        assert "#42" in prompt
        assert "owner/repo" in prompt
        assert "pdf-parser" in prompt
        assert "mission:dev" in prompt
        assert "run:log" in prompt

    def test_handles_missing_body(self):
        issue = {"number": 1, "title": "Test", "body": None, "labels": []}
        prompt = autonomous_runner.build_mission_prompt(issue, "o/r")
        assert "#1" in prompt

    def test_handles_empty_labels(self):
        issue = {"number": 1, "title": "T", "body": "", "labels": []}
        prompt = autonomous_runner.build_mission_prompt(issue, "o/r")
        assert "Labels:" in prompt

    def test_dev_mission_includes_skill_conventions(self):
        issue = {
            "number": 5,
            "title": "Acquire skill: foo",
            "body": "Wrap foo.",
            "labels": [{"name": "mission:dev"}, {"name": "status:active"}],
        }
        prompt = autonomous_runner.build_mission_prompt(issue, "o/r")
        assert "submodule" in prompt
        assert "ghcr.io" in prompt
        assert "memory:skill" in prompt
        assert "validate-submodules" in prompt

    def test_non_dev_mission_omits_skill_conventions(self):
        issue = {
            "number": 6,
            "title": "Plan next quarter",
            "body": "Create a plan.",
            "labels": [{"name": "mission:planning"}, {"name": "status:active"}],
        }
        prompt = autonomous_runner.build_mission_prompt(issue, "o/r")
        assert "submodule" not in prompt


# ---------------------------------------------------------------------------
# list_active_missions filtering
# ---------------------------------------------------------------------------

class TestListActiveMissions:
    @patch("autonomous_runner._run_gh")
    def test_filters_to_mission_labels(self, mock_gh):
        import json
        mock_gh.return_value = json.dumps([
            {"number": 1, "title": "A", "labels": [{"name": "mission:dev"}, {"name": "status:active"}]},
            {"number": 2, "title": "B", "labels": [{"name": "status:active"}]},  # no mission:*
            {"number": 3, "title": "C", "labels": [{"name": "mission:research"}, {"name": "status:active"}]},
        ])
        result = autonomous_runner.list_active_missions("o/r")
        assert len(result) == 2
        assert result[0]["number"] == 1
        assert result[1]["number"] == 3


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

class TestParseArgs:
    def test_single_mission(self):
        args = autonomous_runner.parse_args([
            "--mission-issue", "42",
            "--mission-repo", "owner/repo",
        ])
        assert args.mission_issue == 42
        assert args.mission_repo == "owner/repo"
        assert not args.loop

    def test_loop_mode(self):
        args = autonomous_runner.parse_args([
            "--loop",
            "--mission-repo", "owner/repo",
            "--poll-interval", "30",
            "--max-iterations", "5",
        ])
        assert args.loop is True
        assert args.poll_interval == 30
        assert args.max_iterations == 5

    def test_defaults(self):
        args = autonomous_runner.parse_args(["--mission-issue", "1", "--mission-repo", "o/r"])
        assert args.poll_interval == 60
        assert args.max_iterations == 0
        assert args.model is None


# ---------------------------------------------------------------------------
# main() validation
# ---------------------------------------------------------------------------

class TestMainValidation:
    @patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_test"}, clear=False)
    def test_requires_mission_repo(self):
        with pytest.raises(SystemExit) as exc_info:
            autonomous_runner.main(["--mission-issue", "1"])
        assert exc_info.value.code == 1

    @patch.dict("os.environ", {"GITHUB_TOKEN": ""}, clear=False)
    def test_requires_github_token(self):
        with pytest.raises(SystemExit) as exc_info:
            autonomous_runner.main(["--mission-issue", "1", "--mission-repo", "o/r"])
        assert exc_info.value.code == 1

    @patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_test"}, clear=False)
    def test_requires_issue_or_loop(self):
        with pytest.raises(SystemExit) as exc_info:
            autonomous_runner.main(["--mission-repo", "o/r"])
        assert exc_info.value.code == 1
