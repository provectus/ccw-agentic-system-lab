# Agent System Design — your worksheet

**Workshop step 5.** Fill this out before you write any prompts or orchestration code.
You will defend each choice in a one-sentence justification.

Time budget: ~20 minutes. Don't optimize for completeness — optimize for **defensible decisions**.

---

## What you're building (read this first)

Steps 1–4 toured the **harness** — the pre-built code in this repo (the SDK loop in
`agent/loop.py`, the tool wrappers, telemetry, model routing). This step is about the
*system* that runs on top of it. Before you decompose anything, get crisp on what that
system actually does.

You are building a **PR & Issue Concierge**: an agent that operates on a real GitHub
repo (your fork of `ccw-inventory-management`) in two modes. Each mode takes a single
URL as input and produces a single concrete artifact on GitHub as output:

| Mode | Input | What it does | Output |
|---|---|---|---|
| **PR Review** (`review`) | a PR URL | reads the diff, reviews each changed file for bugs/security/perf/test-gaps/style, merges the findings | posts a PR **review** — a top-level summary plus inline comments on specific lines |
| **Issue Resolution** (`triage`) | an issue URL | reads the issue, plans a fix as file-scoped changes, edits the code, runs the tests | opens a **draft PR** with the patch, a Conventional-Commits title, and a body explaining the fix |

> The CLI commands keep their original short names — `python -m agent review …` and
> `python -m agent triage …` — so the names you'll see in code (`agent/modes/review.py`,
> `agent/modes/triage.py`) line up with the commands. This worksheet uses the clearer
> labels **PR Review** and **Issue Resolution** throughout.

The catch: doing either well in a *single* model call is unreliable. A 10-file PR review
asks one prompt to hold every file in context, weigh severity consistently, and format
inline comments — quality degrades and cost balloons. So instead you **decompose** the
work across several specialized **roles** (Router, Coordinator, Reviewer, Planner,
Patcher, Critic, Synthesizer). Each role is one `run_agent()` turn with its own system
prompt and its own model tier. The design exercise below is deciding *how* to split the
work across those roles — what runs in parallel, what must run in order, who gets which
model, and what each role hands to the next.

That is the whole game: **turn "review this PR" into a small org chart of cheap+smart
model calls that, together, beat one expensive call.**

---

## The roles

The intro names seven roles. Here's what each is **responsible for** and where it runs —
the job descriptions you'll need to answer §3 and §5. Deciding each role's *model tier*
(§3) and its exact *structured output* (§5) is the exercise; this table is just the "what
does this role do" you shouldn't have to guess. The authoritative spec for each —
`input`, `output`, `escalation`, `model_tier` — lives in the frontmatter of the matching
`prompts/<role>.md`.

| Role | Runs in | Responsible for | Reads → produces (conceptually) | Default tier |
|---|---|---|---|---|
| **Router** | both | Classify the input URL and fetch its metadata, then forward | a PR/issue URL → metadata for the Coordinator or Planner | Haiku |
| **Coordinator** | PR Review | Split the PR's changed files into independent, parallel-dispatchable work units | Router's PR metadata → a list of work units | Sonnet |
| **Reviewer** (×N) | PR Review | Examine **one** work unit and report the issues it finds | one work unit (file + hunks + context) → line-anchored findings with severity | Opus |
| **Planner** | Issue Resolution | Read the issue and propose an ordered list of file-scoped changes | issue body (may explore the repo) → an ordered fix plan | Sonnet |
| **Patcher** | Issue Resolution | Turn one plan step (or Critic feedback) into a concrete code change | one plan step → a unified diff that applies cleanly | Sonnet |
| **Critic** | both (added in step 13) | The advisor gate: judge whether the work is good enough to ship | a proposed review or patch → APPROVE / REQUEST_CHANGES + feedback | Opus |
| **Synthesizer** | both | Merge the workers' outputs into the single artifact that gets posted | Reviewer findings, *or* Planner plan + Patcher diff → the PR review, *or* the PR title + body + commit message | Sonnet |

Note how the roles chain: each row's "produces" is the next role's "reads". That hand-off
is exactly what §5 (output contracts) asks you to formalize.

---

## Key terms

Pin these down before filling in the tables — the worksheet uses them throughout.

- **Role** — a single specialized step in the pipeline (Router, Reviewer, Critic, …).
  In code it's one call to `run_agent(role, prompt, …)` with one system prompt and one
  model tier. Roles don't share memory; whatever one role needs from another travels in
  the message you pass it.
- **Work unit** — *the* term to nail down. A work unit is the **smallest self-contained
  chunk of input that one worker can handle on its own, in a single turn, without needing
  the others.** Self-contained is the key word: it must carry enough context to be
  worked in isolation. Good work units are what make parallelism possible — if you can
  cut the input into N independent units, you can run N workers at once.
  *Analogy:* to proofread a 300-page book with a team, the natural work unit is one
  chapter — each proofreader gets a chapter plus a one-line synopsis, and they all work
  at the same time. **Your job in §1 is to decide what the equivalent "chapter" is for a
  PR diff and for an issue fix** — and how big is too big (when do you split one further?).
- **Pattern** — the named shape of how roles connect (orchestrator-workers, pipeline,
  advisor/critic). See §2 and *Building Effective Agents*.
- **Model tier** — which model a role runs on (Haiku / Sonnet / Opus). Cheaper tiers for
  cheap/mechanical roles, smarter tiers for the judgement-heavy ones. Set in
  `agent/config.py:ROLE_MODEL_MAP`; see §3.
- **Output contract** — the structured shape (usually JSON) a role must return so the
  *next* role can consume it programmatically. If the Reviewer doesn't return a `line`,
  the Synthesizer can't post an inline comment. See §5.
- **dry_run** — every side-effecting tool defaults to `dry_run=True`, returning a preview
  of what it *would* do instead of doing it. The `--dry-run` CLI flag (on by default)
  flows into your tool calls as `cfg.dry_run`. See §4.

---

## 1. Work decomposition

For each mode, what units of work exist? Which can run in parallel? Which must run in sequence?

Use these questions to drive your answer (don't just list roles — decide the **granularity**):

- **What is one work unit?** What's the "chapter" — a whole PR? one changed file? one hunk?
  For Issue Resolution: the whole issue, or one file-scoped step of the fix plan?
- **When is a unit too big to handle in one turn?** e.g. a 600-line file — split by hunk?
  Leave it whole? What about binary or unchanged files?
- **How many workers run at once?** Is there a cap (rate limits, cost), or unbounded?
- **What is strictly ordered?** Which role's output is another role's *required* input,
  so it can't start early?

### PR Review mode (`review`)

- One work unit is: 
- Splitting rule (when a unit is too big / should be skipped):
- Parallel (and max concurrent workers):
- Sequential (what must finish before what):

### Issue Resolution mode (`triage`)

- One work unit is:
- Splitting rule:
- Parallel:
- Sequential:

---

## 2. Pattern choice

For each mode, which of these patterns are you using and why?

- **Orchestrator-workers** — a coordinator splits the input into work units; independent
  workers process them in parallel; results are merged. Best when the work is
  "*embarrassingly parallel*" (units don't depend on each other).
- **Pipeline** — sequential stages; each stage's output is the next stage's input. Best
  when steps are inherently ordered (you can't run a test before you've written the fix).
- **Advisor (critic)** — a second model reviews the first model's output before it ships,
  and can send it back for revision. You add this to both modes in step 13.

| Mode | Pattern | Why (one sentence) |
|---|---|---|
| PR Review (`review`) | | |
| Issue Resolution (`triage`) | | |

Reference: [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents).

---

## 3. Model tier assignment

For each role, which model tier and why? (What each role *does* is in **The roles** above.)
The defaults below are reasonable — your job is to be able to **defend or override** them.
Think about it this way: a role earns Opus when
a wrong answer is *expensive* (a bad review wastes engineer time; a bad merge ships a bug),
and earns Haiku when the work is mechanical (parsing a URL, classifying input).

| Role | Model | Why (one sentence) |
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

The harness registers these tools (see `agent/loop.py`):

- GitHub: `gh_pr_diff`, `gh_pr_files`, `gh_pr_comment`, `gh_review_submit`, `gh_issue_read`, `gh_pr_create`
- Git: `git_checkout`, `git_apply`, `git_commit`, `git_push`
- Repo (sandboxed to workspace): `read_file`, `grep`, `glob`
- Tests: `run_pytest`, `run_npm_test`

Questions to answer:

- Are there tools you wish the harness provided that you'll work around? (e.g. inline-comment-batched, branch-rename, file-write)
- Are there tools you will NOT give to specific roles? The SDK won't restrict tools per
  role automatically — you enforce it in the prompt. (e.g. should the Reviewer be able to
  call `git_push`? Probably no. Which single role should own `gh_review_submit`?)
- How will side-effecting tools be gated? (default: `dry_run=True` everywhere; flip via the CLI flag)

---

## 5. Output contracts

For each role you'll invoke, what structured format do you expect the model to return?
Remember the test: **can the next role consume this output programmatically?** A role's
contract exists to feed the role downstream of it — design backward from what the consumer
needs (e.g. the Synthesizer needs `line` numbers to post inline comments, so the Reviewer
must emit them).

Suggested templates live in the corresponding `prompts/*.md` frontmatter, and **The roles**
table above lists what each role reads and produces. Confirm or override here.

| Role | Output shape | Who consumes it |
|---|---|---|
| Router | | |
| Coordinator | | |
| Reviewer | | |
| Planner | | |
| Patcher | | |
| Critic | | |
| Synthesizer | | |

---

## 6. Rough cost estimate (informational)

Back-of-envelope: ~$2 per run for a typical PR (~10 files, ~500 LOC diff) using the default model tiers.

If you change tiers (e.g. downgrade Reviewer to Sonnet), what's your new estimate?

- Per Reviewer call (Opus, ~5k in / ~600 out): ~$0.10
- Per Reviewer call (Sonnet, ~5k in / ~600 out): ~$0.018
- 10 files × Opus: ~$1.00 just for reviewers; with Sonnet: ~$0.18

Estimate:
