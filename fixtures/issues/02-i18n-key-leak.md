---
title: "Reports page leaks raw i18n keys when locale is `ja` — shows `reports.quarterly_performance` instead of translated text"
labels: ["bug", "i18n", "reports"]
---

## Summary

When the app locale is set to `ja` (Japanese), several headings on the Reports page render as raw i18n keys instead of translated strings.

## Repro

1. Start the app and open `http://localhost:3000/reports`.
2. Switch the locale to `ja` (locale picker is in the top bar).
3. The "Quarterly Performance" header, the table column headers, and the "Monthly Trends" subtitle render as the raw keys (e.g. `reports.quarterly_performance`, `reports.column_orders`).

## Expected

All visible text on the Reports page should use the `t()` translation helper and have entries in both `client/src/locales/en.js` and `client/src/locales/ja.js`.

## Actual

`client/src/views/Reports.vue` uses hardcoded English strings in several places (page header, table headers, chart labels). When the locale falls back to a missing key, Vue I18n displays the key itself.

## Likely fix location

`client/src/views/Reports.vue`. Compare to `client/src/views/Inventory.vue` (which appears to handle i18n correctly) for the pattern: every visible string goes through `{{ $t('namespace.key') }}` and the key exists in both `en.js` and `ja.js`.

## Acceptance criteria

- Every visible string on `/reports` uses `$t()`.
- Both `en.js` and `ja.js` have the new keys under a `reports.*` namespace.
- A simple snapshot test or visual check confirms no raw keys render when locale=ja.
