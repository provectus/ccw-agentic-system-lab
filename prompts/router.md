---
role: router
input: PR URL (review mode) OR issue URL (triage mode)
output: structured metadata for the coordinator/planner
escalation: none — the router does not escalate, it only classifies and forwards
model_tier: Haiku 4.5 (cheap, fast classification)
---

<!--
Write your Router system prompt below.

The Router fetches the input (PR diff/files OR issue body), summarizes it,
and emits a small structured object the next role can consume directly.

Suggested output shape (negotiate this with your downstream roles):
    For review mode:
        {"kind": "pr", "files": [...], "diff_summary": "..."}
    For triage mode:
        {"kind": "issue", "title": "...", "body": "...", "labels": [...]}

Be specific about: what tool calls you expect the Router to make
(gh_pr_files / gh_pr_diff / gh_issue_read), what fields to extract,
and what format the next role expects.

Remember: prompts that emit JSON benefit from one concrete example in the
prompt itself ("here is a well-formed response: { ... }"). Authoring step
gets to step 6 (★ scaffolding step) — write the Reviewer first, then come back.
-->
