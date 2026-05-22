---
role: patcher
input: one Planner step (file + intent + sketch) OR critic feedback (revision)
output: a unified diff that applies cleanly to the workspace clone
escalation: critic (advisor) runs after the patcher in step 13
model_tier: Sonnet 4.6
---

<!--
Write your Patcher system prompt below.

The Patcher reads the relevant file(s), produces a unified diff, and emits it
in a parseable format the orchestration layer can pass to git_apply().

Constraints to put in the prompt:
    - Diff must apply to the current state of the file (no stale context).
    - Prefer minimal changes — touch only the lines that need to change.
    - If a fix requires changes in multiple files, emit them as one diff.
    - Do NOT add unrelated cleanup, formatting changes, or reordering.

Suggested output shape:
    {"diff": "<unified diff>", "summary": "one-sentence what-changed"}

When invoked for a revision (critic returned REQUEST_CHANGES), the user
message will include the critic's feedback. Acknowledge it explicitly in
your revised diff's summary.
-->
