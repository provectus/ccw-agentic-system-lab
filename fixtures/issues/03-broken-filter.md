---
title: "`filter_by_month` ignores quarter codes when month string contains the quarter substring — e.g. `Q1-2025` matches items with order_date `2025-01-Q1`"
labels: ["bug", "backend", "filter"]
---

## Summary

`filter_by_month()` in `server/main.py` has a subtle false-positive: items whose `order_date` happens to contain the quarter string (`Q1-2025`) get matched when filtering by an actual month, because the function uses an `in` substring check.

## Repro

1. Open the Orders page in the running app.
2. Add a filter for month `2025-01`.
3. Inspect the results: any synthetic test rows whose `order_date` contains substrings like `2025-01-15` and `2025-01` match correctly — but the function is fragile to format drift.

The clearer bug surface: pass `month=2025-1` (no leading zero) — `'2025-1' in '2025-01'` is True, so January matches "2025-1" too. The function should compare on canonical month tokens.

## Expected

Filter should canonicalize the month input (or use a regex anchored to the year-month boundary) and reject inputs that don't match `YYYY-MM` or one of the `Q[1-4]-YYYY` codes.

## Actual

`filter_by_month()` does substring matching (`m in item.get('order_date', '')`) which is permissive and accepts malformed input.

## Likely fix location

`server/main.py:filter_by_month()` (around line 14-32). The function and its callers — `/api/spending/monthly`, `/api/reports/monthly-trends`, possibly the orders endpoint.

## Notes for the agent

- The fix should add input validation (raise `HTTPException(400)` on malformed month) AND tighten the matching.
- Add unit tests for: (a) valid month, (b) valid quarter, (c) `2025-1` rejected, (d) `Q5-2025` rejected, (e) `all` returns everything.
