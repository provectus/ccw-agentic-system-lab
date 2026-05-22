# Agent System Design — your worksheet

**Workshop step 5.** Fill this out before you write any prompts or orchestration code.
You will defend each choice in a one-sentence justification.

Time budget: ~20 minutes. Don't optimize for completeness — optimize for **defensible decisions**.

---

## 1. Work decomposition

For each mode, what units of work exist? Which can run in parallel? Which must run in sequence?

### Review mode

- Work units:
- Parallel:
- Sequential:

### Triage mode

- Work units:
- Parallel:
- Sequential:

---

## 2. Pattern choice

For each mode, which of these patterns are you using and why?

- **Orchestrator-workers** — coordinator splits work; workers run independently in parallel.
- **Pipeline** — sequential stages; each stage's output is the next stage's input.
- **Advisor (critic)** — a second model reviews the first model's output before it ships.

| Mode | Pattern | Why |
|---|---|---|
| Review | | |
| Triage | | |

References: [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents).

---

## 3. Model tier assignment

For each role, which model tier and why?

| Role | Model | Why |
|---|---|---|
| Router | Haiku 4.5 | |
| Coordinator | Sonnet 4.6 | |
| Reviewer | Opus 4.7 | |
| Planner | Sonnet 4.6 | |
| Patcher | Sonnet 4.6 | |
| Critic | Opus 4.7 | |
| Synthesizer | Sonnet 4.6 | |

If you change any of the defaults in `agent/config.py`, justify it here.

---

## 4. Tool surface review

The scaffold registers these tools (see `agent/loop.py`):

- GitHub: `gh_pr_diff`, `gh_pr_files`, `gh_pr_comment`, `gh_review_submit`, `gh_issue_read`, `gh_pr_create`
- Git: `git_checkout`, `git_apply`, `git_commit`, `git_push`
- Repo (sandboxed to workspace): `read_file`, `grep`, `glob`
- Tests: `run_pytest`, `run_npm_test`

Questions to answer:

- Are there tools you wish the scaffold provided that you'll work around? (e.g. inline-comment-batched, branch-rename, file-write)
- Are there tools you will NOT give to specific roles? (e.g. should the Reviewer be able to call `git_push`? Probably no.)
- How will side-effecting tools be gated? (default: `dry_run=True` everywhere; flip via the CLI flag)

---

## 5. Output contracts

For each role you'll invoke, what structured format do you expect the model to return?

Suggested templates live in the corresponding `prompts/*.md` frontmatter. Confirm or override here.

| Role | Output shape |
|---|---|
| Router | |
| Coordinator | |
| Reviewer | |
| Planner | |
| Patcher | |
| Critic | |
| Synthesizer | |

---

## 6. Rough cost estimate (informational)

Back-of-envelope: ~$2 per run for a typical PR (~10 files, ~500 LOC diff) using the default model tiers.

If you change tiers (e.g. downgrade Reviewer to Sonnet), what's your new estimate?

- Per Reviewer call (Opus, ~5k in / ~600 out): ~$0.10
- Per Reviewer call (Sonnet, ~5k in / ~600 out): ~$0.018
- 10 files × Opus: ~$1.00 just for reviewers; with Sonnet: ~$0.18

Estimate:
