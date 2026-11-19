"""Interactive Streamlit dashboard for the Hotel Booking Demand analysis."""

from __future__ import annotations

import calendar
import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


MONTHS = list(calendar.month_name)[1:]
MONTH_LOOKUP = {month.lower(): month for month in MONTHS}
MONTH_LOOKUP.update({month[:3].lower(): month for month in MONTHS})
MONTH_LOOKUP.update({str(index): calendar.month_name[index] for index in range(1, 13)})
MONTH_LOOKUP.update({f"{index:02}": calendar.month_name[index] for index in range(1, 13)})

REQUIRED_COLUMNS = {
    "hotel",
    "is_canceled",
    "lead_time",
    "arrival_date_year",
    "arrival_date_month",
    "adr",
    "adults",
}
CHART_COLORS = ["#2563EB", "#14B8A6", "#F59E0B", "#8B5CF6", "#EC4899"]

st.set_page_config(
    page_title="Hotel Booking Analysis Dashboard",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #f5f7fb; }
    [data-testid="stSidebar"] { background: #101b33; }
    [data-testid="stSidebar"] * { color: #eef3ff; }
    [data-testid="stSidebar"] label { color: #d6e0f5 !important; }
    .hero {
        padding: 1.65rem 1.9rem;
        margin: 0 0 1.3rem 0;
        border-radius: 18px;
        background: linear-gradient(115deg, #10213f 0%, #1d4ed8 68%, #14b8a6 130%);
        color: white;
        box-shadow: 0 10px 28px rgba(23, 50, 93, .16);
    }
    .hero h1 { margin: 0; font-size: 2rem; }
    .hero p { margin: .45rem 0 0; color: #dbeafe; }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e7ebf3;
        padding: 1rem 1.1rem;
        border-radius: 14px;
        box-shadow: 0 4px 14px rgba(16, 33, 63, .04);
    }
    div[data-testid="stMetricLabel"] { color: #596579; }
    h2, h3 { color: #16233c; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def read_csv_data(file_bytes: bytes) -> pd.DataFrame:
    """Parse CSV bytes once and cache the result for reruns."""
    return pd.read_csv(io.BytesIO(file_bytes), low_memory=False)


def normalize_month(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    text = str(value).strip()
    return MONTH_LOOKUP.get(text.lower(), text)


def prepare_data(raw_data: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, int]:
    """Apply the notebook's cleaning choices to a copy of the loaded data."""
    data = raw_data.copy()
    data.columns = [str(column).strip() for column in data.columns]
    original_missing = data.isna().sum()
    duplicate_count = int(data.duplicated().sum())
    data = data.drop_duplicates().copy()

    numeric_columns = [
        "is_canceled",
        "lead_time",
        "arrival_date_year",
        "adr",
        "adults",
        "children",
        "babies",
        "total_of_special_requests",
        "arrival_date_month",
    ]
    for column in numeric_columns:
        if column in data.columns and column != "arrival_date_month":
            data[column] = pd.to_numeric(data[column], errors="coerce")

    if "children" not in data:
        data["children"] = 0
    data["children"] = data["children"].fillna(0)
    if "babies" not in data:
        data["babies"] = 0
    data["babies"] = data["babies"].fillna(0)

    for column in ("agent", "company"):
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce").fillna(0)

    if "country" in data.columns:
        modes = data["country"].mode(dropna=True)
        fill_country = modes.iloc[0] if not modes.empty else "Unknown"
        data["country"] = data["country"].fillna(fill_country)

    data["arrival_date_month"] = data["arrival_date_month"].map(normalize_month)
    data["arrival_date_year"] = pd.to_numeric(data["arrival_date_year"], errors="coerce")
    data["is_canceled"] = pd.to_numeric(data["is_canceled"], errors="coerce")
    guest_columns = [column for column in ("adults", "children", "babies") if column in data]
    data["total_guests"] = data[guest_columns].fillna(0).sum(axis=1)

    if "reservation_status_date" in data.columns:
        data["reservation_status_date"] = pd.to_datetime(
            data["reservation_status_date"], errors="coerce"
        )

    return data, original_missing, duplicate_count


def display_chart(figure: go.Figure) -> None:
    figure.update_layout(
        template="plotly_white",
        margin=dict(l=12, r=12, t=55, b=12),
        title_font=dict(size=17, color="#17233b"),
        font=dict(color="#39465d"),
        legend_title_text="",
    )
    st.plotly_chart(figure, width="stretch")


def available_values(data: pd.DataFrame, column: str) -> list:
    if column not in data.columns:
        return []
    return sorted(data[column].dropna().unique().tolist(), key=lambda value: str(value))


def show_notebook_findings() -> None:
    st.subheader("Findings recorded in the notebook")
    st.caption(
        "These are results from the notebook's unfiltered run. They are reference "
        "findings and do not change with the dashboard filters."
    )
    findings = [
        "The notebook reports **119,390 bookings** and found **44,224 canceled** "
        "versus **75,166 not canceled** (about **37.04%** canceled).",
        "**City Hotel** had 79,330 bookings compared with 40,060 for Resort Hotel.",
        "Average lead time was **104.01 days**. Online TA was the largest market "
        "segment with 56,477 bookings.",
        "Average ADR was **105.30** for City Hotel and **94.95** for Resort Hotel. "
        "The notebook measured a very weak negative lead-time/ADR correlation "
        "(−0.063).",
        "Transient customers had the highest cancellation rate in the notebook "
        "(about **40.75%**); bookings with zero special requests also had the "
        "highest cancellation rate by request count.",
    ]
    for finding in findings:
        st.markdown(f"- {finding}")


def plot_hotel_comparison(data: pd.DataFrame) -> None:
    if "hotel" not in data or data.empty:
        st.info("Hotel type data is not available for this selection.")
        return
    summary = data.groupby("hotel", dropna=False).agg(
        Bookings=("is_canceled", "size"),
        Cancellation_Rate=("is_canceled", "mean"),
        Average_ADR=("adr", "mean"),
    ).reset_index()
    bookings, cancellations, adr = st.columns(3)
    with bookings:
        figure = px.bar(
            summary,
            x="hotel",
            y="Bookings",
            color="hotel",
            color_discrete_sequence=CHART_COLORS,
            title="Bookings by hotel type",
            labels={"hotel": "Hotel type"},
            text_auto=".2s",
        )
        display_chart(figure)
    with cancellations:
        figure = px.bar(
            summary.assign(Cancellation_Rate=summary["Cancellation_Rate"] * 100),
            x="hotel",
            y="Cancellation_Rate",
            title="Cancellation rate by hotel type",
            labels={"hotel": "Hotel type", "Cancellation_Rate": "Cancellation rate (%)"},
            color_discrete_sequence=CHART_COLORS,
        )
        display_chart(figure)
    with adr:
        figure = px.bar(
            summary,
            x="hotel",
            y="Average_ADR",
            title="Average ADR by hotel type",
            labels={"hotel": "Hotel type", "Average_ADR": "Average ADR"},
            color_discrete_sequence=CHART_COLORS,
        )
        display_chart(figure)


def show_overview(
    data: pd.DataFrame,
    all_data: pd.DataFrame,
    original_shape: tuple[int, int],
) -> None:
    st.subheader("Dataset overview")
    st.write(
        f"The loaded dataset contains **{len(all_data):,} unique rows** and "
        f"**{original_shape[1]:,} source columns**."
    )
    display_columns = [
        column
        for column in (
            "hotel",
            "is_canceled",
            "lead_time",
            "arrival_date_year",
            "arrival_date_month",
            "country",
            "market_segment",
            "customer_type",
            "adults",
            "children",
            "babies",
            "adr",
        )
        if column in data.columns
    ]
    st.caption("Privacy-safe preview of the current filtered selection.")
    st.dataframe(data[display_columns].head(8), width="stretch", hide_index=True)

    st.subheader("Key performance indicators")
    metrics = st.columns(5)
    total = len(data)
    cancellations = int(data["is_canceled"].eq(1).sum())
    cancel_rate = data["is_canceled"].mean()
    adr = data["adr"].mean()
    guest_total = data["total_guests"].sum()
    metrics[0].metric("Total Bookings", f"{total:,}")
    metrics[1].metric("Total Cancellations", f"{cancellations:,}")
    metrics[2].metric("Cancellation Rate", f"{cancel_rate:.1%}" if pd.notna(cancel_rate) else "N/A")
    metrics[3].metric("Average Daily Rate (ADR)", f"{adr:,.2f}" if pd.notna(adr) else "N/A")
    metrics[4].metric("Total Guests", f"{guest_total:,.0f}")

    st.subheader("Hotel type comparison")
    plot_hotel_comparison(data)

    left, right = st.columns(2)
    with left:
        st.markdown("#### Bookings by arrival year")
        if data["arrival_date_year"].notna().any():
            yearly = (
                data.dropna(subset=["arrival_date_year"])
                .groupby("arrival_date_year")
                .size()
                .rename("Bookings")
                .reset_index()
            )
            yearly["arrival_date_year"] = yearly["arrival_date_year"].astype(int).astype(str)
            display_chart(
                px.bar(
                    yearly,
                    x="arrival_date_year",
                    y="Bookings",
                    title="Annual booking volume",
                    labels={"arrival_date_year": "Arrival year"},
                    color_discrete_sequence=CHART_COLORS,
                )
            )
        else:
            st.info("Arrival-year values are not available.")
    with right:
        st.markdown("#### Arrival month pattern")
        month_data = data.dropna(subset=["arrival_date_month"])
        if not month_data.empty:
            monthly = month_data["arrival_date_month"].value_counts().reindex(MONTHS, fill_value=0)
            display_chart(
                px.bar(
                    x=monthly.index,
                    y=monthly.values,
                    title="Bookings by arrival month",
                    labels={"x": "Arrival month", "y": "Bookings"},
                    color_discrete_sequence=CHART_COLORS,
                )
            )
        else:
            st.info("Arrival-month values are not available.")
    show_notebook_findings()


def show_hotel_performance(data: pd.DataFrame) -> None:
    st.subheader("Hotel type performance")
    plot_hotel_comparison(data)
    if data.empty:
        return
    summary = (
        data.groupby("hotel", dropna=False)
        .agg(
            Bookings=("is_canceled", "size"),
            Cancellations=("is_canceled", "sum"),
            Cancellation_Rate=("is_canceled", "mean"),
            Average_ADR=("adr", "mean"),
            Average_Lead_Time=("lead_time", "mean"),
        )
        .reset_index()
    )
    summary["Cancellation_Rate"] = summary["Cancellation_Rate"].map(
        lambda value: f"{value:.1%}" if pd.notna(value) else "N/A"
    )
    st.dataframe(summary, width="stretch", hide_index=True)
    best = data.groupby("hotel")["is_canceled"].size()
    if not best.empty:
        st.info(f"Most bookings in the current selection: **{best.idxmax()}** ({best.max():,}).")


def show_cancellations(data: pd.DataFrame) -> None:
    st.subheader("Booking cancellation analysis")
    if data.empty:
        return
    status_counts = (
        data["is_canceled"].map({0: "Not canceled", 1: "Canceled"}).fillna("Unknown")
        .value_counts()
        .rename_axis("Booking status")
        .reset_index(name="Bookings")
    )
    left, right = st.columns(2)
    with left:
        display_chart(
            px.pie(
                status_counts,
                names="Booking status",
                values="Bookings",
                hole=0.58,
                title="Canceled vs. not canceled",
                color_discrete_sequence=CHART_COLORS,
            )
        )
    with right:
        if "customer_type" in data:
            customer_rates = (
                data.groupby("customer_type")["is_canceled"]
                .mean()
                .mul(100)
                .sort_values(ascending=False)
                .rename("Cancellation rate (%)")
                .reset_index()
            )
            display_chart(
                px.bar(
                    customer_rates,
                    x="customer_type",
                    y="Cancellation rate (%)",
                    title="Cancellation rate by customer type",
                    labels={"customer_type": "Customer type"},
                    color_discrete_sequence=CHART_COLORS,
                )
            )
        else:
            st.info("Customer type is not present in this CSV.")

    left, right = st.columns(2)
    with left:
        if "market_segment" in data:
            segment_rates = (
                data.groupby("market_segment")["is_canceled"]
                .mean()
                .mul(100)
                .sort_values(ascending=False)
                .rename("Cancellation rate (%)")
                .reset_index()
            )
            display_chart(
                px.bar(
                    segment_rates,
                    x="market_segment",
                    y="Cancellation rate (%)",
                    title="Cancellation rate by market segment",
                    labels={"market_segment": "Market segment"},
                    color_discrete_sequence=CHART_COLORS,
                )
            )
        else:
            st.info("Market segment is not present in this CSV.")
    with right:
        if "total_of_special_requests" in data:
            request_rates = (
                data.groupby("total_of_special_requests")["is_canceled"]
                .mean()
                .mul(100)
                .rename("Cancellation rate (%)")
                .reset_index()
            )
            display_chart(
                px.bar(
                    request_rates,
                    x="total_of_special_requests",
                    y="Cancellation rate (%)",
                    title="Special requests and cancellation",
                    labels={"total_of_special_requests": "Number of special requests"},
                    color_discrete_sequence=CHART_COLORS,
                )
            )
        else:
            st.info("Special-request data is not present in this CSV.")

    rate = data["is_canceled"].mean()
    st.info(
        f"Cancellation rate for the current filters: **{rate:.1%}**."
        if pd.notna(rate)
        else "Cancellation rate is unavailable for this selection."
    )


def show_customer_country(data: pd.DataFrame) -> None:
    st.subheader("Customer and country analysis")
    left, right = st.columns(2)
    with left:
        if "customer_type" in data and not data.empty:
            customer_counts = (
                data["customer_type"].value_counts().rename_axis("Customer type").reset_index(name="Bookings")
            )
            display_chart(
                px.bar(
                    customer_counts,
                    x="Customer type",
                    y="Bookings",
                    title="Bookings by customer type",
                    color_discrete_sequence=CHART_COLORS,
                )
            )
        else:
            st.info("Customer type is not present in this CSV.")
    with right:
        if "country" in data and not data.empty:
            country_counts = (
                data["country"].fillna("Unknown").value_counts().head(15)
                .rename_axis("Country")
                .reset_index(name="Bookings")
            )
            display_chart(
                px.bar(
                    country_counts.sort_values("Bookings"),
                    x="Bookings",
                    y="Country",
                    orientation="h",
                    title="Top 15 booking countries",
                    color_discrete_sequence=CHART_COLORS,
                )
            )
        else:
            st.info("Country is not present in this CSV.")
    if "market_segment" in data and not data.empty:
        segment_counts = (
            data["market_segment"].value_counts().rename_axis("Market segment").reset_index(name="Bookings")
        )
        display_chart(
            px.bar(
                segment_counts,
                x="Market segment",
                y="Bookings",
                title="Bookings by market segment",
                color_discrete_sequence=CHART_COLORS,
            )
        )


def show_booking_trends(data: pd.DataFrame) -> None:
    st.subheader("Monthly and yearly booking trends")
    if data.empty:
        return
    dated = data.dropna(subset=["arrival_date_year", "arrival_date_month"]).copy()
    dated["month_number"] = dated["arrival_date_month"].map(
        {month: index for index, month in enumerate(MONTHS, start=1)}
    )
    dated = dated.dropna(subset=["month_number"])
    if dated.empty:
        st.info("Arrival year and month values are needed to draw booking trends.")
        return
    dated["arrival_month"] = pd.to_datetime(
        {
            "year": dated["arrival_date_year"].astype(int),
            "month": dated["month_number"].astype(int),
            "day": 1,
        },
        errors="coerce",
    )
    dated = dated.dropna(subset=["arrival_month"])
    monthly = (
        dated.groupby(["arrival_month", "hotel"], dropna=False)
        .size()
        .reset_index(name="Bookings")
    )
    display_chart(
        px.line(
            monthly,
            x="arrival_month",
            y="Bookings",
            color="hotel",
            markers=True,
            title="Monthly arrivals by hotel type",
            labels={"arrival_month": "Arrival month", "hotel": "Hotel type"},
            color_discrete_sequence=CHART_COLORS,
        )
    )
    yearly = dated.groupby("arrival_date_year").size().reset_index(name="Bookings")
    yearly["arrival_date_year"] = yearly["arrival_date_year"].astype(int).astype(str)
    display_chart(
        px.bar(
            yearly,
            x="arrival_date_year",
            y="Bookings",
            title="Yearly booking volume",
            labels={"arrival_date_year": "Arrival year"},
            color_discrete_sequence=CHART_COLORS,
        )
    )


def show_adr_lead_time(data: pd.DataFrame) -> None:
    st.subheader("Average Daily Rate and lead time")
    if data.empty:
        return
    left, right = st.columns(2)
    with left:
        adr_data = data.dropna(subset=["adr"])
        display_chart(
            px.histogram(
                adr_data,
                x="adr",
                color="hotel",
                nbins=50,
                title="Average Daily Rate distribution",
                labels={"adr": "ADR"},
                color_discrete_sequence=CHART_COLORS,
            )
        )
    with right:
        lead_data = data.dropna(subset=["lead_time"])
        display_chart(
            px.histogram(
                lead_data,
                x="lead_time",
                color="hotel",
                nbins=40,
                title="Lead time distribution",
                labels={"lead_time": "Days booked before arrival"},
                color_discrete_sequence=CHART_COLORS,
            )
        )
    st.markdown("#### Lead time compared with ADR")
    scatter_data = data.dropna(subset=["lead_time", "adr"])
    if len(scatter_data) > 5000:
        scatter_data = scatter_data.sample(5000, random_state=42)
    display_chart(
        px.scatter(
            scatter_data,
            x="lead_time",
            y="adr",
            color="hotel",
            opacity=0.55,
            title="Lead time vs. ADR (up to 5,000 sampled bookings)",
            labels={"lead_time": "Days booked before arrival", "adr": "Average Daily Rate"},
            color_discrete_sequence=CHART_COLORS,
        )
    )
    corr_data = data[["lead_time", "adr"]].dropna()
    correlation = corr_data["lead_time"].corr(corr_data["adr"]) if len(corr_data) > 1 else np.nan
    average_lead = data["lead_time"].mean()
    st.info(
        f"Average lead time in this selection is **{average_lead:.1f} days**; "
        f"the lead-time/ADR correlation is **{correlation:.3f}**."
        if pd.notna(correlation) and pd.notna(average_lead)
        else "Not enough valid lead-time and ADR observations to calculate the relationship."
    )
    if "hotel" in data:
        adr_by_hotel = data.groupby("hotel")["adr"].mean().dropna()
        if not adr_by_hotel.empty:
            display_chart(
                px.bar(
                    adr_by_hotel.rename("Average ADR").reset_index(),
                    x="hotel",
                    y="Average ADR",
                    title="Average ADR by hotel type",
                    labels={"hotel": "Hotel type"},
                    color_discrete_sequence=CHART_COLORS,
                )
            )


def show_guest_distribution(data: pd.DataFrame) -> None:
    st.subheader("Guest distribution")
    if data.empty:
        return
    data = data.copy()
    data["Guest group size"] = pd.cut(
        data["total_guests"],
        bins=[-0.1, 0.9, 1.9, 2.9, 3.9, np.inf],
        labels=["0", "1", "2", "3", "4+"],
    )
    distribution = (
        data["Guest group size"].value_counts(sort=False).rename_axis("Guests per booking")
        .reset_index(name="Bookings")
    )
    left, right = st.columns(2)
    with left:
        display_chart(
            px.bar(
                distribution,
                x="Guests per booking",
                y="Bookings",
                title="Bookings by party size",
                color_discrete_sequence=CHART_COLORS,
            )
        )
    with right:
        if {"adults", "children", "babies"}.issubset(data.columns):
            guest_totals = pd.DataFrame(
                {
                    "Guest type": ["Adults", "Children", "Babies"],
                    "Guests": [
                        data["adults"].fillna(0).sum(),
                        data["children"].fillna(0).sum(),
                        data["babies"].fillna(0).sum(),
                    ],
                }
            )
            display_chart(
                px.pie(
                    guest_totals,
                    names="Guest type",
                    values="Guests",
                    hole=0.55,
                    title="Guest composition",
                    color_discrete_sequence=CHART_COLORS,
                )
            )
    st.caption("Party size is calculated from adults, children, and babies for each booking.")


def show_data_quality(
    data: pd.DataFrame,
    original_missing: pd.Series,
    duplicate_count: int,
    original_shape: tuple[int, int],
) -> None:
    st.subheader("Missing values and data quality")
    st.write(
        f"Original CSV: **{original_shape[0]:,} rows × {original_shape[1]:,} columns**. "
        f"Exact duplicate rows detected before cleaning: **{duplicate_count:,}**."
    )
    missing = original_missing[original_missing.gt(0)].sort_values(ascending=False)
    if missing.empty:
        st.success("No missing values were present in the loaded CSV.")
    else:
        quality = pd.DataFrame(
            {
                "Column": missing.index,
                "Missing values": missing.values,
                "Missing (%)": (missing.values / max(len(data) + duplicate_count, 1) * 100).round(2),
            }
        )
        display_chart(
            px.bar(
                quality.sort_values("Missing values"),
                x="Missing values",
                y="Column",
                orientation="h",
                title="Missing values in the original CSV",
                hover_data=["Missing (%)"],
                color_discrete_sequence=CHART_COLORS,
            )
        )
        st.dataframe(quality, width="stretch", hide_index=True)
    st.markdown(
        """
        **Cleaning applied by the dashboard**
        - Exact duplicate rows are removed from the analysis copy.
        - Missing children and babies are treated as zero for guest totals.
        - Missing country values are filled with the most frequent country
          (or `Unknown` if no country value exists).
        - Missing agent and company identifiers are filled with zero, matching
          the notebook's cleaning approach.
        - Date and numeric fields are parsed safely; invalid values are excluded
          from the relevant chart rather than changing the source CSV.
        - ADR and lead-time outliers are shown, not removed.
        """
    )
    adr = data["adr"].dropna()
    if not adr.empty:
        q1, q3 = adr.quantile([0.25, 0.75])
        iqr = q3 - q1
        outlier_count = int(((adr < q1 - 1.5 * iqr) | (adr > q3 + 1.5 * iqr)).sum())
        st.info(f"IQR rule flags **{outlier_count:,} ADR outliers** in the cleaned data; none are removed.")


st.markdown(
    """
    <div class="hero">
      <h1>Hotel Booking Analysis Dashboard</h1>
      <p>Explore booking patterns, cancellations, guests, pricing, and data quality.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("## 🏨 Hotel bookings")
st.sidebar.caption("Choose a section and refine the analysis.")
page = st.sidebar.selectbox(
    "Dashboard section",
    [
        "Overview",
        "Hotel Performance",
        "Cancellation Analysis",
        "Customer & Country",
        "Booking Trends",
        "ADR & Lead Time",
        "Guest Distribution",
        "Data Quality",
    ],
)

project_dir = Path(__file__).resolve().parent
local_csvs = sorted(project_dir.glob("*.csv"))
uploaded_file = st.sidebar.file_uploader("Upload hotel booking CSV", type=["csv"])

local_file: Path | None = None
if local_csvs:
    local_file = st.sidebar.selectbox(
        "Or choose a CSV in the project folder",
        local_csvs,
        format_func=lambda path: path.name,
    )

if uploaded_file is not None:
    source_name = uploaded_file.name
    csv_bytes = uploaded_file.getvalue()
elif local_file is not None:
    source_name = local_file.name
    try:
        csv_bytes = local_file.read_bytes()
    except OSError as error:
        st.error(f"Could not read {local_file.name}: {error}")
        st.stop()
else:
    st.info(
        "No hotel-booking CSV was found. Upload the dataset in the sidebar, or place "
        "a CSV file in the project folder and rerun the dashboard."
    )
    st.stop()

try:
    raw_data = read_csv_data(csv_bytes)
except (UnicodeDecodeError, pd.errors.ParserError, OSError, ValueError) as error:
    st.error(f"Could not load {source_name} as a CSV: {error}")
    st.stop()

raw_data.columns = [str(column).strip() for column in raw_data.columns]
original_shape = raw_data.shape
missing_required = sorted(REQUIRED_COLUMNS.difference(raw_data.columns))
if missing_required:
    st.error(
        "This CSV is missing columns needed for the dashboard: "
        + ", ".join(f"`{column}`" for column in missing_required)
    )
    st.stop()

data, raw_missing, duplicate_count = prepare_data(raw_data)
st.sidebar.caption(f"Data source: {source_name} · {len(data):,} unique rows")

st.sidebar.markdown("### Filters")
hotel_options = available_values(data, "hotel")
selected_hotels = st.sidebar.multiselect("Hotel type", hotel_options, default=hotel_options)
year_options = sorted(
    [int(value) for value in data["arrival_date_year"].dropna().unique()]
)
selected_years = st.sidebar.multiselect("Arrival year", year_options, default=year_options)
month_options = [month for month in MONTHS if month in set(data["arrival_date_month"].dropna())]
selected_months = st.sidebar.multiselect("Arrival month", month_options, default=month_options)

selected_market_segments: list = []
if "market_segment" in data:
    options = available_values(data, "market_segment")
    selected_market_segments = st.sidebar.multiselect(
        "Market segment", options, default=options
    )
selected_customer_types: list = []
if "customer_type" in data:
    options = available_values(data, "customer_type")
    selected_customer_types = st.sidebar.multiselect(
        "Customer type", options, default=options
    )
status_filter = st.sidebar.selectbox(
    "Booking status", ["All bookings", "Not canceled", "Canceled"]
)

filtered_data = data[
    data["hotel"].isin(selected_hotels)
    & data["arrival_date_year"].isin(selected_years)
    & data["arrival_date_month"].isin(selected_months)
].copy()
if "market_segment" in filtered_data:
    filtered_data = filtered_data[filtered_data["market_segment"].isin(selected_market_segments)]
if "customer_type" in filtered_data:
    filtered_data = filtered_data[filtered_data["customer_type"].isin(selected_customer_types)]
if status_filter == "Not canceled":
    filtered_data = filtered_data[filtered_data["is_canceled"].eq(0)]
elif status_filter == "Canceled":
    filtered_data = filtered_data[filtered_data["is_canceled"].eq(1)]

st.caption(f"Showing {len(filtered_data):,} of {len(data):,} unique bookings after filters.")
if filtered_data.empty:
    st.warning("No bookings match the selected filters. Adjust the sidebar selections.")
    st.stop()

if page == "Overview":
    show_overview(filtered_data, data, original_shape)
elif page == "Hotel Performance":
    show_hotel_performance(filtered_data)
elif page == "Cancellation Analysis":
    show_cancellations(filtered_data)
elif page == "Customer & Country":
    show_customer_country(filtered_data)
elif page == "Booking Trends":
    show_booking_trends(filtered_data)
elif page == "ADR & Lead Time":
    show_adr_lead_time(filtered_data)
elif page == "Guest Distribution":
    show_guest_distribution(filtered_data)
elif page == "Data Quality":
    show_data_quality(data, raw_missing, duplicate_count, original_shape)

st.caption(
    "For privacy, guest names, email addresses, phone numbers, and payment-card "
    "fields are not shown in this dashboard."
)
