"""Smoke tests for the lab scaffold. Run with: `uv run pytest tests/smoke.py`

Goal: catch breakage in the scaffold layer BEFORE participants notice. These
tests intentionally do NOT exercise the Claude Agent SDK (no API key needed)
or the gh CLI (no network needed).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_help_prints():
    """`python -m agent --help` exits 0 and prints usage."""
    result = subprocess.run(
        [sys.executable, "-m", "agent", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "review" in result.stdout
    assert "triage" in result.stdout
    assert "--dry-run" in result.stdout


def test_github_dry_run_comment_preview():
    """gh_pr_comment(dry_run=True) returns a structured preview without touching GitHub."""
    from agent.tools import github

    out = github.gh_pr_comment(
        "https://github.com/example/repo/pull/42",
        path="server/main.py",
        line=10,
        body="watch this null deref",
        dry_run=True,
    )
    assert "DRY RUN" in out
    assert "server/main.py" in out
    assert "watch this null deref" in out


def test_github_url_parse_rejects_garbage():
    """URL parsers reject inputs that aren't PR or issue URLs."""
    from agent.tools import github

    with pytest.raises(ValueError):
        github.gh_pr_diff("not a url")


def test_telemetry_writes_jsonl(tmp_path):
    """TelemetryLogger writes one JSONL line per record and reconstructs spans."""
    from agent.telemetry import TelemetryLogger

    logger = TelemetryLogger(trace_id="testtrace", log_dir=tmp_path)
    logger.run_start(mode="review", url="http://x", dry_run=True)
    with logger.span("coordinator.plan", kind="model_call", role="coordinator", model="claude-sonnet-4-6"):
        logger.tool_call("gh_pr_diff", args_summary="pr_url=http://x", output_summary="diff…")
    logger.run_end(status="ok")

    lines = logger.path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 4  # run_start, tool_call, model_call (closed by span), run_end
    records = [json.loads(line) for line in lines]
    kinds = [r["kind"] for r in records]
    assert "run_start" in kinds
    assert "tool_call" in kinds
    assert "model_call" in kinds
    assert "run_end" in kinds
    for r in records:
        assert r["trace_id"] == "testtrace"


def test_prompt_loader_rejects_empty():
    """load_prompt() raises if the file has only frontmatter (no body)."""
    from agent.loop import load_prompt

    # All prompts ship empty in the scaffold — confirm the guard catches it.
    with pytest.raises(RuntimeError, match="only frontmatter"):
        load_prompt("router")


def test_repo_tool_rejects_sandbox_escape(tmp_path, monkeypatch):
    """repo.read_file rejects paths that escape the workspace root."""
    monkeypatch.setattr("agent.config.WORKSPACE_DIR", tmp_path)
    (tmp_path / "ccw-inventory-management").mkdir()
    from agent.tools import repo

    with pytest.raises(ValueError, match="escapes workspace sandbox"):
        repo.read_file("../../etc/passwd")


def test_config_pick_model_returns_known_model():
    """pick_model() returns one of the three known model IDs for every role."""
    from agent import config

    valid = {config.MODEL_HAIKU, config.MODEL_SONNET, config.MODEL_OPUS}
    for role in config.ROLE_MODEL_MAP:
        assert config.pick_model(role) in valid, role
