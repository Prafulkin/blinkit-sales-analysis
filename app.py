"""Interactive Blinkit sales analysis dashboard.

Portfolio adaptation by Praful Kinkar of a project originally credited to
Ashutosh Sahoo; see LICENSE and README.md for attribution and scope.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT / "Dataset" / "Blinkit_Cleaned_Data.csv"
REQUIRED_COLUMNS = {
    "Item Fat Content", "Item Identifier", "Item Type", "Outlet Establishment Year",
    "Outlet Identifier", "Outlet Location Type", "Outlet Size", "Outlet Type",
    "Item Visibility", "Item Weight", "Sales", "Rating",
}
FILTER_COLUMNS = ("Item Type", "Outlet Type", "Outlet Size", "Outlet Location Type")
ACCENT = "#168A4A"
HIGHLIGHT = "#F7C600"
DARK_BACKGROUND = "#0E1117"
LIGHT_TEXT = "#FAFAFA"
MUTED_GRID = "#343842"
ALL_OPTION = "All"


@st.cache_data(show_spinner="Loading dataset…")
def load_dataset(path: Path = DATASET_PATH) -> pd.DataFrame:
    """Load and validate the supplied cleaned dataset."""
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")
    data = pd.read_csv(path)
    missing = sorted(REQUIRED_COLUMNS.difference(data.columns))
    if missing:
        raise ValueError("Dataset is missing required columns: " + ", ".join(missing))
    data = data.copy()
    for column in ("Sales", "Rating", "Item Visibility", "Item Weight", "Outlet Establishment Year"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    if data["Sales"].isna().any() or not data["Sales"].gt(0).all():
        raise ValueError("Sales must contain numeric, positive values without missing entries.")
    if data["Rating"].isna().any() or not data["Rating"].between(1, 5).all():
        raise ValueError("Rating must contain numeric values on the observed 1–5 scale.")
    return data


def filter_data(data: pd.DataFrame, filters: Mapping[str, Sequence[str]]) -> pd.DataFrame:
    """Apply categorical filters; empty selections or an All choice include all values."""
    filtered = data
    for column, selected in filters.items():
        if selected and ALL_OPTION not in selected:
            filtered = filtered.loc[filtered[column].isin(selected)]
    return filtered.copy()


def calculate_kpis(data: pd.DataFrame) -> dict[str, float | int]:
    """Calculate sales, sales per record, record count, and average rating."""
    if data.empty:
        return {"total_sales": 0.0, "average_sales": 0.0, "record_count": 0, "average_rating": 0.0}
    return {
        "total_sales": float(data["Sales"].sum()),
        "average_sales": float(data["Sales"].mean()),
        "record_count": int(data["Sales"].count()),
        "average_rating": float(data["Rating"].mean()),
    }


def _bar_chart(data: pd.DataFrame, category: str, title: str, *, horizontal: bool = True) -> plt.Figure:
    summary = data.groupby(category, dropna=False)["Sales"].sum().sort_values(ascending=not horizontal)
    height = max(3.6, 0.38 * len(summary)) if horizontal else 4.2
    fig, ax = plt.subplots(figsize=(8.4, height), facecolor=DARK_BACKGROUND, layout="constrained")
    ax.set_facecolor(DARK_BACKGROUND)
    ax.tick_params(colors=LIGHT_TEXT, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(MUTED_GRID)

    if horizontal:
        bars = ax.barh(summary.index.astype(str), summary.values, color=HIGHLIGHT, edgecolor="none", height=0.68)
        ax.set_xlabel("Total Sales (source values)", color=LIGHT_TEXT, labelpad=10)
        ax.set_ylabel(category, color=LIGHT_TEXT, labelpad=10)
        ax.margins(x=0.18)
        for bar, value in zip(bars, summary.values):
            ax.annotate(
                f"{value:,.2f}",
                (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                xytext=(6, 0), textcoords="offset points", va="center", ha="left",
                color=LIGHT_TEXT, fontsize=8, clip_on=False,
            )
    else:
        bars = ax.bar(summary.index.astype(str), summary.values, color=HIGHLIGHT, edgecolor="none", width=0.66)
        ax.set_xlabel(category, color=LIGHT_TEXT, labelpad=10)
        ax.set_ylabel("Total Sales (source values)", color=LIGHT_TEXT, labelpad=10)
        ax.tick_params(axis="x", labelrotation=0, pad=6)
        ax.margins(y=0.2)
        for bar, value in zip(bars, summary.values):
            ax.annotate(
                f"{value:,.2f}",
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 5), textcoords="offset points", va="bottom", ha="center",
                color=LIGHT_TEXT, fontsize=8, clip_on=False,
            )
    ax.set_title(title, color=LIGHT_TEXT, fontsize=13, fontweight="bold", pad=14, loc="left")
    ax.grid(axis="x" if horizontal else "y", color=MUTED_GRID, linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    return fig


def _show_chart(data: pd.DataFrame, category: str, title: str, *, horizontal: bool = True) -> None:
    if data.empty:
        st.info(f"No records available for {title.lower()} under the current filters.")
        return
    fig = _bar_chart(data, category, title, horizontal=horizontal)
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def main() -> None:
    st.set_page_config(page_title="Blinkit Sales Analysis", page_icon="📊", layout="wide")
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] > div:first-child { padding-top: 1.4rem; }
        [data-testid="stSidebar"] { min-width: 20rem; }
        [data-testid="stSidebar"] .stMultiSelect { margin-bottom: 1.15rem; }
        [data-testid="stSidebar"] [data-baseweb="tag"] { max-width: 100%; }
        [data-testid="stSidebar"] [data-baseweb="tag"] span {
            white-space: normal; overflow-wrap: anywhere; line-height: 1.25;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Blinkit Sales Analysis")
    st.caption("Interactive exploration of the supplied item/outlet snapshot. Sales currency and period are not specified by the source.")

    try:
        data = load_dataset()
    except (OSError, pd.errors.ParserError, ValueError) as error:
        st.error(f"Unable to load a valid dataset: {error}")
        st.info("Confirm Dataset/Blinkit_Cleaned_Data.csv exists and contains the documented columns.")
        st.stop()

    st.sidebar.header("Dataset filters")
    selections: dict[str, list[str]] = {}
    for column in FILTER_COLUMNS:
        options = sorted(data[column].dropna().astype(str).unique().tolist())
        selections[column] = st.sidebar.multiselect(
            column,
            [ALL_OPTION, *options],
            default=[ALL_OPTION],
            key=f"filter_{column}",
            help="Choose All to include every value, or clear All and select specific values.",
            placeholder="All values",
        )
    filtered = filter_data(data, selections)

    st.sidebar.caption(f"Showing {len(filtered):,} of {len(data):,} records.")
    if filtered.empty:
        st.warning("No records match the selected filters. Select at least one value for each filter.")

    metrics = calculate_kpis(filtered)
    cards = st.columns(4)
    cards[0].metric("Total Sales", f"{metrics['total_sales']:,.2f}")
    cards[1].metric("Average Sales / Record", f"{metrics['average_sales']:,.2f}")
    cards[2].metric("Number of Records", f"{metrics['record_count']:,}")
    cards[3].metric("Average Rating", f"{metrics['average_rating']:.2f} / 5")
    st.caption("Record count is not units sold. Sales are displayed without a currency symbol because the source does not identify a currency.")

    st.subheader("Sales overview")
    left, right = st.columns(2)
    with left:
        _show_chart(filtered, "Item Type", "Sales by Item Type")
        _show_chart(filtered, "Outlet Size", "Sales by Outlet Size")
    with right:
        _show_chart(filtered, "Outlet Type", "Sales by Outlet Type")
        _show_chart(filtered, "Outlet Location Type", "Sales by Location Tier")

    with st.expander("Additional analysis", expanded=False):
        fat, year = st.columns(2)
        with fat:
            _show_chart(filtered, "Item Fat Content", "Sales by Fat Content")
        with year:
            _show_chart(filtered, "Outlet Establishment Year", "Sales by Outlet Establishment Year", horizontal=False)
        st.markdown("#### Average Rating by Item Type")
        rating_summary = filtered.groupby("Item Type", as_index=False).agg(
            Average_Rating=("Rating", "mean"), Records=("Rating", "count"), Total_Sales=("Sales", "sum")
        ).sort_values("Average_Rating")
        st.dataframe(rating_summary, width="stretch", hide_index=True)
        st.markdown("#### Item Visibility and Sales")
        st.caption("This is a descriptive association only; correlation does not establish causation.")
        fig, ax = plt.subplots(figsize=(8.4, 4.2), facecolor=DARK_BACKGROUND, layout="constrained")
        ax.set_facecolor(DARK_BACKGROUND)
        sns.scatterplot(data=filtered, x="Item Visibility", y="Sales", alpha=0.45, ax=ax, color=HIGHLIGHT, edgecolor=None)
        ax.set_title("Item Visibility versus Sales", color=LIGHT_TEXT, fontsize=13, fontweight="bold", pad=14, loc="left")
        ax.set_xlabel("Item Visibility", color=LIGHT_TEXT, labelpad=10)
        ax.set_ylabel("Sales (source values)", color=LIGHT_TEXT, labelpad=10)
        ax.tick_params(colors=LIGHT_TEXT, labelsize=9)
        ax.grid(color=MUTED_GRID, linewidth=0.8, alpha=0.8)
        for spine in ax.spines.values():
            spine.set_color(MUTED_GRID)
        st.pyplot(fig, width="stretch")
        plt.close(fig)

    st.subheader("Key Business Insights")
    if filtered.empty:
        st.write("No insight can be calculated for an empty filter selection.")
    else:
        item_totals = filtered.groupby("Item Type")["Sales"].sum().sort_values(ascending=False)
        location_totals = filtered.groupby("Outlet Location Type")["Sales"].sum().sort_values(ascending=False)
        size_averages = filtered.groupby("Outlet Size")["Sales"].mean().sort_values(ascending=False)
        st.markdown(
            f"- Highest sales item type: **{item_totals.index[0]}** ({item_totals.iloc[0]:,.2f} source units).\n"
            f"- Highest sales location tier: **{location_totals.index[0]}** ({location_totals.iloc[0]:,.2f} source units).\n"
            f"- Highest average sales per record by outlet size: **{size_averages.index[0]}** ({size_averages.iloc[0]:,.2f})."
        )
        st.caption("These summaries update with the current filters and describe this dataset snapshot only.")

    st.subheader("Filtered data preview")
    st.dataframe(filtered.head(100), width="stretch", hide_index=True)
    st.download_button(
        "Download filtered data as CSV",
        data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name="blinkit_filtered_data.csv",
        mime="text/csv",
        disabled=filtered.empty,
    )

    st.divider()
    st.caption("Portfolio adaptation by Praful Kinkar. Original project credited to Ashutosh Sahoo; see LICENSE and README for attribution.")


if __name__ == "__main__":
    main()
