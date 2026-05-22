"""Git operations on the workspace clone of ccw-inventory-management."""

from __future__ import annotations

import tempfile
from pathlib import Path

from agent.config import WORKSPACE_DIR, TARGET_REPO_DIR_NAME
from agent.tools._shell import dry_run_preview, run


def _clone_root() -> Path:
    """Return the path of the cloned target repo. Created by scripts/setup-lab.sh."""
    return WORKSPACE_DIR / TARGET_REPO_DIR_NAME


def git_clone(repo_url: str, dest: Path | None = None) -> str:
    """Clone a repo into the workspace. Skips if already present (cached)."""
    target = dest or _clone_root()
    if target.exists() and (target / ".git").exists():
        return f"git_clone: already cloned at {target} — skipping."
    target.parent.mkdir(parents=True, exist_ok=True)
    result = run(["git", "clone", repo_url, str(target)])
    return f"git_clone:\n{result.render()}"


def git_checkout(branch: str, create: bool = False) -> str:
    cmd = ["git", "checkout", "-b" if create else "-q", branch] if create else ["git", "checkout", branch]
    result = run(cmd, cwd=_clone_root())
    return f"git_checkout({branch!r}, create={create}):\n{result.render()}"


def git_branch(name: str) -> str:
    """Create a new branch (without switching)."""
    result = run(["git", "branch", name], cwd=_clone_root())
    return f"git_branch({name!r}):\n{result.render()}"


def git_apply(diff: str, dry_run: bool = True) -> str:
    """Apply a unified diff. Writes diff to a temp file and runs `git apply`."""
    if dry_run:
        first_line = (diff.splitlines() or ["(empty diff)"])[0]
        return dry_run_preview(
            "apply diff to workspace",
            first_line=first_line, total_lines=len(diff.splitlines()),
        )
    with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False, encoding="utf-8") as f:
        f.write(diff)
        patch_path = f.name
    try:
        result = run(["git", "apply", "--whitespace=fix", patch_path], cwd=_clone_root())
        return f"git_apply:\n{result.render()}"
    finally:
        Path(patch_path).unlink(missing_ok=True)


def git_commit(message: str, dry_run: bool = True) -> str:
    if dry_run:
        return dry_run_preview("commit", message=message)
    # Stage everything that changed, then commit. Participants can edit
    # this if they want more selective staging in their orchestration.
    run(["git", "add", "-A"], cwd=_clone_root())
    result = run(["git", "commit", "-m", message], cwd=_clone_root())
    return f"git_commit:\n{result.render()}"


def git_push(dry_run: bool = True) -> str:
    if dry_run:
        head_res = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=_clone_root())
        branch = head_res.stdout.strip() or "(unknown branch)"
        return dry_run_preview("push branch to origin", branch=branch)
    result = run(["git", "push", "-u", "origin", "HEAD"], cwd=_clone_root())
    return f"git_push:\n{result.render()}"


__all__ = ["git_clone", "git_checkout", "git_branch", "git_apply", "git_commit", "git_push"]
