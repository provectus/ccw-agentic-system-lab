"""CLI entry point: python -m agent {review,triage,adversarial} [url] [--dry-run]

Defaults: when no URL is passed, falls back to URLs in .lab-state.json
written by scripts/setup-lab.sh.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from agent.config import LAB_STATE_FILE, RunConfig


def _load_default_url(mode: str) -> str | None:
    if not LAB_STATE_FILE.exists():
        return None
    try:
        state = json.loads(LAB_STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if mode == "review":
        return state.get("pr_url")
    if mode in ("triage", "adversarial"):
        return state.get("issue_url")
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent",
        description="CCW Agentic System Lab — dual-mode PR & Issue Concierge.",
    )
    parser.add_argument(
        "mode",
        choices=["review", "triage", "adversarial"],
        help="review: analyze a PR. triage: read an issue → open draft PR. adversarial: bonus walkthrough.",
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help="PR URL (review) or issue URL (triage/adversarial). Defaults to .lab-state.json.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview side effects (PR comments, pushes) without executing. Default: True.",
    )
    parser.add_argument(
        "--no-dry-run",
        action="store_false",
        dest="dry_run",
        help="Actually post comments, push branches, and open PRs.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print extra debug output to stderr.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    url = args.url or _load_default_url(args.mode)
    if url is None:
        print(
            f"ERROR: no URL provided and no .lab-state.json default for mode={args.mode!r}.\n"
            "Run scripts/setup-lab.sh first, or pass a URL explicitly.",
            file=sys.stderr,
        )
        return 2

    cfg = RunConfig(mode=args.mode, url=url, dry_run=args.dry_run, verbose=args.verbose)

    if args.verbose:
        print(f"[agent] mode={cfg.mode} url={cfg.url} dry_run={cfg.dry_run}", file=sys.stderr)

    # Late imports so `--help` works even before participants have authored prompts.
    if cfg.mode == "review":
        from agent.modes.review import run as run_mode
    elif cfg.mode == "triage":
        from agent.modes.triage import run as run_mode
    else:
        from agent.modes.adversarial import run as run_mode

    return asyncio.run(run_mode(cfg))


if __name__ == "__main__":
    raise SystemExit(main())
