---
title: "Reorder threshold compares with `>=` but should use `>` — items at reorder_point never flagged"
labels: ["bug", "inventory", "good-first-issue"]
---

## Summary

Items whose `quantity_on_hand` equals their `reorder_point` are not flagged for restock on the Inventory page. The dashboard counts them as "in stock" when they should appear in the "needs reorder" bucket.

## Repro

1. Start the app per `README.md`.
2. Open `http://localhost:3000/inventory`.
3. Note any SKU where `quantity_on_hand == reorder_point` (e.g. SKU `WID-001` shows 50 / reorder 50).
4. Open the Dashboard. It is excluded from the "Needs Reorder" panel.

## Expected

Items at OR BELOW the reorder point should be flagged. The business rule is "if we are at the threshold, place an order now."

## Actual

Items at the threshold are treated as healthy stock and only items strictly below trigger.

## Likely fix location

Search the backend for the comparison: `server/main.py` around the dashboard summary endpoint, or wherever `reorder_point` is referenced. The frontend may also have a duplicate check in `client/src/views/Dashboard.vue`. Pick the **single source of truth** and update it; the other call site should consume that value.

## Notes for the agent

- Add a test that exercises the boundary case (`quantity == reorder_point`) before changing the comparison.
- The fix is intentionally small — one operator change, one new test.
