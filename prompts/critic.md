---
role: critic
input: a patch (review-mode synthesizer output OR triage-mode patcher diff)
output: APPROVE or REQUEST_CHANGES with specific actionable feedback
escalation: none — the critic IS the escalation
model_tier: Opus 4.7 (we want the smartest model checking the work)
---

<!--
Write your Critic system prompt below.

The Critic is the advisor pattern from "Building Effective Agents". It runs
AFTER the worker has produced its output and BEFORE that output reaches the
side-effecting tool (gh_pr_comment / gh_pr_create).

Calibrate the Critic for SIGNAL, not nitpicks. Ask it to consider:
    - Does the patch actually fix the reported issue? (Triage)
    - Does the review surface real issues, not style nits? (Review)
    - Are there confidence flags worth lowering?
    - Is there a missing test that should accompany this change? (Triage)

Suggested output shape:
    {
      "event": "APPROVE" | "REQUEST_CHANGES",
      "feedback": "one-paragraph rationale; if REQUEST_CHANGES, be specific about what to change",
      "confidence": 0.0-1.0
    }

The orchestration code caps revision loops at 2 attempts. Make the critic
willing to APPROVE on the second pass even if not perfect.
-->
