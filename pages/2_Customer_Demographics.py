import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_data, add_derived_columns

st.set_page_config(
    page_title="Customer Demographics",
    page_icon="👥",
    layout="wide",
)

df = add_derived_columns(load_data())

st.title("Customer Demographics")
st.caption("Customer profile, family structure, education and age analysis with default risk")

# -----------------------------
# Filters
# -----------------------------
with st.sidebar:
    st.header("Filters")

    gender_options = ["All"] + sorted(df["CODE_GENDER"].dropna().unique().tolist())
    age_options = ["All"] + df["AGE_GROUP"].dropna().astype(str).unique().tolist()
    family_options = ["All"] + sorted(df["NAME_FAMILY_STATUS"].dropna().unique().tolist())
    education_options = ["All"] + sorted(df["NAME_EDUCATION_TYPE"].dropna().unique().tolist())

    gender_filter = st.selectbox("Gender", gender_options)
    age_filter = st.selectbox("Age Group", age_options)
    family_filter = st.selectbox("Family Status", family_options)
    education_filter = st.selectbox("Education", education_options)
    target_filter = st.selectbox(
        "Target (Default)",
        ["All", "Non-default", "Default"],
    )

filtered = df.copy()

if gender_filter != "All":
    filtered = filtered[filtered["CODE_GENDER"] == gender_filter]

if age_filter != "All":
    filtered = filtered[filtered["AGE_GROUP"].astype(str) == age_filter]

if family_filter != "All":
    filtered = filtered[filtered["NAME_FAMILY_STATUS"] == family_filter]

if education_filter != "All":
    filtered = filtered[filtered["NAME_EDUCATION_TYPE"] == education_filter]

if target_filter == "Non-default":
    filtered = filtered[filtered["TARGET"] == 0]
elif target_filter == "Default":
    filtered = filtered[filtered["TARGET"] == 1]

# -----------------------------
# KPIs
# -----------------------------
customers = len(filtered)
male_customers = int((filtered["CODE_GENDER"] == "M").sum())
female_customers = int((filtered["CODE_GENDER"] == "F").sum())
avg_age = filtered["AGE_YEARS"].mean() if customers else 0
married_count = int((filtered["NAME_FAMILY_STATUS"] == "Married").sum())
married_pct = married_count / customers * 100 if customers else 0
avg_family_size = filtered["CNT_FAM_MEMBERS"].mean() if customers else 0
customers_with_children = int((filtered["CNT_CHILDREN"] > 0).sum())
children_pct = customers_with_children / customers * 100 if customers else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Male Customers", f"{male_customers:,}")
k2.metric("Female Customers", f"{female_customers:,}")
k3.metric("Average Age", f"{avg_age:.2f} years")
k4.metric("Married Customers", f"{married_pct:.2f}%")
k5.metric("Average Family Size", f"{avg_family_size:.2f}")
k6.metric("Customers with Children", f"{children_pct:.2f}%")

# -----------------------------
# Row 1
# -----------------------------
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("Age Distribution")
    fig = px.histogram(
        filtered,
        x="AGE_YEARS",
        nbins=30,
        labels={"AGE_YEARS": "Age (Years)"},
    )
    fig.update_layout(yaxis_title="Customers", xaxis_title="Age (Years)")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Gender Distribution")
    gender_df = (
        filtered["CODE_GENDER"]
        .replace({"M": "Male", "F": "Female", "XNA": "Unknown"})
        .value_counts()
        .rename_axis("Gender")
        .reset_index(name="Customers")
    )
    fig = px.pie(gender_df, names="Gender", values="Customers", hole=0.55)
    fig.update_layout(margin=dict(t=50, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

with c3:
    st.subheader("Family Status Distribution")
    family_df = (
        filtered["NAME_FAMILY_STATUS"]
        .value_counts()
        .rename_axis("Family Status")
        .reset_index(name="Customers")
    )
    fig = px.bar(
        family_df,
        x="Family Status",
        y="Customers",
        text="Customers",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(xaxis_tickangle=-20)
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Row 2
# -----------------------------
c4, c5 = st.columns(2)

with c4:
    st.subheader("Default Rate by Education")
    education_df = (
        filtered.groupby("NAME_EDUCATION_TYPE", dropna=False)["TARGET"]
        .mean()
        .mul(100)
        .reset_index(name="Default Rate")
        .sort_values("Default Rate", ascending=False)
    )
    fig = px.bar(
        education_df,
        x="Default Rate",
        y="NAME_EDUCATION_TYPE",
        orientation="h",
        text="Default Rate",
    )
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(
        xaxis_title="Default Rate (%)",
        yaxis_title="Education",
    )
    st.plotly_chart(fig, use_container_width=True)

with c5:
    st.subheader("Default Rate by Age Group")
    age_df = (
        filtered.groupby("AGE_GROUP", observed=False)["TARGET"]
        .mean()
        .mul(100)
        .reset_index(name="Default Rate")
    )
    age_df["AGE_GROUP"] = age_df["AGE_GROUP"].astype(str)

    fig = px.line(
        age_df,
        x="AGE_GROUP",
        y="Default Rate",
        markers=True,
        text="Default Rate",
    )
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="top center")
    fig.update_layout(
        xaxis_title="Age Group",
        yaxis_title="Default Rate (%)",
    )
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Customer table
# -----------------------------
st.subheader("Customer Table (Sample)")

table_cols = [
    "SK_ID_CURR",
    "CODE_GENDER",
    "DAYS_BIRTH",
    "NAME_FAMILY_STATUS",
    "NAME_EDUCATION_TYPE",
    "CNT_CHILDREN",
    "CNT_FAM_MEMBERS",
    "TARGET",
]

display_df = filtered[table_cols].head(10).copy()
display_df["TARGET"] = display_df["TARGET"].map({0: "Non-default", 1: "Default"})

st.dataframe(display_df, use_container_width=True, hide_index=True)
