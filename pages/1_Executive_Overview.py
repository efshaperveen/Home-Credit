import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_data, add_derived_columns

st.set_page_config(
    page_title="Executive Overview",
    page_icon="📊",
    layout="wide",
)

df = add_derived_columns(load_data())

st.title("Home Credit | Executive Overview")
st.caption("Key performance indicators and overall loan portfolio summary")

# -----------------------------
# Filters
# -----------------------------
with st.sidebar:
    st.header("Filters")

    contract_options = ["All"] + sorted(df["NAME_CONTRACT_TYPE"].dropna().unique().tolist())
    gender_options = ["All"] + sorted(df["CODE_GENDER"].dropna().unique().tolist())

    contract_filter = st.selectbox("Contract Type", contract_options)
    gender_filter = st.selectbox("Gender", gender_options)

    income_min = float(df["AMT_INCOME_TOTAL"].min())
    income_max = float(df["AMT_INCOME_TOTAL"].max())
    income_range = st.slider(
        "Income Range",
        min_value=income_min,
        max_value=income_max,
        value=(income_min, income_max),
    )

    credit_min = float(df["AMT_CREDIT"].min())
    credit_max = float(df["AMT_CREDIT"].max())
    credit_range = st.slider(
        "Credit Range",
        min_value=credit_min,
        max_value=credit_max,
        value=(credit_min, credit_max),
    )

    target_filter = st.selectbox(
        "Target (Default)",
        ["All", "Non-default", "Default"],
    )

filtered = df.copy()

if contract_filter != "All":
    filtered = filtered[filtered["NAME_CONTRACT_TYPE"] == contract_filter]

if gender_filter != "All":
    filtered = filtered[filtered["CODE_GENDER"] == gender_filter]

filtered = filtered[
    filtered["AMT_INCOME_TOTAL"].between(*income_range)
    & filtered["AMT_CREDIT"].between(*credit_range)
]

if target_filter == "Non-default":
    filtered = filtered[filtered["TARGET"] == 0]
elif target_filter == "Default":
    filtered = filtered[filtered["TARGET"] == 1]

# -----------------------------
# KPIs
# -----------------------------
applications = len(filtered)
defaults = int(filtered["TARGET"].sum())
non_defaults = applications - defaults
default_rate = (defaults / applications * 100) if applications else 0
avg_credit = filtered["AMT_CREDIT"].mean() if applications else 0
avg_income = filtered["AMT_INCOME_TOTAL"].mean() if applications else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Applications", f"{applications:,}")
k2.metric("Defaults", f"{defaults:,}")
k3.metric("Default Rate", f"{default_rate:.2f}%")
k4.metric("Non-defaults", f"{non_defaults:,}")
k5.metric("Average Credit", f"{avg_credit:,.0f}")
k6.metric("Average Income", f"{avg_income:,.0f}")

# -----------------------------
# Row 1: Default vs Non-default, Application outcome, Loan distribution
# -----------------------------
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("Default vs Non-default")
    donut_df = pd.DataFrame({
        "Status": ["Non-default", "Default"],
        "Count": [non_defaults, defaults],
    })
    fig = px.pie(
        donut_df,
        names="Status",
        values="Count",
        hole=0.58,
        title=f"{applications:,} Applications",
    )
    fig.update_layout(margin=dict(t=50, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Application Outcome")
    outcome_df = pd.DataFrame({
        "Outcome": ["Non-default", "Default"],
        "Applications": [non_defaults, defaults],
    })
    fig = px.bar(
        outcome_df,
        x="Outcome",
        y="Applications",
        text="Applications",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(yaxis_title="Applications", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

with c3:
    st.subheader("Loan Amount Distribution")
    fig = px.histogram(
        filtered,
        x="AMT_CREDIT",
        nbins=35,
        labels={"AMT_CREDIT": "Credit Amount"},
    )
    fig.update_layout(yaxis_title="Applications", xaxis_title="Credit Amount")
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Row 2: Income vs Credit + Contract Type
# -----------------------------
c4, c5 = st.columns(2)

with c4:
    st.subheader("Income vs Credit Amount")
    scatter_data = filtered[["AMT_INCOME_TOTAL", "AMT_CREDIT", "TARGET"]].dropna()

    # Keep the dashboard responsive when many rows are selected.
    if len(scatter_data) > 10000:
        scatter_data = scatter_data.sample(10000, random_state=42)

    fig = px.scatter(
        scatter_data,
        x="AMT_INCOME_TOTAL",
        y="AMT_CREDIT",
        color="TARGET",
        color_discrete_map={0: "#1f9d8b", 1: "#f2a900"},
        labels={
            "AMT_INCOME_TOTAL": "Income",
            "AMT_CREDIT": "Credit Amount",
            "TARGET": "Default",
        },
        opacity=0.55,
    )
    st.plotly_chart(fig, use_container_width=True)

with c5:
    st.subheader("Default Rate by Contract Type")
    contract_df = (
        filtered.groupby("NAME_CONTRACT_TYPE", dropna=False)["TARGET"]
        .mean()
        .mul(100)
        .reset_index(name="Default Rate")
    )
    fig = px.bar(
        contract_df,
        x="NAME_CONTRACT_TYPE",
        y="Default Rate",
        text="Default Rate",
    )
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(yaxis_title="Default Rate (%)", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Sample table
# -----------------------------
st.subheader("Sample Application Data")

table_cols = [
    "SK_ID_CURR",
    "TARGET",
    "NAME_CONTRACT_TYPE",
    "AMT_CREDIT",
    "AMT_INCOME_TOTAL",
    "AMT_ANNUITY",
    "DAYS_BIRTH",
]

display_df = filtered[table_cols].head(10).copy()
display_df["TARGET"] = display_df["TARGET"].map({0: "Non-default", 1: "Default"})

st.dataframe(display_df, use_container_width=True, hide_index=True)
