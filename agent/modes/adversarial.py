"""Adversarial mode — BONUS walkthrough (workshop step 14, no points).

Run the same triage problem through three Patcher invocations with different
personas, then have a Judge (Opus) pick the best fix. This is primarily
a guided reading; the canonical walkthrough is the Boris Cherny / Jared Sumner
demo: https://www.youtube.com/watch?v=DlTCu_pNDHE&list=PLmWCw1CzcFim2obQ-w3ohbULOfwp5lApR&index=4

Personas (define these in prompts/patcher.md or inline below):
    - defensive   : prefers minimal, safe changes; adds null checks and guards
    - aggressive  : prefers root-cause fixes; willing to refactor surrounding code
    - conservative: prefers the smallest possible diff; no refactors

Skeleton steps:
    1. Read the issue (router/planner reuse from triage mode).
    2. Run 3 patchers in parallel with persona variants of the same prompt.
    3. Run a Judge agent (Opus, persona = "neutral senior reviewer") on the 3
       diffs side-by-side; ask for {"winner": int, "rationale": str}.
    4. Apply the winning diff, open the PR (or just print for the bonus).
"""

from __future__ import annotations

from agent.config import RunConfig
from agent.telemetry import TelemetryLogger


async def run(cfg: RunConfig) -> int:
    telemetry = TelemetryLogger()
    telemetry.run_start(mode="adversarial", url=cfg.url, dry_run=cfg.dry_run)

    try:
        # TODO bonus — implement only if you want to extend.
        # Personas could be a dict[str, str] of system-prompt suffixes layered
        # onto the base Patcher prompt.
        print(
            "Adversarial mode is the bonus walkthrough (step 14). It is intentionally\n"
            "left as a skeleton — see agent/modes/adversarial.py for the pattern."
        )
        telemetry.run_end(status="not_implemented")
        return 0
    except Exception:
        telemetry.run_end(status="error")
        raise
