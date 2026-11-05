from pathlib import Path
import unittest

import pandas as pd

from app import calculate_kpis, filter_data


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


if __name__ == "__main__":
    unittest.main()
