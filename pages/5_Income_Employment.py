import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_data, add_derived_columns

st.set_page_config(page_title="Income & Employment", page_icon="💼", layout="wide")

df = add_derived_columns(load_data())

st.title("Income & Employment")
st.caption("Analyze customer income, employment profile, and relationship with default risk")

with st.sidebar:
    st.header("Filters")
    contract_options = ["All"] + sorted(df["NAME_CONTRACT_TYPE"].dropna().unique().tolist())
    occupation_options = ["All"] + sorted(df["OCCUPATION_TYPE"].dropna().unique().tolist())
    income_type_options = ["All"] + sorted(df["NAME_INCOME_TYPE"].dropna().unique().tolist())
    target_options = ["All", "Non-default", "Default"]

    contract_filter = st.selectbox("Contract Type", contract_options)
    occupation_filter = st.selectbox("Occupation Type", occupation_options)
    income_type_filter = st.selectbox("Income Type", income_type_options)
    target_filter = st.selectbox("Target (Default)", target_options)

filtered = df.copy()

if contract_filter != "All":
    filtered = filtered[filtered["NAME_CONTRACT_TYPE"] == contract_filter]
if occupation_filter != "All":
    filtered = filtered[filtered["OCCUPATION_TYPE"] == occupation_filter]
if income_type_filter != "All":
    filtered = filtered[filtered["NAME_INCOME_TYPE"] == income_type_filter]
if target_filter == "Non-default":
    filtered = filtered[filtered["TARGET"] == 0]
elif target_filter == "Default":
    filtered = filtered[filtered["TARGET"] == 1]

n = len(filtered)
avg_income = filtered["AMT_INCOME_TOTAL"].mean() if n else 0
median_income = filtered["AMT_INCOME_TOTAL"].median() if n else 0

# DAYS_EMPLOYED has positive 365243 for Home Credit's special "not employed" code.
# Treat that value as missing for duration analysis.
employment_days = filtered["DAYS_EMPLOYED"].replace(365243, pd.NA)
employment_years = (-employment_days / 365.25)
avg_employment = employment_years.mean() if n else 0
employed = filtered["DAYS_EMPLOYED"].ne(365243).sum()
unemployed = filtered["DAYS_EMPLOYED"].eq(365243).sum()
employed_pct = employed / n * 100 if n else 0
unemployed_pct = unemployed / n * 100 if n else 0

employed_default_rate = (
    filtered.loc[filtered["DAYS_EMPLOYED"].ne(365243), "TARGET"].mean() * 100
    if employed else 0
)

k = st.columns(6)
k[0].metric("Average Income", f"{avg_income:,.0f}")
k[1].metric("Median Income", f"{median_income:,.0f}")
k[2].metric("Avg. Employment Duration", f"{avg_employment:.2f} years")
k[3].metric("Employed Customers", f"{employed_pct:.2f}%")
k[4].metric("Unemployed Customers", f"{unemployed_pct:.2f}%")
k[5].metric("Default Rate (Employed)", f"{employed_default_rate:.2f}%")

c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("Income Distribution")
    fig = px.histogram(filtered, x="AMT_INCOME_TOTAL", nbins=40)
    fig.update_layout(xaxis_title="Income", yaxis_title="Customers")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Average Income by Occupation")
    occ = (
        filtered.dropna(subset=["OCCUPATION_TYPE"])
        .groupby("OCCUPATION_TYPE")["AMT_INCOME_TOTAL"]
        .mean().reset_index(name="Average Income")
        .sort_values("Average Income", ascending=False)
        .head(8)
    )
    fig = px.bar(occ, x="Average Income", y="OCCUPATION_TYPE",
                 orientation="h", text="Average Income")
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(xaxis_title="Average Income", yaxis_title="Occupation")
    st.plotly_chart(fig, use_container_width=True)

with c3:
    st.subheader("Employment Duration Distribution")
    emp = employment_years.dropna().clip(lower=0, upper=40)
    fig = px.histogram(emp, nbins=25, labels={"value": "Employment Years"})
    fig.update_layout(xaxis_title="Employment Years", yaxis_title="Customers")
    st.plotly_chart(fig, use_container_width=True)

c4, c5 = st.columns(2)

with c4:
    st.subheader("Default Rate by Occupation")
    occ_rate = (
        filtered.dropna(subset=["OCCUPATION_TYPE"])
        .groupby("OCCUPATION_TYPE")["TARGET"]
        .mean().mul(100).reset_index(name="Default Rate")
        .sort_values("Default Rate", ascending=False)
    )
    fig = px.bar(occ_rate, x="Default Rate", y="OCCUPATION_TYPE",
                 orientation="h", text="Default Rate")
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(xaxis_title="Default Rate (%)", yaxis_title="Occupation")
    st.plotly_chart(fig, use_container_width=True)

with c5:
    st.subheader("Income vs Credit Amount")
    scatter = filtered[["AMT_INCOME_TOTAL", "AMT_CREDIT", "TARGET"]].dropna()
    if len(scatter) > 10000:
        scatter = scatter.sample(10000, random_state=42)
    fig = px.scatter(
        scatter,
        x="AMT_INCOME_TOTAL",
        y="AMT_CREDIT",
        color="TARGET",
        opacity=0.55,
        labels={"AMT_INCOME_TOTAL": "Income", "AMT_CREDIT": "Credit Amount", "TARGET": "Default"},
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Customer Income & Employment Details")
cols = [
    "SK_ID_CURR", "AMT_INCOME_TOTAL", "NAME_INCOME_TYPE",
    "OCCUPATION_TYPE", "DAYS_EMPLOYED", "AMT_CREDIT", "AMT_ANNUITY", "TARGET"
]
show = filtered[cols].head(10).copy()
show["TARGET"] = show["TARGET"].map({0: "Non-default", 1: "Default"})
st.dataframe(show, use_container_width=True, hide_index=True)
