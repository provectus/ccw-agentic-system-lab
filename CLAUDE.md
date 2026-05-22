# ccw-agentic-system-lab — Claude Code memory

Lab scaffold for the Provectus CCW Module 2.2 workshop: participants build a dual-mode "PR & Issue Concierge" with the Claude Agent SDK.

## Entry points

- `python -m agent {review,triage,adversarial} [url] [--dry-run]` — main CLI
- `bash scripts/setup-lab.sh` — forks `provectus/ccw-inventory-management`, plants canned PR + issue
- `pytest tests/smoke.py` — smoke tests

## Layout

- `agent/loop.py` — Claude Agent SDK setup, role→model mapping, shared run loop
- `agent/tools/{github,git,repo,tests}.py` — pre-built tool wrappers, all support `dry_run=True`
- `agent/modes/{review,triage,adversarial}.py` — **TODO scaffolds** participants fill in
- `agent/telemetry.py` — JSONL span logger; output at `runs/<iso-timestamp>.jsonl`
- `prompts/*.md` — **empty** files with frontmatter; participants author during the workshop

## Conventions

- Side-effecting tools (`gh pr comment`, `gh pr create`, `git push`) accept `dry_run: bool` that returns a structured preview instead of executing.
- Model tier per role: Router=Haiku 4.5, Coordinator/Planner/Patcher/Synthesizer=Sonnet 4.6, Reviewer/Critic=Opus 4.7. Defaults in `agent/config.py`; override via env vars (see `.env.example`).
- All shell calls go through `subprocess.run(capture_output=True, text=True, check=False)` — no `shell=True`.
- Sandboxed file ops: `agent/tools/repo.py` only reads inside `./workspace/ccw-inventory-management`.

## Telemetry record kinds

`run_start`, `run_end`, `model_call`, `tool_call`, `error`. Parent/child via `parent_span_id`. Schema in `agent/telemetry.py`.

## Lab state

`./. lab-state.json` (created by `setup-lab.sh`) holds the canned PR URL and issue URL. The agent defaults to these when no URL is passed on the CLI.

## Reference design

Facilitator-only answer key for the design exercise lives at `docs/reference-design.md`. Do not share with participants until after step 4.
