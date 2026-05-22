"""Configuration: model tiers per role, paths, defaults.

Override any value via environment variables (see .env.example). Defaults
match the Joplin spec §System Architecture role-to-model table.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Role = Literal[
    "router",
    "coordinator",
    "reviewer",
    "planner",
    "patcher",
    "critic",
    "synthesizer",
]

# Anthropic model IDs. Keep these in one place so step 4 ("read agent/loop.py")
# can show participants exactly where model selection lives.
MODEL_HAIKU = "claude-haiku-4-5"
MODEL_SONNET = "claude-sonnet-4-6"
MODEL_OPUS = "claude-opus-4-7"


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


ROLE_MODEL_MAP: dict[Role, str] = {
    "router": _env("AGENT_MODEL_ROUTER", MODEL_HAIKU),
    "coordinator": _env("AGENT_MODEL_COORDINATOR", MODEL_SONNET),
    "reviewer": _env("AGENT_MODEL_WORKER", MODEL_OPUS),
    "planner": _env("AGENT_MODEL_COORDINATOR", MODEL_SONNET),
    "patcher": _env("AGENT_MODEL_PATCHER", MODEL_SONNET),
    "critic": _env("AGENT_MODEL_CRITIC", MODEL_OPUS),
    "synthesizer": _env("AGENT_MODEL_SYNTHESIZER", MODEL_SONNET),
}


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = Path(_env("AGENT_WORKSPACE_DIR", str(REPO_ROOT / "workspace")))
TELEMETRY_DIR = Path(_env("AGENT_TELEMETRY_DIR", str(REPO_ROOT / "runs")))
PROMPTS_DIR = REPO_ROOT / "prompts"
FIXTURES_DIR = REPO_ROOT / "fixtures"
LAB_STATE_FILE = REPO_ROOT / ".lab-state.json"

# Repo the lab operates against. Forked into the participant's account by
# scripts/setup-lab.sh, then cloned into WORKSPACE_DIR.
TARGET_REPO_UPSTREAM = "provectus/ccw-inventory-management"
TARGET_REPO_DIR_NAME = "ccw-inventory-management"
TARGET_BRANCH = "lab/agent-target"


@dataclass(frozen=True)
class RunConfig:
    """Per-invocation configuration assembled by __main__.py."""

    mode: Literal["review", "triage", "adversarial"]
    url: str | None
    dry_run: bool
    verbose: bool = False


def pick_model(role: Role) -> str:
    """Return the model ID for a given agent role.

    Participants reference this in step 4 (walkthrough of agent/loop.py)
    and step 5 (design exercise — model tier justification).
    """
    return ROLE_MODEL_MAP[role]
