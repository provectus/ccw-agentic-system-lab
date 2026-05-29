"""Issue Resolution mode (`triage` command) — TODO scaffold (workshop step 11).

You are implementing a **sequential pipeline** with intra-step parallelism:

    Router (Haiku)       — fetch issue body, classify
        ↓
    Planner (Sonnet)     — propose fix as a list of file-scoped changes
        ↓
    Patcher (Sonnet)     — apply each change via git_apply or direct edits
        ↓
    Critic (Opus)        — (step 13) review the patch before PR
        ↓ (revision loop if requested)
    run_pytest           — validate the patched code
        ↓
    Synthesizer (Sonnet) — assemble PR title, body, commit message
        ↓
    git_commit + git_push + gh_pr_create  — open draft PR (honors cfg.dry_run)

What you need to write:
    1. load_prompt() each role's prompt.
    2. Router → Planner → Patcher → tests → Critic → Synthesizer.
    3. Wire the critic revision loop in step 13:
        - If critic returns REQUEST_CHANGES, re-invoke Patcher with feedback.
        - Cap re-runs at 2 to avoid runaway cost.
    4. Open the draft PR via github_tools.gh_pr_create(... dry_run=cfg.dry_run).

Output format suggestion:
    Planner    → JSON {"plan": [{"file": "...", "intent": "...", "diff_sketch": "..."}, ...]}
    Patcher    → JSON {"diff": "<unified diff>", "summary": "..."}
    Critic     → JSON {"event": "APPROVE"|"REQUEST_CHANGES", "feedback": "..."}
    Synthesizer→ JSON {"title": "...", "body": "...", "commit_message": "..."}
"""

from __future__ import annotations

from agent.config import RunConfig
from agent.telemetry import TelemetryLogger


async def run(cfg: RunConfig) -> int:
    telemetry = TelemetryLogger()
    telemetry.run_start(mode="triage", url=cfg.url, dry_run=cfg.dry_run)

    try:
        # TODO step 11.1 — Router: read the issue.
        # router_prompt = load_prompt("router")
        # issue = await run_agent("router", router_prompt, ..., telemetry, "router.dispatch")

        # TODO step 11.2 — Planner.
        # planner_prompt = load_prompt("planner")
        # plan = await run_agent("planner", planner_prompt, issue, telemetry, "planner.plan")

        # TODO step 11.3 — Patcher.
        # patcher_prompt = load_prompt("patcher")
        # patch = await run_agent("patcher", patcher_prompt, plan, telemetry, "patcher.apply")
        # from agent.tools import git as git_tools
        # git_tools.git_apply(patch.diff, dry_run=cfg.dry_run)

        # TODO step 13 — Critic gate with revision loop.
        # critic_prompt = load_prompt("critic")
        # for attempt in range(2):
        #     critique = await run_agent("critic", critic_prompt, patch, telemetry, f"critic.{attempt}")
        #     if critique.event == "APPROVE":
        #         break
        #     patch = await run_agent("patcher", patcher_prompt, critique.feedback, telemetry, f"patcher.rev{attempt}")

        # TODO step 11.4 — Validate.
        # from agent.tools import tests as test_tools
        # test_output = test_tools.run_pytest("")
        # telemetry.tool_call("run_pytest", output_summary=test_output[-500:])

        # TODO step 11.5 — Synthesizer.
        # synth_prompt = load_prompt("synthesizer")
        # pr_meta = await run_agent("synthesizer", synth_prompt, ..., telemetry, "synth.pr_body")

        # TODO step 11.6 — Commit + push + open PR.
        # git_tools.git_commit(pr_meta.commit_message, dry_run=cfg.dry_run)
        # git_tools.git_push(dry_run=cfg.dry_run)
        # github_tools.gh_pr_create(
        #     repo="<owner>/<fork>", head="<branch>", base="main",
        #     title=pr_meta.title, body=pr_meta.body,
        #     draft=True, dry_run=cfg.dry_run,
        # )

        print(
            "Issue Resolution mode is not implemented yet. See agent/modes/triage.py for TODOs.\n"
            "Refer to workshop step 11 in claudesdk-agentic-system-lab.json."
        )
        telemetry.run_end(status="not_implemented")
        return 1
    except Exception:
        telemetry.run_end(status="error")
        raise
