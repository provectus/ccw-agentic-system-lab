"""Sandboxed file operations on the workspace clone.

All paths are resolved against `workspace/ccw-inventory-management`. Attempts
to traverse outside that root raise ValueError. The sandbox is intentional —
the agent should not be able to read the lab repo's own source or its own
prompts, only the target repo.
"""

from __future__ import annotations

import glob as _glob
from pathlib import Path

from agent.config import WORKSPACE_DIR, TARGET_REPO_DIR_NAME


def _root() -> Path:
    return (WORKSPACE_DIR / TARGET_REPO_DIR_NAME).resolve()


def _sandboxed(path: str) -> Path:
    """Resolve `path` against the workspace clone; reject traversal."""
    root = _root()
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path {path!r} escapes workspace sandbox {root}") from exc
    return candidate


def read_file(path: str, max_bytes: int = 200_000) -> str:
    p = _sandboxed(path)
    if not p.exists():
        return f"read_file: not found: {path}"
    if not p.is_file():
        return f"read_file: not a regular file: {path}"
    data = p.read_bytes()
    truncated = len(data) > max_bytes
    text = data[:max_bytes].decode("utf-8", errors="replace")
    suffix = f"\n…(truncated, {len(data) - max_bytes} bytes omitted)" if truncated else ""
    return text + suffix


def grep(pattern: str, path: str = ".") -> str:
    """Recursive grep. Uses ripgrep if available, falls back to `grep -rn`."""
    from agent.tools._shell import run

    search_root = _sandboxed(path)
    rg_check = run(["which", "rg"])
    if rg_check.ok:
        result = run(["rg", "--no-heading", "-n", pattern, str(search_root)])
    else:
        result = run(["grep", "-rn", pattern, str(search_root)])
    return result.stdout or f"(no matches for pattern={pattern!r} in {path})"


def glob_files(pattern: str) -> str:
    """Glob inside the workspace clone. Pattern is relative to the workspace root."""
    root = _root()
    matches = sorted(_glob.glob(str(root / pattern), recursive=True))
    if not matches:
        return f"(no matches for pattern={pattern!r})"
    # Return paths relative to the workspace root for readability.
    return "\n".join(str(Path(m).relative_to(root)) for m in matches)


__all__ = ["read_file", "grep", "glob_files"]
