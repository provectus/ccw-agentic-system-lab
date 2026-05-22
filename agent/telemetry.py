"""JSONL span logger for the agent loop.

One file per run at TELEMETRY_DIR/<iso-timestamp>.jsonl. Each line is a
self-contained record; lines reconstruct an execution tree via parent_span_id.

Inspired by ab-casdk-harness/src/harness/tracer/base.py but intentionally
~100 lines: no exporter protocol, no decorators, no cross-process propagation.

Record kinds:
    run_start, run_end, model_call, tool_call, error

Example record:
    {
      "ts": "2026-05-22T14:32:11.421Z",
      "trace_id": "abc123def456",
      "span_id": "def456789",
      "parent_span_id": "abc123def456",
      "kind": "model_call",
      "name": "reviewer.file_review",
      "role": "reviewer",
      "model": "claude-opus-4-7",
      "tokens_in": 4823,
      "tokens_out": 612,
      "tokens_cached": 1200,
      "cost_usd": 0.0934,
      "duration_ms": 8412,
      "status": "ok",
      "attributes": {"file": "src/api/suppliers.py", "hunk_count": 3}
    }
"""

from __future__ import annotations

import json
import secrets
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Literal

from agent.config import TELEMETRY_DIR

Kind = Literal["run_start", "run_end", "model_call", "tool_call", "error"]


def _hex(n_bytes: int) -> str:
    return secrets.token_hex(n_bytes)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class TelemetryLogger:
    """One logger per agent run. Thread-safe is NOT a goal."""

    def __init__(self, trace_id: str | None = None, log_dir: Path | None = None):
        self.trace_id = trace_id or _hex(6)
        self.log_dir = log_dir or TELEMETRY_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        ts = _now_iso().replace(":", "-").replace(".", "-")
        self.path = self.log_dir / f"{ts}_{self.trace_id}.jsonl"
        self._stack: list[str] = []  # span_id stack for parent inference

    def _write(self, record: dict[str, Any]) -> None:
        record.setdefault("ts", _now_iso())
        record.setdefault("trace_id", self.trace_id)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def _new_span(self) -> tuple[str, str | None]:
        span_id = _hex(4)
        parent = self._stack[-1] if self._stack else None
        return span_id, parent

    def run_start(self, mode: str, url: str | None, dry_run: bool) -> str:
        span_id, parent = self._new_span()
        self._stack.append(span_id)
        self._write({
            "span_id": span_id,
            "parent_span_id": parent,
            "kind": "run_start",
            "name": f"run.{mode}",
            "attributes": {"url": url, "dry_run": dry_run},
        })
        return span_id

    def run_end(self, status: str = "ok", **attrs: Any) -> None:
        span_id = self._stack.pop() if self._stack else None
        parent = self._stack[-1] if self._stack else None
        self._write({
            "span_id": span_id,
            "parent_span_id": parent,
            "kind": "run_end",
            "name": "run.end",
            "status": status,
            "attributes": attrs,
        })

    @contextmanager
    def span(self, name: str, kind: Kind = "model_call", **attrs: Any) -> Iterator[str]:
        """Open a nested span. Use for model_call and tool_call records."""
        span_id, parent = self._new_span()
        self._stack.append(span_id)
        start = time.perf_counter()
        record: dict[str, Any] = {
            "span_id": span_id,
            "parent_span_id": parent,
            "kind": kind,
            "name": name,
            "status": "ok",
            "attributes": dict(attrs),
        }
        try:
            yield span_id
        except Exception as exc:  # noqa: BLE001 — telemetry must not mask the error
            record["status"] = "error"
            record["attributes"]["error"] = repr(exc)
            self._write(record)
            self.error(name, exc, span_id=span_id)
            self._stack.pop()
            raise
        else:
            record["duration_ms"] = int((time.perf_counter() - start) * 1000)
            self._write(record)
            self._stack.pop()

    def model_call(
        self,
        name: str,
        role: str,
        model: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        tokens_cached: int = 0,
        cost_usd: float = 0.0,
        duration_ms: int = 0,
        **attrs: Any,
    ) -> None:
        """Record a completed model call. Use when you already have token counts."""
        _, parent = self._new_span()
        self._write({
            "span_id": _hex(4),
            "parent_span_id": parent,
            "kind": "model_call",
            "name": name,
            "role": role,
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "tokens_cached": tokens_cached,
            "cost_usd": cost_usd,
            "duration_ms": duration_ms,
            "status": "ok",
            "attributes": attrs,
        })

    def tool_call(
        self,
        tool: str,
        args_summary: str = "",
        output_summary: str = "",
        duration_ms: int = 0,
        status: str = "ok",
        **attrs: Any,
    ) -> None:
        _, parent = self._new_span()
        self._write({
            "span_id": _hex(4),
            "parent_span_id": parent,
            "kind": "tool_call",
            "name": f"tool.{tool}",
            "tool": tool,
            "args_summary": args_summary[:500],
            "output_summary": output_summary[:500],
            "duration_ms": duration_ms,
            "status": status,
            "attributes": attrs,
        })

    def error(self, name: str, exc: BaseException, span_id: str | None = None) -> None:
        _, parent = self._new_span()
        self._write({
            "span_id": span_id or _hex(4),
            "parent_span_id": parent,
            "kind": "error",
            "name": name,
            "status": "error",
            "attributes": {
                "error_type": type(exc).__name__,
                "error_message": str(exc)[:1000],
            },
        })
