# Initial project audit and prioritized fixes

This audit records issues identified before improvements in this adaptation. It is not a claim about the upstream author's intent.

## Priority 1 — correctness and reproducibility

1. **Mismatched SQL KPI population:** Average Sales and record count filtered to establishment year 2022, while Total Sales and Average Rating did not. Establishment year is not a transaction-date filter.
2. **Incorrect top-five query order:** The item type query used ascending sales order, so it returned the lowest, not highest, sales categories. The stored result CSV showed the high-sales categories.
3. **Streamlit tests expected absent functions:** `tests/test_data_validation.py` imported `calculate_kpis` and `filter_data`, neither of which existed in the original app.
4. **Broken devcontainer JSON:** The checked-in configuration contained unrelated fragments and did not parse as JSON.
5. **Notebook data path:** The original notebook read the raw CSV from the working directory although it is stored under `Dataset/`.

## Priority 2 — interpretation and consistency

6. The app and screenshot labeled a sales-record count as “Items Sold” / “No of Items”, despite the dataset containing no quantity field.
7. Several files displayed `$` although the supplied source documentation does not establish a currency.
8. App insight text was hard-coded and could become inconsistent with filtered or refreshed data.
9. The original dashboard mixed on-the-fly aggregations and precomputed result CSVs, which could become inconsistent.
10. The item-type sales query/result ordering, KPI scope, and thousand-versus-full-sales presentation needed clarification.

## Priority 3 — documentation and maintenance

11. Requirements used UTF-16 encoding; commonplace packaging tools expect UTF-8/ASCII-compatible text.
12. Methodology text incorrectly described the existing MIT LICENSE as truncated, and made an unverified claim about local PBIX model contents.
13. Notebook heatmap section began with explanatory text in a code cell, and saved outputs were stale/not executed in the current kernel.
14. Attribution differed between project files. The MIT notice identifies Ashutosh Sahoo; this adaptation should distinguish original material from new changes.

## Verified baseline facts

The supplied cleaned CSV has 8,523 rows and 13 columns; it contains 1,463 missing `Item Weight` values and no exact full-row duplicates. Its sales sum is 1,201,681.4808, mean sales per record is 140.9928, and mean rating is 3.9659. Currency and measurement period are not specified. Raw and cleaned CSVs are alternate representations of the same records, not separate populations.

The Power BI package and screenshot were inspected, but Power BI Desktop/service access was unavailable. The screenshot is static and not proof of report interactivity. The package has remote dataset/report connection metadata and a `DataModel` entry; whether its model is usable/editable cannot be established from this workspace inspection.
