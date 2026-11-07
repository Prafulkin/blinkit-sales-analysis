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
HIGHLIGHT = "#78D9A2"
DARK_BACKGROUND = "#10161F"
LIGHT_TEXT = "#E8EDF4"
MUTED_GRID = "#2D3745"
ALL_OPTION = "All"
NAVIGATION_SECTIONS = (
    "Overview",
    "Sales Analysis",
    "Product Analysis",
    "Outlet Analysis",
    "Data Quality",
)


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


def summarize_insights(data: pd.DataFrame) -> dict[str, tuple[str, float] | None]:
    """Return the leading sales and rating groups in the current filter context."""
    if data.empty:
        return {
            "highest_sales_item_type": None,
            "highest_sales_outlet_type": None,
            "best_rated_item_type": None,
        }

    item_sales = data.groupby("Item Type")["Sales"].sum().sort_values(ascending=False)
    outlet_sales = data.groupby("Outlet Type")["Sales"].sum().sort_values(ascending=False)
    item_ratings = data.groupby("Item Type")["Rating"].mean().sort_values(ascending=False)
    return {
        "highest_sales_item_type": (str(item_sales.index[0]), float(item_sales.iloc[0])),
        "highest_sales_outlet_type": (str(outlet_sales.index[0]), float(outlet_sales.iloc[0])),
        "best_rated_item_type": (str(item_ratings.index[0]), float(item_ratings.iloc[0])),
    }


def calculate_missing_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Summarize missing values for the currently filtered rows."""
    missing = data.isna().sum()
    percentages = missing.div(len(data)).mul(100) if len(data) else missing.astype(float)
    return pd.DataFrame(
        {
            "Column": data.columns,
            "Missing Records": missing.to_numpy(dtype=int),
            "Missing %": percentages.to_numpy(dtype=float),
        }
    ).sort_values(["Missing Records", "Column"], ascending=[False, True], ignore_index=True)


def _bar_chart(data: pd.DataFrame, category: str, title: str, *, horizontal: bool = True) -> plt.Figure:
    summary = data.groupby(category, dropna=False)["Sales"].sum().sort_values(ascending=not horizontal)
    height = max(3.0, 0.34 * len(summary)) if horizontal else 3.6
    fig, ax = plt.subplots(figsize=(7.0, height), facecolor=DARK_BACKGROUND, layout="constrained")
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
    ax.set_title(title, color=LIGHT_TEXT, fontsize=12, fontweight="bold", pad=12, loc="left")
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


def _show_rating_chart(data: pd.DataFrame) -> None:
    if data.empty:
        st.info("No records available for average rating by item type under the current filters.")
        return
    summary = data.groupby("Item Type")["Rating"].mean().sort_values()
    fig, ax = plt.subplots(
        figsize=(7.0, max(3.0, 0.34 * len(summary))),
        facecolor=DARK_BACKGROUND,
        layout="constrained",
    )
    ax.set_facecolor(DARK_BACKGROUND)
    bars = ax.barh(summary.index.astype(str), summary.values, color=HIGHLIGHT, edgecolor="none", height=0.68)
    ax.set_xlim(0, 5)
    ax.set_xlabel("Average Rating (1–5)", color=LIGHT_TEXT, labelpad=9)
    ax.tick_params(colors=LIGHT_TEXT, labelsize=9)
    ax.grid(axis="x", color=MUTED_GRID, linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(MUTED_GRID)
    for bar, value in zip(bars, summary.values):
        ax.annotate(
            f"{value:.2f}",
            (bar.get_width(), bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            color=LIGHT_TEXT,
            fontsize=8,
        )
    ax.set_title("Average Rating by Item Type", color=LIGHT_TEXT, fontsize=12, fontweight="bold", loc="left")
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def _show_visibility_chart(data: pd.DataFrame) -> None:
    if data.empty:
        st.info("No records available for item visibility versus sales under the current filters.")
        return
    fig, ax = plt.subplots(figsize=(7.0, 3.6), facecolor=DARK_BACKGROUND, layout="constrained")
    ax.set_facecolor(DARK_BACKGROUND)
    sns.scatterplot(
        data=data,
        x="Item Visibility",
        y="Sales",
        alpha=0.42,
        ax=ax,
        color=HIGHLIGHT,
        edgecolor=None,
        s=22,
    )
    ax.set_title("Item Visibility versus Sales", color=LIGHT_TEXT, fontsize=12, fontweight="bold", loc="left")
    ax.set_xlabel("Item Visibility", color=LIGHT_TEXT, labelpad=9)
    ax.set_ylabel("Sales (source values)", color=LIGHT_TEXT, labelpad=9)
    ax.tick_params(colors=LIGHT_TEXT, labelsize=9)
    ax.grid(color=MUTED_GRID, linewidth=0.8, alpha=0.8)
    for spine in ax.spines.values():
        spine.set_color(MUTED_GRID)
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def _render_chart_panel(data: pd.DataFrame, category: str, title: str, *, horizontal: bool = True) -> None:
    with st.container(border=True):
        _show_chart(data, category, title, horizontal=horizontal)


def _render_rating_panel(data: pd.DataFrame) -> None:
    with st.container(border=True):
        _show_rating_chart(data)


def _render_visibility_panel(data: pd.DataFrame) -> None:
    with st.container(border=True):
        _show_visibility_chart(data)


def _render_chart_grid(data: pd.DataFrame, panels: Sequence[tuple[str, str, bool]]) -> None:
    left, right = st.columns(2)
    for index, (category, title, horizontal) in enumerate(panels):
        with (left if index % 2 == 0 else right):
            _render_chart_panel(data, category, title, horizontal=horizontal)


def _render_insights(data: pd.DataFrame) -> None:
    insights = summarize_insights(data)
    with st.container(border=True):
        st.markdown("#### Filtered insights")
        st.metric("Total records after filters", f"{len(data):,}")
        if data.empty:
            st.info("No insights available for an empty filter selection.")
        else:
            for label, key in (
                ("Highest sales category", "highest_sales_item_type"),
                ("Highest sales outlet type", "highest_sales_outlet_type"),
                ("Best-rated item category", "best_rated_item_type"),
            ):
                result = insights[key]
                if result is not None:
                    st.markdown(f"**{label}**  \n{result[0]}")
                    st.caption(f"{result[1]:,.2f}" if key != "best_rated_item_type" else f"{result[1]:.2f} / 5")

    missing_summary = calculate_missing_summary(data)
    with st.container(border=True):
        st.markdown("#### Missing data")
        nonzero_missing = missing_summary.loc[missing_summary["Missing Records"] > 0]
        if nonzero_missing.empty:
            st.success("No missing values in the filtered records.")
        else:
            for _, row in nonzero_missing.iterrows():
                st.markdown(f"**{row['Column']}**")
                st.caption(f"{row['Missing Records']:,} records · {row['Missing %']:.1f}%")


def main() -> None:
    st.set_page_config(page_title="Blinkit Sales Analysis", page_icon="📊", layout="wide")
    st.markdown(
        """
        <style>
        :root { color-scheme: dark; }
        [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background: #0B1017;
            color: #E8EDF4;
        }
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] li,
        [data-testid="stSidebar"] { color: #E8EDF4; }
        [data-testid="stSidebar"] {
            background: #101721;
            border-right: 1px solid #263141;
        }
        [data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }
        [data-testid="stSidebar"] .stMultiSelect { margin-bottom: 0.8rem; }
        [data-testid="stSidebar"] [data-baseweb="tag"] { max-width: 100%; }
        [data-testid="stSidebar"] [data-baseweb="tag"] span {
            white-space: normal; overflow-wrap: anywhere; line-height: 1.2;
        }
        section.main > div { max-width: 1680px; padding: 1.8rem 2.2rem 3rem; }
        h1, h2, h3 { letter-spacing: -0.025em; }
        h1 { font-size: 2rem !important; }
        [data-testid="stMetric"] {
            background: #141D28;
            border: 1px solid #293648;
            border-radius: 12px;
            padding: 0.85rem 1rem;
            min-height: 6rem;
        }
        [data-testid="stMetricLabel"] p { color: #A7B3C3; font-size: 0.82rem; }
        [data-testid="stMetricValue"] { color: #F2F5F9; font-size: 1.55rem; }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: #111923;
            border-color: #293648;
            border-radius: 14px;
        }
        [data-baseweb="select"] > div {
            background: #141D28;
            border-color: #344255;
        }
        [data-baseweb="tag"] { background: #244A38; }
        input[type="radio"] { accent-color: #78D9A2; }
        label[data-baseweb="radio"]:has(input:checked) > div:first-child {
            background-color: #78D9A2 !important;
        }
        [data-testid="stPlotlyChart"], [data-testid="stImage"] { border-radius: 10px; }
        @media (max-width: 1100px) {
            section.main > div { padding: 1.3rem 1rem 2rem; }
            [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: 0.7rem; }
            [data-testid="stColumn"] { min-width: 200px !important; flex: 1 1 200px; }
        }
        @media (max-width: 760px) {
            section.main > div { padding: 1rem 0.8rem 2rem; }
            [data-testid="stColumn"] { min-width: 100% !important; flex-basis: 100%; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    try:
        data = load_dataset()
    except (OSError, pd.errors.ParserError, ValueError) as error:
        st.error(f"Unable to load a valid dataset: {error}")
        st.info("Confirm Dataset/Blinkit_Cleaned_Data.csv exists and contains the documented columns.")
        st.stop()

    st.sidebar.markdown("### Blinkit")
    st.sidebar.caption("SALES INTELLIGENCE")
    st.sidebar.markdown("#### Navigation")
    section = st.sidebar.radio(
        "Dashboard section",
        NAVIGATION_SECTIONS,
        key="dashboard_section",
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    st.sidebar.markdown("#### Dataset filters")
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

    st.sidebar.caption(f"{len(filtered):,} of {len(data):,} records")
    if filtered.empty:
        st.warning("No records match the selected filters. Select at least one value for each filter.")

    st.title("Blinkit Sales Analysis")
    st.caption("A focused view of sales, product performance, and outlet patterns in the supplied dataset snapshot.")
    st.markdown(f"**{len(data):,} records** in dataset · Sales currency and reporting period are not specified.")
    st.subheader(section)

    metrics = calculate_kpis(filtered)
    cards = st.columns(4)
    cards[0].metric("Total Sales", f"{metrics['total_sales']:,.2f}")
    cards[1].metric("Average Sales / Record", f"{metrics['average_sales']:,.2f}")
    cards[2].metric("Number of Records", f"{metrics['record_count']:,}")
    cards[3].metric("Average Rating", f"{metrics['average_rating']:.2f} / 5")
    st.caption("Record count is not units sold. Sales are displayed without a currency symbol because the source does not identify a currency.")

    if section == "Overview":
        charts_column, insights_column = st.columns([2.2, 1])
        with charts_column:
            _render_chart_grid(
                filtered,
                (
                    ("Item Type", "Sales by Item Type", True),
                    ("Outlet Type", "Sales by Outlet Type", True),
                    ("Outlet Size", "Sales by Outlet Size", True),
                    ("Outlet Location Type", "Sales by Location Tier", True),
                    ("Item Fat Content", "Sales by Fat Content", True),
                    ("Outlet Establishment Year", "Sales by Establishment Year", False),
                ),
            )
            _render_rating_panel(filtered)
            _render_visibility_panel(filtered)
        with insights_column:
            _render_insights(filtered)
    elif section == "Sales Analysis":
        _render_chart_grid(
            filtered,
            (
                ("Item Type", "Sales by Item Type", True),
                ("Outlet Type", "Sales by Outlet Type", True),
                ("Item Fat Content", "Sales by Fat Content", True),
            ),
        )
        with st.container(border=True):
            st.caption("Item visibility and sales are shown as a descriptive association; correlation does not establish causation.")
            _show_visibility_chart(filtered)
    elif section == "Product Analysis":
        _render_chart_grid(
            filtered,
            (
                ("Item Type", "Sales by Item Type", True),
                ("Item Fat Content", "Sales by Fat Content", True),
            ),
        )
        _render_rating_panel(filtered)
        with st.container(border=True):
            st.caption("Item visibility and sales are shown as a descriptive association; correlation does not establish causation.")
            _show_visibility_chart(filtered)
    elif section == "Outlet Analysis":
        _render_chart_grid(
            filtered,
            (
                ("Outlet Type", "Sales by Outlet Type", True),
                ("Outlet Size", "Sales by Outlet Size", True),
                ("Outlet Location Type", "Sales by Location Tier", True),
                ("Outlet Establishment Year", "Sales by Establishment Year", False),
            ),
        )
    else:
        missing_summary = calculate_missing_summary(filtered)
        with st.container(border=True):
            st.markdown("#### Missing data by field")
            st.dataframe(
                missing_summary.style.format({"Missing %": "{:.1f}%"}),
                width="stretch",
                hide_index=True,
            )
            st.caption("Missingness is calculated after applying the current filters. No values are imputed.")
        with st.container(border=True):
            st.markdown("#### Filtered data preview")
            st.dataframe(filtered.head(100), width="stretch", hide_index=True)
            st.download_button(
                "Download filtered data as CSV",
                data=filtered.to_csv(index=False).encode("utf-8-sig"),
                file_name="blinkit_filtered_data.csv",
                mime="text/csv",
                disabled=filtered.empty,
            )

    st.divider()
    st.caption("Portfolio adaptation by Praful Kinkar · Original project credited to Ashutosh Sahoo; see LICENSE and README for attribution.")


if __name__ == "__main__":
    main()
