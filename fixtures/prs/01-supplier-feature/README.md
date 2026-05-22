# Planted PR: Supplier Management Feature

**This file is for facilitators only. Do not show participants.**

`patch.diff` introduces a partial "supplier management" feature on top of `ccw-inventory-management` `main`. It adds:

- A new `Supplier` Pydantic model and a `/api/suppliers` GET + POST endpoint in `server/main.py`.
- A new `Suppliers.vue` view in `client/src/views/`.
- A nav link to the new page in the sidebar.

The PR contains **five planted issues** that a competent Reviewer should flag.
A successful workshop run catches at least 3 of these. Catching 4 or 5 indicates
the participant's Reviewer prompt is well-calibrated.

## Planted issues

| # | Type | Location | Description |
|---|---|---|---|
| 1 | **Correctness (missing null check)** | `server/main.py` — new `create_supplier` endpoint | `body.contact_email` is accessed and lowercased without checking that `body.contact_email` is not None. The Pydantic model declares `contact_email: Optional[str]`, so None is a legal input. |
| 2 | **Security (hardcoded credential placeholder)** | `server/main.py` — new `_send_supplier_notification` helper | The function contains `SMTP_PASSWORD = "changeme_in_prod"` inline. Even though it is labeled as a placeholder, it is exactly the kind of string that gets shipped accidentally. |
| 3 | **Performance (N+1 query pattern)** | `server/main.py` — new `get_suppliers` endpoint | For each supplier in the list, the code calls `_count_open_orders_for(supplier.id)` which itself iterates the entire orders list. Result is O(suppliers × orders). The whole thing should be done in one pass. |
| 4 | **Tests (missing coverage for the new endpoint)** | No new tests in `tests/` for the supplier endpoints. The repo has a `tests/` directory and existing tests for inventory and orders — the convention is one test file per endpoint group. |
| 5 | **Style (CSS class name typo)** | `client/src/views/Suppliers.vue` — class name `supplier-card-conteiner` (sic) referenced in the template and styled in `<style scoped>`. Hard to catch without the diff, but a careful Reviewer reading both the template and the style block will notice the spelling. |

## Why these five

They cover the spectrum the workshop's Reviewer prompt should be calibrated for: **correctness**, **security**, **performance**, **test coverage**, and **style**. Workshop step 11 (the Critic) is most likely to catch issue #4 (missing tests) which Reviewers tend to underweight.

## Calibrating difficulty

If during dry-runs the Reviewer catches all 5 trivially, replace one with a harder issue (e.g., a subtle race condition in a hypothetical background task). If it catches fewer than 3, the Reviewer prompt likely needs better signal calibration — the prompt should explicitly enumerate "check for: null safety, secrets, query patterns, test coverage, naming."

## Regenerating the patch

If `ccw-inventory-management` `main` shifts and the patch no longer applies cleanly, regenerate:

```bash
cd ccw-inventory-management
git checkout -b regenerate/supplier-feature main
# … apply the changes by hand following the descriptions above
git diff main > /path/to/ccw-agentic-system-lab/fixtures/prs/01-supplier-feature/patch.diff
git checkout main && git branch -D regenerate/supplier-feature
```
