# CCW Agentic System Lab

> Module 2.2 of the Provectus Claude Code Workshop — Advanced track.
> Build a dual-mode "PR & Issue Concierge" agentic system with the [Claude Agent SDK](https://docs.claude.com/en/docs/agent-sdk/overview).

In this lab you build an agent that operates against a real fork of [`provectus/ccw-inventory-management`](https://github.com/provectus/ccw-inventory-management) in two modes:

- **PR Review mode** (`review` command) — given a PR URL, the agent fans out per-file reviewers, synthesizes findings, and posts an inline review.
- **Issue Resolution mode** (`triage` command) — given an issue URL, the agent plans a fix, applies patches, runs tests, and opens a draft PR.

The scaffold provides the tedious parts (tool wrappers, SDK loop, telemetry, fixtures, setup script). **You write the parts where pedagogy matters**: the prompts, the orchestration in `agent/modes/*.py`, and the design document in `docs/design.md`.

---

## Prerequisites

| Requirement | Verify with |
|---|---|
| Python 3.11+ | `python3 --version` |
| `uv` package manager | `uv --version` (install: `curl -LsSf https://astral.sh/uv/install.sh \| sh`) |
| GitHub CLI authenticated | `gh auth status` |
| Anthropic API key | `echo $ANTHROPIC_API_KEY` |
| A GitHub account with permission to fork public repos | — |

Run `bash scripts/verify-env.sh` to check all of the above at once.

---

## Quickstart

```bash
# 1. Clone and install
git clone https://github.com/provectus/ccw-agentic-system-lab.git
cd ccw-agentic-system-lab
uv sync
cp .env.example .env
# edit .env to set ANTHROPIC_API_KEY

# 2. Set up the lab — forks ccw-inventory-management, plants the canned PR + issue
bash scripts/setup-lab.sh --dry-run    # inspect first
bash scripts/setup-lab.sh              # then run for real

# 3. Author your prompts (see prompts/*.md — start empty)
# 4. Implement agent/modes/review.py and agent/modes/triage.py
# 5. Run:
python -m agent review --dry-run       # uses URLs from .lab-state.json
python -m agent triage --dry-run
```

---

## Repo Layout

```
ccw-agentic-system-lab/
├── agent/                    # SDK loop, tool wrappers, mode implementations
│   ├── __main__.py           # python -m agent {review,triage,adversarial}
│   ├── loop.py               # Agent SDK setup and shared run()
│   ├── config.py             # model tiers, paths
│   ├── telemetry.py          # JSONL span logger
│   ├── modes/                # YOU WRITE — orchestration per mode
│   └── tools/                # pre-built gh, git, repo, tests wrappers
├── prompts/                  # YOU WRITE — coordinator, worker, synth prompts
├── fixtures/                 # Canned issues and a planted PR
├── scripts/                  # setup-lab.sh, teardown.sh, verify-env.sh
├── docs/                     # design.md (you fill), reference-design.md (key)
├── tests/                    # smoke tests
└── runs/                     # auto-created — JSONL telemetry per run
```

---

## What you write vs. what the scaffold provides

**Scaffold provides:**
- All tool wrappers in `agent/tools/*.py` — `gh` and `git` shell escaping is tedious and not pedagogically interesting.
- Telemetry logger in `agent/telemetry.py` — span-shaped JSONL records.
- Agent SDK loop in `agent/loop.py` — model selection, tool registration, message handling.
- Setup script in `scripts/setup-lab.sh` — forks the target repo, plants fixtures, opens canned PR + issue.
- Empty `prompts/*.md` files with frontmatter explaining what each prompt must specify.

**You write:**
- Prompts in `prompts/*.md` — the actual coordinator, worker, and synthesizer system prompts.
- Orchestration in `agent/modes/review.py` and `agent/modes/triage.py` — dispatching, parallelism, synthesis.
- The Critic in step 11 — an advisor escalation gate.
- `docs/design.md` content — your architecture decisions, justifications, rough cost estimate.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `gh auth status` fails | not logged in | `gh auth login` |
| `claude_agent_sdk` import error | venv not activated | `uv sync && source .venv/bin/activate` |
| `setup-lab.sh` fails on `gh repo fork` | already forked | safe to ignore; script skips if fork exists |
| Agent runs but posts nothing | `--dry-run` is on by default | re-run without `--dry-run` (after reviewing the preview) |
| Telemetry log missing | `runs/` not writable | check filesystem permissions; logs land at `runs/<iso-timestamp>.jsonl` |

See `docs/design.md` for the design exercise template and `docs/reference-design.md` for a facilitator-only answer key.
