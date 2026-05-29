# Reference Design — facilitator answer key

**Do not share with participants until after step 5.**

This is the canonical answer to `docs/design.md`. Use it to coach participants who are stuck, and to evaluate the design exercises in workshop step 5.

---

## 1. Work decomposition

**Review mode** — work units are *files*. Each file's hunks are reviewed independently.
- **Parallel**: file-level reviewers (cap at ~8 to control cost and rate limits).
- **Sequential**: Router → Coordinator → (parallel Reviewers) → Synthesizer → Submit.

**Triage mode** — work units are *file-scoped changes* in a plan.
- **Parallel**: only within Patcher if the plan touches multiple independent files. Most fixes are sequential.
- **Sequential**: Router → Planner → Patcher → tests → (step 13) Critic → Synthesizer → PR.

---

## 2. Pattern choice

| Mode | Pattern | Why |
|---|---|---|
| Review | Orchestrator-workers, parallel | File-scoped review is **embarrassingly parallel**. Coordinator does cheap planning; expensive Opus reviewers run independently. |
| Triage | Pipeline (sequential) with optional intra-Patcher parallelism, plus Advisor (critic) in step 13 | Fix-and-test is inherently ordered: you can't write the test before you know the fix. Critic catches plan/patch mismatches before opening a PR. |

The Critic is the **advisor** pattern from Building Effective Agents. In step 13, we add it to *both* modes.

---

## 3. Model tier assignment

The defaults in `agent/config.py` reflect the consensus rationale:

| Role | Default Model | Reasoning |
|---|---|---|
| Router | Haiku | Classification + URL parsing. Cheap, fast, no reasoning needed. |
| Coordinator | Sonnet | Light planning. Sonnet handles "split N files into M work units" easily. |
| Reviewer | Opus | THE quality-load-bearing call. False positives in reviews are expensive (engineer time); false negatives are expensive (bugs ship). Opus pays off here. |
| Planner | Sonnet | Reading a bug report and proposing 1-3 file changes is well within Sonnet's range. |
| Patcher | Sonnet | Writing small diffs to fix known bugs is a sweet spot for Sonnet. Opus only helps if the bug is genuinely hard. |
| Critic | Opus | The whole point of the critic is "would a senior reviewer ship this?" Use the smartest model. |
| Synthesizer | Sonnet | Merging structured worker outputs into prose. Sonnet is fine. |

**Cost guidance**: a typical PR review with these defaults is ~$1-2 per run. Downgrading Reviewer from Opus to Sonnet drops to ~$0.30 with a measurable quality hit. Probably not worth it.

---

## 4. Tool surface review

The scaffold's tool surface is intentionally minimal. Calibrate the design exercise around:

- The Reviewer should NEVER need git or PR-modifying tools. Restrict via prompt — the SDK won't gate by role automatically.
- The Synthesizer is the only role that should invoke `gh_pr_comment` and `gh_review_submit`.
- For `run_npm_test`, expect the agent to call it once after a patch. If it calls more than 2-3 times in a single run, the critic should have caught the issue earlier.

---

## 5. Output contracts

Match the templates in `prompts/*.md`. The non-negotiables:

- Reviewer must emit per-line findings with severity. Without `line` the Synthesizer cannot post inline comments.
- Patcher must emit a unified diff. Free-form "here's how I'd fix it" prose breaks `git_apply`.
- Critic must emit `event: APPROVE | REQUEST_CHANGES`. The orchestration code branches on this string.

---

## 6. Cost estimate

For the lab's planted PR (~3 files touched, ~150 LOC diff):

- 3 Reviewers × Opus × ~4k in / ~500 out ≈ $0.24
- Coordinator + Synthesizer (Sonnet, 2 calls) ≈ $0.02
- Critic (Opus, 1 call) ≈ $0.08
- **Total per review run ≈ $0.35**

For the canned issue (single-file fix):

- Router (Haiku) ≈ $0.001
- Planner + Patcher + Synthesizer (Sonnet, ~3 calls) ≈ $0.03
- Critic (Opus) ≈ $0.05
- **Total per triage run ≈ $0.08**

Real-world PRs cost more (more files, more revision loops). The $2 target in the brief is informational — runs that exceed it during the workshop are fine and should be discussed in bonus step 15.

---

## Common stumbling points

1. **Participants forget `dry_run=cfg.dry_run`** in their orchestration. They run without `--dry-run` first and spam the PR. Add a callout in step 10/12 — "verify --dry-run is in your tool calls before the real run."
2. **Reviewer prompt is too generic** ("review this code") and produces "looks good!" findings. The prompt needs explicit categories to look for (correctness, security, perf, tests, style) and ONE example finding.
3. **Synthesizer hallucinates line numbers** when merging. Workaround: have the Reviewer emit `(path, line, body)` tuples and have the Synthesizer just pass them through, not reformat them.
4. **Step 13's critic loops forever** because the patcher never satisfies it. The provided scaffold caps revisions at 2; participants who write their own loop sometimes omit the cap. Coach them to add it.
5. **Costs surprise people in step 15.** Some participants assume Sonnet "looks similar enough" to Opus and downgrade everything; their telemetry log shows the same quality but the Critic stops catching things. Use this as the teaching moment.
