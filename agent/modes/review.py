"""Review mode — TODO scaffold (workshop step 9).

You are implementing the **orchestrator-workers** pattern:

    Router (Haiku)       — fetch PR metadata, classify
        ↓
    Coordinator (Sonnet) — split files into work units, dispatch in parallel
        ↓ ↓ ↓
    Reviewer × N (Opus)  — each reviews one file's hunks, returns findings
        ↓
    Synthesizer (Sonnet) — merges findings, formats inline comments + summary
        ↓
    gh_review_submit     — posts the review (honors cfg.dry_run)

Workshop step 13 adds a Critic (Opus) between Synthesizer and submit.

The scaffold already provides:
    - All tools (agent/tools/*) — see agent/loop.py for the registered set.
    - run_agent(role, system_prompt, user_message, telemetry, span_name)
      — your message-loop helper. Awaits one role's response.
    - load_prompt(name) — reads a prompt file by name (from prompts/<name>.md).

What you need to write:
    1. Use load_prompt() to read your prompts in.
    2. Call run_agent() for the Router to fetch PR metadata.
    3. Call run_agent() for the Coordinator to plan work units.
       Hint: parse its JSON output and use asyncio.gather() for parallelism.
    4. Call run_agent() per file for each Reviewer.
    5. Call run_agent() for the Synthesizer to merge findings.
    6. Call github_tools.gh_review_submit(...) to post (with cfg.dry_run).

Output format suggestion (negotiate this in your design.md):
    Coordinator → JSON {"work_units": [{"file": "...", "hunks": [...]}, ...]}
    Reviewer    → JSON {"findings": [{"line": int, "severity": str, "body": str}, ...]}
    Synthesizer → JSON {"top_level": "...", "inline": [{"path": "...", "line": int, "body": "..."}, ...]}
"""

from __future__ import annotations

from agent.config import RunConfig
from agent.telemetry import TelemetryLogger


async def run(cfg: RunConfig) -> int:
    """Entry point called by python -m agent review <pr_url>.

    Return 0 on success, non-zero on failure.
    """
    telemetry = TelemetryLogger()
    telemetry.run_start(mode="review", url=cfg.url, dry_run=cfg.dry_run)

    try:
        # TODO step 9.1 — Router: fetch PR diff and file list.
        # router_prompt = load_prompt("router")
        # router_output = await run_agent("router", router_prompt, ..., telemetry, "router.dispatch")

        # TODO step 9.2 — Coordinator: plan work units.
        # coordinator_prompt = load_prompt("coordinator")
        # plan = await run_agent("coordinator", coordinator_prompt, ..., telemetry, "coordinator.plan")

        # TODO step 9.3 — Reviewers (parallel via asyncio.gather).
        # reviewer_prompt = load_prompt("reviewer")
        # findings = await asyncio.gather(*[
        #     run_agent("reviewer", reviewer_prompt, ..., telemetry, f"reviewer.{unit.file}")
        #     for unit in plan.work_units
        # ])

        # TODO step 13 — Critic gate (advisor pattern). Add after step 11 in the workshop.
        # critic_prompt = load_prompt("critic")
        # critique = await run_agent("critic", critic_prompt, ..., telemetry, "critic.review")

        # TODO step 9.4 — Synthesizer: merge findings into one review.
        # synthesizer_prompt = load_prompt("synthesizer")
        # review = await run_agent("synthesizer", synthesizer_prompt, ..., telemetry, "synth.merge")

        # TODO step 9.5 — Submit.
        # from agent.tools import github as github_tools
        # github_tools.gh_review_submit(cfg.url, "COMMENT", review.top_level, dry_run=cfg.dry_run)
        # for item in review.inline:
        #     github_tools.gh_pr_comment(cfg.url, item.path, item.line, item.body, dry_run=cfg.dry_run)

        print(
            "Review mode is not implemented yet. See agent/modes/review.py for TODOs.\n"
            "Refer to workshop step 9 in claudesdk-agentic-system-lab.json."
        )
        telemetry.run_end(status="not_implemented")
        return 1
    except Exception:
        telemetry.run_end(status="error")
        raise
