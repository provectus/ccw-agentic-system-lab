"""Shared subprocess helper. No shell=True, ever.

All wrappers in this package route through `run()` so failure modes,
output capture, and dry-run handling are uniform.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ShellResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def render(self, max_lines: int = 80) -> str:
        out = self.stdout.strip()
        err = self.stderr.strip()
        if not out and not err:
            return f"(exit {self.returncode}, no output)"
        lines: list[str] = []
        if out:
            lines.append("--- stdout ---")
            lines.extend(out.splitlines()[:max_lines])
        if err:
            lines.append("--- stderr ---")
            lines.extend(err.splitlines()[:max_lines])
        lines.append(f"--- exit {self.returncode} ---")
        return "\n".join(lines)


def run(cmd: list[str], cwd: Path | str | None = None, check: bool = False) -> ShellResult:
    """Execute `cmd` and return a ShellResult. Never raises on non-zero exit
    unless `check=True`.
    """
    proc = subprocess.run(  # noqa: S603 — cmd is always a list, never shell=True
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=check,
    )
    return ShellResult(proc.returncode, proc.stdout, proc.stderr)


def dry_run_preview(action: str, **details: object) -> str:
    """Render a structured 'would have run' preview for dry_run=True."""
    lines = [f"DRY RUN — would {action}:"]
    for k, v in details.items():
        rendered = str(v)
        if len(rendered) > 400:
            rendered = rendered[:400] + " …(truncated)"
        lines.append(f"  {k}: {rendered}")
    return "\n".join(lines)
