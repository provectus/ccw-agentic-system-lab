"""Run the target repo's test commands.

Whitelisted command list — the agent cannot invoke arbitrary shell. Pytest is
restricted to flags listed in PYTEST_ALLOWED_FLAGS; everything else is dropped.
npm test is invoked verbatim with no arguments.
"""

from __future__ import annotations

from agent.config import WORKSPACE_DIR, TARGET_REPO_DIR_NAME
from agent.tools._shell import run


# Conservative pytest flag whitelist. Add to this list intentionally.
PYTEST_ALLOWED_FLAGS = {
    "-q", "-v", "-x", "--tb=short", "--tb=long", "--tb=line",
    "-k", "--co", "--collect-only", "-s",
}


def _workspace() -> str:
    return str(WORKSPACE_DIR / TARGET_REPO_DIR_NAME)


def _filter_pytest_args(args: str) -> list[str]:
    """Split, keep paths and approved flags, drop anything else."""
    out: list[str] = []
    tokens = args.split()
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in PYTEST_ALLOWED_FLAGS:
            out.append(tok)
            # -k expects a follow-up expression
            if tok == "-k" and i + 1 < len(tokens):
                out.append(tokens[i + 1])
                i += 2
                continue
        elif tok.startswith("-"):
            # Drop unknown flags rather than passing them through.
            pass
        else:
            # Treat as a path/node id.
            out.append(tok)
        i += 1
    return out


def run_pytest(args: str = "") -> str:
    """Run pytest in the workspace clone. Returns stdout+stderr+exit code."""
    cmd = ["uv", "run", "pytest", *_filter_pytest_args(args)] if args else ["uv", "run", "pytest", "-q"]
    result = run(cmd, cwd=_workspace())
    return f"run_pytest:\n{result.render(max_lines=200)}"


def run_npm_test() -> str:
    """Run `npm test` in the workspace clone's client directory if present, else root."""
    from pathlib import Path

    cwd = Path(_workspace())
    client = cwd / "client"
    target = client if (client / "package.json").exists() else cwd
    result = run(["npm", "test", "--", "--run"], cwd=target)
    return f"run_npm_test (cwd={target}):\n{result.render(max_lines=200)}"


__all__ = ["run_pytest", "run_npm_test"]
