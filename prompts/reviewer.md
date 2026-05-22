---
role: reviewer
input: one work unit (single file + its hunks + surrounding context)
output: structured findings — line-anchored comments, severity, rationale
escalation: critic if the work unit looks complex or out-of-scope
model_tier: Opus 4.7 (this is where reasoning quality matters most)
---

<!--
Write your Reviewer system prompt below.

The Reviewer is invoked ONCE per work unit (typically once per file). Each
Reviewer is a fresh context — it sees only its work unit, plus tools to
read related files if it needs more context.

What to look for (calibrate per your design.md decisions):
    - Correctness bugs: missing null checks, off-by-one, race conditions
    - Security: hardcoded credentials, unvalidated input, injection vectors
    - Performance: N+1 queries, sync calls in async contexts, unbounded loops
    - Tests: missing coverage for the new code paths
    - Style: only flag if a project convention is clearly violated

Suggested output shape:
    {"findings": [
        {"line": 42, "severity": "high|medium|low", "category": "correctness|security|perf|tests|style", "body": "..."},
        ...
    ]}

This is the one prompt you author in step 6 (★) before writing the others.
Aim for ~30-50 lines. Include one concrete example of a well-formed finding.
-->
