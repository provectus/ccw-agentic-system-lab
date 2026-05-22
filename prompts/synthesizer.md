---
role: synthesizer
input: list of worker outputs (Reviewer findings OR Patcher diff + Planner plan)
output: a single human-consumable artifact — PR review body, or PR title+body+commit message
escalation: critic runs after the synthesizer in step 13
model_tier: Sonnet 4.6
---

<!--
Write your Synthesizer system prompt below.

In REVIEW mode, the Synthesizer receives a list of Reviewer findings (one
per file) and produces:
    - A top-level review body (3-5 sentences summarizing the PR)
    - A flat list of inline comments with {path, line, body}

In TRIAGE mode, the Synthesizer receives the Plan + final Patch and produces:
    - PR title (short, imperative — "fix: ..." or "feat: ...")
    - PR body (1-2 paragraphs: problem, fix, testing)
    - Commit message (Conventional Commits format if the repo uses it)

Suggested output shape — review mode:
    {"top_level": "...", "inline": [{"path": "...", "line": int, "body": "..."}, ...]}

Suggested output shape — triage mode:
    {"title": "...", "body": "...", "commit_message": "..."}

Calibrate the Synthesizer to DEDUPLICATE findings ("3 reviewers flagged
hardcoded credentials → emit one comment") and to ORDER inline comments
by file then line.
-->
