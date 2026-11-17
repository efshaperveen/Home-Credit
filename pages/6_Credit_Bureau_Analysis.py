import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Credit Bureau Analysis",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 Credit Bureau Analysis")
st.caption(
    "Analysis of customers' external credit history from the bureau dataset"
)

# ---------------------------------------------------------
# FILE PATHS
# Expected project structure:
#
# project/
# ├── app.py
# ├── data/
# │   ├── application_train.csv
# │   └── bureau.csv
# └── pages/
#     └── 6_Credit_Bureau_Analysis.py
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
BUREAU_PATH = BASE_DIR / "data" / "bureau.csv"
APPLICATION_PATH = BASE_DIR / "data" / "application_train.csv"


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
@st.cache_data
def load_bureau(path):
    return pd.read_csv(path)


@st.cache_data
def load_application(path):
    # Only columns required by this page are loaded.
    return pd.read_csv(
        path,
        usecols=[
            "SK_ID_CURR",
            "CODE_GENDER",
            "TARGET",
            "NAME_EDUCATION_TYPE"
        ]
    )


if not BUREAU_PATH.exists():
    st.error(f"bureau.csv not found: {BUREAU_PATH}")
    st.stop()

if not APPLICATION_PATH.exists():
    st.error(f"application_train.csv not found: {APPLICATION_PATH}")
    st.stop()


bureau = load_bureau(BUREAU_PATH)
application = load_application(APPLICATION_PATH)

# ---------------------------------------------------------
# CHECK REQUIRED COLUMNS
# ---------------------------------------------------------
bureau_required = [
    "SK_ID_CURR",
    "SK_ID_BUREAU",
    "CREDIT_ACTIVE",
    "CREDIT_CURRENCY",
    "DAYS_CREDIT",
    "CREDIT_DAY_OVERDUE",
    "AMT_CREDIT_SUM",
    "AMT_CREDIT_SUM_DEBT",
    "AMT_CREDIT_SUM_OVERDUE",
    "CREDIT_TYPE"
]

missing_bureau = [
    col for col in bureau_required
    if col not in bureau.columns
]

if missing_bureau:
    st.error(f"Missing columns in bureau.csv: {missing_bureau}")
    st.stop()


# ---------------------------------------------------------
# CLEAN DATA
# ---------------------------------------------------------
numeric_columns = [
    "DAYS_CREDIT",
    "CREDIT_DAY_OVERDUE",
    "AMT_CREDIT_SUM",
    "AMT_CREDIT_SUM_DEBT",
    "AMT_CREDIT_SUM_OVERDUE"
]

for col in numeric_columns:
    bureau[col] = pd.to_numeric(
        bureau[col],
        errors="coerce"
    ).fillna(0)

# Absolute credit duration.
bureau["CREDIT_DURATION_DAYS"] = bureau["DAYS_CREDIT"].abs()

# Merge gender, target and education from application_train.
# One row per customer in application_train, so this does not
# multiply bureau rows.
customer_info = application[
    [
        "SK_ID_CURR",
        "CODE_GENDER",
        "TARGET",
        "NAME_EDUCATION_TYPE"
    ]
].drop_duplicates("SK_ID_CURR")

bureau_full = bureau.merge(
    customer_info,
    on="SK_ID_CURR",
    how="left"
)


# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------
with st.sidebar:
    st.header("🔎 Filters")

    credit_type_options = (
        ["All"]
        + sorted(
            bureau_full["CREDIT_TYPE"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
    )

    gender_options = (
        ["All"]
        + sorted(
            bureau_full["CODE_GENDER"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
    )

    active_options = (
        ["All"]
        + sorted(
            bureau_full["CREDIT_ACTIVE"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
    )

    credit_type_filter = st.selectbox(
        "Contract Type",
        credit_type_options
    )

    gender_filter = st.selectbox(
        "Gender",
        gender_options
    )

    active_filter = st.selectbox(
        "Credit Active Status",
        active_options
    )

    min_days = int(
        bureau_full["DAYS_CREDIT"].min()
    )

    max_days = int(
        bureau_full["DAYS_CREDIT"].max()
    )

    date_range = st.slider(
        "Date Range (Days Credit)",
        min_value=min_days,
        max_value=max_days,
        value=(min_days, 0)
        if min_days <= 0 <= max_days
        else (min_days, max_days)
    )


# ---------------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------------
filtered = bureau_full.copy()

if credit_type_filter != "All":
    filtered = filtered[
        filtered["CREDIT_TYPE"].astype(str)
        == credit_type_filter
    ]

if gender_filter != "All":
    filtered = filtered[
        filtered["CODE_GENDER"].astype(str)
        == gender_filter
    ]

if active_filter != "All":
    filtered = filtered[
        filtered["CREDIT_ACTIVE"].astype(str)
        == active_filter
    ]

filtered = filtered[
    filtered["DAYS_CREDIT"].between(
        date_range[0],
        date_range[1]
    )
]


# ---------------------------------------------------------
# KPI CALCULATIONS
# ---------------------------------------------------------
total_records = len(filtered)

customers_with_bureau = (
    filtered["SK_ID_CURR"]
    .nunique()
)

total_customers = len(application)

bureau_customer_pct = (
    customers_with_bureau / total_customers * 100
    if total_customers
    else 0
)

average_bureau_credit = (
    filtered["AMT_CREDIT_SUM"].mean()
    if total_records
    else 0
)

median_bureau_credit = (
    filtered["AMT_CREDIT_SUM"].median()
    if total_records
    else 0
)

active_credits = int(
    (filtered["CREDIT_ACTIVE"] == "Active").sum()
)

active_credit_pct = (
    active_credits / total_records * 100
    if total_records
    else 0
)

overdue_total = (
    filtered["AMT_CREDIT_SUM_OVERDUE"].sum()
    if total_records
    else 0
)

avg_overdue_per_credit = (
    filtered["AMT_CREDIT_SUM_OVERDUE"].mean()
    if total_records
    else 0
)

average_credit_duration = (
    filtered["CREDIT_DURATION_DAYS"].mean()
    if total_records
    else 0
)

# Bureau-linked default rate.
# A customer is considered bureau-linked if their customer ID
# appears in the currently filtered bureau data.
linked_customer_ids = filtered["SK_ID_CURR"].dropna().unique()

linked_application = application[
    application["SK_ID_CURR"].isin(linked_customer_ids)
]

bureau_linked_default_rate = (
    linked_application["TARGET"].mean() * 100
    if len(linked_application)
    else 0
)

overall_default_rate = (
    application["TARGET"].mean() * 100
)

default_difference = (
    bureau_linked_default_rate
    - overall_default_rate
)


# ---------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------
k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    st.metric(
        "Customers with Bureau History",
        f"{customers_with_bureau:,}",
        f"{bureau_customer_pct:.2f}% of {total_customers:,}"
    )

with k2:
    st.metric(
        "Average Bureau Credit",
        f"{average_bureau_credit:,.0f}",
        f"Median: {median_bureau_credit:,.0f}"
    )

with k3:
    st.metric(
        "Active Bureau Loans",
        f"{active_credits:,}",
        f"{active_credit_pct:.1f}% of bureau credits"
    )

with k4:
    st.metric(
        "Overdue Bureau Amount",
        f"{overdue_total:,.0f}",
        f"Avg per credit: {avg_overdue_per_credit:,.0f}"
    )

with k5:
    st.metric(
        "Average Credit Duration",
        f"{average_credit_duration:,.0f}",
        f"≈ {average_credit_duration / 365.25:.2f} years"
    )

with k6:
    st.metric(
        "Bureau-Linked Default Rate",
        f"{bureau_linked_default_rate:.2f}%",
        f"vs. overall {overall_default_rate:.2f}% "
        f"({default_difference:+.2f} pp)"
    )


# ---------------------------------------------------------
# ROW 1
# ---------------------------------------------------------
c1, c2, c3 = st.columns(3)


# ---------------------------------------------------------
# ACTIVE VS CLOSED
# ---------------------------------------------------------
with c1:
    st.subheader("Active vs Closed Bureau Credits")

    status_df = (
        filtered["CREDIT_ACTIVE"]
        .value_counts()
        .reset_index()
    )

    status_df.columns = [
        "Credit Status",
        "Number of Credits"
    ]

    fig = px.pie(
        status_df,
        names="Credit Status",
        values="Number of Credits",
        hole=0.58
    )

    fig.update_traces(
        textinfo="percent",
        hovertemplate=(
            "%{label}<br>"
            "Credits: %{value:,}<br>"
            "Share: %{percent}<extra></extra>"
        )
    )

    fig.update_layout(
        showlegend=True,
        margin=dict(l=10, r=10, t=20, b=10)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------------------------------------------------------
# CREDIT STATUS DISTRIBUTION
# ---------------------------------------------------------
with c2:
    st.subheader("Credit Status Distribution")

    status_df = (
        filtered["CREDIT_ACTIVE"]
        .value_counts(normalize=True)
        .mul(100)
        .reset_index()
    )

    status_df.columns = [
        "Credit Status",
        "Share"
    ]

    fig = px.bar(
        status_df,
        x="Credit Status",
        y="Share",
        text="Share"
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig.update_layout(
        yaxis_title="Share of credits (%)",
        xaxis_title=""
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------------------------------------------------------
# OVERDUE AMOUNT DISTRIBUTION
# ---------------------------------------------------------
with c3:
    st.subheader("Overdue Amount Distribution")
    st.caption("(AMT_CREDIT_SUM_OVERDUE)")

    overdue = filtered[
        "AMT_CREDIT_SUM_OVERDUE"
    ].fillna(0)

    bins = [
        -0.01,
        0,
        1000,
        5000,
        10000,
        50000,
        float("inf")
    ]

    labels = [
        "0",
        "(0–1K]",
        "(1K–5K]",
        "(5K–10K]",
        "(10K–50K]",
        "> 50K"
    ]

    overdue_bucket = pd.cut(
        overdue,
        bins=bins,
        labels=labels,
        include_lowest=True
    )

    overdue_df = (
        overdue_bucket
        .value_counts()
        .reindex(labels, fill_value=0)
        .reset_index()
    )

    overdue_df.columns = [
        "Overdue Range",
        "Number of Credits"
    ]

    fig = px.bar(
        overdue_df,
        x="Overdue Range",
        y="Number of Credits",
        text="Number of Credits"
    )

    fig.update_traces(
        texttemplate="%{text:,}",
        textposition="outside"
    )

    fig.update_layout(
        yaxis_title="Number of credits",
        xaxis_title=""
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------------------------------------------------------
# ROW 2
# ---------------------------------------------------------
c4, c5 = st.columns(2)


# ---------------------------------------------------------
# CREDIT AMOUNT BY CUSTOMER SEGMENT
# ---------------------------------------------------------
with c4:
    st.subheader(
        "Bureau Credit Amount by Customer Segment"
    )
    st.caption("(Avg. AMT_CREDIT_SUM)")

    segment_df = (
        filtered.dropna(
            subset=["NAME_EDUCATION_TYPE"]
        )
        .groupby("NAME_EDUCATION_TYPE")[
            "AMT_CREDIT_SUM"
        ]
        .mean()
        .reset_index()
        .sort_values(
            "AMT_CREDIT_SUM",
            ascending=True
        )
    )

    fig = px.bar(
        segment_df,
        x="AMT_CREDIT_SUM",
        y="NAME_EDUCATION_TYPE",
        orientation="h",
        text="AMT_CREDIT_SUM"
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title="Average Bureau Credit Amount",
        yaxis_title=""
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------------------------------------------------------
# CREDIT DURATION DISTRIBUTION
# ---------------------------------------------------------
with c5:
    st.subheader(
        "Credit Duration Distribution (DAYS_CREDIT)"
    )

    duration = filtered[
        "CREDIT_DURATION_DAYS"
    ].dropna()

    duration_bins = [
        0,
        180,
        365,
        730,
        1095,
        1825,
        2555,
        float("inf")
    ]

    duration_labels = [
        "0–180",
        "181–365",
        "366–730",
        "731–1,095",
        "1,096–1,825",
        "1,826–2,555",
        "> 2,555"
    ]

    duration_bucket = pd.cut(
        duration,
        bins=duration_bins,
        labels=duration_labels,
        include_lowest=True
    )

    duration_df = (
        duration_bucket
        .value_counts()
        .reindex(duration_labels, fill_value=0)
        .reset_index()
    )

    duration_df.columns = [
        "Credit Duration",
        "Number of Credits"
    ]

    fig = px.bar(
        duration_df,
        x="Credit Duration",
        y="Number of Credits",
        text="Number of Credits"
    )

    fig.update_traces(
        texttemplate="%{text:,}",
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title="Credit Duration (Days, absolute value)",
        yaxis_title="Number of credits"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------------------------------------------------------
# DATA TABLE
# ---------------------------------------------------------
st.subheader("Bureau Credit Records (Sample)")

table_columns = [
    "SK_ID_CURR",
    "SK_ID_BUREAU",
    "CREDIT_ACTIVE",
    "CREDIT_CURRENCY",
    "DAYS_CREDIT",
    "AMT_CREDIT_SUM",
    "AMT_CREDIT_SUM_DEBT",
    "AMT_CREDIT_SUM_OVERDUE",
    "CREDIT_DAY_OVERDUE"
]

table_columns = [
    col for col in table_columns
    if col in filtered.columns
]

sample = filtered[
    table_columns
].head(10).copy()

st.caption(
    f"Total Records: {total_records:,}"
)

st.dataframe(
    sample,
    use_container_width=True,
    hide_index=True
)
