---
role: coordinator
input: router output (PR metadata) — list of changed files with hunks
output: parallel-dispatchable work units, one per file (or per hunk for big diffs)
escalation: none — coordinator only plans, never decides
model_tier: Sonnet 4.6 (good reasoning, lower cost than Opus)
---

<!--
Write your Coordinator system prompt below.

The Coordinator receives the Router's PR summary and decides how to split
work across parallel Reviewers. Each work unit should be self-contained
(one file's worth of context plus its hunks).

Suggested output shape:
    {"work_units": [
        {"file": "src/api/suppliers.py", "hunks": ["@@ -10,7 +10,14 @@ ..."], "context": "this file is..." },
        ...
    ]}

Make explicit: how many parallel workers you want (cap at, say, 8), how to
split files >300 lines (split by hunk?), and what to do with binary/unchanged
files (skip).
-->
