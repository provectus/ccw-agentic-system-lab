---
role: planner
input: issue body + (optionally) tool calls to explore the target repo
output: ordered list of file-scoped changes the Patcher should apply
escalation: none — planner doesn't make changes, it only plans
model_tier: Sonnet 4.6
---

<!--
Write your Planner system prompt below.

The Planner reads the issue and proposes a fix as a sequence of small,
file-scoped changes. Each change is self-contained enough that the Patcher
can apply it without re-reading the full repo.

Encourage the Planner to:
    1. Use read_file / grep / glob to locate the buggy code FIRST.
    2. Propose the SMALLEST diff that fixes the reported behavior.
    3. Name each change with a one-line intent and a code sketch.

Suggested output shape:
    {"plan": [
        {"file": "client/src/views/Reports.vue", "intent": "guard against undefined month", "sketch": "..."},
        {"file": "server/main.py", "intent": "add unit test for filter_by_month", "sketch": "..."},
    ]}
-->
