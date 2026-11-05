# Methodology and assumptions

## Provenance and attribution

This portfolio adaptation builds on [Ashuytosh/Blinkit_Data_Analysis](https://github.com/Ashuytosh/Blinkit_Data_Analysis), a project credited to Ashutosh Sahoo. The original MIT license is preserved in `LICENSE`; that notice does not establish a separate license for the dataset. The inherited project files do not identify a definitive original dataset publisher/source, so dataset provenance and redistribution terms beyond the supplied repository remain unverified. Improvements to this adaptation are by Praful Kinkar.

## Preparation and quality checks

- Use `Dataset/BlinkIT Grocery Data.csv` as the raw analysis input; do not modify it in place.
- Standardize observed `LF`, `low fat`, and `reg` values to `Low Fat` and `Regular` in the analysis copy.
- Rename `Total Sales` to `Sales` for concise Python/dashboard expressions. SQL examples use the imported source-style `Total_Sales` field.
- Convert establishment year, visibility, item weight, sales, and rating to numeric types and validate required fields.
- Preserve all records and the 1,463 missing `Item Weight` values; no imputation is justified by available documentation.
- Check exact full-row duplicates. Zero were found in the supplied raw and cleaned files. Repeated identifiers are not by themselves duplicates.
- Flag possible sales outliers with the IQR rule for review; do not remove them automatically.
- The supplied cleaned file has `Outlet Age` computed against 2025. It is not a current age and is not recreated in the notebook.

## KPI definitions

Use the same unfiltered row population in SQL, Python, Power BI, and Streamlit by default. There is no transaction-date field; outlet establishment year must not be used as a hidden date filter.

- **Total Sales:** sum of non-missing recorded sales values.
- **Average Sales:** arithmetic mean of recorded sales per row.
- **Number of Records:** number of non-missing sales values. This is not a sold-quantity measure.
- **Average Rating:** arithmetic mean of non-missing row ratings.

Do not add a currency symbol: currency is undocumented. For the dashboard, filters change the population for every KPI and group contribution. A category contribution is its total sales divided by sales for the currently selected population, multiplied by 100.

## Analytical choices and limitations

- Compare sales totals and averages per record separately. Totals can vary with group record counts.
- Include group counts where averages need context.
- Treat rankings as descriptive of the supplied snapshot, not forecasts or causal conclusions.
- Use item-visibility scatterplots and correlation as descriptive association only; correlation does not establish causation.
- Outlet establishment year identifies an outlet cohort, not when sales occurred. This data cannot establish a year-over-year sales trend.
- There is no transaction timestamp, quantity, order identifier, documented currency, or documented sales period. These constraints limit business interpretation.

## Reproducibility

Windows setup: create and activate a virtual environment, install `requirements.txt`, run `python -m pytest`, then start with `streamlit run app.py`. SQL is SQL Server T-SQL and assumes a table named `dbo.blinkit_data` in `blinkit_db`; adjust table/column mappings to the actual SQL Server import. Power BI editing depends on access to the semantic model referenced by the supplied PBIX; see `power_bi_setup.md`.
