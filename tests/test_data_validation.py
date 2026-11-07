from pathlib import Path
from itertools import product
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

from app import (
    FILTER_COLUMNS,
    NAVIGATION_SECTIONS,
    calculate_kpis,
    calculate_missing_summary,
    filter_data,
    summarize_insights,
)


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "Dataset" / "Blinkit_Cleaned_Data.csv"
REQUIRED_COLUMNS = {
    "Item Fat Content",
    "Item Identifier",
    "Item Type",
    "Outlet Establishment Year",
    "Outlet Identifier",
    "Outlet Location Type",
    "Outlet Size",
    "Outlet Type",
    "Item Visibility",
    "Item Weight",
    "Sales",
    "Rating",
}


class DatasetValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = pd.read_csv(DATASET_PATH)

    def test_required_columns_are_present(self) -> None:
        self.assertTrue(REQUIRED_COLUMNS.issubset(self.data.columns))

    def test_required_measure_columns_are_numeric(self) -> None:
        for column in ("Sales", "Rating", "Item Visibility", "Item Weight"):
            with self.subTest(column=column):
                self.assertTrue(pd.api.types.is_numeric_dtype(self.data[column]))

    def test_sales_and_rating_have_no_missing_values(self) -> None:
        self.assertEqual(int(self.data["Sales"].isna().sum()), 0)
        self.assertEqual(int(self.data["Rating"].isna().sum()), 0)

    def test_item_weight_missingness_matches_documented_snapshot(self) -> None:
        self.assertEqual(int(self.data["Item Weight"].isna().sum()), 1463)

    def test_sales_are_positive_and_ratings_are_in_range(self) -> None:
        self.assertTrue((self.data["Sales"] > 0).all())
        self.assertTrue(self.data["Rating"].between(1, 5).all())

    def test_kpis_count_records_not_units(self) -> None:
        metrics = calculate_kpis(self.data)
        self.assertEqual(metrics["record_count"], len(self.data))
        self.assertAlmostEqual(metrics["total_sales"], self.data["Sales"].sum())
        self.assertAlmostEqual(metrics["average_sales"], self.data["Sales"].mean())
        self.assertAlmostEqual(metrics["average_rating"], self.data["Rating"].mean())

    def test_filters_compose_and_empty_selection_means_all(self) -> None:
        filtered = filter_data(
            self.data,
            {"Item Type": ["Dairy"], "Outlet Location Type": ["Tier 1"]},
        )
        self.assertGreater(len(filtered), 0)
        self.assertTrue(filtered["Item Type"].eq("Dairy").all())
        self.assertTrue(filtered["Outlet Location Type"].eq("Tier 1").all())
        self.assertEqual(len(filter_data(self.data, {})), len(self.data))

    def test_all_filter_value_includes_all_records(self) -> None:
        self.assertEqual(len(filter_data(self.data, {"Item Type": ["All"]})), len(self.data))
        self.assertEqual(
            len(filter_data(self.data, {"Item Type": ["All", "Dairy"]})),
            len(self.data),
        )

    def test_filtered_kpis_match_filtered_rows(self) -> None:
        filtered = filter_data(
            self.data,
            {
                "Item Type": ["Dairy"],
                "Outlet Type": ["Supermarket Type1"],
                "Outlet Size": ["Medium"],
                "Outlet Location Type": ["Tier 1"],
            },
        )
        self.assertGreater(len(filtered), 0)
        metrics = calculate_kpis(filtered)
        self.assertEqual(metrics["record_count"], len(filtered))
        self.assertAlmostEqual(metrics["total_sales"], filtered["Sales"].sum())
        self.assertAlmostEqual(metrics["average_sales"], filtered["Sales"].mean())
        self.assertAlmostEqual(metrics["average_rating"], filtered["Rating"].mean())

    def test_every_filter_value_and_combined_filters_match_rows(self) -> None:
        for column in FILTER_COLUMNS:
            for value in self.data[column].dropna().astype(str).unique():
                with self.subTest(column=column, value=value):
                    filtered = filter_data(self.data, {column: [value]})
                    self.assertGreater(len(filtered), 0)
                    self.assertTrue(filtered[column].astype(str).eq(value).all())
                    self.assertEqual(calculate_kpis(filtered)["record_count"], len(filtered))

        combined = filter_data(
            self.data,
            {
                "Item Type": ["Dairy"],
                "Outlet Type": ["Supermarket Type1"],
                "Outlet Size": ["Medium"],
                "Outlet Location Type": ["Tier 1"],
            },
        )
        self.assertTrue(combined["Item Type"].eq("Dairy").all())
        self.assertTrue(combined["Outlet Type"].eq("Supermarket Type1").all())
        self.assertTrue(combined["Outlet Size"].eq("Medium").all())
        self.assertTrue(combined["Outlet Location Type"].eq("Tier 1").all())

    def test_all_single_value_filter_combinations(self) -> None:
        values_by_column = [
            self.data[column].dropna().astype(str).unique()
            for column in FILTER_COLUMNS
        ]
        for values in product(*values_by_column):
            filters = {
                column: [value]
                for column, value in zip(FILTER_COLUMNS, values)
            }
            filtered = filter_data(self.data, filters)
            for column, (value,) in filters.items():
                self.assertTrue(filtered[column].astype(str).eq(value).all())
            self.assertEqual(calculate_kpis(filtered)["record_count"], len(filtered))

    def test_insights_match_filtered_aggregates(self) -> None:
        filtered = filter_data(self.data, {"Outlet Location Type": ["Tier 1"]})
        insights = summarize_insights(filtered)

        self.assertEqual(
            insights["highest_sales_item_type"][0],
            filtered.groupby("Item Type")["Sales"].sum().idxmax(),
        )
        self.assertEqual(
            insights["highest_sales_outlet_type"][0],
            filtered.groupby("Outlet Type")["Sales"].sum().idxmax(),
        )
        self.assertEqual(
            insights["best_rated_item_type"][0],
            filtered.groupby("Item Type")["Rating"].mean().idxmax(),
        )
        self.assertIsNone(summarize_insights(filtered.iloc[0:0])["highest_sales_item_type"])

    def test_missing_data_summary_uses_filtered_records(self) -> None:
        filtered = filter_data(self.data, {"Outlet Location Type": ["Tier 1"]})
        summary = calculate_missing_summary(filtered).set_index("Column")

        self.assertEqual(
            summary.loc["Item Weight", "Missing Records"],
            filtered["Item Weight"].isna().sum(),
        )
        self.assertAlmostEqual(
            summary.loc["Item Weight", "Missing %"],
            filtered["Item Weight"].isna().mean() * 100,
        )
        empty_summary = calculate_missing_summary(filtered.iloc[0:0])
        self.assertTrue((empty_summary["Missing %"] == 0).all())


class DashboardNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = pd.read_csv(DATASET_PATH)

    def test_navigation_sections_render_without_streamlit_errors(self) -> None:
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.radio(key="dashboard_section").value, "Overview")
        for section in NAVIGATION_SECTIONS:
            with self.subTest(section=section):
                app.radio(key="dashboard_section").set_value(section).run()
                self.assertFalse(app.exception)
                self.assertIn(section, [element.value for element in app.subheader])

        selected = {
            "Item Type": ["Dairy"],
            "Outlet Type": ["Supermarket Type1"],
            "Outlet Size": ["Medium"],
            "Outlet Location Type": ["Tier 1"],
        }
        for column, values in selected.items():
            app.multiselect(key=f"filter_{column}").set_value(values)
        app.run()
        self.assertFalse(app.exception)
        expected = calculate_kpis(filter_data(self.data, selected))
        rendered_metrics = {metric.label: metric.value for metric in app.metric}
        self.assertEqual(rendered_metrics["Number of Records"], f"{expected['record_count']:,}")
        self.assertEqual(rendered_metrics["Total Sales"], f"{expected['total_sales']:,.2f}")

    def test_filter_widgets_default_to_all(self) -> None:
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
        for column in FILTER_COLUMNS:
            with self.subTest(column=column):
                self.assertEqual(app.multiselect(key=f"filter_{column}").value, ["All"])


if __name__ == "__main__":
    unittest.main()
